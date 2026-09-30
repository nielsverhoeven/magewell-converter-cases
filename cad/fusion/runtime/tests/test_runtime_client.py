"""The offline commands of scripts/fusion_run.py (plan, digest), run as a process in a throw-away checkout."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from cad.fusion.runtime.tests import runtime_support as support

PLAN = "cad/fusion/runtime/testdoc/plan.json"
INVENTORY = "cad/fusion/runtime/testdoc/inventory.json"


class ClientOffline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mcc-client-")
        self.checkout = support.make_checkout(self.tmp)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.inventory = os.path.join(self.checkout, *INVENTORY.split("/"))
        if os.path.exists(self.inventory):
            os.remove(self.inventory)

    def client(self, *args):
        """(exit code, parsed stdout or None, stderr) of the checkout's own copy of the client."""
        p = subprocess.run([sys.executable, "-B", os.path.join(self.checkout, "scripts", "fusion_run.py"), *args],
                           capture_output=True, text=True, timeout=120, cwd=self.checkout)
        return p.returncode, json.loads(p.stdout) if p.stdout.strip() else None, p.stderr

    def test_plan_records_the_test_document(self):
        code, out, err = self.client("plan", PLAN)
        self.assertEqual(code, 0, err)
        self.assertEqual((out["ok"], out["result"], out["document"]), (True, "recorded", "MCC-RuntimeTest"))
        self.assertIsNone(out["run_dir"])
        self.assertNotIn("inventory_text", out)
        self.assertFalse(os.path.exists(os.path.join(self.checkout, "exports")))         # recording writes nothing

    def test_write_inventory_then_stale_then_written_again(self):
        code, out, err = self.client("plan", PLAN, "--write-inventory")
        self.assertEqual(code, 0, err)
        self.assertEqual(out["inventory_written"], INVENTORY)
        with open(self.inventory, "rb") as fh:
            original = fh.read()
        self.assertEqual(sum(1 for line in original.decode("utf-8").splitlines() if line.lstrip().startswith('{"kind"')), 12)
        with open(self.inventory, "wb") as fh:
            fh.write(original.replace(b'"Test_Block_Extrude"', b'"Test_Block_Extrude2"'))
        code, out, err = self.client("plan", PLAN)
        self.assertEqual(code, 1)
        self.assertEqual((out["ok"], out["stage"]), (False, "gates in configuration runtime-test/a"))
        self.assertIn("inventory_committed", " ".join(out["violations"]))
        code, out, err = self.client("plan", PLAN, "--write-inventory")
        self.assertEqual(code, 0, err)
        with open(self.inventory, "rb") as fh:
            self.assertEqual(fh.read(), original)

    def test_a_plan_that_lacks_inputs_exits_1(self):
        path = os.path.join(self.checkout, *PLAN.split("/"))
        with open(path, encoding="utf-8") as fh:
            plan = json.load(fh)
        plan["inputs"] = ["cad/__init__.py"]                                # no cad/fusion/__init__.py, no testdoc
        support.write(path, json.dumps(plan))
        code, out, err = self.client("plan", PLAN)
        self.assertEqual(code, 1)
        self.assertEqual((out["ok"], out["stage"]), (False, "inputs"))
        self.assertTrue(any("cad/fusion/runtime/testdoc/builder.py" in v for v in out["violations"]), out["violations"])

    def test_an_invalid_plan_exits_1(self):
        path = os.path.join(self.checkout, *PLAN.split("/"))
        with open(path, encoding="utf-8") as fh:
            plan = json.load(fh)
        plan["protected_prefix"] = []
        support.write(path, json.dumps(plan))
        code, out, err = self.client("plan", PLAN)
        self.assertEqual(code, 1)
        self.assertEqual(out["stage"], "plan")

    def test_digest(self):
        code, out, err = self.client("digest", PLAN)
        self.assertEqual(code, 0, err)
        self.assertEqual(out["algorithm"], "sha256-lf-v1")
        self.assertRegex(out["value"], r"^[0-9a-f]{64}$")
        again = self.client("digest", PLAN)[1]
        self.assertEqual(again, out)

    def test_a_plan_outside_the_checkout_is_a_usage_error(self):
        code, out, err = self.client("plan", os.path.join(self.tmp, "nowhere.json"))
        self.assertEqual(code, 2)
        self.assertIn("usage error", err)


if __name__ == "__main__":
    unittest.main()
