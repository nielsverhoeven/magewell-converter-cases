"""A text scan of ``fusion_backend.py`` against the recorded adsk members (plan K5a step 3).

It catches a misspelt member without Fusion.  ``fixtures/adsk_members.json`` lists every adsk class member the backend
uses, each with its line in the stub of the installed version (``module:Class.member`` to line).  Two checks:

1. every attribute name the backend reads or calls, and every ``adsk.core`` / ``adsk.fusion`` class it names, is either
   in that list, one of the backend's own names, a field of a spec, or a plain Python name;
2. where the stub files are installed (Autodesk ``webdeploy`` on Windows or macOS, or the folder in the environment
   variable ``MCC_ADSK_STUBS``), every listed member exists in its class in the stub.  Where they are not installed the
   test still checks the list itself, so it never skips: CI runs on Linux without Fusion.

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import ast
import dataclasses
import json
import os
import re
import unittest
from pathlib import Path

from ..core import spec as specs

GEN = Path(__file__).resolve().parents[1]
BACKEND = GEN / "core" / "fusion_backend.py"
MEMBERS = json.loads((Path(__file__).parent / "fixtures" / "adsk_members.json").read_text(encoding="utf-8"))["members"]

# attribute names of plain Python objects the backend uses (str, list, dict, exceptions)
PYTHON_NAMES = {"append", "get", "items", "partition", "setdefault", "rsplit", "join", "__name__", "rjust"}
# names that belong to the backend or to the facade, not to adsk
OWN_NAMES = {"expr", "facade", "fusion", "PLANE_NORMAL", "Env", "value", "RecordingBackend", "execute", "raw_inventory",
             "build_record", "KitError", "adsk", "core", "registry", "values"}  # registry, values: attributes of ctx


def members_by_class() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for key in MEMBERS:
        _, rest = key.split(":")
        cls, member = rest.split(".")
        out.setdefault(cls, set()).add(member)
    return out


def own_attribute_names(tree: ast.AST) -> set[str]:
    """Attributes the module assigns on ``self`` or another object of its own, plus every function, class and argument name."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) \
                and node.value.id == "self":
            names.add(node.attr)
    return names


class StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(BACKEND.read_text(encoding="utf-8"), filename=str(BACKEND))

    def test_the_backend_uses_no_adsk_member_that_is_not_recorded(self):
        known = {m for ms in members_by_class().values() for m in ms} | set(members_by_class())
        known |= own_attribute_names(self.tree) | PYTHON_NAMES | OWN_NAMES
        spec_classes = [c for c in vars(specs).values() if isinstance(c, type) and dataclasses.is_dataclass(c)]
        known |= {f.name for c in spec_classes for f in dataclasses.fields(c)} | {c.__name__ for c in spec_classes}
        unknown = sorted({node.attr for node in ast.walk(self.tree) if isinstance(node, ast.Attribute)} - known)
        self.assertEqual(unknown, [], "attribute names that are in no list: a misspelt adsk member, or add it to "
                                      "tests/fixtures/adsk_members.json with its stub line")

    def test_every_recorded_member_is_used_by_the_backend(self):
        used = {node.attr for node in ast.walk(self.tree) if isinstance(node, ast.Attribute)}
        unused = sorted(k for k in MEMBERS if k.split(".")[1] not in used)
        self.assertEqual(unused, [], "remove the member from the list or use it")

    def test_every_adsk_class_the_backend_names_is_recorded(self):
        named = set()
        for node in ast.walk(self.tree):  # adsk.core.X and adsk.fusion.X
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)                     and isinstance(node.value.value, ast.Name) and node.value.value.id == "adsk":
                named.add(f"{node.value.attr}:{node.attr}")
        recorded = {key.split(".")[0] for key in MEMBERS}  # module:Class
        self.assertEqual(sorted(named - recorded), [], "an adsk class with no recorded member")
        self.assertIn("core:ValueInput", named)

    def test_the_backend_never_calls_createByReal(self):
        attributes = {node.attr for node in ast.walk(self.tree) if isinstance(node, ast.Attribute)}
        self.assertNotIn("createByReal", attributes)  # centimetres and radians: every dimension is a string expression

    def test_the_list_is_well_formed(self):
        self.assertGreater(len(MEMBERS), 100)
        for key, line in MEMBERS.items():
            self.assertRegex(key, r"^(core|fusion):[A-Za-z0-9]+\.[A-Za-z0-9]+$")
            self.assertIsInstance(line, int)

    def test_the_members_exist_in_the_stub_where_it_is_installed(self):
        stubs = stub_dir()
        if stubs is None:
            return  # not a skip: the list was checked above and the stub is checked wherever the CAD workstation has it
        for mod in ("core", "fusion"):
            lines = (stubs / f"{mod}.py").read_text(encoding="utf-8").split("\n")
            for key, line in MEMBERS.items():
                if not key.startswith(mod + ":"):
                    continue
                cls, member = key.split(":")[1].split(".")
                self.assertTrue(member_in_class(lines, cls, member), f"{key} is not in the stub")


def stub_dir() -> Path | None:
    candidates = []
    if os.environ.get("MCC_ADSK_STUBS"):
        candidates.append(Path(os.environ["MCC_ADSK_STUBS"]))
    for base in (Path.home() / "AppData" / "Local" / "Autodesk" / "webdeploy" / "production",
                 Path.home() / "Library" / "Application Support" / "Autodesk" / "webdeploy" / "production"):
        if base.is_dir():
            candidates += sorted(base.glob("*/Api/Python/packages/adsk"))
    for path in candidates:
        if (path / "fusion.py").is_file() and (path / "core.py").is_file():
            return path
    return None


def member_in_class(lines: list[str], cls: str, member: str) -> bool:
    start = next((i for i, line in enumerate(lines) if line.startswith((f"class {cls}(", f"class {cls}:"))), None)
    if start is None:
        return False
    pattern = re.compile(rf"\s+(?:def (?:_get_)?{re.escape(member)}\(|{re.escape(member)} = _)")
    for line in lines[start + 1:]:
        if line.startswith("class "):
            return False
        if pattern.match(line):
            return True
    return False


if __name__ == "__main__":
    unittest.main()
