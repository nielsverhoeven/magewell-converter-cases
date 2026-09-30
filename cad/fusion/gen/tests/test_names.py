"""Names and sets of the modelling kit (plan 3.5): every row of the suffix table, the grammar, the reserved
enhancement suffixes and the frozen anchors.

The relative imports are deliberate: cad/tests/test_layers.py forbids an absolute ``cad.fusion`` import in any
file under cad/ until the layering test of milestone K3 replaces that rule.
"""
from __future__ import annotations

import unittest

from ..core import names

OWNERS = ("Shell", "Cradle", "Patch", "Fastener", "Fan", "Label", "Vent", "Rail", "SideBolt")


class ParseTests(unittest.TestCase):
    def test_three_tokens(self):
        self.assertEqual(names.parse("Shell_Floor_Body"), ("Shell", "Floor", "Body"))
        self.assertEqual(names.parse("Patch_Slot4_SeatCut"), ("Patch", "Slot4", "SeatCut"))

    def test_wrong_grammar_is_refused(self):
        for bad in ("Shell_Floor", "Shell_Floor_Body_Extra", "shell_Floor_Body", "Shell_floor_Body", "Shell__Body",
                    "Shell_Floor_", "_Floor_Body", "Shell-Floor_Body", "Shell_4Floor_Body", "", "Shell_Fl oor_Body"):
            with self.subTest(bad):
                with self.assertRaises(names.KitNameError):
                    names.parse(bad)

    def test_a_non_string_is_refused(self):
        with self.assertRaises(names.KitNameError):
            names.parse(3)

    def test_set_of_is_the_first_two_tokens(self):
        self.assertEqual(names.set_of("Vent_FarLoA_SlotPat"), "Vent_FarLoA")
        self.assertEqual(names.set_of("Fastener_PatchMid_BossAdd"), "Fastener_PatchMid")

    def test_kit_name_error_is_a_kit_error(self):
        self.assertTrue(issubclass(names.KitNameError, names.KitError))


class SuffixTableTests(unittest.TestCase):
    """One row of the table of 3.5 each."""

    ROWS = (
        ("new", "Shell_Floor_Body"),
        ("join", "Cradle_Deck_FrameAdd"),
        ("cut", "Patch_Slot4_SeatCut"),
        ("rejoin", "Fan_Aperture_Ring1Rejoin"),
        ("pattern", "Vent_FarLoA_SlotPat"),
        ("text_cut", "Label_Size_TextCut"),
        ("text_join", "Label_Size_TextAdd"),
    )

    def test_the_table(self):
        self.assertEqual(names.SUFFIX, {"new": "Body", "join": "Add", "cut": "Cut", "rejoin": "Rejoin", "pattern": "Pat",
                                        "text_cut": "TextCut", "text_join": "TextAdd"})

    def test_every_row_passes(self):
        for kind, name in self.ROWS:
            with self.subTest(kind):
                self.assertEqual(names.check(name, OWNERS, kind), names.parse(name))

    def test_every_row_fails_under_every_other_kind(self):
        for kind, name in self.ROWS:
            for other, _ in self.ROWS:
                if other == kind:
                    continue
                with self.subTest(f"{name} as {other}"):
                    with self.assertRaises(names.KitNameError):
                        names.check(name, OWNERS, other)

    def test_a_text_name_is_not_a_plain_cut_or_join(self):
        with self.assertRaises(names.KitNameError):
            names.check("Label_Size_TextCut", OWNERS, "cut")
        with self.assertRaises(names.KitNameError):
            names.check("Label_Size_TextAdd", OWNERS, "join")

    def test_unknown_owner(self):
        with self.assertRaises(names.KitNameError) as ctx:
            names.check("Gizmo_Floor_Body", OWNERS, "new")
        self.assertIn("Gizmo", str(ctx.exception))

    def test_unknown_kind(self):
        with self.assertRaises(names.KitNameError):
            names.check("Shell_Floor_Body", OWNERS, "extrude")

    def test_kind_none_checks_grammar_and_owner_only(self):
        self.assertEqual(names.check("Shell_Floor_BodySk", OWNERS, None), ("Shell", "Floor", "BodySk"))
        with self.assertRaises(names.KitNameError):
            names.check("Gizmo_Floor_BodySk", OWNERS, None)


class ReservedSuffixTests(unittest.TestCase):
    """Verdict A9: Thread, Fillet and Chamfer are reserved; #81 creates none."""

    def test_the_reserved_suffixes(self):
        self.assertEqual(names.RESERVED_SUFFIX, ("Thread", "Fillet", "Chamfer"))

    def test_the_enhancement_names_are_reserved(self):
        self.assertEqual(names.ENHANCE_NAMES, ("after", "side_faces", "faces", "edges", "require_thread", "thread",
                                               "rule_fillet", "chamfer"))

    def test_refused_for_the_build_phase_under_every_kind(self):
        for suffix in names.RESERVED_SUFFIX:
            name = f"Fastener_Mid_Screw{suffix}"
            for kind in list(names.SUFFIX) + [s.lower() for s in names.RESERVED_SUFFIX]:
                with self.subTest(f"{name} {kind}"):
                    with self.assertRaises(names.KitNameError):
                        names.check(name, OWNERS, kind, phase="build")

    def test_accepted_for_the_enhance_phase(self):
        self.assertEqual(names.check("Fastener_Mid_ScrewThread", OWNERS, "thread", phase="enhance")[2], "ScrewThread")
        self.assertEqual(names.check("Shell_Walls_EdgeFillet", OWNERS, "fillet", phase="enhance")[2], "EdgeFillet")
        self.assertEqual(names.check("Shell_Walls_LipChamfer", OWNERS, "chamfer", phase="enhance")[2], "LipChamfer")

    def test_the_enhance_phase_still_matches_the_suffix_to_the_kind(self):
        with self.assertRaises(names.KitNameError):
            names.check("Shell_Walls_EdgeFillet", OWNERS, "chamfer", phase="enhance")

    def test_the_enhance_phase_takes_no_build_kind(self):
        with self.assertRaises(names.KitNameError):
            names.check("Shell_Floor_Body", OWNERS, "new", phase="enhance")

    def test_unknown_phase(self):
        with self.assertRaises(names.KitNameError):
            names.check("Shell_Floor_Body", OWNERS, "new", phase="later")


class DerivedTests(unittest.TestCase):
    def test_the_five_tags(self):
        for tag in ("Sk", "SkA", "SkB", "PlA", "PlB"):
            with self.subTest(tag):
                out = names.derived("Cradle_Deck_FrameAdd", tag)
                self.assertEqual(out, "Cradle_Deck_FrameAdd" + tag)
                self.assertEqual(names.set_of(out), "Cradle_Deck")
                self.assertEqual(len(names.parse(out)), 3)

    def test_an_unknown_tag_is_refused(self):
        with self.assertRaises(names.KitNameError):
            names.derived("Cradle_Deck_FrameAdd", "Sketch")


class ComponentTests(unittest.TestCase):
    def test_valid(self):
        for ok in ("Base", "Lid", "Reserve_FanBay", "Ghost_Device"):
            with self.subTest(ok):
                self.assertEqual(names.component_check(ok), ok)

    def test_invalid(self):
        for bad in ("base", "Reserve_fanBay", "A_B_C", "Reserve_", "_Base", "Base Lid", "", "Fan-Bay"):
            with self.subTest(bad):
                with self.assertRaises(names.KitNameError):
                    names.component_check(bad)


class AnchorTests(unittest.TestCase):
    def matches(self, name: str) -> bool:
        return any(rx.fullmatch(name) for rx in names.ANCHORS)

    def test_the_frozen_anchors(self):
        for name in ("Shell_Floor_Body", "Shell_Walls_Add", "Shell_Lid_Body", "Fastener_PatchMid_BossAdd",
                     "Fastener_LidCorner_WebAdd", "Patch_Slot4_BoreCut"):
            with self.subTest(name):
                self.assertTrue(self.matches(name))

    def test_other_names_are_not_anchors(self):
        for name in ("Shell_Floor_Add", "Shell_Wall_Add", "Fastener_PatchMid_BoreCut", "Patch_Slot4_SeatCut",
                     "Patch_Slot4_BoreCutX", "Fastener__BossAdd", "Cradle_Deck_FrameAdd"):
            with self.subTest(name):
                self.assertFalse(self.matches(name))

    def test_every_anchor_is_a_valid_build_name(self):
        for name, kind in (("Shell_Floor_Body", "new"), ("Shell_Walls_Add", "join"), ("Shell_Lid_Body", "new"),
                           ("Fastener_PatchMid_BossAdd", "join"), ("Fastener_PatchMid_WebAdd", "join"),
                           ("Patch_Slot4_BoreCut", "cut")):
            with self.subTest(name):
                names.check(name, OWNERS, kind)


if __name__ == "__main__":
    unittest.main()
