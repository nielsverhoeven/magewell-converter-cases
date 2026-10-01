"""SH3: the S1 blocks of ``shared/rail.py`` (issue #81, plan 3.10, 5.3 and 7, verdicts A5, A6, A10 and D81.11): ``rail_male`` and
``rail_female``.

Same chain as ``test_s1_tg``: recorded through the facade, plan checks (CK11: every ``Rail_*`` object comes from a ``rail.*`` call),
OpenCascade replay, K4a fixture, fresh oracle mesh, parity gate.  The female block's oracle mesh carries two zero-area triangles
(plan 2.5.3); its residual is the 0.03 mm3 the loft differs from the oracle's ``hull()`` plus facet noise of the sloped faces.
No test skips: ``oracle.require_openscad()`` fails them under ``MCC_REQUIRE_OPENSCAD=1`` and skips only where OpenSCAD is missing.
"""
from __future__ import annotations

import math

import pytest

from cad.fusion.gen.core import checks, expr
from cad.fusion.gen.shared import rail
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

BLOCKS = ("rail_male", "rail_female")
ROOT_W, DEPTH, CLR, MALE_H, SIDE_W, WALL, FLOOR_T = 65.0, 4.0, 0.5, 3.5, 3.0, 3.0, 3.0
TAN60 = math.tan(math.radians(60))
MOUTH_W = ROOT_W - 2 * DEPTH / TAN60
K = (ROOT_W - MOUTH_W) / (2 * DEPTH)
LEN = 60.0


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("s1_rail")


def rail_calls() -> list:
    record, _, _ = s1_support.build_record()
    return [c for c in record["shared_calls"] if c["builder_id"].startswith("rail.")]


def real_names(call: dict) -> list:
    return [n for n in call["produced"] if not n.endswith(("Sk", "SkA", "SkB", "PlA", "PlB"))]


def strip_volume(e: float) -> float:
    """One lock strip: 2 mm of base, 0.5 mm of vertical entry side below the roof line, then ``e`` more with the 45 degree chamfer
    cut off the entry corner; 20 mm wide."""
    height = (DEPTH - MALE_H) + e
    return 20.0 * (2.0 * height - 0.5 * e * e)


def test_the_plan_checks_find_nothing():
    assert [str(f) for f in s1_support.findings()] == []


def test_every_rail_object_comes_from_a_rail_call_and_the_calls_are_the_three_builders():
    calls = rail_calls()
    assert [c["builder_id"] for c in calls] == ["rail.male", "rail.female_backing", "rail.female_cut"]
    assert [c["parent"] for c in calls] == [None, None, None]
    assert [c["placement"] for c in calls] == [["x_mid", "y_mid", "z0", "flip"], ["x_mid", "y_mid", "z_sill"],
                                               ["x_mid", "y_mid", "z0", "x_open"]]
    assert [real_names(c) for c in calls] == [
        ["Rail_Male_TaperAdd", "Rail_Male_StripAAdd", "Rail_Male_StripBAdd"],
        ["Rail_Female_BackingAdd"],
        ["Rail_Female_GrooveCut", "Rail_Female_LockSlotCut", "Rail_Female_LeadInCut"]]
    record, _, _ = s1_support.build_record()
    produced = {n for c in calls for n in c["produced"]}
    rail_objects = {s["name"] for s in record["specs"] if s["name"].startswith("Rail_")}
    assert rail_objects and rail_objects <= produced
    for call in calls:  # the instance name is positional; none of the builders takes lock_e or `first` in the product calls
        assert "set_name" not in call["arguments"] and "lock_e" not in call["arguments"] and "first" not in call["arguments"]


def test_a_rail_object_made_outside_a_rail_call_is_a_ck11_finding():
    _, rows, pset = s1_support.build_record()
    kit = s1_support.new_kit()
    comp = kit.component("S1_RailMale", role="part", datum=(None, None, None))
    comp.extrude("Block_RailMale_Body", axis="Z", loops=[comp.rect("-T_RAIL_LEN / 2", "T_RAIL_LEN / 2", "-T_RAIL_PLATE_W / 2",
                                                                    "T_RAIL_PLATE_W / 2")], start=None, end="T_RAIL_PLATE_T", op="new")
    comp.extrude("Rail_Stray_FootAdd", axis="Z", loops=[comp.rect("-T_BOSS_H", "T_BOSS_H", "-T_BOSS_H", "T_BOSS_H")],
                 start="T_RAIL_PLATE_T", end="T_RAIL_PLATE_T + T_BOSS_H", op="join")
    record = kit._backend.build_record()
    found = checks.run(record, rows, {s1_support.CONFIGURATION: pset}, [], owners=["Block", "Rail"], protected_prefixes=[])
    assert {(f.id, f.name) for f in found if f.id == "CK11"} == {("CK11", "Rail_Stray_FootAdd"), ("CK11", "Rail_Stray_FootAddSk")}


def test_the_male_taper_and_the_two_strips_are_the_closed_form_volumes():
    changes = s1_support.block_features("rail_male")
    taper = (MOUTH_W + MOUTH_W + 2 * MALE_H * K) / 2 * MALE_H * LEN
    assert changes["Rail_Male_TaperAdd"] == pytest.approx(taper, rel=1e-7)
    assert changes["Rail_Male_StripAAdd"] == pytest.approx(strip_volume(0.6), rel=1e-7)
    assert changes["Rail_Male_StripBAdd"] == pytest.approx(strip_volume(0.6), rel=1e-7)


def test_the_female_groove_slot_backing_and_lead_in_are_the_closed_form_volumes():
    changes = s1_support.block_features("rail_female")
    hm, hr = MOUTH_W / 2 + CLR / math.sin(math.radians(60)), ROOT_W / 2 + CLR / math.sin(math.radians(60))
    groove_len = LEN / 2 + WALL + LEN / 2  # from the closed end at -30 out to x_open = 33
    assert changes["Rail_Female_GrooveCut"] == pytest.approx(-(hm + hr) * DEPTH * groove_len, rel=1e-7)
    # one box across the roof's full width, 5.5 + 1.5 + ... : the strips' span grown by 0.5 each side (3.0 mm) by (0.6 + 0.5) high
    assert changes["Rail_Female_LockSlotCut"] == pytest.approx(-(2.0 + 2 * CLR) * 2 * hr * (0.6 + CLR), rel=1e-7)
    assert changes["Rail_Female_BackingAdd"] == pytest.approx((2.0 + 2 * CLR + 2 * WALL) * 2 * (ROOT_W / 2 + SIDE_W) * (0.6 + CLR), rel=1e-7)
    # the lead-in is the ruled solid between the groove section and the section flared by 1 mm, over 1 mm of length, less the
    # part of it that lies in the groove itself: it must remove material, but only a few tens of mm3 (the oracle's is 37.9)
    assert -40.0 < changes["Rail_Female_LeadInCut"] < -35.0


def test_the_lead_in_is_a_loft_between_the_groove_section_and_the_flared_section():
    record, _, _ = s1_support.build_record()
    specs = {s["name"]: s for s in record["specs"]}
    lead = specs["Rail_Female_LeadInCut"]
    assert (lead["spec"], lead["op"], len(lead["sketches"]), len(lead["planes"])) == ("LoftSpec", "cut", 2, 2)
    kit = s1_support.new_kit()
    offsets = [kit.env.value(specs[n]["offset"]) for n in lead["planes"]]
    assert offsets == pytest.approx([LEN / 2 + WALL - 1.0, LEN / 2 + WALL])
    a, b = (specs[n]["loops"][0] for n in lead["sketches"])
    assert (a["kind"], len(a["args"]), b["kind"], len(b["args"])) == ("polygon", 4, "polygon", 4)
    # 1 x 45 degrees: flanks, mouth and roof each flare by MCC_RAIL_LEADIN over MCC_RAIL_LEADIN of length
    def value(point):
        return [0.0 if c is None else kit.env.value(c) for c in point]

    (ya0, za0), (ya1, _), (ya2, za2), _ = (value(pt) for pt in a["args"])
    (yb0, zb0), (yb1, _), (yb2, zb2), _ = (value(pt) for pt in b["args"])
    assert (ya0 - yb0, yb1 - ya1) == pytest.approx((1.0, 1.0))
    assert (za0, zb0, za2, zb2) == pytest.approx((0.0, 0.0, DEPTH, DEPTH + 1.0))
    assert yb2 - ya2 == pytest.approx(1.0 + K * 1.0)  # the flank keeps its slope, so the top flares by 1 + K


def test_the_groove_is_closed_at_the_end_wall_and_open_at_x_open():
    record, _, _ = s1_support.build_record()
    groove = {s["name"]: s for s in record["specs"]}["Rail_Female_GrooveCut"]
    kit = s1_support.new_kit()
    start = -kit.env.value(groove["start_offset"].removeprefix("-(").removesuffix(")")) if groove["start_offset"].startswith("-(") \
        else kit.env.value(groove["start_offset"])
    assert start == pytest.approx(-LEN / 2)  # 3 mm of sill (MCC_RAIL_END_WALL, D64.1) remain between it and the block's -X face
    assert start + kit.env.value(groove["distance"]) == pytest.approx(LEN / 2 + WALL)


def test_the_groove_keeps_half_a_millimetre_around_the_male_on_flanks_and_roof():
    kit = s1_support.new_kit()
    horiz = kit.env.value("MCC_RAIL_CLR_HORIZ")
    assert horiz * math.sin(math.radians(60)) == pytest.approx(CLR)  # normal to the flank
    assert kit.env.value("MCC_RAIL_DEPTH - MCC_RAIL_MALE_H") == pytest.approx(CLR)  # at the roof
    assert kit.env.value("MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_ROOF_CLR") == pytest.approx(0.6 + CLR)  # over the strips, in the slot


def male_on_a_tile(**placement):
    """A male rail at a placement other than the origin, on a 20 x 20 x 3 tile under its mouth centre (so that the bounding box of
    the part is the rail's own)."""
    kit = s1_support.new_kit()
    comp = kit.component("S1_RailMale", role="part", datum=(None, None, None))
    x_mid, y_mid = placement["x_mid"], placement["y_mid"]
    comp.extrude("Block_RailMale_Body", axis="Z",
                 loops=[comp.rect(expr.sub(x_mid, "T_BOSS_H"), expr.add(x_mid, "T_BOSS_H"), expr.sub(y_mid, "T_BOSS_H"),
                                  expr.add(y_mid, "T_BOSS_H"))], start=None, end="T_RAIL_PLATE_T", op="new")
    names = rail.male(comp, "Male", length="T_RAIL_LEN", **placement)
    return kit, names


def test_the_male_follows_x_mid_y_mid_and_z0():
    kit, names = male_on_a_tile(x_mid="T_RAIL_LEN / 2", y_mid="T_RAIL_PLATE_W / 4", z0="T_RAIL_PLATE_T", flip=False)
    assert names == ["Rail_Male_TaperAdd", "Rail_Male_StripAAdd", "Rail_Male_StripBAdd"]
    shape = ocp_replay.measure(s1_support.replay_kit(kit, "S1_RailMale").shape)
    top_hw = MOUTH_W / 2 + MALE_H * K
    assert shape["bbox_min"] == pytest.approx([0.0, 20.0 - top_hw, 0.0], abs=1e-6)
    assert shape["bbox_max"] == pytest.approx([LEN, 20.0 + top_hw, 3.0 + DEPTH + 0.6], abs=1e-6)


def strip_xs(kit) -> list:
    specs = {s.name: s for s in kit._backend.timeline}
    sketch = specs["Rail_Male_StripAAddSk"]
    return [kit.env.value(u) if u is not None else 0.0 for u, _ in sketch.loops[0].args]


def test_flip_mirrors_the_strips_about_x_mid_and_nothing_else():
    plain, _ = male_on_a_tile(x_mid="T_RAIL_LEN / 2", y_mid="T_RAIL_PLATE_W / 4", z0="T_RAIL_PLATE_T", flip=False)
    mirrored, _ = male_on_a_tile(x_mid="T_RAIL_LEN / 2", y_mid="T_RAIL_PLATE_W / 4", z0="T_RAIL_PLATE_T", flip=True)
    # x = x_mid + 27 for the exit face, 25 for the entry side, 25.6 where the chamfer meets the top
    assert strip_xs(plain) == pytest.approx([55.0, 55.0, 55.6, 57.0, 57.0])
    assert strip_xs(mirrored) == pytest.approx([5.0, 5.0, 4.4, 3.0, 3.0])
    a, b = (ocp_replay.measure(s1_support.replay_kit(k, "S1_RailMale").shape) for k in (plain, mirrored))
    assert (a["volume_mm3"], a["bbox_min"], a["bbox_max"]) == pytest.approx((b["volume_mm3"], b["bbox_min"], b["bbox_max"]), abs=1e-6)
    record = mirrored._backend.build_record()
    assert record["shared_calls"][0]["arguments"]["flip"] is True and "flip" in record["shared_calls"][0]["placement"]


def test_only_the_coupon_passes_lock_e_and_it_reaches_the_strips_the_slot_and_the_backing():
    e = "MCC_RAIL_LOCK_PLAY_MARGIN"  # 0.3 mm
    kit, _ = male_on_a_tile(x_mid="T_RAIL_LEN / 2", y_mid="T_RAIL_PLATE_W / 4", z0="T_RAIL_PLATE_T", flip=False, lock_e=e)
    male = kit._backend.build_record()["shared_calls"][0]
    assert male["arguments"]["lock_e"] == e  # a non-placement argument: CK10 compares it, so it needs a declared exception
    shape = ocp_replay.measure(s1_support.replay_kit(kit, "S1_RailMale").shape)
    assert shape["bbox_max"][2] == pytest.approx(3.0 + DEPTH + 0.3, abs=1e-6)
    # the female side takes the same value
    kit = s1_support.new_kit()
    comp = kit.component("S1_RailFemale", role="part", datum=(None, None, None))
    comp.extrude("Block_RailFemale_Body", axis="Z", loops=[comp.rect("-T_RAIL_LEN / 2 - MCC_RAIL_END_WALL", "T_RAIL_LEN / 2 + MCC_WALL",
                                                                      "-T_RAIL_PLATE_W / 2", "T_RAIL_PLATE_W / 2")],
                 start=None, end="MCC_RAIL_SILL_H", op="new")
    rail.female_backing(comp, "Female", x_mid=None, y_mid=None, z_sill="MCC_RAIL_SILL_H", length="T_RAIL_LEN", lock_e=e)
    rail.female_cut(comp, "Female", x_mid=None, y_mid=None, z0=None, length="T_RAIL_LEN", x_open="T_RAIL_LEN / 2 + MCC_WALL",
                    lock_e=e)
    changes = {f["name"]: f["volume_change_mm3"] for f in s1_support.replay_kit(kit, "S1_RailFemale").features}
    hr = ROOT_W / 2 + CLR / math.sin(math.radians(60))
    assert changes["Rail_Female_LockSlotCut"] == pytest.approx(-(2.0 + 2 * CLR) * 2 * hr * (0.3 + CLR), rel=1e-7)
    top = ocp_replay.measure(s1_support.replay_kit(kit, "S1_RailFemale").shape)["bbox_max"][2]
    assert top == pytest.approx(7.0 + 0.3 + CLR, abs=1e-6)


def test_the_female_follows_x_mid_y_mid_z0_and_z_sill():
    origin = s1_support.block_features("rail_female")
    kit = s1_support.new_kit()
    comp = kit.component("S1_RailFemale", role="part", datum=(None, None, None))
    x_mid, y_mid, z0 = "T_RAIL_LEN / 2", "T_RAIL_PLATE_W / 4", "T_RAIL_PLATE_T"
    sill = "T_RAIL_PLATE_T + MCC_RAIL_SILL_H"
    reach = "MCC_RAIL_ROOT_W / 2 + MCC_RAIL_SILL_SIDE_W"
    comp.extrude("Block_RailFemale_Body", axis="Z",
                 loops=[comp.rect("-MCC_RAIL_END_WALL", "T_RAIL_LEN + MCC_WALL", f"{y_mid} - ({reach})", f"{y_mid} + {reach}")],
                 start=z0, end=sill, op="new")
    rail.female_backing(comp, "Female", x_mid=x_mid, y_mid=y_mid, z_sill=sill, length="T_RAIL_LEN")
    rail.female_cut(comp, "Female", x_mid=x_mid, y_mid=y_mid, z0=z0, length="T_RAIL_LEN", x_open="T_RAIL_LEN + MCC_WALL")
    result = s1_support.replay_kit(kit, "S1_RailFemale")
    moved = {f["name"]: f["volume_change_mm3"] for f in result.features}
    for name in ("Rail_Female_BackingAdd", "Rail_Female_GrooveCut", "Rail_Female_LockSlotCut", "Rail_Female_LeadInCut"):
        assert moved[name] == pytest.approx(origin[name], rel=1e-7), name


def test_without_lead_in_there_is_no_lead_in_feature():
    kit = s1_support.new_kit()
    comp = kit.component("S1_RailFemale", role="part", datum=(None, None, None))
    comp.extrude("Block_RailFemale_Body", axis="Z", loops=[comp.rect("-T_RAIL_LEN / 2 - MCC_RAIL_END_WALL", "T_RAIL_LEN / 2 + MCC_WALL",
                                                                      "-T_RAIL_PLATE_W / 2", "T_RAIL_PLATE_W / 2")],
                 start=None, end="MCC_RAIL_SILL_H", op="new")
    names = rail.female_cut(comp, "Female", x_mid=None, y_mid=None, z0=None, length="T_RAIL_LEN", x_open="T_RAIL_LEN / 2 + MCC_WALL",
                            lead_in=False)
    assert names == ["Rail_Female_GrooveCut", "Rail_Female_LockSlotCut"]


def test_a_dimension_that_is_a_number_or_a_literal_is_refused():
    kit = s1_support.new_kit()
    comp = kit.component("S1_RailMale", role="part", datum=(None, None, None))
    comp.extrude("Block_RailMale_Body", axis="Z", loops=[comp.rect("-T_RAIL_LEN / 2", "T_RAIL_LEN / 2", "-T_RAIL_PLATE_W / 2",
                                                                    "T_RAIL_PLATE_W / 2")], start=None, end="T_RAIL_PLATE_T", op="new")
    with pytest.raises(expr.LiteralError):
        rail.male(comp, "Male", x_mid=None, y_mid=None, z0=None, length="60 mm", flip=False)
    with pytest.raises(TypeError):
        rail.male(comp, "Male", x_mid=None, y_mid=None, z0=None, length=60.0, flip=False)


@pytest.mark.parametrize("block", BLOCKS)
def test_a_block_replays_to_its_oracle(block, work):
    oracle.require_openscad()
    run = s1_support.run_block(block, work)
    assert s1_support.gate_problems(run) == []
    if block == "rail_male":
        assert run.report["residual"]["counted_rel"] == 0.0  # planar faces only: the two meshes are the same solid
    else:  # the loft against the hull: tenths of a mm3, a few micrometres thick
        assert run.report["residual"]["extra_volume_mm3"] < 0.5 and run.report["residual"]["missing_volume_mm3"] < 0.5
