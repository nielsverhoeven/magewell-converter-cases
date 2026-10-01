"""C2: the lid fasteners of the case master, stages B3 and L3 (issue #81, plan 3.4 and 4, verdict A2, D81.5, D81.6).

The builders of ``cad/fusion/gen/case/lidfast.py`` run through the facade on the recording backend, the OpenCascade replay
executes the record with the parameter set of the template (``pro-convert-for-ndi-to-hdmi``, configuration ``default``) and the
result is compared with the K4a stage fixtures (``fixtures/s2_stages.json``) and with a fresh oracle mesh, within the thresholds of
the brief (``s1_support.gate_problems``).  Stages are cumulative: stage 3 of the document is the shell (stages 1 and 2) plus the
lid fasteners, which is exactly what the fixture B3 and L3 hold.  The tests that need the oracle never skip.
"""
from __future__ import annotations

import functools
import json
import math

import pytest

from cad import params
from cad.fusion.gen.case import frame, lidfast
from cad.fusion.gen.core import expr
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
STAGES = (("base", "Base", 3, "B3"), ("lid", "Lid", 3, "L3"))
SETS = ("Corners", "PatchMid", "FarMid")
FASTENER_BASE = ["Fastener_Corners_BossAdd", "Fastener_PatchMid_BossAdd", "Fastener_FarMid_BossAdd",
                 "Fastener_Corners_WebAdd", "Fastener_PatchMid_WebAdd", "Fastener_FarMid_WebAdd",
                 "Fastener_Corners_BoreCut", "Fastener_PatchMid_BoreCut", "Fastener_FarMid_BoreCut"]
FASTENER_LID = ["Fastener_Corners_ShaftCut", "Fastener_Corners_Cone1Cut", "Fastener_Corners_Cone2Cut",
                "Fastener_Corners_Cone3Cut", "Fastener_Corners_Cone4Cut",
                "Fastener_PatchMid_ShaftCut", "Fastener_PatchMid_Cone1Cut", "Fastener_FarMid_ShaftCut", "Fastener_FarMid_Cone1Cut"]
BASE_FEATURES = ["Shell_Floor_Body", "Shell_Walls_Add", "Shell_Tongue_RingAdd", *FASTENER_BASE]
LID_FEATURES = ["Shell_Lid_Body", "Shell_Groove_RingCut", *FASTENER_LID]


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _fixture(part: str, name: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][f"{TEMPLATE}.{part}.{name}"]


def _env(stage=3):
    """The record, the parameter set of the template and its numbers (the template's configuration)."""
    _, record, rows, sets = _build(stage)
    pset = sets[TEMPLATE]
    return record, pset, expr.Env(rows, pset["values"])


def _replay(component: str, stage: int):
    record, pset, _ = _env(stage)
    _, _, rows, _ = _build(stage)
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"], components=[component])[component]


def _export(component: str, stage: int, out_dir):
    document, _, _, _ = _build(stage)
    result = _replay(component, stage)
    exports = [e for c in document["configurations"] if c["id"] == TEMPLATE for e in c["exports"] if e["component"] == component]
    (entry,) = ocp_replay.export({component: result}, {"configurations": [{"id": TEMPLATE, "exports": exports}]}, TEMPLATE, out_dir)
    return result, entry


def _features(record: dict, component: str) -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == component]


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

def test_stage_3_records_the_planned_features():
    _, record, _, _ = _build(3)
    assert _features(record, "Base") == BASE_FEATURES
    assert _features(record, "Lid") == LID_FEATURES


def test_the_full_build_has_the_same_lid_fastener_features():
    """No stage: the stubs of the other milestones add nothing to the lid fasteners."""
    _, record, _, _ = _build(None)
    assert [n for n in _features(record, "Base") if n.startswith("Fastener_")] == FASTENER_BASE
    assert [n for n in _features(record, "Lid") if n.startswith("Fastener_")] == FASTENER_LID


def test_the_shared_builders_are_called_once_per_set_in_the_order_of_the_phases():
    _, record, _, _ = _build(3)
    calls = [c for c in record["shared_calls"] if c["builder_id"].startswith("fasteners.")]
    assert [c["builder_id"] for c in calls] == (["fasteners.heat_set_boss"] * 3 + ["fasteners.insert_bore"] * 3
                                                + ["fasteners.lid_screw_hole"] * 3)
    assert [c["produced"][0].split("_")[1] for c in calls] == list(SETS) * 3


def test_the_phase_order_of_the_base_is_joins_then_cuts():
    _, record, _, _ = _build(3)
    ops = [s["op"] for s in record["specs"] if s["spec"] == "ExtrudeSpec" and s["component"] == "Base"]
    # floor body; walls, tongue, 3 bosses and 3 webs; 3 bores
    assert ops == ["new"] + ["join"] * 8 + ["cut"] * 3


def test_every_boss_set_has_one_boss_one_web_and_one_bore_per_fastener():
    _, record, _, _ = _build(3)
    sketches = {s["name"]: s for s in record["specs"] if s["spec"] == "SketchSpec"}
    specs = {s["name"]: s for s in record["specs"]}
    for name, count in {"Corners": 4, "PatchMid": 1, "FarMid": 1}.items():
        for what, kind in (("BossAdd", "circle"), ("WebAdd", "polygon"), ("BoreCut", "circle")):
            loops = sketches[specs[f"Fastener_{name}_{what}"]["sketch"]]["loops"]
            assert [loop["kind"] for loop in loops] == [kind] * count, f"{name} {what}"
    cones = [n for n in LID_FEATURES if n.endswith("Cut") and "Cone" in n]
    assert all(specs[n]["spec"] == "LoftSpec" and specs[n]["op"] == "cut" for n in cones)


def test_the_names_carry_the_frozen_anchors_and_the_flags_of_the_two_mid_sets():
    from cad.fusion.gen.core import names

    for name in SETS:
        for what in ("BossAdd", "WebAdd"):
            assert any(p.fullmatch(f"Fastener_{name}_{what}") for p in names.ANCHORS)
    _, _, _, sets = _build(3)
    flags = set(sets["_build"]["suppress"])
    assert {"Fastener_PatchMid", "Fastener_FarMid"} <= flags and "Fastener_Corners" not in flags


def test_the_centres_are_the_plan_expressions():
    expected = {"Corners": [(frame.FX, frame.FY), (frame.FX, expr.neg(frame.FY)), (expr.neg(frame.FX), frame.FY),
                            (expr.neg(frame.FX), expr.neg(frame.FY))],
                "PatchMid": [("V_FAST_PATCH_MID_X", frame.FY)], "FarMid": [("V_FAST_FAR_MID_X", expr.neg(frame.FY))]}
    assert {name: list(centres) for name, centres in lidfast.SETS} == expected
    _, record, _, _ = _build(3)
    by_id = {}
    for call in record["shared_calls"]:
        by_id.setdefault(call["builder_id"], []).append(call["arguments"])
    assert all((a["z0"], a["z1"], a["d"]) == (frame.FT, frame.ZT, "V_BOSS_D") for a in by_id["fasteners.heat_set_boss"])
    assert all((a["z_open"], a["depth"], a["d"]) == (frame.ZT, "V_INSERT_DEPTH", "V_INSERT_HOLE_D")
               for a in by_id["fasteners.insert_bore"])
    assert all((a["z0"], a["z1"], a["shaft_d"], a["csk_d"], a["angle"]) == (
        frame.ZT, frame.ZLID, "MCC_M3_CLR_D", "MCC_LID_CSK_D", "MCC_LID_CSK_ANGLE") for a in by_id["fasteners.lid_screw_hole"])


def test_the_web_points_follow_the_plan_for_every_direction():
    _, _, env = _env()
    tu, tv = env.value("V_WEB_TAN_U"), env.value("V_WEB_TAN_V")
    r = env.value("MCC_FASTENER_INSET") - env.value("MCC_WEB_FACE_MARGIN")
    b = env.value("V_BOSS_D") / 2
    local = [(tu, tv), (r, b), (r, -b), (tu, -tv)]
    cx, cy = 10.0, 20.0
    for direction, make in (("+X", lambda u, v: (cx + u, cy + v)), ("-X", lambda u, v: (cx - u, cy + v)),
                            ("+Y", lambda u, v: (cx + v, cy + u)), ("-Y", lambda u, v: (cx + v, cy - u))):
        points = lidfast.web_points("10 mm", "20 mm", direction)
        got = [(env.value(x), env.value(y)) for x, y in points]
        assert got == pytest.approx([make(u, v) for u, v in local]), direction
    with pytest.raises(ValueError, match="direction"):
        lidfast.web_points(None, None, "up")


def test_the_web_reaches_into_its_wall_and_stops_short_of_the_outer_face():
    """The web's bar lies inside the wall's thickness and short of the outer face: it shares volume with its target (D81.5)."""
    _, _, env = _env()
    reach = env.value("MCC_FASTENER_INSET") - env.value("MCC_WEB_FACE_MARGIN")
    assert env.value("MCC_FASTENER_INSET") - env.value("MCC_WALL") < reach < env.value("MCC_FASTENER_INSET")


def test_the_countersink_leaves_the_land_the_constants_demand():
    _, _, env = _env()
    depth = ((env.value("MCC_LID_CSK_D") - env.value("MCC_M3_CLR_D")) / 2
             / math.tan(math.radians(env.value("MCC_LID_CSK_ANGLE")) / 2))
    assert env.value("MCC_LID_T") - depth >= env.value("MCC_LID_CSK_LAND_MIN")


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay equals the committed fixture (no OpenSCAD needed)
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("part,component,stage,name", STAGES)
def test_the_replay_matches_the_committed_fixture(part, component, stage, name):
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
    return tmp_path_factory.mktemp("case_lidfast")


@pytest.mark.parametrize("part,component,stage,name", STAGES)
def test_a_stage_replays_to_its_oracle(part, component, stage, name, work):
    oracle.require_openscad()
    result, entry = _export(component, stage, work / f"replay-{name}")
    mesh_path = work / f"replay-{name}" / entry["files"][1]
    reference = oracle.render_s2(TEMPLATE, part, stage, work / "oracle")
    code, report = s1_support.parity(mesh_path, reference, name, work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), _fixture(part, name), code, report)
    assert s1_support.gate_problems(run) == []
