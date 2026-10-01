"""C7: the fan aperture and the fan switch of the case master, stage B10 (issue #81, plan 3.4 and 4, verdict A2, D81.4, D81.5, D81.8).

The builders of ``cad/fusion/gen/case/fan.py`` and ``switch.py`` run through the facade on the recording backend, the OpenCascade
replay executes the record with a parameter set and the result is compared with the K4a stage fixtures (``fixtures/s2_stages.json``)
and with a fresh oracle mesh, within the thresholds of the brief (``s1_support.gate_problems``): the template with the fan on
(configuration ``pro-convert-for-ndi-to-hdmi.base_fan``, fixture ``B10``) and the Plus case with fan and switch
(``pro-convert-hdmi-plus``, fixture ``B10.fan_switch``).

Stages are cumulative.  Stage 10 of the base holds the lid fasteners, the cradle, the floor, the side bolt, the patch wall and the
vents; a stage whose milestone has not landed is a stub in ``gen/case`` and the document does not build it.  The reference is then
a *staged oracle*: the K4a harness with exactly those stages left out (``_staged_harness``), rendered fresh, and the offline replay
is checked against the fixture only in the corners the missing stages cannot move; once every earlier milestone is on main the
reference is the committed fixture itself.  The choice follows the record (``_missing_base_stages``), it never skips a test.  The
tests that need the oracle never skip: where OpenSCAD is missing, ``oracle.require_openscad()`` fails them when
``MCC_REQUIRE_OPENSCAD=1`` (CI) and skips them only on a developer machine.
"""
from __future__ import annotations

import functools
import json
import math
import pathlib

import pytest

from cad import params
from cad.fusion.gen.case import fan, frame, switch
from cad.fusion.gen.core import checks, expr
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
PLUS = oracle.PLUS
TEMPLATE_FAN = f"{TEMPLATE}.base_fan"
STAGE = 10
OPENING = "Fan_Aperture_OpeningCut"
FAN_FEATURES = ["Fan_Aperture_ScrewCut", OPENING, "Fan_Aperture_Ring1Rejoin", "Fan_Aperture_Ring2Rejoin", "Fan_Aperture_BarARejoin",
                "Fan_Aperture_BarBRejoin", "Fan_Aperture_BarCRejoin"]
SWITCH_FEATURES = ["Switch_Toggle_PadAdd", "Switch_Toggle_BoreCut", "Switch_Toggle_RecessCut"]
# the order of the record: joins, cuts (fan, then switch), re-joins
RECORD_ORDER = [SWITCH_FEATURES[0], FAN_FEATURES[0], OPENING, *SWITCH_FEATURES[1:], *FAN_FEATURES[2:]]
# the oracle stage that each owner of an earlier milestone stands for (the base stages 3 to 8)
STAGE_OF_OWNER = {"Fastener": 3, "Cradle": 4, "Floor": 5, "SideBolt": 6, "Patch": 7, "Vent": 8}


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _fixture(key: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][key]


def _features(record: dict, prefixes=("Fan_", "Switch_")) -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == "Base" and s["name"].startswith(prefixes)]


def _spec(record: dict, name: str) -> dict:
    (spec,) = [s for s in record["specs"] if s.get("name") == name]
    return spec


def _loops(record: dict, name: str) -> list[dict]:
    return _spec(record, _spec(record, name)["sketch"])["loops"]


@functools.lru_cache(maxsize=None)
def _replay(configuration: str):
    _, record, rows, sets = _build(STAGE)
    pset = sets[configuration]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"], components=["Base"])["Base"]


def _env(configuration: str) -> expr.Env:
    _, _, rows, sets = _build(STAGE)
    return expr.Env(rows, sets[configuration]["values"])


def _changes(configuration: str) -> dict:
    return {f["name"]: f["volume_change_mm3"] for f in _replay(configuration).features}


def _missing_base_stages() -> tuple[int, ...]:
    """The oracle stages below 10 that the document does not build yet: the earlier milestones whose module is still a stub."""
    _, record, _, _ = _build(STAGE)
    present = {name.split("_")[0] for name in _features(record, ("",))}
    return tuple(sorted(stage for owner, stage in STAGE_OF_OWNER.items() if owner not in present))


def _staged_harness(missing: tuple[int, ...]) -> str:
    """The K4a stage harness with the base stages of ``missing`` switched off (the lid part is left as it is)."""
    head, rest = oracle.HARNESS_S2.split("module stage_base", 1)
    base, tail = rest.split("module stage_lid", 1)
    for stage in missing:
        base = base.replace(f"stage >= {stage})", "false)")
    return head + "module stage_base" + base + "module stage_lid" + tail


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

def test_stage_10_records_the_fan_and_switch_features_in_the_order_of_the_phases():
    _, record, _, _ = _build(STAGE)
    assert _features(record) == RECORD_ORDER
    assert sorted(RECORD_ORDER) == sorted(FAN_FEATURES + SWITCH_FEATURES)
    ops = {s["name"]: s["op"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec") and s["component"] == "Base"}
    assert [ops[n] for n in RECORD_ORDER] == ["join"] + ["cut"] * 4 + ["rejoin"] * 5


def test_nothing_of_the_fan_or_the_switch_is_recorded_before_stage_10_and_the_full_build_has_it_all():
    for stage in (8, 9):
        assert _features(_build(stage)[1]) == []
    assert _features(_build(None)[1]) == RECORD_ORDER


def test_the_fan_and_the_switch_touch_the_base_only():
    _, record, _, _ = _build(STAGE)
    lid = [s["name"] for s in record["specs"] if s["component"] == "Lid" and s["name"].startswith(("Fan_", "Switch_"))]
    assert lid == []


def test_the_outermost_ring_is_never_a_feature_and_the_grille_is_two_rings_and_three_bars():
    """D81.8: the opening is cut at the inner diameter of ring 3, so ring 3 stays wall; no key for its outer diameter."""
    _, record, rows, sets = _build(STAGE)
    assert frame.GRILLE_REJOIN_RINGS == (1, 2)
    assert "Fan_Aperture_Ring3Rejoin" not in _features(record)
    assert "V_FAN_RING3_OD" not in {r.get("name") for r in rows if isinstance(r, dict)} | set(sets["_build"]["values"])
    (circle,) = _loops(record, OPENING)
    assert (circle["kind"], circle["args"][2]) == ("circle", "V_FAN_RING3_ID")


def test_every_rejoin_names_the_opening_cut_it_refills():
    _, record, _, _ = _build(STAGE)
    rejoins = [s for s in record["specs"] if s["spec"] == "ExtrudeSpec" and s["op"] == "rejoin"]
    assert [s["name"] for s in rejoins] == FAN_FEATURES[2:]
    assert {s["within"] for s in rejoins} == {OPENING}
    assert _spec(record, OPENING)["op"] == "cut"


def test_the_screw_cut_is_four_circles_on_the_hole_pitch_around_the_fan_centre():
    _, record, _, _ = _build(STAGE)
    loops = _loops(record, "Fan_Aperture_ScrewCut")
    assert [loop["kind"] for loop in loops] == ["circle"] * 4 and {loop["args"][2] for loop in loops} == {"V_FAN_HOLE_D"}
    env = expr.Env(_build(STAGE)[2], _build(STAGE)[3][TEMPLATE_FAN]["values"])
    pitch = env.value("V_FAN_HOLE_PITCH")
    centres = {(round(env.value(loop["args"][0]) - env.value("V_FAN_Y"), 6), round(env.value(loop["args"][1]) - env.value(frame.ZC), 6))
               for loop in loops}
    assert centres == {(sy * pitch / 2, sz * pitch / 2) for sy in (1, -1) for sz in (1, -1)}


def test_the_rings_are_rings_of_the_grille_diameters_and_the_bars_are_one_loop_each():
    _, record, _, _ = _build(STAGE)
    for i in frame.GRILLE_REJOIN_RINGS:
        sketch = _spec(record, _spec(record, f"Fan_Aperture_Ring{i}Rejoin")["sketch"])
        assert (len(sketch["loops"]), len(sketch["holes"])) == (1, 1)
        assert sketch["loops"][0]["args"][2] == f"V_FAN_RING{i}_OD" and sketch["holes"][0]["args"][2] == f"V_FAN_RING{i}_ID"
    for name, kind in (("A", "rect"), ("B", "polygon"), ("C", "polygon")):
        loops = _loops(record, f"Fan_Aperture_Bar{name}Rejoin")
        assert [loop["kind"] for loop in loops] == [kind]
        assert len(_spec(record, _spec(record, f"Fan_Aperture_Bar{name}Rejoin")["sketch"])["holes"]) == 0


@pytest.mark.parametrize("name,angle", [("A", 0.0), ("B", 60.0), ("C", 120.0)])
def test_a_bar_is_two_opposite_spokes_of_the_oracle_at_its_angle(name, angle):
    """A spoke at the oracle's local angle a points to (y, z) = (sin a, -cos a): the bar's corners are its two ends, one spoke width
    wide, about the fan centre; the bar keeps the radius of the oracle's grille (it ends in the wall)."""
    _, record, _, _ = _build(STAGE)
    env = _env(TEMPLATE_FAN)
    cy, cz, r, h = env.value("V_FAN_Y"), env.value(frame.ZC), env.value("V_FAN_OPENING_D") / 2, env.value("MCC_FAN_GRILLE_SPOKE_W") / 2
    a = math.radians(angle)
    s, c = math.sin(a), math.cos(a)
    expected = {(round(cy + sy * r * s + t * h * c, 5), round(cz - sy * r * c + t * h * s, 5)) for sy in (1, -1) for t in (1, -1)}
    (loop,) = _loops(record, f"Fan_Aperture_Bar{name}Rejoin")
    if loop["kind"] == "rect":
        u0, u1, v0, v1 = (env.value(t) for t in loop["args"])
        got = {(round(u, 5), round(v, 5)) for u in (u0, u1) for v in (v0, v1)}
    else:
        got = {(round(env.value(u), 5), round(env.value(v), 5)) for u, v in loop["args"]}
    assert got == expected


def test_the_spoke_pitch_is_sixty_degrees_and_the_bars_use_one_and_two_pitches():
    _, record, _, _ = _build(STAGE)
    assert _env(TEMPLATE_FAN).value("MCC_FAN_GRILLE_SPOKE_PITCH") == pytest.approx(60.0)
    text_b = json.dumps(_loops(record, "Fan_Aperture_BarBRejoin"))
    text_c = json.dumps(_loops(record, "Fan_Aperture_BarCRejoin"))
    assert "sin(MCC_FAN_GRILLE_SPOKE_PITCH)" in text_b and "sin(2 * MCC_FAN_GRILLE_SPOKE_PITCH)" in text_c


def test_the_switch_pad_is_a_loft_on_the_inner_face_and_the_cuts_run_to_the_outer_face():
    _, record, _, _ = _build(STAGE)
    pad = _spec(record, "Switch_Toggle_PadAdd")
    assert (pad["spec"], pad["op"]) == ("LoftSpec", "join")
    sketches = [_spec(record, name) for name in pad["sketches"]]
    assert [s["loops"][0]["args"][2] for s in sketches] == ["V_SWITCH_BODY_D", "V_SWITCH_PAD_D"]
    planes = [_spec(record, name)["offset"] for name in pad["planes"]]
    assert planes == [switch.PAD_X, frame.XIH]
    bore, recess = _spec(record, "Switch_Toggle_BoreCut"), _spec(record, "Switch_Toggle_RecessCut")
    assert (bore["op"], recess["op"]) == ("cut", "cut")
    assert _loops(record, "Switch_Toggle_BoreCut")[0]["args"][2] == "V_SWITCH_BORE_D"
    assert _loops(record, "Switch_Toggle_RecessCut")[0]["args"][2] == "V_SWITCH_BODY_D"


def test_the_flags_have_their_members_and_the_kit_checks_find_nothing_about_them():
    document, record, rows, sets = _build(STAGE)
    findings = checks.run(record, rows, sets, document.get("shared_exceptions", []), owners=document["owners"],
                          protected_prefixes=document["protected_prefixes"])
    assert [str(f) for f in findings if f.id != "CK4"] == []
    assert not [f for f in findings if f.name in ("Fan_Aperture", "Switch_Toggle")]
    assert {"Fan_Aperture", "Switch_Toggle"} <= set(sets["_build"]["suppress"])
    assert sets["_build"]["suppress"]["Fan_Aperture"] is False and sets["_build"]["suppress"]["Switch_Toggle"] is False


def test_the_option_fan_switches_only_the_fan_and_the_switch_never_a_reserve():
    """The flags of the sets: the template without its fan has both set, the template with it only the switch, the plus case neither."""
    _, _, _, sets = _build(STAGE)
    flags = {c: {k: v for k, v in sets[c]["suppress"].items() if k in ("Fan_Aperture", "Switch_Toggle")} for c in
             (TEMPLATE, TEMPLATE_FAN, PLUS)}
    assert flags[TEMPLATE] == {"Fan_Aperture": True, "Switch_Toggle": True}
    assert flags[TEMPLATE_FAN] == {"Fan_Aperture": False, "Switch_Toggle": True}
    assert flags[PLUS] == {"Fan_Aperture": False, "Switch_Toggle": False}
    assert not [k for k in sets[PLUS]["suppress"] if k.startswith("Reserve_")]


def test_the_modules_import_nothing_but_the_frame():
    folder = pathlib.Path(__file__).resolve().parents[1] / "case"
    for module in ("fan.py", "switch.py"):
        imports = [line for line in (folder / module).read_text(encoding="utf-8").splitlines() if line.startswith(("import ", "from "))]
        assert imports == ["from __future__ import annotations", "from . import frame as F"], module


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay of the configurations
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("configuration", [TEMPLATE_FAN, PLUS, "_build"])
def test_the_replay_is_one_valid_solid_with_no_dead_feature(configuration):
    result = _replay(configuration)
    shape = ocp_replay.measure(result.shape)
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    assert result.dead_features == []


def test_no_feature_is_dead_in_any_configuration():
    for configuration in _build(STAGE)[3]:   # the nine configurations and the build configuration
        assert _replay(configuration).dead_features == [], configuration


def test_the_template_with_its_fan_has_the_switch_suppressed_and_every_fan_feature_live():
    changes = _changes(TEMPLATE_FAN)
    assert {n for n, v in changes.items() if n.startswith("Switch_") and v == 0} == set(SWITCH_FEATURES)
    for name in FAN_FEATURES:
        assert changes[name] != 0, name


def test_without_the_fan_flag_cleared_the_fan_and_the_switch_do_nothing():
    changes = _changes(TEMPLATE)
    assert all(changes[name] == 0 for name in FAN_FEATURES + SWITCH_FEATURES)


@pytest.mark.parametrize("configuration", [PLUS, "_build"])
def test_the_volumes_the_features_add_and_remove_follow_the_dimensions(configuration):
    """No oracle needed: the aperture, the rings, the pad, the bore and the recess each change the volume by their own solid."""
    env, changes = _env(configuration), _changes(configuration)
    wall = env.value("MCC_WALL")
    disc = lambda d: math.pi / 4 * env.value(d) ** 2   # noqa: E731
    assert changes[OPENING] == pytest.approx(-disc("V_FAN_RING3_ID") * wall, rel=1e-4)
    assert changes["Fan_Aperture_ScrewCut"] == pytest.approx(-4 * disc("V_FAN_HOLE_D") * wall, rel=1e-4)
    for i in frame.GRILLE_REJOIN_RINGS:
        assert changes[f"Fan_Aperture_Ring{i}Rejoin"] == pytest.approx(
            (disc(f"V_FAN_RING{i}_OD") - disc(f"V_FAN_RING{i}_ID")) * wall, rel=1e-4)
    d1, d2, t = env.value("V_SWITCH_BODY_D"), env.value("V_SWITCH_PAD_D"), env.value("V_SWITCH_PAD_T") - wall
    assert changes["Switch_Toggle_PadAdd"] == pytest.approx(math.pi * t / 12 * (d1 * d1 + d1 * d2 + d2 * d2), rel=1e-4)
    assert changes["Switch_Toggle_BoreCut"] == pytest.approx(-disc("V_SWITCH_BORE_D") * env.value("V_SWITCH_PAD_T"), rel=1e-4)
    recess = env.value("V_SWITCH_RECESS_T")
    assert changes["Switch_Toggle_RecessCut"] == pytest.approx(-(disc("V_SWITCH_BODY_D") - disc("V_SWITCH_BORE_D")) * recess, rel=1e-4)


@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_a_bar_adds_material_only_inside_the_opening_cut(name):
    """Each bar adds less than its own length times its width in the wall: the part in the solid wall beyond the cut adds nothing."""
    env, changes = _env(PLUS), _changes(PLUS)
    inside = env.value("V_FAN_RING3_ID") * env.value("MCC_FAN_GRILLE_SPOKE_W") * env.value("MCC_WALL")
    assert 0 < changes[f"Fan_Aperture_Bar{name}Rejoin"] <= inside + 1e-6


def test_the_grille_leaves_the_opening_open_between_its_rings_and_bars():
    """The opening cut removes the whole disc; the rejoins give back less than half of it (rings and bars, no hub)."""
    changes = _changes(PLUS)
    given = sum(changes[n] for n in FAN_FEATURES[2:])
    assert 0 < given < 0.5 * -changes[OPENING]


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay equals the committed fixture where the stages that are missing cannot matter
# --------------------------------------------------------------------------------------------------------------

def test_the_replay_matches_the_fixture_once_every_earlier_stage_is_on_main():
    """With the side bolt, the patch wall or the vents missing the fixture B10 holds more than the document builds: only the staged
    oracle below can be compared.  With nothing missing the two replays are the fixtures."""
    if _missing_base_stages():
        return
    for configuration, key in ((TEMPLATE_FAN, f"{TEMPLATE}.base.B10"), (PLUS, f"{PLUS}.base.B10.fan_switch")):
        shape, fixture = ocp_replay.measure(_replay(configuration).shape), _fixture(key)
        for corner in ("bbox_min", "bbox_max"):
            assert max(abs(a - b) for a, b in zip(shape[corner], fixture[corner])) <= s1_support.FRAME_TOL, (configuration, corner)
        assert shape["volume_mm3"] == pytest.approx(fixture["volume_mm3"], rel=s1_support.VOLUME_GUARD), configuration


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against a fresh oracle mesh and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("case_fan")


def _stage_10_against_its_oracle(work, configuration: str, slug: str, key: str, fan_switch: bool, label: str) -> None:
    oracle.require_openscad()
    document, _, _, _ = _build(STAGE)
    result = _replay(configuration)
    exports = [e for c in document["configurations"] if c["id"] == configuration for e in c["exports"] if e["component"] == "Base"]
    (entry,) = ocp_replay.export({"Base": result}, {"configurations": [{"id": configuration, "exports": exports}]}, configuration,
                                 work / f"replay-{label}")
    mesh_path = work / f"replay-{label}" / entry["files"][1]
    missing = _missing_base_stages()
    defines = {"slug": f'"{slug}"', "part": '"base"', "stage": str(STAGE), "fan": "true", "fan_switch": "true" if fan_switch else "false",
               "rail": "true", "lid_vents": "true"}
    (work / f"oracle-{label}").mkdir(exist_ok=True)
    reference = oracle._export(_staged_harness(missing), defines, work / f"oracle-{label}" / f"staged_B10_{label}.stl", f"staged B10 {label}")
    fixture = oracle.measure(reference) if missing else _fixture(key)
    code, report = s1_support.parity(mesh_path, reference, "B10", work / f"parity-{label}")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), fixture, code, report)
    assert s1_support.gate_problems(run) == []


def test_stage_10_of_the_template_with_its_fan_replays_to_its_oracle(work):
    """The template's base with the fan on and no switch (the part ``base_fan``): fixture ``B10``."""
    _stage_10_against_its_oracle(work, TEMPLATE_FAN, TEMPLATE, f"{TEMPLATE}.base.B10", False, "template")


def test_stage_10_of_the_plus_case_with_fan_and_switch_replays_to_its_oracle(work):
    """The Plus case's base with the fan and the switch: fixture ``B10.fan_switch``."""
    _stage_10_against_its_oracle(work, PLUS, PLUS, f"{PLUS}.base.B10.fan_switch", True, "plus")
