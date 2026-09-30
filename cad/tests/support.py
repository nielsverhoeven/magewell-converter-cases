"""Helpers shared by the solver tests."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

TOL = 1e-9  # mm: the parity tolerance of issue #77 (integers, counts, labels and list order are exact)


def same(actual, expected, path="value"):
    """Numbers within TOL, bools/strings/None exact, sequences of equal length and order, dicts of equal keys."""
    if isinstance(expected, dict):
        assert set(actual) == set(expected), f"{path}: keys {sorted(actual)} != {sorted(expected)}"
        for k in expected:
            same(actual[k], expected[k], f"{path}.{k}")
    elif isinstance(expected, (list, tuple)):
        assert isinstance(actual, (list, tuple)) and len(actual) == len(expected), f"{path}: length {len(actual)} != {len(expected)}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            same(a, e, f"{path}[{i}]")
    elif isinstance(expected, (bool, str)) or expected is None:
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"
    else:
        assert abs(float(actual) - float(expected)) <= TOL, f"{path}: {actual!r} != {expected!r}"


@lru_cache(maxsize=None)
def layout_fixture() -> dict:
    return json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "scad_layout.json").read_text(encoding="utf-8"))
