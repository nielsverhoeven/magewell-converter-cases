"""The pure modules of the runtime import without adsk, so that CI and scripts/ can use them, and parse as Python 3.12."""
import ast
import glob
import os
import subprocess
import sys
import unittest

from cad.fusion.runtime.tests import runtime_support as support

PURE = ("runner", "pipeline", "port", "recording", "expr", "inventory", "digest", "paramset", "registry",
        "plan", "planrun", "gates", "manifest", "testdoc.builder", "testdoc.expected")


class PureModules(unittest.TestCase):
    def test_import_with_adsk_blocked(self):
        for name in PURE:
            with self.subTest(name):
                code = ("import sys; sys.modules['adsk'] = None; "
                        "import importlib; importlib.import_module('cad.fusion.runtime.%s')" % name)
                p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, timeout=60,
                                   cwd=support.REPO)
                self.assertEqual(p.returncode, 0, p.stderr)

    def test_every_source_of_the_runtime_and_the_client_parses_as_python_3_12(self):
        """CI runs Python 3.12; the development machines run 3.14. Only the grammar is checked here."""
        runtime = os.path.join(support.REPO, "cad", "fusion", "runtime")
        paths = glob.glob(os.path.join(runtime, "**", "*.py"), recursive=True)
        paths.append(os.path.join(support.REPO, "scripts", "fusion_run.py"))
        self.assertGreater(len(paths), 20)
        for path in sorted(paths):
            with self.subTest(os.path.relpath(path, support.REPO)):
                with open(path, encoding="utf-8") as fh:
                    ast.parse(fh.read(), filename=path, feature_version=(3, 12))


if __name__ == "__main__":
    unittest.main()
