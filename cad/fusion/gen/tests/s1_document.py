"""The S1 test document ``MCC-S1`` (issue #81, plan 5.3, verdict A10): one component per shared-builder test block.

Every component is a plain block body (an extrude along Z of one rectangle; the two tongue-and-groove blocks and the D-wall block
are rings or slabs the same way), exported as target ``s1`` with the block name as part.  The shared-builder calls live in one
block module per shared module (``s1_tg``, ``s1_fasteners``, ``s1_panel``, ``s1_rail``), each with the two functions
``add(comps)`` and ``cut(comps)``, where ``comps`` maps a block name to its ``Component``.  ``build`` builds the bodies, then
calls ``add`` of every block module that exists, then ``cut`` of every block module that exists (a module is looked up with
``importlib.util.find_spec``; a missing one is left out), so a later milestone adds a block file without touching this one.

It names no inventory, is exempt from CK10 (its builder module lies under ``cad.fusion.gen.tests``) and never gives a complete
run.  The block sizes are the test parameters ``T_*`` of ``fixtures/s1_registry.csv``.
"""
from __future__ import annotations

import importlib
import importlib.util

from ..core.facade import Kit

BLOCK_MODULES = ("s1_tg", "s1_fasteners", "s1_panel", "s1_rail")

# Abbreviations of plan 5.3.
X0 = "-T_TG_L / 2 + MCC_WALL"
X1 = "T_TG_L / 2 - MCC_WALL"
Y0 = "-T_TG_W / 2 + MCC_WALL"
Y1 = "T_TG_W / 2 - MCC_WALL"
LEN = "MCC_WALL + MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T"
SW = "MCC_RAIL_ROOT_W / 2 + MCC_RAIL_SILL_SIDE_W"

# block -> (component name, datum)
COMPONENTS = {
    "tongue": ("S1_Tongue", ("-T_TG_L / 2", "-T_TG_W / 2", None)),
    "groove": ("S1_Groove", ("-T_TG_L / 2", "-T_TG_W / 2", None)),
    "heat_set_boss": ("S1_HeatSetBoss", ("-T_BOSS_PLATE / 2", "-T_BOSS_PLATE / 2", None)),
    "lid_screw_hole": ("S1_LidScrewHole", ("-T_LID / 2", "-T_LID / 2", None)),
    "side_bolt": ("S1_SideBolt", ("-T_SB_W / 2", None, None)),
    "d_wall_cut": ("S1_DWallCut", ("-T_D_W / 2", "-(MCC_PANEL_SEAT_T + MCC_WALL)", None)),
    "rail_male": ("S1_RailMale", ("-T_RAIL_LEN / 2", "-T_RAIL_PLATE_W / 2", "-T_RAIL_PLATE_T")),
    "rail_female": ("S1_RailFemale", ("-T_RAIL_LEN / 2 - MCC_RAIL_END_WALL", f"-({SW})", None)),
}


def _bodies(comps: dict) -> None:
    """The plain body of every block, and the one extra join of the side-bolt block (the floor strip)."""
    def body(block, name, loops, start, end, holes=None):
        c = comps[block]
        c.extrude(name, axis="Z", loops=loops, holes=holes, start=start, end=end, op="new")

    c = comps["tongue"]
    body("tongue", "Block_Tongue_Body", [c.rect("-T_TG_L / 2", "T_TG_L / 2", "-T_TG_W / 2", "T_TG_W / 2")], None, "T_TG_PLATE",
         holes=[c.rect(X0, X1, Y0, Y1)])
    c = comps["groove"]
    body("groove", "Block_Groove_Body", [c.rect("-T_TG_L / 2", "T_TG_L / 2", "-T_TG_W / 2", "T_TG_W / 2")], None, "MCC_LID_T")
    c = comps["heat_set_boss"]
    body("heat_set_boss", "Block_Boss_Body", [c.rect("-T_BOSS_PLATE / 2", "T_BOSS_PLATE / 2", "-T_BOSS_PLATE / 2", "T_BOSS_PLATE / 2")],
         None, "MCC_FLOOR_T")
    c = comps["lid_screw_hole"]
    body("lid_screw_hole", "Block_Lid_Body", [c.rect("-T_LID / 2", "T_LID / 2", "-T_LID / 2", "T_LID / 2")], None, "MCC_LID_T")
    c = comps["side_bolt"]
    body("side_bolt", "Block_SideBolt_Body", [c.rect("-T_SB_W / 2", "T_SB_W / 2", None, "MCC_WALL")], None, "T_SB_H")
    c.extrude("Block_SideBolt_FloorAdd", axis="Z", loops=[c.rect("-T_SB_W / 2", "T_SB_W / 2", None, "MCC_WALL + MCC_GAP_FAR")],
              start=None, end="MCC_FLOOR_T", op="join")
    c = comps["d_wall_cut"]
    body("d_wall_cut", "Block_DWall_Body", [c.rect("-T_D_W / 2", "T_D_W / 2", "-(MCC_PANEL_SEAT_T + MCC_WALL)", None)], None, "T_D_H")
    c = comps["rail_male"]
    body("rail_male", "Block_RailMale_Body", [c.rect("-T_RAIL_LEN / 2", "T_RAIL_LEN / 2", "-T_RAIL_PLATE_W / 2", "T_RAIL_PLATE_W / 2")],
         "-T_RAIL_PLATE_T", None)
    c = comps["rail_female"]
    body("rail_female", "Block_RailFemale_Body",
         [c.rect("-T_RAIL_LEN / 2 - MCC_RAIL_END_WALL", "T_RAIL_LEN / 2 + MCC_WALL", f"-({SW})", SW)], None, "MCC_RAIL_SILL_H")


def _block_modules() -> list:
    found = []
    for name in BLOCK_MODULES:
        qualified = f"{__package__}.{name}"
        if importlib.util.find_spec(qualified) is not None:
            found.append(importlib.import_module(qualified))
    return found


def build(ctx):
    """The entry of the document plan: build the bodies, then every block module's ``add``, then its ``cut``."""
    kit = Kit(ctx)
    comps = {block: kit.component(name, role="part", datum=datum) for block, (name, datum) in COMPONENTS.items()}
    _bodies(comps)
    modules = _block_modules()
    for module in modules:
        module.add(comps)
    for module in modules:
        module.cut(comps)
    return kit.inventory()
