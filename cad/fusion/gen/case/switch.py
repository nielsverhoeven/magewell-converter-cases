"""Fan switch: the pad and the cutout in the plus X wall (issue #81, plan 3.4; stage B10).

Oracle: ``mcc_switch_pad`` (a frustum from the body diameter at the pad's tip to the pad diameter at the wall's inner face) and
``mcc_switch_cutout`` (the through bore and the recess pocket), placed by the shell at ``(L / 2 - MCC_WALL, switch_y, switch_z)``
(``lib/mcc/shell.scad:303-308,335-340``, ``switch.scad:65-143``).  The pad is a join, a loft that stands on the wall's inner face; the
bore and the recess are cuts through the wall and the pad.  Every dimension is a parameter-name expression (``V_SWITCH_*``,
``V_CASE_L``, ``V_CONN_Z``); the whole switch is switched off by its flag ``Switch_Toggle``.
"""
from __future__ import annotations

from . import frame as F

CY = "V_SWITCH_Y"
PAD_X = "V_CASE_L / 2 - V_SWITCH_PAD_T"      # the pad's tip, inside the case


def add(base) -> None:
    """B10: the pad (a join), a loft from the body diameter at its tip to the pad diameter on the wall's inner face."""
    base.loft("Switch_Toggle_PadAdd", axis="X", loop_a=base.circle(CY, F.ZC, "V_SWITCH_BODY_D"), at_a=PAD_X,
              loop_b=base.circle(CY, F.ZC, "V_SWITCH_PAD_D"), at_b=F.XIH, op="join")


def cut(base) -> None:
    """B10: the through bore (from the pad's tip to the outer face), then the recess pocket (from its depth to the outer face)."""
    base.extrude("Switch_Toggle_BoreCut", axis="X", loops=[base.circle(CY, F.ZC, "V_SWITCH_BORE_D")], start=PAD_X, end=F.XH, op="cut")
    base.extrude("Switch_Toggle_RecessCut", axis="X", loops=[base.circle(CY, F.ZC, "V_SWITCH_BODY_D")],
                 start="V_CASE_L / 2 - V_SWITCH_RECESS_T", end=F.XH, op="cut")
