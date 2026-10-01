"""The panel dispatcher (issue #81, plan 3.10, verdict A4 and A6; owner ``Patch``): the only entry for products.

Oracle: ``lib/mcc/panel.scad``: ``mcc_panel_wall_cut`` (a connector mounted in the case's own wall) and ``mcc_panel_cutout`` (a flat
panel, the coupons).  ``family`` is an option, not a dimension: ``"D"`` (the Neutrik D series, the blank ``DBA-BL-B`` included) is
the only value, and anything else raises ``ValueError``, as the oracle's unknown-part assert does (``panel.scad:38-42``).  The
Mini-DIN-8 PTZ/Tally port stays internal on every SKU and is never dispatched.

A product calls ``panel.wall_cut`` or ``panel.plate_cut`` and never ``shared/neutrik.py`` (verdict A8, rule 4); the build record
shows each ``neutrik.*`` call with its ``panel.*`` parent, which is what the check CK11 asks for.  Options and frame: ``neutrik.py``.
Every argument is required, so the build record always carries the same arguments and CK10 can compare two documents.
"""
from __future__ import annotations

from . import neutrik, shared

FAMILIES = ("D",)
PLACEMENT = neutrik.PLACEMENT
WALL_PLACEMENT = neutrik.WALL_PLACEMENT


def _family(family) -> None:
    if family not in FAMILIES:
        raise ValueError(f"unknown panel family {family!r}: the families are {FAMILIES} "
                         "(Neutrik D parts and the DBA-BL-B blank; Mini-DIN-8 stays internal)")


@shared("panel.wall_cut", placement=WALL_PLACEMENT)
def wall_cut(comp, set_name, *, family, axis, a, b, face, wall_side, seat_t, wall_t, seat_d, win_d, mirror, turn):
    """A connector mounted straight into a wall ``wall_t`` thick: seat hole, body window and the two fixing bores
    (``Patch_<set>_SeatCut``, ``_WindowCut``, ``_BoreCut``).  The case's patch wall passes ``wall_side="lower"``,
    ``mirror=True`` and ``turn=False``."""
    _family(family)
    return neutrik.d_wall_cut(comp, set_name, axis=axis, a=a, b=b, face=face, wall_side=wall_side, seat_t=seat_t, wall_t=wall_t,
                              seat_d=seat_d, win_d=win_d, mirror=mirror, turn=turn)


@shared("panel.plate_cut", placement=PLACEMENT)
def plate_cut(comp, set_name, *, family, axis, a, b, face, wall_side, panel_t, seat_t, hole_d, mirror, turn):
    """A connector's cutout in a flat panel ``panel_t`` thick with its rear seat pocket (``Patch_<set>_HoleCut``,
    ``_ScrewCut``, ``_PocketACut``, ``_PocketBCut``, ``_PocketRCut``)."""
    _family(family)
    return neutrik.d_plate_cut(comp, set_name, axis=axis, a=a, b=b, face=face, wall_side=wall_side, panel_t=panel_t,
                               seat_t=seat_t, hole_d=hole_d, mirror=mirror, turn=turn)
