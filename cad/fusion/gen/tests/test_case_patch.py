"""C5: the side bolt and the patch wall of the case master, stages B6 and B7 (issue #81, plan 3.4 and 4, verdict A2, A8, D81.5).

The builders of ``cad/fusion/gen/case/sidebolt.py`` (the captive 1/4"-20 bolt's boss, web and three bores, through the shared
``fasteners.side_bolt_boss`` and ``fasteners.side_bolt_cut``) and ``cad/fusion/gen/case/patch.py`` (the bezel recess and four
slot cuts through the shared ``panel.wall_cut``) run through the facade on the recording backend; the OpenCascade replay executes
the record with the parameter set of the template (``pro-convert-for-ndi-to-hdmi``, configuration ``default``) and the result is
compared with a fresh oracle mesh, within the thresholds of the brief (``s1_support.gate_problems``).

Stages B6 and B7 of the K4a fixture are cumulative and hold the cradle (B4) and the floor with its rail (B5), which milestones C3
and C4 build and which may not be on main when this file runs.  The comparison therefore renders the staged oracle with the
harness lines of a stage whose builders the record does not yet contain removed (``_oracle_lines``): with C3 and C4 on main the
full stage is compared; without them, B1 to B3 plus the milestone's own stage.  The committed fixture still pins the box corners.
Tests never skip: ``oracle.require_openscad()`` fails them under ``MCC_REQUIRE_OPENSCAD=1``.
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

import pytest

from cad import params
from cad.fusion.gen.case import build, frame, patch, sidebolt
from cad.fusion.gen.core import checks, expr
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
STAGES = (("B6", 6), ("B7", 7))
SIDEBOLT_ADD = ["SideBolt_Boss_CylAdd", "SideBolt_Boss_WebAdd"]
SIDEBOLT_CUT = ["SideBolt_Bore_HeadCut", "SideBolt_Bore_ShankCut", "SideBolt_Bore_PocketCut"]
SLOT_NAMES = [f"Patch_Slot{i}_{what}Cut" for i in frame.SLOTS for what in ("Seat", "Window", "Bore")]
PATCH_CUT = ["Patch_Recess_PocketCut", *SLOT_NAMES]
SLOT_FLAGS = [f"Patch_Slot{i}" for i in frame.SLOTS]
# (marker of the earlier milestone's features in the record, the harness lines of the oracle that build them)
EARLIER = (("Cradle_", ("if (stage >= 4) mcc_cradle(dev, cfg);",)),
           ("Floor_", ("if (stage >= 5) mcc_floor_features_add(dev, cfg);", "if (stage >= 5) mcc_rail_features_cut(dev, cfg);")))


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _fixture(name: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][f"{TEMPLATE}.base.{name}"]


def _env(stage=7):
    _, _, rows, sets = _build(stage)
    pset = sets[TEMPLATE]
    return expr.Env(rows, pset["values"])


def _replay(stage=7, suppress=None):
    _, record, rows, sets = _build(stage)
    pset = sets[TEMPLATE]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"] if suppress is None else suppress, components=["Base"])["Base"]


def _features(record: dict, component: str = "Base") -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == component]


def _spec(record: dict, name: str) -> dict:
    return next(s for s in record["specs"] if s["name"] == name)


def _own(record: dict) -> list[str]:
    return [n for n in _features(record) if n.startswith(("SideBolt_", "Patch_"))]


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

def test_stage_6_and_7_record_the_planned_features():
    assert _own(_build(6)[1]) == SIDEBOLT_ADD + SIDEBOLT_CUT
    assert _own(_build(7)[1]) == SIDEBOLT_ADD + SIDEBOLT_CUT + PATCH_CUT
    assert _own(_build(None)[1]) == SIDEBOLT_ADD + SIDEBOLT_CUT + PATCH_CUT


def test_the_calls_are_in_the_stages_and_phases_of_the_plan():
    """Rows 5 (join), 9 (cut) and 10 (cut) of the call table: B6 adds the boss and cuts the bores, B7 cuts the patch wall."""
    rows = {fn: (row, number) for row, number, fn, _keys in build.CALLS}
    assert rows[sidebolt.add] == (5, 6) and rows[sidebolt.cut] == (9, 6) and rows[patch.cut] == (10, 7)
    _, record, _, _ = _build(7)
    ops = {s["name"]: s["op"] for s in record["specs"] if s["spec"] == "ExtrudeSpec" and s["component"] == "Base"}
    assert [ops[n] for n in SIDEBOLT_ADD] == ["join"] * 2 and {ops[n] for n in SIDEBOLT_CUT + PATCH_CUT} == {"cut"}
    order = [s["name"] for s in record["specs"] if s["spec"] == "ExtrudeSpec" and s["component"] == "Base"]
    assert max(order.index(n) for n in SIDEBOLT_ADD) < min(order.index(n) for n in SIDEBOLT_CUT + PATCH_CUT)   # D81.4


def test_the_shared_calls_take_the_plan_arguments():
    _, record, _, _ = _build(7)
    calls = [c for c in record["shared_calls"] if c["builder_id"].startswith(("fasteners.side_bolt", "panel."))]
    assert [c["builder_id"] for c in calls] == ["fasteners.side_bolt_boss", "fasteners.side_bolt_cut"] + ["panel.wall_cut"] * 4
    boss, cut = calls[:2]
    length = "MCC_WALL + MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T"
    assert boss["arguments"] == {"x": "V_SIDEBOLT_X", "z": "V_SIDEBOLT_Z", "y_face": frame.YL, "length": length,
                                 "d": "MCC_SIDE_BOLT_BOSS_OD", "web_t": "MCC_SIDE_BOLT_SUPPORT_WEB_T", "web_y0": frame.YIL,
                                 "web_z0": frame.FT}
    assert cut["arguments"] == {"x": "V_SIDEBOLT_X", "z": "V_SIDEBOLT_Z", "y_face": frame.YL, "length": length,
                                "head_d": "MCC_SIDE_BOLT_HEAD_D + 2 * MCC_CLR_SLIDE", "head_h": "MCC_SIDE_BOLT_HEAD_REC_H",
                                "shank_d": "MCC_TRIPOD_CLR_D", "pocket_d": "MCC_SIDE_BOLT_POCKET_D",
                                "pocket_y0": "-V_CASE_W / 2 + MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T",
                                "pocket_h": "MCC_SIDE_BOLT_POCKET_H"}
    for i, call in zip(frame.SLOTS, calls[2:]):
        assert call["arguments"] == {
            "family": "D", "axis": "Y", "a": f"V_SLOT{i}_X", "b": frame.ZC, "face": frame.YSEAT,
            "wall_side": "lower", "seat_t": "MCC_PANEL_SEAT_T", "wall_t": "MCC_T_PATCH - MCC_PANEL_BEZEL_T",
            "seat_d": f"V_SLOT{i}_SEAT_D", "win_d": f"V_SLOT{i}_WIN_D", "mirror": True, "turn": False}
    inner = [c for c in record["shared_calls"] if c["builder_id"].startswith("neutrik.")]
    assert [[n for n in c["produced"] if n.endswith("Cut")] for c in inner] == [[f"Patch_Slot{i}_{w}Cut" for w in ("Seat", "Window", "Bore")] for i in frame.SLOTS]
    assert all(c["parent"] is not None for c in inner)   # the dispatcher is the only way in


def test_the_slot_count_is_the_capacity_and_the_case_passes_no_other_orientation():
    assert frame.SLOTS == (1, 2, 3, 4) == tuple(range(1, frame.CAPACITY["slots"] + 1))
    _, record, rows, _ = _build(7)
    assert {r["name"] for r in rows if re.fullmatch(r"V_SLOT\d+_X", r["name"])} == {f"V_SLOT{i}_X" for i in frame.SLOTS}
    assert {(c["arguments"]["wall_side"], c["arguments"]["mirror"], c["arguments"]["turn"])
            for c in record["shared_calls"] if c["builder_id"] == "panel.wall_cut"} == {("lower", True, False)}


def test_only_patch_imports_the_panel_builder_and_only_the_case_builders_import_nothing_else_from_the_shared_ones():
    """Verdict A8: in ``gen/case`` only ``patch.py`` imports ``shared/panel.py``; sidebolt goes through ``shared/fasteners.py``."""
    sources = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path(patch.__file__).parent.glob("*.py"))}
    assert [n for n, s in sources.items() if re.search(r"import[^\n]*\bpanel\b", s)] == ["patch.py"]
    assert not [n for n, s in sources.items() if re.search(r"import[^\n]*\bneutrik\b", s)]
    assert "fasteners" in sources["sidebolt.py"] and "panel" not in sources["sidebolt.py"]
    for module in (sidebolt, patch):
        text = sources[Path(module.__file__).name]
        assert not re.search(r"cad\.(params|layout|rules)|import\s+math", text)


def test_the_names_carry_the_owners_and_the_slot_sets_of_the_flags():
    document, record, _, _ = _build(7)
    assert {"SideBolt", "Patch"} <= set(document["owners"])
    for name in SIDEBOLT_ADD + SIDEBOLT_CUT + PATCH_CUT:
        assert name.split("_")[0] in ("SideBolt", "Patch"), name
    for flag in SLOT_FLAGS:
        assert [n for n in SLOT_NAMES if n.startswith(flag + "_")] and len([n for n in SLOT_NAMES if n.startswith(flag + "_")]) == 3
    assert "Patch_Recess" not in {f for f in _build(7)[3]["_build"]["suppress"]}   # the recess is no flag; it is in every case


def test_the_flags_of_the_slots_are_in_the_build_configuration_and_clear():
    _, _, _, sets = _build(7)
    suppress = sets["_build"]["suppress"]
    assert all(flag in suppress and suppress[flag] is False for flag in SLOT_FLAGS)


def test_the_plan_checks_find_no_finding_of_the_side_bolt_and_patch_milestone():
    document, record, rows, sets = _build(7)
    findings = checks.run(record, rows, sets, document.get("shared_exceptions", []), owners=document["owners"],
                          protected_prefixes=document["protected_prefixes"])
    assert not [str(f) for f in findings if f.id != "CK4"]
    assert not {f.name for f in findings} & set(SLOT_FLAGS)   # the four slot flags have members


def test_the_recess_profile_follows_the_plan():
    env = _env()
    _, record, _, _ = _build(7)
    spec = _spec(record, "Patch_Recess_PocketCut")
    sketches = {s["name"]: s for s in record["specs"] if s["spec"] == "SketchSpec"}
    (loop,) = sketches[spec["sketch"]]["loops"]
    assert loop["kind"] == "polygon"
    ys, zc, h = env.value(frame.YSEAT), env.value("V_CONN_Z"), env.value("MCC_PLATE_H")
    yh, bezel, k = env.value(frame.YH), env.value("MCC_PANEL_BEZEL_T"), env.value("MCC_PATCH_RECESS_ROOF_K")
    points = [(env.value(u), env.value(v)) for u, v in loop["args"]]
    assert points == pytest.approx([(ys, zc - h / 2), (yh, zc - h / 2), (yh, zc + h / 2 + bezel * k), (ys, zc + h / 2)])
    assert sketches[spec["sketch"]]["on"] == "origin:YZ" and spec["op"] == "cut"   # axis X
    assert (env.value(spec["start_offset"]), env.value(spec["distance"])) == pytest.approx(
        (-env.value("V_PLATE_L") / 2, env.value("V_PLATE_L")))
    # the roof corner leaves through the outer face, the wall top is not exceeded by the straight part (D36 assert of the oracle)
    assert zc + h / 2 + bezel <= env.value("V_CASE_Z_TOP") + 1e-9


def test_the_slot_positions_stay_inside_the_recess_and_the_wall():
    env = _env()
    half = env.value("V_PLATE_L") / 2
    for i in frame.SLOTS:
        assert abs(env.value(f"V_SLOT{i}_X")) + env.value(f"V_SLOT{i}_WIN_D") / 2 < half


def test_the_side_bolt_boss_is_flush_and_the_web_runs_to_the_axis():
    """D81.5: the boss starts at the outer face (shares the wall's volume) and the web ends on the bolt axis, not on a line."""
    env = _env()
    _, record, _, _ = _build(7)
    boss, web = _spec(record, "SideBolt_Boss_CylAdd"), _spec(record, "SideBolt_Boss_WebAdd")
    assert env.value("MCC_SIDE_BOLT_PROUD") == 0
    sketches = {s["name"]: s for s in record["specs"] if s["spec"] == "SketchSpec"}
    assert (sketches[boss["sketch"]]["on"], sketches[web["sketch"]]["on"]) == ("origin:XZ", "origin:XY")   # axes Y and Z
    assert env.value(frame.YL) < env.value(frame.YIL) < env.value(frame.YL) + env.value(
        "MCC_WALL + MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T")      # the boss runs through the wall into the gap
    assert env.value(web["distance"]) + env.value(web["start_offset"]) == pytest.approx(env.value("V_SIDEBOLT_Z"))
    assert env.value(web["start_offset"]) == pytest.approx(env.value("MCC_FLOOR_T"))


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay against the committed fixture and the flags
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,stage", STAGES)
def test_the_replay_has_no_dead_feature_and_the_box_of_the_committed_fixture(name, stage):
    result = _replay(stage)
    shape, fixture = ocp_replay.measure(result.shape), _fixture(name)
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    assert result.dead_features == []
    for corner in ("bbox_min", "bbox_max"):
        worst = max(abs(a - b) for a, b in zip(shape[corner], fixture[corner]))
        assert worst <= s1_support.FRAME_TOL, f"{name} {corner} differs from the fixture by {worst:.4f} mm"


def test_every_feature_removes_or_adds_volume_in_the_planned_direction():
    changes = {f["name"]: f["volume_change_mm3"] for f in _replay().features}
    assert all(changes[n] > 0 for n in SIDEBOLT_ADD)
    assert all(changes[n] < 0 for n in SIDEBOLT_CUT + PATCH_CUT)


def test_suppressing_a_slot_flag_removes_exactly_the_three_cuts_of_that_slot():
    _, _, _, sets = _build(7)
    on = _replay()
    for i in frame.SLOTS:
        off = _replay(suppress={**sets[TEMPLATE]["suppress"], f"Patch_Slot{i}": True})
        assert off.dead_features == []
        gone = {f["name"] for f in off.features if f["suppressed"]} - {f["name"] for f in on.features if f["suppressed"]}
        assert gone == {f"Patch_Slot{i}_{w}Cut" for w in ("Seat", "Window", "Bore")}
        assert ocp_replay.measure(off.shape)["volume_mm3"] > ocp_replay.measure(on.shape)["volume_mm3"]


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against a staged oracle, and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("case_patch")


def _oracle_lines(record: dict) -> tuple[str, ...]:
    """The harness lines of earlier milestones whose features the record does not have yet (C3 cradle, C4 floor)."""
    present = _features(record)
    return tuple(line for marker, lines in EARLIER if not any(n.startswith(marker) for n in present) for line in lines)


def _staged_oracle(stage: int, out_dir: Path) -> Path:
    """The stage oracle of the template with the not-yet-built earlier stages removed (a no-op once C3 and C4 are on main)."""
    harness = oracle.HARNESS_S2
    for line in _oracle_lines(_build(stage)[1]):
        assert line in harness, line
        harness = harness.replace(line, "")
    defines = {"slug": f'"{TEMPLATE}"', "part": '"base"', "stage": str(stage), "fan": "false", "fan_switch": "false",
               "rail": "true", "lid_vents": "true"}
    return oracle._export(harness, defines, Path(out_dir) / f"s2_b{stage}_staged.stl", f"B{stage} staged")


@pytest.mark.parametrize("name,stage", STAGES)
def test_a_stage_replays_to_its_oracle(name, stage, work):
    oracle.require_openscad()
    document, _, _, _ = _build(stage)
    result = _replay(stage)
    exports = [e for c in document["configurations"] if c["id"] == TEMPLATE for e in c["exports"] if e["component"] == "Base"]
    (entry,) = ocp_replay.export({"Base": result}, {"configurations": [{"id": TEMPLATE, "exports": exports}]}, TEMPLATE,
                                 work / f"replay-{name}")
    mesh_path = work / f"replay-{name}" / entry["files"][1]
    reference = _staged_oracle(stage, work / "oracle")
    code, report = s1_support.parity(mesh_path, reference, name, work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), oracle.measure(reference),
                              code, report)
    assert s1_support.gate_problems(run) == []
    fixture = _fixture(name)   # the same box as the cumulative fixture
    for corner in ("bbox_min", "bbox_max"):
        assert max(abs(a - b) for a, b in zip(run.shape[corner], fixture[corner])) <= s1_support.FRAME_TOL
