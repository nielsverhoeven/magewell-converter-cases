"""Expression grammar, normal form, references, violations."""
import unittest

from cad.fusion.runtime import expr


class ExprTests(unittest.TestCase):
    def test_normal_form(self):
        cases = {
            "MCC_WALL*2+V_CASE_L": "MCC_WALL * 2 + V_CASE_L",
            "  V_CASE_L /2 ": "V_CASE_L / 2",
            "( V_CASE_L / 2 )": "V_CASE_L / 2",
            "(MCC_A + MCC_B) / 2": "(MCC_A + MCC_B) / 2",
            "MCC_A - (MCC_B - MCC_C)": "MCC_A - (MCC_B - MCC_C)",
            "MCC_A - (MCC_B + MCC_C)": "MCC_A - (MCC_B + MCC_C)",
            "MCC_A + (MCC_B + MCC_C)": "MCC_A + MCC_B + MCC_C",
            "MCC_A / (MCC_B * MCC_C)": "MCC_A / (MCC_B * MCC_C)",
            "MCC_A * (MCC_B * MCC_C)": "MCC_A * MCC_B * MCC_C",
            "max(MCC_A;MCC_B)": "max(MCC_A; MCC_B)",
            "max( MCC_A , MCC_B )": "max(MCC_A; MCC_B)",
            "-MCC_A": "-MCC_A",
            "-(MCC_A + MCC_B)": "-(MCC_A + MCC_B)",
            "MCC_H / tan( MCC_ANGLE )": "MCC_H / tan(MCC_ANGLE)",
            "3.0 mm": "3 mm",
            "3.50mm": "3.5 mm",
            "0.250": "0.25",
            "1e1": "10",
            "45.0 deg": "45 deg",
            "MCC_A * 1.50": "MCC_A * 1.5",
            "+MCC_A": "MCC_A",
        }
        for src, want in cases.items():
            self.assertEqual(expr.normalise(src), want, src)
            self.assertEqual(expr.normalise(want), want, "idempotent: " + want)

    def test_references_and_literal(self):
        self.assertEqual(expr.references("max(MCC_A; MCC_B) / 2 - V_X"), ["MCC_A", "MCC_B", "V_X"])
        self.assertEqual(expr.references("3 mm"), [])
        self.assertTrue(expr.is_literal("2 * 1.5 mm"))
        self.assertFalse(expr.is_literal("MCC_A"))

    def test_violations(self):
        ok = ["MCC_A", "V_CASE_L / 2", "2 * MCC_A", "(MCC_A + MCC_B) / 2", "max(MCC_A; MCC_B)",
              "MCC_H / tan(MCC_ANGLE)", "-MCC_A", "MCC_A * MCC_RATIO"]
        for e in ok:
            self.assertEqual(expr.violations(e), [], e)
        bad = {"3 mm": "bare number", "MCC_A + 2": "as a dimension", "MCC_A + 2 mm": "as a dimension",
               "floor(MCC_A)": "forbidden", "if(MCC_A; 1; 2)": "forbidden", "sqrt(MCC_A)": "not in the allowed",
               "MCC_A * 5 mm": "carries a unit", "MCC_A + 1 in": "not allowed", "MCC_A ^ 2": "unexpected",
               "MCC_A +": "unexpected", "min(MCC_A; 5 mm)": "as a dimension", "": "empty"}
        for e, needle in bad.items():
            v = expr.violations(e)
            self.assertTrue(v and any(needle in x for x in v), (e, v))

    def test_errors(self):
        for e in ["MCC_A $ 2", "(MCC_A", "MCC_A)", "max(MCC_A"]:
            with self.assertRaises(expr.ExprError):
                expr.parse(e)


if __name__ == "__main__":
    unittest.main()
