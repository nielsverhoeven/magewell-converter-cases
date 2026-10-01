"""Cradle: the deck frame, the two rib patterns of the deck lattice and the far-flank ribs (issue #81, plan 3.4; stage B4).

Oracle: ``mcc_cradle``, ``_mcc_cradle_deck_lattice`` and ``_mcc_far_flank_rib`` (``lib/mcc/cradle.scad:104-119,235-282``).  Every
dimension is a parameter-name expression: the device box ``V_DEV_*``, the deck ladder ``V_N_DECK_*``, ``V_DECK_*0`` and
``V_DECK_PITCH_*``, and the far-flank rib position ``V_FARRIB<i>_X`` of each of the ribs of ``frame.FAR_RIBS``.  A rib that the
device does not use is switched off by its flag ``Cradle_FarRib<i>`` (the set of its two features), never by a branch here.

Everything here is a join.  The deck frame, the lattice ribs and the legs of a far-flank rib stand on the floor top (``MCC_FLOOR_T``)
and the deck top is ``V_DEV_Z_LO``; the body of a rib stands on the legs, so every join shares a face with what it joins.

Known dead feature: ``Cradle_FarRib2_LegsAdd``.  Rib 2 stands at x = -12 mm and the far-middle lid fastener at -12.64 mm in the template
(the replay finds the same in all nine configurations), so its legs lie wholly inside that fastener's boss and web (stage B3 joins first) and the join changes no volume.  The
geometry is the oracle's; the feature is kept as the plan has it (a Z-extrude per feature keeps the sketches independent of the sign
of the rib's x, which the kit checks).
"""
from __future__ import annotations

from . import frame as F

RIB_T = "MCC_CRADLE_RIB_T"
DECK_LO = "V_DEV_Z_LO"
DECK_X = ("V_DEV_X_LO", "V_DEV_X_HI")
DECK_Y = ("V_DEV_Y_LO", "V_DEV_Y_HI")
LEG = "min(MCC_CRADLE_RIB_LEG, MCC_GAP_FAR / 2)"


def add_deck(base) -> None:
    """The deck frame (a ring around the device box, one wall wide) and the two rib patterns of the lattice inside it."""
    base.extrude("Cradle_Deck_FrameAdd", axis="Z",
                 loops=[base.rect("V_DEV_X_LO - MCC_WALL", "V_DEV_X_HI + MCC_WALL", "V_DEV_Y_LO - MCC_WALL", "V_DEV_Y_HI + MCC_WALL")],
                 holes=[base.rect(*DECK_X, *DECK_Y)], start=F.FT, end=DECK_LO, op="join")
    # ribs at the X grid: one rib seed spanning the device's Y range, repeated along X
    base.extrude("Cradle_Deck_RibXAdd", axis="Z", loops=[base.rect(f"V_DECK_X0 - {RIB_T} / 2", f"V_DECK_X0 + {RIB_T} / 2", *DECK_Y)],
                 start=F.FT, end=DECK_LO, op="join")
    base.pattern("Cradle_Deck_RibXPat", seed="Cradle_Deck_RibXAdd", axis="X", count="V_N_DECK_X", pitch="V_DECK_PITCH_X")
    # ribs at the Y grid: one rib seed spanning the device's X range, repeated along Y
    base.extrude("Cradle_Deck_RibYAdd", axis="Z", loops=[base.rect(*DECK_X, f"V_DECK_Y0 - {RIB_T} / 2", f"V_DECK_Y0 + {RIB_T} / 2")],
                 start=F.FT, end=DECK_LO, op="join")
    base.pattern("Cradle_Deck_RibYPat", seed="Cradle_Deck_RibYAdd", axis="Y", count="V_N_DECK_Y", pitch="V_DECK_PITCH_Y")


def add_far_rib(base, i: int) -> None:
    """Far-flank rib ``i``: two legs from the floor to the deck top at the two ends of the duct, and the body above the deck top
    from the far wall's inner face to the device's far flank (it locates the device against the wall)."""
    x = f"V_FARRIB{i}_X"
    x0, x1 = f"{x} - {RIB_T} / 2", f"{x} + {RIB_T} / 2"
    base.extrude(f"Cradle_FarRib{i}_LegsAdd", axis="Z",
                 loops=[base.rect(x0, x1, F.YIL, f"{F.YIL} + {LEG}"), base.rect(x0, x1, f"V_DEV_Y_LO - {LEG}", "V_DEV_Y_LO")],
                 start=F.FT, end=DECK_LO, op="join")
    base.extrude(f"Cradle_FarRib{i}_BodyAdd", axis="Z", loops=[base.rect(x0, x1, F.YIL, "V_DEV_Y_LO")],
                 start=DECK_LO, end=f"{DECK_LO} + MCC_CRADLE_RIB_H", op="join")


def add(base) -> None:
    """B4: the cradle (joins): the deck, then the far-flank ribs of the capacity table."""
    add_deck(base)
    for i in F.FAR_RIBS:
        add_far_rib(base, i)
