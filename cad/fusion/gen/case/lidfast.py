"""Lid fasteners: bosses, webs and bores in the base (B3) and the countersunk screw holes of the lid (L3); owner ``Fastener``.

Oracle: ``mcc_heat_set_boss`` and ``mcc_heat_set_bore`` (``lib/mcc/fasteners.scad``), ``_mcc_gusset_web`` (``shell.scad:77-100``)
and ``mcc_lid_screw_hole`` (the countersink of issue #100).  Three sets, one per place: ``Corners`` (four corner fasteners, no
flag), ``PatchMid`` and ``FarMid`` (one fastener each; their flags switch the set).  The bosses, bores and lid holes are the
shared builders of ``shared/fasteners.py``; the gusset web, which has no shared builder, is built here as a polygon prism (D81.6).
"""
from __future__ import annotations

from ..core import expr
from ..shared import fasteners
from . import frame as F

# (set, centres): every set is its own call of the shared builders, so that its flag switches exactly its own features.
SETS = (
    ("Corners", ((F.FX, F.FY), (F.FX, expr.neg(F.FY)), (expr.neg(F.FX), F.FY), (expr.neg(F.FX), expr.neg(F.FY)))),
    ("PatchMid", (("V_FAST_PATCH_MID_X", F.FY),)),
    ("FarMid", (("V_FAST_FAR_MID_X", expr.neg(F.FY)),)),
)
# The wall each web ties into, per fastener of every set: corners towards the nearer X wall, the patch mid towards plus Y, the
# far mid towards minus Y (plan 3.4, finding 2.2).
DIRECTIONS = {
    "Corners": ("+X", "+X", "-X", "-X"),
    "PatchMid": ("+Y",),
    "FarMid": ("-Y",),
}

TU, TV = "V_WEB_TAN_U", "V_WEB_TAN_V"        # tangent point of the web circle, in the boss frame
REACH = "MCC_FASTENER_INSET - MCC_WEB_FACE_MARGIN"  # the web bar's distance from the boss axis (inside the wall)
HALF = "V_BOSS_D / 2"                        # half width of the web bar


def web_points(cx, cy, direction: str) -> tuple:
    """The four model points of the gusset web of the boss at ``(cx, cy)`` whose wall lies towards ``direction``.

    In the boss's own frame (plus u towards the wall) the trapezoid is ``(TU, TV)``, ``(R, B)``, ``(R, -B)``, ``(TU, -TV)``;
    ``"-X"`` negates every u term, the Y directions swap u and v."""
    if direction not in ("+X", "-X", "+Y", "-Y"):
        raise ValueError(f"direction is '+X', '-X', '+Y' or '-Y', got {direction!r}")

    def offset(c, term, sign):
        return expr.add(c, term) if sign > 0 else expr.sub(c, term)

    toward = 1 if direction[0] == "+" else -1
    frame_uv = ((TU, 1, TV, 1), (REACH, 1, HALF, 1), (REACH, 1, HALF, -1), (TU, 1, TV, -1))
    points = []
    for u_term, u_sign, v_term, v_sign in frame_uv:
        u, v = (u_term, toward * u_sign), (v_term, v_sign)
        points.append(((u, v), (v, u))[direction[1] == "Y"])
    return tuple((offset(cx, *x), offset(cy, *y)) for x, y in points)


def add_base(base) -> None:
    """B3: the three boss sets (one join each), then the web of every boss (one join per set, one polygon per boss)."""
    for name, centres in SETS:
        fasteners.heat_set_boss(base, name, centres=list(centres), z0=F.FT, z1=F.ZT, d="V_BOSS_D")
    for name, centres in SETS:
        loops = [base.polygon(web_points(cu, cv, d)) for (cu, cv), d in zip(centres, DIRECTIONS[name])]
        base.extrude(f"Fastener_{name}_WebAdd", axis="Z", loops=loops, start=F.FT, end=F.ZT, op="join")


def cut_base(base) -> None:
    """B3: the blind insert bore in the top of every boss."""
    for name, centres in SETS:
        fasteners.insert_bore(base, name, centres=list(centres), z_open=F.ZT, depth="V_INSERT_DEPTH", d="V_INSERT_HOLE_D")


def cut_lid(lid) -> None:
    """L3: the countersunk screw hole of the lid above every boss (the shaft and one cone per hole)."""
    for name, centres in SETS:
        fasteners.lid_screw_hole(lid, name, centres=list(centres), z0=F.ZT, z1=F.ZLID, shaft_d="MCC_M3_CLR_D",
                                 csk_d="MCC_LID_CSK_D", angle="MCC_LID_CSK_ANGLE")
