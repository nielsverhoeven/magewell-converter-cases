"""S1 block of ``shared/panel.py``: ``d_wall_cut`` (plan 5.3).  ``add(comps)`` and ``cut(comps)`` as ``s1_document`` calls them.

The block is a wall tile 40 x 5 x 45 whose seat face is at y = 0 and whose wall lies below it, with the connector at the middle of
the tile's height, as in the oracle (``mcc_panel_wall_cut("NE8FDP-B", wall_t = 5)`` turned to look along y).  The oracle's local X
points to world minus X, so the screws sit at ``(+SX, +SY)`` and ``(-SX, -SY)``: ``mirror=True``, as the case's patch wall has it.
``plate_cut`` has no block here; its block belongs to the coupon issue (#83).
"""
from __future__ import annotations

from ..shared import panel


def add(comps: dict) -> None:
    """The block has no additive shared call."""


def cut(comps: dict) -> None:
    panel.wall_cut(comps["d_wall_cut"], "D", family="D", axis="Y", a=None, b="T_D_H / 2", face=None, wall_side="lower",
                   seat_t="MCC_PANEL_SEAT_T", wall_t="MCC_PANEL_SEAT_T + MCC_WALL", seat_d="T_D_SEAT_D", win_d="T_D_WIN_D",
                   mirror=True, turn=False)
