"""The import rules of the modelling kit (plan K3 step 6, verdict A8): a static scan of the source text with ``ast``;
no file is imported.  ``scan(root)`` returns the violations of every ``*.py`` under a ``cad`` directory, so the
negative tests run it on a small temporary tree.

1. ``adsk`` only in ``gen/core/fusion_backend.py``, ``gen/core/probes.py``, ``gen/core/enhance_fusion.py`` and ``fusion/runtime/``.
2. ``gen/shared/**`` and ``gen/<product>/**`` import the standard library, ``cad.fusion.gen.core``, their own package
   and, for a product, ``cad.fusion.gen.shared``; never ``cad.params``, a solver, ``cad.rules``, the runtime, the replay or OCP.
3. ``gen/core`` imports no shared or product module; shared imports no product; a product imports no other product.
4. ``shared.neutrik`` only from ``shared/panel.py``; in ``gen/case`` only ``floor.py`` imports ``shared.rail`` and only
   ``patch.py`` imports ``shared.panel``.
5. Nothing under ``cad/`` imports ``scripts`` or changes ``sys.path``; the one exception is ``fusion/runtime/hostlib.py``.
6. ``cad.fusion.replay`` is imported only by files under a ``tests`` directory (and by the replay package itself).

A product package is a directory under ``cad/fusion/gen/`` other than ``core``, ``shared`` and ``tests``.
"""
from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path
from typing import NamedTuple

CAD = Path(__file__).resolve().parents[3]

GEN = "cad.fusion.gen"
ADSK_FILES = ("fusion/gen/core/fusion_backend.py", "fusion/gen/core/probes.py", "fusion/gen/core/enhance_fusion.py")
ADSK_TREES = ("fusion/runtime/",)
NOT_PRODUCT = ("core", "shared", "tests")
SYS_PATH_CALLS = ("append", "insert", "extend")
# The one named exception to rule 5 (runtime verdict A1): the job executor puts the job's checkout first on
# ``sys.path`` for the length of one job and restores the list, which is what makes a worktree job run the worktree's
# code. The runtime's own test_runtime_layering proves that no other runtime file and no test changes ``sys.path``.
SYS_PATH_EXEMPT = ("fusion/runtime/hostlib.py",)


class Violation(NamedTuple):
    rule: int
    path: str
    text: str

    def __str__(self) -> str:
        return f"rule {self.rule}: {self.path}: {self.text}"


def _dotted(node) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return node.id if isinstance(node, ast.Name) else ""


def _package_of(root: Path, path: Path) -> list[str]:
    """The dotted package a module lives in: for ``cad/fusion/gen/core/facade.py`` that is ``cad.fusion.gen.core``, and
    for a package's own ``__init__.py`` the package itself."""
    parts = [root.name, *path.relative_to(root).parts]
    return parts[:-1]


def imported_modules(root: Path, path: Path, tree: ast.AST) -> set[str]:
    """Every module an import statement names, relative imports resolved; ``from m import a`` names ``m`` and ``m.a``."""
    package = _package_of(root, path)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)]
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            out |= {module} | {f"{module}.{a.name}" for a in node.names if a.name != "*"}
    return out


def changes_sys_path(tree: ast.AST) -> list[int]:
    """Line numbers of ``sys.path`` on the left of an assignment or as the object of append, insert or extend."""
    lines = []
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        for target in targets:
            for t in ast.walk(target):
                if _dotted(t) == "sys.path":
                    lines.append(node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SYS_PATH_CALLS \
                and _dotted(node.func.value) == "sys.path":
            lines.append(node.lineno)
    return lines


def _within(module: str, package: str) -> bool:
    return module == package or module.startswith(package + ".")


def products(root: Path) -> list[str]:
    gen = root / "fusion" / "gen"
    if not gen.is_dir():
        return []
    return sorted(d.name for d in gen.iterdir() if d.is_dir() and d.name not in NOT_PRODUCT and not d.name.startswith(("_", ".")))


def scan(root: Path) -> list[Violation]:
    found: list[Violation] = []
    product_names = products(root)
    parents = {"cad", "cad.fusion", GEN}  # `from cad.fusion.gen import core` names these too
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        mods = imported_modules(root, path, tree)
        parts = rel.split("/")
        area = parts[2] if parts[:2] == ["fusion", "gen"] and len(parts) > 3 else None
        is_product = area is not None and area not in NOT_PRODUCT

        def report(rule, text):
            found.append(Violation(rule, rel, text))

        # 1
        for m in sorted(mods):
            if _within(m, "adsk") and rel not in ADSK_FILES and not rel.startswith(ADSK_TREES):
                report(1, f"imports {m}; adsk is imported only by the Fusion backend, the probes, the enhancement executor and the runtime")
        # 2
        if area == "shared" or is_product:
            own = f"{GEN}.{area}"
            allowed = [own, f"{GEN}.core"] + ([f"{GEN}.shared"] if is_product else [])
            for m in sorted(mods):
                if m.split(".")[0] in sys.stdlib_module_names or m in parents or any(_within(m, a) for a in allowed):
                    continue
                report(2, f"imports {m}; only the standard library, {', '.join(allowed)}")
        # 3
        if area == "core":
            for m in sorted(mods):
                if _within(m, f"{GEN}.shared") or any(_within(m, f"{GEN}.{p}") for p in product_names):
                    report(3, f"imports {m}; the core knows no shared or product module")
        elif area == "shared":
            for m in sorted(mods):
                if any(_within(m, f"{GEN}.{p}") for p in product_names):
                    report(3, f"imports {m}; shared builders import no product")
        elif is_product:
            for m in sorted(mods):
                if any(_within(m, f"{GEN}.{p}") for p in product_names if p != area):
                    report(3, f"imports {m}; a product imports no other product")
        # 4
        if any(_within(m, f"{GEN}.shared.neutrik") for m in mods) and rel not in ("fusion/gen/shared/panel.py", "fusion/gen/shared/neutrik.py"):
            report(4, f"imports {GEN}.shared.neutrik; only shared/panel.py does")
        if area == "case":
            for module, owner in (("rail", "floor.py"), ("panel", "patch.py")):
                if any(_within(m, f"{GEN}.shared.{module}") for m in mods) and parts[-1] != owner:
                    report(4, f"imports {GEN}.shared.{module}; in gen/case only {owner} does")
        # 5
        for m in sorted(mods):
            if _within(m, "scripts"):
                report(5, f"imports {m}; nothing under cad/ imports scripts/")
        for line in changes_sys_path(tree):
            if rel not in SYS_PATH_EXEMPT:
                report(5, f"line {line} changes sys.path")
        # 6
        if any(_within(m, "cad.fusion.replay") for m in mods) and "tests" not in parts[:-1] and not rel.startswith("fusion/replay/"):
            report(6, "imports cad.fusion.replay; only files under a tests directory do")
    return found


class RealTreeTests(unittest.TestCase):
    def test_the_cad_tree_obeys_the_six_rules(self):
        found = scan(CAD)
        self.assertEqual(found, [], "\n".join(map(str, found)))

    def test_the_product_packages_are_the_directories_other_than_core_shared_tests(self):
        for name in products(CAD):
            self.assertNotIn(name, NOT_PRODUCT)


class NegativeTests(unittest.TestCase):
    """One temporary file per rule, reported by name; and the files that may do it are not reported."""

    def tree(self, files: dict[str, str]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "cad"
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for folder in {p.parent for p in root.rglob("*.py")}:
            init = folder / "__init__.py"
            if not init.exists():
                init.write_text("# package\n", encoding="utf-8")
        return root

    def reported(self, files, rule):
        return sorted({v.path for v in scan(self.tree(files)) if v.rule == rule})

    def test_rule_1_adsk_outside_the_backend(self):
        root = self.tree({"fusion/gen/core/facade.py": "import adsk.core\n", "fusion/gen/core/fusion_backend.py": "import adsk.fusion\n",
                          "fusion/gen/core/probes.py": "from adsk import core\n", "fusion/runtime/job.py": "import adsk.core\n",
                          "fusion/gen/shared/tg.py": "import adsk\n"})
        self.assertEqual(sorted(v.path for v in scan(root) if v.rule == 1), ["fusion/gen/core/facade.py", "fusion/gen/shared/tg.py"])

    def test_rule_2_shared_and_products_import_only_the_allowed_modules(self):
        files = {"fusion/gen/shared/a.py": "from cad import params\n", "fusion/gen/shared/b.py": "from cad.fusion.replay import x\n",
                 "fusion/gen/case/c.py": "import OCP\n", "fusion/gen/case/d.py": "from cad.layout import solve\n",
                 "fusion/gen/case/ok.py": "import json\nfrom ..core import facade\nfrom ..shared import tg\nfrom . import frame\n"
                                          "from cad.fusion.gen.core import expr\nfrom cad.fusion.gen.shared import rail\n",
                 "fusion/gen/shared/ok.py": "import re\nfrom ..core import names\nfrom . import tg\n"}
        self.assertEqual(self.reported(files, 2), ["fusion/gen/case/c.py", "fusion/gen/case/d.py", "fusion/gen/shared/a.py", "fusion/gen/shared/b.py"])

    def test_rule_2_a_shared_module_may_not_import_a_product(self):
        self.assertEqual(self.reported({"fusion/gen/shared/a.py": "from ..case import frame\n", "fusion/gen/case/frame.py": ""}, 2),
                         ["fusion/gen/shared/a.py"])

    def test_rule_3_the_core_imports_no_shared_or_product_module(self):
        files = {"fusion/gen/core/a.py": "from ..shared import tg\n", "fusion/gen/core/b.py": "import cad.fusion.gen.case.frame\n",
                 "fusion/gen/core/ok.py": "from . import names\nfrom .names import KitError\n", "fusion/gen/case/frame.py": "",
                 "fusion/gen/shared/tg.py": ""}
        self.assertEqual(self.reported(files, 3), ["fusion/gen/core/a.py", "fusion/gen/core/b.py"])

    def test_rule_3_shared_imports_no_product_and_products_do_not_import_each_other(self):
        files = {"fusion/gen/shared/a.py": "from ..case import frame\n", "fusion/gen/case/frame.py": "from ..brackets import arch\n",
                 "fusion/gen/brackets/arch.py": "from ..shared import tg\n", "fusion/gen/shared/tg.py": ""}
        self.assertEqual(self.reported(files, 3), ["fusion/gen/case/frame.py", "fusion/gen/shared/a.py"])

    def test_rule_4_neutrik_is_imported_by_panel_only(self):
        files = {"fusion/gen/shared/panel.py": "from . import neutrik\n", "fusion/gen/shared/neutrik.py": "",
                 "fusion/gen/shared/tg.py": "from .neutrik import d_wall_cut\n", "fusion/gen/case/patch.py": "from ..shared import neutrik\n"}
        self.assertEqual(self.reported(files, 4), ["fusion/gen/case/patch.py", "fusion/gen/shared/tg.py"])

    def test_rule_4_in_the_case_only_floor_calls_rail_and_only_patch_calls_panel(self):
        files = {"fusion/gen/case/floor.py": "from ..shared import rail, panel\n", "fusion/gen/case/patch.py": "from ..shared import panel, rail\n",
                 "fusion/gen/case/shell.py": "from ..shared import rail\n", "fusion/gen/shared/rail.py": "", "fusion/gen/shared/panel.py": ""}
        self.assertEqual(self.reported(files, 4), ["fusion/gen/case/floor.py", "fusion/gen/case/patch.py", "fusion/gen/case/shell.py"])
        found = [(v.path, v.text) for v in scan(self.tree(files)) if v.rule == 4]
        self.assertEqual(len(found), 3)  # floor: panel; patch: rail; shell: rail

    def test_rule_5_scripts_and_sys_path(self):
        files = {"tools/a.py": "from scripts import build\n", "tools/b.py": "import sys\nsys.path.insert(0, '.')\n",
                 "tools/c.py": "import sys\nsys.path = []\n", "tools/d.py": "import sys\nsys.path += ['x']\n",
                 "tools/e.py": "import sys\nsys.path.append('x')\nsys.path[0] = 'y'\n", "tools/f.py": "import scripts.parity\n",
                 "tools/ok.py": "import sys\nprint(sys.path)\nprint(sys.path[0])\n"}
        self.assertEqual(self.reported(files, 5), ["tools/a.py", "tools/b.py", "tools/c.py", "tools/d.py", "tools/e.py", "tools/f.py"])

    def test_rule_5_the_job_executor_is_the_one_file_that_may_change_sys_path(self):
        change = "import sys\nsys.path.insert(0, '.')\n"
        files = {"fusion/runtime/hostlib.py": change, "fusion/runtime/runner.py": change, "fusion/runtime/tests/t.py": change,
                 "fusion/runtime/host/MccRun/hostlib.py": change}
        self.assertEqual(self.reported(files, 5), ["fusion/runtime/host/MccRun/hostlib.py", "fusion/runtime/runner.py",
                                                   "fusion/runtime/tests/t.py"])

    def test_rule_6_the_replay_is_imported_by_tests_only(self):
        files = {"fusion/gen/case/a.py": "from cad.fusion.replay import ocp_replay\n", "tools/b.py": "from cad.fusion import replay\n",
                 "fusion/gen/tests/ok.py": "from cad.fusion.replay import ocp_replay\n", "tests/ok.py": "import cad.fusion.replay\n",
                 "fusion/replay/ocp_replay.py": "from . import other\nimport cad.fusion.replay.other\n", "fusion/replay/other.py": ""}
        self.assertEqual(self.reported(files, 6), ["fusion/gen/case/a.py", "tools/b.py"])

    def test_a_clean_tree_has_no_violation(self):
        root = self.tree({"fusion/gen/core/a.py": "import json\nfrom . import b\n", "fusion/gen/core/b.py": "",
                          "fusion/gen/shared/tg.py": "from ..core import names\n", "fusion/gen/case/floor.py": "from ..shared import rail\n",
                          "fusion/gen/shared/rail.py": ""})
        self.assertEqual(scan(root), [])
