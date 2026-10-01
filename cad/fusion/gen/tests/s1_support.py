"""Support for the S1 tests (issue #81, plan 5.3 and 7): build the S1 document, replay one block, run the parity gate.

This file is the only place in the tests that spells the parity command line.  Everything runs at the repository root, as the
real commands do, because the plan names its files relative to it.  The recording backend, the replay and ``scripts/parity.py``
are the three things a block goes through: the builders describe the geometry (recorded), OpenCascade executes it (replayed) and
the parity tool compares the exported mesh with the OpenSCAD oracle.
"""
from __future__ import annotations

import contextlib
import functools
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple

from cad import params
from cad.fusion.gen.core import checks, plan
from cad.fusion.gen.tests import oracle
from cad.fusion.replay import ocp_replay

REPO = Path(__file__).resolve().parents[4]
PLAN_PATH = "cad/fusion/documents/mcc-s1.json"
PARITY = REPO / "scripts" / "parity.py"
CONFIGURATION = "default"

# The thresholds of the architecture brief (E); the parity tool applies the same numbers to the residual pieces.
FRAME_TOL = 0.02       # mm, every bounding-box corner coordinate
VOLUME_GUARD = 0.0005  # relative: a coarse guard in case the residual tool is not there (plan 7)
TOTAL_RESIDUAL = 0.002  # residual volume / part volume


@contextlib.contextmanager
def at_repo_root():
    previous = os.getcwd()
    os.chdir(REPO)
    try:
        yield
    finally:
        os.chdir(previous)


def load_plan() -> dict:
    with at_repo_root():
        return plan.load_plan(PLAN_PATH)


@functools.lru_cache(maxsize=None)
def _build(stage):
    document = load_plan()
    with at_repo_root():
        record, rows, sets = plan.build(document, stage)
    # a record goes through JSON on disk, so go through it here too: tuples become lists
    return json.loads(json.dumps(record)), rows, sets


def build_record(stage=None):
    """``(record, rows, parameter set)`` of the S1 document on the recording backend: the build record of every block, the
    registry rows and the parameter set of the build configuration.  ``stage`` is ``options['stage']`` of the build."""
    record, rows, sets = _build(stage)
    return json.loads(json.dumps(record)), rows, sets[CONFIGURATION]


def new_kit():
    """A ``Kit`` on the recording backend with the registry and the build values of the S1 document, for the tests that build
    a block of their own (a builder called with other arguments than the S1 blocks use)."""
    from cad.fusion.gen.core.facade import Kit

    _, rows, pset = build_record()
    return Kit(SimpleNamespace(backend="recording", design=None, document="MCC-S1", registry=rows, values=pset["values"],
                               options={}, log=print))


def replay_kit(kit, component: str):
    """Replay one component of a kit built with ``new_kit`` and return its ``ComponentResult``."""
    _, rows, pset = build_record()
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    record = json.loads(json.dumps(kit._backend.build_record()))
    return ocp_replay.replay(record, env, {}, components=[component])[component]


def findings(stage=None) -> list:
    """The plan checks (CK1 to CK7, CK9, CK11) over the S1 document: the empty list is a pass."""
    document = load_plan()
    record, rows, pset = build_record(stage)
    return checks.run(record, rows, {CONFIGURATION: pset}, document.get("shared_exceptions", []),
                      owners=document["owners"], protected_prefixes=document["protected_prefixes"])


def replay_block(part: str, out_dir, facet=None):
    """Replay the record, export ``part``'s STEP and STL to ``out_dir/s1/<part>.step`` and ``.model.stl``.  Returns
    ``(ComponentResult, export entry)``; the entry's ``files`` are relative to ``out_dir``.  ``facet`` is the replay's diagnostic
    mode (circles as that many sides, like the oracle's tessellation): never a verdict, it only isolates a residual that is
    not a facet effect."""
    results, exports = _replay(part, facet)
    subset = {"configurations": [{"id": CONFIGURATION, "exports": exports}]}
    (entry,) = ocp_replay.export(results, subset, CONFIGURATION, out_dir)
    return results[exports[0]["component"]], entry


def _replay(part: str, facet=None):
    document = load_plan()
    record, rows, pset = build_record()
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    exports = [e for e in document["configurations"][0]["exports"] if e["part"] == part]
    if len(exports) != 1:
        raise ValueError(f"{part!r} is not a block of the S1 document")
    return ocp_replay.replay(record, env, pset["suppress"], facet=facet, components=[exports[0]["component"]]), exports


def block_features(part: str) -> dict:
    """``{feature name: volume change in mm3}`` of one block's replay (nothing is exported)."""
    results, exports = _replay(part)
    return {f["name"]: f["volume_change_mm3"] for f in results[exports[0]["component"]].features}


def parity(candidate, reference, name: str, out_dir, **options):
    """Run ``scripts/parity.py compare CANDIDATE REFERENCE --name NAME --out OUT_DIR --samples 0`` from the repository root.
    ``options`` become flags (``candidate_frame=path`` is ``--candidate-frame path``).  Returns ``(exit code, report)``: the
    exit code is 0 pass, 1 differences, 2 unusable input; the report is the parsed ``parity-NAME.json`` or ``None``."""
    out_dir = Path(out_dir)
    command = [sys.executable, str(PARITY), "compare", str(candidate), str(reference), "--name", name, "--out", str(out_dir),
               "--samples", "0"]
    for key, value in options.items():
        command += [f"--{key.replace('_', '-')}", str(value)]
    done = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    report = out_dir / f"parity-{name}.json"
    return done.returncode, (json.loads(report.read_text(encoding="utf-8")) if report.is_file() else None)


def fixture(block: str) -> dict:
    return oracle.load_fixture(oracle.S1_FIXTURE)["blocks"][block]


def oracle_mesh(block: str, out_dir) -> Path:
    """The oracle mesh of an S1 block, rendered once per ``out_dir`` (the caller has called ``oracle.require_openscad()``)."""
    path = Path(out_dir) / f"s1_{block}.stl"
    return path if path.is_file() else oracle.render_s1(block, out_dir)


class BlockRun(NamedTuple):
    """One block through the whole chain: the replay result, its exact measurement, the mesh measurement, the fixture and
    the parity gate (exit code and report)."""

    result: object
    shape: dict
    mesh: dict
    fixture: dict
    code: int
    report: dict


def run_block(block: str, work_dir, facet=None) -> BlockRun:
    """Replay ``block``, render its oracle, and run the parity gate on the two meshes (``facet`` as in ``replay_block``)."""
    work = Path(work_dir)
    label = f"{block}_facet" if facet else block
    result, entry = replay_block(block, work / ("replay-facet" if facet else "replay"), facet)
    mesh_path = work / ("replay-facet" if facet else "replay") / entry["files"][1]
    code, report = parity(mesh_path, oracle_mesh(block, work / "oracle"), label, work / "parity")
    return BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), fixture(block), code, report)


def gate_problems(run: BlockRun) -> list[str]:
    """Where a block misses the thresholds of the architecture brief (E): one solid, valid, one shell; every box corner within
    ``FRAME_TOL`` of the K4a fixture; the replay volume within ``VOLUME_GUARD`` of it (the coarse guard); the parity gate
    passes (no residual piece both above 0.5 mm3 and thicker than 0.05 mm) and the residual is at most ``TOTAL_RESIDUAL``
    of the part.  Empty means pass."""
    problems = []
    shape, fixture_ = run.shape, run.fixture
    if (shape["solids"], shape["shells"], shape["valid"]) != (1, 1, True):
        problems.append(f"replay solids/shells/valid is {(shape['solids'], shape['shells'], shape['valid'])}, not (1, 1, True)")
    if run.result.dead_features:
        problems.append(f"dead features (change no volume): {run.result.dead_features}")
    for corner in ("bbox_min", "bbox_max"):
        worst = max(abs(a - b) for a, b in zip(shape[corner], fixture_[corner]))
        if worst > FRAME_TOL:
            problems.append(f"{corner} differs from the fixture by {worst:.4f} mm (limit {FRAME_TOL})")
    rel = abs(shape["volume_mm3"] - fixture_["volume_mm3"]) / fixture_["volume_mm3"]
    if rel > VOLUME_GUARD:
        problems.append(f"replay volume {shape['volume_mm3']:.3f} against fixture {fixture_['volume_mm3']:.3f} mm3 ({rel:.4%})")
    if run.code != 0 or run.report is None or run.report["verdict"]["status"] != "pass":
        problems.append(f"parity exit code {run.code}, verdict {None if run.report is None else run.report['verdict']}")
    else:
        residual = run.report["residual"]
        if residual["counted_rel"] > TOTAL_RESIDUAL or residual["regions_total"] != 0:
            problems.append(f"residual {residual['counted_rel']:.4%} of the part, {residual['regions_total']} failing region(s)")
    return problems
