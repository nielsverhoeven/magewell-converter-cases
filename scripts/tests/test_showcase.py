"""Self-tests of scripts/showcase.py (issue #74). No GL, no OpenSCAD, no exports/: tiny ASCII-STL cubes.

    python -m pytest scripts/tests/test_showcase.py -q

Nothing here skips: the pure half of the showcase pipeline must be testable on a runner without
pyvista/vtk (the `tests` job of cad-gates.yml installs requirements.txt only), and
`test_showcase_imports_no_gl` pins that.
"""

from __future__ import annotations

import dataclasses
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import showcase

SCRIPTS = Path(__file__).resolve().parents[1]
FP = "test-fingerprint"     # a fixed render fingerprint: plan_jobs() tests do not depend on requirements-render.txt


def write_cube(path: Path, lo=(0.0, 0.0, 0.0), hi=(10.0, 10.0, 10.0)) -> Path:
    """Write the box lo..hi as an ASCII STL (12 triangles)."""

    x0, y0, z0 = lo
    x1, y1, z1 = hi
    v = {
        (i, j, k): (float(x1 if i else x0), float(y1 if j else y0), float(z1 if k else z0))
        for i in (0, 1) for j in (0, 1) for k in (0, 1)
    }
    quads = [
        ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
        ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
        ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
    ]
    lines = ["solid cube"]
    for a, b, c, d in quads:
        for tri in ((a, b, c), (a, c, d)):
            lines.append("facet normal 0 0 0\n outer loop")
            lines += [" vertex %r %r %r" % v[p] for p in tri]
            lines.append(" endloop\nendfacet")
    lines.append("endsolid cube")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


def make_exports(root: Path, cases=("case-a", "case-b"), brackets=("brk",), ghost=()) -> Path:
    exports = root / "exports"
    for i, slug in enumerate(cases):
        for part in ("base", "lid"):
            write_cube(exports / slug / f"{part}.model.stl", (0, 0, 0), (20 + i, 10, 5 if part == "base" else 6))
        write_cube(exports / slug / "base_fan.model.stl")            # an extra part: ignored
        if slug in ghost:
            write_cube(exports / slug / "ghost_device.model.stl", (2, 2, 1), (9, 9, 4))
    write_cube(exports / "coupons" / "neutrik-tile" / "neutrik-tile.model.stl")   # not a case
    for slug in brackets:
        write_cube(exports / "brackets" / slug / "arm.model.stl", (0, 0, 0), (10, 4, 2))
        write_cube(exports / "brackets" / slug / "centre.model.stl", (5, 0, 0), (25, 4, 2))
    return exports


def plan(exports: Path, fingerprint: str = FP) -> list[showcase.Job]:
    return showcase.plan_jobs(showcase.discover_showcase_targets(exports), fingerprint)


# ---------------------------------------------------------------------------------------- isolation


def test_showcase_imports_no_gl():
    """D74.1: the pure module never pulls in the GL stack (in this process and in a fresh one)."""

    assert "pyvista" not in sys.modules and "vtk" not in sys.modules
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import showcase, showcase_gl; "
        "assert 'pyvista' not in sys.modules and 'vtk' not in sys.modules, 'GL imported'"
    )
    subprocess.run([sys.executable, "-c", code, str(SCRIPTS)], check=True, capture_output=True, text=True)


# ------------------------------------------------------------------------------------ jobs and names


def test_one_job_per_case_view_and_bracket_target(tmp_path):
    jobs = plan(make_exports(tmp_path))
    assert len(jobs) == 2 * 3 + 1
    assert [j.view for j in jobs if j.target == "case-a"] == ["iso", "patch-wall", "underside"]
    assert sum(1 for j in jobs if j.target == "brk") == 1


def test_image_names(tmp_path):
    names = sorted(j.image for j in plan(make_exports(tmp_path)))
    assert names == sorted([
        "case-a-iso.png", "case-a-patch-wall.png", "case-a-underside.png",
        "case-b-iso.png", "case-b-patch-wall.png", "case-b-underside.png",
        "brackets-brk.png",
    ])


def test_views_hold_the_right_parts(tmp_path):
    jobs = {(j.target, j.view): j for j in plan(make_exports(tmp_path, ghost=("case-a",)))}
    roles = lambda j: sorted(m.role for m in j.meshes)   # noqa: E731
    assert roles(jobs["case-a", "iso"]) == ["base", "ghost", "lid"]
    assert roles(jobs["case-b", "iso"]) == ["base", "lid"]          # the ghost is optional
    assert roles(jobs["case-a", "patch-wall"]) == ["base", "lid"]
    assert roles(jobs["case-a", "underside"]) == ["base"]
    iso_lid = next(m for m in jobs["case-a", "iso"].meshes if m.role == "lid")
    assert 0.0 < iso_lid.opacity < 1.0                               # translucent lid in the iso view only
    wall_lid = next(m for m in jobs["case-a", "patch-wall"].meshes if m.role == "lid")
    assert wall_lid.opacity == 1.0


def test_coupons_and_extra_parts_are_not_cases(tmp_path):
    targets = showcase.discover_showcase_targets(make_exports(tmp_path))
    assert [t.name for t in targets if t.kind == "case"] == ["case-a", "case-b"]
    assert [t.name for t in targets if t.kind == "bracket"] == ["brk"]
    assert all("coupon" not in t.name for t in targets)
    case = targets[0]
    assert [p for p, _ in case.parts] == ["base", "lid"]             # base_fan.model.stl is ignored


def test_bracket_parts_are_laid_out_side_by_side_along_x(tmp_path):
    job = next(j for j in plan(make_exports(tmp_path)) if j.target == "brk")
    arm, centre = job.meshes                                        # sorted by part name
    assert (arm.path.name, centre.path.name) == ("arm.model.stl", "centre.model.stl")
    assert arm.offset == (0.0, 0.0, 0.0)                             # arm spans x 0..10
    assert centre.offset == (10.0 + showcase.BRACKET_GAP_MM - 5.0, 0.0, 0.0)   # centre spans x 5..25


# ------------------------------------------------------------------------------------------ cameras


BOUNDS = ((-10.0, -20.0, 0.0), (10.0, 20.0, 10.0))
TOWARD = {   # independent of camera_for(): the direction focal point -> camera, from the documented azimuth/elevation
    "iso": (-math.sin(math.radians(35)) * math.cos(math.radians(30)), math.cos(math.radians(35)) * math.cos(math.radians(30)), math.sin(math.radians(30))),
    "patch-wall": (math.sin(math.radians(18)) * math.cos(math.radians(12)), math.cos(math.radians(18)) * math.cos(math.radians(12)), math.sin(math.radians(12))),
    "underside": (math.cos(math.radians(30)) * math.cos(math.radians(35)), math.sin(math.radians(30)) * math.cos(math.radians(35)), -math.sin(math.radians(35))),
    "row": (math.sin(math.radians(10)) * math.cos(math.radians(42)), math.cos(math.radians(10)) * math.cos(math.radians(42)), math.sin(math.radians(42))),
}


@pytest.mark.parametrize("name", sorted(TOWARD))
def test_camera_direction_up_and_tight_fit(name):
    aspect = 1.6
    cam = showcase.camera_for(name, BOUNDS, aspect)
    focal, position = np.array(cam.focal), np.array(cam.position)
    assert cam.focal == (0.0, 0.0, 5.0)                              # the centre of the bounds
    assert cam.up == (0.0, 0.0, 1.0)
    assert cam.view_angle == showcase.VIEW_ANGLE_DEG
    direction = (position - focal) / np.linalg.norm(position - focal)
    assert direction == pytest.approx(TOWARD[name], abs=1e-12)

    # every corner lies inside the frustum, and the tightest one touches the margin exactly
    forward = -direction
    right = np.cross(forward, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    tan_half = math.tan(math.radians(cam.view_angle) / 2.0)
    extent = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v = np.array([sx * 10.0, sy * 20.0, 5.0 + sz * 5.0]) - position
                depth = float(v @ forward)
                assert depth > 0
                extent.append(max(abs(float(v @ up)) / (depth * tan_half), abs(float(v @ right)) / (depth * tan_half * aspect)))
    assert max(extent) == pytest.approx(1.0 / showcase.FIT_MARGIN, rel=1e-9)


def test_patch_wall_constant_and_camera_side():
    assert showcase.PATCH_WALL_NORMAL in ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0))
    cam = showcase.camera_for("patch-wall", BOUNDS)
    side = np.sign(np.array(cam.position)[1] - cam.focal[1])
    assert side == showcase.PATCH_WALL_NORMAL[1]                      # the camera looks at the patch wall from outside
    with pytest.raises(ValueError):
        showcase.camera_for("nope", BOUNDS)


# ----------------------------------------------------------------------------- hashing and churn


def test_inputs_hash_is_stable_and_follows_one_byte(tmp_path):
    exports = make_exports(tmp_path)
    before = {(j.target, j.view): j.inputs_sha256 for j in plan(exports)}
    assert before == {(j.target, j.view): j.inputs_sha256 for j in plan(exports)}
    lid = exports / "case-a" / "lid.model.stl"
    lid.write_bytes(lid.read_bytes().replace(b"vertex 20.0 10.0 6.0", b"vertex 20.0 10.0 6.5", 1))
    after = {(j.target, j.view): j.inputs_sha256 for j in plan(exports)}
    changed = {k for k in before if before[k] != after[k]}
    assert changed == {("case-a", "iso"), ("case-a", "patch-wall")}  # the views that draw the lid, nothing else
    assert plan(exports, "another-fingerprint")[0].inputs_sha256 != after["case-a", "iso"]


def test_fingerprint_covers_size_and_requirements():
    base = showcase.render_fingerprint((1600, 1000), "pyvista==1\n")
    assert base == showcase.render_fingerprint((1600, 1000), "pyvista==1\n")
    assert base != showcase.render_fingerprint((1600, 1000), "pyvista==2\n")
    assert base != showcase.render_fingerprint((800, 500), "pyvista==1\n")


def test_unchanged_manifest_plans_nothing(tmp_path):
    jobs = plan(make_exports(tmp_path))
    manifest = showcase.build_manifest(jobs, tmp_path / "out")
    assert showcase.plan_outputs(jobs, manifest) == []               # no churn
    assert len(showcase.plan_outputs(jobs, None)) == len(jobs)       # no previous manifest: everything
    stale = json.loads(json.dumps(manifest))
    stale["images"]["case-a-iso.png"]["inputs_sha256"] = "0" * 64
    assert [j.image for j in showcase.plan_outputs(jobs, stale)] == ["case-a-iso.png"]
    stale["renderer"] = "old"
    assert len(showcase.plan_outputs(jobs, stale)) == len(jobs)      # a new renderer version redraws all


def test_a_missing_png_is_rendered_again(tmp_path):
    jobs = plan(make_exports(tmp_path))
    out = tmp_path / "out"
    out.mkdir()
    manifest = showcase.build_manifest(jobs, out)
    assert len(showcase.plan_outputs(jobs, manifest, out)) == len(jobs)
    for job in jobs:
        (out / job.image).write_bytes(b"png")
    assert showcase.plan_outputs(jobs, manifest, out) == []


def test_manifest_is_written_once(tmp_path):
    jobs = plan(make_exports(tmp_path))
    path = tmp_path / "manifest.json"
    manifest = showcase.build_manifest(jobs, tmp_path)
    assert showcase.write_manifest(manifest, path) is True
    stamp = path.stat().st_mtime_ns
    assert showcase.write_manifest(manifest, path) is False          # identical: file untouched
    assert path.stat().st_mtime_ns == stamp
    assert json.loads(path.read_text(encoding="utf-8"))["renderer"] == showcase.RENDERER_VERSION


# ---------------------------------------------------------------------------------------- budget


def sized(tmp_path: Path, n: int, size: int) -> list[Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        p = tmp_path / f"{i}.png"
        with p.open("wb") as f:
            f.truncate(size)
        paths.append(p)
    return paths


def test_budget_per_image(tmp_path):
    assert showcase.enforce_budget(sized(tmp_path, 1, 250 * 1024)) == 250 * 1024
    with pytest.raises(showcase.BudgetError):
        showcase.enforce_budget(sized(tmp_path / "x", 1, 250 * 1024 + 1))


def test_budget_total_and_count(tmp_path):
    with pytest.raises(showcase.BudgetError, match="total"):
        showcase.enforce_budget(sized(tmp_path / "a", 41, 250 * 1024), max_images=100)   # 41 x 250 KiB > 10 MiB
    with pytest.raises(showcase.BudgetError, match="limit of"):
        showcase.enforce_budget(sized(tmp_path / "b", showcase.MAX_IMAGES + 1, 10))
    assert showcase.enforce_budget(sized(tmp_path / "c", showcase.MAX_IMAGES, 10)) == showcase.MAX_IMAGES * 10


# ------------------------------------------------------------------------------------- CLI, errors


def test_missing_lid_is_a_clear_error(tmp_path, capsys):
    exports = make_exports(tmp_path)
    (exports / "case-b" / "lid.model.stl").unlink()
    assert showcase.main(["--exports", str(exports), "--out", str(tmp_path / "out")]) == 1
    err = capsys.readouterr().err
    assert "case-b" in err and "lid.model.stl" in err
    assert not (tmp_path / "out" / "case-a-iso.png").exists()         # nothing drawn before the check


def test_no_exports_and_no_case_are_errors(tmp_path, capsys):
    assert showcase.main(["--exports", str(tmp_path / "missing"), "--out", str(tmp_path / "o")]) == 1
    (tmp_path / "empty").mkdir()
    assert showcase.main(["--exports", str(tmp_path / "empty"), "--out", str(tmp_path / "o")]) == 1
    assert capsys.readouterr().err.count("error:") == 2


def test_unknown_only_target_is_an_error(tmp_path, capsys):
    exports = make_exports(tmp_path)
    assert showcase.main(["--exports", str(exports), "--out", str(tmp_path / "o"), "--only", "nope"]) == 1
    assert "nope" in capsys.readouterr().err


def prepared_run(tmp_path: Path):
    """Exports, plus an output folder that already holds every PNG and a matching manifest."""

    exports = make_exports(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    jobs = showcase.plan_jobs(showcase.discover_showcase_targets(exports), showcase.render_fingerprint())
    for job in jobs:
        (out / job.image).write_bytes(b"\x89PNG placeholder")
    showcase.write_manifest(showcase.build_manifest(jobs, out), out / "manifest.json")
    return exports, out, jobs


def test_unchanged_run_renders_nothing_and_writes_nothing(tmp_path, capsys):
    exports, out, jobs = prepared_run(tmp_path)
    stamps = {p.name: p.stat().st_mtime_ns for p in out.iterdir()}
    code = showcase.main(["--exports", str(exports), "--out", str(out), "--previous", str(out / "manifest.json")])
    assert code == 0
    assert f"{len(jobs)} image(s) planned, 0 rendered" in capsys.readouterr().out
    assert {p.name: p.stat().st_mtime_ns for p in out.iterdir()} == stamps   # no file touched: no diff, no PR
    assert "pyvista" not in sys.modules                                      # nothing was drawn


def test_oversized_image_fails_the_run(tmp_path, capsys):
    exports, out, jobs = prepared_run(tmp_path)
    with (out / jobs[0].image).open("wb") as f:
        f.truncate(showcase.MAX_IMAGE_BYTES + 1)
    code = showcase.main(["--exports", str(exports), "--out", str(out), "--previous", str(out / "manifest.json")])
    assert code == 1
    assert jobs[0].image in capsys.readouterr().err


def test_job_is_a_frozen_value():
    job = showcase.Job("a.png", "t", "iso", (), showcase.camera_for("iso", BOUNDS), (1600, 1000), "x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        job.image = "b.png"  # type: ignore[misc]
