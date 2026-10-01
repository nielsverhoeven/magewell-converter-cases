"""Tongue-and-groove builders (issue #81, plan 3.10; oracle ``_mcc_tg_frame``, ``lib/mcc/shell.scad:129-137``).

Both builders take the same rectangle ``x0, x1, y0, y1``, so a tongue and its groove cannot drift apart when the caller
passes the same four expressions.  No fixed owner: the caller passes the full feature name.
"""
from __future__ import annotations

from ..core import expr
from . import shared


@shared("tg.tongue", placement=("x0", "x1", "y0", "y1", "z"))
def tongue(comp, name, *, x0, x1, y0, y1, z, width, height):
    """The tongue: a ring around the rectangle, ``width`` wide, from ``z`` to ``z + height`` (a join, axis Z)."""
    outer = comp.rect(expr.sub(x0, width), expr.add(x1, width), expr.sub(y0, width), expr.add(y1, width))
    hole = comp.rect(x0, x1, y0, y1)
    return comp.extrude(name, axis="Z", loops=[outer], holes=[hole], start=z, end=expr.add(z, height), op="join")


@shared("tg.groove", placement=("x0", "x1", "y0", "y1", "z"))
def groove(comp, name, *, x0, x1, y0, y1, z, width, height, clearance):
    """The groove: the tongue ring grown by ``clearance`` on both sides, from ``z`` to ``z + height`` (a cut, axis Z)."""
    grow = expr.add(width, clearance)
    outer = comp.rect(expr.sub(x0, grow), expr.add(x1, grow), expr.sub(y0, grow), expr.add(y1, grow))
    hole = comp.rect(expr.add(x0, clearance), expr.sub(x1, clearance), expr.add(y0, clearance), expr.sub(y1, clearance))
    return comp.extrude(name, axis="Z", loops=[outer], holes=[hole], start=z, end=expr.add(z, height), op="cut")
