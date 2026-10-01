"""Fastener builders (issue #81, plan 3.10; owners ``Fastener`` and ``SideBolt``).

Oracle: ``lib/mcc/fasteners.scad``: the heat-set bore and boss, ``mcc_lid_screw_hole`` (the 90 degree countersink of #100, which
replaced the thumbscrew hole) and the captive side bolt's boss and cut.  ``centres`` is a list of ``(u, v)`` expression pairs
(``None`` is zero); all circles of one call are one sketch and one feature, except the countersink cones: a loft takes one
loop per section, so a lid screw hole makes one cone loft per centre.

The side-bolt web runs up to the bolt axis, not to the boss underside as the oracle's does: a join shares volume or a face with
its target, never only a line (D81.5).  The extra material is the two thin wedges between the web's flat top and the cylinder.
"""
from __future__ import annotations

from ..core import expr
from . import shared


@shared("fasteners.heat_set_boss", placement=("centres", "z0", "z1"))
def heat_set_boss(comp, set_name, *, centres, z0, z1, d):
    """A full cylinder of diameter ``d`` at every centre, from ``z0`` to ``z1`` (a join, axis Z).  Its bore is the separate
    ``insert_bore`` call in the cut phase."""
    loops = [comp.circle(cu, cv, d) for cu, cv in centres]
    return comp.extrude(f"Fastener_{set_name}_BossAdd", axis="Z", loops=loops, start=z0, end=z1, op="join")


@shared("fasteners.insert_bore", placement=("centres", "z_open"))
def insert_bore(comp, set_name, *, centres, z_open, depth, d):
    """The blind bore of a heat-set insert: diameter ``d`` from ``z_open - depth`` to ``z_open`` (a cut, axis Z)."""
    loops = [comp.circle(cu, cv, d) for cu, cv in centres]
    return comp.extrude(f"Fastener_{set_name}_BoreCut", axis="Z", loops=loops, start=expr.sub(z_open, depth), end=z_open,
                        op="cut")


@shared("fasteners.lid_screw_hole", placement=("centres", "z0", "z1"))
def lid_screw_hole(comp, set_name, *, centres, z0, z1, shaft_d, csk_d, angle):
    """A countersunk screw hole in a lid whose outward face is at ``z1``: the shaft ``shaft_d`` from ``z0`` to ``z1`` (one
    extrude cut) and, per centre, the countersink cone from ``shaft_d`` at ``z1 - depth`` to ``csk_d`` at ``z1`` (a loft cut
    between two circles, the cone frustum).  ``depth = (csk_d - shaft_d) / 2 / tan(angle / 2)``, so the cone meets the shaft
    with no step (``angle`` is the included angle of the head, ``MCC_LID_CSK_ANGLE``)."""
    depth = expr.div(expr.half(expr.sub(csk_d, shaft_d)), f"tan({expr.half(angle)})")
    z_cone = expr.sub(z1, depth)
    loops = [comp.circle(cu, cv, shaft_d) for cu, cv in centres]
    names = [comp.extrude(f"Fastener_{set_name}_ShaftCut", axis="Z", loops=loops, start=z0, end=z1, op="cut")]
    for i, (cu, cv) in enumerate(centres, 1):
        names.append(comp.loft(f"Fastener_{set_name}_Cone{i}Cut", axis="Z", loop_a=comp.circle(cu, cv, shaft_d), at_a=z_cone,
                               loop_b=comp.circle(cu, cv, csk_d), at_b=z1, op="cut"))
    return names


@shared("fasteners.side_bolt_boss", placement=("x", "z", "y_face", "web_y0", "web_z0"))
def side_bolt_boss(comp, *, x, z, y_face, length, d, web_t, web_y0, web_z0):
    """The captive side bolt's boss (axis Y): a cylinder of diameter ``d`` at ``(x, z)`` from ``y_face`` to
    ``y_face + length`` and, as a second join, the support web: a box ``web_t`` thick centred on ``x``, from ``web_y0`` to
    the end of the cylinder, from ``web_z0`` up to the bolt axis ``z`` (D81.5)."""
    y_end = expr.add(y_face, length)
    cyl = comp.extrude("SideBolt_Boss_CylAdd", axis="Y", loops=[comp.circle(x, z, d)], start=y_face, end=y_end, op="join")
    web = comp.extrude("SideBolt_Boss_WebAdd", axis="Z",
                       loops=[comp.rect(expr.sub(x, expr.half(web_t)), expr.add(x, expr.half(web_t)), web_y0, y_end)],
                       start=web_z0, end=z, op="join")
    return [cyl, web]


@shared("fasteners.side_bolt_cut", placement=("x", "z", "y_face", "pocket_y0"))
def side_bolt_cut(comp, *, x, z, y_face, length, head_d, head_h, shank_d, pocket_d, pocket_y0, pocket_h):
    """The side bolt's three bores (axis Y, cuts): the head recess ``head_d`` from ``y_face`` over ``head_h``, the shank
    ``shank_d`` through ``length``, and the E-clip pocket ``pocket_d`` from ``pocket_y0`` over ``pocket_h``."""
    def bore(name, d, y0, y1):
        return comp.extrude(f"SideBolt_Bore_{name}Cut", axis="Y", loops=[comp.circle(x, z, d)], start=y0, end=y1, op="cut")

    return [bore("Head", head_d, y_face, expr.add(y_face, head_h)),
            bore("Shank", shank_d, y_face, expr.add(y_face, length)),
            bore("Pocket", pocket_d, pocket_y0, expr.add(pocket_y0, pocket_h))]
