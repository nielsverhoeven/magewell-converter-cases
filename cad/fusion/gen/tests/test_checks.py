"""The plan checks (plan 3.9, K3 step 4): a clean record gives no finding, and one deliberately broken record per
check id gives findings of exactly that id.  CK10 is ``checks.definitions`` over several records.

Numbers of configuration ``a`` (``b`` differs where a test says so): MCC_WALL = 3, V_X = 10, V_D = 8, V_A = 30,
V_GAP = 50, V_L = 100, V_W = 60, V_H = 20, V_S0 = 2, V_N_ROWS = 2.  The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace

from ..core import checks
from ..core.checks import Finding
from ..core.facade import Kit
from ..core.names import KitError


def row(name, unit, kind, expression=None, fusion=None):
    return {"name": name, "unit": unit, "kind": kind, "expression": expression, "fusion": fusion,
            "comment": "", "description": "test row", "src": "test", "conf": None}


VALUES_A = {"V_X": 10.0, "V_D": 8.0, "V_A": 30.0, "V_GAP": 50.0, "V_L": 100.0, "V_W": 60.0, "V_H": 20.0, "V_S0": 2.0,
            "V_N_ROWS": 2}
REGISTRY = [row("MCC_WALL", "mm", "constant", "3 mm", "3 mm")] + [
    row(n, "" if n.startswith("V_N_") else "mm", "solver") for n in VALUES_A]
FLAGS = ("Shell_Floor", "Shell_Walls", "Rail_Male", "Patch_Hole", "Vent_Slot", "Vent_Plug")
OWNERS = ["Shell", "Rail", "Patch", "Vent"]


def configs(**b_values):
    """The two configurations: ``b`` is ``a`` with the given values; in ``b`` the Vent_Slot and Vent_Plug sets are suppressed."""
    a = {"values": dict(VALUES_A), "suppress": {f: False for f in FLAGS}}
    b = {"values": {**VALUES_A, **b_values}, "suppress": {f: f.startswith("Vent_") for f in FLAGS}}
    return {"a": a, "b": b}


def make_record() -> dict:
    ctx = SimpleNamespace(backend="recording", design=None, document="Doc", registry=REGISTRY, values=VALUES_A,
                          options={}, log=print)
    kit = Kit(ctx)
    c = kit.component("Base", role="part", datum=(None, None, None))
    c.extrude("Shell_Floor_Body", axis="Z", loops=[c.rect("MCC_WALL", "V_L", "MCC_WALL", "V_W")], start=None, end="V_H", op="new")
    c.extrude("Shell_Walls_Add", axis="Z", loops=[c.rect("MCC_WALL", "V_L", "MCC_WALL", "V_W")], start="V_S0", end="V_H", op="join")
    with c.shared_call("rail.male", {"x": "V_X", "width": "V_W"}, ("x",)):
        c.extrude("Rail_Male_FootAdd", axis="Z", loops=[c.rect("V_X", "V_L", "MCC_WALL", "V_W")], start="MCC_WALL", end="V_H", op="join")
    with c.shared_call("panel.wall_cut", {"axis": "X"}, ("axis",)):
        with c.shared_call("neutrik.d_wall_cut", {"d": "V_D"}, ()):
            c.extrude("Patch_Hole_BoreCut", axis="Z", loops=[c.circle("V_A", "V_A", "V_D")], start=None, end="V_H", op="cut")
    c.extrude("Vent_Slot_SlotCut", axis="Z", loops=[c.rect("V_X", "V_A", "V_X", "V_A"), c.rect("V_GAP", "V_L", "V_X", "V_A")],
              start=None, end="V_H", op="cut")
    c.pattern("Vent_Slot_SlotPat", seed="Vent_Slot_SlotCut", axis="X", count="V_N_ROWS", pitch="V_D")
    c.extrude("Vent_Plug_PlugRejoin", axis="Z", loops=[c.rect("V_X", "V_A", "V_X", "V_A")], start=None, end="V_H", op="rejoin",
              within="Vent_Slot_SlotCut")
    return kit._backend.build_record()


def spec(record, name) -> dict:
    return next(s for s in record["specs"] if s.get("name") == name)


def run(record, sets=None, **kwargs):
    return checks.run(record, REGISTRY, sets or configs(), owners=OWNERS, **kwargs)


class Base(unittest.TestCase):
    def setUp(self):
        self.record = make_record()

    def only(self, findings, check_id, count=None):
        self.assertTrue(findings, f"no finding, {check_id} expected")
        self.assertEqual({f.id for f in findings}, {check_id}, [str(f) for f in findings])
        if count is not None:
            self.assertEqual(len(findings), count, [str(f) for f in findings])
        return findings


class CleanTests(Base):
    def test_the_clean_record_passes_every_check(self):
        self.assertEqual(run(self.record), [])

    def test_no_owner_list_skips_the_owner_check_only(self):
        self.assertEqual(checks.run(self.record, REGISTRY, configs()), [])

    def test_a_finding_prints_its_id_name_and_text(self):
        self.assertEqual(str(Finding("CK1", "A_B_C", "text")), "CK1 A_B_C: text")


class NameTests(Base):
    def test_ck1_a_name_with_a_wrong_grammar(self):
        spec(self.record, "Shell_Walls_Add")["name"] = "Walls"
        self.only(run(self.record), "CK1", 1)

    def test_ck1_an_unknown_owner(self):
        self.only(checks.run(self.record, REGISTRY, configs(), owners=["Shell", "Patch", "Vent"]), "CK1")

    def test_ck1_a_suffix_that_does_not_match_the_operation(self):
        spec(self.record, "Vent_Slot_SlotCut")["op"] = "join"
        self.assertIn("CK1", {f.id for f in run(self.record)})

    def test_ck1_a_name_that_occurs_twice(self):
        spec(self.record, "Shell_Walls_Add")["name"] = "Shell_Floor_Body"
        self.assertTrue(any("twice" in f.text or "times" in f.text for f in run(self.record) if f.id == "CK1"))

    def test_ck1_a_sketch_name_without_a_derived_tag(self):
        spec(self.record, "Shell_Walls_AddSk")["name"] = "Shell_Walls_Plate"
        self.assertIn("CK1", {f.id for f in run(self.record)})

    def test_ck1_a_bad_component_name(self):
        self.record["components"][0]["name"] = "base"
        self.assertIn("CK1", {f.id for f in run(self.record)})


class ExpressionTests(Base):
    def test_ck2_an_unknown_name(self):
        spec(self.record, "Shell_Walls_AddSk")["dims"][0]["text"] = "V_UNKNOWN + MCC_WALL"
        self.only(run(self.record), "CK2", 1)

    def test_ck2_a_typed_number(self):
        spec(self.record, "Shell_Walls_Add")["distance"] = "V_H - 3"
        self.only(run(self.record), "CK2", 1)

    def test_ck2_a_count_that_is_not_a_bare_name(self):
        spec(self.record, "Vent_Slot_SlotPat")["count"] = "V_N_ROWS + 1"
        self.only(run(self.record), "CK2", 1)

    def test_ck2_a_missing_diameter(self):
        spec(self.record, "Patch_Hole_BoreCutSk")["loops"][0]["args"][2] = None
        self.assertIn("CK2", {f.id for f in run(self.record)})

    def test_ck2_an_expression_that_is_not_a_string(self):
        spec(self.record, "Shell_Walls_Add")["start_offset"] = 2
        self.only(run(self.record), "CK2", 1)


class PhaseTests(Base):
    def test_ck3_a_join_after_a_cut(self):
        specs = self.record["specs"]
        i = next(k for k, s in enumerate(specs) if s.get("name") == "Shell_Walls_Add")
        j = next(k for k, s in enumerate(specs) if s.get("name") == "Vent_Slot_SlotCut")
        specs.insert(j + 2, specs.pop(i + 1))  # the sketch of the join stays, the join moves behind the cut
        specs.insert(j + 1, specs.pop(i))
        self.only(run(self.record), "CK3")

    def test_ck3_a_second_body(self):
        spec(self.record, "Shell_Walls_Add")["op"] = "new"
        self.assertIn("CK3", {f.id for f in run(self.record)})

    def test_ck3_a_reserve_component_holds_new_bodies_only(self):
        self.record["components"][0]["role"] = "reserve"
        self.assertIn("CK3", {f.id for f in run(self.record)})

    def test_ck3_a_pattern_of_an_unknown_seed(self):
        spec(self.record, "Vent_Slot_SlotPat")["seed"] = "Vent_Slot_Nothing"
        self.assertIn("CK3", {f.id for f in run(self.record)})

    def test_ck3_skips_specs_of_phase_enhance(self):
        spec(self.record, "Shell_Walls_Add")["phase"] = "enhance"
        spec(self.record, "Shell_Walls_Add")["op"] = "new"
        self.assertNotIn("CK3", {f.id for f in run(self.record)})


class SetTests(Base):
    def test_ck4_a_flag_without_members(self):
        sets = configs()
        sets["a"]["suppress"]["Ghost_Nothing"] = False
        self.only(run(self.record, sets), "CK4", 1)

    def test_ck4_a_flag_that_names_a_protected_prefix(self):
        self.only(run(self.record, protected_prefixes=("Vent_",)), "CK4")

    def test_ck4_a_flag_that_is_not_owner_and_set(self):
        sets = configs()
        sets["a"]["suppress"]["Vent"] = False
        self.assertIn("CK4", {f.id for f in run(self.record, sets)})

    def test_ck4_a_pattern_and_its_seed_in_two_sets(self):
        spec(self.record, "Vent_Slot_SlotPat")["seed"] = "Patch_Hole_BoreCut"
        self.assertIn("CK4", {f.id for f in run(self.record)})

    def test_ck4_a_feature_fed_by_a_sketch_of_another_set(self):
        spec(self.record, "Shell_Walls_Add")["sketch"] = "Shell_Floor_BodySk"
        self.only(run(self.record), "CK4", 1)


class NumberTests(Base):
    def test_ck5_a_count_below_one(self):
        self.only(run(self.record, configs(V_N_ROWS=0)), "CK5", 1)

    def test_ck5_a_size_that_is_not_positive_even_in_a_suppressed_set(self):
        # V_A = 8 = V_D: the diameter stays positive, the size V_A - V_X of the slot sketch is negative
        findings = run(self.record, configs(V_A=5.0))
        self.assertIn("CK5", {f.id for f in findings})
        self.assertTrue(any(f.name == "Vent_Slot_SlotCutSk" for f in findings if f.id == "CK5"))

    def test_ck5_a_distance_that_is_not_positive(self):
        self.assertIn("CK5", {f.id for f in run(self.record, configs(V_H=0.0))})

    def test_ck5_a_count_that_is_not_whole(self):
        self.only(run(self.record, configs(V_N_ROWS=2.5)), "CK5", 1)

    def test_ck6_an_offset_that_changes_sign(self):
        findings = run(self.record, configs(V_S0=-2.0))
        self.assertEqual([f.id for f in findings], ["CK6"], [str(f) for f in findings])
        self.assertEqual(findings[0].name, "Shell_Walls_Add")

    def test_ck6_an_offset_that_is_zero_but_not_textually_zero(self):
        findings = run(self.record, configs(V_S0=0.0))
        self.assertEqual([f.id for f in findings], ["CK6"], [str(f) for f in findings])

    def test_ck6_a_textually_zero_offset_is_fine(self):
        self.assertEqual([f for f in run(self.record) if f.id == "CK6"], [])


class SketchTests(Base):
    def test_ck7_loops_that_touch_in_a_live_set(self):
        sets = configs(V_GAP=30.0)
        sets["b"]["suppress"] = {f: False for f in FLAGS}
        findings = self.only(run(self.record, sets), "CK7")
        self.assertTrue(all(f.name == "Vent_Slot_SlotCutSk" for f in findings))

    def test_ck7_is_silent_for_a_suppressed_set(self):
        # in b the Vent sets are suppressed: the touching loops of b are not checked, those of a still are fine
        self.assertEqual(run(self.record, configs(V_GAP=30.0)), [])

    def test_ck7_a_hole_that_does_not_lie_inside(self):
        sketch = spec(self.record, "Shell_Walls_AddSk")
        sketch["holes"] = [{"kind": "rect", "args": ["V_X", "V_GAP", "V_X", "V_A"], "phase": "build"}]
        sketch["loops"] = sketch["loops"][:1]
        sketch["loops"][0]["args"] = ["V_X", "V_A", "V_X", "V_A"]
        findings = self.only(run(self.record), "CK7", 2)  # one per configuration
        self.assertEqual({f.name for f in findings}, {"Shell_Walls_AddSk"})

    def test_ck7_loft_sections_with_unequal_vertex_counts(self):
        record = copy.deepcopy(self.record)
        square = {"kind": "polygon", "args": [["V_X", "V_X"], ["V_A", "V_X"], ["V_A", "V_A"], ["V_X", "V_A"]], "phase": "build"}
        triangle = {"kind": "polygon", "args": [["V_X", "V_X"], ["V_A", "V_X"], ["V_A", "V_A"]], "phase": "build"}
        for name, loop in (("Shell_Lid_BodySkA", square), ("Shell_Lid_BodySkB", triangle)):
            record["specs"].append({"spec": "SketchSpec", "name": name, "component": "Base", "on": "origin:XY",
                                    "datum": [None, None], "loops": [loop], "holes": [], "points": [], "lines": [],
                                    "circles": [], "constraints": [], "dims": [], "profiles": 1, "rule": "all", "texts": [],
                                    "phase": "build"})
        record["specs"].append({"spec": "LoftSpec", "name": "Shell_Lid_Body", "component": "Base",
                                "sketches": ["Shell_Lid_BodySkA", "Shell_Lid_BodySkB"], "planes": [], "op": "join",
                                "phase": "build"})
        findings = [f for f in run(record) if f.id == "CK7"]
        self.assertEqual([f.name for f in findings], ["Shell_Lid_Body"])


class RejoinTests(Base):
    def test_ck9_a_rejoin_live_while_its_cut_is_suppressed(self):
        sets = configs()
        sets["b"]["suppress"]["Vent_Plug"] = False
        self.only(run(self.record, sets), "CK9", 1)

    def test_ck9_a_rejoin_without_within(self):
        spec(self.record, "Vent_Plug_PlugRejoin")["within"] = None
        self.only(run(self.record), "CK9", 1)

    def test_ck9_within_that_names_a_join(self):
        spec(self.record, "Vent_Plug_PlugRejoin")["within"] = "Shell_Walls_Add"
        self.only(run(self.record), "CK9", 1)

    def test_ck9_within_that_names_a_later_feature(self):
        specs = self.record["specs"]
        i = next(k for k, s in enumerate(specs) if s.get("name") == "Vent_Plug_PlugRejoin")
        spec(self.record, "Vent_Plug_PlugRejoin")["within"] = "Vent_Plug_PlugRejoin"
        self.assertTrue(i > 0)
        self.only(run(self.record), "CK9", 1)

    def test_ck9_within_on_another_operation(self):
        spec(self.record, "Shell_Walls_Add")["within"] = "Vent_Slot_SlotCut"
        self.only(run(self.record), "CK9", 1)

    def test_ck9_within_in_another_component(self):
        self.record["components"].append({"name": "Lid", "role": "part", "datum": [None, None, None], "phase": "build"})
        spec(self.record, "Vent_Slot_SlotCut")["component"] = "Lid"
        self.assertIn("CK9", {f.id for f in run(self.record)})


class OwnerTests(Base):
    def test_ck11_a_rail_object_outside_a_rail_call(self):
        self.record["shared_calls"][0]["produced"] = []
        findings = self.only(run(self.record), "CK11", 2)  # the sketch and the feature
        self.assertEqual({f.name for f in findings}, {"Rail_Male_FootAdd", "Rail_Male_FootAddSk"})

    def test_ck11_a_neutrik_call_without_a_panel_parent(self):
        self.record["shared_calls"][2]["parent"] = None
        findings = self.only(run(self.record), "CK11", 1)
        self.assertEqual(findings[0].name, "neutrik.d_wall_cut")

    def test_ck11_a_neutrik_call_under_another_builder(self):
        self.record["shared_calls"][2]["parent"] = "rail.male"
        self.only(run(self.record), "CK11", 1)


def call(builder, arguments, placement=(), parent=None):
    return {"builder_id": builder, "arguments": arguments, "placement": list(placement), "produced": [], "parent": parent,
            "phase": "build"}


def record_of(document, *calls):
    return {"document": document, "shared_calls": list(calls)}


class DefinitionTests(unittest.TestCase):
    def setUp(self):
        self.case = record_of("Case", call("rail.female_cut", {"name": "A", "x_mid": "V_X", "width": "V_W"}, ("x_mid",)))

    def test_ck10_equal_definitions_and_different_placement_pass(self):
        other = record_of("Brackets", call("rail.female_cut", {"name": "B", "x_mid": "V_Y", "width": "V_W"}, ("x_mid",)))
        self.assertEqual(checks.definitions([self.case, other]), [])

    def test_ck10_a_definition_argument_that_differs(self):
        other = record_of("Coupons", call("rail.female_cut", {"name": "B", "x_mid": "V_X", "width": "V_D"}, ("x_mid",)))
        findings = checks.definitions([self.case, other])
        self.assertEqual([(f.id, f.name) for f in findings], [("CK10", "rail.female_cut")])
        self.assertIn("'width'", findings[0].text)
        self.assertIn("Case", findings[0].text)
        self.assertIn("Coupons", findings[0].text)

    def test_ck10_the_same_difference_with_a_matching_exception_passes(self):
        other = record_of("Coupons", call("rail.female_cut", {"name": "B", "x_mid": "V_X", "width": "V_D"}, ("x_mid",)))
        for entry in ({"builder": "rail.female_cut", "argument": "width", "reason": "the ladder"}, "rail.female_cut:width"):
            self.assertEqual(checks.definitions([self.case, other], [entry]), [], entry)

    def test_ck10_an_exception_for_another_argument_does_not_help(self):
        other = record_of("Coupons", call("rail.female_cut", {"name": "B", "x_mid": "V_X", "width": "V_D"}, ("x_mid",)))
        self.assertEqual(len(checks.definitions([self.case, other], [{"builder": "rail.female_cut", "argument": "lock_e"}])), 1)
        self.assertEqual(len(checks.definitions([self.case, other], [{"builder": "rail.male", "argument": "width"}])), 1)

    def test_ck10_an_optional_argument_that_one_document_leaves_out_differs(self):
        other = record_of("Coupons", call("rail.female_cut", {"name": "B", "x_mid": "V_X", "width": "V_W", "lock_e": "V_RLOCK_E"},
                                          ("x_mid",)))
        findings = checks.definitions([self.case, other])
        self.assertEqual(len(findings), 1)
        self.assertIn("'lock_e'", findings[0].text)
        self.assertEqual(checks.definitions([self.case, other], ["rail.female_cut:lock_e"]), [])

    def test_ck10_a_malformed_exception_is_refused(self):
        for bad in ("the table of 3.5", [{"builder": "rail.male"}], ["rail.male"], [3]):
            with self.assertRaises(KitError, msg=repr(bad)):
                checks.definitions([self.case], bad)
