"""The Neutrik D-series cutters (issue #81, plan 3.10, verdict A4; owner ``Patch``).  Called by ``shared/panel.py`` only.

Oracle: ``lib/mcc/neutrik.scad``: ``mcc_neutrik_d_wall_cut`` (a connector mounted straight into a wall: perfectly round seat
hole and body window, D40; two plain tap-drill fixing bores at their nominal diameter, D41) and ``mcc_neutrik_d_cutout`` (the
flat panel with its rear seat pocket).  The oracle's facets, ``circum`` factors and ``MCC_EPS`` overshoot do not migrate (rule 9
of 3.2): a circle is a circle and a cut reaches exactly its faces.

Frame.  ``axis`` is the normal of the wall; ``(a, b)`` is the connector centre in the plane normal to it, in the facade's
``(u, v)`` order (``(y, z)`` for X, ``(x, z)`` for Y, ``(x, y)`` for Z); ``face`` is the coordinate of the flange-seat face along
``axis``.  ``wall_side`` says on which side of ``face`` the material lies: ``"lower"`` (the case's patch wall: the connector's
outside is toward plus ``axis``) or ``"upper"`` (a coupon whose wall stands on the plus side of the seat face).

The screw positions are one table, ``SCREWS``, in the ``(u, v)`` plane, ``SX`` and ``SY`` being half the pitches
``MCC_D_SCREW_PITCH_X`` and ``_Y`` (knowledge/neutrik/d-series-cutout.md:47):

==========  =========  ==============================  ===========================================================
``mirror``  ``turn``   the two screws, relative to (a, b)  where it is used
==========  =========  ==============================  ===========================================================
False       False      (-SX, +SY) and (+SX, -SY)       the oracle's flat panel, ``mirror=false`` (front view)
True        False      (+SX, +SY) and (-SX, -SY)       the case's patch wall, seen from outside (``shell.scad:192-197``)
False       True       (+SY, -SX) and (-SY, +SX)       the depth-mockup jig (``P4-83`` 3.5 row 2: ``(y, z)``, ``wall_side="upper"``)
True        True       (+SY, +SX) and (-SY, -SX)       the same jig, mirrored
==========  =========  ==============================  ===========================================================

``turn`` is the quarter turn of the connector about the hole axis: the pitches swap (the first of the pair is the offset along
``u``) and so do the two sides of the flat panel's seat pocket.  ``mirror`` flips the sign of the offset along the connector's own
X, which is ``u`` for ``turn=False`` and ``v`` for ``turn=True``.
"""
from __future__ import annotations

from ..core import expr
from ..core.facade import AXES
from . import shared

WALL_SIDES = ("lower", "upper")
PLACEMENT = ("axis", "a", "b", "face", "wall_side", "mirror", "turn")
# The wall cut also places its own connector class: the seat and window diameters are per-slot call data (the plate cut has neither).
WALL_PLACEMENT = PLACEMENT + ("seat_d", "win_d")

# (mirror, turn) -> the two screws as ((sign of u offset, pitch of u offset), (sign of v offset, pitch of v offset)).
# "X" is MCC_D_SCREW_PITCH_X / 2, "Y" is MCC_D_SCREW_PITCH_Y / 2.
SCREWS = {
    (False, False): (((-1, "X"), (+1, "Y")), ((+1, "X"), (-1, "Y"))),
    (True, False): (((+1, "X"), (+1, "Y")), ((-1, "X"), (-1, "Y"))),
    (False, True): (((+1, "Y"), (-1, "X")), ((-1, "Y"), (+1, "X"))),
    (True, True): (((+1, "Y"), (+1, "X")), ((-1, "Y"), (-1, "X"))),
}
_PITCH = {"X": "MCC_D_SCREW_PITCH_X", "Y": "MCC_D_SCREW_PITCH_Y"}


def _check_options(axis, wall_side, mirror, turn) -> None:
    if axis not in AXES:
        raise ValueError(f"axis is one of {AXES}, got {axis!r}")
    if wall_side not in WALL_SIDES:
        raise ValueError(f"wall_side is one of {WALL_SIDES}, got {wall_side!r}")
    for name, value in (("mirror", mirror), ("turn", turn)):
        if not isinstance(value, bool):
            raise TypeError(f"{name} is True or False, got {value!r}")


def _offset(centre, sign, pitch) -> str:
    return expr.add(centre, expr.half(_PITCH[pitch])) if sign > 0 else expr.sub(centre, expr.half(_PITCH[pitch]))


def screw_centres(a, b, mirror, turn) -> list:
    """The two screw centres as ``(u, v)`` expression pairs, by the table ``SCREWS``."""
    return [(_offset(a, su, pu), _offset(b, sv, pv)) for (su, pu), (sv, pv) in SCREWS[(bool(mirror), bool(turn))]]


def _layer(face, near, far, wall_side):
    """``(start, end)`` along the axis of the layer of material from ``near`` to ``far`` away from the seat face (``near`` is
    ``None`` for the face itself), on the side of the face where the wall lies."""
    if wall_side == "lower":
        return expr.sub(face, far), expr.sub(face, near)
    return expr.add(face, near), expr.add(face, far)


def _cut(comp, set_name, what, axis, loops, face, near, far, wall_side):
    start, end = _layer(face, near, far, wall_side)
    return comp.extrude(f"Patch_{set_name}_{what}Cut", axis=axis, loops=loops, start=start, end=end, op="cut")


@shared("neutrik.d_wall_cut", placement=WALL_PLACEMENT)
def d_wall_cut(comp, set_name, *, axis, a, b, face, wall_side, seat_t, wall_t, seat_d, win_d, mirror, turn):
    """What a D connector needs from a wall it is mounted in directly (cuts along ``axis``): the seat hole ``seat_d`` through
    the first ``seat_t`` of the wall from the seat face, the body window ``win_d`` through the rest of the wall (``wall_t``
    in all), and two plain bores ``MCC_FIXING_BORE_D`` straight through the whole wall."""
    _check_options(axis, wall_side, mirror, turn)

    def cut(what, loops, near, far):
        return _cut(comp, set_name, what, axis, loops, face, near, far, wall_side)

    bores = [comp.circle(cu, cv, "MCC_FIXING_BORE_D") for cu, cv in screw_centres(a, b, mirror, turn)]
    return [cut("Seat", [comp.circle(a, b, seat_d)], None, seat_t),
            cut("Window", [comp.circle(a, b, win_d)], seat_t, wall_t),
            cut("Bore", bores, None, wall_t)]


@shared("neutrik.d_plate_cut", placement=PLACEMENT)
def d_plate_cut(comp, set_name, *, axis, a, b, face, wall_side, panel_t, seat_t, hole_d, mirror, turn):
    """A D connector's cutout in a flat panel ``panel_t`` thick (cuts along ``axis``): the round hole ``hole_d`` and the two
    ``MCC_M3_CLR_D`` screw holes through the panel, and the rear seat pocket that leaves exactly ``seat_t`` of material at the
    seat face.  The pocket is the flange footprint plus ``MCC_D_SEAT_POCKET_CLR`` with the flange's corner radius, from the rear
    face to ``seat_t`` short of the seat face; it needs ``panel_t`` above ``seat_t`` (the oracle skips it otherwise).  The
    kit draws no arcs (rule 8 of 3.2), so the rounded rectangle is two crossing rectangles (``PocketA``, ``PocketB``) and the four
    corner circles (``PocketR``), three cuts into the same hollow."""
    _check_options(axis, wall_side, mirror, turn)

    def cut(what, loops, near, far):
        return _cut(comp, set_name, what, axis, loops, face, near, far, wall_side)

    # half sides of the pocket along u and v; a turned connector swaps the two flange sides
    side_u, side_v = ("MCC_D_FLANGE_Y", "MCC_D_FLANGE_X") if turn else ("MCC_D_FLANGE_X", "MCC_D_FLANGE_Y")
    hu = expr.half(expr.add(side_u, "MCC_D_SEAT_POCKET_CLR"))
    hv = expr.half(expr.add(side_v, "MCC_D_SEAT_POCKET_CLR"))
    ru, rv = expr.sub(hu, "MCC_D_FLANGE_R"), expr.sub(hv, "MCC_D_FLANGE_R")  # where the corner circles sit
    corners = [comp.circle(along_u(a, ru), along_v(b, rv), expr.twice("MCC_D_FLANGE_R"))
               for along_u in (expr.add, expr.sub) for along_v in (expr.add, expr.sub)]
    screws = [comp.circle(cu, cv, "MCC_M3_CLR_D") for cu, cv in screw_centres(a, b, mirror, turn)]
    return [cut("Hole", [comp.circle(a, b, hole_d)], None, panel_t),
            cut("Screw", screws, None, panel_t),
            cut("PocketA", [comp.rect(expr.sub(a, hu), expr.add(a, hu), expr.sub(b, rv), expr.add(b, rv))], seat_t, panel_t),
            cut("PocketB", [comp.rect(expr.sub(a, ru), expr.add(a, ru), expr.sub(b, hv), expr.add(b, hv))], seat_t, panel_t),
            cut("PocketR", corners, seat_t, panel_t)]
