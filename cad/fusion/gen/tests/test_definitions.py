"""Shared definitions across documents (CK10; plan section 6, K3 step 4): the real plans of the repository.

``plan.main(["--definitions", ...])`` over every plan under ``cad/fusion/documents/``; the command itself leaves out
the test documents (a builder module under ``cad.fusion.gen.tests``).  Until the first product plan lands the
directory holds none, and the command over no plan passes.  The synthetic cases of the command are in test_plan.py,
those of the check in test_checks.py.  The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import contextlib
import io
import os
import unittest
from pathlib import Path

from ..core import plan

REPO = Path(__file__).resolve().parents[4]
DOCUMENTS = REPO / "cad" / "fusion" / "documents"


class DefinitionTests(unittest.TestCase):
    def test_the_shared_definitions_of_every_product_plan_are_equal(self):
        previous = os.getcwd()
        os.chdir(REPO)  # the command runs at the repository root: the paths inside a plan are relative to it
        self.addCleanup(os.chdir, previous)
        plans = sorted(p.relative_to(REPO).as_posix() for p in DOCUMENTS.glob("*.json"))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = plan.main(["--definitions", *plans])
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
