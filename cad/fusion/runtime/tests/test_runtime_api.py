"""Every Fusion API member the runtime uses is on the committed list, and the list agrees with the stubs.

`fixtures/adsk_members.json` lists every adsk class member that the files calling the API use, each with its line in
the stub of the installed Fusion ('module:Class.member': line). The checks that need only the list always run, so CI
(Linux, no Fusion) never skips. Where the stubs are installed (Autodesk webdeploy, or the folder named by the
environment variable MCC_ADSK_STUBS) the list is also compared with them; `python -m cad.fusion.runtime.api_check` is
the same comparison as a command.
"""
import ast
import json
import os
import unittest

from cad.fusion.runtime import api_check
from cad.fusion.runtime.tests import runtime_support as support

RUNTIME = os.path.join(support.REPO, "cad", "fusion", "runtime")
with open(api_check.FIXTURE, encoding="utf-8") as _fh:
    MEMBERS = json.load(_fh)["members"]


def parse(rel):
    with open(os.path.join(RUNTIME, *rel.split("/")), encoding="utf-8") as fh:
        return ast.parse(fh.read())


class ApiMembers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trees = {rel: parse(rel) for rel in api_check.FILES}
        cls.recorded = {key.split(":")[1].split(".")[1] for key in MEMBERS}
        cls.classes = {key.split(":")[1].split(".")[0] for key in MEMBERS}

    def test_the_list_is_well_formed(self):
        self.assertGreater(len(MEMBERS), 100)
        for key, line in MEMBERS.items():
            self.assertRegex(key, r"^(core|fusion):[A-Za-z0-9]+\.[A-Za-z0-9]+$")
            self.assertIsInstance(line, int)

    def test_every_attribute_name_is_on_the_list(self):
        allowed = self.recorded | self.classes | api_check.KNOWN | {"cast"}
        for rel, tree in self.trees.items():
            unknown = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} - allowed)
            with self.subTest(rel):
                self.assertEqual(unknown, [], "a misspelt adsk member, or add it to tests/fixtures/adsk_members.json "
                                              "with its stub line")

    def test_every_adsk_class_the_files_name_is_on_the_list(self):
        named = set()
        for tree in self.trees.values():
            for node in ast.walk(tree):                                   # adsk.core.X and adsk.fusion.X
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) \
                        and isinstance(node.value.value, ast.Name) and node.value.value.id == "adsk":
                    named.add(node.attr)
        named = {n for n in named if not n.startswith("__")}             # adsk.__file__ is a module attribute
        self.assertEqual(sorted(named - self.classes), [])
        self.assertIn("ValueInput", named)

    def test_every_listed_member_is_used(self):
        names = set()
        for tree in self.trees.values():
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    names.add(node.attr)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    names.add(node.value)                                  # getattr(MeshRefinementSettings, "...")
        self.assertEqual(sorted(k for k in MEMBERS if k.split(".")[1] not in names), [],
                         "remove the member from the list, or use it")

    def test_no_file_creates_a_value_from_a_real_number(self):
        for tree in self.trees.values():
            attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            self.assertNotIn("createByReal", attributes)                   # cm and rad: every value is a text

    def test_the_list_agrees_with_the_installed_stubs(self):
        directory = api_check.stub_dir()
        if directory is None:
            self.assertTrue(MEMBERS)                                       # nothing installed: the list checks above stand
            return
        self.assertEqual(api_check.check_fixture(directory, MEMBERS), [])

    def test_a_misspelt_member_is_found(self):
        source = "import adsk.core\nadsk.core.Application.get().userInterface.messageBoks('x')\n"
        found = {n.attr for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Attribute)}
        self.assertIn("messageBoks", found - self.recorded - self.classes - api_check.KNOWN)


if __name__ == "__main__":
    unittest.main()
