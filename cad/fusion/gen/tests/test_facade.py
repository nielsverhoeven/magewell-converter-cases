"""The facade of the modelling kit (plan 3.3, 3.6 to 3.8, K2a step 4): loops, extrude, phases, within, shared calls,
the reserved enhancement surface, the recording backend and the raw inventory.

The context is a ``types.SimpleNamespace`` and the registry a list of literal rows.  Numbers under the build values:
V_X = 10, V_X2 = 10, V_H = 20, V_D = 8, V_L = 100, V_W = 60, V_NEG = -5, MCC_WALL = 3.

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ..core import expr, facade
from ..core.facade import DuplicateNameError, Kit, PhaseError, ZeroOffsetError
from ..core.names import KitError, KitNameError

FIXTURES = Path(__file__).parent / "fixtures"


def row(name, unit, kind, expression=None, fusion=None):
    return {"name": name, "unit": unit, "kind": kind, "expression": expression, "fusion": fusion,
            "comment": "", "description": "test row", "src": "test", "conf": None}


VALUES = {"V_X": 10.0, "V_X2": 10.0, "V_H": 20.0, "V_D": 8.0, "V_L": 100.0, "V_W": 60.0, "V_NEG": -5.0}
REGISTRY = [row("MCC_WALL", "mm", "constant", "3 mm", "3 mm")] + [row(n, "mm", "solver") for n in VALUES]


def make_kit(**extra) -> Kit:
    ctx = SimpleNamespace(backend="recording", design=None, document="Doc", registry=REGISTRY, values=VALUES,
                          options={}, log=print, **extra)
    return Kit(ctx)


def dims(sketch):
    return [(d.kind, d.a, d.b, d.axis, d.text) for d in sketch.dims]


def cons(sketch):
    return [(c.kind, c.a, c.b) for c in sketch.constraints]


def specs(kit, cls):
    return [s for s in kit._backend.timeline if isinstance(s, cls)]


class RectangleTests(unittest.TestCase):
    def test_a_rectangle_at_the_origin_datum(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        self.assertEqual(c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")],
                                   start=None, end="MCC_WALL", op="new"), "Shell_Floor_Body")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(sk.name, "Shell_Floor_BodySk")
        self.assertEqual(sk.on, "origin:XY")
        self.assertEqual(sk.datum, (None, None))
        self.assertEqual(sk.points, ("p0_0", "p0_1", "p0_2", "p0_3"))
        self.assertEqual(sk.lines, (("l0_0", "p0_0", "p0_1"), ("l0_1", "p0_1", "p0_2"),
                                    ("l0_2", "p0_2", "p0_3"), ("l0_3", "p0_3", "p0_0")))
        self.assertEqual(dims(sk), [("distance", "O", "p0_0", "u", "V_X"),
                                    ("distance", "O", "p0_0", "v", "MCC_WALL"),
                                    ("distance", "p0_0", "p0_1", "u", "V_L - V_X"),
                                    ("distance", "p0_1", "p0_2", "v", "V_W - MCC_WALL")])
        self.assertEqual(cons(sk), [("parallel_u", "l0_0", ""), ("parallel_v", "l0_1", ""),
                                    ("parallel_u", "l0_2", ""), ("parallel_v", "l0_3", "")])
        self.assertEqual((sk.profiles, sk.rule), (1, "all"))

    def test_a_rectangle_against_a_datum_point(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=("V_X", "MCC_WALL", None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "V_H", "V_W")], start=None, end="V_H", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(sk.datum, ("V_X", "MCC_WALL"))
        self.assertEqual(sk.points[0], "P0")
        # the u coordinate equals the datum: a constraint and no dimension
        self.assertEqual(dims(sk), [("distance", "O", "P0", "u", "V_X"),
                                    ("distance", "O", "P0", "v", "MCC_WALL"),
                                    ("distance", "P0", "p0_0", "v", "V_H - MCC_WALL"),
                                    ("distance", "p0_0", "p0_1", "u", "V_L - V_X"),
                                    ("distance", "p0_1", "p0_2", "v", "V_W - V_H")])
        self.assertIn(("same_u", "P0", "p0_0"), cons(sk))
        self.assertNotIn(("same_v", "P0", "p0_0"), cons(sk))

    def test_a_datum_on_one_axis_is_tied_to_the_origin_on_the_other(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=("V_X", None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", None, "V_W")], start=None, end="V_H", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(cons(sk)[0], ("same_v", "O", "P0"))
        self.assertEqual(dims(sk)[0], ("distance", "O", "P0", "u", "V_X"))
        self.assertIn(("same_u", "P0", "p0_0"), cons(sk))
        self.assertIn(("same_v", "P0", "p0_0"), cons(sk))

    def test_a_datum_that_evaluates_negative_is_negated(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=("V_NEG", None, None))
        c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(dims(sk)[0], ("distance", "O", "P0", "u", "-(V_NEG)"))
        self.assertEqual(dims(sk)[1], ("distance", "P0", "p0_0", "u", "V_X - V_NEG"))

    def test_a_zero_datum_is_refused(self):
        kit = Kit(SimpleNamespace(backend="recording", document="Doc", registry=REGISTRY, values=dict(VALUES, V_X=0.0)))
        c = kit.component("Base", role="part", datum=("V_X", None, None))
        with self.assertRaises(ZeroOffsetError):
            c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_L", "V_W", "V_H", "V_W")], start=None, end="V_H", op="new")

    def test_an_offset_that_is_zero_under_the_values_is_refused(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=("V_X2", None, None))
        with self.assertRaises(ZeroOffsetError):  # V_X and V_X2 differ as text but are both 10
            c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="new")


class CircleTests(unittest.TestCase):
    def test_a_circle(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Patch_Hole_Body", axis="Z", loops=[c.circle("V_X", "V_H", "V_D")], start=None, end="MCC_WALL", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(sk.points, ("c0",))
        self.assertEqual(sk.circles, (("k0", "c0"),))
        self.assertEqual(dims(sk), [("distance", "O", "c0", "u", "V_X"), ("distance", "O", "c0", "v", "V_H"),
                                    ("diameter", "k0", "", "", "V_D")])
        self.assertEqual(cons(sk), [])

    def test_a_circle_centre_equal_to_the_datum_is_a_constraint(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=("V_X", "V_H", None))
        c.extrude("Patch_Hole_Body", axis="Z", loops=[c.circle("V_X", "V_H", "V_D")], start=None, end="MCC_WALL", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(cons(sk), [("same_u", "P0", "c0"), ("same_v", "P0", "c0")])
        self.assertEqual(dims(sk)[-1], ("diameter", "k0", "", "", "V_D"))


class PolygonTests(unittest.TestCase):
    def test_a_five_point_polygon(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        poly = c.polygon([("V_X", "MCC_WALL"), ("V_L", "MCC_WALL"), ("V_L", "V_H"), ("V_W", "V_W"), ("V_X", "V_H")])
        c.extrude("Shell_Wedge_Body", axis="Z", loops=[poly], start=None, end="V_H", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(sk.points, tuple(f"q0_{k}" for k in range(5)))
        self.assertEqual(sk.lines, tuple((f"m0_{k}", f"q0_{k}", f"q0_{(k + 1) % 5}") for k in range(5)))
        self.assertEqual(dims(sk), [("distance", "O", "q0_0", "u", "V_X"),
                                    ("distance", "O", "q0_0", "v", "MCC_WALL"),
                                    ("distance", "O", "q0_1", "u", "V_L"),
                                    ("distance", "O", "q0_2", "v", "V_H"),
                                    ("distance", "O", "q0_3", "u", "V_W"),
                                    ("distance", "O", "q0_3", "v", "V_W"),
                                    ("distance", "O", "q0_4", "u", "V_X"),
                                    ("distance", "O", "q0_4", "v", "V_H")])
        # equal to the previous vertex: a constraint, no dimension; the closing line gets none
        self.assertEqual(cons(sk), [("same_v", "q0_0", "q0_1"), ("same_u", "q0_1", "q0_2")])

    def test_fewer_than_three_points_are_refused(self):
        c = make_kit().component("Base", role="part", datum=(None, None, None))
        with self.assertRaises(KitError):
            c.polygon([("V_X", "V_H"), ("V_L", "V_H")])


class RingTests(unittest.TestCase):
    def test_a_ring(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        c.extrude("Shell_Ring_Body", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="new",
                  holes=[c.circle("V_W", "V_H", "V_D")])
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual(dims(sk), [("distance", "O", "p0_0", "u", "V_X"),
                                    ("distance", "O", "p0_0", "v", "MCC_WALL"),
                                    ("distance", "p0_0", "p0_1", "u", "V_L - V_X"),
                                    ("distance", "p0_1", "p0_2", "v", "V_W - MCC_WALL"),
                                    ("distance", "O", "c1", "u", "V_W"),
                                    ("distance", "O", "c1", "v", "V_H"),
                                    ("diameter", "k1", "", "", "V_D")])
        self.assertEqual((sk.profiles, sk.rule, len(sk.loops), len(sk.holes)), (2, "ring", 1, 1))

    def test_holes_need_one_outer_loop_strictly_around_them(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        outer = c.rect("V_X", "V_L", "MCC_WALL", "V_W")
        with self.assertRaises(KitError):  # two outer loops with holes
            c.extrude("Shell_A_Body", axis="Z", loops=[outer, c.circle("V_H", "V_H", "V_D")], holes=[c.circle("V_W", "V_H", "V_D")],
                      start=None, end="V_H", op="new")
        with self.assertRaises(KitError):  # the hole pokes out of the outer loop (circle at u = 10, d = 8)
            c.extrude("Shell_B_Body", axis="Z", loops=[outer], holes=[c.circle("V_X", "V_H", "V_D")], start=None, end="V_H", op="new")

    def test_loops_that_touch_or_overlap_are_refused(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        with self.assertRaises(KitError):
            c.extrude("Shell_A_Body", axis="Z", start=None, end="V_H", op="new",
                      loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W"), c.circle("V_W", "V_H", "V_D")])
        # nothing was recorded by the refused call
        self.assertEqual(kit.inventory()["items"], [{"kind": "component", "name": "Base", "component": "."}])
        c.extrude("Shell_A_Body", axis="Z", start=None, end="V_H", op="new",
                  loops=[c.rect("V_X", "V_H", "MCC_WALL", "V_H"), c.rect("V_W", "V_L", "V_W", "V_L")])


class ExtrudeTests(unittest.TestCase):
    def setUp(self):
        self.kit = make_kit()
        self.c = self.kit.component("Base", role="part", datum=(None, None, None))

    def test_start_distance_and_direction(self):
        self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start="V_X", end="V_L", op="new")
        f = specs(self.kit, facade.ExtrudeSpec)[0]
        self.assertEqual((f.start_offset, f.distance, f.direction, f.op, f.within), ("V_X", "V_L - V_X", "positive", "new", None))
        self.assertEqual(f.sketch, "Shell_Floor_BodySk")

    def test_without_a_start_there_is_no_start_offset(self):
        self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        f = specs(self.kit, facade.ExtrudeSpec)[0]
        self.assertEqual((f.start_offset, f.distance), (None, "V_H"))

    def test_a_plane_normal_against_the_axis_flips_the_start_offset(self):
        with mock.patch.dict(facade.PLANE_NORMAL, {"XY": -1}):
            self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start="V_X", end="V_L", op="new")
        f = specs(self.kit, facade.ExtrudeSpec)[0]
        self.assertEqual((f.start_offset, f.distance, f.direction), ("-(V_X)", "V_L - V_X", "negative"))

    def test_the_in_plane_axes_follow_the_axis(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=("V_X", "V_H", "MCC_WALL"))
        c.extrude("Shell_Side_Body", axis="X", loops=[c.rect("V_H", "V_L", "MCC_WALL", "V_W")], start=None, end="V_D", op="new")
        sk = specs(kit, facade.SketchSpec)[0]
        self.assertEqual((sk.on, sk.datum), ("origin:YZ", ("V_H", "MCC_WALL")))
        c.extrude("Shell_Side_Add", axis="Y", loops=[c.rect("V_X", "V_L", "V_H", "V_W")], start=None, end="V_D", op="join")
        sk = specs(kit, facade.SketchSpec)[1]
        self.assertEqual((sk.on, sk.datum), ("origin:XZ", ("V_X", "MCC_WALL")))

    def test_both_ends_none_and_bad_arguments(self):
        with self.assertRaises(KitError):
            self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end=None, op="new")
        with self.assertRaises(KitError):
            self.c.extrude("Shell_Floor_Body", axis="W", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        with self.assertRaises(KitError):
            self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="weld")

    def test_a_number_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.c.rect(3, "V_L", None, "V_W")
        with self.assertRaises(TypeError):
            self.c.circle("V_X", "V_H", 8.0)
        with self.assertRaises(TypeError):
            self.c.polygon([("V_X", 1), ("V_L", "V_H"), ("V_W", "V_W")])
        with self.assertRaises(TypeError):
            self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end=5, op="new")
        with self.assertRaises(TypeError):
            self.kit.component("Other", role="part", datum=(1, None, None))

    def test_a_typed_literal_and_an_unknown_name_are_refused(self):
        with self.assertRaises(expr.LiteralError):
            self.c.rect("3 mm", "V_L", None, "V_W")
        with self.assertRaises(expr.UnknownNameError):
            self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_NOPE", op="new")

    def test_names(self):
        loops = [self.c.rect(None, "V_L", None, "V_W")]
        for bad, op in (("Shell_Floor_Add", "new"), ("Shell_Floor_Body", "cut"), ("Shell_Floor_ThreadAdd", "new"),
                        ("Shell_Floor", "new"), ("shell_Floor_Body", "new")):
            with self.subTest(bad), self.assertRaises(KitNameError):
                self.c.extrude(bad, axis="Z", loops=loops, start=None, end="V_H", op=op)
        self.assertEqual(self.kit.inventory()["items"], [{"kind": "component", "name": "Base", "component": "."}])

    def test_a_known_owner_list_is_enforced_when_the_context_has_one(self):
        kit = make_kit(owners=["Shell"])
        c = kit.component("Base", role="part", datum=(None, None, None))
        with self.assertRaises(KitNameError):
            c.extrude("Patch_Hole_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        c.extrude("Shell_Hole_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")

    def test_duplicate_names(self):
        self.c.extrude("Shell_Floor_Body", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        self.c.extrude("Shell_Wall_Add", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="join")
        with self.assertRaises(DuplicateNameError):
            self.c.extrude("Shell_Wall_Add", axis="Z", loops=[self.c.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="join")
        other = self.kit.component("Lid", role="part", datum=(None, None, None))
        with self.assertRaises(DuplicateNameError):  # names are unique in the document, not per component
            other.extrude("Shell_Floor_Body", axis="Z", loops=[other.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
        with self.assertRaises(DuplicateNameError):
            self.kit.component("Base", role="part", datum=(None, None, None))

    def test_a_bad_component(self):
        with self.assertRaises(KitNameError):
            self.kit.component("base", role="part", datum=(None, None, None))
        with self.assertRaises(KitError):
            self.kit.component("Other", role="solid", datum=(None, None, None))
        with self.assertRaises(KitError):
            self.kit.component("Other", role="part", datum=(None, None))


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.kit = make_kit()
        self.c = self.kit.component("Base", role="part", datum=(None, None, None))
        self.n = 0

    def go(self, op, name=None, **kw):
        self.n += 1
        suffix = {"new": "Body", "join": "Add", "cut": "Cut", "rejoin": "Rejoin"}[op]
        return self.c.extrude(name or f"Shell_S{self.n}_{suffix}", axis="Z", start=None, end="V_H", op=op,
                              loops=[self.c.rect(None, "V_L", None, "V_W")], **kw)

    def test_new_joins_cuts_rejoins_in_order(self):
        self.go("new")
        self.go("join")
        self.go("join")
        cut = self.go("cut")
        self.go("cut")
        self.go("rejoin", within=cut)
        self.go("rejoin", within=cut)
        self.assertEqual(len(specs(self.kit, facade.ExtrudeSpec)), 7)

    def test_the_first_feature_of_a_part_is_new(self):
        for op in ("join", "cut"):
            with self.subTest(op), self.assertRaises(PhaseError):
                self.go(op)

    def test_a_part_has_one_body(self):
        self.go("new")
        with self.assertRaises(PhaseError):
            self.go("new")

    def test_a_join_after_a_cut_raises(self):
        self.go("new")
        self.go("cut")
        with self.assertRaises(PhaseError):
            self.go("join")

    def test_anything_but_a_rejoin_after_a_rejoin_raises(self):
        self.go("new")
        cut = self.go("cut")
        self.go("rejoin", within=cut)
        for op in ("join", "cut"):
            with self.subTest(op), self.assertRaises(PhaseError):
                self.go(op)

    def test_a_refused_call_leaves_the_phase_alone(self):
        self.go("new")
        self.go("cut")
        with self.assertRaises(PhaseError):
            self.go("join")
        self.go("cut")  # still allowed

    def test_a_reserve_and_a_ghost_hold_bodies_only(self):
        for role in ("reserve", "ghost"):
            with self.subTest(role):
                r = self.kit.component(f"{role.capitalize()}_Bay", role=role, datum=(None, None, None))
                r.extrude(f"Fan_{role.capitalize()}A_Body", axis="Z", loops=[r.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
                r.extrude(f"Fan_{role.capitalize()}B_Body", axis="Z", loops=[r.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="new")
                with self.assertRaises(PhaseError):
                    r.extrude(f"Fan_{role.capitalize()}C_Add", axis="Z", loops=[r.rect(None, "V_L", None, "V_W")], start=None, end="V_H", op="join")


class RejoinTests(unittest.TestCase):
    def setUp(self):
        self.kit = make_kit()
        self.c = self.kit.component("Base", role="part", datum=(None, None, None))
        self.n = 0
        self.go("new", "Shell_Floor_Body")

    def go(self, op, name, **kw):
        return self.c.extrude(name, axis="Z", start=None, end="V_H", op=op, loops=[self.c.rect(None, "V_L", None, "V_W")], **kw)

    def test_a_rejoin_names_its_cut(self):
        self.go("join", "Shell_Wall_Add")
        self.go("cut", "Fan_Hole_OpeningCut")
        self.go("rejoin", "Fan_Hole_Ring1Rejoin", within="Fan_Hole_OpeningCut")
        rejoin = specs(self.kit, facade.ExtrudeSpec)[-1]
        self.assertEqual((rejoin.op, rejoin.within), ("rejoin", "Fan_Hole_OpeningCut"))

    def test_a_rejoin_without_within_raises(self):
        self.go("cut", "Fan_Hole_OpeningCut")
        with self.assertRaises(KitError):
            self.go("rejoin", "Fan_Hole_Ring1Rejoin")

    def test_within_on_another_operation_raises(self):
        with self.assertRaises(KitError) as cm:  # a join, while the phase is still right for it
            self.go("join", "Shell_Wall_Add", within="Shell_Floor_Body")
        self.assertNotIsInstance(cm.exception, PhaseError)
        self.go("cut", "Fan_Hole_OpeningCut")
        with self.assertRaises(KitError) as cm:
            self.go("cut", "Fan_Other_Cut", within="Fan_Hole_OpeningCut")
        self.assertNotIsInstance(cm.exception, PhaseError)

    def test_within_naming_a_join_raises(self):
        self.go("join", "Shell_Wall_Add")
        self.go("cut", "Fan_Hole_OpeningCut")
        with self.assertRaises(KitError) as cm:
            self.go("rejoin", "Fan_Hole_Ring1Rejoin", within="Shell_Wall_Add")
        self.assertIn("names a cut", str(cm.exception))

    def test_within_naming_a_later_or_unknown_feature_raises(self):
        self.go("cut", "Fan_Hole_OpeningCut")
        with self.assertRaises(KitError):  # a cut that does not exist yet
            self.go("rejoin", "Fan_Hole_Ring1Rejoin", within="Fan_Later_LaterCut")
        with self.assertRaises(KitError):  # the re-join itself is not an earlier feature
            self.go("rejoin", "Fan_Hole_Ring2Rejoin", within="Fan_Hole_Ring2Rejoin")

    def test_within_naming_a_cut_of_another_component_raises(self):
        self.go("cut", "Fan_Hole_OpeningCut")
        other = self.kit.component("Lid", role="part", datum=(None, None, None))
        other.extrude("Shell_Lid_Body", axis="Z", start=None, end="V_H", op="new", loops=[other.rect(None, "V_L", None, "V_W")])
        with self.assertRaises(KitError):
            other.extrude("Fan_Hole_Ring1Rejoin", axis="Z", start=None, end="V_H", op="rejoin", within="Fan_Hole_OpeningCut",
                          loops=[other.rect(None, "V_L", None, "V_W")])


class SharedCallTests(unittest.TestCase):
    def setUp(self):
        self.kit = make_kit()
        self.c = self.kit.component("Base", role="part", datum=(None, None, None))

    def feature(self, name, op="new"):
        self.c.extrude(name, axis="Z", start=None, end="V_H", op=op, loops=[self.c.rect(None, "V_L", None, "V_W")])

    def test_a_call_records_arguments_placement_and_produced_names(self):
        with self.c.shared_call("tg.groove", {"x_mid": "V_X", "length": "V_L"}, ("x_mid",)):
            self.feature("Shell_Floor_Body")
        (call,) = self.kit._backend.shared
        self.assertEqual((call.builder_id, call.arguments, call.placement, call.parent),
                         ("tg.groove", {"x_mid": "V_X", "length": "V_L"}, ("x_mid",), None))
        self.assertEqual(call.produced, ["Shell_Floor_Body", "Shell_Floor_BodySk"])

    def test_a_nested_call_records_its_parent(self):
        with self.c.shared_call("panel.wall_cut", {"a": "V_X"}, ()):
            with self.c.shared_call("neutrik.seat", {"b": "V_H"}, ("b",)):
                self.feature("Shell_Floor_Body")
            self.feature("Shell_Wall_Add", "join")
        with self.c.shared_call("rail.female_cut", {}, ()):
            pass
        outer, inner, third = sorted(self.kit._backend.shared, key=lambda s: [
            "panel.wall_cut", "neutrik.seat", "rail.female_cut"].index(s.builder_id))
        self.assertEqual((outer.parent, inner.parent, third.parent), (None, "panel.wall_cut", None))
        self.assertEqual(inner.produced, ["Shell_Floor_Body", "Shell_Floor_BodySk"])
        self.assertEqual(outer.produced, ["Shell_Wall_Add", "Shell_Wall_AddSk"])

    def test_the_stack_unwinds_after_an_error(self):
        with self.assertRaises(ZeroDivisionError):
            with self.c.shared_call("a.b", {}, ()):
                raise ZeroDivisionError
        with self.c.shared_call("c.d", {}, ()):
            pass
        self.assertEqual([c.parent for c in self.kit._backend.shared], [None, None])

    def test_bad_arguments(self):
        with self.assertRaises(KitError):
            with self.c.shared_call("a.b", {"x": "V_X"}, ("y",)):
                pass
        with self.assertRaises(KitError):
            with self.c.shared_call("", {}, ()):
                pass

    def test_a_feature_outside_a_call_is_in_no_call(self):
        self.feature("Shell_Floor_Body")
        with self.c.shared_call("a.b", {}, ()):
            pass
        self.assertEqual(self.kit._backend.shared[0].produced, [])


class KitTests(unittest.TestCase):
    def test_enhance_is_reserved(self):
        kit = make_kit()
        for attr in ("after", "side_faces", "faces", "edges", "require_thread", "thread", "rule_fillet", "chamfer"):
            with self.subTest(attr), self.assertRaises(NotImplementedError):
                getattr(kit.enhance, attr)

    def test_the_backend_comes_from_the_context(self):
        with self.assertRaises(KitError):
            Kit(SimpleNamespace(backend="nope", document="Doc", registry=REGISTRY, values=VALUES))

    def test_api_version(self):
        self.assertEqual(facade.API, 1)
        self.assertEqual(set(facade.PLANE_NORMAL), {"XY", "XZ", "YZ"})


def three_feature_component() -> Kit:
    kit = make_kit()
    c = kit.component("Base", role="part", datum=(None, None, None))
    c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect(None, "V_L", None, "V_W")], start=None, end="MCC_WALL", op="new")
    c.extrude("Shell_Walls_Add", axis="Z", start="MCC_WALL", end="V_H", op="join",
              loops=[c.rect(None, "V_L", None, "V_W")],
              holes=[c.rect("MCC_WALL", expr.sub("V_L", "MCC_WALL"), "MCC_WALL", expr.sub("V_W", "MCC_WALL"))])
    c.extrude("Patch_Hole_BoreCut", axis="Z", loops=[c.circle("V_X", "V_H", "V_D")], start=None, end="MCC_WALL", op="cut")
    return kit


class InventoryTests(unittest.TestCase):
    def test_the_inventory_of_a_three_feature_component(self):
        want = json.loads((FIXTURES / "facade_inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(three_feature_component().inventory(), want)

    def test_a_rejoin_carries_within_in_the_inventory(self):
        kit = make_kit()
        c = kit.component("Base", role="part", datum=(None, None, None))
        loops = lambda: [c.rect(None, "V_L", None, "V_W")]  # noqa: E731
        c.extrude("Shell_Floor_Body", axis="Z", loops=loops(), start=None, end="V_H", op="new")
        c.extrude("Fan_Hole_OpeningCut", axis="Z", loops=loops(), start=None, end="V_H", op="cut")
        c.extrude("Fan_Hole_Ring1Rejoin", axis="Z", loops=loops(), start="MCC_WALL", end="V_H", op="rejoin", within="Fan_Hole_OpeningCut")
        last = kit.inventory()["items"][-1]
        self.assertEqual(last, {"kind": "feature", "name": "Fan_Hole_Ring1Rejoin", "component": "Base", "type": "ExtrudeFeature",
                                "expressions": ["MCC_WALL", "V_H - MCC_WALL"], "within": "Fan_Hole_OpeningCut"})

    def test_every_expression_references_a_parameter(self):
        for item in three_feature_component().inventory()["items"]:
            for text in item.get("expressions", []):
                self.assertTrue(expr.names_in(text), text)

    def test_the_build_record(self):
        kit = three_feature_component()
        with kit._components["Base"].shared_call("a.b", {"p": "V_X"}, ("p",)):
            pass
        rec = kit._backend.build_record(api=facade.API)
        self.assertEqual(list(rec), ["schema", "api", "document", "components", "specs", "shared_calls"])
        self.assertEqual((rec["schema"], rec["api"], rec["document"]), (1, 1, "Doc"))
        self.assertEqual([c["name"] for c in rec["components"]], ["Base"])
        self.assertEqual([(s["spec"], s["name"]) for s in rec["specs"]],
                         [("SketchSpec", "Shell_Floor_BodySk"), ("ExtrudeSpec", "Shell_Floor_Body"),
                          ("SketchSpec", "Shell_Walls_AddSk"), ("ExtrudeSpec", "Shell_Walls_Add"),
                          ("SketchSpec", "Patch_Hole_BoreCutSk"), ("ExtrudeSpec", "Patch_Hole_BoreCut")])
        self.assertEqual(rec["shared_calls"][0]["builder_id"], "a.b")
        json.dumps(rec)  # plain data


if __name__ == "__main__":
    unittest.main()
