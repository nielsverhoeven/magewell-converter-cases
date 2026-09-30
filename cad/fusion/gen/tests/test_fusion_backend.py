"""The Fusion backend (plan 3.11, 3.14, K5a): the translation of a spec into adsk calls, run against the fake of
``fake_adsk.py``.  Nothing here runs Fusion, and no test skips.

The context is a ``types.SimpleNamespace`` and the registry a list of literal rows.  Numbers under the build values:
V_X = 10, V_H = 20, V_D = 8, V_L = 100, V_W = 60, MCC_WALL = 3, V_N_DECK = 4.  The fake lays the sketches out as
x, y on XY, x, z on XZ and y, z on YZ, so the sketch normal is +Z, -Y and +X; ``setUp`` sets ``facade.PLANE_NORMAL`` to
that.  Seeds are centimetres: V_X is 1.0, MCC_WALL 0.3.

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import dataclasses
import importlib
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ..core import expr, facade
from ..core.facade import Kit
from ..core.names import KitError
from ..core.spec import PlaneSpec
from . import fake_adsk
from .fake_adsk import ERROR, FeatureOperations as Ops, ExtentDirections as Dirs

PKG = __package__.rsplit(".", 1)[0]  # cad.fusion.gen
MODULE = f"{PKG}.core.fusion_backend"
REPO = Path(__file__).resolve().parents[4]
H, V = "DimensionOrientations.HorizontalDimensionOrientation", "DimensionOrientations.VerticalDimensionOrientation"


def row(name, unit, kind, expression=None, fusion=None):
    return {"name": name, "unit": unit, "kind": kind, "expression": expression, "fusion": fusion,
            "comment": "", "description": "test row", "src": "test", "conf": None}


MM = {"V_X": 10.0, "V_H": 20.0, "V_D": 8.0, "V_L": 100.0, "V_W": 60.0}
COUNTS = {"V_N_DECK": 4}
VALUES = {**MM, **COUNTS}
REGISTRY = ([row("MCC_WALL", "mm", "constant", "3 mm", "3 mm")] + [row(n, "mm", "solver") for n in MM]
            + [row(n, "none", "solver") for n in COUNTS])


class FusionCase(unittest.TestCase):
    """A fake adsk in ``sys.modules``, the backend module imported against it, a fresh fake design."""

    def setUp(self):
        patch = mock.patch.dict(facade.PLANE_NORMAL, fake_adsk.NORMALS)
        patch.start()
        self.addCleanup(patch.stop)
        fakes = fake_adsk.installed(MODULE)
        fakes.__enter__()
        self.addCleanup(fakes.__exit__, None, None, None)
        self.module = importlib.import_module(MODULE)
        self.design = fake_adsk.Design()

    def kit(self, registry=REGISTRY, values=VALUES) -> Kit:
        return Kit(SimpleNamespace(backend="fusion", design=self.design, document="Doc", registry=registry, values=values,
                                   options={}, log=print))

    def part(self, kit=None):
        """A part with its floor body (an XY rectangle, 3 mm thick): ready for joins, cuts and text."""
        kit = kit or self.kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="MCC_WALL", op="new")
        return kit, c

    @property
    def comp(self):
        return self.design.components[0]

    def expressions(self, sketch_name):
        return [d.parameter.expression for d in self.design.sketch(sketch_name).dimensions]


class SketchTests(FusionCase):
    def test_a_rectangle_on_xy_is_built_in_the_order_of_3_6(self):
        kit, _ = self.part()
        sk = self.design.sketch("Shell_Floor_BodySk")
        self.assertEqual(self.design.log, [("addNewComponent",), ("sketches.add", "XY")] + [("addByTwoPoints", "Shell_Floor_BodySk")] * 4
                         + [("extrude.add", Ops.NewBodyFeatureOperation)])
        self.assertEqual(sk.deferred_history, [True, False])  # deferred only while creating
        self.assertEqual([(ln.startSketchPoint.at, ln.endSketchPoint.at) for ln in sk.lines],
                         [((1.0, 0.3), (10.0, 0.3)), ((10.0, 0.3), (10.0, 6.0)), ((10.0, 6.0), (1.0, 6.0)), ((1.0, 6.0), (1.0, 0.3))])
        self.assertEqual(len(sk.points), 4)  # the lines are chained through shared points; the last closes on the first
        self.assertEqual(sk.constraints, [("horizontal", (1.0, 0.3), (10.0, 0.3)), ("vertical", (10.0, 0.3), (10.0, 6.0)),
                                          ("horizontal", (10.0, 6.0), (1.0, 6.0)), ("vertical", (1.0, 6.0), (1.0, 0.3))])
        self.assertEqual([(d.orientation.rsplit(".", 1)[1], d.a, d.b) for d in sk.dimensions],
                         [("HorizontalDimensionOrientation", (0.0, 0.0), (1.0, 0.3)), ("VerticalDimensionOrientation", (0.0, 0.0), (1.0, 0.3)),
                          ("HorizontalDimensionOrientation", (1.0, 0.3), (10.0, 0.3)), ("VerticalDimensionOrientation", (10.0, 0.3), (10.0, 6.0))])
        self.assertEqual(self.expressions("Shell_Floor_BodySk"), ["V_X", "MCC_WALL", "V_L - V_X", "V_W - MCC_WALL"])

    def test_every_expression_goes_through_the_one_emitter(self):
        kit, c = self.part()
        c.extrude("Shell_Wall_SlotCut", axis="Z", loops=[c.rect("max(V_X, V_D)", "V_L", "V_X", "V_W")], start=None, end="V_H", op="cut")
        self.assertEqual(self.expressions("Shell_Wall_SlotCutSk")[0], expr.fusion("max(V_X, V_D)"))
        self.assertIn(";", self.expressions("Shell_Wall_SlotCutSk")[0])  # Fusion separates arguments with ;

    def test_the_sketch_axes_are_read_from_the_sketch_not_assumed(self):
        # a sketch on XZ whose x runs along Z and y along X: x cross y is +Y here
        self.design.frames["XZ"] = ((0, 0, 1), (1, 0, 0))
        facade.PLANE_NORMAL["XZ"] = 1
        kit, c = self.part()
        c.extrude("Shell_Side_Add", axis="Y", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="join")
        sk = self.design.sketch("Shell_Side_AddSk")
        # model (x=1.0, z=0.3) is sketch (0.3, 1.0); a line along model X is a vertical line of this sketch
        self.assertEqual(sk.lines[0].startSketchPoint.at, (0.3, 1.0))
        self.assertEqual(sk.constraints[0][0], "vertical")  # parallel_u: along model X
        self.assertEqual(sk.constraints[1][0], "horizontal")  # parallel_v: along model Z
        self.assertEqual([d.orientation.rsplit(".", 1)[1] for d in sk.dimensions],
                         ["VerticalDimensionOrientation", "HorizontalDimensionOrientation"] * 2)

    def test_a_datum_point_is_a_sketch_point_and_an_equal_coordinate_is_a_constraint(self):
        kit = self.kit()
        c = kit.component("Base", role="part", datum=("V_X", "MCC_WALL", None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "V_H", "V_W")], start=None, end="V_H", op="new")
        sk = self.design.sketch("Shell_Floor_BodySk")
        self.assertEqual(self.design.log.count(("sketchPoints.add", "Shell_Floor_BodySk")), 1)
        self.assertIn(("verticalPoints", (1.0, 0.3), (1.0, 2.0)), sk.constraints)  # same_u: u is the sketch's x
        self.assertEqual(self.expressions("Shell_Floor_BodySk")[:3], ["V_X", "MCC_WALL", "V_H - MCC_WALL"])
        self.assertEqual((sk.dimensions[0].a, sk.dimensions[0].b), ((0.0, 0.0), (1.0, 0.3)))  # O to P0

    def test_a_ring_extrudes_the_profile_with_two_loops_only(self):
        self.design.profile_loops["Fan_Ring_AddSk"] = [2, 1]  # the ring and the disc inside its hole
        kit, c = self.part()
        c.extrude("Fan_Ring_Add", axis="Z", loops=[c.rect("V_X", "V_L", "V_X", "V_W")],
                  holes=[c.circle("V_L / 2", "V_W / 2", "V_D")], start=None, end="V_H", op="join")
        sk = self.design.sketch("Fan_Ring_AddSk")
        self.assertEqual([(ci.centerSketchPoint.at, round(ci.radius, 9)) for ci in sk.circles], [((5.0, 3.0), 0.4)])
        diameter = [d for d in sk.dimensions if d.kind == "diameter"]
        self.assertEqual([d.parameter.expression for d in diameter], ["V_D"])
        profile = self.design.feature("Fan_Ring_Add").input.profile
        self.assertEqual(profile.profileLoops.count, 2)  # one Profile, not a collection

    def test_separate_loops_extrude_every_profile(self):
        kit, c = self.part()
        c.extrude("Shell_Two_Add", axis="Z", loops=[c.rect("V_X", "V_H", "V_X", "V_W"), c.rect("V_L", "V_L + V_X", "V_X", "V_W")],
                  start=None, end="V_H", op="join")
        collection = self.design.feature("Shell_Two_Add").input.profile
        self.assertEqual(len(collection.items), 2)


class ExtrudeTests(FusionCase):
    def test_a_new_body_in_a_part_carries_the_name_of_its_component(self):
        kit, _ = self.part()
        feature = self.design.feature("Shell_Floor_Body")
        self.assertEqual(feature.input.operation, Ops.NewBodyFeatureOperation)
        self.assertEqual(len(feature.input.profile.items), 1)
        self.assertIsNone(feature.input.startExtent)
        self.assertEqual((feature.input.extent[0], feature.input.extent[1].text), ("distance", "MCC_WALL"))
        self.assertEqual(feature.input.direction, Dirs.PositiveExtentDirection)
        self.assertEqual(self.comp.name, "Base")
        self.assertEqual(self.comp.bodies[0].name, "Base")
        self.assertIsNone(feature.input.participantBodies)

    def test_the_component_is_grounded_with_the_identity_transform(self):
        kit = self.kit()
        kit.component("Base", role="part", datum=(None, None, None))
        self.assertEqual(self.design.log, [("addNewComponent",)])
        self.assertEqual(self.comp.name, "Base")
        self.assertTrue(self.design.occurrences[0].isGroundToParent)

    def test_a_cut_names_its_body_and_a_start_offset_takes_the_sign_of_the_plane_normal(self):
        kit, c = self.part()
        # the normal of XZ is -Y in the fake: a start of V_X along plus Y is -V_X along the normal, and the direction is negative
        c.extrude("Shell_Wall_SlotCut", axis="Y", loops=[c.rect("V_X", "V_L", "V_X", "V_W")], start="V_X", end="V_H", op="cut")
        inp = self.design.feature("Shell_Wall_SlotCut").input
        self.assertEqual(inp.operation, Ops.CutFeatureOperation)
        self.assertEqual(inp.startExtent[0], "offset")
        self.assertEqual(inp.startExtent[1].text, expr.fusion("-(V_X)"))
        self.assertEqual((inp.extent[0], inp.extent[1].text), ("distance", "V_H - V_X"))
        self.assertEqual(inp.direction, Dirs.NegativeExtentDirection)
        self.assertEqual(inp.participantBodies, [self.comp.bodies[0]])
        self.assertEqual(len(self.comp.bodies), 1)

    def test_a_join_relies_on_the_one_body_and_sets_no_participants(self):
        kit, c = self.part()
        c.extrude("Shell_Wall_Add", axis="Z", loops=[c.rect("V_X", "V_H", "V_X", "V_W")], start=None, end="V_H", op="join")
        inp = self.design.feature("Shell_Wall_Add").input
        self.assertEqual(inp.operation, Ops.JoinFeatureOperation)
        self.assertIsNone(inp.participantBodies)

    def test_a_rejoin_is_a_join_with_the_body_as_participant(self):
        kit, c = self.part()
        c.extrude("Fan_Opening_Cut", axis="Z", loops=[c.rect("V_X", "V_H", "V_X", "V_W")], start=None, end="V_H", op="cut")
        c.extrude("Fan_Bars_Rejoin", axis="Z", loops=[c.rect("V_X", "V_L", "V_X", "V_W")], start=None, end="V_H", op="rejoin",
                  within="Fan_Opening_Cut")
        inp = self.design.feature("Fan_Bars_Rejoin").input
        self.assertEqual(inp.operation, Ops.JoinFeatureOperation)
        self.assertEqual(inp.participantBodies, [self.comp.bodies[0]])

    def test_a_reserve_component_names_each_body_after_its_feature(self):
        kit = self.kit()
        c = kit.component("Reserve_FanBay", role="reserve", datum=(None, None, None))
        c.extrude("Reserve_Fan_Body", axis="Z", loops=[c.rect("V_X", "V_L", "V_X", "V_W")], start=None, end="V_H", op="new")
        c.extrude("Reserve_Fan2_Body", axis="Z", loops=[c.rect("V_X", "V_L", "V_X", "V_W")], start="V_H", end="V_L", op="new")
        self.assertEqual([b.name for b in self.comp.bodies], ["Reserve_Fan_Body", "Reserve_Fan2_Body"])  # several bodies are allowed


class LoftPatternTextTests(FusionCase):
    def test_a_loft_makes_two_offset_planes_two_sketches_and_one_feature(self):
        kit, c = self.part()
        circle = lambda d: c.circle("V_L / 2", "V_W / 2", d)  # noqa: E731
        c.loft("Shell_Cone_TaperCut", axis="Z", loop_a=circle("V_H"), at_a="V_X", loop_b=circle("V_D"), at_b="V_H", op="cut")
        self.assertEqual([(p.origin_name, p.offset) for p in self.design.planes], [("XY", "V_X"), ("XY", "V_H")])
        self.assertEqual([p.name for p in self.design.planes], ["Shell_Cone_TaperCutPlA", "Shell_Cone_TaperCutPlB"])
        self.assertIn(("sketches.add", "XY+V_X"), self.design.log)
        self.assertIn(("sketches.add", "XY+V_H"), self.design.log)
        inp = self.design.feature("Shell_Cone_TaperCut").input
        self.assertEqual(inp.operation, Ops.CutFeatureOperation)
        self.assertEqual(len(inp.loftSections.items), 2)
        self.assertEqual(inp.participantBodies, [self.comp.bodies[0]])
        self.assertEqual([round(ci.radius, 9) for s in ("Shell_Cone_TaperCutSkA", "Shell_Cone_TaperCutSkB")
                          for ci in self.design.sketch(s).circles], [1.0, 0.4])

    def test_a_pattern_repeats_the_seed_along_an_origin_axis_with_bare_counts(self):
        kit, c = self.part()
        c.extrude("Vent_Slot_SlotCut", axis="Z", loops=[c.rect("V_X", "V_H", "V_D", "V_X")], start=None, end="V_H", op="cut")
        c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D",
                  axis2="Y", count2="V_N_DECK", pitch2="V_H * 2")
        inp = self.design.feature("Vent_Slot_SlotPat").input
        self.assertEqual(inp.entities.items, [self.design.feature("Vent_Slot_SlotCut")])
        self.assertEqual((inp.axis.axis, inp.count.text, inp.pitch.text), ("X", "V_N_DECK", "V_D"))
        self.assertEqual(inp.distance_type, fake_adsk.PatternDistanceType.SpacingPatternDistanceType)
        axis2, count2, pitch2 = inp.direction_two
        self.assertEqual((axis2.axis, count2.text, pitch2.text), ("Y", "V_N_DECK", "V_H * 2"))

    def text(self, c, axis, name, **kw):
        options = dict(axis=axis, frame=c.rect("V_X", "V_L", "V_X", "V_W"), start="V_D", end="V_H", string="MAGEWELL", height="V_D",
                       halign="center", valign="middle", font="Arial", style="bold", op="cut")
        options.update(kw)
        return c.text(name, **options)

    def test_a_text_is_a_construction_frame_one_sketch_text_and_a_cut_of_it(self):
        kit, c = self.part()
        self.text(c, "Z", "Label_Top_TextCut")
        sk = self.design.sketch("Label_Top_TextCutSk")
        self.assertTrue(all(ln.isConstruction for ln in sk.lines) and len(sk.lines) == 4)
        self.assertEqual(self.expressions("Label_Top_TextCutSk"), ["V_X", "V_X", "V_L - V_X", "V_W - V_X"])  # the frame only
        text = sk.texts[0]
        self.assertEqual((text.input.expression, text.input.height.text), ("'MAGEWELL'", "V_D"))
        corner, diagonal, horizontal, vertical, spacing = text.input.multi_line
        self.assertEqual((corner.at, diagonal.at), ((1.0, 1.0), (10.0, 6.0)))  # the opposite corners of the frame
        self.assertEqual((horizontal, vertical, spacing), (fake_adsk.HorizontalAlignments.CenterHorizontalAlignment,
                                                           fake_adsk.VerticalAlignments.MiddleVerticalAlignment, 0))
        self.assertEqual((text.input.fontName, text.input.textStyle, text.input.isHorizontalFlip),
                         ("Arial", fake_adsk.TextStyles.TextStyleBold, False))
        inp = self.design.feature("Label_Top_TextCut").input
        self.assertIs(inp.profile, text)  # the profile of the extrude is the sketch text itself
        self.assertEqual((inp.operation, inp.startExtent[1].text, inp.extent[1].text, inp.direction),
                         (Ops.CutFeatureOperation, "V_D", "V_H - V_D", Dirs.PositiveExtentDirection))
        self.assertEqual(inp.participantBodies, [self.comp.bodies[0]])

    def test_a_text_reads_unmirrored_from_plus_axis_so_it_is_flipped_when_plus_axis_points_against_the_normal(self):
        kit, c = self.part()
        self.text(c, "Y", "Label_Side_TextCut", style="regular", halign="left", valign="top")  # the normal of XZ is -Y
        text = self.design.sketch("Label_Side_TextCutSk").texts[0]
        self.assertTrue(text.input.isHorizontalFlip)
        self.assertIsNone(text.input.textStyle)  # regular is the default: nothing is set
        self.assertEqual(text.input.multi_line[2:4], (fake_adsk.HorizontalAlignments.LeftHorizontalAlignment,
                                                      fake_adsk.VerticalAlignments.TopVerticalAlignment))
        self.assertEqual(self.design.feature("Label_Side_TextCut").input.direction, Dirs.NegativeExtentDirection)

    def test_a_text_can_join(self):
        kit, c = self.part()
        self.text(c, "Z", "Label_Top_TextAdd", op="join")
        self.assertEqual(self.design.feature("Label_Top_TextAdd").input.operation, Ops.JoinFeatureOperation)


class AssertionTests(FusionCase):
    """Fusion answers unfavourably: the backend stops with a BackendError that names what failed."""

    def test_a_sketch_that_is_not_fully_constrained(self):
        self.design.unconstrained.add("Shell_Floor_BodySk")
        with self.assertRaisesRegex(self.module.BackendError, r"sketch Shell_Floor_BodySk: fully constrained False"):
            self.part()

    def test_a_sketch_with_the_wrong_number_of_profiles(self):
        self.design.profile_loops["Shell_Floor_BodySk"] = [1, 1]
        with self.assertRaisesRegex(self.module.BackendError, r"profiles 2 \(expected 1\)"):
            self.part()

    def test_a_sketch_that_is_not_healthy(self):
        self.design.sketch_health["Shell_Floor_BodySk"] = ERROR
        with self.assertRaisesRegex(self.module.BackendError, "Shell_Floor_BodySk.*fake sketch message"):
            self.part()

    def test_a_feature_that_is_not_healthy_reports_fusions_message(self):
        self.design.feature_health["Shell_Floor_Body"] = ERROR
        with self.assertRaisesRegex(self.module.BackendError, "feature Shell_Floor_Body.*fake feature message"):
            self.part()

    def test_a_plane_normal_that_differs_from_the_sketch(self):
        facade.PLANE_NORMAL["XY"] = -1
        with self.assertRaisesRegex(self.module.BackendError, "PLANE_NORMAL"):
            self.part()

    def test_a_sketch_direction_that_is_not_along_a_model_axis(self):
        self.design.frames["XY"] = ((0.6, 0.8, 0), (-0.8, 0.6, 0))
        with self.assertRaisesRegex(self.module.BackendError, "not along a model axis"):
            self.part()

    def test_a_sketch_origin_that_is_not_the_model_origin(self):
        self.design.sketch_origin = (0.1, 0.0, 0.0)
        with self.assertRaisesRegex(self.module.BackendError, "sketch origin is not the model origin"):
            self.part()

    def test_a_name_that_fusion_changes(self):
        self.design.rename["Shell_Floor_Body"] = "Shell_Floor_Body 1"
        with self.assertRaisesRegex(self.module.BackendError, "Fusion named it 'Shell_Floor_Body 1'"):
            self.part()

    def test_a_cut_needs_exactly_one_body(self):
        kit, c = self.part()
        self.comp.bodies.append(fake_adsk.Body(self.design))
        with self.assertRaisesRegex(self.module.BackendError, "holds 2 bodies"):
            c.extrude("Shell_Wall_SlotCut", axis="Z", loops=[c.rect("V_X", "V_H", "V_X", "V_W")], start=None, end="V_H", op="cut")

    def test_a_join_that_leaves_two_bodies_in_a_part(self):
        kit, c = self.part()
        original = self.comp._add_feature("extrude")

        def add_with_second_body(inp):
            feature = original(inp)
            self.comp.bodies.append(fake_adsk.Body(self.design))
            return feature

        self.comp.features.extrudeFeatures.add = add_with_second_body
        with self.assertRaisesRegex(self.module.BackendError, "part Base holds 2 bodies"):
            c.extrude("Shell_Wall_Add", axis="Z", loops=[c.rect("V_X", "V_H", "V_X", "V_W")], start=None, end="V_H", op="join")

    def test_a_spec_of_the_enhancement_phase_is_refused(self):
        backend = self.module.FusionBackend(SimpleNamespace(design=self.design, registry=REGISTRY, values=VALUES))
        spec = dataclasses.replace(PlaneSpec("Shell_Floor_Pl", "Base", "origin:XY", "V_X"), phase="enhance")
        with self.assertRaisesRegex(self.module.BackendError, "enhance_fusion.py of #85"):
            backend.execute(spec)

    def test_no_design_is_a_backend_error(self):
        with self.assertRaisesRegex(self.module.BackendError, "ctx.design is None"):
            self.module.FusionBackend(SimpleNamespace(design=None, registry=REGISTRY, values=VALUES))

    def test_the_backend_error_is_a_kit_error(self):
        self.assertTrue(issubclass(self.module.BackendError, KitError))


class KitIntegrationTests(FusionCase):
    def build(self, kit):
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="MCC_WALL", op="new")
        with c.shared_call("rail.male", {"x": "V_X"}, ("x",)):
            c.extrude("Rail_Male_FootAdd", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start="MCC_WALL", end="V_H", op="join")
        c.extrude("Vent_Slot_SlotCut", axis="Z", loops=[c.rect("V_X", "V_H", "V_D", "V_X")], start=None, end="V_H", op="cut")
        c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_DECK", pitch="V_D")
        return kit

    def test_the_facade_reaches_the_backend_as_FusionBackend_ctx(self):
        kit = self.kit()
        self.assertIsInstance(kit._backend, self.module.FusionBackend)

    def test_the_raw_inventory_and_the_build_record_equal_those_of_the_recording_backend(self):
        fusion = self.build(self.kit())
        recording = self.build(Kit(SimpleNamespace(backend="recording", design=None, document="Doc", registry=REGISTRY,
                                                   values=VALUES, options={}, log=print)))
        self.assertEqual(fusion.inventory(), recording.inventory())
        self.assertEqual(fusion._backend.build_record(), recording._backend.build_record())

    def test_a_shared_call_is_bookkeeping_only(self):
        kit = self.build(self.kit())
        self.assertEqual([c["builder_id"] for c in kit._backend.build_record()["shared_calls"]], ["rail.male"])
        self.assertEqual(self.design.log.count(("sketches.add", "XY")), 3)  # floor, foot, slot: the call added none of its own

    def test_a_failure_in_the_middle_leaves_the_failed_spec_unrecorded(self):
        self.design.feature_health["Shell_Floor_Body"] = ERROR
        kit = self.kit()
        with self.assertRaises(self.module.BackendError):
            self.build(kit)
        self.assertEqual([i["name"] for i in kit.inventory()["items"]], ["Base", "Shell_Floor_BodySk"])


class ImportBoundaryTests(unittest.TestCase):
    """The kit imports and runs without adsk; only the backend module needs it."""

    def run_python(self, code: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True, timeout=120)

    def test_importing_the_kit_and_running_the_recording_backend_does_not_load_adsk_or_the_fusion_backend(self):
        code = (
            "import sys\n"
            "sys.modules['adsk'] = None\n"  # any attempt to import adsk raises ImportError
            f"from {PKG}.core import facade, record, checks, plan\n"
            "from types import SimpleNamespace as NS\n"
            "rows = [{'name': 'V_L', 'unit': 'mm', 'kind': 'solver', 'expression': None, 'fusion': None}]\n"
            "kit = facade.Kit(NS(backend='recording', design=None, document='D', registry=rows, values={'V_L': 10.0}, options={}))\n"
            "kit.component('Base', role='part', datum=(None, None, None))\n"
            f"assert '{MODULE}' not in sys.modules, 'fusion_backend was imported'\n"
            "print('ok')\n")
        done = self.run_python(code)
        self.assertEqual((done.returncode, done.stdout.strip()), (0, "ok"), done.stderr)

    def test_the_backend_module_itself_needs_adsk_and_says_so(self):
        done = self.run_python(f"import sys\nsys.modules['adsk'] = None\nimport {MODULE}\n")
        self.assertNotEqual(done.returncode, 0)
        self.assertRegex(done.stderr, "ModuleNotFoundError|ImportError")

    def test_a_fusion_context_without_adsk_fails_at_the_import_not_later(self):
        code = (
            "import sys\nsys.modules['adsk'] = None\nfrom types import SimpleNamespace as NS\n"
            f"from {PKG}.core import facade\n"
            "try:\n"
            "    facade.Kit(NS(backend='fusion', design=None, document='D', registry=[], values={}, options={}))\n"
            "except ImportError:\n"
            "    print('import error')\n")
        done = self.run_python(code)
        self.assertEqual(done.stdout.strip(), "import error", done.stderr)


if __name__ == "__main__":
    unittest.main()
