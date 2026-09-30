"""S0 for issue #76: cad/ is a verified mirror of the frozen OpenSCAD sources.

Two links, both while lib/mcc exists (issue #86 deletes this module, cad/tools and the fixture's role as
a gate; the fixture then becomes an ordinary golden or is deleted with the oracle):

    cad/**  ==  cad/fixtures/scad_values.json      offline, always runs            (test_cad_equals_fixture)
    fixture ==  a fresh OpenSCAD run                      needs OpenSCAD, CI sets MCC_REQUIRE_OPENSCAD=1
"""
from __future__ import annotations

import csv
import math
import json
import shutil
from pathlib import Path

import pytest

from cad import params
from cad import params as P

tools = pytest.importorskip("cad.tools.scad_export", reason="cad/tools removed after the cutover (#86)")


def test_cad_equals_the_committed_fixture(scad_values):
    assert tools.compare_cad_to_values(scad_values) == []


@pytest.mark.openscad
def test_fixture_and_cad_equal_a_fresh_openscad_run(openscad_exe):
    assert tools.check() == []


def test_a_variant_that_switches_tripod_insert_on_cannot_be_expressed():
    """The option left the closed list (P2-81 Q81.3): false is dropped, true is refused (T1-81.7)."""
    assert tools.case_options_of("x", {"fan": True, "tripod_insert": False}) == {"fan": True}
    with pytest.raises(ValueError, match="T1-81.7"):
        tools.case_options_of("x", {"fan": True, "tripod_insert": True})


def test_fixture_documents_which_oracle_files_it_came_from(scad_values):
    files = scad_values["oracle_files"]
    assert "lib/mcc/constants.scad" in files and len(files) == 1 + 8 + 8
    assert all(len(h) == 64 for h in files.values())


# ---- the gate must actually fail on drift: mutate a copy of cad/ and expect the named problem ----------------


@pytest.fixture()
def cad_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "cad"
    shutil.copytree(params.CAD_DIR, dst, ignore=shutil.ignore_patterns("__pycache__", "tests", "tools", "*.pyc"))
    return dst


def _edit_csv(cad: Path, name: str, column: int, new: str) -> None:
    path = cad / "parameters" / "constants.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        table = list(csv.reader(fh))
    for row in table:
        if row[0] == name:
            row[column] = new
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh, lineterminator="\n").writerows(table)


def test_a_changed_constant_is_reported(scad_values, cad_copy):
    _edit_csv(cad_copy, "MCC_WALL", 2, "3.1 mm")
    problems = tools.compare_cad_to_values(scad_values, cad_copy)
    assert any("MCC_WALL" in p for p in problems) and any("MCC_T_PATCH" in p for p in problems)


def test_a_changed_derived_expression_is_reported(scad_values, cad_copy):
    _edit_csv(cad_copy, "MCC_T_PATCH", 2, "MCC_PANEL_BEZEL_T + MCC_WALL")
    assert any("MCC_T_PATCH" in p for p in tools.compare_cad_to_values(scad_values, cad_copy))


def test_a_missing_and_an_extra_row_are_reported(scad_values, cad_copy):
    path = cad_copy / "parameters" / "constants.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    kept = [l for l in lines if not l.startswith("MCC_FLOOR_T,")] + ["MCC_INVENTED,mm,1 mm,x | src=nowhere | conf=assumed"]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    problems = tools.compare_cad_to_values(scad_values, cad_copy)
    assert any("MCC_FLOOR_T" in p and "missing" in p for p in problems)
    assert any("MCC_INVENTED" in p for p in problems)


def test_a_changed_table_value_is_reported(scad_values, cad_copy):
    path = cad_copy / "data" / "panel_parts.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["rows"]["NAHDMI-W-B"]["depth"] = 41.0
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert any("panel_parts" in p and "depth" in p for p in tools.compare_cad_to_values(scad_values, cad_copy))


def test_a_changed_port_position_or_confidence_is_reported(scad_values, cad_copy):
    path = cad_copy / "devices" / "pro-convert-hdmi-tx.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["ports"][0]["pos"] = [-17, 0]
    doc["ports"][1]["confidence"] = "measured"
    path.write_text(json.dumps(doc), encoding="utf-8")
    problems = tools.compare_cad_to_values(scad_values, cad_copy)
    assert any("pro-convert-hdmi-tx" in p and "pos" in p for p in problems)
    assert any("pro-convert-hdmi-tx" in p and "confidence" in p for p in problems)


def test_a_changed_case_option_is_reported(scad_values, cad_copy):
    path = cad_copy / "cases" / "pro-convert-hdmi-plus.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["options"]["fan_switch"] = False
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert any("pro-convert-hdmi-plus" in p and "fan_switch" in p for p in tools.compare_cad_to_values(scad_values, cad_copy))


def test_a_configuration_that_exists_only_in_cad_is_validated_by_the_policy_table(scad_values, cad_copy):
    """`bare` (P2-81 B6) has no OpenSCAD part; its options are checked against EXTRA_CONFIGURATIONS, and an unknown one is reported."""
    assert tools.EXTRA_CONFIGURATIONS == {"pro-convert-for-ndi-to-hdmi": {"bare": {"rail": False, "lid_vents": False}}}
    path = cad_copy / "cases" / "pro-convert-for-ndi-to-hdmi.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["test_configurations"]["bare"] == {"rail": False, "lid_vents": False} and "bare" not in doc["configurations"]
    doc["test_configurations"]["bare"]["rail"] = True
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert any("bare" in p and "rail" in p for p in tools.compare_cad_to_values(scad_values, cad_copy))
    doc["test_configurations"]["bare"] = {"rail": False, "lid_vents": False}
    doc["test_configurations"]["extra"] = {"fan": True}
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert any("test_configurations" in p and "extra" in p for p in tools.compare_cad_to_values(scad_values, cad_copy))
    # export status is data (A2): `bare` moved under `configurations` would claim an OpenSCAD part that does not exist
    doc["test_configurations"] = {}
    doc["configurations"]["bare"] = {"rail": False, "lid_vents": False}
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert any("configurations" in p and "bare" in p for p in tools.compare_cad_to_values(scad_values, cad_copy))


@pytest.mark.openscad
def test_the_manual_pass_report_lists_the_defaulted_rows(openscad_exe):
    sc = tools.scrape()
    text = tools.manual_pass_report(sc, tools.build(sc))
    for heading in ("src defaulted", "conf defaulted", "conf decided", "decided candidates", "no geometry, model or test references",
                    "only by a coupon or a test"):
        assert heading in text
    assert "- MCC_INSERT_BORE_EXTRA" in text and "- MCC_SIDE_BOLT_HEAD_REC_D" in text
    assert "- MCC_SLOTS_MAX: 'fixed user decision'" in text


# ---- value pins (A7 of the gate of #76): they pin values, so they belong to the transition and go with #86 ----------
# Before #86 a correction from the manual pass goes into the override tables of cad/tools/scad_meta.py, never into
# the CSV (the CSV is regenerated by `python -m cad.tools.scad_export write`).


@pytest.fixture(scope="module")
def rows():
    return P.read_registry()


def test_hand_checked_anchor_values():
    c = P.constants()
    assert c["MCC_WALL"] == 3.0 and c["MCC_SLOTS_MAX"] == 4
    assert c["MCC_GAP_FAR"] == 16.0 and c["MCC_SIDE_BOLT_PROUD"] == 0.0     # tests/test_constants.scad:54-58
    assert c["MCC_T_PATCH"] == 8.0 and c["MCC_PLATE_H"] == 39.0 and c["MCC_PANEL_BAND"] == 3.0
    assert c["MCC_RAIL_MOUTH_W"] == pytest.approx(60.3812, abs=1e-4)
    assert c["MCC_LID_FASTENER_CLR_MIN"] == pytest.approx(6.14, abs=1e-12)
    assert c["MCC_RAIL_FLANK_ANGLE"] == 60.0 and c["MCC_RAIL_LOCK_RAMP_IN"] == 45.0
    assert c["MCC_D_FLANGE_X"] == 26 and c["MCC_D_FLANGE_Y"] == 31
    assert c["MCC_VENT_EXHAUST_Z_LO"] == 32 and c["MCC_VENT_EXHAUST_Z_HI"] == 44


HARVESTED = {   # name: (value, unit, src) -- every literal that sat outside constants.scad and is now a row
    "MCC_PATCH_RECESS_ROOF_K": (1.2, "none", "lib/mcc/shell.scad:164"),
    "MCC_LID_N_FAST_LARGE": (6.0, "none", "lib/mcc/layout.scad:337"),
    "MCC_LID_N_FAST_SMALL": (4.0, "none", "lib/mcc/layout.scad:337"),
    "MCC_VENT_INTAKE_Z0": (5.0, "mm", "lib/mcc/layout.scad:390"),
    "MCC_VENT_MID_EXCL_MARGIN": (2.0, "mm", "lib/mcc/vents.scad:103"),
    "MCC_CRADLE_FLANK_RIB_CLR": (2.0, "mm", "lib/mcc/cradle.scad:133"),
    "MCC_CRADLE_FLANK_RIB_END_MARGIN": (8.0, "mm", "lib/mcc/cradle.scad:134"),
    "MCC_CRADLE_FLANK_RIB_MID_SPAN": (40.0, "mm", "lib/mcc/cradle.scad:143"),
    "MCC_CRADLE_PATCH_RIB_EDGE": (3.0, "mm", "lib/mcc/cradle.scad:247"),
    "MCC_WEB_FACE_MARGIN": (0.5, "mm", "lib/mcc/shell.scad:84"),
    "MCC_WEB_HULL_INSET": (0.2, "mm", "lib/mcc/shell.scad:94"),
    "MCC_INSERT_BORE_OVERDEPTH": (1.0, "mm", "lib/mcc/fasteners.scad:33"),
    "MCC_CRADLE_RIB_LEG": (3.0, "mm", "lib/mcc/cradle.scad:268"),
    "MCC_FAN_GRILLE_RING_W": (1.8, "mm", "lib/mcc/fan.scad:66"),
    "MCC_FAN_GRILLE_GAP_W": (3.0, "mm", "lib/mcc/fan.scad:67"),
    "MCC_FAN_GRILLE_SPOKE_W": (2.0, "mm", "lib/mcc/fan.scad:72"),
    "MCC_FAN_GRILLE_SPOKE_PITCH": (60.0, "deg", "lib/mcc/fan.scad:73"),
    "MCC_FAN_OPENING_MARGIN": (2.0, "mm", "lib/mcc/fan.scad:151"),
    "MCC_D_SEAT_POCKET_CLR": (1.0, "mm", "lib/mcc/neutrik.scad:90"),
}


def test_harvested_literals_exist_with_the_architects_provenance(rows):
    by = {r.name: r for r in rows}
    consts = P.constants()
    assert len(HARVESTED) == 19
    for name, (value, unit, src) in HARVESTED.items():
        assert consts[name] == value and by[name].src == src and by[name].conf == "assumed" and by[name].unit == unit, name
        assert by[name].is_literal
