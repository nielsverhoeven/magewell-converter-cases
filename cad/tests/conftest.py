"""Shared pytest fixtures of the cad/ tests.

OpenSCAD-dependent tests (S0 while lib/mcc is the frozen oracle) use the `openscad_exe` fixture:
  * OpenSCAD found                          -> the path
  * not found, MCC_REQUIRE_OPENSCAD=1       -> the test FAILS (CI sets it: a gate must never skip silently)
  * not found, variable unset               -> the test is skipped with a reason
  * cad/tools is gone (after the cutover)   -> the test is skipped; such tests are deleted by issue #86
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR.parent / "fixtures"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "openscad: needs the frozen OpenSCAD oracle installed (S0 re-derive)")


@pytest.fixture(scope="session")
def openscad_exe() -> Path:
    try:
        from cad.tools import openscad_runner as osr
    except ImportError:
        pytest.skip("cad.tools is removed (post-cutover): oracle tests no longer apply")
    exe = osr.find_openscad()
    if exe is None:
        if os.environ.get("MCC_REQUIRE_OPENSCAD") == "1":
            pytest.fail("OpenSCAD is required (MCC_REQUIRE_OPENSCAD=1) but was not found")
        pytest.skip("OpenSCAD not found (set MCC_OPENSCAD, install the nightly, or put openscad on PATH)")
    return exe


@pytest.fixture(scope="session")
def scad_values() -> dict:
    """The committed S0 fixture: what OpenSCAD evaluated (constants, devices, case variants)."""
    return json.loads((FIXTURES_DIR / "scad_values.json").read_text(encoding="utf-8"))
