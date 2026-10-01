"""Floor: the rail sill block, the insertion passage and the female mount rail (B5); owner ``Floor`` and ``Rail``.

Oracle: ``mcc_floor_features_add`` (``lib/mcc/mounts.scad:76-97``: the sill block, the backing and the passage) and
``mcc_rail_features_cut`` (``mounts.scad:126-136``: the groove, the lock slot and the lead-in).  This is the only module of the
case that calls the shared rail builder (verdict A8); the rail's own features (``Rail_Female_*``) belong to the owner ``Rail``, the
sill and the passage (``Floor_RailSill_*``) to ``Floor``.  The option ``rail`` of the oracle sets the two flags
``Floor_RailSill`` and ``Rail_Female``, equal in every parameter set (T1-81.1); a suppressed sill takes its backing with it.

Since issue #87 the floor has no strap slots and no stacking recesses: there is no ``cut`` function and no stage B9.

Differences from the oracle (none moves a corner): the passage starts exactly on the sill's plus X face and ends on the inner
wall face instead of overlapping each by ``MCC_EPS`` (a join shares a face, D81.5); the groove ends on the plus X face, the
oracle's 1 mm overshoot being air.
"""
from __future__ import annotations

from ..core import expr
from ..shared import rail
from . import frame as F

SET = "Female"
RAIL_Y = "MCC_RAIL_Y"
RAIL_Z_SILL = "MCC_RAIL_SILL_H"
RAIL_LEN = "MCC_RAIL_LEN"
# half width of the sill: half the root width and a full side wall each side (D30)
_SW = expr.add(expr.half("MCC_RAIL_ROOT_W"), "MCC_RAIL_SILL_SIDE_W")
_SILL_END = expr.add(expr.half(RAIL_LEN), "MCC_RAIL_END_WALL")   # where the sill ends, measured from the middle of the rail


def add(base) -> None:
    """B5: the sill block, the insertion passage and the rail's backing (joins)."""
    y0, y1 = expr.sub(RAIL_Y, _SW), expr.add(RAIL_Y, _SW)
    base.extrude("Floor_RailSill_BlockAdd", axis="Z", loops=[base.rect(expr.neg(_SILL_END), _SILL_END, y0, y1)],
                 start=None, end=RAIL_Z_SILL, op="join")
    base.extrude("Floor_RailSill_PassageAdd", axis="Z", loops=[base.rect(_SILL_END, F.XIH, y0, y1)], start=None,
                 end=expr.mn(RAIL_Z_SILL, "V_FANBAY_Z_LO"), op="join")
    rail.female_backing(base, SET, x_mid=None, y_mid=RAIL_Y, z_sill=RAIL_Z_SILL, length=RAIL_LEN)


def cut_rail(base) -> None:
    """B5: the groove, the lock slot and the lead-in, open on the plus X face (cuts)."""
    rail.female_cut(base, SET, x_mid=None, y_mid=RAIL_Y, z0=None, length=RAIL_LEN, x_open=F.XH, lead_in=True)
