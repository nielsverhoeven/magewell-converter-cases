"""Static scan of the runtime's sources: what it imports, that it never saves, and where sys.path changes."""
import ast
import glob
import os
import sys
import unittest

from cad.fusion.runtime.tests import runtime_support as support

RUNTIME = os.path.join(support.REPO, "cad", "fusion", "runtime")
CLIENT = os.path.join(support.REPO, "scripts", "fusion_run.py")
TESTS = os.path.join(RUNTIME, "tests")
OWN = "cad.fusion.runtime"
STANDALONE = ("cad/fusion/runtime/hostlib.py", "cad/fusion/runtime/host/MccRun/MccRun.py",
              "cad/fusion/runtime/host/MccFusionBridge/MccFusionBridge.py")
NEVER_CALLED = ("save", "saveAs")
PATH_EDITORS = {"cad/fusion/runtime/hostlib.py", "scripts/fusion_run.py"}     # the only files that may change sys.path
PARAMS_DOOR = "cad/fusion/runtime/registry.py"


def rel(path):
    return os.path.relpath(path, support.REPO).replace(os.sep, "/")


def parse(paths):
    trees = {}
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            trees[rel(path)] = ast.parse(fh.read())
    return trees


def runtime_sources():
    out = [CLIENT]
    for folder, dirs, names in os.walk(RUNTIME):
        dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__")]      # the tests are scanned on their own
        out += [os.path.join(folder, n) for n in names if n.endswith(".py")]
    return sorted(out)


def imported(tree, name):
    """Absolute names of the modules a file imports statically."""
    package = os.path.dirname(name).replace("/", ".")
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = package
            for _ in range(max(node.level - 1, 0)):
                base = base.rpartition(".")[0]
            prefix = (base + "." if node.module else base) if node.level else ""
            names.append(prefix + (node.module or ""))
    return names


def changes_sys_path(tree):
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            target = node.func.value                                   # sys.path.insert(...), .append(...)
        elif isinstance(node, (ast.Assign, ast.AugAssign)):
            first = node.targets[0] if isinstance(node, ast.Assign) else node.target
            target = first.value if isinstance(first, ast.Subscript) else first
        if isinstance(target, ast.Attribute) and target.attr == "path" \
                and isinstance(target.value, ast.Name) and target.value.id == "sys":
            return True
    return False


class Layering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trees = parse(runtime_sources())
        cls.tests = parse(sorted(glob.glob(os.path.join(TESTS, "*.py"))))

    def test_imports(self):
        allowed = set(sys.stdlib_module_names) | {"adsk"}
        for name, tree in self.trees.items():
            for module in imported(tree, name):
                own = module == OWN or module.startswith(OWN + ".")
                with self.subTest(file=name, module=module):
                    self.assertTrue(module.split(".")[0] in allowed or own, module)
                    if name in STANDALONE:
                        self.assertFalse(own, "%s is loaded by path and imports no sibling" % name)

    def test_the_parameter_data_has_one_door(self):
        named = []                                                     # import_module("<a module written out>")
        for name, tree in self.trees.items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "import_module" \
                        and node.args and isinstance(node.args[0], ast.Constant):
                    named.append((name, node.args[0].value))
        self.assertEqual(named, [(PARAMS_DOOR, "cad.params")])

    def test_nothing_saves_a_document(self):
        for name, tree in self.trees.items():
            used = {n.func.attr for n in ast.walk(tree)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
            self.assertEqual(sorted(used & set(NEVER_CALLED)), [], name)

    def test_sys_path_changes_only_in_the_executor_and_the_client(self):
        editors = {name for name, tree in self.trees.items() if changes_sys_path(tree)}
        self.assertLessEqual(editors, PATH_EDITORS)
        self.assertIn("scripts/fusion_run.py", editors)
        self.assertEqual([name for name, tree in self.tests.items() if changes_sys_path(tree)], [])


if __name__ == "__main__":
    unittest.main()
