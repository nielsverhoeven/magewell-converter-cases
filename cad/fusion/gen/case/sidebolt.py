"""Side bolt: the captive 1/4"-20 bolt's boss and web (B6) and its three bores through the far wall (B6); owner ``SideBolt``.

Oracle: ``mcc_captive_side_bolt_boss`` and ``mcc_captive_side_bolt_cut`` (``lib/mcc/fasteners.scad:162-211,249-291``) placed by
``mcc_shell_base`` (``shell.scad:284-286,324-326``).  Both go through the shared builders of ``shared/fasteners.py``.  The boss
is flush with the far wall's outer face (``MCC_SIDE_BOLT_PROUD`` is 0), so ``y_face`` is the outer face ``frame.YL``; the web runs
up to the bolt axis, not to the boss underside as the oracle's does (D81.5: a join shares volume or a face with its target).
There is no flag: the side bolt is in every case.
"""
from __future__ import annotations

from ..shared import fasteners
from . import frame as F

X, Z = "V_SIDEBOLT_X", "V_SIDEBOLT_Z"
LENGTH = "MCC_WALL + MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T"   # from the outer face to the end of the boss (the pad's face)


def add(base) -> None:
    """B6: the boss cylinder and its support web (two joins), through ``fasteners.side_bolt_boss``."""
    fasteners.side_bolt_boss(base, x=X, z=Z, y_face=F.YL, length=LENGTH, d="MCC_SIDE_BOLT_BOSS_OD",
                             web_t="MCC_SIDE_BOLT_SUPPORT_WEB_T", web_y0=F.YIL, web_z0=F.FT)


def cut(base) -> None:
    """B6: the head recess, the shank bore and the E-clip pocket (three cuts), through ``fasteners.side_bolt_cut``."""
    fasteners.side_bolt_cut(base, x=X, z=Z, y_face=F.YL, length=LENGTH, head_d="MCC_SIDE_BOLT_HEAD_D + 2 * MCC_CLR_SLIDE",
                            head_h="MCC_SIDE_BOLT_HEAD_REC_H", shank_d="MCC_TRIPOD_CLR_D", pocket_d="MCC_SIDE_BOLT_POCKET_D",
                            pocket_y0="-V_CASE_W / 2 + MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T",
                            pocket_h="MCC_SIDE_BOLT_POCKET_H")
