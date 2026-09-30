"""The facade, part two (plan 3.3, 3.7, 3.9, 3.14, K2b step 2): loft, pattern and text on the recording backend.

The context is a ``types.SimpleNamespace`` and the registry a list of literal rows.  Numbers under the build values:
V_X = 10, V_H = 20, V_D = 8, V_L = 100, V_W = 60, MCC_WALL = 3, V_N_DECK = 4, V_N_ROWS = 2, V_N_ZERO = 0, V_N_FRAC = 2.5.

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from ..core import expr, facade
from ..core.facade import Kit, PhaseError
from ..core.names import KitError, KitNameError
from ..core.spec import LoftSpec, PatternSpec, PlaneSpec, SketchSpec, TextSpec


def row(name, unit, kind, expression=None, fusion=None):
    return {"name": name, "unit": unit, "kind": kind, "expression": expression, "fusion": fusion,
            "comment": "", "description": "test row", "src": "test", "conf": None}


MM = {"V_X": 10.0, "V_H": 20.0, "V_D": 8.0, "V_L": 100.0, "V_W": 60.0}
COUNTS = {"V_N_DECK": 4, "V_N_ROWS": 2, "V_N_ZERO": 0, "V_N_FRAC": 2.5}
VALUES = {**MM, **COUNTS}
REGISTRY = ([row("MCC_WALL", "mm", "constant", "3 mm", "3 mm")] + [row(n, "mm", "solver") for n in MM]
            + [row(n, "none", "solver") for n in COUNTS])


def make_kit() -> Kit:
    return Kit(SimpleNamespace(backend="recording", design=None, document="Doc", registry=REGISTRY, values=VALUES,
                               options={}, log=print))


def part(kit: Kit):
    """A part with its body, ready for joins, cuts and text."""
    c = kit.component("Base", role="part", datum=(None, None, None))
    c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="new")
    return c


def slot(c, name="Vent_Slot_SlotCut"):
    """A cut that a pattern can repeat."""
    return c.extrude(name, axis="Z", loops=[c.rect("MCC_WALL", "V_X", "V_X", "V_H")], start=None, end="V_D", op="cut")


def of(kit, cls):
    return [s for s in kit._backend.timeline if isinstance(s, cls)]


def dims(sketch):
    return [(d.kind, d.a, d.b, d.axis, d.text) for d in sketch.dims]


class LoftTests(unittest.TestCase):
    def loft(self, c, **over):
        args = dict(axis="Z", loop_a=c.rect("V_X", "V_L", "MCC_WALL", "V_W"), at_a="V_D",
                    loop_b=c.rect("V_X", "V_L", "MCC_WALL", "V_W"), at_b="V_H", op="join")
        args.update(over)
        return c.loft("Cone_Top_TaperAdd", **args)

    def test_a_loft_yields_two_planes_two_sketches_and_one_feature_in_that_order(self):
        kit = make_kit()
        c = part(kit)
        before = len(kit._backend.timeline)
        self.assertEqual(self.loft(c), "Cone_Top_TaperAdd")
        added = kit._backend.timeline[before:]
        self.assertEqual([type(s) for s in added], [PlaneSpec, PlaneSpec, SketchSpec, SketchSpec, LoftSpec])
        self.assertEqual([s.name for s in added], ["Cone_Top_TaperAddPlA", "Cone_Top_TaperAddPlB", "Cone_Top_TaperAddSkA",
                                                   "Cone_Top_TaperAddSkB", "Cone_Top_TaperAdd"])
        pa, pb, ska, skb, feature = added
        self.assertEqual((pa.base, pa.offset, pb.base, pb.offset), ("origin:XY", "V_D", "origin:XY", "V_H"))
        self.assertEqual((ska.on, skb.on), ("plane:Cone_Top_TaperAddPlA", "plane:Cone_Top_TaperAddPlB"))
        self.assertEqual(dims(ska), dims(skb))  # the same loop is drawn the same way on both planes
        self.assertEqual((ska.profiles, ska.rule, ska.texts), (1, "all", ()))
        self.assertEqual(feature.sketches, ("Cone_Top_TaperAddSkA", "Cone_Top_TaperAddSkB"))
        self.assertEqual(feature.planes, ("Cone_Top_TaperAddPlA", "Cone_Top_TaperAddPlB"))
        self.assertEqual(feature.op, "join")

    def test_its_inventory_rows(self):
        kit = make_kit()
        c = part(kit)
        self.loft(c)
        items = kit.inventory()["items"][-5:]
        self.assertEqual(items[0], {"kind": "plane", "name": "Cone_Top_TaperAddPlA", "component": "Base",
                                    "on": "origin:XY", "expressions": ["V_D"]})
        self.assertEqual(items[1]["expressions"], ["V_H"])
        self.assertEqual((items[2]["kind"], items[2]["on"]), ("sketch", "plane:Cone_Top_TaperAddPlA"))
        self.assertEqual(items[2]["expressions"], ["V_X", "MCC_WALL", "V_L - V_X", "V_W - MCC_WALL"])
        self.assertEqual(items[4], {"kind": "feature", "name": "Cone_Top_TaperAdd", "component": "Base",
                                    "type": "LoftFeature", "expressions": []})
        json.dumps(kit.inventory())

    def test_the_build_record_carries_the_loft_specs(self):
        kit = make_kit()
        c = part(kit)
        self.loft(c)
        record = kit._backend.build_record()
        self.assertEqual([s["spec"] for s in record["specs"]][-5:],
                         ["PlaneSpec", "PlaneSpec", "SketchSpec", "SketchSpec", "LoftSpec"])
        json.dumps(record)

    def test_an_at_of_none_uses_the_origin_plane_and_creates_no_plane(self):
        kit = make_kit()
        c = part(kit)
        self.loft(c, at_a=None)
        planes = of(kit, PlaneSpec)
        self.assertEqual([p.name for p in planes], ["Cone_Top_TaperAddPlB"])
        self.assertEqual([s.on for s in of(kit, SketchSpec)][1:], ["origin:XY", "plane:Cone_Top_TaperAddPlB"])

    def test_a_negative_plane_normal_negates_the_offset(self):
        kit = make_kit()
        c = part(kit)
        with mock.patch.dict(facade.PLANE_NORMAL, {"XY": -1}):
            self.loft(c)
        self.assertEqual([p.offset for p in of(kit, PlaneSpec)], ["-(V_D)", "-(V_H)"])

    def test_two_circles_and_a_body_loft(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.loft("Cone_Top_TaperBody", axis="Z", loop_a=c.circle("V_X", "V_H", "V_D"), at_a=None,
               loop_b=c.circle("V_X", "V_H", "MCC_WALL"), at_b="V_H", op="new")
        self.assertEqual([type(s).__name__ for s in kit._backend.timeline],
                         ["ComponentSpec", "PlaneSpec", "SketchSpec", "SketchSpec", "LoftSpec"])

    def test_a_loft_refuses_what_the_plan_refuses(self):
        kit = make_kit()
        c = part(kit)
        rect = c.rect("V_X", "V_L", "MCC_WALL", "V_W")
        with self.assertRaises(KitError):  # sections of another kind
            self.loft(c, loop_b=c.circle("V_X", "V_H", "V_D"))
        with self.assertRaises(KitError):  # polygons with another vertex count
            self.loft(c, loop_a=c.polygon([("V_X", "V_H"), ("V_L", "V_H"), ("V_L", "V_W")]),
                      loop_b=c.polygon([("V_X", "V_H"), ("V_L", "V_H"), ("V_L", "V_W"), ("V_X", "V_W")]))
        with self.assertRaises(KitError):  # the same plane twice, as text
            self.loft(c, at_b="V_D")
        with self.assertRaises(KitError):  # and under the values
            self.loft(c, at_a="V_X * 2", at_b="V_H")
        with self.assertRaises(KitError):  # both on the origin plane
            self.loft(c, at_a=None, at_b=None)
        with self.assertRaises(KitError):  # a loft has no within, so no re-join
            self.loft(c, op="rejoin")
        with self.assertRaises(KitError):  # a number is no loop
            self.loft(c, loop_a=3)
        with self.assertRaises(TypeError):  # a number is no expression
            self.loft(c, at_a=5)
        with self.assertRaises(KitError):
            self.loft(c, axis="W")
        with self.assertRaises(KitNameError):  # the suffix must match the operation
            c.loft("Cone_Top_TaperCut", axis="Z", loop_a=rect, at_a="V_D", loop_b=rect, at_b="V_H", op="join")
        self.assertEqual(len(of(kit, LoftSpec)), 0)  # nothing was recorded by a refused call

    def test_a_loft_obeys_the_phase_rule(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        with self.assertRaises(PhaseError):
            self.loft(c)  # a join after a cut
        c.loft("Cone_Top_TaperCut", axis="Z", loop_a=c.rect("V_X", "V_L", "MCC_WALL", "V_W"), at_a="V_D",
               loop_b=c.rect("V_X", "V_L", "MCC_WALL", "V_W"), at_b="V_H", op="cut")


class PatternTests(unittest.TestCase):
    def test_a_pattern_of_a_cut(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        before = len(kit._backend.timeline)
        self.assertEqual(c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D"),
                         "Vent_Slot_SlotPat")
        (spec,) = kit._backend.timeline[before:]
        self.assertEqual(spec, PatternSpec(name="Vent_Slot_SlotPat", component="Base", seed="Vent_Slot_SlotCut", axis="X",
                                           count="V_N_DECK", pitch="V_D"))
        self.assertEqual(kit.inventory()["items"][-1],
                         {"kind": "feature", "name": "Vent_Slot_SlotPat", "component": "Base",
                          "type": "RectangularPatternFeature", "expressions": ["V_N_DECK", "V_D"]})
        record = kit._backend.build_record()
        self.assertEqual(record["specs"][-1]["spec"], "PatternSpec")
        self.assertEqual(record["specs"][-1]["axis2"], None)

    def test_a_grid(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D",
                  axis2="Y", count2="V_N_ROWS", pitch2="V_H * 2")
        self.assertEqual(kit.inventory()["items"][-1]["expressions"], ["V_N_DECK", "V_D", "V_N_ROWS", "V_H * 2"])
        self.assertEqual((of(kit, PatternSpec)[0].axis2, of(kit, PatternSpec)[0].count2), ("Y", "V_N_ROWS"))

    def test_a_pattern_of_a_loft_join(self):
        kit = make_kit()
        c = part(kit)
        c.loft("Cone_Top_TaperAdd", axis="Z", loop_a=c.circle("V_X", "V_H", "V_D"), at_a="V_D",
               loop_b=c.circle("V_X", "V_H", "MCC_WALL"), at_b="V_H", op="join")
        c.pattern("Cone_Top_TaperPat", seed="Cone_Top_TaperAdd", axis="Y", count="V_N_ROWS", pitch="V_W")
        self.assertEqual(len(of(kit, PatternSpec)), 1)

    def test_the_count_is_the_bare_name_of_a_V_N_parameter(self):
        kit = make_kit()
        c = part(kit)
        slot(c)

        def pattern(count, **over):
            args = dict(seed="Vent_Slot_SlotCut", axis="X", count=count, pitch="V_D")
            args.update(over)
            return c.pattern("Vent_Slot_SlotPat", **args)

        with self.assertRaises(TypeError):
            pattern(4)  # a number
        with self.assertRaises(KitError):
            pattern("V_N_DECK + 1")  # an expression
        with self.assertRaises(KitError):
            pattern("4")  # a number as text
        with self.assertRaises(KitError):
            pattern("V_L")  # a name without the V_N_ prefix
        with self.assertRaises(expr.UnknownNameError):
            pattern("V_N_NOPE")  # a V_N_ name the registry lacks
        with self.assertRaises(KitError):
            pattern("V_N_ZERO")  # a count of at least 1 under the build values
        with self.assertRaises(KitError):
            pattern("V_N_FRAC")  # and a whole number
        with self.assertRaises(KitError):
            pattern("V_N_DECK", axis2="Y", count2="V_N_DECK + 1", pitch2="V_D")  # the second count is held to the same rule
        self.assertEqual(of(kit, PatternSpec), [])

    def test_the_pitch_is_an_expression_that_is_positive(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        for pitch, error in ((8, TypeError), ("8", expr.LiteralError), ("V_X - V_L", KitError), ("V_Q", expr.UnknownNameError)):
            with self.assertRaises(error, msg=repr(pitch)):
                c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch=pitch)

    def test_a_seed_from_another_set_or_another_component_or_of_another_kind_is_refused(self):
        kit = make_kit()
        c = part(kit)
        slot(c, "Vent_Slot_SlotCut")
        slot_b = c.extrude("Vent_Hole_HoleCut", axis="Z", loops=[c.circle("V_X", "V_H", "V_D")], start=None, end="V_D", op="cut")
        with self.assertRaises(KitError) as caught:
            c.pattern("Vent_Slot_SlotPat", seed=slot_b, axis="X", count="V_N_DECK", pitch="V_D")
        self.assertIn("share a set", str(caught.exception))
        with self.assertRaises(KitError):  # a seed that does not exist
            c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_NopeCut", axis="X", count="V_N_DECK", pitch="V_D")
        other = kit.component("Lid", role="part", datum=(None, None, None))
        with self.assertRaises(KitError):  # a seed of another component
            other.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        with self.assertRaises(KitError):  # a pattern is no seed
            c.pattern("Vent_Slot_RepeatPat", seed="Vent_Slot_SlotPat", axis="X", count="V_N_DECK", pitch="V_D")
        with self.assertRaises(KitError):  # the body is no seed
            c.pattern("Shell_Floor_BodyPat", seed="Shell_Floor_Body", axis="X", count="V_N_DECK", pitch="V_D")

    def test_the_axes_come_together(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        base = dict(seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        with self.assertRaises(KitError):
            c.pattern("Vent_Slot_SlotPat", axis2="Y", **base)  # axis2 without count2 and pitch2
        with self.assertRaises(KitError):
            c.pattern("Vent_Slot_SlotPat", count2="V_N_ROWS", pitch2="V_D", **base)
        with self.assertRaises(KitError):
            c.pattern("Vent_Slot_SlotPat", axis2="X", count2="V_N_ROWS", pitch2="V_D", **base)  # the same axis twice
        with self.assertRaises(KitError):
            c.pattern("Vent_Slot_SlotPat", axis2="Q", count2="V_N_ROWS", pitch2="V_D", **base)

    def test_the_name_and_the_phase(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        with self.assertRaises(KitNameError):
            c.pattern("Vent_Slot_SlotCut2", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        with self.assertRaises(KitNameError):
            c.pattern("Vent_Slot_Slot", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        # a join can be patterned until a cut has been made; afterwards the pattern would go back in the order
        kit = make_kit()
        c = part(kit)
        c.extrude("Deck_Rib_RibAdd", axis="Z", loops=[c.rect("MCC_WALL", "V_X", "V_X", "V_H")], start=None, end="V_D", op="join")
        slot(c)
        with self.assertRaises(PhaseError):
            c.pattern("Deck_Rib_RibPat", seed="Deck_Rib_RibAdd", axis="X", count="V_N_DECK", pitch="V_D")

    def test_a_name_is_used_once_and_a_pattern_belongs_to_the_shared_call_it_was_made_in(self):
        kit = make_kit()
        c = part(kit)
        slot(c)
        with c.shared_call("vents.row", {"n": "V_N_DECK"}, ()) as call:
            c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        self.assertEqual(call.produced, ["Vent_Slot_SlotPat"])
        with self.assertRaises(facade.DuplicateNameError):
            c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")


class TextTests(unittest.TestCase):
    def text(self, c, name="Label_Size_TextCut", **over):
        args = dict(axis="Z", frame=c.rect("V_X", "V_L", "V_X", "V_W"), start="V_D", end="V_H", string="M3",
                    height="MCC_WALL", halign="center", valign="middle", font="Arial", style="bold", op="cut")
        args.update(over)
        return c.text(name, **args)

    def test_a_text_yields_a_sketch_with_texts_and_the_height_as_its_last_expression(self):
        kit = make_kit()
        c = part(kit)
        before = len(kit._backend.timeline)
        self.assertEqual(self.text(c), "Label_Size_TextCut")
        sketch, feature = kit._backend.timeline[before:]
        self.assertEqual([type(s) for s in (sketch, feature)], [SketchSpec, TextSpec])
        self.assertEqual(sketch.name, "Label_Size_TextCutSk")
        self.assertEqual(sketch.texts, ("M3",))
        self.assertEqual(dims(sketch), [("distance", "O", "p0_0", "u", "V_X"), ("distance", "O", "p0_0", "v", "V_X"),
                                        ("distance", "p0_0", "p0_1", "u", "V_L - V_X"),
                                        ("distance", "p0_1", "p0_2", "v", "V_W - V_X"),
                                        ("text_height", "t0", "", "", "MCC_WALL")])
        self.assertEqual((sketch.profiles, sketch.rule), (0, "text"))
        self.assertEqual((feature.sketch, feature.string, feature.height), ("Label_Size_TextCutSk", "M3", "MCC_WALL"))
        self.assertEqual((feature.halign, feature.valign, feature.font, feature.style), ("center", "middle", "Arial", "bold"))
        self.assertEqual((feature.start_offset, feature.distance, feature.direction, feature.op),
                         ("V_D", "V_H - V_D", "positive", "cut"))
        self.assertEqual(feature.frame.kind, "rect")

    def test_its_inventory_rows(self):
        kit = make_kit()
        c = part(kit)
        self.text(c)
        sketch_item, feature_item = kit.inventory()["items"][-2:]
        self.assertEqual(sketch_item, {"kind": "sketch", "name": "Label_Size_TextCutSk", "component": "Base",
                                       "on": "origin:XY", "texts": ["M3"],
                                       "expressions": ["V_X", "V_X", "V_L - V_X", "V_W - V_X", "MCC_WALL"]})
        self.assertEqual(feature_item, {"kind": "feature", "name": "Label_Size_TextCut", "component": "Base",
                                        "type": "ExtrudeFeature", "expressions": ["V_D", "V_H - V_D"]})
        record = kit._backend.build_record()
        self.assertEqual([s["spec"] for s in record["specs"]][-2:], ["SketchSpec", "TextSpec"])
        self.assertEqual(record["specs"][-1]["frame"]["kind"], "rect")
        json.dumps(record)

    def test_a_join_ends_with_TextAdd_and_a_none_start_has_no_offset(self):
        kit = make_kit()
        c = part(kit)
        self.text(c, "Label_Size_TextAdd", start=None, end="V_D", op="join")
        self.assertEqual(kit.inventory()["items"][-1]["expressions"], ["V_D"])
        with mock.patch.dict(facade.PLANE_NORMAL, {"XY": -1}):
            self.text(c, "Label_Other_TextCut")
        self.assertEqual((of(kit, TextSpec)[1].start_offset, of(kit, TextSpec)[1].direction), ("-(V_D)", "negative"))

    def test_a_string_with_a_single_quote_or_a_line_break_is_refused(self):
        kit = make_kit()
        c = part(kit)
        for bad in ("it's", "a\nb", "a\rb", ""):
            with self.assertRaises(KitError, msg=repr(bad)):
                self.text(c, string=bad)
        with self.assertRaises(KitError):
            self.text(c, string=3)
        self.assertEqual(of(kit, TextSpec), [])

    def test_a_name_must_end_with_TextCut_or_TextAdd(self):
        kit = make_kit()
        c = part(kit)
        for bad in ("Label_Size_Cut", "Label_Size_Text", "Label_Size_TextAdd", "Label_Size_Label"):
            with self.assertRaises(KitNameError, msg=bad):
                self.text(c, bad)  # the op is a cut: only TextCut fits
        with self.assertRaises(KitNameError):
            self.text(c, "Label_Size_TextCut", op="join")
        # and an extrude may not take the text suffixes
        with self.assertRaises(KitNameError):
            c.extrude("Label_Size_TextCut", axis="Z", loops=[c.rect("V_X", "V_L", "V_X", "V_W")], start=None, end="V_D", op="cut")

    def test_the_options_are_checked(self):
        kit = make_kit()
        c = part(kit)
        for over in (dict(halign="middle"), dict(valign="center"), dict(style="italic"), dict(font=""), dict(op="new"),
                     dict(op="rejoin"), dict(axis="Q"), dict(frame=c.circle("V_X", "V_H", "V_D")), dict(frame=3),
                     dict(start=None, end=None)):
            with self.assertRaises(KitError, msg=repr(over)):
                self.text(c, **over)
        with self.assertRaises(TypeError):
            self.text(c, height=3)  # a number is no expression
        with self.assertRaises(expr.LiteralError):
            self.text(c, height="3")
        with self.assertRaises(KitError):  # a height that is not positive under the values
            self.text(c, height="V_X - V_L")

    def test_a_text_obeys_the_phase_rule(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        with self.assertRaises(PhaseError):
            self.text(c)  # there is no body yet
        self.text(part(make_kit()), "Label_Size_TextCut")  # with a body it works
        c = part(make_kit())
        self.text(c, "Label_Size_TextCut")
        with self.assertRaises(PhaseError):
            self.text(c, "Label_Size_TextAdd", op="join")  # a join after a cut
        reserve = kit.component("Reserve_Bay", role="reserve", datum=(None, None, None))
        with self.assertRaises(PhaseError):
            self.text(reserve)


if __name__ == "__main__":
    unittest.main()
