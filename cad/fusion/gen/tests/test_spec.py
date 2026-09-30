"""Specs of the modelling kit (plan 3.9, K1 step 4): fields, the phase default, to_json.

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import dataclasses
import json
import unittest

from ..core import spec
from ..core.names import KitError

ALL = (spec.Loop, spec.Dim, spec.Constraint, spec.SketchSpec, spec.PlaneSpec, spec.ExtrudeSpec, spec.LoftSpec,
       spec.PatternSpec, spec.TextSpec, spec.ComponentSpec, spec.SharedCall)


class FieldTests(unittest.TestCase):
    def test_the_field_lists_of_the_plan(self):
        want = {
            spec.Loop: ("kind", "args"),
            spec.Dim: ("kind", "a", "b", "axis", "text"),
            spec.Constraint: ("kind", "a", "b"),
            spec.SketchSpec: ("name", "component", "on", "datum", "loops", "holes", "points", "lines", "circles",
                              "constraints", "dims", "profiles", "rule", "texts"),
            spec.PlaneSpec: ("name", "component", "base", "offset"),
            spec.ExtrudeSpec: ("name", "component", "sketch", "start_offset", "distance", "direction", "op", "within"),
            spec.LoftSpec: ("name", "component", "sketches", "planes", "op"),
            spec.PatternSpec: ("name", "component", "seed", "axis", "count", "pitch", "axis2", "count2", "pitch2"),
            spec.TextSpec: ("name", "component", "sketch", "frame", "string", "height", "halign", "valign", "font",
                            "style", "start_offset", "distance", "direction", "op"),
            spec.ComponentSpec: ("name", "role", "datum"),
            spec.SharedCall: ("builder_id", "arguments", "placement", "produced", "parent"),
        }
        for cls in ALL:
            with self.subTest(cls.__name__):
                self.assertEqual(tuple(f.name for f in dataclasses.fields(cls)), want[cls] + ("phase",))

    def test_every_spec_is_frozen_and_has_the_phase_default(self):
        for cls in ALL:
            with self.subTest(cls.__name__):
                phase = next(f for f in dataclasses.fields(cls) if f.name == "phase")
                self.assertEqual(phase.default, "build")
                self.assertTrue(cls.__dataclass_params__.frozen)
                self.assertTrue(callable(cls.to_json))


def sample() -> spec.ExtrudeSpec:
    return spec.ExtrudeSpec(name="Shell_Floor_Body", component="Base", sketch="Shell_Floor_BodySk", start_offset=None,
                            distance="V_CASE_H - MCC_WALL", direction="positive", op="new")


class ToJsonTests(unittest.TestCase):
    def test_extrude(self):
        self.assertEqual(sample().to_json(), {
            "name": "Shell_Floor_Body", "component": "Base", "sketch": "Shell_Floor_BodySk", "start_offset": None,
            "distance": "V_CASE_H - MCC_WALL", "direction": "positive", "op": "new", "within": None, "phase": "build"})

    def test_nested_specs_and_tuples_become_plain_lists_and_dicts(self):
        loop = spec.Loop("polygon", (("V_A", "V_B"), ("V_C", "V_B"), ("V_C", "V_D")))
        text = spec.TextSpec(name="Label_Size_TextCut", component="Lid", sketch="Label_Size_TextCutSk",
                             frame=spec.Loop("rect", ("V_A", "V_B", "V_C", "V_D")), string="ND", height="V_H",
                             halign="left", valign="middle", font="Arial", style="bold", start_offset="V_A",
                             distance="V_B", direction="negative", op="cut")
        doc = {"loop": loop.to_json(), "text": text.to_json()}
        self.assertEqual(doc["loop"]["args"], [["V_A", "V_B"], ["V_C", "V_B"], ["V_C", "V_D"]])
        self.assertEqual(doc["text"]["frame"], {"kind": "rect", "args": ["V_A", "V_B", "V_C", "V_D"], "phase": "build"})
        self.assertEqual(json.loads(json.dumps(doc)), doc)

    def test_shared_call(self):
        call = spec.SharedCall("rail.female_cut", {"x_mid": "V_X", "lead_in": True}, ("x_mid",))
        self.assertEqual(call.to_json(), {"builder_id": "rail.female_cut", "arguments": {"x_mid": "V_X", "lead_in": True},
                                          "placement": ["x_mid"], "produced": [], "parent": None, "phase": "build"})
        call.produced.append("Rail_Groove_GrooveCut")
        self.assertEqual(call.to_json()["produced"], ["Rail_Groove_GrooveCut"])

    def test_two_shared_calls_do_not_share_the_produced_list(self):
        a, b = spec.SharedCall("tg.tongue", {}, ()), spec.SharedCall("tg.groove", {}, ())
        a.produced.append("X")
        self.assertEqual(b.produced, [])


class PhaseTests(unittest.TestCase):
    def test_enhance_is_reserved_and_accepted(self):
        out = spec.ExtrudeSpec(name="A_B_C", component="C", sketch="s", start_offset=None, distance="V_A", direction="positive",
                               op="cut", phase="enhance")
        self.assertEqual(out.to_json()["phase"], "enhance")

    def test_any_other_phase_is_refused(self):
        with self.assertRaises(KitError):
            spec.Loop("rect", ("a", "b", "c", "d"), phase="later")

    def test_frozen(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            sample().name = "Other_Floor_Body"


if __name__ == "__main__":
    unittest.main()
