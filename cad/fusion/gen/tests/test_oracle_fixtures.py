"""K4a: the oracle harness and its committed fixtures (issue #81).

The offline tests need nothing but the committed files.  The tests that use the ``fresh`` fixture render the frozen oracle
(``lib/mcc``) with the one OpenSCAD runner of #76 and compare the result with the committed fixtures to 0.001 mm3
and 0.001 mm2.  Where OpenSCAD is missing, ``oracle.require_openscad()`` fails them when ``MCC_REQUIRE_OPENSCAD=1``
(CI) and skips them otherwise; they never pass silently.

Re-derive the fixtures with::

    python -m cad.fusion.gen.tests.oracle s1 --all --update-fixtures
    python -m cad.fusion.gen.tests.oracle s2 --all --update-fixtures
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import pytest

from cad.fusion.gen.tests import oracle

REPO = Path(__file__).resolve().parents[4]
GOLDEN = REPO / "tests" / "golden"


def _s1() -> dict:
    return oracle.load_fixture(oracle.S1_FIXTURE)["blocks"]


def _s2() -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"]


def _golden(name: str) -> dict:
    raw = json.loads((GOLDEN / f"{name}.json").read_text(encoding="utf-8"))
    return {"volume_mm3": raw["volume_mm3"], "area_mm2": raw["area_mm2"],
            "bbox_min": raw["bbox"]["min"], "bbox_max": raw["bbox"]["max"]}


# --------------------------------------------------------------------------------------------------------------
# Offline: the committed files and the harness text
# --------------------------------------------------------------------------------------------------------------

def test_fixture_keys_are_the_planned_set() -> None:
    assert list(_s1()) == list(oracle.S1_BLOCKS)
    assert list(_s2()) == list(oracle.s2_cases())
    assert len(_s2()) == 16
    for entry in _s2().values():
        assert set(entry) == {"slug", "part", "stage", "options", "volume_mm3", "area_mm2", "bbox_min", "bbox_max"}


def test_the_template_has_stages_b1_to_b8_and_b10_and_lid_stages() -> None:
    names = [v["stage"] for k, v in _s2().items() if v["slug"] == oracle.TEMPLATE and ".bare" not in k]
    assert names == ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B10", "L1", "L2", "L3", "L4"]
    assert _s2()["pro-convert-hdmi-plus.base.B10.fan_switch"]["options"] == {
        "fan": True, "fan_switch": True, "rail": True, "lid_vents": True}
    for key in ("pro-convert-for-ndi-to-hdmi.base.B8.bare", "pro-convert-for-ndi-to-hdmi.lid.L4.bare"):
        assert _s2()[key]["options"] == {"fan": False, "fan_switch": False, "rail": False, "lid_vents": False}


def test_stages_are_cumulative_in_the_fixture() -> None:
    """Box heights and the lid's z range of the template, as the plan states them (5.2)."""
    s2 = _s2()
    base = "pro-convert-for-ndi-to-hdmi.base."
    assert s2[base + "B1"]["bbox_max"][2] == 48.0
    for stage in ("B2", "B3", "B4", "B5", "B6", "B7", "B8", "B10"):
        assert s2[base + stage]["bbox_max"][2] == 50.0
        assert s2[base + stage]["bbox_min"] == [-96.95, -79.925, 0.0]
    lid = "pro-convert-for-ndi-to-hdmi.lid."
    for stage in ("L1", "L2", "L3", "L4"):
        assert (s2[lid + stage]["bbox_min"][2], s2[lid + stage]["bbox_max"][2]) == (48.0, 51.0)


@pytest.mark.parametrize("key,golden", sorted(oracle.S2_GOLDENS.items()))
def test_last_stage_fixture_equals_the_committed_golden(key: str, golden: str) -> None:
    """B8, B10 and L4 of the template and B10 of the Plus case are the library's own parts (harness self-test)."""
    assert oracle.differences(_s2()[key], _golden(golden), key) == []


def test_the_harness_follows_main_not_the_plan() -> None:
    """Issues #87 and #100: no floor cuts, no thumbscrew hole, no counterbore constant in either harness text."""
    for text in (oracle.HARNESS_S1, oracle.HARNESS_S2):
        assert "mcc_floor_features_cut" not in text
        assert "mcc_thumbscrew_hole" not in text
        assert "MCC_LID_CB_D" not in text
        assert "mcc_lid_screw_hole" in text
    assert "9 <= stage" not in oracle.HARNESS_S2 and "stage >= 9" not in oracle.HARNESS_S2
    assert oracle.HARNESS_S2.count("include <mcc/devices/") == len(oracle.SLUGS) == 8


def test_a_missing_stage_is_refused_before_openscad_runs(tmp_path: Path) -> None:
    with pytest.raises(oracle.OracleError, match="no B9"):
        oracle.render_s2(oracle.TEMPLATE, "base", 9, tmp_path)
    with pytest.raises(oracle.OracleError, match="unknown slug"):
        oracle.render_s2("nope", "base", 1, tmp_path)
    with pytest.raises(oracle.OracleError, match="unknown S1 block"):
        oracle.render_s1("thumbscrew_hole", tmp_path)


def test_measure_reads_volume_area_and_box(tmp_path: Path) -> None:
    import trimesh

    box = trimesh.creation.box(extents=(2.0, 3.0, 4.0))
    box.apply_translation((1.0, 1.5, 2.0))
    path = tmp_path / "box.stl"
    box.export(str(path))
    m = oracle.measure(path)
    assert m["volume_mm3"] == pytest.approx(24.0, abs=1e-4)
    assert m["area_mm2"] == pytest.approx(52.0, abs=1e-4)
    assert m["bbox_min"] == pytest.approx([0.0, 0.0, 0.0], abs=1e-5)
    assert m["bbox_max"] == pytest.approx([2.0, 3.0, 4.0], abs=1e-5)


def test_differences_uses_the_stated_tolerances() -> None:
    a = {"volume_mm3": 10.0, "area_mm2": 20.0, "bbox_min": [0, 0, 0], "bbox_max": [1, 1, 1]}
    assert oracle.differences(a, dict(a, volume_mm3=10.0009), "x") == []
    assert len(oracle.differences(a, dict(a, volume_mm3=10.002), "x")) == 1
    assert len(oracle.differences(a, dict(a, area_mm2=20.002), "x")) == 1
    assert len(oracle.differences(a, dict(a, bbox_max=[1, 1, 1.01]), "x")) == 1


def test_require_openscad_fails_when_required_and_skips_otherwise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oracle.openscad_runner, "find_openscad", lambda: None)
    monkeypatch.setenv("MCC_REQUIRE_OPENSCAD", "1")
    with pytest.raises(oracle.OracleError, match="MCC_REQUIRE_OPENSCAD"):
        oracle.require_openscad()
    monkeypatch.delenv("MCC_REQUIRE_OPENSCAD")
    with pytest.raises(unittest.SkipTest):
        oracle.require_openscad()


def test_the_cli_refuses_an_incomplete_command() -> None:
    with pytest.raises(SystemExit):
        oracle.main(["s2", oracle.TEMPLATE])


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: a fresh render equals the committed fixture
# --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fresh(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Every S1 block and every S2 case, rendered once in one pool."""
    oracle.require_openscad()
    s1, s2 = oracle.derive_all(tmp_path_factory.mktemp("oracle"))
    return {"s1": s1, "s2": s2}


@pytest.mark.parametrize("block", list(oracle.S1_BLOCKS))
def test_s1_block_equals_a_fresh_render(fresh: dict, block: str) -> None:
    assert oracle.differences(fresh["s1"][block], _s1()[block], f"S1 {block}") == []


@pytest.mark.parametrize("key", list(oracle.s2_cases()))
def test_s2_stage_equals_a_fresh_render(fresh: dict, key: str) -> None:
    assert oracle.differences(fresh["s2"][key], _s2()[key], f"S2 {key}") == []


@pytest.mark.parametrize("key,golden", sorted(oracle.S2_GOLDENS.items()))
def test_fresh_last_stage_equals_the_committed_golden(fresh: dict, key: str, golden: str) -> None:
    assert oracle.differences(fresh["s2"][key], _golden(golden), f"{key} vs tests/golden/{golden}.json") == []
