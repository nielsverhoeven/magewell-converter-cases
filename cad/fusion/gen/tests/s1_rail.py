"""S1 blocks of ``shared/rail.py``: ``rail_male`` and ``rail_female`` (plan 5.3).  ``add(comps)`` and ``cut(comps)`` as ``s1_document`` calls them.

The male block is a 60 x 80 x 3 plate below z = 0 with the rail standing on it (``mcc_rail_male(len = 60)``); the female block is
the 66 x 71 sill block with its backing and the groove, slot and lead-in (``mcc_rail_female_cut(len = 60, open_ext = 4, entry_x =
33)``).  Neither passes ``lock_e``: only the rail-lock coupon does (A5).
"""
from __future__ import annotations

from ..shared import rail


def add(comps: dict) -> None:
    rail.male(comps["rail_male"], "Male", x_mid=None, y_mid=None, z0=None, length="T_RAIL_LEN", flip=False)
    rail.female_backing(comps["rail_female"], "Female", x_mid=None, y_mid=None, z_sill="MCC_RAIL_SILL_H", length="T_RAIL_LEN")


def cut(comps: dict) -> None:
    rail.female_cut(comps["rail_female"], "Female", x_mid=None, y_mid=None, z0=None, length="T_RAIL_LEN",
                    x_open="T_RAIL_LEN / 2 + MCC_WALL", lead_in=True)
