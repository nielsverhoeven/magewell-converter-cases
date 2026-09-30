"""Input digest sha256-lf-v1."""
import os
import shutil
import tempfile
import types
import unittest

from cad.fusion.runtime import digest


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="mcc-digest-")
        os.makedirs(os.path.join(self.root, "cad", "a", "__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def put(self, rel, data):
        path = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)

    def test_digest(self):
        self.put("cad/a/x.py", b"a = 1\nb = 2\n")
        self.put("cad/a/y.csv", b"Name,Unit\nA,mm\n")
        self.put("cad/a/__pycache__/x.cpython-314.pyc", b"\x00\x01")
        d1 = digest.digest_files(self.root, ["cad/**/*.py", "cad/a/*.csv"])
        self.assertEqual(d1["files"], 2)
        self.assertEqual(digest.input_files(self.root, ["cad/**"]), ["cad/a/x.py", "cad/a/y.csv"])
        self.put("cad/a/x.py", b"a = 1\r\nb = 2\r\n")                       # CRLF checkout
        self.assertEqual(digest.digest_files(self.root, ["cad/**/*.py", "cad/a/*.csv"]), d1)
        self.put("cad/a/x.py", b"a = 1\nb = 3\n")
        self.assertNotEqual(digest.digest_files(self.root, ["cad/**/*.py", "cad/a/*.csv"]), d1)
        with self.assertRaises(ValueError):
            digest.digest_files(self.root, ["../x"])
        with self.assertRaises(ValueError):
            digest.digest_files(self.root, ["nothing/*.py"])

    def test_the_replay_is_no_build_input(self):
        self.put("cad/fusion/gen/a.py", b"x = 1\n")
        before = digest.digest_files(self.root, ["cad/fusion/**/*.py"])
        self.put("cad/fusion/replay/ocp_replay.py", b"x = 1\n")
        self.assertEqual(digest.input_files(self.root, ["cad/fusion/**/*.py"]), ["cad/fusion/gen/a.py"])
        self.assertEqual(digest.digest_files(self.root, ["cad/fusion/**/*.py"]), before)

    def test_the_runtime_is_a_mandatory_input_but_not_its_test_document_or_tests(self):
        for rel in ("cad/fusion/runtime/pipeline.py", "cad/fusion/runtime/probe/spin.py", "cad/fusion/runtime/fusion_facts.json",
                    "cad/fusion/runtime/testdoc/builder.py", "cad/fusion/runtime/tests/test_x.py", "cad/fusion/gen/a.py"):
            self.put(rel, b"x = 1\n")
        self.assertEqual(digest.input_files(self.root, ["cad/fusion/gen/*.py"]),
                         ["cad/fusion/gen/a.py", "cad/fusion/runtime/fusion_facts.json", "cad/fusion/runtime/pipeline.py",
                          "cad/fusion/runtime/probe/spin.py"])
        self.assertEqual(digest.input_files(self.root, ["cad/fusion/runtime/testdoc/*.py"]),       # a plan may name them
                         ["cad/fusion/runtime/fusion_facts.json", "cad/fusion/runtime/pipeline.py",
                          "cad/fusion/runtime/probe/spin.py", "cad/fusion/runtime/testdoc/builder.py"])
        before = digest.digest_files(self.root, ["cad/fusion/gen/*.py"])
        self.put("cad/fusion/runtime/tests/test_x.py", b"x = 2\n")                                # a test is no input
        self.put("cad/fusion/runtime/testdoc/builder.py", b"x = 2\n")
        self.assertEqual(digest.digest_files(self.root, ["cad/fusion/gen/*.py"]), before)
        self.put("cad/fusion/runtime/pipeline.py", b"x = 2\n")                                    # the runtime is
        self.assertNotEqual(digest.digest_files(self.root, ["cad/fusion/gen/*.py"]), before)

    def test_loaded_modules_that_no_pattern_matches_are_reported(self):
        for rel in ("cad/fusion/gen/core/a.py", "cad/fusion/gen/shared/b.py", "cad/fusion/runtime/pipeline.py"):
            self.put(rel, b"x = 1\n")

        def module(rel):
            return types.SimpleNamespace(__file__=os.path.join(self.root, *rel.split("/")))
        loaded = {"a": module("cad/fusion/gen/core/a.py"), "b": module("cad/fusion/gen/shared/b.py"),
                  "rt": module("cad/fusion/runtime/pipeline.py"), "elsewhere": types.SimpleNamespace(__file__=__file__),
                  "builtin": types.SimpleNamespace(), "null": types.SimpleNamespace(__file__=None)}
        self.assertEqual(digest.undeclared_modules(self.root, ["cad/fusion/gen/core/**/*.py"], loaded),
                         ["cad/fusion/gen/shared/b.py"])                    # the runtime is covered, core is named
        self.assertEqual(digest.undeclared_modules(self.root, ["cad/fusion/gen/**/*.py"], loaded), [])
        self.assertEqual(digest.undeclared_modules(self.root, ["cad/fusion/gen/**/*.py"], {}), [])


if __name__ == "__main__":
    unittest.main()
