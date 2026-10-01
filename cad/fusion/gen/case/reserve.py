"""The reserved bays: the fan bay and the splitter bay (issue #81, plan 3.4; arch brief B 'Reservation', verdicts D81.7, D81.11).

Oracle: the reserved boxes of ``layout.scad:331-342``.  Each bay is one box body in its own component, built from the six numeric
keys of the solver (``V_FANBAY_*``, ``V_SPLITBAY_*``) and nothing else.  Both exist in every configuration, with the fan on or off
(the bay is reserved even when unused); no suppress flag may name a ``Reserve_*`` feature, so none of the bodies below has a flag
in its set, and the kit's protected-prefix check refuses one.  A reserve is never exported (the document plan's ``never_export``).
The plug envelopes of the oracle's preview are not modelled (the default of Q81.2).
"""
from __future__ import annotations


def _bay(comp, name: str, prefix: str) -> None:
    comp.extrude(name, axis="Z", loops=[comp.rect(f"{prefix}_X_LO", f"{prefix}_X_HI", f"{prefix}_Y_LO", f"{prefix}_Y_HI")],
                 start=f"{prefix}_Z_LO", end=f"{prefix}_Z_HI", op="new")


def build(fan_bay, splitter_bay) -> None:
    """One box body in each reserve component."""
    _bay(fan_bay, "Reserve_FanBay_Body", "V_FANBAY")
    _bay(splitter_bay, "Reserve_SplitterBay_Body", "V_SPLITBAY")
