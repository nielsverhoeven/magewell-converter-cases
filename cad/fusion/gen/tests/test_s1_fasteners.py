"""SH1: the S1 blocks of ``shared/fasteners.py`` (issue #81, plan 5.3 and 7, verdict A11, #100): ``heat_set_boss`` (with its bore),
``lid_screw_hole`` (the 90 degree countersink; its cone is a loft cut) and ``side_bolt`` (boss, web and the three bores).

Same chain as ``test_s1_tg``: recorded through the facade, plan checks, OpenCascade replay, K4a fixture, fresh oracle mesh, parity
gate.  The round features are exact circles in the replay and 64-gons (circumscribed) in the oracle, so their residual is a set of
slivers a few micrometres thick; the side-bolt block adds the two wedges of D81.5 (see ``test_the_side_bolt_residual_...``).
No test skips: ``oracle.require_openscad()`` fails them under ``MCC_REQUIRE_OPENSCAD=1`` and skips only where OpenSCAD is missing.
"""
from __future__ import annotations

import math

import pytest

from cad.fusion.gen.core import expr
from cad.fusion.gen.shared import fasteners
from cad.fusion.gen.tests import oracle, s1_support

BLOCKS = ("heat_set_boss", "lid_screw_hole", "side_bolt")
# M3 insert: boss d = 1.8 * 4.6, bore d = 4, depth = 5.7 + 1; lid hole: shaft 3.4, countersink 6.72 + 2 * 0.3 = 7.32 at 90 degrees
BOSS_R, BORE_R, BORE_DEPTH = 1.8 * 4.6 / 2, 2.0, 5.7 + 1.0
SHAFT_R, CSK_R, LID_T = 1.7, 7.32 / 2, 3.0


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("s1_fasteners")


def fastener_calls() -> list:
    record, _, _ = s1_support.build_record()
    return [c for c in record["shared_calls"] if c["builder_id"].startswith("fasteners.")]


def csk_removed(count: int = 1) -> float:
    """The volume the lid hole removes from a lid ``LID_T`` thick, in closed form: the shaft plus the cone beyond the shaft."""
    depth = (CSK_R - SHAFT_R)  # a 90 degree countersink: the radius grows by 1 mm per mm of depth
    shaft = math.pi * SHAFT_R ** 2 * LID_T
    cone = math.pi * depth / 3 * (CSK_R ** 2 + CSK_R * SHAFT_R + SHAFT_R ** 2) - math.pi * SHAFT_R ** 2 * depth
    return count * (shaft + cone)


def test_the_plan_checks_find_nothing():
    assert [str(f) for f in s1_support.findings()] == []


def test_each_block_is_recorded_as_the_calls_of_its_builders():
    calls = fastener_calls()
    assert [c["builder_id"] for c in calls] == [
        "fasteners.heat_set_boss", "fasteners.side_bolt_boss",  # the add phase
        "fasteners.insert_bore", "fasteners.lid_screw_hole", "fasteners.side_bolt_cut"]  # the cut phase
    placement = {c["builder_id"]: c["placement"] for c in calls}
    assert placement["fasteners.heat_set_boss"] == ["centres", "z0", "z1"]
    assert placement["fasteners.insert_bore"] == ["centres", "z_open"]
    assert placement["fasteners.lid_screw_hole"] == ["centres", "z0", "z1"]
    assert placement["fasteners.side_bolt_boss"] == ["x", "z", "y_face", "web_y0", "web_z0"]
    assert placement["fasteners.side_bolt_cut"] == ["x", "z", "y_face", "pocket_y0"]
    produced = {c["builder_id"]: [n for n in c["produced"] if not n.endswith(("Sk", "SkA", "SkB", "PlA", "PlB"))] for c in calls}
    assert produced == {
        "fasteners.heat_set_boss": ["Fastener_Boss_BossAdd"],
        "fasteners.insert_bore": ["Fastener_Boss_BoreCut"],
        "fasteners.lid_screw_hole": ["Fastener_Lid_ShaftCut", "Fastener_Lid_Cone1Cut"],
        "fasteners.side_bolt_boss": ["SideBolt_Boss_CylAdd", "SideBolt_Boss_WebAdd"],
        "fasteners.side_bolt_cut": ["SideBolt_Bore_HeadCut", "SideBolt_Bore_ShankCut", "SideBolt_Bore_PocketCut"]}


def test_the_countersink_cone_is_a_loft_cut_between_two_circles():
    record, _, _ = s1_support.build_record()
    specs = {s["name"]: s for s in record["specs"]}
    cone = specs["Fastener_Lid_Cone1Cut"]
    assert (cone["spec"], cone["op"], len(cone["sketches"]), len(cone["planes"])) == ("LoftSpec", "cut", 2, 2)
    a, b = (specs[n] for n in cone["sketches"])
    assert [loop["kind"] for loop in (*a["loops"], *b["loops"])] == ["circle", "circle"]
    assert (a["loops"][0]["args"][2], b["loops"][0]["args"][2]) == ("MCC_M3_CLR_D", "MCC_LID_CSK_D")
    # the cone's small section is one depth below the lid's outward face, where depth = (csk_d - d) / 2 / tan(angle / 2)
    kit = s1_support.new_kit()
    offsets = [kit.env.value(specs[n]["offset"]) for n in cone["planes"]]
    assert offsets == pytest.approx([LID_T - (CSK_R - SHAFT_R), LID_T], abs=1e-9)
    assert "tan(MCC_LID_CSK_ANGLE / 2)" in specs[cone["planes"][0]]["offset"]


def test_the_boss_and_its_bore_are_cylinders_of_the_closed_form_volume():
    changes = s1_support.block_features("heat_set_boss")
    assert changes["Fastener_Boss_BossAdd"] == pytest.approx(math.pi * BOSS_R ** 2 * 10.0, rel=1e-6)
    assert changes["Fastener_Boss_BoreCut"] == pytest.approx(-math.pi * BORE_R ** 2 * BORE_DEPTH, rel=1e-6)


def test_the_lid_hole_removes_the_shaft_and_the_cone_beyond_it():
    changes = s1_support.block_features("lid_screw_hole")
    assert changes["Fastener_Lid_ShaftCut"] + changes["Fastener_Lid_Cone1Cut"] == pytest.approx(-csk_removed(), rel=1e-6)


def lid_tile_with_two_holes():
    kit = s1_support.new_kit()
    comp = kit.component("S1_LidScrewHole", role="part", datum=("-T_LID / 2", "-T_LID / 2", None))
    comp.extrude("Block_Lid_Body", axis="Z", loops=[comp.rect("-T_LID / 2", "T_LID / 2", "-T_LID / 2", "T_LID / 2")], start=None,
                 end="MCC_LID_T", op="new")
    names = fasteners.lid_screw_hole(comp, "Lid", centres=[("-T_LID / 4", None), ("T_LID / 4", None)], z0=None, z1="MCC_LID_T",
                                     shaft_d="MCC_M3_CLR_D", csk_d="MCC_LID_CSK_D", angle="MCC_LID_CSK_ANGLE")
    return kit, names


def test_several_centres_are_one_shaft_feature_and_one_cone_loft_each():
    kit, names = lid_tile_with_two_holes()
    assert names == ["Fastener_Lid_ShaftCut", "Fastener_Lid_Cone1Cut", "Fastener_Lid_Cone2Cut"]
    result = s1_support.replay_kit(kit, "S1_LidScrewHole")
    assert result.dead_features == []
    assert ocp_volume(result) == pytest.approx(20 * 20 * LID_T - csk_removed(2), rel=1e-6)


def test_several_boss_centres_are_one_sketch_and_one_feature():
    kit = s1_support.new_kit()
    comp = kit.component("S1_HeatSetBoss", role="part", datum=("-T_BOSS_PLATE / 2", "-T_BOSS_PLATE / 2", None))
    comp.extrude("Block_Boss_Body", axis="Z", loops=[comp.rect("-T_BOSS_PLATE / 2", "T_BOSS_PLATE / 2", "-T_BOSS_PLATE / 2",
                                                                "T_BOSS_PLATE / 2")], start=None, end="MCC_FLOOR_T", op="new")
    centres = [("-T_BOSS_PLATE / 4", None), ("T_BOSS_PLATE / 4", None)]
    fasteners.heat_set_boss(comp, "Boss", centres=centres, z0="MCC_FLOOR_T", z1="MCC_FLOOR_T + T_BOSS_H",
                            d="MCC_BOSS_MIN_RATIO * MCC_INSERT_M3_OD")
    fasteners.insert_bore(comp, "Boss", centres=centres, z_open="MCC_FLOOR_T + T_BOSS_H",
                          depth="MCC_INSERT_M3_LEN + MCC_INSERT_BORE_OVERDEPTH", d="MCC_INSERT_M3_HOLE_D")
    sketches = [s for s in kit._backend.timeline if type(s).__name__ == "SketchSpec" and s.name.startswith("Fastener_Boss_")]
    assert [(s.name, len(s.loops)) for s in sketches] == [("Fastener_Boss_BossAddSk", 2), ("Fastener_Boss_BoreCutSk", 2)]
    result = s1_support.replay_kit(kit, "S1_HeatSetBoss")
    assert ocp_volume(result) == pytest.approx(20 * 20 * 3 + 2 * math.pi * (BOSS_R ** 2 * 10 - BORE_R ** 2 * BORE_DEPTH), rel=1e-6)


def ocp_volume(result) -> float:
    from cad.fusion.replay import ocp_replay

    return ocp_replay.measure(result.shape)["volume_mm3"]


def test_the_side_bolt_web_runs_up_to_the_bolt_axis_and_is_a_join_that_shares_volume():
    # D81.5: a join shares volume or a face with its target, never only a line.  The oracle's web ends at the boss underside
    # (a line contact at x = 0); this one ends at the axis, inside the cylinder.
    record, _, _ = s1_support.build_record()
    specs = {s["name"]: s for s in record["specs"]}
    web, cyl = specs["SideBolt_Boss_WebAdd"], specs["SideBolt_Boss_CylAdd"]
    assert (web["op"], cyl["op"]) == ("join", "join")
    assert web["distance"] == "MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T"
    kit = s1_support.new_kit()
    top = kit.env.value("MCC_FLOOR_T") + kit.env.value(web["distance"])
    axis, radius = kit.env.value("MCC_SIDE_BOLT_AXIS_Z"), kit.env.value("MCC_SIDE_BOLT_BOSS_OD") / 2
    assert top == pytest.approx(axis)
    assert axis - radius < top  # the web's top is inside the boss cylinder's z range: shared volume


def test_a_dimension_that_is_a_number_or_a_literal_is_refused():
    kit = s1_support.new_kit()
    comp = kit.component("S1_HeatSetBoss", role="part", datum=(None, None, None))
    comp.extrude("Block_Boss_Body", axis="Z", loops=[comp.rect("MCC_WALL", "T_BOSS_PLATE", "MCC_WALL", "T_BOSS_PLATE")], start=None,
                 end="MCC_FLOOR_T", op="new")
    with pytest.raises(expr.LiteralError):
        fasteners.heat_set_boss(comp, "Boss", centres=[("T_BOSS_PLATE / 2", "T_BOSS_PLATE / 2")], z0="MCC_FLOOR_T",
                                z1="MCC_FLOOR_T + T_BOSS_H", d="8.28 mm")
    with pytest.raises(TypeError):
        fasteners.heat_set_boss(comp, "Boss", centres=[("T_BOSS_PLATE / 2", "T_BOSS_PLATE / 2")], z0="MCC_FLOOR_T",
                                z1="MCC_FLOOR_T + T_BOSS_H", d=8.28)


@pytest.mark.parametrize("block", BLOCKS)
def test_a_block_replays_to_its_oracle(block, work):
    oracle.require_openscad()
    run = s1_support.run_block(block, work)
    assert s1_support.gate_problems(run) == []


def test_the_side_bolt_residual_is_the_two_web_wedges_and_nothing_else(work):
    """Verdict A11: with the circles of the replay cut into the oracle's 64-gons (``--facet``, a diagnostic that isolates what is
    not a facet effect), the side-bolt block differs from the oracle in exactly two pieces above 0.5 mm3, each below 0.7 mm3.
    They are the wedges between the web's flat top and the boss cylinder (D81.5); both are thinner than 0.05 mm, so the gate
    passes, and nothing is missing from the candidate."""
    oracle.require_openscad()
    run = s1_support.run_block("side_bolt", work, facet=64)
    assert run.code == 0 and run.report["verdict"]["status"] == "pass"
    extra, missing = run.report["residual"]["sub_threshold"]["extra"], run.report["residual"]["sub_threshold"]["missing"]
    assert extra["pieces"] == extra["large_but_thin"] == 2
    assert 0.5 < extra["max_piece_volume_mm3"] < 0.7
    assert extra["max_thickness_mm"] < 0.05
    assert missing["pieces"] == 0
    assert run.report["residual"]["extra_volume_mm3"] == pytest.approx(2 * extra["max_piece_volume_mm3"], rel=1e-2)
