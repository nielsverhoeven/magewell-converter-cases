"""SH2: the S1 block of ``shared/panel.py`` and ``shared/neutrik.py`` (issue #81, plan 3.10, 5.3 and 7, verdict A4 and A6):
``d_wall_cut``, the Neutrik D connector cut into a wall.

The block goes through the whole chain of ``test_s1_tg``: recorded through the facade, plan checks, OpenCascade replay, K4a
fixture, fresh oracle mesh, parity gate.  ``plate_cut`` has no oracle block (it belongs to the coupon issue #83), so its geometry
is proved in closed form on small tiles, in the three frames the options allow (lower wall on axis Y, upper wall on axis Y,
upper wall on axis X turned: the depth-mockup jig).  The screw table is checked for all four ``(mirror, turn)`` pairs against
the oracle's own screw positions pushed through the oracle's own rotations.  No test skips: ``oracle.require_openscad()`` fails
them under ``MCC_REQUIRE_OPENSCAD=1`` and skips only where OpenSCAD is missing.
"""
from __future__ import annotations

import math

import pytest

from cad.fusion.gen.core import checks, expr
from cad.fusion.gen.core.names import KitError
from cad.fusion.gen.shared import panel
from cad.fusion.gen.tests import oracle, s1_support

SX, SY = 19.0 / 2, 24.0 / 2  # half the screw pitches of constants.csv
SEAT_R, WIN_R, BORE_R, M3_R = 24.2 / 2, 24.8 / 2, 2.5 / 2, 3.4 / 2
SEAT_T, WALL_T, PANEL_T = 2.0, 5.0, 3.0
POCKET_AREA = (26 + 1) * (31 + 1) - (4 - math.pi) * 3.5 ** 2  # the flange plus 1 mm, corners of radius 3.5


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("s1_panel")


def panel_calls() -> list:
    record, _, _ = s1_support.build_record()
    return [c for c in record["shared_calls"] if c["builder_id"].startswith(("panel.", "neutrik."))]


def user_names(call: dict) -> list:
    return [n for n in call["produced"] if not n.endswith(("Sk", "SkA", "SkB", "PlA", "PlB"))]


def test_the_plan_checks_find_nothing():
    assert [str(f) for f in s1_support.findings()] == []


def test_the_block_is_one_panel_call_with_one_neutrik_call_inside():
    dispatcher, provider = panel_calls()
    assert (dispatcher["builder_id"], provider["builder_id"]) == ("panel.wall_cut", "neutrik.d_wall_cut")
    assert dispatcher["parent"] is None and provider["parent"] == "panel.wall_cut"  # CK11
    assert dispatcher["placement"] == provider["placement"] == ["axis", "a", "b", "face", "wall_side", "mirror", "turn"]
    assert user_names(dispatcher) == []  # the dispatcher draws nothing itself
    assert user_names(provider) == ["Patch_D_SeatCut", "Patch_D_WindowCut", "Patch_D_BoreCut"]
    for call in (dispatcher, provider):  # the instance name is positional and never an argument (CK10 would compare it)
        assert "set_name" not in call["arguments"] and "name" not in call["arguments"]
    assert "family" in dispatcher["arguments"] and "family" not in provider["arguments"]
    # what the case will pass: material below the seat face, screws as the wall is seen from outside
    assert (provider["arguments"]["wall_side"], provider["arguments"]["turn"], provider["arguments"]["mirror"]) == ("lower", False, True)


def _record_of(kit):
    return kit._backend.build_record()


def test_a_neutrik_call_without_a_panel_parent_is_a_finding_of_check_ck11():
    kit = s1_support.new_kit()
    comp = d_tile(kit, "Y", "lower")
    panel.neutrik.d_wall_cut(comp, "D", axis="Y", a=None, b="T_D_H / 2", face=None, wall_side="lower", seat_t="MCC_PANEL_SEAT_T",
                       wall_t="MCC_PANEL_SEAT_T + MCC_WALL", seat_d="T_D_SEAT_D", win_d="T_D_WIN_D", mirror=True, turn=False)
    document = s1_support.load_plan()
    _, rows, pset = s1_support.build_record()
    found = checks.run(_record_of(kit), rows, {s1_support.CONFIGURATION: pset}, [], owners=document["owners"],
                       protected_prefixes=[])
    assert [(f.id, f.name) for f in found if f.id == "CK11"] == [("CK11", "neutrik.d_wall_cut")]


# ---- the screw table ----------------------------------------------------------------------------------------------


def oracle_screws(mirror: bool) -> list:
    """The oracle's two screw centres in the connector's local frame: ``mcc_neutrik_d_cutout`` (``neutrik.scad:80-82``) with the
    flag as it is, and ``mcc_neutrik_d_wall_cut`` (``:151``) which has no flag and always the front view."""
    sign = -1 if mirror else 1
    return [(-sign * SX, SY), (sign * SX, -SY)]


def rotate_oracle(points, frame: str) -> list:
    """The ``(u, v)`` of local ``(x, y)`` points after the oracle's own reorientation of the frame.  ``wall``: the S1 block and
    the case, ``rotate([90, 0, 180])``, local (x, y, z) to world (-x, z, y), so ``(u, v) = (x, z) = (-x, y)``.  ``plate``: the
    flat panel as it is, ``(u, v) = (x, y)``.  ``jig``: the depth-mockup, ``rotate([0, -90, 0])``, local (x, y, z) to world
    (-z, y, x), so ``(u, v) = (y, z) = (y, x)``."""
    return [{"wall": lambda x, y: (-x, y), "plate": lambda x, y: (x, y), "jig": lambda x, y: (y, x)}[frame](x, y)
            for x, y in points]


def screws_of(kit, record, feature: str) -> list:
    """The two circle centres of the sketch of ``feature``, evaluated with the build values."""
    sketch = next(s for s in record["specs"] if s["name"] == feature + "Sk")
    return [(kit.env.value(loop["args"][0]), kit.env.value(loop["args"][1])) for loop in sketch["loops"]]


def pairs_equal(got, want) -> bool:
    return sorted(got) == pytest.approx(sorted(want), abs=1e-9)


def d_tile(kit, axis: str, wall_side: str, name: str = "S1_DWallCut"):
    """A component with a plain tile ``T_D_W`` wide, ``T_D_H`` high and ``MCC_WALL`` thick, the wall's seat face at 0."""
    if axis == "Y":
        comp = kit.component(name, role="part", datum=("-T_D_W / 2", None, None))
        loop = comp.rect("-T_D_W / 2", "T_D_W / 2", None, "T_D_H")
    else:
        comp = kit.component(name, role="part", datum=(None, "-T_D_W / 2", None))
        loop = comp.rect("-T_D_W / 2", "T_D_W / 2", None, "T_D_H")
    start, end = (None, "MCC_WALL") if wall_side == "upper" else ("-MCC_WALL", None)
    comp.extrude("Block_DWall_Body", axis=axis, loops=[loop], start=start, end=end, op="new")
    return comp


def offsets(mirror: bool, turn: bool) -> list:
    """The two screw bores of a wall cut centred on ``(0, T_D_H / 2)``, relative to that centre, read from the recorded sketch."""
    kit = s1_support.new_kit()
    comp = d_tile(kit, "Y", "lower")
    panel.wall_cut(comp, "D", **wall_args(mirror=mirror, turn=turn))
    return [(u, v - 22.5) for u, v in screws_of(kit, _record_of(kit), "Patch_D_BoreCut")]


@pytest.mark.parametrize("mirror, turn", [(True, False), (False, False), (False, True), (True, True)])
def test_the_screw_table_equals_the_oracle_in_its_frames(mirror, turn):
    """One table gives the screws of the four ``(mirror, turn)`` pairs.  Each is the oracle's local screw positions through the
    oracle's own reorientation: the case's patch wall is ``(True, False)``, the oracle's front-view panel ``(False, False)``, the
    depth-mockup jig ``(False, True)`` (P4-83 3.5 row 2: ``(a + SY, b - SX)`` and ``(a - SY, b + SX)``); ``(True, True)`` is that jig
    with the oracle's mirror flag."""
    frame = {(True, False): "wall", (False, False): "plate", (False, True): "jig", (True, True): "jig"}[(mirror, turn)]
    oracle_mirror = (mirror, turn) == (True, True)
    assert pairs_equal(offsets(mirror, turn), rotate_oracle(oracle_screws(oracle_mirror), frame))


def test_the_table_values_themselves():
    assert offsets(False, False) == [(-SX, SY), (SX, -SY)]
    assert offsets(True, False) == [(SX, SY), (-SX, -SY)]
    assert offsets(False, True) == [(SY, -SX), (-SY, SX)]
    assert offsets(True, True) == [(SY, SX), (-SY, -SX)]


def test_the_plate_cut_screws_follow_the_same_table():
    for mirror, turn in [(True, False), (False, False), (False, True), (True, True)]:
        kit = s1_support.new_kit()
        comp = d_tile(kit, "Y", "lower")
        panel.plate_cut(comp, "D", family="D", axis="Y", a=None, b="T_D_H / 2", face=None, wall_side="lower", panel_t="MCC_WALL",
                        seat_t="MCC_PANEL_SEAT_T", hole_d="T_D_SEAT_D", mirror=mirror, turn=turn)
        got = [(u, v - 22.5) for u, v in screws_of(kit, _record_of(kit), "Patch_D_ScrewCut")]
        assert got == offsets(mirror, turn)


# ---- the wall cut, in closed form ----------------------------------------------------------------------------------


def test_the_wall_cut_removes_a_seat_a_window_and_two_bores():
    changes = s1_support.block_features("d_wall_cut")
    assert changes["Patch_D_SeatCut"] == pytest.approx(-math.pi * SEAT_R ** 2 * SEAT_T, rel=1e-6)
    assert changes["Patch_D_WindowCut"] == pytest.approx(-math.pi * WIN_R ** 2 * (WALL_T - SEAT_T), rel=1e-6)
    assert changes["Patch_D_BoreCut"] == pytest.approx(-2 * math.pi * BORE_R ** 2 * WALL_T, rel=1e-6)


def test_the_screw_bores_keep_the_web_of_t1_61_to_the_openings():
    """The oracle's assert T1-61: at least ``MCC_WALL_BORE_WEB_MIN`` of wall between a bore and the seat hole or window.  The
    builders cannot assert, so the numbers are checked here for the block's diameters and for the screw positions of every pair."""
    web_min = s1_support.new_kit().env.value("MCC_WALL_BORE_WEB_MIN")
    for turn in (False, True):
        for u, v in offsets(False, turn):
            assert math.hypot(u, v) - WIN_R - BORE_R >= web_min


@pytest.mark.parametrize("axis, wall_side", [("Y", "lower"), ("Y", "upper"), ("X", "upper"), ("X", "lower"), ("Z", "upper")])
def test_the_wall_cut_is_the_same_cut_on_either_side_of_the_face_and_on_any_axis(axis, wall_side):
    kit = s1_support.new_kit()
    if axis == "Z":  # a wall normal to Z: the tile is the plate T_D_W by T_D_H and MCC_WALL thick
        comp = kit.component("S1_DWallCut", role="part", datum=(None, None, None))
        comp.extrude("Block_DWall_Body", axis="Z", loops=[comp.rect(None, "T_D_W", None, "T_D_H")], start=None, end="MCC_WALL",
                     op="new")
        a, b = "T_D_W / 2", "T_D_H / 2"
    else:
        comp = d_tile(kit, axis, wall_side)
        a, b = (None, "T_D_H / 2")
    names = panel.wall_cut(comp, "D", family="D", axis=axis, a=a, b=b, face=None, wall_side=wall_side,
                           seat_t="MCC_PANEL_SEAT_T", wall_t="MCC_WALL", seat_d="T_D_SEAT_D", win_d="T_D_WIN_D", mirror=False,
                           turn=False)
    assert names == ["Patch_D_SeatCut", "Patch_D_WindowCut", "Patch_D_BoreCut"]
    result = s1_support.replay_kit(kit, "S1_DWallCut")
    assert result.dead_features == []
    removed = math.pi * (SEAT_R ** 2 * SEAT_T + WIN_R ** 2 * (PANEL_T - SEAT_T) + 2 * BORE_R ** 2 * PANEL_T)
    assert _volume(result) == pytest.approx(40 * 45 * PANEL_T - removed, rel=1e-6)


def _volume(result) -> float:
    from cad.fusion.replay import ocp_replay

    return ocp_replay.measure(result.shape)["volume_mm3"]


# ---- the plate cut, in closed form ---------------------------------------------------------------------------------


PLATE_CASES = [("Y", "lower", False, False), ("Y", "upper", True, False), ("X", "upper", False, True), ("X", "upper", True, True)]


@pytest.mark.parametrize("axis, wall_side, mirror, turn", PLATE_CASES)
def test_the_plate_cut_is_a_hole_two_screws_and_a_rounded_pocket(axis, wall_side, mirror, turn):
    """The flat-panel cutout with its rear seat pocket (``neutrik.scad:37-93``).  Hole through the panel; the two ``MCC_M3_CLR_D``
    screws through it; the pocket (flange plus 1 mm, corner radius 3.5, three cuts: two crossing rectangles and four corner
    circles) from the rear face to ``seat_t`` short of the seat face.  Every cut removes material, and what the pocket
    removes is the rounded rectangle less what the hole and the screws (all inside it) took before."""
    kit = s1_support.new_kit()
    comp = d_tile(kit, axis, wall_side)
    names = panel.plate_cut(comp, "D", family="D", axis=axis, a=None, b="T_D_H / 2", face=None, wall_side=wall_side,
                            panel_t="MCC_WALL", seat_t="MCC_PANEL_SEAT_T", hole_d="T_D_SEAT_D", mirror=mirror, turn=turn)
    assert names == ["Patch_D_HoleCut", "Patch_D_ScrewCut", "Patch_D_PocketACut", "Patch_D_PocketBCut", "Patch_D_PocketRCut"]
    result = s1_support.replay_kit(kit, "S1_DWallCut")
    assert result.dead_features == []
    changes = {f["name"]: f["volume_change_mm3"] for f in result.features}
    hole, screws = math.pi * SEAT_R ** 2, 2 * math.pi * M3_R ** 2
    assert changes["Patch_D_HoleCut"] == pytest.approx(-hole * PANEL_T, rel=1e-6)
    assert changes["Patch_D_ScrewCut"] == pytest.approx(-screws * PANEL_T, rel=1e-6)
    pocket = sum(changes[f"Patch_D_Pocket{k}Cut"] for k in "ABR")
    assert pocket == pytest.approx(-(POCKET_AREA - hole - screws) * (PANEL_T - SEAT_T), rel=1e-6)
    assert all(changes[f"Patch_D_Pocket{k}Cut"] < 0 for k in "ABR")
    assert _volume(result) == pytest.approx(40 * 45 * PANEL_T - hole * PANEL_T - screws * PANEL_T
                                            - (POCKET_AREA - hole - screws) * (PANEL_T - SEAT_T), rel=1e-6)


def test_a_turned_plate_pocket_swaps_its_two_sides():
    """``turn`` swaps the flange sides: the pocket is 32 along ``u`` and 27 along ``v``, not 27 and 32."""
    for turn, along_u in ((False, 27.0), (True, 32.0)):
        kit = s1_support.new_kit()
        comp = d_tile(kit, "Y", "lower")
        panel.plate_cut(comp, "D", family="D", axis="Y", a=None, b="T_D_H / 2", face=None, wall_side="lower",
                        panel_t="MCC_WALL", seat_t="MCC_PANEL_SEAT_T", hole_d="T_D_SEAT_D", mirror=False, turn=turn)
        record = _record_of(kit)
        sketch = next(s for s in record["specs"] if s["name"] == "Patch_D_PocketACutSk")
        (loop,) = sketch["loops"]
        u0, u1 = (kit.env.value(x) for x in loop["args"][:2])
        assert u1 - u0 == pytest.approx(along_u)


# ---- refusals ------------------------------------------------------------------------------------------------------


def wall_args(**overrides) -> dict:
    args = dict(family="D", axis="Y", a=None, b="T_D_H / 2", face=None, wall_side="lower", seat_t="MCC_PANEL_SEAT_T",
                wall_t="MCC_PANEL_SEAT_T + MCC_WALL", seat_d="T_D_SEAT_D", win_d="T_D_WIN_D", mirror=True, turn=False)
    args.update(overrides)
    return args


def test_an_unknown_family_is_refused_like_the_oracles_unknown_part():
    kit = s1_support.new_kit()
    comp = d_tile(kit, "Y", "lower")
    with pytest.raises(ValueError, match="family"):
        panel.wall_cut(comp, "D", **wall_args(family="MINIDIN8"))
    with pytest.raises(ValueError, match="family"):
        panel.plate_cut(comp, "D", family="XLR", axis="Y", a=None, b="T_D_H / 2", face=None, wall_side="lower",
                        panel_t="MCC_WALL", seat_t="MCC_PANEL_SEAT_T", hole_d="T_D_SEAT_D", mirror=False, turn=False)
    assert not any(c["produced"] for c in _record_of(kit)["shared_calls"])  # a refused call draws nothing


@pytest.mark.parametrize("bad, error", [(dict(wall_side="middle"), ValueError), (dict(axis="W"), ValueError),
                                        (dict(mirror=1), TypeError), (dict(turn="no"), TypeError)])
def test_a_wrong_option_is_refused(bad, error):
    kit = s1_support.new_kit()
    comp = d_tile(kit, "Y", "lower")
    with pytest.raises(error):
        panel.wall_cut(comp, "D", **wall_args(**bad))


def test_a_dimension_that_is_a_number_or_a_literal_is_refused():
    kit = s1_support.new_kit()
    comp = d_tile(kit, "Y", "lower")
    with pytest.raises(expr.LiteralError):
        panel.wall_cut(comp, "D", **wall_args(seat_d="24.2 mm"))
    with pytest.raises(TypeError):
        panel.wall_cut(comp, "D", **wall_args(seat_d=24.2))
    with pytest.raises(TypeError):
        panel.wall_cut(comp, "D", **wall_args(b=22.5))


@pytest.mark.parametrize("missing", ["mirror", "turn", "wall_side", "family"])
def test_every_option_is_required_so_that_the_record_always_carries_it(missing):
    kit = s1_support.new_kit()
    comp = d_tile(kit, "Y", "lower")
    args = wall_args()
    del args[missing]
    with pytest.raises((TypeError, KitError)):  # a placement option is refused by the record (KitError), the rest by the signature
        panel.wall_cut(comp, "D", **args)


# ---- the block against its oracle ---------------------------------------------------------------------------------


def test_the_block_replays_to_its_oracle(work):
    oracle.require_openscad()
    run = s1_support.run_block("d_wall_cut", work)
    assert s1_support.gate_problems(run) == []
    # perfectly round holes (D40): the exact circles of the replay against the oracle's 96- and 64-gons, a few slivers
    assert run.report["residual"]["counted_rel"] <= 0.002
