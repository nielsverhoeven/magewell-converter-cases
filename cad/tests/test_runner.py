"""The one OpenSCAD runner (cad/tools/openscad_runner.py): executable lookup, echo runs, file exports.

Transition tests: they need the tool and end with it (issue #86).  The live ones need OpenSCAD; with
MCC_REQUIRE_OPENSCAD=1 (CI) a missing OpenSCAD fails them instead of skipping.
"""
from __future__ import annotations

import pytest

osr = pytest.importorskip("cad.tools.openscad_runner", reason="cad/tools removed after the cutover (#86)")


def test_the_executable_lookup_honours_mcc_openscad(monkeypatch, tmp_path):
    monkeypatch.setenv("MCC_OPENSCAD", str(tmp_path / "does-not-exist"))
    assert osr.find_openscad() is None
    fake = tmp_path / "openscad-fake"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("MCC_OPENSCAD", str(fake))
    assert osr.find_openscad() == fake


@pytest.mark.openscad
def test_run_export_writes_the_requested_format_and_reports_echo(openscad_exe, tmp_path):
    text = 'include <mcc/constants.scad>\necho("probe", MCC_WALL);\ncube([MCC_WALL, 2, 2]);\n'
    stl = tmp_path / "out" / "part.stl"
    res = osr.run_export(text, stl, exe=openscad_exe)
    assert res.ok and stl.is_file() and stl.stat().st_size > 100
    assert res.echo_lines and res.echo_lines[0].startswith('ECHO: "probe"')
    svg = tmp_path / "flat.svg"
    assert osr.run_export("square([3, 4]);\n", svg, exe=openscad_exe).ok and "<svg" in svg.read_text(encoding="utf-8")
    contours = osr.export_2d("square([3, 4]);\n", exe=openscad_exe)
    xs = sorted({x for c in contours for x, _ in c})
    assert len(contours) == 1 and xs == [0.0, 3.0]


@pytest.mark.openscad
def test_run_export_reports_an_assertion_failure_and_passes_defines(openscad_exe, tmp_path):
    res = osr.run_export('assert(false, "mcc: T1-99 probe");\ncube(1);\n', tmp_path / "x.stl", exe=openscad_exe)
    assert not res.ok and osr.assertion_code(res.errors[0]) == "T1-99"
    res = osr.run_export("cube(size);\n", tmp_path / "y.stl", {"size": "3"}, exe=openscad_exe)
    assert res.ok and (tmp_path / "y.stl").is_file()
