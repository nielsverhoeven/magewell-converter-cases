"""C4: the floor of the case master, stage B5 (issue #81, plan 3.4 and 4, verdict A2, A8, D81.5, D81.11; issue #87).

The builders of ``cad/fusion/gen/case/floor.py`` (the sill block, the insertion passage, and the female rail through the shared
builder) run through the facade on the recording backend; the OpenCascade replay executes the record with the parameter set of
the template (``pro-convert-for-ndi-to-hdmi``, configuration ``default``) and the result is compared with a fresh oracle mesh,
within the thresholds of the brief (``s1_support.gate_problems``).

Stage B5 of the K4a fixture is cumulative and holds the cradle (B4), which milestone C3 builds; with C3 on main the comparison is
the stock stage render and the stock fixture B5.  Tests never skip: ``oracle.require_openscad()`` fails them under
``MCC_REQUIRE_OPENSCAD=1``.
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

import pytest

from cad import params
from cad.fusion.gen.case import build, floor, frame
from cad.fusion.gen.core import checks, expr, names
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
CRADLE = ["Cradle_Deck_FrameAdd", "Cradle_Deck_RibXAdd", "Cradle_Deck_RibXPat", "Cradle_Deck_RibYAdd", "Cradle_Deck_RibYPat",
          *(f"Cradle_FarRib{i}_ProfileAdd" for i in (1, 2, 3, 4, 5))]
FLOOR_FEATURES = ["Floor_RailSill_BlockAdd", "Floor_RailSill_PassageAdd", "Rail_Female_BackingAdd",
                  "Rail_Female_GrooveCut", "Rail_Female_LockSlotCut", "Rail_Female_LeadInCut"]
BASE_FEATURES = ["Shell_Floor_Body", "Shell_Walls_Add", "Shell_Tongue_RingAdd",
                 "Fastener_Corners_BossAdd", "Fastener_PatchMid_BossAdd", "Fastener_FarMid_BossAdd",
                 "Fastener_Corners_WebAdd", "Fastener_PatchMid_WebAdd", "Fastener_FarMid_WebAdd", *CRADLE,
                 "Floor_RailSill_BlockAdd", "Floor_RailSill_PassageAdd", "Rail_Female_BackingAdd",
                 "Fastener_Corners_BoreCut", "Fastener_PatchMid_BoreCut", "Fastener_FarMid_BoreCut",
                 "Rail_Female_GrooveCut", "Rail_Female_LockSlotCut", "Rail_Female_LeadInCut"]


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _fixture(name: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][f"{TEMPLATE}.base.{name}"]


def _env(stage=5):
    _, _, rows, sets = _build(stage)
    pset = sets[TEMPLATE]
    return expr.Env(rows, pset["values"])


def _replay(stage=5, suppress=None):
    _, record, rows, sets = _build(stage)
    pset = sets[TEMPLATE]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"] if suppress is None else suppress, components=["Base"])["Base"]


def _features(record: dict, component: str = "Base") -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == component]


def _spec(record: dict, name: str) -> dict:
    return next(s for s in record["specs"] if s["name"] == name)


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

def test_stage_5_records_the_planned_features_in_the_order_of_the_phases():
    _, record, _, _ = _build(5)
    assert _features(record) == BASE_FEATURES
    ops = {s["name"]: s["op"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec") and s["component"] == "Base"}
    assert [ops[n] for n in FLOOR_FEATURES] == ["join"] * 3 + ["cut"] * 3
    # the other milestones add nothing to the floor: compare the features of the shell, the lid fasteners, the cradle and the floor (C5 added
    # the side bolt and the patch wall to the full build)
    assert [n for n in _features(_build(None)[1]) if n.split("_")[0] in ("Shell", "Fastener", "Cradle", "Floor", "Rail")] == BASE_FEATURES


def test_there_is_no_floor_cut_and_no_stage_9():
    """Issue #87: no strap pockets and no stacking recesses; the floor has the two functions of stage 5 and nothing else."""
    assert not hasattr(floor, "cut")
    assert [c for c in (floor.add, floor.cut_rail)] == [fn for _row, number, fn, _keys in build.CALLS
                                                          if fn.__module__ == floor.__name__ and number == 5]
    _, record, _, _ = _build(None)
    assert not [n for n in _features(record) if n.startswith(("Floor_Strap", "Floor_Stack"))]


def test_floor_is_the_only_caller_of_the_rail_builder_and_the_rail_features_are_the_builders():
    _, record, _, _ = _build(5)
    calls = [c for c in record["shared_calls"] if c["builder_id"].startswith("rail.")]
    assert [c["builder_id"] for c in calls] == ["rail.female_backing", "rail.female_cut"]
    produced = {n for c in calls for n in c["produced"]}
    assert {n for n in _features(record) if n.startswith("Rail_")} == {"Rail_Female_BackingAdd", "Rail_Female_GrooveCut",
                                                                         "Rail_Female_LockSlotCut", "Rail_Female_LeadInCut"}
    assert {n for n in _features(record) if n.startswith("Rail_")} <= produced
    callers = [p.name for p in sorted(Path(floor.__file__).parent.glob("*.py")) if "shared import" in p.read_text(encoding="utf-8")
               and re.search(r"import[^\n]*\brail\b", p.read_text(encoding="utf-8"))]
    assert callers == ["floor.py"]


def test_the_shared_calls_take_the_plan_arguments():
    _, record, _, _ = _build(5)
    backing, cut = (c for c in record["shared_calls"] if c["builder_id"].startswith("rail."))
    assert backing["arguments"] == {"x_mid": None, "y_mid": "MCC_RAIL_Y", "z_sill": "MCC_RAIL_SILL_H",
                                    "length": "MCC_RAIL_LEN"}
    assert cut["arguments"] == {"x_mid": None, "y_mid": "MCC_RAIL_Y", "z0": None, "length": "MCC_RAIL_LEN",
                                "x_open": frame.XH, "lead_in": True}
    assert backing["placement"] == ["x_mid", "y_mid", "z_sill"] and cut["placement"] == ["x_mid", "y_mid", "z0", "x_open"]


def test_the_two_rail_flags_are_in_the_build_configuration():
    _, _, _, sets = _build(5)
    assert {"Floor_RailSill", "Rail_Female"} <= set(sets["_build"]["suppress"])


def test_the_two_rail_flags_are_equal_in_every_parameter_set():
    """T1-81.1: ``rail`` is one option; its two flags never differ."""
    for path in sorted((s1_support.REPO / "cad" / "parameters" / "variants").glob("*.json")):
        for config, doc in json.loads(path.read_text(encoding="utf-8"))["configurations"].items():
            assert doc["flags"]["Floor_RailSill"] == doc["flags"]["Rail_Female"], f"{path.stem}/{config}"


def test_the_plan_checks_find_no_finding_of_the_floor_milestone():
    document, record, rows, sets = _build(5)
    findings = checks.run(record, rows, sets, document.get("shared_exceptions", []), owners=document["owners"],
                          protected_prefixes=document["protected_prefixes"])
    assert not [str(f) for f in findings if f.id != "CK4"]
    assert not {f.name for f in findings} & {"Floor_RailSill", "Rail_Female"}   # both flags have members


def test_the_sill_geometry_follows_the_plan():
    env = _env()
    half = env.value("MCC_RAIL_LEN") / 2 + env.value("MCC_RAIL_END_WALL")
    sw = env.value("MCC_RAIL_ROOT_W") / 2 + env.value("MCC_RAIL_SILL_SIDE_W")
    y = env.value("MCC_RAIL_Y")
    inner = env.value("V_CASE_L") / 2 - env.value("MCC_WALL")
    _, record, _, _ = _build(5)
    sketches = {s["name"]: s for s in record["specs"] if s["spec"] == "SketchSpec"}
    block, passage = (_spec(record, n) for n in ("Floor_RailSill_BlockAdd", "Floor_RailSill_PassageAdd"))

    def box(spec):
        (loop,) = sketches[spec["sketch"]]["loops"]
        assert loop["kind"] == "rect"
        return [env.value(a) for a in loop["args"]]
    assert box(block) == pytest.approx([-half, half, y - sw, y + sw])
    assert box(passage) == pytest.approx([half, inner, y - sw, y + sw])
    # D81.5: both rise from the exterior face (start None) and the passage touches the sill's plus X face and the inner wall face
    assert block["start_offset"] is None and passage["start_offset"] is None
    assert half < inner < env.value("V_CASE_L") / 2
    assert env.value(block["distance"]) == env.value("MCC_RAIL_SILL_H") > env.value("MCC_FLOOR_T")   # shares volume with the slab
    # the passage is capped by the fan-bay reservation above it and its roof stays at least the minimum (D34, T1-38)
    assert env.value(passage["distance"]) == min(env.value("MCC_RAIL_SILL_H"), env.value("V_FANBAY_Z_LO"))
    assert env.value(passage["distance"]) - env.value("MCC_RAIL_DEPTH") >= env.value("MCC_RAIL_PASSAGE_ROOF_MIN") - 1e-9


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay against the committed fixture and the rail's flags
# --------------------------------------------------------------------------------------------------------------

def test_the_replay_has_no_dead_feature_and_the_box_of_the_committed_fixture():
    result = _replay()
    shape, fixture = ocp_replay.measure(result.shape), _fixture("B5")
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    assert result.dead_features == []
    for corner in ("bbox_min", "bbox_max"):
        worst = max(abs(a - b) for a, b in zip(shape[corner], fixture[corner]))
        assert worst <= s1_support.FRAME_TOL, f"B5 {corner} differs from the fixture by {worst:.4f} mm"


def test_the_floor_features_change_the_volume_in_the_planned_direction():
    changes = {f["name"]: f["volume_change_mm3"] for f in _replay().features}
    assert all(changes[n] > 0 for n in FLOOR_FEATURES[:3]) and all(changes[n] < 0 for n in FLOOR_FEATURES[3:])


def test_suppressing_the_two_rail_flags_removes_every_floor_feature():
    """The option ``rail = false`` of the oracle: no sill, no passage, no backing, no groove (the bare configuration)."""
    _, _, _, sets = _build(5)
    off = _replay(suppress={**sets[TEMPLATE]["suppress"], "Floor_RailSill": True, "Rail_Female": True})
    on = _replay()
    assert off.dead_features == []
    # the fifth far-flank rib is suppressed in the template as well (its flag is set in every real configuration)
    assert {f["name"] for f in off.features if f["suppressed"]} == set(FLOOR_FEATURES) | {"Cradle_FarRib5_ProfileAdd"}
    assert ocp_replay.measure(off.shape)["volume_mm3"] != pytest.approx(ocp_replay.measure(on.shape)["volume_mm3"], rel=1e-3)


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against the stage oracle, and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("case_floor")


def test_stage_5_replays_to_its_oracle(work):
    oracle.require_openscad()
    document, _, _, _ = _build(5)
    result = _replay()
    exports = [e for c in document["configurations"] if c["id"] == TEMPLATE for e in c["exports"] if e["component"] == "Base"]
    (entry,) = ocp_replay.export({"Base": result}, {"configurations": [{"id": TEMPLATE, "exports": exports}]}, TEMPLATE,
                                 work / "replay-B5")
    mesh_path = work / "replay-B5" / entry["files"][1]
    reference = oracle.render_s2(TEMPLATE, "base", 5, work / "oracle")
    code, report = s1_support.parity(mesh_path, reference, "B5", work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), _fixture("B5"), code, report)
    assert s1_support.gate_problems(run) == []
