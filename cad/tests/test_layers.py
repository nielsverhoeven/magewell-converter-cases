"""The layering of 01-ARCH-BRIEF section B, enforced for every P-layer module that sits directly in cad/:

    P0  numeric, params             data accessors                          stdlib (+ cad.numeric for params)
    P1  layout, brackets, coupons   solvers                                 P0; brackets may also read layout (B.3)
    P2  rules, rules_*              design rules and their helpers          P0 and P1

Standard library only (they run on Python 3.12, 3.14 and inside Fusion), no adsk, no cad.fusion, no scripts/,
and a lower layer never imports a higher one.  The table names the modules of issues #76 to #84 up front, so
no later issue has to edit this file; only the modules that exist are checked.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

CAD = Path(__file__).resolve().parents[1]

P0 = {"cad.numeric", "cad.params"}
ALLOWED: dict[str, set[str]] = {
    "numeric": set(),
    "params": {"cad.numeric"},
    "layout": P0,
    "brackets": P0 | {"cad.layout"},
    "coupons": P0,
}
RULES_MAY_IMPORT = P0 | {"cad.layout", "cad.brackets", "cad.coupons"}


def allowed_for(stem: str) -> set[str] | None:
    if stem in ALLOWED:
        return ALLOWED[stem]
    if stem == "rules" or stem.startswith("rules_"):
        return RULES_MAY_IMPORT | {f"cad.{p.stem}" for p in CAD.glob("rules*.py")}
    return None


def p_layer_files() -> list[Path]:
    return sorted(p for p in CAD.glob("*.py") if p.stem != "__init__")


def imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out |= {node.module} | {f"{node.module}.{a.name}" for a in node.names}
    return out


def test_the_p_layer_directory_holds_only_known_modules():
    unknown = [p.name for p in p_layer_files() if allowed_for(p.stem) is None]
    assert not unknown, f"{unknown}: add the module to ALLOWED in cad/tests/test_layers.py (layer P0, P1 or P2)"


@pytest.mark.parametrize("path", p_layer_files(), ids=lambda p: p.name)
def test_p_layer_modules_import_only_the_standard_library_and_lower_layers(path):
    allowed = allowed_for(path.stem) or set()
    for mod in imports(path):
        top = mod.split(".")[0]
        if top == "cad":
            assert mod == "cad" or any(mod == a or mod.startswith(a + ".") for a in allowed), f"{path.name} imports {mod}"
        else:
            assert top in sys.stdlib_module_names or top == "__future__", f"{path.name} imports non-stdlib {mod}"
            assert top not in ("adsk", "scripts"), f"{path.name} imports {mod}"


@pytest.mark.parametrize("path", p_layer_files(), ids=lambda p: p.name)
def test_the_p_layer_modules_parse_as_python_3_12(path):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 12))


# ---- every file under cad/, tools and tests included (A4 of the gate of #76) --------------------------------------


def all_cad_files() -> list[Path]:
    """Every source under cad/ except cad/fusion/: that tree has its own scans (the kit's test_layering.py and the
    runtime's test_runtime_layering.py), because it imports adsk and cad.fusion on purpose."""
    return sorted(p for p in CAD.rglob("*.py") if "__pycache__" not in p.parts and "fusion" not in p.relative_to(CAD).parts[:1])


def sys_path_uses(tree: ast.AST) -> list[int]:
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "path" and isinstance(node.value, ast.Name) and node.value.id == "sys":
            lines.append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module == "sys" and any(a.name == "path" for a in node.names):
            lines.append(node.lineno)
    return lines


@pytest.mark.parametrize("path", all_cad_files(), ids=lambda p: p.relative_to(CAD).as_posix())
def test_no_file_under_cad_imports_fusion_or_the_build_scripts_or_changes_sys_path(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for mod in imports(path):
        top = mod.split(".")[0]
        assert top not in ("adsk", "scripts"), f"{path.name} imports {mod}"
        assert mod != "cad.fusion" and not mod.startswith("cad.fusion."), f"{path.name} imports {mod}"
    assert not sys_path_uses(tree), f"{path.name} touches sys.path (line {sys_path_uses(tree)})"
