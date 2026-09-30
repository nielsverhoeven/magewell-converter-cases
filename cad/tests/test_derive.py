"""Derived parameter sets (P2-81 verdict B3): a real configuration plus overrides, written by `python -m cad.layout derive`.

The case master is built under such a set (every flag clear, a few keys moved to free positions).  Offline and permanent.
"""
from __future__ import annotations

import copy
import json

import pytest

from cad import layout as LY
from cad import params

SPEC = {"schema": 1, "name": "mcc-case-build", "configuration": "_build",
        "base": {"slug": "pro-convert-hdmi-plus", "configuration": "default"}, "flags": "clear",
        "overrides": {"V_FARRIB5_X": {"value": "-30 mm", "reason": "rib 5 is live in no real configuration; a free position"}}}


@pytest.fixture()
def spec_file(tmp_path):
    path = tmp_path / "build_overrides.json"
    path.write_text(json.dumps(SPEC), encoding="utf-8")
    return path


def changed(**edits):
    spec = copy.deepcopy(SPEC)
    for key, value in edits.items():
        spec[key] = value
    return spec


def test_a_derived_set_is_the_base_with_every_flag_clear_and_the_overrides_applied(spec_file, tmp_path):
    out = tmp_path / "build_set.json"
    LY.write_derived(spec_file, out)
    base = params.parameter_set(params.VARIANTS_DIR / "pro-convert-hdmi-plus.json", "default")
    got = params.parameter_set(out, "_build")
    assert params.parameter_set_configurations(out) == ["_build"]
    assert set(got["values"]) == set(base["values"]) and set(got["suppress"]) == set(base["suppress"])
    assert got["units"] == base["units"] and got["slots"] == base["slots"]
    assert not any(got["suppress"].values()) and any(base["suppress"].values())
    differing = {k for k in base["values"] if got["values"][k] != base["values"][k]}
    assert differing == {"V_FARRIB5_X"} and got["values"]["V_FARRIB5_X"] == -30.0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["derived"]["base"] == "pro-convert-hdmi-plus/default" and doc["derived"]["overrides"]["V_FARRIB5_X"]["reason"]


def test_the_build_rib_is_a_free_position_so_no_rib_is_dead(spec_file, tmp_path):
    out = tmp_path / "build_set.json"
    LY.write_derived(spec_file, out)
    v = params.parameter_set(out, "_build")["values"]
    ribs = [v[f"V_FARRIB{i}_X"] for i in range(1, 6)]
    assert len(set(ribs)) == 5                                   # five distinct ribs: the fifth does not sit on the fourth


def test_flags_keep_leaves_the_base_flags(spec_file, tmp_path):
    spec = changed(flags="keep")
    path = tmp_path / "keep.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp_path / "keep_set.json"
    LY.write_derived(path, out)
    base = params.parameter_set(params.VARIANTS_DIR / "pro-convert-hdmi-plus.json", "default")
    assert params.parameter_set(out, "_build")["suppress"] == base["suppress"]


def test_a_derived_set_is_total_with_the_variant_files_and_the_registry_accepts_it(spec_file, tmp_path):
    out = tmp_path / "build_set.json"
    LY.write_derived(spec_file, out)
    files = sorted(params.VARIANTS_DIR.glob("*.json")) + [out]
    assert params.check_parameter_sets(files) == []
    rows = params.registry([params.CONSTANTS_CSV], files)
    assert len([r for r in rows if r["kind"] == "solver"]) == 96


BAD_SPECS = {
    "unknown key": (changed(overrides={"V_NOPE": {"value": "1 mm", "reason": "x"}}), "not a parameter"),
    "a flag is not overridden": (changed(overrides={"Cradle_FarRib5": {"value": "1", "reason": "x"}}), "not a parameter"),
    "unit differs (none for mm)": (changed(overrides={"V_FARRIB5_X": {"value": "30", "reason": "x"}}), r"is '30' \(none\)"),
    "unit differs (deg for mm)": (changed(overrides={"V_FARRIB5_X": {"value": "30 deg", "reason": "x"}}), r"is '30 deg' \(deg\)"),
    "unit differs (mm for a count)": (changed(overrides={"V_N_DECK_X": {"value": "4 mm", "reason": "x"}}), r"is '4 mm' \(mm\)"),
    "count below one": (changed(overrides={"V_N_DECK_X": {"value": "0", "reason": "x"}}), "at least 1"),
    "no reason": (changed(overrides={"V_FARRIB5_X": {"value": "-30 mm", "reason": " "}}), "reason"),
    "unknown base": (changed(base={"slug": "nope", "configuration": "default"}), "does not exist"),
    "unknown configuration": (changed(base={"slug": "pro-convert-hdmi-plus", "configuration": "base_fan"}), "no configuration"),
    "bad flags mode": (changed(flags="set"), "flags must be"),
    "bad schema": (changed(schema=2), "schema 1"),
    "extra key": (dict(SPEC, extra=1), "exactly the keys"),
    "bad name": (changed(name="Mcc Case"), "name"),
}


@pytest.mark.parametrize("name", sorted(BAD_SPECS))
def test_a_malformed_spec_is_refused_with_the_reason(name):
    spec, message = BAD_SPECS[name]
    with pytest.raises(ValueError, match=message):
        LY.derive_document(spec)


def test_the_check_reports_a_missing_a_stale_and_a_fresh_file(spec_file, tmp_path):
    out = tmp_path / "build_set.json"
    assert "missing" in LY.check_derived(spec_file, out)[0]
    LY.write_derived(spec_file, out)
    assert LY.check_derived(spec_file, out) == []
    out.write_text(out.read_text(encoding="utf-8").replace("-30 mm", "-31 mm"), encoding="utf-8")
    assert "stale" in LY.check_derived(spec_file, out)[0]


def test_the_command_writes_checks_and_reports_a_bad_spec(spec_file, tmp_path, capsys):
    out = tmp_path / "build_set.json"
    assert LY.main(["derive", str(spec_file), "--out", str(out)]) == 0 and out.is_file()
    assert LY.main(["derive", str(spec_file), "--out", str(out), "--check"]) == 0
    out.write_text("{}\n", encoding="utf-8")
    assert LY.main(["derive", str(spec_file), "--out", str(out), "--check"]) == 1
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(changed(flags="set")), encoding="utf-8")
    assert LY.main(["derive", str(bad), "--out", str(out)]) == 2
    assert LY.main(["derive", str(spec_file)]) == 2
    assert "flags must be" in capsys.readouterr().out
