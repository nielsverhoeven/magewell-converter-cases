"""Value text, row ordering, set totality."""
import unittest

from cad.fusion.runtime import paramset


class ParamsetTests(unittest.TestCase):
    def test_paramset_helpers(self):
        self.assertEqual(paramset.number_text(60.0), "60")
        self.assertEqual(paramset.number_text(0.1), "0.1")
        self.assertEqual(paramset.number_text(1e-7), "0.0000001")
        self.assertEqual(paramset.value_text(193.9, "mm"), "193.9 mm")
        self.assertEqual(paramset.value_text(3, ""), "3")
        with self.assertRaises(paramset.ParamError):
            paramset.set_texts({"V_N_X": 0}, [{"name": "V_N_X", "unit": "", "kind": "solver", "fusion": None}])
        with self.assertRaises(paramset.ParamError):
            paramset.order_rows([{"name": "A", "unit": "mm", "kind": "expression", "fusion": "B"},
                                 {"name": "B", "unit": "mm", "kind": "expression", "fusion": "A"}])
        with self.assertRaises(paramset.ParamError):
            paramset.order_rows([{"name": "A", "unit": "mm", "kind": "expression", "fusion": "NOPE * 2"}])

    def test_row_checks(self):
        rows = [{"name": "MCC_A", "unit": "mm", "kind": "constant", "fusion": "3.0 mm"},
                {"name": "MCC_B", "unit": "mm", "kind": "expression", "fusion": "max(MCC_A; 2 mm)"},
                {"name": "MCC_C", "unit": "mm", "kind": "expression", "fusion": "16.14 mm"},      # arrived evaluated
                {"name": "V_X", "unit": "mm", "kind": "solver", "fusion": None},
                {"name": "V_N_X", "unit": "", "kind": "solver", "fusion": None}]
        self.assertEqual(paramset.check_rows(rows), [])
        self.assertEqual([r["name"] for r in paramset.order_rows(rows)], [r["name"] for r in rows])
        for bad, text in (({"name": "MCC_D", "unit": "mm", "kind": "constant", "fusion": "MCC_A"}, "must not reference"),
                          ({"name": "MCC_D", "unit": "cm", "kind": "constant", "fusion": "1 cm"}, "unit"),
                          ({"name": "MCC_D", "unit": "mm", "kind": "fixed", "fusion": "1 mm"}, "unknown kind"),
                          ({"name": "V_X", "unit": "mm", "kind": "solver", "fusion": None}, "duplicate"),
                          ({"name": "V_Y", "unit": "mm", "kind": "solver", "fusion": "1 mm"}, "carries no text"),
                          ({"name": "MCC_D", "unit": "mm", "kind": "expression", "fusion": "MCC_A +"}, "MCC_D")):
            problems = paramset.check_rows(rows + [bad])
            self.assertTrue(any(text in p for p in problems), (bad, problems))


if __name__ == "__main__":
    unittest.main()
