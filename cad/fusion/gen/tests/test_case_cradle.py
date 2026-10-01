"""C3: the cradle of the case master, stage B4 (issue #81, plan 3.4 and 4, verdict A8, B1, D81.4, D81.5).

The builder ``cad/fusion/gen/case/cradle.py`` runs through the facade on the recording backend, the OpenCascade replay executes the
record with the parameter set of the template (``pro-convert-for-ndi-to-hdmi``, configuration ``default``) and the result is compared
with a fresh oracle mesh: every box corner within 0.02 mm, no residual piece both above 0.5 mm3 and thicker than 0.05 mm, the
residual at most 0.2 % of the part (the thresholds of the brief, applied by ``s1_support.gate_problems``).

Stage B4 of the K4a fixture is cumulative: it holds the lid fasteners of stage B3 as well as the cradle.  While the lid fasteners
(milestone C2) are not in the document, the oracle of this test is the stage oracle of ``oracle.HARNESS_S2`` with only its stage 3
block (the bosses, webs and bores) switched off, so it holds exactly the features this document builds: the shell, the tongue and the
cradle.  Once ``Fastener_*`` features are in the document the stock fixture ``B4`` and the stock stage render are used.  The choice
follows the record, it never skips a test.  The tests that need the oracle never skip: where OpenSCAD is missing,
``oracle.require_openscad()`` fails them when ``MCC_REQUIRE_OPENSCAD=1`` (CI) and skips them only on a developer machine.
"""
from __future__ import annotations

import functools
import json

import pytest

from cad import params
from cad.fusion.gen.case import build, frame
from cad.fusion.gen.core import checks
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay
from cad.tools import openscad_runner

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
TEMPLATE = oracle.TEMPLATE
STAGE = 4
SHELL = ["Shell_Floor_Body", "Shell_Walls_Add", "Shell_Tongue_RingAdd"]
DECK = ["Cradle_Deck_FrameAdd", "Cradle_Deck_RibXAdd", "Cradle_Deck_RibXPat", "Cradle_Deck_RibYAdd", "Cradle_Deck_RibYPat"]
RIBS = [name for i in (1, 2, 3, 4, 5) for name in (f"Cradle_FarRib{i}_LegsAdd", f"Cradle_FarRib{i}_BodyAdd")]
CRADLE = DECK + RIBS
# The legs of far-flank rib 2 stand at x = -12 mm, 0.64 mm from the far-middle lid fastener (x = -12.64): they lie wholly inside that
# fastener's boss and web (stage B3 joins first), so the join changes no volume.  The geometry is the oracle's and the replay
# matches it; the feature is dead in all nine configurations and in the build configuration.  Reported to the lead, see the PR.
KNOWN_DEAD = ["Cradle_FarRib2_LegsAdd"]
FLAGS = [f"Cradle_FarRib{i}" for i in (1, 2, 3, 4, 5)]


@functools.lru_cache(maxsize=None)
def _build(stage):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _features(record: dict, component: str) -> list[str]:
    return [s["name"] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")
            and s["component"] == component]


def _spec(record: dict, name: str) -> dict:
    (spec,) = [s for s in record["specs"] if s.get("name") == name]
    return spec


def _replay(configuration: str = TEMPLATE, stage: int = STAGE):
    _, record, rows, sets = _build(stage)
    pset = sets[configuration]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"], components=["Base"])["Base"]


def _has_lid_fasteners() -> bool:
    _, record, _, _ = _build(STAGE)
    return any(name.startswith("Fastener_") for name in _features(record, "Base"))


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builder records
# --------------------------------------------------------------------------------------------------------------

def test_stage_4_records_the_deck_and_the_five_far_flank_ribs_after_the_shell():
    _, record, _, _ = _build(STAGE)
    names = _features(record, "Base")
    assert [n for n in names if not n.startswith("Fastener_")] == SHELL + CRADLE   # the shell, then the cradle, in the plan's order
    assert names.index("Cradle_Deck_FrameAdd") > max(names.index(n) for n in SHELL)


def test_the_far_ribs_follow_the_capacity_table():
    assert frame.FAR_RIBS == (1, 2, 3, 4, 5) and RIBS == [
        f"Cradle_FarRib{i}_{part}Add" for i in frame.FAR_RIBS for part in ("Legs", "Body")]


def test_no_cradle_feature_is_recorded_before_stage_4():
    _, record, _, _ = _build(3)
    assert not [n for n in _features(record, "Base") if n.startswith("Cradle_")]


def test_every_cradle_feature_is_a_join_or_a_pattern_of_a_join():
    _, record, _, _ = _build(STAGE)
    for name in CRADLE:
        spec = _spec(record, name)
        assert spec["spec"] == ("PatternSpec" if name.endswith("Pat") else "ExtrudeSpec")
        if spec["spec"] == "ExtrudeSpec":
            assert spec["op"] == "join", name


def test_the_deck_frame_is_a_ring_and_the_legs_are_two_rectangles():
    _, record, _, _ = _build(STAGE)
    frame_sketch = _spec(record, _spec(record, "Cradle_Deck_FrameAdd")["sketch"])
    assert (len(frame_sketch["loops"]), len(frame_sketch["holes"])) == (1, 1)
    legs_sketch = _spec(record, _spec(record, "Cradle_FarRib1_LegsAdd")["sketch"])
    assert (len(legs_sketch["loops"]), len(legs_sketch["holes"])) == (2, 0)
    body_sketch = _spec(record, _spec(record, "Cradle_FarRib1_BodyAdd")["sketch"])
    assert (len(body_sketch["loops"]), len(body_sketch["holes"])) == (1, 0)


def test_the_patterns_count_with_the_solvers_keys():
    _, record, _, _ = _build(STAGE)
    x, y = _spec(record, "Cradle_Deck_RibXPat"), _spec(record, "Cradle_Deck_RibYPat")
    assert (x["axis"], x["count"], x["pitch"], x["seed"]) == ("X", "V_N_DECK_X", "V_DECK_PITCH_X", "Cradle_Deck_RibXAdd")
    assert (y["axis"], y["count"], y["pitch"], y["seed"]) == ("Y", "V_N_DECK_Y", "V_DECK_PITCH_Y", "Cradle_Deck_RibYAdd")


def test_the_far_ribs_read_their_own_position_key():
    _, record, _, _ = _build(STAGE)
    for i in frame.FAR_RIBS:
        for part in ("Legs", "Body"):
            spec = _spec(record, f"Cradle_FarRib{i}_{part}Add")
            sketch = _spec(record, spec["sketch"])
            assert f"V_FARRIB{i}_X" in json.dumps(sketch)
            others = [f"V_FARRIB{j}_X" for j in frame.FAR_RIBS if j != i]
            assert not any(k in json.dumps(sketch) for k in others)


def test_the_kit_checks_find_no_cradle_flag_without_a_member():
    """Every Cradle_FarRib flag has its two features now; what is left without a member belongs to later milestones."""
    document, record, rows, sets = _build(STAGE)
    findings = checks.run(record, rows, sets, document.get("shared_exceptions", []), owners=document["owners"],
                          protected_prefixes=document["protected_prefixes"])
    assert [str(f) for f in findings if f.id != "CK4"] == []
    assert not [f for f in findings if f.name in FLAGS]


def test_the_cradle_features_are_in_the_sets_of_their_flags():
    from cad.fusion.gen.core import names

    for name in CRADLE:
        owner, set_name, _ = names.parse(name)
        assert owner == "Cradle"
        if set_name.startswith("FarRib"):
            assert f"{owner}_{set_name}" in FLAGS


def test_the_module_imports_nothing_but_the_frame():
    import pathlib

    text = (pathlib.Path(__file__).resolve().parents[1] / "case" / "cradle.py").read_text(encoding="utf-8")
    imports = [line for line in text.splitlines() if line.startswith(("import ", "from "))]
    assert imports == ["from __future__ import annotations", "from . import frame as F"]


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay of the template and of the build configuration
# --------------------------------------------------------------------------------------------------------------

def test_the_replay_of_the_template_is_one_valid_solid_and_only_the_known_leg_is_dead():
    result = _replay()
    shape = ocp_replay.measure(result.shape)
    assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True)
    assert result.dead_features == KNOWN_DEAD


def test_the_known_dead_leg_is_dead_in_every_configuration_and_nothing_else_is():
    for configuration in _build(STAGE)[3]:
        assert _replay(configuration).dead_features == KNOWN_DEAD, configuration


def test_the_fifth_far_rib_is_suppressed_in_the_template_and_live_in_the_build_configuration():
    template = _replay()
    live = {f["name"]: f["volume_change_mm3"] for f in template.features}
    assert live["Cradle_FarRib4_BodyAdd"] > 0 and live["Cradle_FarRib5_BodyAdd"] == live["Cradle_FarRib5_LegsAdd"] == 0
    built = _replay("_build")
    changes = {f["name"]: f["volume_change_mm3"] for f in built.features}
    assert built.dead_features == KNOWN_DEAD
    for name in CRADLE:
        assert (changes[name] > 0) == (name not in KNOWN_DEAD), name


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against a fresh oracle mesh and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("case_cradle")


_LID_FASTENER_BLOCK = "            if (stage >= 3)\n                for (p = lid_pos) {"


def _oracle_mesh(out_dir):
    """The oracle of the document up to stage 4: the stock stage render once the lid fasteners are in the document, else the stage
    oracle with its stage 3 block (bosses, webs, bores) switched off."""
    if _has_lid_fasteners():
        return oracle.render_s2(TEMPLATE, "base", STAGE, out_dir)
    assert _LID_FASTENER_BLOCK in oracle.HARNESS_S2, "the stage oracle no longer has its stage 3 block in this shape"
    harness = oracle.HARNESS_S2.replace(_LID_FASTENER_BLOCK, _LID_FASTENER_BLOCK.replace("stage >= 3", "stage == 3"))
    defines = {"slug": f'"{TEMPLATE}"', "part": '"base"', "stage": str(STAGE), "fan": "false", "fan_switch": "false",
               "rail": "true", "lid_vents": "true"}
    return oracle._export(harness, defines, out_dir / "s2_cradle_without_lid_fasteners.stl", "B4 without the lid fasteners")


def test_stage_4_replays_to_its_oracle(work):
    oracle.require_openscad()
    document, _, _, _ = _build(STAGE)
    result = _replay()
    exports = [e for c in document["configurations"] if c["id"] == TEMPLATE for e in c["exports"] if e["component"] == "Base"]
    (entry,) = ocp_replay.export({"Base": result}, {"configurations": [{"id": TEMPLATE, "exports": exports}]}, TEMPLATE,
                                 work / "replay-B4")
    mesh_path = work / "replay-B4" / entry["files"][1]
    reference = _oracle_mesh(work / "oracle")
    stages = oracle.load_fixture(oracle.S2_FIXTURE)["stages"]
    fixture = dict(stages[f"{TEMPLATE}.base.B4"])
    if not _has_lid_fasteners():
        fixture["volume_mm3"] = oracle.measure(reference)["volume_mm3"]   # the box is the fixture's, the volume the render's
    code, report = s1_support.parity(mesh_path, reference, "B4", work / "parity")
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh_path), fixture, code, report)
    # the only problem the gate may report is the known dead leg: the box corners, the volume, the parity verdict and the residual pass
    assert s1_support.gate_problems(run) == ([f"dead features (change no volume): {KNOWN_DEAD}"])
