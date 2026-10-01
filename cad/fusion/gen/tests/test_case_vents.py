"""C6: the vents of the case master, stages B8 and L4 (issue #81, plan 3.4 and 4, verdict B1, D81.7).

The builders of ``cad/fusion/gen/case/vents.py`` run through the facade on the recording backend, the OpenCascade replay executes
the record with the parameter set of the template (``pro-convert-for-ndi-to-hdmi``, configuration ``default``) and the result is
compared with the K4a stage fixtures (``fixtures/s2_stages.json``) and with a fresh oracle mesh, within the thresholds of the
brief (``s1_support.gate_problems``).  Stages are cumulative.  Stage 8 of the base holds the cradle (B4), the side bolt (B6) and
the patch wall (B7); a stage whose milestone has not landed is a stub in ``gen/case`` and the document does not build it.  The
reference of stage 8 is then a *staged oracle*: the K4a harness with exactly those stages left out (``_staged_harness``), rendered
fresh; once every earlier milestone is on main the reference is the committed fixture B8 itself.  The lid stage 4 has all its
predecessors (L1 to L3) on main and always meets the fixture.  The tests that need the oracle never skip.
"""
from __future__ import annotations

import functools
import json

import pytest

from cad import params
from cad.fusion.gen.case import frame, vents
from cad.fusion.gen.core import expr
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
STAGES = (("base", "Base", 8, "B8"), ("lid", "Lid", 4, "L4"))
FAR_BASE = ["FarLoA", "FarLoB", "FarLoC", "FarUpA", "FarUpB", "ExhA"]
BASE_RUNS = [*FAR_BASE, "NegXA"]
LID_RUNS = ["LidA", "LidB"]
VENT_FLAGS = {f"Vent_{run}" for run in [*BASE_RUNS, *LID_RUNS]}
# the oracle stage that each owner of an earlier milestone stands for (the stages B4, B6 and B7 of the base)
STAGE_OF_OWNER = {"Cradle": 4, "SideBolt": 6, "Patch": 7}


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _fixture(part: str, name: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][f"{TEMPLATE}.{part}.{name}"]


def _env(config=TEMPLATE, stage=8):
    _, record, rows, sets = _build(stage)
    pset = sets[config]
    return record, pset, expr.Env(rows, pset["values"])


@functools.lru_cache(maxsize=None)
def _replay(component: str, stage: int, config=TEMPLATE):
    record, pset, _ = _env(config, stage)
    _, _, rows, _ = _build(stage)
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"], components=[component])[component]


def _export(component: str, stage: int, out_dir):
    document, _, _, _ = _build(stage)
    result = _replay(component, stage)
    exports = [e for c in document["configurations"] if c["id"] == TEMPLATE for e in c["exports"] if e["component"] == component]
    (entry,) = ocp_replay.export({component: result}, {"configurations": [{"id": TEMPLATE, "exports": exports}]}, TEMPLATE, out_dir)
    return result, entry


def _features(record: dict, component: str, owner: str | None = None) -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == component and (owner is None or s["name"].startswith(owner + "_"))]


def _missing_base_stages() -> tuple[int, ...]:
    """The oracle stages below 8 that the document does not build yet: the earlier milestones whose module is still a stub."""
    _, record, _, _ = _build(8)
    present = {name.split("_")[0] for name in _features(record, "Base")}
    return tuple(sorted(stage for owner, stage in STAGE_OF_OWNER.items() if owner not in present))


def _staged_harness(missing: tuple[int, ...]) -> str:
    """The K4a stage harness with the base stages of ``missing`` switched off (the lid part is left as it is)."""
    head, rest = oracle.HARNESS_S2.split("module stage_base", 1)
    base, tail = rest.split("module stage_lid", 1)
    for stage in missing:
        base = base.replace(f"stage >= {stage})", "false)")
    return head + "module stage_base" + base + "module stage_lid" + tail


def _slot_volume(env: expr.Env, run: str, base: bool) -> float:
    """Volume of one slot of ``run``: width, height and the thickness of the wall it goes through."""
    if not base:
        return env.value("MCC_LID_VENT_SLOT_W") * env.value("MCC_LID_VENT_SLOT_L") * env.value("MCC_LID_T")
    if run.startswith("NegX"):
        z_lo, z_hi = vents.NEGX_Z
    else:
        (z_lo, z_hi), = [(lo, hi) for runs, lo, hi in vents.FAR_BANDS if run in runs]
    return env.value("MCC_VENT_SLOT_W") * (env.value(z_hi) - env.value(z_lo)) * env.value("MCC_WALL")


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

def test_the_capacity_of_the_runs_is_the_capacity_table():
    assert [len(runs) for runs in (frame.VENT_FAR_LOW, frame.VENT_FAR_HIGH, frame.VENT_EXH, frame.VENT_NEGX, frame.VENT_LID)] == [
        3, 2, 1, 1, 2]
    assert [r for runs, _, _ in vents.FAR_BANDS for r in runs] == FAR_BASE and list(frame.VENT_NEGX) == ["NegXA"]


def test_stage_8_records_the_vent_features_in_run_order_seed_then_pattern():
    _, record, _, _ = _build(8)
    expected = [n for run in BASE_RUNS for n in (f"Vent_{run}_SlotCut", f"Vent_{run}_SlotPat")]
    assert _features(record, "Base", "Vent") == expected
    # the lid stages share the numbers: stage 8 holds L1 to L4, so the lid vents are there too
    assert _features(record, "Lid", "Vent") == [n for run in LID_RUNS for n in (f"Vent_{run}_SlotCut", f"Vent_{run}_SlotPat")]


def test_stage_4_of_the_lid_records_the_two_lid_runs():
    _, record, _, _ = _build(4)
    assert _features(record, "Lid", "Vent") == [n for run in LID_RUNS for n in (f"Vent_{run}_SlotCut", f"Vent_{run}_SlotPat")]
    assert _features(record, "Base", "Vent") == []


def test_the_full_build_has_the_same_vent_features():
    """No stage: the stubs of the other milestones add nothing to the vents."""
    _, record, _, _ = _build(None)
    assert _features(record, "Base", "Vent") == [n for run in BASE_RUNS for n in (f"Vent_{run}_SlotCut", f"Vent_{run}_SlotPat")]
    assert _features(record, "Lid", "Vent") == [n for run in LID_RUNS for n in (f"Vent_{run}_SlotCut", f"Vent_{run}_SlotPat")]


def test_every_seed_is_a_cut_through_its_wall_and_every_pattern_repeats_its_own_seed():
    _, record, _, _ = _build(8)
    specs = {s["name"]: s for s in record["specs"]}
    sketches = {s["name"]: s for s in record["specs"] if s["spec"] == "SketchSpec"}
    for run in BASE_RUNS:
        seed, pattern = specs[f"Vent_{run}_SlotCut"], specs[f"Vent_{run}_SlotPat"]
        assert (seed["spec"], seed["op"], seed["component"]) == ("ExtrudeSpec", "cut", "Base")
        assert [loop["kind"] for loop in sketches[seed["sketch"]]["loops"]] == ["rect"]   # one slot, no element of its own
        assert pattern["seed"] == seed["name"] and pattern["axis2"] is None
        # the axis of the extrude is the wall's normal; the pattern runs along the wall
        assert pattern["axis"] == ("Y" if run.startswith("NegX") else "X")


def test_the_phase_order_of_the_base_is_joins_then_cuts():
    _, record, _, _ = _build(8)
    ops = [s["op"] for s in record["specs"] if s["spec"] == "ExtrudeSpec" and s["component"] == "Base"]
    assert ops == sorted(ops, key=["new", "join", "cut", "rejoin"].index)
    assert ops.count("cut") >= 7


def test_the_counts_are_bare_names_and_the_pitches_are_the_plan_expressions():
    _, record, _, _ = _build(8)
    patterns = {s["name"]: s for s in record["specs"] if s["spec"] == "PatternSpec"}
    for run in BASE_RUNS:
        p = patterns[f"Vent_{run}_SlotPat"]
        assert (p["count"], p["pitch"]) == (f"V_N_VENT_{run.upper()}", "MCC_VENT_SLOT_W + MCC_VENT_WEB_W")
    _, record, _, _ = _build(4)
    patterns = {s["name"]: s for s in record["specs"] if s["spec"] == "PatternSpec"}
    for run in LID_RUNS:
        p = patterns[f"Vent_{run}_SlotPat"]
        assert (p["axis"], p["count"], p["pitch"]) == ("X", f"V_N_VENT_{run.upper()}", "MCC_LID_VENT_SLOT_W + MCC_LID_VENT_WEB_W")
        assert (p["axis2"], p["count2"], p["pitch2"]) == ("Y", "V_N_VENT_LID_ROWS", "MCC_LID_VENT_SLOT_L + MCC_LID_VENT_ROW_GAP")


def test_the_flags_of_the_vent_sets_are_in_the_build_configuration_and_a_set_has_one_flag_each():
    _, _, _, sets = _build(8)
    assert VENT_FLAGS <= set(sets["_build"]["suppress"])
    assert len(VENT_FLAGS) == 9 == sum(frame.CAPACITY[k] for k in ("far_low", "far_high", "exhaust", "negx", "lid"))


def test_the_seed_slots_are_centred_on_the_first_position_of_their_run():
    """The seed is the slot of width ``MCC_VENT_SLOT_W`` whose centre is the run's own first position (and likewise on the lid)."""
    _, _, env = _env()
    x0, x1 = vents._slot(vents._x0("FarLoA"), vents.SLOT_W)
    assert (env.value(x0) + env.value(x1)) / 2 == pytest.approx(env.value("V_VENT_FARLOA_X0"))
    assert env.value(x1) - env.value(x0) == pytest.approx(env.value("MCC_VENT_SLOT_W"))
    y0, y1 = vents._slot(vents._y0("NegXA"), vents.SLOT_W)
    assert (env.value(y0) + env.value(y1)) / 2 == pytest.approx(env.value("V_VENT_NEGXA_Y0"))


@pytest.mark.parametrize("config", sorted(c for c in _build(4)[3] if c != "_build"))
def test_the_segments_of_a_band_are_contiguous_in_order_and_never_overlap(config):
    """Each band's segments stand one after the other along their axis, with at least the web between them, in every set."""
    _, pset, env = _env(config, 4)
    values = pset["values"]
    for runs, slot_w, web_w in ((frame.VENT_FAR_LOW, "MCC_VENT_SLOT_W", "MCC_VENT_WEB_W"),
                                (frame.VENT_FAR_HIGH, "MCC_VENT_SLOT_W", "MCC_VENT_WEB_W"),
                                (frame.VENT_LID, "MCC_LID_VENT_SLOT_W", "MCC_LID_VENT_WEB_W")):
        pitch = env.value(slot_w) + env.value(web_w)
        last = None
        for run in runs:
            first, count = env.value(vents._x0(run)), values[vents._count(run)]
            assert count >= 1 and count == int(count), (config, run)
            if last is not None:
                assert first - last >= env.value(web_w) + env.value(slot_w) - 1e-6, (config, run)
            last = first + (count - 1) * pitch


def test_a_segment_with_no_instance_would_be_a_set_flag_and_a_count_of_one():
    """The counts of every set are whole numbers of at least one; a run that does not exist keeps 1 and its flag is set."""
    _, _, _, sets = _build(8)
    for config, pset in sets.items():
        for run in [*BASE_RUNS, *LID_RUNS]:
            assert pset["values"][vents._count(run)] >= 1, (config, run)
        for flag in VENT_FLAGS:
            if pset["suppress"].get(flag):
                assert flag.startswith("Vent_Lid") and config.endswith(".bare"), (config, flag)


def test_the_volume_the_vents_cut_is_the_number_of_slots_times_the_volume_of_a_slot():
    """No oracle needed: each Vent_ feature of the template removes exactly its slots (they stand in solid wall)."""
    result = _replay("Base", 8)
    _, _, env = _env()
    expected = {}
    for run in BASE_RUNS:
        n = env.value(f"V_N_VENT_{run.upper()}")
        expected[f"Vent_{run}_SlotCut"] = -_slot_volume(env, run, True)
        expected[f"Vent_{run}_SlotPat"] = -(n - 1) * _slot_volume(env, run, True)
    got = {f["name"]: f["volume_change_mm3"] for f in result.features if f["name"].startswith("Vent_")}
    assert got == pytest.approx(expected, abs=1e-3)
    lid = _replay("Lid", 4)
    _, _, env = _env(stage=4)
    got = {f["name"]: f["volume_change_mm3"] for f in lid.features if f["name"].startswith("Vent_")}
    rows = env.value("V_N_VENT_LID_ROWS")
    expected = {}
    for run in LID_RUNS:
        n = env.value(f"V_N_VENT_{run.upper()}")
        expected[f"Vent_{run}_SlotCut"] = -_slot_volume(env, run, False)
        expected[f"Vent_{run}_SlotPat"] = -(n * rows - 1) * _slot_volume(env, run, False)
    assert got == pytest.approx(expected, abs=1e-3)


@pytest.mark.parametrize("config", ["_build", "pro-convert-hdmi-plus", "pro-convert-hdmi-tx"])
def test_no_vent_feature_is_dead_in_the_build_configuration_and_in_two_devices(config):
    for component, stage in (("Base", 8), ("Lid", 4)):
        result = _replay(component, stage, config)
        assert [n for n in result.dead_features if n.startswith("Vent_")] == [], (config, component)
        shape = ocp_replay.measure(result.shape)
        assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)


def test_the_bare_configuration_suppresses_the_lid_vents_and_leaves_the_lid_as_stage_3():
    lid = _replay("Lid", 4, "pro-convert-for-ndi-to-hdmi.bare")
    suppressed = {f["name"] for f in lid.features if f.get("suppressed")}
    assert suppressed == {f"Vent_{run}_{what}" for run in LID_RUNS for what in ("SlotCut", "SlotPat")}
    assert ocp_replay.measure(lid.shape)["volume_mm3"] == pytest.approx(_fixture("lid", "L4.bare")["volume_mm3"], rel=1e-5)


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay equals the committed fixture (no OpenSCAD needed)
# --------------------------------------------------------------------------------------------------------------

def test_the_lid_replay_matches_the_committed_fixture():
    result = _replay("Lid", 4)
    shape, fixture = ocp_replay.measure(result.shape), _fixture("lid", "L4")
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    assert result.dead_features == []
    for corner in ("bbox_min", "bbox_max"):
        worst = max(abs(a - b) for a, b in zip(shape[corner], fixture[corner]))
        assert worst <= s1_support.FRAME_TOL, f"L4 {corner} differs from the fixture by {worst:.4f} mm"
    assert shape["volume_mm3"] == pytest.approx(fixture["volume_mm3"], rel=s1_support.VOLUME_GUARD)


def test_the_base_replay_matches_the_fixture_once_every_earlier_stage_is_on_main():
    """With B4, B6 and B7 missing the fixture B8 holds more than the document builds: only the vents' own difference can be
    compared offline (the staged oracle below does the rest).  With nothing missing the replay is the fixture."""
    missing = _missing_base_stages()
    result = _replay("Base", 8)
    shape, fixture = ocp_replay.measure(result.shape), _fixture("base", "B8")
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    if missing:
        return
    for corner in ("bbox_min", "bbox_max"):
        assert max(abs(a - b) for a, b in zip(shape[corner], fixture[corner])) <= s1_support.FRAME_TOL
    assert shape["volume_mm3"] == pytest.approx(fixture["volume_mm3"], rel=s1_support.VOLUME_GUARD)


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against a fresh oracle mesh and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("case_vents")


def test_the_lid_stage_replays_to_its_oracle(work):
    oracle.require_openscad()
    result, entry = _export("Lid", 4, work / "replay-L4")
    mesh_path = work / "replay-L4" / entry["files"][1]
    reference = oracle.render_s2(TEMPLATE, "lid", 4, work / "oracle")
    code, report = s1_support.parity(mesh_path, reference, "L4", work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), _fixture("lid", "L4"), code, report)
    assert s1_support.gate_problems(run) == []


def test_the_base_stage_replays_to_its_staged_oracle(work):
    """Stage 8 against the K4a harness with the missing earlier stages left out (the fixture B8 itself when none is missing).
    The stages left out: see ``_missing_base_stages``; they come back by themselves when their milestones land."""
    oracle.require_openscad()
    missing = _missing_base_stages()
    result, entry = _export("Base", 8, work / "replay-B8")
    mesh_path = work / "replay-B8" / entry["files"][1]
    defines = {"slug": f'"{TEMPLATE}"', "part": '"base"', "stage": "8", "fan": "false", "fan_switch": "false", "rail": "true",
               "lid_vents": "true"}
    (work / "oracle").mkdir(exist_ok=True)
    reference = oracle._export(_staged_harness(missing), defines, work / "oracle" / "staged_B8.stl", "staged B8")
    fixture = oracle.measure(reference) if missing else _fixture("base", "B8")
    code, report = s1_support.parity(mesh_path, reference, "B8", work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), fixture, code, report)
    assert s1_support.gate_problems(run) == []
