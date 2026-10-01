"""C8: the reserved bays and the device ghost of the case master (issue #81, plan 3.4 and 4, verdicts D81.7 and D81.11, Q81.2).

The builders ``cad/fusion/gen/case/reserve.py`` and ``ghost.py`` put one box body into each of ``Reserve_FanBay``,
``Reserve_SplitterBay`` and ``Ghost_Device``, from the solver's numeric boxes (``V_FANBAY_*``, ``V_SPLITBAY_*``) and the device box
(``V_DEV_*``) of the parameter set.  The oracle has no stage for these bodies, so the tests compare against the solver's numbers: the
replay of every configuration gives a box whose corners are the parameter values.  They also prove that nothing else changes: the
specs of ``Base`` and ``Lid`` are the same with and without these two calls, that no suppress flag names a ``Reserve_*`` or ``Ghost_*``
feature, and that the document plan never exports them.  Plug envelopes are not modelled (the default of Q81.2).
"""
from __future__ import annotations

import functools
import json
import pathlib

import pytest

from cad import params
from cad.fusion.gen.case import build, frame
from cad.fusion.gen.core import checks, expr, names
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import s1_support
from cad.fusion.replay import ocp_replay
from cad.fusion.runtime import plan as runtime_plan

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
BODIES = {"Reserve_FanBay": "Reserve_FanBay_Body", "Reserve_SplitterBay": "Reserve_SplitterBay_Body", "Ghost_Device": "Ghost_Device_Body"}
KEYS = {"Reserve_FanBay": "V_FANBAY", "Reserve_SplitterBay": "V_SPLITBAY", "Ghost_Device": "V_DEV"}
CASE_FLAG_PREFIXES = ("Reserve_", "Ghost_")


@functools.lru_cache(maxsize=None)
def _build(stage=None):
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, stage)
    return document, json.loads(json.dumps(record)), rows, sets


def _specs(record: dict, component: str) -> list[dict]:
    return [s for s in record["specs"] if s.get("component") == component]


def _features(record: dict, component: str) -> list[str]:
    return [s["name"] for s in _specs(record, component) if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")]


def _replay(configuration: str, component: str):
    _, record, rows, sets = _build()
    pset = sets[configuration]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    result = ocp_replay.replay(record, env, pset["suppress"], components=[component])[component]
    return result, expr.Env(rows, pset["values"])


# --------------------------------------------------------------------------------------------------------------
# Offline: what the builders record
# --------------------------------------------------------------------------------------------------------------

def test_each_reserve_and_the_ghost_is_one_new_box_body():
    _, record, _, _ = _build()
    roles = {c["name"]: c["role"] for c in record["components"]}
    assert roles["Reserve_FanBay"] == roles["Reserve_SplitterBay"] == "reserve" and roles["Ghost_Device"] == "ghost"
    for component, body in BODIES.items():
        assert _features(record, component) == [body]
        (feature,) = [s for s in _specs(record, component) if s["spec"] == "ExtrudeSpec"]
        assert feature["op"] == "new"
        (sketch,) = [s for s in _specs(record, component) if s["spec"] == "SketchSpec"]
        assert (len(sketch["loops"]), len(sketch["holes"]), sketch["loops"][0]["kind"]) == (1, 0, "rect")


def test_the_bodies_are_built_from_the_solvers_boxes_and_nothing_else():
    _, record, _, _ = _build()
    for component, prefix in KEYS.items():
        (sketch,) = [s for s in _specs(record, component) if s["spec"] == "SketchSpec"]
        (feature,) = [s for s in _specs(record, component) if s["spec"] == "ExtrudeSpec"]
        assert sketch["loops"][0]["args"] == [f"{prefix}_X_LO", f"{prefix}_X_HI", f"{prefix}_Y_LO", f"{prefix}_Y_HI"]
        assert feature["start_offset"] == f"{prefix}_Z_LO"
        assert f"{prefix}_Z_HI" in feature["distance"]


def test_the_owners_are_reserve_and_ghost_and_the_names_parse():
    document, _, _, _ = _build()
    assert {"Reserve", "Ghost"} <= set(document["owners"])
    assert [names.parse(body)[0] for body in BODIES.values()] == ["Reserve", "Reserve", "Ghost"]


def test_the_reserves_and_the_ghost_run_only_without_a_stage_limit_after_the_parts():
    """They are no stage of the oracle: a stage-limited build (the replay of the oracle stages) never holds them."""
    for stage in (1, 4, 10):
        _, record, _, _ = _build(stage)
        for component in BODIES:
            assert _specs(record, component) == [], (stage, component)
    _, record, _, _ = _build()
    index = {s["name"]: i for i, s in enumerate(record["specs"]) if s["spec"] == "ExtrudeSpec"}
    parts = [i for n, i in index.items() if n.split("_")[0] not in ("Reserve", "Ghost")]
    assert max(parts) < min(index[b] for b in BODIES.values())


def test_the_two_calls_are_in_the_table_without_a_stage_number():
    rows = [row for row in build.CALLS if row[2].__module__.endswith((".reserve", ".ghost"))]
    assert [(r[0], r[1], r[3]) for r in rows] == [(18, None, ("fan_bay", "splitter_bay")), (18, None, ("ghost",))]


def test_the_two_modules_import_nothing():
    root = pathlib.Path(__file__).resolve().parents[1] / "case"
    for module in ("reserve.py", "ghost.py"):
        text = (root / module).read_text(encoding="utf-8")
        imports = [line for line in text.splitlines() if line.startswith(("import ", "from "))]
        assert imports == ["from __future__ import annotations"], module


# --------------------------------------------------------------------------------------------------------------
# Offline: nothing else changes
# --------------------------------------------------------------------------------------------------------------

def test_base_and_lid_are_the_same_record_without_the_reserves_and_the_ghost(monkeypatch):
    """The two calls never touch Base or Lid: their specs are the same, in the same order, with the two calls removed."""
    _, with_them, _, _ = _build()
    monkeypatch.setattr(build, "CALLS", tuple(row for row in build.CALLS if row[2].__module__.split(".")[-1] not in ("reserve", "ghost")))
    with s1_support.at_repo_root():
        record, _, _ = kitplan.build(kitplan.load_plan(PLAN_PATH), None)
    without = json.loads(json.dumps(record))
    for part in ("Base", "Lid"):
        assert json.dumps(_specs(with_them, part)) == json.dumps(_specs(without, part)), part
    assert [s for s in without["specs"] if s["component"] not in ("Base", "Lid")] == []
    assert json.dumps(with_them["shared_calls"]) == json.dumps(without["shared_calls"])
    assert [c["name"] for c in without["components"]] == [c["name"] for c in with_them["components"]]


def test_no_suppress_flag_names_a_reserve_or_the_ghost_in_any_configuration():
    _, record, _, sets = _build()
    for configuration, pset in sets.items():
        assert not [flag for flag in pset["suppress"] if flag.startswith(CASE_FLAG_PREFIXES)], configuration
    assert not [s["name"] for s in record["specs"] if str(s.get("flag", "")).startswith(CASE_FLAG_PREFIXES)]


def test_the_kit_checks_find_nothing_about_the_reserves_or_the_ghost():
    """CK4 (a flag without a member) belongs to the milestones that have not landed; reserves are required and protected."""
    document, record, rows, sets = _build()
    assert document["required_components"] == ["Reserve_FanBay", "Reserve_SplitterBay"] and document["protected_prefixes"] == ["Reserve_"]
    findings = checks.run(record, rows, sets, document.get("shared_exceptions", []), owners=document["owners"],
                          protected_prefixes=document["protected_prefixes"])
    assert [str(f) for f in findings if f.id != "CK4"] == []
    assert not [f for f in findings if f.name.startswith(CASE_FLAG_PREFIXES)]


def test_the_plan_never_exports_the_reserves_or_the_ghost():
    document, _, _, _ = _build()
    assert sorted(document["never_export"]) == ["Ghost_", "Reserve_"]
    exported = {e["component"] for c in document["configurations"] for e in c["exports"]}
    assert exported == {"Base", "Lid"}


@pytest.mark.parametrize("component", ["Reserve_FanBay", "Reserve_SplitterBay", "Ghost_Device"])
def test_the_runtime_plan_refuses_to_export_a_reserve_or_the_ghost(component):
    document, _, _, _ = _build()
    assert runtime_plan.validate(json.loads(json.dumps(document)), str(s1_support.REPO)) == []
    bad = json.loads(json.dumps(document))
    configuration = next(c for c in bad["configurations"] if c["exports"])
    configuration["exports"].append({"component": component, "target": configuration["exports"][0]["target"], "part": "ghost-or-reserve"})
    problems = runtime_plan.validate(bad, str(s1_support.REPO))
    assert any(component in p and "never_export" in p for p in problems), problems


# --------------------------------------------------------------------------------------------------------------
# Offline: the replay against the solver's numbers
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("component", list(BODIES))
def test_the_box_corners_are_the_parameter_values_in_every_configuration(component):
    prefix = KEYS[component]
    for configuration in _build()[3]:
        result, env = _replay(configuration, component)
        shape = ocp_replay.measure(result.shape)
        low = [env.value(f"{prefix}_{axis}_LO") for axis in "XYZ"]
        high = [env.value(f"{prefix}_{axis}_HI") for axis in "XYZ"]
        assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True), (configuration, component)
        assert shape["bbox_min"] == pytest.approx(low, abs=1e-6), (configuration, component)
        assert shape["bbox_max"] == pytest.approx(high, abs=1e-6), (configuration, component)
        assert shape["volume_mm3"] == pytest.approx(
            (high[0] - low[0]) * (high[1] - low[1]) * (high[2] - low[2]), rel=1e-9), (configuration, component)
        assert result.dead_features == [], (configuration, component)


def test_the_bays_exist_in_every_configuration_with_the_fan_on_or_off():
    """The reservation rule: both bays are present in all configurations; the fan option never switches them."""
    _, _, _, sets = _build()
    fan = {c: sets[c]["suppress"].get("Fan_Aperture") for c in sets}
    assert set(fan.values()) >= {True, False}, "the sets must hold the fan both on and off for this test to mean something"
    for configuration in sets:
        for component in ("Reserve_FanBay", "Reserve_SplitterBay"):
            result, _ = _replay(configuration, component)
            assert ocp_replay.measure(result.shape)["volume_mm3"] > 0, (configuration, component, fan[configuration])


def test_the_frame_has_no_capacity_entry_for_the_reserves():
    """A reserve is one body in every configuration: no group, no count, no flag (D81.7)."""
    assert not [key for key in frame.CAPACITY if "bay" in key or "ghost" in key or "reserve" in key]
