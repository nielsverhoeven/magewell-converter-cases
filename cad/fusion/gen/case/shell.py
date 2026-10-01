"""The shell of the case: floor, walls, tongue and the lid with its groove (issue #81, plan 3.4; stages B1, B2, L1, L2).

Oracle: ``_mcc_outer_shell_solid`` (``lib/mcc/shell.scad:49-56,269``), the tongue and groove (``shell.scad:110-137,280-281,
418-426``) and the lid slab.  Every dimension is a parameter-name expression from ``frame.py``.
"""
from __future__ import annotations

from ..shared import tg
from . import frame as F


def add_base(base) -> None:
    """B1: the floor slab and the wall ring around the cavity (the outer shell minus the cavity)."""
    base.extrude("Shell_Floor_Body", axis="Z", loops=[base.rect(F.XL, F.XH, F.YL, F.YH)], start=None, end=F.FT, op="new")
    base.extrude("Shell_Walls_Add", axis="Z", loops=[base.rect(F.XL, F.XH, F.YL, F.YH)],
                 holes=[base.rect(F.XIL, F.XIH, F.YIL, F.YIH)], start=F.FT, end=F.ZT, op="join")


def add_tongue(base) -> None:
    """B2: the tongue ring on the wall top, with the patch side moved in by ``MCC_TG_PATCH_INSET`` (D62.1)."""
    tg.tongue(base, "Shell_Tongue_RingAdd", x0=F.XIL, x1=F.XIH, y0=F.YIL, y1=F.YTG, z=F.ZT, width="MCC_TG_W", height="MCC_TG_H")


def add_lid(lid) -> None:
    """L1: the lid slab from the top of the base walls up by ``MCC_LID_T``."""
    lid.extrude("Shell_Lid_Body", axis="Z", loops=[lid.rect(F.XL, F.XH, F.YL, F.YH)], start=F.ZT, end=F.ZLID, op="new")


def cut_lid(lid) -> None:
    """L2: the groove, the tongue's rectangle grown by the clearance ``MCC_CLR_TG``, cut into the underside of the lid."""
    tg.groove(lid, "Shell_Groove_RingCut", x0=F.XIL, x1=F.XIH, y0=F.YIL, y1=F.YTG, z=F.ZT, width="MCC_TG_W", height="MCC_TG_H",
              clearance="MCC_CLR_TG")
