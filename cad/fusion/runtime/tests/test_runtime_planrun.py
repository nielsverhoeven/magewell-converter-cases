"""The offline plan run: the one writer of a committed inventory and the freshness check."""
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from cad.fusion.runtime import planrun, registry, runner
from cad.fusion.runtime.tests import runtime_support as support

PLAN = "cad/fusion/runtime/testdoc/plan.json"
INVENTORY = "cad/fusion/runtime/testdoc/inventory.json"


class PlanRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mcc-planrun-")
        self.checkout = support.make_checkout(self.tmp)
        self.file = os.path.join(self.checkout, *INVENTORY.split("/"))
        if os.path.exists(self.file):
            os.remove(self.file)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_status_write_and_update(self):
        status = planrun.inventory_status(self.checkout, PLAN)
        self.assertEqual((status["exists"], status["fresh"], status["committed_sha256"]), (False, False, None))
        self.assertEqual(status["path"], INVENTORY)
        self.assertEqual(len(status["recorded_sha256"]), 64)

        written = planrun.write_inventory(self.checkout, PLAN)
        self.assertTrue(written["exists"] and written["fresh"])
        self.assertEqual(written["committed_sha256"], written["recorded_sha256"])
        with open(self.file, "rb") as fh:
            original = fh.read()
        self.assertNotIn(b"\r", original)
        self.assertTrue(planrun.record(self.checkout, PLAN)["ok"])

        with open(self.file, "wb") as fh:                                   # the builder moved on, the file did not
            fh.write(original.replace(b'"Test_Block_Extrude"', b'"Test_Block_Extrude2"'))
        stale = planrun.inventory_status(self.checkout, PLAN)
        self.assertFalse(stale["fresh"])
        self.assertTrue(any("Test_Block_Extrude" in line for line in stale["diff"]), stale["diff"])
        failed = planrun.record(self.checkout, PLAN)
        self.assertFalse(failed["ok"])
        self.assertIn("inventory_committed", " ".join(failed["violations"]))

        again = planrun.write_inventory(self.checkout, PLAN)                # the writer replaces a stale file
        self.assertTrue(again["fresh"])
        with open(self.file, "rb") as fh:
            self.assertEqual(fh.read(), original)

    def test_a_file_that_is_no_inventory(self):
        support.write(self.file, "{not json")
        status = planrun.inventory_status(self.checkout, PLAN)
        self.assertFalse(status["fresh"])
        self.assertIn("not a valid inventory", status["diff"][0])

    def test_refusals(self):
        path = os.path.join(self.checkout, *PLAN.split("/"))
        with open(path, encoding="utf-8") as fh:
            plan = json.load(fh)
        del plan["inventory"]
        support.write(path, json.dumps(plan))
        with self.assertRaises(planrun.PlanRunError) as cm:
            planrun.write_inventory(self.checkout, PLAN)
        self.assertIn("names no inventory file", str(cm.exception))
        self.assertEqual(planrun.inventory_status(self.checkout, PLAN)["path"], None)

        plan["inventory"] = INVENTORY
        plan["owners"] = ["Test"]                                           # the Reserve items now fail a gate
        support.write(path, json.dumps(plan))
        with self.assertRaises(planrun.PlanRunError) as cm:
            planrun.write_inventory(self.checkout, PLAN)
        self.assertIn("owner 'Reserve'", " ".join(cm.exception.violations))
        self.assertFalse(os.path.exists(self.file))
        self.assertFalse(planrun.inventory_status(self.checkout, PLAN)["exists"])     # status needs no gate

    def test_a_plan_that_is_not_valid_is_a_plan_run_error(self):
        path = os.path.join(self.checkout, *PLAN.split("/"))
        with open(path, encoding="utf-8") as fh:
            plan = json.load(fh)
        plan["protected_prefix"] = ["Reserve_"]                              # a misspelt key
        support.write(path, json.dumps(plan))
        for call in (planrun.record, planrun.inventory_status, planrun.write_inventory):
            with self.assertRaises(planrun.PlanRunError) as cm:
                call(self.checkout, PLAN)
            self.assertEqual(cm.exception.stage, "plan")
            self.assertIn("unknown key(s): protected_prefix", str(cm.exception))

    def test_record_and_run_forget_what_cad_params_cached(self):
        calls = []
        real = registry.reset
        with mock.patch.object(registry, "reset", side_effect=lambda: (calls.append("reset"), real())):
            planrun.record(self.checkout, PLAN)
            self.assertEqual(calls, ["reset"])
            job = {"kind": "build", "job_id": "job1", "checkout": self.checkout,
                   "args": {"plan": PLAN, "backend": "recording"}}
            self.assertTrue(runner.run(job)["ok"])
            self.assertEqual(calls, ["reset", "reset"])

    def test_a_cached_parameter_file_does_not_outlive_a_run(self):
        import cad.params
        cad.params.constants()
        self.assertGreater(cad.params._constants_cached.cache_info().currsize, 0)
        planrun.record(self.checkout, PLAN)
        self.assertEqual(cad.params._constants_cached.cache_info().currsize, 0)


if __name__ == "__main__":
    unittest.main()
