#!/usr/bin/env python3
"""Showcase renders per case: PNG images made from the exported model-frame STL files (issue #74).

Pure planning half of the showcase pipeline: target discovery, the view table, camera maths, input
hashing, the manifest, the size budget and the CLI. It imports no OpenGL code (no pyvista, no vtk) and
neither `build` nor `bambu_project`, nor anything from cad/: the pixels are drawn by
`scripts/showcase_gl.py`, imported only when an image has to be rendered, so the pytest job stays
GL-free (see scripts/tests/test_showcase.py).

Input contract (architecture.md D74.1 — the interface the Fusion pipeline must keep as well):

    exports/<target>/<part>.model.stl      binary or ASCII STL, millimetres, ASSEMBLY frame, Z up

* Every `exports/<slug>/` except `coupons/` and `brackets/` that holds any `*.model.stl` is a CASE and
  must hold both `base.model.stl` and `lid.model.stl` (otherwise exit 1). `ghost_device.model.stl` is
  an optional extra (drawn as a faint box when present); other parts of a case (`base_fan`, ...) are
  ignored.
* `exports/brackets/<name>/*.model.stl` is a BRACKET target: its parts are laid out side by side along X
  (each translated by its own bounding box plus a fixed gap), never re-posed.

Output per case `<slug>-iso.png`, `<slug>-patch-wall.png`, `<slug>-underside.png`; per bracket target
`brackets-<name>.png`; plus `manifest.json` in the same folder.

Usage:
    python scripts/showcase.py --exports exports --out dist/renders
    python scripts/showcase.py --out docs/renders --previous docs/renders/manifest.json   # only changed views
    python scripts/showcase.py --only pro-convert-hdmi-tx --size 1200x750

Re-rendering is decided by input hashes, never by pixel identity (software GL may differ across Mesa
and VTK versions): an image is drawn again only when the `inputs_sha256` of its manifest entry changed,
its file is missing, or `--previous` was not given. Exit code 1 on a missing input or a budget breach.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import trimesh

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_RENDER = REPO_ROOT / "requirements-render.txt"

RENDERER_VERSION = "1"            # bump when the drawing code (showcase_gl.py) changes its output
MODEL_STL_SUFFIX = ".model.stl"
EXCLUDED_DIRS = ("coupons", "brackets")   # exports/ children that are not cases
BRACKETS_DIR = "brackets"
REQUIRED_CASE_PARTS = ("base", "lid")
GHOST_PART = "ghost_device"

# Patch wall (outward normal) in the model frame: +Y = towards the patch wall, -Y = the far wall that
# carries the side bolt (.claude/knowledge/layout-patch-wall.md:217, the axis table of section 1).
PATCH_WALL_NORMAL = (0.0, 1.0, 0.0)

DEFAULT_SIZE = (1600, 1000)
BACKGROUND = "#f2f3f5"            # flat, so the PNG palette stays small
PALETTE_COLOURS = 128
VIEW_ANGLE_DEG = 30.0             # perspective views
# Cameras: (horizontal base direction, azimuth deg turned from it around Z, elevation deg; < 0 = from below).
# All are perspective: a head-on orthographic view of a flat wall or floor shows no depth (seen on the first
# renders: hole walls and the undercut dovetail flanks vanish), so the patch wall is looked at slightly from
# the side and above, and the underside obliquely from the +X end (the groove's entrance) and +Y.
PERSPECTIVE_CAMERAS = {
    "iso": (PATCH_WALL_NORMAL, 35.0, 30.0),
    "patch-wall": (PATCH_WALL_NORMAL, -18.0, 12.0),
    "underside": ((1.0, 0.0, 0.0), 30.0, -35.0),
    "row": (PATCH_WALL_NORMAL, -10.0, 42.0),           # bracket parts in one row along X
}
FIT_MARGIN = 1.08                 # empty border around the model
BRACKET_GAP_MM = 10.0

# Budget tripwire (D74.3's numbers, enforced already in PR 1 on whatever folder is written).
MAX_IMAGE_BYTES = 250 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024
MAX_IMAGES = 40

# role -> (colour, opacity): ASA-grey base, pale-blue translucent lid, amber faint device ghost.
ROLE_STYLE = {
    "base": ("#707882", 1.0),
    "lid": ("#9fb4c8", 0.35),
    "ghost": ("#c9a227", 0.15),
    "part": ("#707882", 1.0),
}

Vec3 = tuple[float, float, float]


class ShowcaseError(Exception):
    """A missing or malformed input; the CLI prints it and exits 1."""


class BudgetError(ShowcaseError):
    """An image or the whole folder exceeds the size budget."""


@dataclasses.dataclass(frozen=True)
class View:
    """One image per target of `kind`: which roles are drawn, from which camera, at what lid opacity."""

    key: str
    kind: str                     # "case" | "bracket"
    filename: str                 # template with {name}
    roles: tuple[str, ...]
    camera: str                   # "iso" | "patch-wall" | "underside" | "row" (see camera_for)
    lid_opacity: float = ROLE_STYLE["lid"][1]


VIEWS: tuple[View, ...] = (
    View("iso", "case", "{name}-iso.png", ("base", "lid", "ghost"), "iso"),
    View("patch-wall", "case", "{name}-patch-wall.png", ("base", "lid"), "patch-wall", lid_opacity=1.0),
    View("underside", "case", "{name}-underside.png", ("base",), "underside"),
    View("bracket", "bracket", "brackets-{name}.png", ("part",), "row"),
)


@dataclasses.dataclass(frozen=True)
class Target:
    kind: str                                   # "case" | "bracket"
    name: str                                   # case slug / bracket name
    parts: tuple[tuple[str, Path], ...]         # (part name, .model.stl path), sorted by name


@dataclasses.dataclass(frozen=True)
class Camera:
    position: Vec3
    focal: Vec3
    up: Vec3
    view_angle: float                           # degrees, vertical


@dataclasses.dataclass(frozen=True)
class MeshSpec:
    path: Path
    role: str
    colour: str
    opacity: float
    offset: Vec3


@dataclasses.dataclass(frozen=True)
class Job:
    image: str
    target: str
    view: str
    meshes: tuple[MeshSpec, ...]
    camera: Camera
    size: tuple[int, int]
    inputs_sha256: str


# --------------------------------------------------------------------------------------------- discovery


def discover_showcase_targets(exports_dir: Path) -> list[Target]:
    """Cases (sorted by slug) then bracket targets (sorted by name), read from the exports layout only."""

    exports_dir = Path(exports_dir)
    if not exports_dir.is_dir():
        raise ShowcaseError(f"exports folder not found: {exports_dir}")

    targets: list[Target] = []
    for d in sorted(p for p in exports_dir.iterdir() if p.is_dir() and p.name not in EXCLUDED_DIRS):
        stls = _model_stls(d)
        if not stls:
            continue
        missing = [part for part in REQUIRED_CASE_PARTS if part not in stls]
        if missing:
            raise ShowcaseError(
                f"case '{d.name}' has no {', '.join(m + MODEL_STL_SUFFIX for m in missing)} in {d} "
                f"(a case needs {' and '.join(p + MODEL_STL_SUFFIX for p in REQUIRED_CASE_PARTS)})"
            )
        parts = [(part, stls[part]) for part in REQUIRED_CASE_PARTS]
        if GHOST_PART in stls:
            parts.append((GHOST_PART, stls[GHOST_PART]))
        targets.append(Target("case", d.name, tuple(parts)))

    bracket_root = exports_dir / BRACKETS_DIR
    if bracket_root.is_dir():
        for d in sorted(p for p in bracket_root.iterdir() if p.is_dir()):
            stls = _model_stls(d)
            if stls:
                targets.append(Target("bracket", d.name, tuple(sorted(stls.items()))))

    if not any(t.kind == "case" for t in targets):
        raise ShowcaseError(f"no case with *{MODEL_STL_SUFFIX} found under {exports_dir}")
    return targets


def _model_stls(directory: Path) -> dict[str, Path]:
    return {f.name[: -len(MODEL_STL_SUFFIX)]: f for f in directory.glob(f"*{MODEL_STL_SUFFIX}") if f.is_file()}


# ------------------------------------------------------------------------------------------ camera maths


def camera_for(camera: str, bounds: Sequence[Sequence[float]], aspect: float = DEFAULT_SIZE[0] / DEFAULT_SIZE[1]) -> Camera:
    """Camera that frames the axis-aligned `bounds` ((xmin, ymin, zmin), (xmax, ymax, zmax)) exactly.

    Every camera is a perspective camera with Z up, looking at the centre of `bounds` from the direction
    named in PERSPECTIVE_CAMERAS (iso, patch-wall, underside, row); the distance is the smallest at which all
    eight corners of the box fit the picture (plus FIT_MARGIN).
    """

    if camera not in PERSPECTIVE_CAMERAS:
        raise ValueError(f"unknown camera '{camera}'")
    lo, hi = np.asarray(bounds[0], dtype=float), np.asarray(bounds[1], dtype=float)
    centre = (lo + hi) / 2.0
    half = (hi - lo) / 2.0
    corners = np.array([[sx * half[0], sy * half[1], sz * half[2]] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    up = np.array([0.0, 0.0, 1.0])

    (bx, by, _), az_deg, el_deg = PERSPECTIVE_CAMERAS[camera]
    az, el = math.radians(az_deg), math.radians(el_deg)
    hx, hy = bx * math.cos(az) - by * math.sin(az), bx * math.sin(az) + by * math.cos(az)
    toward = np.array([hx * math.cos(el), hy * math.cos(el), math.sin(el)])   # focal point -> camera

    right = np.cross(-toward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, -toward)
    x, y, w = corners @ right, corners @ true_up, corners @ toward   # screen x, screen y, offset towards the camera

    tan_half = math.tan(math.radians(VIEW_ANGLE_DEG) / 2.0) / FIT_MARGIN
    distance = float(np.max(np.maximum(np.abs(y) / tan_half, np.abs(x) / (tan_half * aspect)) + w))
    position = centre + toward * distance
    return Camera(position=_vec(position), focal=_vec(centre), up=_vec(up), view_angle=VIEW_ANGLE_DEG)


def _vec(a: Iterable[float]) -> Vec3:
    x, y, z = (float(v) for v in a)
    return (x, y, z)


def mesh_bounds(path: Path) -> np.ndarray:
    """(2, 3) array of the STL's axis-aligned bounds."""

    try:
        mesh = trimesh.load_mesh(str(path), file_type="stl", process=False)
        bounds = np.asarray(mesh.bounds, dtype=float)
    except Exception as exc:  # trimesh raises many types for a bad file
        raise ShowcaseError(f"cannot read {path}: {exc}") from exc
    if bounds.shape != (2, 3) or not np.all(np.isfinite(bounds)):
        raise ShowcaseError(f"{path} holds no geometry")
    return bounds


# ------------------------------------------------------------------------------------- hashing, planning


def render_fingerprint(size: tuple[int, int] = DEFAULT_SIZE, requirements_text: str | None = None) -> str:
    """sha256 over everything besides the STL bytes that shapes a picture: the renderer version, the
    view table, all render parameters (size, colours, opacities, camera) and requirements-render.txt."""

    if requirements_text is None:
        requirements_text = REQUIREMENTS_RENDER.read_text(encoding="utf-8") if REQUIREMENTS_RENDER.is_file() else ""
    payload = {
        "renderer": RENDERER_VERSION,
        "views": [dataclasses.asdict(v) for v in VIEWS],
        "params": {
            "size": list(size),
            "background": BACKGROUND,
            "palette_colours": PALETTE_COLOURS,
            "view_angle_deg": VIEW_ANGLE_DEG,
            "perspective_cameras": {k: [list(v[0]), v[1], v[2]] for k, v in sorted(PERSPECTIVE_CAMERAS.items())},
            "fit_margin": FIT_MARGIN,
            "bracket_gap_mm": BRACKET_GAP_MM,
            "patch_wall_normal": list(PATCH_WALL_NORMAL),
            "role_style": {k: list(v) for k, v in sorted(ROLE_STYLE.items())},
        },
        "requirements_render": requirements_text,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inputs_hash(meshes: Sequence[MeshSpec], view_key: str, fingerprint: str) -> str:
    """sha256 of the sorted (part, sha256(file bytes), offset) inputs of one view, the view key and the
    render fingerprint: stable for equal inputs, different when any input byte or parameter changes."""

    items = sorted((m.role, m.path.name, _sha256_file(m.path), list(m.offset)) for m in meshes)
    blob = json.dumps({"fingerprint": fingerprint, "view": view_key, "inputs": items}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def plan_jobs(targets: Sequence[Target], fingerprint: str, size: tuple[int, int] = DEFAULT_SIZE) -> list[Job]:
    """Every image the targets yield: three per case, one per bracket target."""

    aspect = size[0] / size[1]
    jobs: list[Job] = []
    for target in targets:
        bounds = {path: mesh_bounds(path) for _, path in target.parts}
        for view in (v for v in VIEWS if v.kind == target.kind):
            if target.kind == "bracket":
                meshes = _bracket_meshes(target, bounds)
            else:
                meshes = _case_meshes(target, view)
            # A faint ghost never widens the frame: frame the solid parts only (all if there is no other).
            solid = [m for m in meshes if m.role != "ghost"] or list(meshes)
            lo = np.min([bounds[m.path][0] + np.asarray(m.offset) for m in solid], axis=0)
            hi = np.max([bounds[m.path][1] + np.asarray(m.offset) for m in solid], axis=0)
            jobs.append(Job(
                image=view.filename.format(name=target.name),
                target=target.name,
                view=view.key,
                meshes=tuple(meshes),
                camera=camera_for(view.camera, (lo, hi), aspect),
                size=size,
                inputs_sha256=inputs_hash(meshes, view.key, fingerprint),
            ))
    return jobs


def _case_meshes(target: Target, view: View) -> list[MeshSpec]:
    meshes: list[MeshSpec] = []
    for part, path in target.parts:
        role = "ghost" if part == GHOST_PART else part
        if role not in view.roles:
            continue
        colour, opacity = ROLE_STYLE[role]
        if role == "lid":
            opacity = view.lid_opacity
        meshes.append(MeshSpec(path, role, colour, opacity, (0.0, 0.0, 0.0)))
    return meshes


def _bracket_meshes(target: Target, bounds: dict[Path, np.ndarray]) -> list[MeshSpec]:
    """Parts side by side along X, each shifted by its own bounding box plus BRACKET_GAP_MM."""

    colour, opacity = ROLE_STYLE["part"]
    meshes: list[MeshSpec] = []
    cursor = 0.0
    for _, path in target.parts:
        lo, hi = bounds[path][0], bounds[path][1]
        meshes.append(MeshSpec(path, "part", colour, opacity, (cursor - float(lo[0]), 0.0, 0.0)))
        cursor += float(hi[0] - lo[0]) + BRACKET_GAP_MM
    return meshes


def plan_outputs(jobs: Sequence[Job], previous_manifest: dict | None = None, out_dir: Path | None = None) -> list[Job]:
    """The jobs that must be (re)rendered: all of them without a previous manifest, else only those whose
    renderer version or `inputs_sha256` differs from it — or, when `out_dir` is given, whose PNG is missing."""

    if not previous_manifest or previous_manifest.get("renderer") != RENDERER_VERSION:
        return list(jobs)
    images = previous_manifest.get("images", {})
    todo: list[Job] = []
    for job in jobs:
        entry = images.get(job.image)
        if entry is None or entry.get("inputs_sha256") != job.inputs_sha256:
            todo.append(job)
        elif out_dir is not None and not (Path(out_dir) / job.image).is_file():
            todo.append(job)
    return todo


# ------------------------------------------------------------------------------- manifest and the budget


def build_manifest(jobs: Sequence[Job], out_dir: Path) -> dict:
    images = {}
    for job in sorted(jobs, key=lambda j: j.image):
        png = Path(out_dir) / job.image
        images[job.image] = {"inputs_sha256": job.inputs_sha256, "bytes": png.stat().st_size if png.is_file() else 0}
    return {"renderer": RENDERER_VERSION, "images": images}


def write_manifest(manifest: dict, path: Path) -> bool:
    """Write the manifest deterministically; return False (and touch nothing) when it is unchanged."""

    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    path = Path(path)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def enforce_budget(
    paths: Iterable[Path], *, max_image_bytes: int = MAX_IMAGE_BYTES,
    max_total_bytes: int = MAX_TOTAL_BYTES, max_images: int = MAX_IMAGES,
) -> int:
    """Raise BudgetError when one image, the image count or the total is over budget; return the total."""

    sizes = [(Path(p), Path(p).stat().st_size) for p in paths]
    for p, n in sizes:
        if n > max_image_bytes:
            raise BudgetError(f"{p.name} is {n} bytes, over the {max_image_bytes} byte limit per image")
    if len(sizes) > max_images:
        raise BudgetError(f"{len(sizes)} images, over the limit of {max_images}")
    total = sum(n for _, n in sizes)
    if total > max_total_bytes:
        raise BudgetError(f"images total {total} bytes, over the {max_total_bytes} byte budget")
    return total


# --------------------------------------------------------------------------------------------------- CLI


def _parse_size(text: str) -> tuple[int, int]:
    try:
        w, h = (int(v) for v in text.lower().split("x"))
        if w < 100 or h < 100:
            raise ValueError
        return (w, h)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--size wants WxH in pixels, at least 100x100 (got '{text}')") from None


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render showcase PNGs from exports/<target>/<part>.model.stl.")
    ap.add_argument("--exports", type=Path, default=REPO_ROOT / "exports", help="exports folder (default: exports)")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "dist" / "renders", help="output folder (default: dist/renders)")
    ap.add_argument("--only", action="append", default=[], metavar="NAME", help="only this case slug or bracket name (repeatable)")
    ap.add_argument("--size", type=_parse_size, default=DEFAULT_SIZE, metavar="WxH", help="image size (default: 1600x1000)")
    ap.add_argument("--previous", type=Path, default=None, metavar="MANIFEST",
                    help="a previous manifest.json: render only the views whose inputs changed")
    args = ap.parse_args(argv)

    try:
        targets = discover_showcase_targets(args.exports)
        if args.only:
            unknown = sorted(set(args.only) - {t.name for t in targets})
            if unknown:
                raise ShowcaseError(f"unknown target(s): {', '.join(unknown)}")
            targets = [t for t in targets if t.name in args.only]

        jobs = plan_jobs(targets, render_fingerprint(args.size), args.size)
        previous = None
        if args.previous is not None:
            try:
                previous = json.loads(args.previous.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                previous = None       # no usable previous manifest: render everything
        todo = plan_outputs(jobs, previous, args.out)

        args.out.mkdir(parents=True, exist_ok=True)
        if todo:
            import showcase_gl        # the only GL import, and only when a picture must be drawn

            for job in todo:
                showcase_gl.render_scene(
                    job.meshes, job.camera, job.size, args.out / job.image,
                    background=BACKGROUND, palette_colours=PALETTE_COLOURS,
                )
                print(f"  [OK]   {job.image}")
        print(f"{len(jobs)} image(s) planned, {len(todo)} rendered, {len(jobs) - len(todo)} unchanged")

        total = enforce_budget(args.out / j.image for j in jobs)
        if write_manifest(build_manifest(jobs, args.out), args.out / "manifest.json"):
            print(f"  [OK]   manifest.json ({total} bytes of images)")
    except ShowcaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
