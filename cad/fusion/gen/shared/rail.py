"""Mount-rail builders (issue #81, plan 3.10, verdicts A5, A6 and D81.11; owner ``Rail``; oracle ``lib/mcc/rail.scad``).

The only code that creates rail geometry: every ``Rail_*`` object of a document comes from one of the three calls (CK11).  The
slide axis is X; the male's top lock is two strips, the female's is one full-width roof slot with its backing (D63.1); the groove
is open at ``x_open`` and closed at the other end (D64.1); the lead-in is 1 x 45 degrees on flanks and roof (the loft below
replaces the oracle's ``hull()`` of two thin slices: both sections are trapezoids with parallel corresponding edges, so the hull
is the ruled solid between them).  ``lock_e`` is ``None`` for every product (the builder then uses ``MCC_RAIL_LOCK_ENGAGE``); only
the rail-lock coupon's e-ladder passes an expression (A5).  A ``None`` placement argument stands for zero.

Abbreviations in the docstrings: ``K`` is ``(MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH)`` (the flank's outward
run per unit of height); ``HM`` is ``MCC_RAIL_MOUTH_W / 2 + MCC_RAIL_CLR_HORIZ`` and ``HR`` is ``MCC_RAIL_ROOT_W / 2 +
MCC_RAIL_CLR_HORIZ`` (the groove's half widths at the mouth and the roof); ``XE`` is ``x_mid + length / 2 -
MCC_RAIL_LOCK_END_OFFSET`` (the strips' exit face); ``SH`` is ``lock_e + MCC_RAIL_ROOF_CLR`` (the slot's height above the roof).

Differences from the oracle (none moves a corner): the strips start on the male's top face, not 0.2 mm inside it (a join shares
a face, D81.5); the groove, the slot and the lead-in start at the mouth plane, with no ``MCC_EPS`` slab below it.
"""
from __future__ import annotations

from ..core import expr
from . import shared

_K = "(MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH)"
_HM = "MCC_RAIL_MOUTH_W / 2 + MCC_RAIL_CLR_HORIZ"
_HR = "MCC_RAIL_ROOT_W / 2 + MCC_RAIL_CLR_HORIZ"


def _engage(lock_e):
    return "MCC_RAIL_LOCK_ENGAGE" if lock_e is None else lock_e


def _x(x_mid, rel, flip=False):
    """``x_mid + rel``, or ``x_mid - rel`` for a mirrored rail."""
    return expr.sub(x_mid, rel) if flip else expr.add(x_mid, rel)


def _trapezoid(y_mid, z0, half_low, half_high, h):
    """The four (y, z) corners of a symmetric trapezoid about ``y_mid``: ``half_low`` at ``z0``, ``half_high`` at ``z0 + h``."""
    z_high = expr.add(z0, h)
    return [(expr.sub(y_mid, half_low), z0), (expr.add(y_mid, half_low), z0),
            (expr.add(y_mid, half_high), z_high), (expr.sub(y_mid, half_high), z_high)]


@shared("rail.male", placement=("x_mid", "y_mid", "z0", "flip"))
def male(comp, set_name, *, x_mid, y_mid, z0, length, flip, lock_e=None):
    """The male rail on a bracket plate whose top face is at ``z0``: ``Rail_<set>_TaperAdd`` (a join, axis X), the dovetail taper
    ``MCC_RAIL_MOUTH_W`` wide at ``z0`` and ``MCC_RAIL_MALE_H`` tall with the groove's flank slope (the polygon
    ``(y_mid -+ MCC_RAIL_MOUTH_W / 2, z0)``, ``(y_mid -+ (MCC_RAIL_MOUTH_W / 2 + MCC_RAIL_MALE_H * K), z0 + MCC_RAIL_MALE_H)``)
    from ``x_mid - length / 2`` to ``x_mid + length / 2``; then ``Rail_<set>_StripAAdd`` and ``StripBAdd`` (joins, axis Y), the two
    lock strips on its top face at ``|y - y_mid|`` from ``MCC_RAIL_LOCK_STRIP_Y_IN`` to ``MCC_RAIL_LOCK_STRIP_Y_OUT``: in (x, z)
    a square exit face at ``XE``, a vertical entry side up to the roof line ``z0 + MCC_RAIL_DEPTH``, the entry chamfer
    ``MCC_RAIL_LOCK_RAMP_IN`` over ``lock_e`` and a flat top at ``z0 + MCC_RAIL_DEPTH + lock_e``.  ``flip`` mirrors the strips'
    x about ``x_mid`` (a bracket that turns the rail round).  ``lock_e`` is ``None`` (``MCC_RAIL_LOCK_ENGAGE``) except in the
    rail-lock coupon."""
    e = _engage(lock_e)
    half = expr.half(length)
    top = expr.add(z0, "MCC_RAIL_MALE_H")
    run = expr.add(expr.half("MCC_RAIL_MOUTH_W"), expr.mul("MCC_RAIL_MALE_H", _K))
    taper = comp.extrude(f"Rail_{set_name}_TaperAdd", axis="X",
                         loops=[comp.polygon(_trapezoid(y_mid, z0, expr.half("MCC_RAIL_MOUTH_W"), run, "MCC_RAIL_MALE_H"))],
                         start=expr.sub(x_mid, half), end=expr.add(x_mid, half), op="join")
    exit_rel = expr.sub(half, "MCC_RAIL_LOCK_END_OFFSET")
    entry_rel = expr.sub(exit_rel, "MCC_RAIL_LOCK_STRIP_X")
    roof = expr.add(z0, "MCC_RAIL_DEPTH")
    crest = expr.add(roof, e)
    section = [(_x(x_mid, entry_rel, flip), top),
               (_x(x_mid, entry_rel, flip), roof),
               (_x(x_mid, expr.add(entry_rel, expr.div(e, "tan(MCC_RAIL_LOCK_RAMP_IN)")), flip), crest),
               (_x(x_mid, exit_rel, flip), crest),
               (_x(x_mid, exit_rel, flip), top)]
    strip_a = comp.extrude(f"Rail_{set_name}_StripAAdd", axis="Y", loops=[comp.polygon(section)],
                           start=expr.add(y_mid, "MCC_RAIL_LOCK_STRIP_Y_IN"), end=expr.add(y_mid, "MCC_RAIL_LOCK_STRIP_Y_OUT"),
                           op="join")
    strip_b = comp.extrude(f"Rail_{set_name}_StripBAdd", axis="Y", loops=[comp.polygon(section)],
                           start=expr.sub(y_mid, "MCC_RAIL_LOCK_STRIP_Y_OUT"), end=expr.sub(y_mid, "MCC_RAIL_LOCK_STRIP_Y_IN"),
                           op="join")
    return [taper, strip_a, strip_b]


@shared("rail.female_backing", placement=("x_mid", "y_mid", "z_sill"))
def female_backing(comp, set_name, *, x_mid, y_mid, z_sill, length, lock_e=None):
    """The material over the lock's roof slot (T1-38): ``Rail_<set>_BackingAdd``, a join, axis Z.  A box from the sill top
    ``z_sill`` up to ``z_sill + SH``, in x from ``XE - MCC_RAIL_LOCK_STRIP_X - MCC_RAIL_MATE_CLR - MCC_WALL`` to
    ``XE + MCC_RAIL_MATE_CLR + MCC_WALL``, in y ``y_mid`` plus and minus ``MCC_RAIL_ROOT_W / 2 + MCC_RAIL_SILL_SIDE_W``.  The
    slot is cut in the same placement by ``female_cut`` (the same ``length`` and ``lock_e``)."""
    exit_x = expr.sub(expr.add(x_mid, expr.half(length)), "MCC_RAIL_LOCK_END_OFFSET")
    x0 = expr.sub(expr.sub(expr.sub(exit_x, "MCC_RAIL_LOCK_STRIP_X"), "MCC_RAIL_MATE_CLR"), "MCC_WALL")
    x1 = expr.add(exit_x, "MCC_RAIL_MATE_CLR", "MCC_WALL")
    reach = expr.add(expr.half("MCC_RAIL_ROOT_W"), "MCC_RAIL_SILL_SIDE_W")
    box = comp.rect(x0, x1, expr.sub(y_mid, reach), expr.add(y_mid, reach))
    return [comp.extrude(f"Rail_{set_name}_BackingAdd", axis="Z", loops=[box], start=z_sill,
                         end=expr.add(z_sill, _engage(lock_e), "MCC_RAIL_ROOF_CLR"), op="join")]


@shared("rail.female_cut", placement=("x_mid", "y_mid", "z0", "x_open"))
def female_cut(comp, set_name, *, x_mid, y_mid, z0, length, x_open, lead_in=True, lock_e=None):
    """The groove, its roof slot and its lead-in, in the case floor whose exterior face is at ``z0`` (the mouth plane).
    ``Rail_<set>_GrooveCut`` (a cut, axis X): the polygon ``(y_mid -+ HM, z0)``, ``(y_mid -+ HR, z0 + MCC_RAIL_DEPTH)`` from the
    closed end ``x_mid - length / 2`` to ``x_open``.  ``Rail_<set>_LockSlotCut`` (a cut, axis Z): one box across the roof's
    full width, ``y_mid`` plus and minus ``HR``, in x from ``XE - MCC_RAIL_LOCK_STRIP_X - MCC_RAIL_MATE_CLR`` to ``XE +
    MCC_RAIL_MATE_CLR``, from the roof ``z0 + MCC_RAIL_DEPTH`` up by ``SH``.  With ``lead_in``, ``Rail_<set>_LeadInCut``, a loft cut
    along X from the groove polygon at ``x_open - MCC_RAIL_LEADIN`` to the polygon flared by ``MCC_RAIL_LEADIN`` on flanks, mouth
    and roof at ``x_open`` (it is 1 x 45 degrees)."""
    roof = expr.add(z0, "MCC_RAIL_DEPTH")
    start = expr.sub(x_mid, expr.half(length))
    groove = comp.extrude(f"Rail_{set_name}_GrooveCut", axis="X",
                          loops=[comp.polygon(_trapezoid(y_mid, z0, _HM, _HR, "MCC_RAIL_DEPTH"))],
                          start=start, end=x_open, op="cut")
    exit_x = expr.sub(expr.add(x_mid, expr.half(length)), "MCC_RAIL_LOCK_END_OFFSET")
    slot = comp.rect(expr.sub(expr.sub(exit_x, "MCC_RAIL_LOCK_STRIP_X"), "MCC_RAIL_MATE_CLR"),
                     expr.add(exit_x, "MCC_RAIL_MATE_CLR"), expr.sub(y_mid, _HR), expr.add(y_mid, _HR))
    names = [groove, comp.extrude(f"Rail_{set_name}_LockSlotCut", axis="Z", loops=[slot], start=roof,
                                  end=expr.add(roof, _engage(lock_e), "MCC_RAIL_ROOF_CLR"), op="cut")]
    if lead_in:
        flare = expr.add(_HM, "MCC_RAIL_LEADIN")
        flare_top = expr.add(flare, expr.mul(expr.add("MCC_RAIL_DEPTH", "MCC_RAIL_LEADIN"), _K))
        outer = _trapezoid(y_mid, z0, flare, flare_top, expr.add("MCC_RAIL_DEPTH", "MCC_RAIL_LEADIN"))
        names.append(comp.loft(f"Rail_{set_name}_LeadInCut", axis="X",
                               loop_a=comp.polygon(_trapezoid(y_mid, z0, _HM, _HR, "MCC_RAIL_DEPTH")),
                               at_a=expr.sub(x_open, "MCC_RAIL_LEADIN"), loop_b=comp.polygon(outer), at_b=x_open, op="cut"))
    return names
