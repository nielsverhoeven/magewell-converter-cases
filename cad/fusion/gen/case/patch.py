"""Patch wall: the bezel recess and the connector cuts (B7); owner ``Patch``; the only caller of ``shared/panel.py`` in the case.

Oracle: ``_mcc_patch_wall_aperture`` and ``_mcc_patch_wall_recess`` (``lib/mcc/shell.scad:140-197``).  The recess is one polygon
prism along X (the roof rises outward and leaves through the wall top); then one ``panel.wall_cut`` per slot of
``frame.SLOTS`` (``MCC_SLOTS_MAX`` = 4), each its own set ``Patch_Slot<i>`` so that its flag switches exactly its own three
cuts.  The case passes ``wall_side="lower"``, ``mirror=True`` and ``turn=False``; the connector family is always ``D``.
"""
from __future__ import annotations

from ..shared import panel
from . import frame as F

HALF_H = "MCC_PLATE_H / 2"


def cut(base) -> None:
    """B7: the recess (``Patch_Recess_PocketCut``), then the seat, window and bores of every slot (cuts)."""
    zlo = F.ZC + " - " + HALF_H
    zhi = F.ZC + " + " + HALF_H
    base.extrude("Patch_Recess_PocketCut", axis="X", start="-V_PLATE_L / 2", end="V_PLATE_L / 2", op="cut", loops=[base.polygon([
        (F.YSEAT, zlo), (F.YH, zlo), (F.YH, f"{zhi} + MCC_PANEL_BEZEL_T * MCC_PATCH_RECESS_ROOF_K"), (F.YSEAT, zhi)])])
    for i in F.SLOTS:
        panel.wall_cut(base, f"Slot{i}", family="D", axis="Y", a=f"V_SLOT{i}_X", b=F.ZC, face=F.YSEAT, seat_t="MCC_PANEL_SEAT_T",
                       wall_t="MCC_T_PATCH - MCC_PANEL_BEZEL_T", seat_d=f"V_SLOT{i}_SEAT_D", win_d=f"V_SLOT{i}_WIN_D",
                       wall_side="lower", mirror=True, turn=False)
