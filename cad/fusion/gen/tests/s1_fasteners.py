"""S1 blocks of ``shared/fasteners.py``: ``heat_set_boss``, ``lid_screw_hole`` and ``side_bolt`` (plan 5.3, #100 for the lid hole).

``add(comps)`` and ``cut(comps)`` as ``s1_document`` calls them.  The lid block holds a countersunk hole (the cone is a loft cut),
not the thumbscrew counterbore of the plan's first text.
"""
from __future__ import annotations

from ..shared import fasteners
from .s1_document import LEN


def add(comps: dict) -> None:
    fasteners.heat_set_boss(comps["heat_set_boss"], "Boss", centres=[(None, None)], z0="MCC_FLOOR_T", z1="MCC_FLOOR_T + T_BOSS_H",
                            d="MCC_BOSS_MIN_RATIO * MCC_INSERT_M3_OD")
    fasteners.side_bolt_boss(comps["side_bolt"], x=None, z="MCC_SIDE_BOLT_AXIS_Z", y_face=None, length=LEN,
                             d="MCC_SIDE_BOLT_BOSS_OD", web_t="MCC_SIDE_BOLT_SUPPORT_WEB_T", web_y0="MCC_WALL",
                             web_z0="MCC_FLOOR_T")


def cut(comps: dict) -> None:
    fasteners.insert_bore(comps["heat_set_boss"], "Boss", centres=[(None, None)], z_open="MCC_FLOOR_T + T_BOSS_H",
                          depth="MCC_INSERT_M3_LEN + MCC_INSERT_BORE_OVERDEPTH", d="MCC_INSERT_M3_HOLE_D")
    fasteners.lid_screw_hole(comps["lid_screw_hole"], "Lid", centres=[(None, None)], z0=None, z1="MCC_LID_T",
                             shaft_d="MCC_M3_CLR_D", csk_d="MCC_LID_CSK_D", angle="MCC_LID_CSK_ANGLE")
    fasteners.side_bolt_cut(comps["side_bolt"], x=None, z="MCC_SIDE_BOLT_AXIS_Z", y_face=None, length=LEN,
                            head_d="MCC_SIDE_BOLT_HEAD_CUT_D", head_h="MCC_SIDE_BOLT_HEAD_REC_H", shank_d="MCC_TRIPOD_CLR_D",
                            pocket_d="MCC_SIDE_BOLT_POCKET_D", pocket_y0="MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T",
                            pocket_h="MCC_SIDE_BOLT_POCKET_H")
