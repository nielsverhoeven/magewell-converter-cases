"""Expressions of the modelling kit (plan 3.4): the grammar, the refusal of a literal, the helpers, and the two
wrappers around cad.params (Env, fusion) against a registry of four rows with values worked out by hand.

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import unittest

from ..core import expr
from ..core.names import KitError

NAMES = frozenset({"V_CASE_L", "V_A", "V_B", "MCC_WALL", "MCC_D_FLANGE_X", "MCC_ANGLE", "V_N_VENT", "T_UNIT"})


def row(name, unit, kind, expression, fusion):
    return {"name": name, "unit": unit, "kind": kind, "expression": expression, "fusion": fusion,
            "comment": "", "description": "test row", "src": "test", "conf": None}


# The registry of four rows of plan K1 step 5: a constant, an expression that calls max, an angle, a solver row.
ROWS = [
    row("MCC_WALL", "mm", "constant", "3 mm", "3 mm"),
    row("MCC_WALL2", "mm", "expression", "max(MCC_WALL, 2 mm) * 2", "max(MCC_WALL; 2 mm) * 2"),
    row("MCC_ANGLE", "deg", "constant", "60 deg", "60 deg"),
    row("V_CASE_L", "mm", "solver", None, None),
]


class ValidTests(unittest.TestCase):
    def test_the_examples_of_the_plan_pass(self):
        for text in ("V_CASE_L / 2 - MCC_WALL", "2 * MCC_D_FLANGE_X", "V_A", "-V_A", "(V_A + V_B) / 2", "V_A * 2 - V_B",
                     "min(V_A, V_B)", "max(V_A, V_B + MCC_WALL)", "MCC_WALL * sin(MCC_ANGLE)", "V_A * 2 * 3",
                     "V_A / 2 / 2", "  V_A  +  V_B  ", "V_A * 1.5", "V_A * .5"):
            with self.subTest(text):
                expr.check(text, NAMES)

    def test_a_name_is_valid_whatever_it_starts_with(self):
        expr.check("T_UNIT + Anything_Goes", NAMES | {"Anything_Goes"})


class TypeTests(unittest.TestCase):
    def test_a_number_is_a_type_error(self):
        for bad in (3, 3.5, None, ["V_A"], ("V_A",)):
            with self.subTest(repr(bad)):
                with self.assertRaises(TypeError):
                    expr.check(bad, NAMES)


class LiteralTests(unittest.TestCase):
    def test_the_four_examples_that_must_fail(self):
        for bad in ("3", "3 mm", "V_CASE_L - 1", "max(V_A, 0)"):
            with self.subTest(bad):
                with self.assertRaises(expr.LiteralError):
                    expr.check(bad, NAMES)

    def test_more_literals(self):
        for bad in ("3.5", "-3", "(3)", "2 * 3", "2 * 3 / 4", "1 + V_A", "V_A + 1", "1 - V_A", "V_A * 3 mm", "2mm",
                    "60 deg", "V_A * 60 deg", "min(V_A, 2)", "max(2, V_A)", "sin(30)", "V_A * (2)", "V_A / -2",
                    "-2 * V_A", "V_A * (2 + V_B)"):
            with self.subTest(bad):
                with self.assertRaises(expr.LiteralError):
                    expr.check(bad, NAMES)

    def test_a_factor_of_a_name_is_fine(self):
        for ok in ("2 * V_A", "V_A * 2", "V_A / 2", "2 * V_A * 3", "V_A * 2 + V_B", "V_A * 2 - V_B / 4"):
            with self.subTest(ok):
                expr.check(ok, NAMES)

    def test_literal_error_is_a_kit_error(self):
        self.assertTrue(issubclass(expr.LiteralError, KitError))


class UnknownNameTests(unittest.TestCase):
    def test_a_name_outside_the_registry(self):
        with self.assertRaises(expr.UnknownNameError) as ctx:
            expr.check("V_A + V_NOPE", NAMES)
        self.assertIn("V_NOPE", str(ctx.exception))

    def test_a_function_name_without_call_is_an_unknown_name(self):
        with self.assertRaises(expr.UnknownNameError):
            expr.check("max + V_A", NAMES)

    def test_the_registry_may_be_any_container(self):
        expr.check("V_A", {"V_A": 1})
        expr.check("V_A", ["V_A"])


class GrammarTests(unittest.TestCase):
    def test_forbidden_functions_and_tokens(self):
        for bad in ("floor(V_A)", "ceil(V_A)", "round(V_A)", "if(V_A, V_B)", "sqrt(V_A)", "V_A ^ 2", "V_A < V_B",
                    "V_A == V_B", "V_A > 2", "'V_A'", '"V_A"', "V_A % 2", "V_A; V_B", "abs(V_A)", "V_A[0]"):
            with self.subTest(bad):
                with self.assertRaises(expr.GrammarError):
                    expr.check(bad, NAMES)

    def test_malformed(self):
        for bad in ("", "   ", "V_A +", "* V_A", "V_A V_B", "(V_A", "V_A)", "max()", "max(V_A,)", "max(V_A V_B)",
                    "sin(V_A, V_B)", "V_A 2", "()", "V_A + * V_B"):
            with self.subTest(bad):
                with self.assertRaises(expr.GrammarError):
                    expr.check(bad, NAMES)

    def test_grammar_is_reported_before_literals_and_names(self):
        with self.assertRaises(expr.GrammarError):
            expr.check("floor(3) + V_NOPE", NAMES)
        with self.assertRaises(expr.LiteralError):
            expr.check("V_NOPE - 1", NAMES)

    def test_the_message_names_the_feature_the_argument_and_the_token(self):
        with self.assertRaises(expr.LiteralError) as ctx:
            expr.check("V_CASE_L - 1", NAMES, "Cradle_Deck_FrameAdd.start")
        self.assertIn("Cradle_Deck_FrameAdd.start", str(ctx.exception))
        self.assertIn("1", str(ctx.exception))
        with self.assertRaises(expr.GrammarError) as ctx:
            expr.check("floor(V_A)", NAMES, "Shell_Walls_Add.end")
        self.assertIn("Shell_Walls_Add.end", str(ctx.exception))
        self.assertIn("floor", str(ctx.exception))
        with self.assertRaises(expr.UnknownNameError) as ctx:
            expr.check("V_NOPE", NAMES, "Fan_Bay_Cut.d")
        self.assertIn("Fan_Bay_Cut.d", str(ctx.exception))
        self.assertIn("V_NOPE", str(ctx.exception))


class NamesInTests(unittest.TestCase):
    def test_names_in(self):
        self.assertEqual(expr.names_in("max(V_A, V_B + MCC_WALL) * 2 - -V_A"), {"V_A", "V_B", "MCC_WALL"})
        self.assertEqual(expr.names_in("2 * 3"), set())

    def test_names_in_raises_on_bad_grammar(self):
        with self.assertRaises(expr.GrammarError):
            expr.names_in("floor(V_A)")


class SameTests(unittest.TestCase):
    def test_equal_after_dropping_outer_parentheses(self):
        self.assertTrue(expr.same("V_A + V_B", "(V_A + V_B)"))
        self.assertTrue(expr.same("((V_A))", "V_A"))
        self.assertTrue(expr.same("V_A+V_B", "V_A + V_B"))

    def test_inner_parentheses_matter(self):
        self.assertFalse(expr.same("(V_A) + (V_B)", "V_A + V_B"))
        self.assertFalse(expr.same("(V_A + V_B) * 2", "V_A + V_B * 2"))
        self.assertTrue(expr.same("(V_A + V_B) * 2", "(V_A + V_B) * 2"))

    def test_different_texts(self):
        self.assertFalse(expr.same("V_A", "V_B"))
        self.assertFalse(expr.same("V_A + V_B", "V_B + V_A"))

    def test_none_equals_none_only(self):
        self.assertTrue(expr.same(None, None))
        self.assertFalse(expr.same(None, "V_A"))
        self.assertFalse(expr.same("V_A", None))

    def test_a_non_string_is_a_type_error(self):
        with self.assertRaises(TypeError):
            expr.same(3, "V_A")


class HelperTests(unittest.TestCase):
    """The helpers are pure string functions; every result is valid and, evaluated, means what it says."""

    def test_add(self):
        self.assertEqual(expr.add("V_A", "V_B"), "V_A + V_B")
        self.assertEqual(expr.add("V_A", "V_B", "MCC_WALL"), "V_A + V_B + MCC_WALL")
        self.assertEqual(expr.add(None, "V_X"), "V_X")
        self.assertEqual(expr.add("V_X", None), "V_X")
        self.assertIsNone(expr.add(None, None))
        self.assertIsNone(expr.add())

    def test_sub(self):
        self.assertEqual(expr.sub("V_A", "V_B"), "V_A - V_B")
        self.assertEqual(expr.sub(None, "V_X"), "-(V_X)")
        self.assertEqual(expr.sub("V_X", None), "V_X")
        self.assertIsNone(expr.sub(None, None))
        self.assertEqual(expr.sub("V_A", "V_B + V_C"), "V_A - (V_B + V_C)")
        self.assertEqual(expr.sub("V_A", "V_B - V_C"), "V_A - (V_B - V_C)")
        self.assertEqual(expr.sub("V_A", "V_B * 2"), "V_A - V_B * 2")
        self.assertEqual(expr.sub("V_A + V_C", "V_B"), "V_A + V_C - V_B")

    def test_neg(self):
        self.assertEqual(expr.neg("V_A"), "-(V_A)")
        self.assertEqual(expr.neg("V_A + V_B"), "-(V_A + V_B)")

    def test_mul_and_div_add_the_parentheses_that_are_needed(self):
        self.assertEqual(expr.mul("V_A", "V_B"), "V_A * V_B")
        self.assertEqual(expr.mul("V_A + V_B", "V_C"), "(V_A + V_B) * V_C")
        self.assertEqual(expr.mul("V_A", "V_B - V_C"), "V_A * (V_B - V_C)")
        self.assertEqual(expr.mul("max(V_A, V_B)", "V_C / 2"), "max(V_A, V_B) * V_C / 2")
        self.assertEqual(expr.div("V_A", "V_B"), "V_A / V_B")
        self.assertEqual(expr.div("V_A + V_B", "2"), "(V_A + V_B) / 2")
        self.assertEqual(expr.div("V_A", "V_B * V_C"), "V_A / (V_B * V_C)")
        self.assertEqual(expr.div("V_A", "V_B / V_C"), "V_A / (V_B / V_C)")
        self.assertEqual(expr.div("V_A", "(V_B + V_C)"), "V_A / (V_B + V_C)")
        self.assertEqual(expr.div("V_A", "V_B + V_C"), "V_A / (V_B + V_C)")

    def test_half_twice_min_max(self):
        self.assertEqual(expr.half("V_A"), "V_A / 2")
        self.assertEqual(expr.half("V_A + V_B"), "(V_A + V_B) / 2")
        self.assertEqual(expr.twice("V_A"), "V_A * 2")
        self.assertEqual(expr.twice("V_A - V_B"), "(V_A - V_B) * 2")
        self.assertEqual(expr.mn("V_A", "V_B"), "min(V_A, V_B)")
        self.assertEqual(expr.mx("V_A", "V_B + V_C"), "max(V_A, V_B + V_C)")

    def test_a_none_is_zero_only_in_add_and_sub(self):
        for fn in (expr.neg, expr.half, expr.twice):
            with self.subTest(fn.__name__):
                with self.assertRaises(TypeError):
                    fn(None)
        for fn in (expr.mul, expr.div, expr.mn, expr.mx):
            with self.subTest(fn.__name__):
                with self.assertRaises(TypeError):
                    fn(None, "V_A")

    def test_a_number_is_a_type_error(self):
        with self.assertRaises(TypeError):
            expr.add("V_A", 3)
        with self.assertRaises(TypeError):
            expr.sub("V_A", 1.5)

    def test_every_result_passes_the_check_and_means_what_it_says(self):
        env = expr.Env(ROWS, {"V_CASE_L": 200.0})
        a, b, c = "V_CASE_L", "MCC_WALL", "MCC_WALL2"  # 200, 3, 6
        cases = [
            (expr.add(a, b, c), 209),
            (expr.sub(a, expr.add(b, c)), 191),
            (expr.sub(a, expr.sub(b, c)), 203),
            (expr.sub(expr.add(a, b), c), 197),
            (expr.sub(None, a), -200),
            (expr.neg(expr.add(b, c)), -9),
            (expr.mul(expr.add(b, c), b), 27),
            (expr.mul(b, expr.sub(a, c)), 582),
            (expr.div(a, expr.mul(b, c)), 200 / 18),
            (expr.div(a, expr.div(c, b)), 100),
            (expr.div(expr.sub(a, b), c), 197 / 6),
            (expr.half(expr.add(a, b)), 101.5),
            (expr.twice(expr.sub(a, b)), 394),
            (expr.mn(a, expr.add(b, c)), 9),
            (expr.mx(a, expr.add(b, c)), 200),
        ]
        for text, want in cases:
            with self.subTest(text):
                expr.check(text, env.names)
                self.assertAlmostEqual(env.value(text), want, places=9)


class EnvTests(unittest.TestCase):
    """Env and fusion against the registry of four rows; every number is worked out by hand:
    MCC_WALL = 3, MCC_WALL2 = max(3, 2) * 2 = 6, MCC_ANGLE = 60 deg, V_CASE_L = 200."""

    def setUp(self):
        self.env = expr.Env(ROWS, {"V_CASE_L": 200.0})

    def test_names(self):
        self.assertEqual(self.env.names, frozenset({"MCC_WALL", "MCC_WALL2", "MCC_ANGLE", "V_CASE_L"}))
        self.assertIsInstance(self.env.names, frozenset)

    def test_units_hold_the_solver_rows_only(self):
        self.assertEqual(self.env.units, {"V_CASE_L": "mm"})

    def test_values(self):
        self.assertEqual(self.env.value("MCC_WALL"), 3.0)
        self.assertEqual(self.env.value("MCC_WALL2"), 6.0)
        self.assertEqual(self.env.value("V_CASE_L / 2 - MCC_WALL"), 97.0)
        self.assertEqual(self.env.value("MCC_WALL2 + V_CASE_L"), 206.0)
        self.assertEqual(self.env.value("2 * MCC_WALL - V_CASE_L / 4"), -44.0)
        self.assertEqual(self.env.value("max(MCC_WALL, MCC_WALL2)"), 6.0)
        self.assertEqual(self.env.value("min(V_CASE_L, MCC_WALL2 * 10)"), 60.0)

    def test_the_angle_row(self):
        self.assertAlmostEqual(self.env.value("MCC_ANGLE"), 60.0, places=9)
        self.assertAlmostEqual(self.env.value("MCC_WALL * sin(MCC_ANGLE)"), 3 * 0.8660254037844386, places=9)
        self.assertAlmostEqual(self.env.value("V_CASE_L * cos(MCC_ANGLE)"), 100.0, places=9)

    def test_values_may_be_a_second_parameter_set(self):
        other = expr.Env(ROWS, {"V_CASE_L": 300.0})
        self.assertEqual(other.value("V_CASE_L / 2 - MCC_WALL"), 147.0)
        self.assertEqual(self.env.value("V_CASE_L / 2 - MCC_WALL"), 97.0)

    def test_env_does_not_keep_the_values_dict(self):
        values = {"V_CASE_L": 200.0}
        env = expr.Env(ROWS, values)
        values["V_CASE_L"] = 1.0
        self.assertEqual(env.value("V_CASE_L"), 200.0)


class FusionTests(unittest.TestCase):
    def test_the_argument_separator_becomes_a_semicolon(self):
        self.assertEqual(expr.fusion("max(MCC_WALL, 2 mm)"), "max(MCC_WALL; 2 mm)")
        self.assertEqual(expr.fusion("min(V_A, max(V_B, V_C))"), "min(V_A; max(V_B; V_C))")

    def test_an_expression_without_a_call_is_unchanged(self):
        self.assertEqual(expr.fusion("V_CASE_L / 2 - MCC_WALL"), "V_CASE_L / 2 - MCC_WALL")
        self.assertEqual(expr.fusion("-(V_X)"), "-(V_X)")

    def test_a_non_string_is_a_type_error(self):
        with self.assertRaises(TypeError):
            expr.fusion(3)


if __name__ == "__main__":
    unittest.main()
