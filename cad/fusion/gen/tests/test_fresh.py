"""Freshness of a committed inventory (plan section 6, K3 step 5, verdict A7).

The kit writes no inventory: the only writer is ``scripts/fusion_run.py plan PLANFILE --write-inventory`` of #79.
This test asks the runtime, ``cad.fusion.runtime.planrun.inventory_status(checkout, plan_rel)``, whether the
committed inventory of each kit plan is still the one its builder produces.

``REQUIRED`` lists the documents whose inventory must exist: ``"MCC-Case"`` since C9 of the case milestones.
``mcc-s1`` names no inventory and is never listed.  A plan without an ``inventory`` key has nothing to compare and is
left out; so is a plan whose inventory file does not exist, unless the document is required.

The runtime is asked in a fresh interpreter (``runtime_status``), never in the process of pytest: the runtime's input-completeness
gate flags every ``cad`` module that the interpreter has loaded and the document does not list among its inputs, and a test session
loads many (the other tests of the kit, the replay, the oracle).  A fresh interpreter loads exactly the modules that
``scripts/fusion_run.py plan`` loads, so the gate stays what it is: this test does not weaken it.  The runtime of #79 must be
there when a plan with an ``inventory`` key exists (the test fails, it does not skip).
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DOCUMENTS = REPO / "cad" / "fusion" / "documents"
REQUIRED = ("MCC-Case",)
KIT_PREFIX = "cad.fusion.gen."
ASK = ("import json, sys; from cad.fusion.runtime import planrun; "
       "print(json.dumps(planrun.inventory_status(sys.argv[1], sys.argv[2])))")


def runtime_status(checkout: Path, plan_rel: str) -> dict:
    """``planrun.inventory_status(checkout, plan_rel)`` computed in a fresh interpreter started in ``checkout``."""
    done = subprocess.run([sys.executable, "-c", ASK, str(checkout), plan_rel], cwd=checkout, capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(f"the runtime could not answer for {plan_rel} (exit {done.returncode}):\n{done.stderr[-2000:]}")
    return json.loads(done.stdout.strip().splitlines()[-1])


def _field(result, key):
    return result[key] if isinstance(result, dict) else getattr(result, key)


def kit_plans(documents: Path = DOCUMENTS) -> list[tuple[str, dict]]:
    """``(document name, plan)`` of every plan whose builder module lies under ``cad.fusion.gen.``, plan file order."""
    out = []
    for path in sorted(documents.glob("*.json")):
        plan = json.loads(path.read_text(encoding="utf-8"))
        if str(plan.get("builder", {}).get("module", "")).startswith(KIT_PREFIX):
            out.append((path, plan))
    return out


def problems(checkout: Path, plans, status, required=REQUIRED) -> list[str]:
    """The reasons a committed inventory is not good: missing while required, or not fresh (with its diff)."""
    found = []
    for path, plan in plans:
        if "inventory" not in plan:
            continue
        result = status(checkout, path.relative_to(checkout).as_posix())
        name = plan.get("document", path.stem)
        if not _field(result, "exists"):
            if name in required:
                found.append(f"{name}: the committed inventory {plan['inventory']} does not exist and is required")
        elif not _field(result, "fresh"):
            found.append(f"{name}: the committed inventory {plan['inventory']} is not fresh\n{_field(result, 'diff')}")
    return found


class FreshTests(unittest.TestCase):
    def test_every_committed_inventory_is_fresh(self):
        plans = kit_plans()
        found = problems(REPO, plans, runtime_status)
        self.assertEqual(found, [], "\n".join(found))

    def test_every_required_document_names_its_inventory_and_has_a_plan(self):
        by_name = {plan.get("document", path.stem): plan for path, plan in kit_plans()}
        for name in REQUIRED:
            self.assertIn(name, by_name)
            self.assertTrue(by_name[name].get("inventory"), f"{name} names no inventory")
            self.assertTrue((REPO / by_name[name]["inventory"]).is_file(), f"{name}: the committed inventory is missing")


class ProblemTests(unittest.TestCase):
    """``problems`` with a stand-in for the runtime."""

    PLAN = Path("cad/fusion/documents/mcc-case.json")

    def ask(self, result, required=(), plan=None):
        plan = {"document": "MCC-Case", "inventory": "cad/fusion/inventory/mcc-case.json"} if plan is None else plan
        calls = []

        def status(checkout, rel):
            calls.append((checkout, rel))
            return result

        found = problems(Path("."), [(Path(".") / self.PLAN, plan)], status, required)
        return found, calls

    def test_a_missing_inventory_is_fine_unless_the_document_is_required(self):
        self.assertEqual(self.ask({"exists": False})[0], [])
        found, _ = self.ask({"exists": False}, required=("MCC-Case",))
        self.assertEqual(len(found), 1)
        self.assertIn("required", found[0])

    def test_a_stale_inventory_fails_with_its_diff(self):
        found, calls = self.ask({"exists": True, "fresh": False, "diff": "+ Shell_New_Add"})
        self.assertEqual(len(found), 1)
        self.assertIn("+ Shell_New_Add", found[0])
        self.assertEqual(calls[0][1], "cad/fusion/documents/mcc-case.json")

    def test_a_fresh_inventory_passes(self):
        self.assertEqual(self.ask({"exists": True, "fresh": True, "diff": ""})[0], [])

    def test_the_answer_may_be_an_object_with_attributes(self):
        from types import SimpleNamespace

        self.assertEqual(len(self.ask(SimpleNamespace(exists=True, fresh=False, diff="d"))[0]), 1)

    def test_a_plan_without_an_inventory_key_is_not_asked(self):
        found, calls = self.ask({"exists": True, "fresh": False, "diff": "x"}, plan={"document": "MCC-S1"})
        self.assertEqual((found, calls), ([], []))

    def test_kit_plans_keeps_the_plans_of_the_kit_only(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.json").write_text(json.dumps({"builder": {"module": "cad.fusion.gen.case.build"}}), encoding="utf-8")
            (Path(tmp) / "b.json").write_text(json.dumps({"builder": {"module": "cad.fusion.runtime.test_doc"}}), encoding="utf-8")
            self.assertEqual([p.name for p, _ in kit_plans(Path(tmp))], ["a.json"])
