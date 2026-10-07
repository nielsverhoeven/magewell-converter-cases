"""Tests of scripts/fusion_archive.py, the PR gate for the committed Fusion snapshots (#125, D125.2)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import fusion_archive as fa


def _step(path: Path, data: str = "#1=CARTESIAN_POINT('',(0.,0.,0.));", date: str = "2026-10-07T10:00:00") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"ISO-10303-21;\nHEADER;\nFILE_NAME('x','{date}');\nENDSEC;\nDATA;\n{data}\nENDSEC;\nEND-ISO-10303-21;\n",
        encoding="utf-8", newline="\n")


BRACKETS = {"brackets": [{"design": "br", "stem": "br", "dir": "br",
                          "parts": [{"name": "arm", "step": "arm", "x": 0, "y": 0, "z": 0, "rz": 0}]}]}


@pytest.fixture
def fixture(tmp_path: Path) -> dict:
    """One case dir (base + lid), one bracket, a matching manifest and archive files."""
    exports = tmp_path / "exports"
    _step(exports / "case-a" / "base.step", "#1=A;")
    _step(exports / "case-a" / "lid.step", "#1=B;")
    _step(exports / "brackets" / "br" / "arm.step", "#1=C;")
    brackets = tmp_path / "brackets.json"
    brackets.write_text(json.dumps(BRACKETS), encoding="utf-8", newline="\n")
    archive = tmp_path / "archive" / "fusion"
    (archive / "cases").mkdir(parents=True)
    (archive / "brackets").mkdir(parents=True)
    (archive / "cases" / "case-a.f3d").write_bytes(b"f3d")
    (archive / "brackets" / "br.f3d").write_bytes(b"f3d")

    def part(step: str) -> dict:
        return {"component": step, "step": step, "fingerprint": fa.step_fingerprint(tmp_path / step)}

    manifest = {
        "failed": [], "placements_sha256": fa.placements_hash(brackets),
        "archives": [
            {"file": "cases/case-a.f3d", "parts": [part("exports/case-a/base.step"), part("exports/case-a/lid.step")]},
            {"file": "brackets/br.f3d", "parts": [part("exports/brackets/br/arm.step")]},
        ]}
    (archive / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return {"repo": tmp_path, "exports": exports, "archive": archive, "brackets": brackets, "manifest": manifest}


def _run(f: dict) -> list[str]:
    return fa.check(f["repo"], f["exports"], f["archive"], f["brackets"])


def _write_manifest(f: dict) -> None:
    (f["archive"] / "manifest.json").write_text(json.dumps(f["manifest"]), encoding="utf-8")


def test_fingerprint_ignores_header(tmp_path: Path) -> None:
    _step(tmp_path / "a.step", date="2026-01-01T00:00:00")
    _step(tmp_path / "b.step", date="2027-12-31T23:59:59")
    assert fa.step_fingerprint(tmp_path / "a.step") == fa.step_fingerprint(tmp_path / "b.step")


def test_fingerprint_changes_with_data(tmp_path: Path) -> None:
    _step(tmp_path / "a.step", "#1=A;")
    _step(tmp_path / "b.step", "#1=B;")
    assert fa.step_fingerprint(tmp_path / "a.step") != fa.step_fingerprint(tmp_path / "b.step")


def test_fingerprint_crlf_equals_lf(tmp_path: Path) -> None:
    _step(tmp_path / "lf.step")
    (tmp_path / "crlf.step").write_bytes((tmp_path / "lf.step").read_bytes().replace(b"\n", b"\r\n"))
    assert fa.step_fingerprint(tmp_path / "lf.step") == fa.step_fingerprint(tmp_path / "crlf.step")


def test_fingerprint_without_data_section_raises(tmp_path: Path) -> None:
    (tmp_path / "bad.step").write_text("ISO-10303-21;\nHEADER;\nENDSEC;\n", encoding="utf-8")
    with pytest.raises(ValueError):
        fa.step_fingerprint(tmp_path / "bad.step")


def test_consistent_fixture_has_no_problems(fixture: dict) -> None:
    assert _run(fixture) == []


def test_expected_steps(fixture: dict) -> None:
    assert fa.expected_steps(fixture["exports"], fixture["brackets"]) == {
        "exports/case-a/base.step", "exports/case-a/lid.step", "exports/brackets/br/arm.step"}


def test_changed_data_is_stale(fixture: dict) -> None:
    _step(fixture["exports"] / "case-a" / "base.step", "#1=CHANGED;")
    problems = _run(fixture)
    assert problems == ["stale: cases/case-a.f3d (exports/case-a/base.step)"]


def test_changed_header_only_is_not_stale(fixture: dict) -> None:
    _step(fixture["exports"] / "case-a" / "base.step", "#1=A;", date="2030-01-01T00:00:00")
    assert _run(fixture) == []


def test_new_base_variant_is_not_archived(fixture: dict) -> None:
    _step(fixture["exports"] / "case-a" / "base_fan.step", "#1=FAN;")
    assert _run(fixture) == ["not archived: exports/case-a/base_fan.step"]


def test_bracket_part_missing_from_brackets_json_is_not_archived(fixture: dict) -> None:
    _step(fixture["exports"] / "brackets" / "br" / "spacer.step", "#1=S;")
    assert _run(fixture) == ["not archived: exports/brackets/br/spacer.step"]


def test_deleted_archive_file_is_missing(fixture: dict) -> None:
    (fixture["archive"] / "cases" / "case-a.f3d").unlink()
    assert _run(fixture) == ["missing archive: cases/case-a.f3d"]


def test_missing_fingerprint_key_is_stale(fixture: dict) -> None:
    del fixture["manifest"]["archives"][1]["parts"][0]["fingerprint"]
    _write_manifest(fixture)
    assert _run(fixture) == ["stale: brackets/br.f3d (exports/brackets/br/arm.step)"]


def test_missing_step_is_reported(fixture: dict) -> None:
    (fixture["exports"] / "case-a" / "lid.step").unlink()
    assert "missing STEP: exports/case-a/lid.step" in _run(fixture)


def test_changed_placements_are_stale(fixture: dict) -> None:
    spec = json.loads(fixture["brackets"].read_text(encoding="utf-8"))
    spec["brackets"][0]["parts"][0]["x"] = 5
    fixture["brackets"].write_text(json.dumps(spec), encoding="utf-8", newline="\n")
    assert _run(fixture) == ["stale: brackets.json placements changed"]


def test_missing_placements_hash_is_stale(fixture: dict) -> None:
    del fixture["manifest"]["placements_sha256"]
    _write_manifest(fixture)
    assert _run(fixture) == ["stale: brackets.json placements changed"]


def test_failed_designs_are_reported(fixture: dict) -> None:
    fixture["manifest"]["failed"] = ["case-a: boom"]
    _write_manifest(fixture)
    assert _run(fixture) == ["manifest records failed designs: case-a: boom"]


def test_missing_manifest(fixture: dict) -> None:
    (fixture["archive"] / "manifest.json").unlink()
    problems = _run(fixture)
    assert len(problems) == 1 and problems[0].startswith("missing manifest")


def test_cli_exit_codes(fixture: dict, capsys: pytest.CaptureFixture) -> None:
    args = ["check", "--repo", str(fixture["repo"]), "--exports", str(fixture["exports"]),
            "--archive", str(fixture["archive"]), "--brackets", str(fixture["brackets"])]
    assert fa.main(args) == 0
    assert "up to date (2 archives, 3 STEPs)" in capsys.readouterr().out
    _step(fixture["exports"] / "case-a" / "base.step", "#1=CHANGED;")
    assert fa.main(args) == 1
    out = capsys.readouterr().out
    assert "stale:" in out and "gh run download" in out and "OCP" in out
