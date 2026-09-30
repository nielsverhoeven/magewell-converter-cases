"""Shared setup of the tests of the scripts/ modules.

Puts <repo>/scripts and <repo> on sys.path, so a test imports a script module (`import parity`,
`import build`) and the `cad` package without touching sys.path itself. This directory has no
__init__.py: pytest's rootdir-relative module names stay unique against cad/tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"

for _path in (SCRIPTS_DIR, REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
