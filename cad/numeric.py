"""Numeric conventions shared by the expression evaluator (cad/params.py) and the layout solver
(cad/layout.py).  Pure Python, standard library only (it must also import inside Fusion's own
interpreter).

The helpers reproduce the OpenSCAD semantics the legacy solver relies on, so that a line-by-line
port stays line-by-line:

  * trigonometry takes DEGREES and is exact at the special angles OpenSCAD returns exactly
    (sin 0/30/90/150/180/210/270/330, cos 0/60/90/120/180/240/270/300, tan multiples of 45).
    Elsewhere it is math.sin(math.radians(x)), which differs from OpenSCAD in the last ulp or two
    (measured 2026-09-30 over -720..1080 deg: |sin|,|cos| error <= 1e-15, tan <= 2.7e-14 relative).  No
    comparison in this repository relies on trig bit-equality: parity tests use rel_tol 1e-9.
  * round() is sign(x) * floor(|x| + 0.5) (half away from zero, floor-based), Python's round() is
    banker's rounding and C's round() differs at 0.49999999999999994.
  * `%` is fmod (the sign of the dividend), Python's `%` follows the divisor.
  * floor()/ceil() return floats (Python's return ints; the value is the same).
  * division by zero yields inf/nan in OpenSCAD and raises in Python: the port must guard it
    explicitly where the legacy code can divide by zero (layout.scad never does).
  * search()/struct_val()/sort(list, idx=[..]) semantics are provided as small functions below.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

_SIN_EXACT = {0.0: 0.0, 30.0: 0.5, 90.0: 1.0, 150.0: 0.5, 180.0: 0.0, 210.0: -0.5, 270.0: -1.0, 330.0: -0.5}
_COS_EXACT = {0.0: 1.0, 60.0: 0.5, 90.0: 0.0, 120.0: -0.5, 180.0: -1.0, 240.0: -0.5, 270.0: 0.0, 300.0: 0.5}
_TAN_EXACT = {0.0: 0.0, 45.0: 1.0, 135.0: -1.0, 180.0: 0.0, 225.0: 1.0, 315.0: -1.0}


def _reduce360(x: float) -> float:
    if 0.0 <= x < 360.0:
        return x
    if -360.0 < x < 0.0:
        return x + 360.0
    x = math.fmod(x, 360.0)
    return x + 360.0 if x < 0 else x


def sin_deg(x: float) -> float:
    r = _reduce360(float(x))
    return _SIN_EXACT.get(r, math.sin(math.radians(r)))


def cos_deg(x: float) -> float:
    r = _reduce360(float(x))
    return _COS_EXACT.get(r, math.cos(math.radians(r)))


def tan_deg(x: float) -> float:
    r = _reduce360(float(x))
    if r in (90.0, 270.0):
        return math.inf if r == 90.0 else -math.inf
    return _TAN_EXACT.get(r, math.tan(math.radians(r)))


def round_half_away(x: float) -> float:
    """OpenSCAD round() is sign(x) * floor(|x| + 0.5): half away from zero, but NOT C's round() at the
    last bit (round(0.49999999999999994) is 1 because |x| + 0.5 rounds up to 1.0).  Exact below 2**52."""
    return math.copysign(math.floor(abs(x) + 0.5), x)


def floor_(x: float) -> float:
    return float(math.floor(x))


def ceil_(x: float) -> float:
    return float(math.ceil(x))


def fmod(a: float, b: float) -> float:
    """OpenSCAD `a % b`."""
    return math.fmod(a, b)


def max_of(values: Iterable[float]) -> float:
    """OpenSCAD max(list).  The legacy code only calls it on non-empty lists."""
    vals = list(values)
    if not vals:
        raise ValueError("max_of([]): OpenSCAD returns undef here; the port must not reach it")
    return max(vals)


def min_of(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        raise ValueError("min_of([]): OpenSCAD returns undef here; the port must not reach it")
    return min(vals)


def search_index(key: Any, table: Sequence[Sequence[Any]]) -> int | None:
    """OpenSCAD `search([key], table)[0]`: index of the FIRST row whose column 0 equals key, else None
    (OpenSCAD returns []).  `table` is a list of [key, value] rows."""
    for i, row in enumerate(table):
        if row[0] == key:
            return i
    return None


def struct_val(struct: Sequence[Sequence[Any]], key: Any, default: Any = None) -> Any:
    """BOSL2 struct_val(): value of the first [key, value] row, else `default`."""
    i = search_index(key, struct)
    return default if i is None else struct[i][1]


def sort_lex(rows: Sequence[Sequence[float]], idx: Sequence[int]) -> list[Sequence[float]]:
    """BOSL2 sort(list, idx=[...]) for a homogeneous list of numeric vectors: lexicographic on the
    given columns, ascending, STABLE (equal keys keep their input order; BOSL2's _sort_vectors
    filters `equal` in input order and stops recursing at the end of idx)."""
    return sorted(rows, key=lambda r: tuple(r[i] for i in idx))


def close(a: float, b: float, rel: float = 1e-9, abs_: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_)


def fmt_num(v: float, digits: int = 9) -> str:
    """Stable, diff-friendly decimal text for a float: rounded to `digits` decimals, trailing zeros
    stripped ('193.9', '41.966666667', '3').  Used for variant files and Fusion expressions."""
    s = f"{round(float(v), digits):.{digits}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s
