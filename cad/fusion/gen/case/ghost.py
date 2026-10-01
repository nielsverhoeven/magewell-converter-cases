"""The device ghost (issue #81, plan 3.4; oracle ``ghost.scad:93-96`` and ``case.scad:116-120``).

One box body in the ``Ghost_Device`` component: the device's bounding box ``V_DEV_*`` of the parameter set, so a configuration shows
the device it holds.  The ghost has no flag and is never exported (the document plan's ``never_export``).
"""
from __future__ import annotations


def build(ghost) -> None:
    """One box body in the ghost component."""
    ghost.extrude("Ghost_Device_Body", axis="Z", loops=[ghost.rect("V_DEV_X_LO", "V_DEV_X_HI", "V_DEV_Y_LO", "V_DEV_Y_HI")],
                  start="V_DEV_Z_LO", end="V_DEV_Z_HI", op="new")
