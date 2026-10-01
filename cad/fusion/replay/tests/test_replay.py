"""K4b: the OpenCascade replay of a build record (issue #81, plan 3.12, verdict A1).

Every build here goes through the kit's facade on the recording backend, so the replay reads exactly what a real
``record.json`` holds.  The volumes are closed forms; the S1 blocks (tongue and groove, rectangles only) are compared with
the committed K4a fixtures and, where OpenSCAD is available, with a fresh oracle mesh through ``scripts/parity.py``.

These tests never skip: OpenCascade is in ``requirements-step.txt`` and installed by every job that runs them.  The one test
that renders the oracle goes through ``oracle.require_openscad()``, which fails when ``MCC_REQUIRE_OPENSCAD=1`` and OpenSCAD
is missing (CI) and skips only on a developer machine without it.
"""
from __future__ import annotations

import ast
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from cad import params
from cad.fusion.gen.core import facade
from cad.fusion.gen.core.facade import Kit
from cad.fusion.gen.tests import oracle
from cad.fusion.replay import ocp_replay

REPO = Path(__file__).resolve().parents[4]
PARITY = REPO / "scripts" / "parity.py"

VALUES = {"V_L": 100.0, "V_W": 60.0, "V_H": 20.0, "V_T": 5.0, "V_CX": 35.0, "V_CY": 30.0, "V_D": 10.0, "V_D2": 5.0,
          "V_PITCH": 30.0, "V_N_HOLES": 2,
          "V_RX0": 10.0, "V_RX1": 90.0, "V_RY0": 10.0, "V_RY1": 50.0,
          "V_HX0": 20.0, "V_HX1": 80.0, "V_HY0": 20.0, "V_HY1": 40.0,
          "V_QX0": 30.0, "V_QX1": 70.0, "V_QY0": 20.0, "V_QY1": 40.0, "V_FAR": 150.0}


def _row(name, unit, kind, expression=None):
    return {"name": name, "unit": unit, "kind": kind, "expression": expression,
            "fusion": expression, "comment": "", "description": "test row", "src": "test", "conf": None}


def _rows(values=VALUES, constants=()):
    rows = [_row(n, "mm", "constant", e) for n, e in constants]
    return rows + [_row(n, "" if n.startswith("V_N_") else "mm", "solver") for n in values]


def _env(rows, values):
    units = {r["name"]: ("none" if r["unit"] == "" else r["unit"]) for r in rows if r["kind"] == "solver"}
    return params.environment(rows, {"values": values, "units": units})


def record_of(builder, values=VALUES, constants=(), document="Doc"):
    """Run ``builder(kit)`` on the recording backend; returns ``(record, env)``."""
    rows = _rows(values, constants)
    ctx = SimpleNamespace(backend="recording", design=None, document=document, registry=rows, values=values,
                          options={}, log=print)
    kit = Kit(ctx)
    builder(kit)
    # a record goes through JSON on disk, so go through it here too: tuples become lists
    return json.loads(json.dumps(kit._backend.build_record())), _env(rows, values)


def replay_one(builder, name, suppress=None, **options):
    record, env = record_of(builder)
    return ocp_replay.replay(record, env, suppress, **options)[name]


def volume(result) -> float:
    return ocp_replay.measure(result.shape)["volume_mm3"]


def base_with_ring_hole_and_pattern(kit):
    c = kit.component("Base", role="part", datum=(None, None, None))
    c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
    c.extrude("Shell_Ring_Add", axis="Z", loops=[c.rect("V_RX0", "V_RX1", "V_RY0", "V_RY1")],
              holes=[c.rect("V_HX0", "V_HX1", "V_HY0", "V_HY1")], start="V_H", end="V_H + V_T", op="join")
    c.extrude("Shell_Hole_Cut", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_D")], start=None, end="V_H", op="cut")
    c.pattern("Shell_Hole_Pat", seed="Shell_Hole_Cut", axis="X", count="V_N_HOLES", pitch="V_PITCH")


BOX = 100.0 * 60.0 * 20.0
RING = (80.0 * 40.0 - 60.0 * 20.0) * 5.0
HOLE = math.pi * 25.0 * 20.0


# ---- analytic volumes ------------------------------------------------------------------------------------------------------


def test_a_box_with_a_ring_a_cylinder_cut_and_a_two_instance_pattern_has_the_closed_form_volume():
    result = replay_one(base_with_ring_hole_and_pattern, "Base")
    assert volume(result) == pytest.approx(BOX + RING - 2 * HOLE, rel=1e-6)
    changes = {f["name"]: f["volume_change_mm3"] for f in result.features}
    assert changes["Shell_Floor_Body"] == pytest.approx(BOX, rel=1e-6)
    assert changes["Shell_Ring_Add"] == pytest.approx(RING, rel=1e-6)
    assert changes["Shell_Hole_Cut"] == pytest.approx(-HOLE, rel=1e-6)
    assert changes["Shell_Hole_Pat"] == pytest.approx(-HOLE, rel=1e-6)
    assert result.dead_features == []
    shape = ocp_replay.measure(result.shape)
    assert (shape["solids"], shape["valid"]) == (1, True)


def test_the_pattern_instances_sit_at_k_times_the_pitch():
    result = replay_one(base_with_ring_hole_and_pattern, "Base")
    # holes at x = 35 and 65 (pitch 30), both with d = 10: the solid between them is intact
    probe = replay_one(base_with_ring_hole_and_pattern, "Base", stage="Shell_Hole_Cut")
    assert volume(probe) - volume(result) == pytest.approx(HOLE, rel=1e-6)


def test_a_suppressed_set_is_absent_from_the_shape():
    result = replay_one(base_with_ring_hole_and_pattern, "Base", suppress={"Shell_Hole": True})
    assert volume(result) == pytest.approx(BOX + RING, rel=1e-6)
    skipped = {f["name"] for f in result.features if f["suppressed"]}
    assert skipped == {"Shell_Hole_Cut", "Shell_Hole_Pat"}
    assert result.dead_features == []  # a suppressed feature is not a dead one
    result = replay_one(base_with_ring_hole_and_pattern, "Base", suppress={"Shell_Ring": True, "Shell_Hole": False})
    assert volume(result) == pytest.approx(BOX - 2 * HOLE, rel=1e-6)


@pytest.mark.parametrize("axis,box", [("Z", ([0, 0, 0], [100, 60, 20])), ("Y", ([0, 0, 0], [100, 20, 60])),
                                      ("X", ([0, 0, 0], [20, 100, 60]))])
def test_a_ring_extrudes_along_every_axis_with_its_hole_cut_out(axis, box):
    def build(kit):
        c = kit.component("Block", role="part", datum=(None, None, None))
        c.extrude("Shell_Ring_Body", axis=axis, loops=[c.rect(None, "V_L", None, "V_W")],
                  holes=[c.circle("V_CX", "V_CY", "V_D")], start=None, end="V_H", op="new")

    result = replay_one(build, "Block")
    shape = ocp_replay.measure(result.shape)
    assert shape["volume_mm3"] == pytest.approx((100 * 60 - 25 * math.pi) * 20, rel=1e-6)
    assert shape["bbox_min"] == pytest.approx(box[0], abs=1e-6)
    assert shape["bbox_max"] == pytest.approx(box[1], abs=1e-6)
    assert shape["valid"]


def test_a_polygon_sketch_in_either_winding_gives_the_same_prism():
    for points in ([("0", "0"), ("V_L", "0"), ("V_L", "V_W")], [("0", "0"), ("V_L", "V_W"), ("V_L", "0")]):
        def build(kit, points=points):
            c = kit.component("Wedge", role="part", datum=(None, None, None))
            c.extrude("Shell_Wedge_Body", axis="Y", loops=[c.polygon([(None if u == "0" else u, None if v == "0" else v)
                                                                      for u, v in points])],
                      start=None, end="V_H", op="new")

        assert volume(replay_one(build, "Wedge")) == pytest.approx(100 * 60 / 2 * 20, rel=1e-6)


def test_a_start_offset_follows_the_recorded_direction_of_the_plane_normal():
    def build(kit):
        c = kit.component("Block", role="part", datum=(None, None, None))
        c.extrude("Shell_Block_Body", axis="Y", loops=[c.rect(None, "V_L", None, "V_H")], start="V_T", end="V_T + V_W", op="new")

    with mock.patch.dict(facade.PLANE_NORMAL, {"XZ": -1}):
        record, env = record_of(build)
    spec = next(s for s in record["specs"] if s["spec"] == "ExtrudeSpec")
    assert (spec["direction"], spec["start_offset"]) == ("negative", "-(V_T)")
    shape = ocp_replay.measure(ocp_replay.replay(record, env)["Block"].shape)
    assert (shape["bbox_min"][1], shape["bbox_max"][1]) == pytest.approx((5.0, 65.0), abs=1e-9)


# ---- lofts -----------------------------------------------------------------------------------------------------------------


def test_a_loft_between_two_circles_has_the_frustum_volume():
    def build(kit):
        c = kit.component("Cone", role="part", datum=(None, None, None))
        c.loft("Shell_Cone_Body", axis="Z", loop_a=c.circle("V_CX", "V_CY", "V_D"), at_a=None,
               loop_b=c.circle("V_CX", "V_CY", "V_D2"), at_b="V_H", op="new")

    big, small, h = 5.0, 2.5, 20.0
    assert volume(replay_one(build, "Cone")) == pytest.approx(math.pi * h / 3 * (big * big + big * small + small * small), rel=1e-6)


@pytest.mark.parametrize("axis", ["Z", "Y", "X"])
def test_a_loft_between_two_similar_rectangles_has_the_frustum_volume(axis):
    def build(kit):
        c = kit.component("Cone", role="part", datum=(None, None, None))
        c.loft("Shell_Cone_Body", axis=axis, loop_a=c.rect("V_RX0", "V_RX1", "V_RY0", "V_RY1"), at_a=None,
               loop_b=c.rect("V_QX0", "V_QX1", "V_QY0", "V_QY1"), at_b="V_H", op="new")

    a1, a2 = 80.0 * 40.0, 40.0 * 20.0
    result = replay_one(build, "Cone")
    shape = ocp_replay.measure(result.shape)
    assert shape["volume_mm3"] == pytest.approx(20.0 / 3 * (a1 + math.sqrt(a1 * a2) + a2), rel=1e-6)
    axis_index = "XYZ".index(axis)
    assert (shape["bbox_min"][axis_index], shape["bbox_max"][axis_index]) == pytest.approx((0.0, 20.0), abs=1e-5)  # a ruled surface has a bounding-box gap of 1e-7


def test_a_loft_cut_removes_its_frustum_from_the_body():
    def build(kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        c.loft("Shell_Cone_Cut", axis="Z", loop_a=c.circle("V_CX", "V_CY", "V_D"), at_a=None,
               loop_b=c.circle("V_CX", "V_CY", "V_D2"), at_b="V_H", op="cut")

    frustum = math.pi * 20.0 / 3 * (25 + 12.5 + 6.25)
    assert volume(replay_one(build, "Base")) == pytest.approx(BOX - frustum, rel=1e-6)


def test_a_loft_on_a_flipped_plane_normal_uses_the_normal_the_extrudes_record():
    def build(kit):
        a = kit.component("Block", role="part", datum=(None, None, None))
        a.extrude("Shell_Block_Body", axis="Y", loops=[a.rect(None, "V_L", None, "V_H")], start=None, end="V_W", op="new")
        b = kit.component("Cone", role="part", datum=(None, None, None))
        b.loft("Shell_Cone_Body", axis="Y", loop_a=b.rect("V_RX0", "V_RX1", "V_RY0", "V_RY1"), at_a=None,
               loop_b=b.rect("V_QX0", "V_QX1", "V_QY0", "V_QY1"), at_b="V_H", op="new")

    with mock.patch.dict(facade.PLANE_NORMAL, {"XZ": -1}):
        record, env = record_of(build)
    shape = ocp_replay.measure(ocp_replay.replay(record, env)["Cone"].shape)
    assert (shape["bbox_min"][1], shape["bbox_max"][1]) == pytest.approx((0.0, 20.0), abs=1e-5)  # a ruled surface has a bounding-box gap of 1e-7


# ---- re-joins and dead features --------------------------------------------------------------------------------------------


def _grille(rejoin_end):
    def build(kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Fan_Bay_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        c.extrude("Fan_Grille_Cut", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_D")], start=None, end="V_H", op="cut")
        c.extrude("Fan_Grille_Rejoin", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_D2")], start=None, end=rejoin_end,
                  op="rejoin", within="Fan_Grille_Cut")
    return build


def test_a_rejoin_inside_its_cut_reports_zero_outside_volume():
    result = replay_one(_grille("V_H"), "Base")
    (rejoin,) = result.rejoins
    assert rejoin["within"] == "Fan_Grille_Cut"
    assert rejoin["added_mm3"] == pytest.approx(math.pi * 2.5 ** 2 * 20, rel=1e-6)
    assert rejoin["outside_mm3"] == 0.0
    assert volume(result) == pytest.approx(BOX - HOLE + math.pi * 2.5 ** 2 * 20, rel=1e-6)


def test_a_rejoin_that_sticks_out_of_its_cut_reports_the_excess():
    result = replay_one(_grille("V_H + V_T"), "Base")
    (rejoin,) = result.rejoins
    assert rejoin["added_mm3"] == pytest.approx(math.pi * 2.5 ** 2 * 25, rel=1e-6)
    assert rejoin["outside_mm3"] == pytest.approx(math.pi * 2.5 ** 2 * 5, rel=1e-6)


def test_a_rejoin_whose_cut_is_suppressed_adds_everything_outside():
    record, env = record_of(_grille("V_H"))
    result = ocp_replay.replay(record, env, {"Fan_Grille": False})["Base"]
    assert result.rejoins[0]["outside_mm3"] == 0.0
    # the cut flag also switches the re-join (same set), so nothing is replayed of either
    result = ocp_replay.replay(record, env, {"Fan_Grille": True})["Base"]
    assert result.rejoins == []
    assert volume(result) == pytest.approx(BOX, rel=1e-6)


def test_a_cut_that_removes_nothing_is_reported_as_a_dead_feature():
    def build(kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        c.extrude("Shell_Void_Cut", axis="Z", loops=[c.rect("V_FAR", "V_FAR + V_D", "V_FAR", "V_FAR + V_D")], start=None,
                  end="V_H", op="cut")

    result = replay_one(build, "Base")
    assert result.dead_features == ["Shell_Void_Cut"]
    assert volume(result) == pytest.approx(BOX, rel=1e-6)


# ---- stage, skipped specs, facet, reserves ---------------------------------------------------------------------------------


def test_stage_stops_after_a_count_of_features_or_after_a_named_one():
    names = lambda r: [f["name"] for f in r.features]  # noqa: E731
    assert names(replay_one(base_with_ring_hole_and_pattern, "Base", stage=2)) == ["Shell_Floor_Body", "Shell_Ring_Add"]
    assert names(replay_one(base_with_ring_hole_and_pattern, "Base", stage="Shell_Hole_Cut"))[-1] == "Shell_Hole_Cut"


def test_a_text_feature_is_skipped_and_listed():
    def build(kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        c.text("Shell_Label_TextCut", axis="Z", frame=c.rect("V_RX0", "V_RX1", "V_RY0", "V_RY1"), start="V_H - V_T", end="V_H",
               string="A", height="V_D", halign="center", valign="middle", font="Arial", style="regular", op="cut")

    result = replay_one(build, "Base")
    assert [(s["name"], s["reason"]) for s in result.skipped] == [("Shell_Label_TextCut", "a text feature has no replay")]
    assert volume(result) == pytest.approx(BOX, rel=1e-6)


def test_facet_mode_replaces_every_circle_by_the_circumscribed_n_gon():
    sides = 64
    radius = 5.0 / math.cos(math.pi / sides)
    area = sides * radius * radius * math.sin(2 * math.pi / sides) / 2
    record, env = record_of(base_with_ring_hole_and_pattern)
    nominal = ocp_replay.replay(record, env)["Base"]
    facet = ocp_replay.replay(record, env, facet=sides)["Base"]
    assert volume(facet) == pytest.approx(BOX + RING - 2 * area * 20, rel=1e-6)
    assert volume(facet) < volume(nominal)


def test_a_reserve_component_keeps_every_body_and_only_the_named_components_are_replayed():
    def build(kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        g = kit.component("Reserve_Fan", role="reserve", datum=(None, None, None))
        g.extrude("Fan_Bay_Body", axis="Z", loops=[g.rect("V_RX0", "V_RX1", "V_RY0", "V_RY1")], start="V_H", end="V_H + V_T", op="new")
        g.extrude("Fan_Duct_Body", axis="Z", loops=[g.rect("V_QX0", "V_QX1", "V_QY0", "V_QY1")], start="V_H + V_D", end="V_H + V_D + V_T", op="new")

    record, env = record_of(build)
    both = ocp_replay.replay(record, env)
    assert list(both) == ["Base", "Reserve_Fan"]
    assert ocp_replay.measure(both["Reserve_Fan"].shape)["volume_mm3"] == pytest.approx((3200 + 800) * 5, rel=1e-6)
    assert list(ocp_replay.replay(record, env, components={"Base"})) == ["Base"]


def test_an_op_on_a_component_whose_body_is_suppressed_is_an_error():
    with pytest.raises(ocp_replay.ReplayError, match="no body"):
        replay_one(base_with_ring_hole_and_pattern, "Base", suppress={"Shell_Floor": True})


# ---- S1 blocks against the K4a fixtures ------------------------------------------------------------------------------------

S1_CONSTANTS = (("MCC_WALL", "3.0 mm"), ("MCC_TG_W", "1.6 mm"), ("MCC_TG_H", "2.0 mm"), ("MCC_CLR_TG", "0.25 mm"),
                ("MCC_LID_T", "3.0 mm"), ("T_TG_L", "60 mm"), ("T_TG_W", "40 mm"), ("T_TG_PLATE", "3 mm"))
S1_VALUES: dict = {}
X0, X1 = "-T_TG_L / 2 + MCC_WALL", "T_TG_L / 2 - MCC_WALL"
Y0, Y1 = "-T_TG_W / 2 + MCC_WALL", "T_TG_W / 2 - MCC_WALL"
OUTER = ("-T_TG_L / 2", "T_TG_L / 2", "-T_TG_W / 2", "T_TG_W / 2")


def build_s1_tongue(kit):
    """The S1 block of the tongue as plan 5.3 lays it out: a wall ring plus the tongue ring on top of it."""
    c = kit.component("S1_Tongue", role="part", datum=("-T_TG_L / 2", "-T_TG_W / 2", None))
    c.extrude("Block_Tongue_Body", axis="Z", loops=[c.rect(*OUTER)], holes=[c.rect(X0, X1, Y0, Y1)], start=None,
              end="T_TG_PLATE", op="new")
    c.extrude("Block_Tongue_RingAdd", axis="Z",
              loops=[c.rect(f"{X0} - MCC_TG_W", f"{X1} + MCC_TG_W", f"{Y0} - MCC_TG_W", f"{Y1} + MCC_TG_W")],
              holes=[c.rect(X0, X1, Y0, Y1)], start="T_TG_PLATE", end="T_TG_PLATE + MCC_TG_H", op="join")


def build_s1_groove(kit):
    """The S1 block of the groove: a lid slab with the groove ring cut from below."""
    c = kit.component("S1_Groove", role="part", datum=("-T_TG_L / 2", "-T_TG_W / 2", None))
    c.extrude("Block_Groove_Body", axis="Z", loops=[c.rect(*OUTER)], start=None, end="MCC_LID_T", op="new")
    o = "MCC_TG_W + MCC_CLR_TG"
    c.extrude("Block_Groove_RingCut", axis="Z",
              loops=[c.rect(f"{X0} - ({o})", f"{X1} + {o}", f"{Y0} - ({o})", f"{Y1} + {o}")],
              holes=[c.rect(f"{X0} + MCC_CLR_TG", f"{X1} - MCC_CLR_TG", f"{Y0} + MCC_CLR_TG", f"{Y1} - MCC_CLR_TG")],
              start=None, end="MCC_TG_H", op="cut")


S1_BUILDERS = {"tongue": ("S1_Tongue", build_s1_tongue), "groove": ("S1_Groove", build_s1_groove)}


def _s1_plan(component, block):
    return {"configurations": [{"id": "default", "exports": [{"component": component, "target": "s1", "part": block}]}]}


def _export_s1(block, out_dir):
    component, builder = S1_BUILDERS[block]
    record, env = record_of(builder, S1_VALUES, S1_CONSTANTS, document="MCC-S1")
    results = ocp_replay.replay(record, env, {})
    (entry,) = ocp_replay.export(results, _s1_plan(component, block), "default", out_dir)
    return results[component], entry


@pytest.mark.parametrize("block", sorted(S1_BUILDERS))
def test_an_s1_block_replays_to_its_k4a_fixture(block, tmp_path):
    result, entry = _export_s1(block, tmp_path)
    assert entry["files"] == [f"s1/{block}.step", f"s1/{block}.model.stl"]
    assert (tmp_path / entry["files"][0]).stat().st_size > 1000
    shape = ocp_replay.measure(result.shape)
    assert (shape["solids"], shape["valid"]) == (1, True)
    fixture = oracle.load_fixture(oracle.S1_FIXTURE)["blocks"][block]
    assert oracle.differences(oracle.measure(tmp_path / entry["files"][1]), fixture, f"replay of S1 {block}") == []


def _parity(candidate: Path, reference: Path, name: str, out_dir: Path):
    done = subprocess.run([sys.executable, str(PARITY), "compare", str(candidate), str(reference), "--name", name,
                           "--out", str(out_dir), "--samples", "0"], cwd=REPO, capture_output=True, text=True)
    report = out_dir / f"parity-{name}.json"
    return done, json.loads(report.read_text(encoding="utf-8")) if report.is_file() else None


@pytest.mark.parametrize("block", sorted(S1_BUILDERS))
def test_an_s1_block_passes_the_parity_gate_against_a_fresh_oracle_mesh(block, tmp_path):
    oracle.require_openscad()
    _, entry = _export_s1(block, tmp_path / "replay")
    reference = oracle.render_s1(block, tmp_path / "oracle")
    done, report = _parity(tmp_path / "replay" / entry["files"][1], reference, block, tmp_path / "parity")
    assert done.returncode == 0, done.stdout + done.stderr
    assert report["verdict"]["status"] == "pass"


# ---- export and report -----------------------------------------------------------------------------------------------------


def test_export_writes_only_the_allow_list_and_a_nested_target(tmp_path):
    record, env = record_of(base_with_ring_hole_and_pattern)
    results = ocp_replay.replay(record, env)
    plan = {"configurations": [{"id": "a/b", "exports": [{"component": "Base", "target": "case/hdmi", "part": "base"}]}]}
    (entry,) = ocp_replay.export(results, plan, "a/b", tmp_path)
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()) == [
        "case/hdmi/base.model.stl", "case/hdmi/base.step"]
    assert entry["files"] == ["case/hdmi/base.step", "case/hdmi/base.model.stl"]
    mesh = oracle.measure(tmp_path / "case/hdmi/base.model.stl")
    assert mesh["volume_mm3"] == pytest.approx(BOX + RING - 2 * HOLE, rel=1e-4)  # the 0.005 mm mesh deflection
    with pytest.raises(ocp_replay.ReplayError, match="no configuration"):
        ocp_replay.export(results, plan, "other", tmp_path)
    plan["configurations"][0]["exports"][0]["component"] = "Missing"
    with pytest.raises(ocp_replay.ReplayError, match="nothing to export"):
        ocp_replay.export(results, plan, "a/b", tmp_path)


def test_report_adds_or_replaces_one_configuration_entry(tmp_path):
    record, env = record_of(base_with_ring_hole_and_pattern)
    results = ocp_replay.replay(record, env)
    ocp_replay.report(tmp_path, "one", results, document="Doc")
    ocp_replay.report(tmp_path, "two", results)
    first = ocp_replay.report(tmp_path, "one", ocp_replay.replay(record, env, {"Shell_Hole": True}))
    doc = json.loads((tmp_path / "replay.json").read_text(encoding="utf-8"))
    assert (doc["document"], doc["kind"], sorted(doc["configurations"])) == ("Doc", "builder-replay", ["one", "two"])
    assert doc["configurations"]["one"] == first
    assert first["components"]["Base"]["volume_mm3"] == pytest.approx(BOX + RING, rel=1e-6)
    assert doc["configurations"]["two"]["components"]["Base"]["volume_mm3"] == pytest.approx(BOX + RING - 2 * HOLE, rel=1e-6)
    assert first["rejoin_outside_mm3"] == 0.0 and first["dead_features"] == []


# ---- the command -----------------------------------------------------------------------------------------------------------


CSV = "name,unit,expression,comment\nMCC_WALL,mm,3.0 mm,test row | src=test | conf=assumed\n"
SET = {"schema": 1, "configurations": {
    "default": {"parameters": {n: (f"{v} mm" if not n.startswith("V_N_") else str(v)) for n, v in VALUES.items()},
                "flags": {"Shell_Hole": False, "Fan_Grille": False}},
    "nohole": {"parameters": {n: (f"{v} mm" if not n.startswith("V_N_") else str(v)) for n, v in VALUES.items()},
               "flags": {"Shell_Hole": True, "Fan_Grille": False}}}}


@pytest.fixture
def document(tmp_path):
    """A plan, its registry and set file on disk, and the record of a build made through the facade."""
    (tmp_path / "constants.csv").write_text(CSV, encoding="utf-8")
    (tmp_path / "set.json").write_text(json.dumps(SET), encoding="utf-8")
    plan = {"schema": 1, "document": "Doc",
            "registry": {"source": "cad.params", "csv": [str(tmp_path / "constants.csv")], "sets": [str(tmp_path / "set.json")]},
            "build_configuration": "default",
            "configurations": [
                {"id": "default", "set": {"file": str(tmp_path / "set.json"), "config": "default"},
                 "exports": [{"component": "Base", "target": "case", "part": "base"}]},
                {"id": "nohole", "set": {"file": str(tmp_path / "set.json"), "config": "nohole"},
                 "exports": [{"component": "Base", "target": "case", "part": "base"}]}]}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    def record_path(builder, name="record.json", **extra):
        rows = params.registry([tmp_path / "constants.csv"], [tmp_path / "set.json"])
        ps = params.parameter_set(tmp_path / "set.json", "default")
        ctx = SimpleNamespace(backend="recording", design=None, document="Doc", registry=rows, values=ps["values"], options={},
                              log=print)
        kit = Kit(ctx)
        builder(kit)
        record = {**kit._backend.build_record(), "plan": str(plan_path), **extra}
        path = tmp_path / name
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    return SimpleNamespace(root=tmp_path, plan=plan_path, record=record_path)


def test_main_replays_one_configuration_into_the_exports_layout(document, capsys):
    out = document.root / "out"
    code = ocp_replay.main([str(document.record(base_with_ring_hole_and_pattern)), "--configuration", "nohole", "--out", str(out)])
    assert code == 0, capsys.readouterr()
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()) == [
        "nohole/exports/case/base.model.stl", "nohole/exports/case/base.step", "replay.json"]
    doc = json.loads((out / "replay.json").read_text(encoding="utf-8"))
    entry = doc["configurations"]["nohole"]
    assert doc["document"] == "Doc"
    assert entry["suppress"]["Shell_Hole"] is True
    assert entry["exports"][0]["files"] == ["nohole/exports/case/base.step", "nohole/exports/case/base.model.stl"]
    assert entry["components"]["Base"]["volume_mm3"] == pytest.approx(BOX + RING, rel=1e-6)


def test_main_all_replays_every_configuration_with_its_own_flags(document):
    out = document.root / "out"
    assert ocp_replay.main([str(document.record(base_with_ring_hole_and_pattern)), "--all", "--out", str(out)]) == 0
    doc = json.loads((out / "replay.json").read_text(encoding="utf-8"))
    assert sorted(doc["configurations"]) == ["default", "nohole"]
    volumes = {k: v["components"]["Base"]["volume_mm3"] for k, v in doc["configurations"].items()}
    assert volumes["default"] == pytest.approx(BOX + RING - 2 * HOLE, rel=1e-6)
    assert volumes["nohole"] == pytest.approx(BOX + RING, rel=1e-6)


def test_main_reads_the_plan_from_the_option_when_the_record_names_none(document):
    out = document.root / "out"
    record = document.record(base_with_ring_hole_and_pattern, plan=None)
    assert ocp_replay.main([str(record), "--configuration", "default", "--out", str(out)]) == 2
    assert ocp_replay.main([str(record), "--configuration", "default", "--out", str(out), "--plan", str(document.plan)]) == 0


def test_main_exits_1_when_a_rejoin_sticks_out_of_its_cut(document, capsys):
    code = ocp_replay.main([str(document.record(_grille("V_H + V_T"))), "--configuration", "default",
                            "--out", str(document.root / "out")])
    assert code == 1
    assert "FAIL: a re-join adds volume outside its cut" in capsys.readouterr().out


def test_main_prints_dead_features_and_skipped_specs(document, capsys):
    def build(kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        c.extrude("Shell_Void_Cut", axis="Z", loops=[c.rect("V_FAR", "V_FAR + V_D", "V_FAR", "V_FAR + V_D")], start=None,
                  end="V_H", op="cut")

    assert ocp_replay.main([str(document.record(build)), "--configuration", "default", "--out", str(document.root / "o")]) == 0
    assert "dead feature (changes no volume): Shell_Void_Cut" in capsys.readouterr().out


def test_main_refuses_an_unusable_input_with_exit_code_2(document, capsys):
    (document.root / "bad.json").write_text("not json", encoding="utf-8")
    assert ocp_replay.main([str(document.root / "bad.json"), "--all", "--out", str(document.root / "o")]) == 2
    assert ocp_replay.main([str(document.record(base_with_ring_hole_and_pattern)), "--configuration", "nope",
                            "--out", str(document.root / "o")]) == 2
    assert "error:" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        ocp_replay.main([str(document.record(base_with_ring_hole_and_pattern))])  # one of --configuration, --all


# ---- what the module may import --------------------------------------------------------------------------------------------


def test_the_replay_imports_only_the_standard_library_cad_params_and_ocp():
    tree = ast.parse(Path(ocp_replay.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported |= {module} | {f"{module}.{a.name}" for a in node.names}
    foreign = sorted(m for m in imported if m.split(".")[0] not in sys.stdlib_module_names | {"OCP", "cad", "__future__"})
    assert foreign == []
    assert sorted(m for m in imported if m.split(".")[0] == "cad") == ["cad", "cad.params"]
    assert "sys.path" not in Path(ocp_replay.__file__).read_text(encoding="utf-8")
