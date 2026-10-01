"""C1: the case document plan, the capacity table and the build configuration (issue #81, plan 3.2, 3.8, 3.9; verdict B1, B3, B5).

Offline: nothing here needs OpenSCAD, OpenCascade or Fusion.  The key set of the parameter sets is the contract with the solver
(``cad/layout.py``, issue #77); this file proves the one table of capacities ``frame.CAPACITY`` against it in both directions,
the build configuration against its hand-written spec, and the document plan against the runtime's reader and the kit's checks.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from cad import layout
from cad.fusion.gen.case import frame
from cad.fusion.gen.core import checks, plan as kitplan
from cad.fusion.gen.tests import s1_support
from cad.fusion.runtime import plan as runtime_plan

REPO = s1_support.REPO
CASE = REPO / "cad" / "fusion" / "gen" / "case"
PLAN = "cad/fusion/documents/mcc-case.json"
OVERRIDES = CASE / "build_overrides.json"
BUILD_SET = CASE / "build_set.json"
VARIANTS = sorted((REPO / "cad" / "parameters" / "variants").glob("*.json"))
SLUGS = ("pro-convert-for-ndi-to-aio", "pro-convert-for-ndi-to-hdmi-4k", "pro-convert-for-ndi-to-hdmi",
         "pro-convert-for-ndi-to-sdi", "pro-convert-hdmi-plus", "pro-convert-hdmi-tx", "pro-convert-sdi-plus", "pro-convert-sdi-tx")
FLAG_COUNT, KEY_COUNT = 24, 96   # after issue #87 (no strap keys) and verdict B1 and B2


def _json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _configurations(path) -> dict:
    return _json(path)["configurations"]


# The names the capacity table implies (verdict B1): one row per family, key names and flag names.
def expected_keys() -> dict[str, str]:
    """``{key name: flag of its set}`` of every key that the capacity table indexes."""
    out: dict[str, str] = {}
    for i in frame.SLOTS:
        for suffix in ("X", "SEAT_D", "WIN_D"):
            out[f"V_SLOT{i}_{suffix}"] = f"Patch_Slot{i}"
    for i in frame.FAR_RIBS:
        out[f"V_FARRIB{i}_X"] = f"Cradle_FarRib{i}"
    for runs, first in ((frame.VENT_FAR_LOW, "X0"), (frame.VENT_FAR_HIGH, "X0"), (frame.VENT_EXH, "X0"),
                        (frame.VENT_NEGX, "Y0"), (frame.VENT_LID, "X0")):
        for run in runs:
            out[f"V_VENT_{run.upper()}_{first}"] = out[f"V_N_VENT_{run.upper()}"] = f"Vent_{run}"
    for i in frame.GRILLE_REJOIN_RINGS:
        out[f"V_FAN_RING{i}_OD"] = out[f"V_FAN_RING{i}_ID"] = "Fan_Aperture"
    out[f"V_FAN_RING{frame.CAPACITY['fan_rings']}_ID"] = "Fan_Aperture"   # the outermost ring gives the opening: no OD key
    return out


KEY_FAMILIES = (r"V_SLOT\d+_\w+", r"V_FARRIB\d+_X", r"V_N?_?VENT_(?:FARLO|FARUP|EXH|NEGX|LID)[A-Z](?:_X0|_Y0)?", r"V_FAN_RING\d+_(?:OD|ID)")
FLAG_FAMILY = r"Patch_Slot\d+|Cradle_FarRib\d+|Vent_(?:FarLo|FarUp|Exh|NegX|Lid)[A-Z]"


def indexed_keys(parameters) -> set[str]:
    run = re.compile(r"V_(?:N_)?VENT_(?:FARLO|FARUP|EXH|NEGX|LID)[A-Z](?:_X0|_Y0)?")
    others = [re.compile(p) for p in (KEY_FAMILIES[0], KEY_FAMILIES[1], KEY_FAMILIES[3])]
    return {k for k in parameters if run.fullmatch(k) or any(o.fullmatch(k) for o in others)}


# --------------------------------------------------------------------------------------------------------------
# The capacity table (verdict B1)
# --------------------------------------------------------------------------------------------------------------

def test_the_capacity_table_equals_the_solvers():
    assert frame.CAPACITY == layout.CAPACITY
    assert frame.CAPACITY == {"slots": 4, "far_ribs": 5, "far_low": 3, "far_high": 2, "exhaust": 1, "negx": 1, "lid": 2, "fan_rings": 3}


def test_the_tuples_of_the_frame_follow_the_table():
    assert frame.SLOTS == (1, 2, 3, 4) and frame.FAR_RIBS == (1, 2, 3, 4, 5)
    assert frame.VENT_FAR_LOW == ("FarLoA", "FarLoB", "FarLoC") and frame.VENT_FAR_HIGH == ("FarUpA", "FarUpB")
    assert frame.VENT_EXH == ("ExhA",) and frame.VENT_NEGX == ("NegXA",) and frame.VENT_LID == ("LidA", "LidB")
    assert frame.GRILLE_REJOIN_RINGS == (1, 2)


@pytest.mark.parametrize("path", VARIANTS, ids=lambda p: p.stem)
def test_the_table_and_the_key_set_agree_in_both_directions(path):
    """Every key and flag the table implies is in every configuration; every capacity-indexed key and flag is implied."""
    expected = expected_keys()
    for config, doc in _configurations(path).items():
        got = indexed_keys(doc["parameters"])
        assert got - set(expected) == set(), f"{path.stem}/{config}: keys the table does not account for"
        assert set(expected) - got == set(), f"{path.stem}/{config}: keys the table needs and the set lacks"
        flags = {f for f in doc["flags"] if re.fullmatch(FLAG_FAMILY, f)}
        assert flags == set(expected.values()) - {"Fan_Aperture"}, f"{path.stem}/{config}: indexed flags"


@pytest.mark.parametrize("path", VARIANTS, ids=lambda p: p.stem)
def test_every_set_has_the_same_96_keys_and_24_flags(path):
    configs = _configurations(path)
    reference = next(iter(configs.values()))
    for config, doc in configs.items():
        assert (len(doc["parameters"]), len(doc["flags"])) == (KEY_COUNT, FLAG_COUNT), f"{path.stem}/{config}"
        assert doc["parameters"].keys() == reference["parameters"].keys() and doc["flags"].keys() == reference["flags"].keys()
        assert not [k for k in doc["parameters"] if "STRAP" in k or "STACK" in k]   # issue #87


def test_no_case_module_holds_a_count_of_its_own():
    for path in sorted(CASE.glob("*.py")):
        if path.name != "frame.py":
            assert not re.search(r"range\(\s*\d", path.read_text(encoding="utf-8")), f"{path.name}: a range over a literal count"


def test_frame_holds_strings_and_tuples_only():
    for name, value in vars(frame).items():
        if not name.startswith("_") and name != "annotations":
            assert isinstance(value, (str, tuple, dict)), f"frame.{name} is a {type(value).__name__}"


# --------------------------------------------------------------------------------------------------------------
# The build configuration (verdict B3)
# --------------------------------------------------------------------------------------------------------------

def test_there_is_no_build_set_module_in_the_case_package():
    assert not (CASE / "build_set.py").exists()


def test_the_only_override_is_the_fifth_far_flank_rib():
    spec = _json(OVERRIDES)
    assert set(spec["overrides"]) == {"V_FARRIB5_X"}
    assert spec["flags"] == "clear" and spec["base"] == {"slug": "pro-convert-hdmi-plus", "configuration": "default"}
    assert all(entry["reason"].strip() for entry in spec["overrides"].values())


def test_the_build_set_is_fresh_total_and_derived_from_the_spec():
    assert layout.check_derived(OVERRIDES, BUILD_SET) == []
    built = _configurations(BUILD_SET)["_build"]
    base = _configurations(REPO / "cad" / "parameters" / "variants" / "pro-convert-hdmi-plus.json")["default"]
    assert not any(built["flags"].values()) and built["flags"].keys() == base["flags"].keys()
    assert {k for k in built["parameters"] if built["parameters"][k] != base["parameters"][k]} == {"V_FARRIB5_X"}


def test_an_override_names_only_a_key_of_a_set_that_the_base_suppresses():
    """The key's set is suppressed in the base configuration and no object of another set uses the key."""
    spec = _json(OVERRIDES)
    base = _configurations(REPO / "cad" / "parameters" / "variants" / f"{spec['base']['slug']}.json")[spec["base"]["configuration"]]
    record = kitplan.build(s1_support_plan())[0]
    for key in spec["overrides"]:
        owner_set = expected_keys()[key]
        assert base["flags"][owner_set] is True, f"{key} belongs to {owner_set}, which {spec['base']['slug']} does not suppress"
        for item in record["specs"]:
            if key in json.dumps(item):
                assert f"{item['name'].split('_')[0]}_{item['name'].split('_')[1]}" == owner_set, f"{item['name']} uses {key}"


def s1_support_plan() -> dict:
    with s1_support.at_repo_root():
        return kitplan.load_plan(PLAN)


# --------------------------------------------------------------------------------------------------------------
# The document plan (contract C3 of #79)
# --------------------------------------------------------------------------------------------------------------

def test_the_runtime_accepts_the_plan():
    loaded = runtime_plan.load(str(REPO), PLAN)
    assert loaded["document"] == "MCC-Case" and loaded["build_configuration"] == "_build"
    assert loaded["builder"] == {"module": "cad.fusion.gen.case.build", "entry": "build", "options": {"stage": None}}


def test_the_plan_lists_the_planned_configurations_and_exports():
    document = _json(REPO / PLAN)
    configs = {c["id"]: c for c in document["configurations"]}
    assert set(configs) == set(SLUGS) | {"_build", "pro-convert-for-ndi-to-hdmi.base_fan", "pro-convert-for-ndi-to-hdmi.bare"}
    for slug in SLUGS:
        assert configs[slug]["set"] == {"file": f"cad/parameters/variants/{slug}.json", "config": "default"}
        assert configs[slug]["exports"] == [{"component": "Base", "target": slug, "part": "base"},
                                            {"component": "Lid", "target": slug, "part": "lid"}]
    assert configs["pro-convert-for-ndi-to-hdmi.base_fan"]["exports"] == [
        {"component": "Base", "target": "pro-convert-for-ndi-to-hdmi", "part": "base_fan"}]
    assert configs["pro-convert-for-ndi-to-hdmi.bare"]["exports"] == [] and configs["_build"]["exports"] == []
    assert configs["_build"]["set"] == {"file": "cad/fusion/gen/case/build_set.json", "config": "_build"}


def test_the_plan_names_the_protected_components_and_the_build_inputs():
    document = _json(REPO / PLAN)
    assert document["owners"] == ["Shell", "Patch", "Floor", "Cradle", "Vent", "Fan", "Switch", "SideBolt", "Fastener", "Rail",
                                  "Ghost", "Reserve"]
    assert document["required_components"] == ["Reserve_FanBay", "Reserve_SplitterBay"]
    assert document["protected_prefixes"] == ["Reserve_"] and document["never_export"] == ["Reserve_", "Ghost_"]
    assert "cad/fusion/gen/case/build_set.json" in document["inputs"] and "cad/fusion/gen/case/**/*.py" in document["inputs"]
    assert document["aba"] is True and document["shared_exceptions"] == []
    # No inventory key until C9 (verdict B5): test_fresh asks the runtime in this process, whose inputs gate sees every cad module
    # a pytest session has loaded, so a plan that names an inventory cannot pass there.  C9 adds the key and the file together and removes this line.
    assert "inventory" not in document and not (REPO / "cad" / "fusion" / "inventory" / "mcc-case.json").exists()


# The flags whose set has members since a case milestone landed; each milestone C2 to C8 adds its flags here.
FLAGS_WITH_MEMBERS = {"Fastener_PatchMid", "Fastener_FarMid", "Floor_RailSill", "Rail_Female"}   # C2, C4
FLAGS_WITH_MEMBERS |= {f"Cradle_FarRib{i}" for i in frame.FAR_RIBS}   # C3
FLAGS_WITH_MEMBERS |= {f"Patch_Slot{i}" for i in frame.SLOTS}   # C5


def test_the_kit_checks_find_nothing_but_flags_of_sets_that_are_not_built_yet():
    """A flag whose set has no member yet is CK4; every milestone C2 to C8 removes its flags from the findings."""
    document = s1_support_plan()
    with s1_support.at_repo_root():
        record, rows, sets = kitplan.build(document)
    findings = checks.run(record, rows, sets, document.get("shared_exceptions", []), owners=document["owners"],
                          protected_prefixes=document["protected_prefixes"])
    flags = set(_configurations(BUILD_SET)["_build"]["flags"])
    assert [str(f) for f in findings if f.id != "CK4"] == []
    assert {f.name for f in findings} <= flags - FLAGS_WITH_MEMBERS


def test_the_offline_run_reaches_the_gates_and_fails_only_on_flags_without_members():
    # a fresh process: the runtime's inputs gate would see the modules this test process has loaded
    done = subprocess.run([sys.executable, str(REPO / "scripts" / "fusion_run.py"), "plan", PLAN], cwd=REPO, capture_output=True,
                          text=True)
    result = json.loads(done.stdout)
    assert result["stage"].startswith("gates"), (result["stage"], result["violations"])
    assert result["violations"], "the flags of C3 to C8 are members-less until those land; if this is empty a flag was lost"
    assert not [v for v in result["violations"] if any(f"flag {flag} " in v for flag in FLAGS_WITH_MEMBERS)], result["violations"]
    assert all(re.fullmatch(r"flags: flag [A-Za-z0-9]+_[A-Za-z0-9]+ has no member in the document", v) for v in result["violations"]), \
        result["violations"]
