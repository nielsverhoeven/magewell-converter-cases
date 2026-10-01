"""Vents: the far-wall and minus X wall runs (B8) and the lid vent field (L4); owner ``Vent``.

Oracle: ``mcc_vents`` and ``mcc_lid_vents_cut`` (``lib/mcc/vents.scad:131-151,287-341``).  The oracle tiles a run with slots and
drops the slots that overlap an exclusion; the solver turns each run into a fixed number of contiguous segments, one per set,
with the position of the first slot (``V_VENT_<S>_X0``, the slot's centre) and its own count (``V_N_VENT_<S>``).  A segment is a
seed slot, cut through the wall (or the lid), and a linear pattern of it at the pitch ``slot + web``; a segment that does not
exist has its flag set and its count parked at 1, and no single instance of a pattern is ever suppressed (ruling e, D81.7).
The capacity of every band is ``frame.CAPACITY``, iterated through the tuples of ``frame`` (verdict B1).

The slot seeds start and end exactly on the wall faces; the oracle's ``MCC_EPS`` overshoot is air.
"""
from __future__ import annotations

from ..core import expr
from . import frame as F

SLOT_W = "MCC_VENT_SLOT_W"
PITCH = "MCC_VENT_SLOT_W + MCC_VENT_WEB_W"
LID_SLOT_W = "MCC_LID_VENT_SLOT_W"
LID_SLOT_L = "MCC_LID_VENT_SLOT_L"
LID_PITCH = "MCC_LID_VENT_SLOT_W + MCC_LID_VENT_WEB_W"
LID_ROW_PITCH = "MCC_LID_VENT_SLOT_L + MCC_LID_VENT_ROW_GAP"

# (runs of the band, z low, z high): one row per band of the far wall, every run of a band shares its two heights.
FAR_BANDS = (
    (F.VENT_FAR_LOW, "V_VENT_FARLO_Z_LO", "V_VENT_FARLO_Z_HI"),
    (F.VENT_FAR_HIGH, "V_VENT_FARUP_Z_LO", "V_VENT_FARUP_Z_HI"),
    (F.VENT_EXH, "MCC_VENT_EXHAUST_Z_LO", "MCC_VENT_EXHAUST_Z_HI"),
)
NEGX_Z = ("V_VENT_NEGX_Z_LO", "V_VENT_NEGX_Z_HI")


def _x0(run: str) -> str:
    return f"V_VENT_{run.upper()}_X0"


def _y0(run: str) -> str:
    return f"V_VENT_{run.upper()}_Y0"


def _count(run: str) -> str:
    return f"V_N_VENT_{run.upper()}"


def _slot(centre: str, width: str) -> tuple:
    """The two ends of a slot of ``width`` whose centre is ``centre``."""
    return expr.sub(centre, expr.half(width)), expr.add(centre, expr.half(width))


def cut_base(base) -> None:
    """B8: every run of the far wall (axis Y, through the wall) and of the minus X wall (axis X, through the wall)."""
    for runs, z_lo, z_hi in FAR_BANDS:
        for run in runs:
            x0, x1 = _slot(_x0(run), SLOT_W)
            seed = base.extrude(f"Vent_{run}_SlotCut", axis="Y", loops=[base.rect(x0, x1, z_lo, z_hi)], start=F.YL, end=F.YIL,
                                op="cut")
            base.pattern(f"Vent_{run}_SlotPat", seed=seed, axis="X", count=_count(run), pitch=PITCH)
    for run in F.VENT_NEGX:
        y0, y1 = _slot(_y0(run), SLOT_W)
        seed = base.extrude(f"Vent_{run}_SlotCut", axis="X", loops=[base.rect(y0, y1, *NEGX_Z)], start=F.XL, end=F.XIL, op="cut")
        base.pattern(f"Vent_{run}_SlotPat", seed=seed, axis="Y", count=_count(run), pitch=PITCH)


def cut_lid(lid) -> None:
    """L4: the two runs of the lid vent field, each a grid of ``V_N_VENT_<S>`` slots by ``V_N_VENT_LID_ROWS`` rows (cuts)."""
    for run in F.VENT_LID:
        x0, x1 = _slot(_x0(run), LID_SLOT_W)
        seed = lid.extrude(f"Vent_{run}_SlotCut", axis="Z",
                           loops=[lid.rect(x0, x1, "V_VENT_LID_Y0", expr.add("V_VENT_LID_Y0", LID_SLOT_L))], start=F.ZT, end=F.ZLID,
                           op="cut")
        lid.pattern(f"Vent_{run}_SlotPat", seed=seed, axis="X", count=_count(run), pitch=LID_PITCH, axis2="Y",
                    count2="V_N_VENT_LID_ROWS", pitch2=LID_ROW_PITCH)
