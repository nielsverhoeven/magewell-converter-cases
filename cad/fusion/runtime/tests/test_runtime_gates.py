"""Gates that the pipeline tests do not reach: the re-join gate and the numeric fallback of the parameter gate."""
import unittest

from cad.fusion.runtime import gates


def snapshot(cut_suppressed, rejoin_suppressed, order=("Test_Hole_Cut", "Test_Hole_Rejoin")):
    state = {"Test_Hole_Cut": cut_suppressed, "Test_Hole_Rejoin": rejoin_suppressed}
    return {"timeline": [{"index": n, "kind": "feature", "name": name, "suppressed": state[name]}
                         for n, name in enumerate(order)]}


NOTES = {"Test_Hole_Rejoin": {"within": "Test_Hole_Cut"}, "Test_Thread_ModeledThread": {"phase": "enhance"}}


class RejoinGate(unittest.TestCase):
    def test_pass(self):
        for cut, rejoin in ((False, False), (True, True), (False, True)):
            self.assertEqual(gates.gate_rejoin(snapshot(cut, rejoin), NOTES)["status"], "pass", (cut, rejoin))
        self.assertEqual(gates.gate_rejoin(snapshot(True, False), {})["status"], "pass")

    def test_live_rejoin_in_a_suppressed_cut(self):
        result = gates.gate_rejoin(snapshot(True, False), NOTES)
        self.assertEqual(result["status"], "fail")
        self.assertIn("Test_Hole_Rejoin is live while the cut Test_Hole_Cut", result["violations"][0])

    def test_order_and_missing_cut(self):
        result = gates.gate_rejoin(snapshot(False, False, order=("Test_Hole_Rejoin", "Test_Hole_Cut")), NOTES)
        self.assertIn("comes before the cut", result["violations"][0])
        lonely = {"timeline": [{"index": 0, "kind": "feature", "name": "Test_Hole_Rejoin", "suppressed": False}]}
        self.assertIn("which is not in the document", gates.gate_rejoin(lonely, NOTES)["violations"][0])

    def test_it_is_part_of_every_gate_run(self):
        self.assertIn("gate_rejoin", gates.run_all.__code__.co_names)


class ParameterGate(unittest.TestCase):
    ROWS = [{"name": "MCC_A", "unit": "mm", "kind": "constant", "fusion": "3.0 mm"},
            {"name": "MCC_B", "unit": "mm", "kind": "expression", "fusion": "MCC_A * 2"},
            {"name": "MCC_C", "unit": "mm", "kind": "expression", "fusion": "16.139999999999997 mm"},
            {"name": "V_X", "unit": "mm", "kind": "solver", "fusion": None}]

    def run_gate(self, **echo):
        document = {"MCC_A": ("3.00 mm", 3.0), "MCC_B": ("MCC_A * 2", 6.0), "MCC_C": ("16.14 mm", 16.139999999999997),
                    "V_X": ("194.9 mm", 194.9)}
        document.update(echo)
        snapshot = {"user_parameters": [{"name": n, "unit": "mm", "expression": e, "value": v}
                                        for n, (e, v) in document.items()]}
        return gates.gate_parameters(snapshot, self.ROWS, {"V_X": "194.9 mm"})

    def test_a_number_echoed_with_other_digits_passes_by_value(self):
        self.assertEqual(self.run_gate()["status"], "pass")

    def test_a_changed_value_or_expression_fails(self):
        self.assertIn("MCC_C", self.run_gate(MCC_C=("16.2 mm", 16.2))["violations"][0])
        self.assertIn("MCC_B", self.run_gate(MCC_B=("MCC_A * 3", 9.0))["violations"][0])
        self.assertIn("MCC_B", self.run_gate(MCC_B=("6 mm", 6.0))["violations"][0])      # typed over an expression
        self.assertIn("MCC_A", self.run_gate(MCC_A=("MCC_B / 2", 3.0))["violations"][0])  # same value, not the constant


if __name__ == "__main__":
    unittest.main()
