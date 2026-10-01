"""C1: the shell of the case master, stages B1, B2, L1 and L2 (issue #81, plan 3.4 and 4, verdict B1 to B5).

The builders of ``cad/fusion/gen/case/shell.py`` run through the facade on the recording backend, the OpenCascade replay executes
the record with the parameter set of the template (``pro-convert-for-ndi-to-hdmi``, configuration ``default``) and the result is
compared with the K4a stage fixtures (``fixtures/s2_stages.json``) and with a fresh oracle mesh: every box corner within 0.02 mm, no
residual piece both above 0.5 mm3 and thicker than 0.05 mm, the residual at most 0.2 % of the part (the thresholds of the brief,
applied by ``s1_support.gate_problems``).  The tests that need the oracle never skip: where OpenSCAD is missing,
``oracle.require_openscad()`` fails them when ``MCC_REQUIRE_OPENSCAD=1`` (CI) and skips them only on a developer machine.
"""
from __future__ import annotations

import functools
import json

import pytest

from cad import params
from cad.fusion.gen.case import build, frame
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.core.names import KitError
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
# (part, component, stage number, stage name): the stages of the shell
STAGES = (("base", "Base", 1, "B1"), ("base", "Base", 2, "B2"), ("lid", "Lid", 1, "L1"), ("lid", "Lid", 2, "L2"))
FEATURES = {
    ("Base", 1): ["Shell_Floor_Body", "Shell_Walls_Add"],
    ("Base", 2): ["Shell_Floor_Body", "Shell_Walls_Add", "Shell_Tongue_RingAdd"],
    ("Lid", 1): ["Shell_Lid_Body"],
    ("Lid", 2): ["Shell_Lid_Body", "Shell_Groove_RingCut"],
}


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _fixture(part: str, name: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][f"{TEMPLATE}.{part}.{name}"]


def _replay(component: str, stage: int):
    """The replay result of ``component`` of the document built up to ``stage``, with the template's parameter set."""
    _, record, rows, sets = _build(stage)
    pset = sets[TEMPLATE]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"], components=[component])[component]


def _export(component: str, stage: int, out_dir):
    document, _, _, _ = _build(stage)
    result = _replay(component, stage)
    exports = [e for c in document["configurations"] if c["id"] == TEMPLATE for e in c["exports"] if e["component"] == component]
    subset = {"configurations": [{"id": TEMPLATE, "exports": exports}]}
    (entry,) = ocp_replay.export({component: result}, subset, TEMPLATE, out_dir)
    return result, entry


def _features(record: dict, component: str) -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == component]


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("component,stage", sorted(FEATURES))
def test_a_stage_records_the_planned_features(component, stage):
    _, record, _, _ = _build(stage)
    assert _features(record, component) == FEATURES[(component, stage)]


def test_the_call_table_has_no_row_12_and_no_stage_9():
    """Issue #87 removed the floor cuts: no floor.cut, no row 12 and no stage 9 in the table."""
    from cad.fusion.gen.case import floor

    assert not hasattr(floor, "cut")
    assert 9 not in {number for _row, number, _fn, _keys in build.CALLS}
    assert 12 not in {row for row, _number, _fn, _keys in build.CALLS}
    assert [row for row, *_ in build.CALLS] == sorted(row for row, *_ in build.CALLS)


def test_the_full_build_of_this_milestone_is_the_shell_of_stage_2():
    """With no stage the document holds the five components and the four shell features (the features of the other owners are theirs)."""
    _, record, _, _ = _build(None)
    assert [(c["name"], c["role"]) for c in record["components"]] == [
        ("Base", "part"), ("Lid", "part"), ("Reserve_FanBay", "reserve"), ("Reserve_SplitterBay", "reserve"),
        ("Ghost_Device", "ghost")]
    assert [n for n in _features(record, "Base") if n.startswith("Shell_")] == FEATURES[("Base", 2)]
    assert [n for n in _features(record, "Lid") if n.startswith("Shell_")] == FEATURES[("Lid", 2)]
    assert [c["builder_id"] for c in record["shared_calls"]] == ["tg.tongue", "tg.groove"]


def test_the_tongue_and_the_groove_take_the_same_rectangle():
    _, record, _, _ = _build(2)
    tongue, groove = record["shared_calls"]
    for key in ("x0", "x1", "y0", "y1"):
        assert tongue["arguments"][key] == groove["arguments"][key]
    assert tongue["arguments"]["y1"] == frame.YTG and tongue["arguments"]["x0"] == frame.XIL
    assert tongue["placement"] == groove["placement"] == ["x0", "x1", "y0", "y1", "z"]


def test_a_stage_is_a_whole_number_of_at_least_one():
    for bad in (0, -1, "B1", 1.5, True):
        with pytest.raises(KitError, match="stage"):
            build._stage({"stage": bad})
    assert build._stage({}) is None and build._stage({"stage": 3}) == 3


def test_the_shell_names_the_frozen_anchors():
    from cad.fusion.gen.core import names

    for feature in ("Shell_Floor_Body", "Shell_Walls_Add", "Shell_Lid_Body"):
        assert any(pattern.fullmatch(feature) for pattern in names.ANCHORS)


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay equals the committed fixture (no OpenSCAD needed)
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("part,component,stage,name", STAGES)
def test_the_replay_matches_the_committed_fixture(part, component, stage, name, tmp_path):
    result = _replay(component, stage)
    shape, fixture = ocp_replay.measure(result.shape), _fixture(part, name)
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    assert result.dead_features == []
    for corner in ("bbox_min", "bbox_max"):
        worst = max(abs(a - b) for a, b in zip(shape[corner], fixture[corner]))
        assert worst <= s1_support.FRAME_TOL, f"{name} {corner} differs from the fixture by {worst:.4f} mm"
    assert shape["volume_mm3"] == pytest.approx(fixture["volume_mm3"], rel=s1_support.VOLUME_GUARD)


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against a fresh oracle mesh and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("case_shell")


@pytest.mark.parametrize("part,component,stage,name", STAGES)
def test_a_stage_replays_to_its_oracle(part, component, stage, name, work):
    oracle.require_openscad()
    result, entry = _export(component, stage, work / f"replay-{name}")
    mesh_path = work / f"replay-{name}" / entry["files"][1]
    reference = oracle.render_s2(TEMPLATE, part, stage, work / "oracle")
    code, report = s1_support.parity(mesh_path, reference, name, work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), _fixture(part, name), code, report)
    assert s1_support.gate_problems(run) == []
