"""Fan aperture with the grille re-joins (issue #81, plan 3.4; stage B10; verdict D81.8).

Oracle: ``mcc_fan_cutout`` with ``grille = true`` and its private ``_mcc_fan_grille_2d`` (``lib/mcc/fan.scad:55-165``), placed by
``mcc_vents`` in the plus X wall (``vents.scad:171-179``).  The oracle cuts "opening minus grille"; the document cuts the round
opening at the inner diameter of the outermost grille ring (``V_FAN_RING3_ID``), so that ring stays wall material and is never a
feature, and joins the two inner rings and the three bars back into the cut afterwards (re-joins within ``Fan_Aperture_OpeningCut``).
The bars keep the radius of the oracle's grille, ``V_FAN_OPENING_D / 2``, so they end inside the wall; what a bar adds to the body lies
inside the cut.  The oracle's hub circle lies inside the bars and is left out.  Each bar is two opposite spokes of the oracle: a spoke at
the oracle's local angle ``a`` points to ``(y, z) = (sin a, -cos a)`` in the model, because the fan frame is placed with
``rotate([0, 90, 0])``.

Every dimension is a parameter-name expression: the fan centre ``V_FAN_Y`` and ``V_CONN_Z``, the ring diameters ``V_FAN_RING<i>_OD``
and ``_ID``, and the grille constants.  The whole aperture is switched off by its flag ``Fan_Aperture`` (the set of its features).
"""
from __future__ import annotations

from . import frame as F

CY = "V_FAN_Y"
HALF_PITCH = "V_FAN_HOLE_PITCH / 2"
R = "V_FAN_OPENING_D / 2"                       # bar half length: the radius of the oracle's grille, in the wall
H = "MCC_FAN_GRILLE_SPOKE_W / 2"                # bar half width
PITCH = "MCC_FAN_GRILLE_SPOKE_PITCH"            # angle between neighbouring spokes
OPENING = "Fan_Aperture_OpeningCut"


def cut(base) -> None:
    """B10: the four screw holes, then the round opening at the inner diameter of the outermost ring (cuts)."""
    screws = [base.circle(f"{CY} {sy} {HALF_PITCH}", f"{F.ZC} {sz} {HALF_PITCH}", "V_FAN_HOLE_D")
              for sy in ("+", "-") for sz in ("+", "-")]
    base.extrude("Fan_Aperture_ScrewCut", axis="X", loops=screws, start=F.XIH, end=F.XH, op="cut")
    base.extrude(OPENING, axis="X", loops=[base.circle(CY, F.ZC, "V_FAN_RING3_ID")], start=F.XIH, end=F.XH, op="cut")


def _bar(base, name: str, angle: str) -> None:
    """One bar: the rectangle of two opposite spokes at ``angle`` from the vertical, as a polygon of four corners."""
    s, c = f"sin({angle})", f"cos({angle})"
    corners = [(f"{CY} + {R} * {s} + {H} * {c}", f"{F.ZC} - {R} * {c} + {H} * {s}"),
               (f"{CY} + {R} * {s} - {H} * {c}", f"{F.ZC} - {R} * {c} - {H} * {s}"),
               (f"{CY} - {R} * {s} - {H} * {c}", f"{F.ZC} + {R} * {c} - {H} * {s}"),
               (f"{CY} - {R} * {s} + {H} * {c}", f"{F.ZC} + {R} * {c} + {H} * {s}")]
    base.extrude(name, axis="X", loops=[base.polygon(corners)], start=F.XIH, end=F.XH, op="rejoin", within=OPENING)


def rejoin(base) -> None:
    """B10: the two inner rings and the three bars of the grille (re-joins within the opening cut)."""
    for i in F.GRILLE_REJOIN_RINGS:
        base.extrude(f"Fan_Aperture_Ring{i}Rejoin", axis="X", loops=[base.circle(CY, F.ZC, f"V_FAN_RING{i}_OD")],
                     holes=[base.circle(CY, F.ZC, f"V_FAN_RING{i}_ID")], start=F.XIH, end=F.XH, op="rejoin", within=OPENING)
    base.extrude("Fan_Aperture_BarARejoin", axis="X",
                 loops=[base.rect(f"{CY} - {H}", f"{CY} + {H}", f"{F.ZC} - {R}", f"{F.ZC} + {R}")],
                 start=F.XIH, end=F.XH, op="rejoin", within=OPENING)
    _bar(base, "Fan_Aperture_BarBRejoin", PITCH)
    _bar(base, "Fan_Aperture_BarCRejoin", f"2 * {PITCH}")
