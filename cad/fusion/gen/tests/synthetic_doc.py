"""A tiny builder for the tests of the command line (``test_plan.py``): one part, one rail call.

Not a product document: there are no product builders yet (plan section 3.13).  The options of the plan select the
variant: ``width`` (the non-placement argument of the rail call, CK10), ``lock_e`` (an optional argument passed
only when given), ``misuse`` (a second body: PhaseError), ``stray_rail`` (a ``Rail_*`` object made outside a ``rail.*`` call, CK11).
"""
from __future__ import annotations

from ..core.facade import Kit


def build(ctx):
    kit = Kit(ctx)
    base = kit.component("Base", role="part", datum=(None, None, None))
    base.extrude("Shell_Floor_Body", axis="Z", loops=[base.rect("MCC_WALL", "V_L", "MCC_WALL", "V_W")],
                 start=None, end="V_H", op="new")
    arguments = {"x": "V_X", "width": ctx.options.get("width", "V_W")}
    if "lock_e" in ctx.options:
        arguments["lock_e"] = ctx.options["lock_e"]
    with base.shared_call("rail.male", arguments, ("x",)):
        base.extrude("Rail_Male_FootAdd", axis="Z", loops=[base.rect("V_X", "V_L", "MCC_WALL", "V_W")],
                     start="MCC_WALL", end="V_H", op="join")
    if ctx.options.get("stray_rail"):
        base.extrude("Rail_Stray_FootAdd", axis="Z", loops=[base.rect("V_X", "V_L", "MCC_WALL", "V_W")],
                     start="MCC_WALL", end="V_H", op="join")
    if ctx.options.get("misuse"):
        base.extrude("Shell_Extra_Body", axis="Z", loops=[base.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="new")
    return kit.inventory()
