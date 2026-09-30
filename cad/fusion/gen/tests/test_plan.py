"""The command line of the kit (plan 3.13, K3 step 2) on small synthetic plans: ``--document --check``, ``--stage``,
``--record`` (only under ``build/``) and ``--definitions`` with ``shared_exceptions``.

There are no product builders yet, so the plans here use ``synthetic_doc`` as the builder.  That module lies under
``cad.fusion.gen.tests`` and is therefore a *test document*; the CK10 tests that need a product document patch the
prefix (``plan.TEST_MODULE_PREFIX``).  The commands run in a temporary directory, like the real command runs at the
repository root; everything that is imported lazily is imported here first, so that changing the directory breaks no import.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cad import params  # noqa: F401  (imported before the tests change the working directory)

from ..core import plan
from . import synthetic_doc  # noqa: F401

CSV = "name,unit,expression,comment\nMCC_WALL,mm,3.0 mm,test row\n"
SET = {"schema": 1, "configurations": {"default": {
    "parameters": {"V_X": "10 mm", "V_L": "100 mm", "V_W": "60 mm", "V_H": "20 mm"},
    "flags": {"Shell_Floor": False, "Rail_Male": False}}}}


class PlanCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        previous = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        (self.root / "constants.csv").write_text(CSV, encoding="utf-8")
        (self.root / "set.json").write_text(json.dumps(SET), encoding="utf-8")

    def write_plan(self, name="doc.json", document="Doc", options=None, **over):
        body = {"schema": 1, "document": document,
                "builder": {"module": "cad.fusion.gen.tests.synthetic_doc", "entry": "build", "options": options or {}},
                "registry": {"source": "cad.params", "csv": ["constants.csv"], "sets": ["set.json"]},
                "build_configuration": "default",
                "configurations": [{"id": "default", "set": {"file": "set.json", "config": "default"}, "exports": []}],
                "owners": ["Shell", "Rail"], "required_components": [], "protected_prefixes": [], "shared_exceptions": []}
        body.update(over)
        (self.root / name).write_text(json.dumps(body), encoding="utf-8")
        return name

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = plan.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class DocumentTests(PlanCase):
    def test_a_clean_document_has_no_finding(self):
        code, out, _ = self.run_main("--document", self.write_plan(), "--check")
        self.assertEqual(code, 0, out)
        self.assertIn("no findings", out)

    def test_without_check_the_document_is_only_recorded(self):
        code, out, _ = self.run_main("--document", self.write_plan())
        self.assertEqual((code, "recorded" in out), (0, True))

    def test_a_finding_gives_exit_code_1_and_names_the_check(self):
        code, out, _ = self.run_main("--document", self.write_plan(options={"stray_rail": True}), "--check")
        self.assertEqual(code, 1)
        self.assertIn("CK11 Rail_Stray_FootAdd", out)

    def test_the_owners_of_the_plan_reach_ck1(self):
        code, out, _ = self.run_main("--document", self.write_plan(owners=["Shell"]), "--check")
        self.assertEqual(code, 1)
        self.assertIn("CK1 ", out)

    def test_the_record_carries_the_plan_the_options_and_the_stage(self):
        self.write_plan(options={"width": "V_W"})
        code, _, _ = self.run_main("--document", "doc.json", "--stage", "5", "--record", "build/fusion/doc/record.json")
        self.assertEqual(code, 0)
        record = json.loads((self.root / "build/fusion/doc/record.json").read_text(encoding="utf-8"))
        self.assertEqual((record["plan"], record["document"], record["options"]), ("doc.json", "Doc", {"width": "V_W", "stage": 5}))
        self.assertEqual({"schema", "api", "document", "components", "specs", "shared_calls", "plan", "options"}, set(record))

    def test_a_stage_that_is_not_a_number_stays_text(self):
        self.write_plan()
        self.run_main("--document", "doc.json", "--stage", "B10", "--record", "build/r.json")
        self.assertEqual(json.loads((self.root / "build/r.json").read_text(encoding="utf-8"))["options"]["stage"], "B10")

    def test_a_record_outside_build_is_refused_and_not_written(self):
        self.write_plan()
        for path in ("record.json", "../record.json", "buildx/record.json", "build/../record.json"):
            code, _, err = self.run_main("--document", "doc.json", "--record", path)
            self.assertEqual(code, 2, path)
            self.assertIn("build/", err)
        self.assertFalse((self.root / "record.json").exists())
        self.assertFalse((self.root.parent / "record.json").exists())

    def test_a_registry_source_other_than_cad_params_is_refused(self):
        code, _, err = self.run_main("--document", self.write_plan(registry={"source": "inline", "rows": []}))
        self.assertEqual(code, 2)
        self.assertIn("cad.params", err)

    def test_a_missing_plan_or_key_is_an_unusable_plan(self):
        self.assertEqual(self.run_main("--document", "nothing.json")[0], 2)
        self.write_plan("bad.json", builder=None)
        self.assertEqual(self.run_main("--document", "bad.json")[0], 2)

    def test_a_builder_that_cannot_be_imported_is_an_unusable_plan(self):
        code, _, err = self.run_main("--document", self.write_plan(builder={"module": "cad.fusion.gen.tests.nothing", "entry": "build"}))
        self.assertEqual(code, 2)
        self.assertIn("builder", err)

    def test_a_builder_that_misuses_the_kit_fails_with_exit_code_1(self):
        code, _, err = self.run_main("--document", self.write_plan(options={"misuse": True}), "--check")
        self.assertEqual(code, 1)
        self.assertIn("PhaseError", err)

    def test_an_entry_that_does_not_exist_is_an_unusable_plan(self):
        code, _, _ = self.run_main("--document", self.write_plan(builder={
            "module": "cad.fusion.gen.tests.synthetic_doc", "entry": "nothing_here"}))
        self.assertEqual(code, 2)

    def test_the_kit_is_restored_after_a_build(self):
        from ..core import facade
        original = facade.Kit.__init__
        self.run_main("--document", self.write_plan())
        self.assertIs(facade.Kit.__init__, original)

    def test_the_options_are_exclusive(self):
        for argv in ([], ["--check"], ["--document", "a.json", "--definitions"], ["--definitions", "--check"]):
            with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(io.StringIO()):
                plan.main(argv)
            self.assertEqual(caught.exception.code, 2, argv)


class DefinitionTests(PlanCase):
    def product(self):
        return mock.patch.object(plan, "TEST_MODULE_PREFIX", "product.")

    def two(self, second_options, second_exceptions=()):
        self.write_plan("a.json", document="Case", options={"width": "V_W"})
        self.write_plan("b.json", document="Coupons", options=second_options, shared_exceptions=list(second_exceptions))

    def test_test_documents_are_exempt(self):
        self.two({"width": "V_H"})
        self.assertTrue(plan.is_test_document(plan.load_plan("a.json")))
        code, out, _ = self.run_main("--definitions", "a.json", "b.json")
        self.assertEqual(code, 0, out)

    def test_no_plan_at_all_passes(self):
        self.assertEqual(self.run_main("--definitions")[0], 0)

    def test_equal_definitions_pass(self):
        self.two({"width": "V_W"})
        with self.product():
            code, out, _ = self.run_main("--definitions", "a.json", "b.json")
        self.assertEqual(code, 0, out)

    def test_a_definition_that_differs_fails(self):
        self.two({"width": "V_H"})
        with self.product():
            code, out, _ = self.run_main("--definitions", "a.json", "b.json")
        self.assertEqual(code, 1)
        self.assertIn("CK10 rail.male", out)

    def test_a_shared_exception_of_one_plan_covers_the_difference(self):
        self.two({"width": "V_H"}, [{"builder": "rail.male", "argument": "width"}])
        with self.product():
            code, out, _ = self.run_main("--definitions", "a.json", "b.json")
        self.assertEqual(code, 0, out)

    def test_a_shared_exceptions_entry_that_is_not_a_list_is_an_unusable_plan(self):
        self.write_plan("a.json", shared_exceptions="the table of 3.5")
        with self.product():
            self.assertEqual(self.run_main("--definitions", "a.json")[0], 2)
