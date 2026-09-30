"""The showcase PNGs reach the release zips (issue #74): scripts/package_release.py, synthetic files only.

    python -m pytest scripts/tests/test_package_release_renders.py -q
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import build
import package_release


def setup_tree(tmp_path: Path, monkeypatch) -> None:
    """A fake repo root: exports/<case>/..., dist/renders/*.png; build and package_release point at it."""

    monkeypatch.setattr(build, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(build, "EXPORTS_DIR", tmp_path / "exports")
    monkeypatch.setattr(package_release, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(package_release, "RENDERS_DIR", tmp_path / "dist" / "renders")
    renders = tmp_path / "dist" / "renders"
    renders.mkdir(parents=True)
    for name in (
        "case-iso.png", "case-patch-wall.png", "case-underside.png",
        "case-4k-iso.png",                                   # another case whose slug starts with "case-"
        "brackets-arch.png", "brackets-vertical.png",
    ):
        (renders / name).write_bytes(b"png " + name.encode())
    (renders / "manifest.json").write_text("{}", encoding="utf-8")
    for slug, parts in (("case", ("base", "lid")), ("brackets/arch", ("arm",))):
        for part in parts:
            d = tmp_path / "exports" / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{part}.stl").write_bytes(b"solid")


def make_target(tmp_path: Path, name: str, parts: list[str], kind: str) -> build.Target:
    scad = tmp_path / f"{Path(name).name}.scad"
    scad.write_text("// no device include\n", encoding="utf-8")
    return build.Target(name=name, scad_path=scad, parts=parts, kind=kind)


def test_device_zip_gets_its_own_renders_only(tmp_path, monkeypatch):
    setup_tree(tmp_path, monkeypatch)
    zip_path = package_release.package_model(make_target(tmp_path, "case", ["base", "lid"], "model"), "v1.0.0", "abc")
    assert zip_path is not None
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        readme = zf.read("README.txt").decode("utf-8")
    assert {"renders/case-iso.png", "renders/case-patch-wall.png", "renders/case-underside.png"} <= names
    assert not any(n.startswith("renders/case-4k") or n.endswith("manifest.json") for n in names)
    assert "  renders/case-iso.png" in readme                      # the README contents list names them
    assert {"base.stl", "lid.stl"} <= names


def test_brackets_zip_gets_the_bracket_renders(tmp_path, monkeypatch):
    setup_tree(tmp_path, monkeypatch)
    target = make_target(tmp_path, "brackets/arch", ["arm"], "bracket")
    zip_path = package_release.package_brackets([target], "v1.0.0", "abc")
    assert zip_path is not None
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        readme = zf.read("README.txt").decode("utf-8")
    assert {"renders/brackets-arch.png", "renders/brackets-vertical.png", "arch/arm.stl"} <= names
    assert "  renders/brackets-arch.png" in readme


def test_coupons_zip_takes_no_renders(tmp_path, monkeypatch):
    setup_tree(tmp_path, monkeypatch)
    target = make_target(tmp_path, "coupons/tile", ["tile"], "coupon")
    (tmp_path / "exports" / "coupons" / "tile").mkdir(parents=True)
    (tmp_path / "exports" / "coupons" / "tile" / "tile.stl").write_bytes(b"solid")
    zip_path = package_release.package_coupons([target], "v1.0.0", "abc")
    assert zip_path is not None
    with zipfile.ZipFile(zip_path) as zf:
        assert not any(n.startswith("renders/") for n in zf.namelist())
