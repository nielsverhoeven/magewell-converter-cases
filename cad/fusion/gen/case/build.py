"""Entry point of the case document (contract C2 of #79; issue #81, plan 3.1): the fixed call table of the case master.

``build(ctx)`` creates the five components under the root and runs the table below in order.  Rows 1 to 6 are joins, 7 to 13 are
cuts, 14 is the re-join: the order the kit enforces.  No function receives a device, a slug or a case definition; each receives
the ``Component`` objects it works on and nothing else.  Row 19 of the plan (the enhancement hook of #85) is reserved: no code.

The option ``stage`` (``options['stage']`` of the document plan, an int or None) is the S2 stage of the oracle harness
(``cad.fusion.gen.tests.oracle``): with ``stage = k`` only the calls of stages up to k run, the base stages B1 to B8 and B10
and the lid stages L1 to L4 sharing the number k.  None runs everything.  There is no stage B9: the floor cuts of the plan
(strap pockets and stacking recesses) left the oracle with issue #87, so ``floor`` has no ``cut`` and this table no row 12.
"""
from __future__ import annotations

from ..core.facade import Kit
from ..core.names import KitError
from . import cradle, fan, floor, frame, ghost, lidfast, patch, reserve, shell, sidebolt, switch, vents

# (row of plan 3.1, stage, function, component keys).  Stage None: not a stage of the oracle (reserves and the ghost).
CALLS = (
    (1, 1, shell.add_base, ("base",)),
    (1, 2, shell.add_tongue, ("base",)),
    (2, 3, lidfast.add_base, ("base",)),
    (3, 4, cradle.add, ("base",)),
    (4, 5, floor.add, ("base",)),
    (5, 6, sidebolt.add, ("base",)),
    (6, 10, switch.add, ("base",)),
    (7, 3, lidfast.cut_base, ("base",)),
    (8, 5, floor.cut_rail, ("base",)),
    (9, 6, sidebolt.cut, ("base",)),
    (10, 7, patch.cut, ("base",)),
    (11, 8, vents.cut_base, ("base",)),
    (13, 10, fan.cut, ("base",)),
    (13, 10, switch.cut, ("base",)),
    (14, 10, fan.rejoin, ("base",)),
    (15, 1, shell.add_lid, ("lid",)),
    (15, 2, shell.cut_lid, ("lid",)),
    (16, 3, lidfast.cut_lid, ("lid",)),
    (17, 4, vents.cut_lid, ("lid",)),
    (18, None, reserve.build, ("fan_bay", "splitter_bay")),
    (18, None, ghost.build, ("ghost",)),
)


def _stage(options: dict):
    stage = options.get("stage")
    if stage is not None and (not isinstance(stage, int) or isinstance(stage, bool) or stage < 1):
        raise KitError(f"options['stage'] is None or a whole number of at least 1, got {stage!r}")
    return stage


def build(ctx):
    """Build the case document on ``ctx.backend`` and return the raw inventory the kit recorded."""
    stage = _stage(ctx.options)
    kit = Kit(ctx)
    comps = {
        "base": kit.component("Base", role="part", datum=frame.DATUM),
        "lid": kit.component("Lid", role="part", datum=frame.DATUM),
        "fan_bay": kit.component("Reserve_FanBay", role="reserve", datum=frame.DATUM),
        "splitter_bay": kit.component("Reserve_SplitterBay", role="reserve", datum=frame.DATUM),
        "ghost": kit.component("Ghost_Device", role="ghost", datum=frame.DATUM),
    }
    for _row, number, function, keys in CALLS:
        if stage is None or (number is not None and number <= stage):
            function(*(comps[key] for key in keys))
    return kit.inventory()
