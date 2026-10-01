"""S1 blocks of ``shared/tg.py``: ``tongue`` and ``groove`` (plan 5.3).  ``add(comps)`` and ``cut(comps)`` as ``s1_document`` calls them."""
from __future__ import annotations

from ..shared import tg
from .s1_document import X0, X1, Y0, Y1


def add(comps: dict) -> None:
    tg.tongue(comps["tongue"], "Block_Tongue_RingAdd", x0=X0, x1=X1, y0=Y0, y1=Y1, z="T_TG_PLATE", width="MCC_TG_W",
              height="MCC_TG_H")


def cut(comps: dict) -> None:
    tg.groove(comps["groove"], "Block_Groove_RingCut", x0=X0, x1=X1, y0=Y0, y1=Y1, z=None, width="MCC_TG_W", height="MCC_TG_H",
              clearance="MCC_CLR_TG")
