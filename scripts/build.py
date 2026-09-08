#!/usr/bin/env python3
"""Single build/test entry point for magewell-converter-cases.

Wraps the pinned OpenSCAD CLI (Manifold backend) and trimesh mesh checks behind one
implementation, per .claude/knowledge/architecture.md §8 (export policy) and §9 (4-tier test
policy). scripts/render.ps1 is a thin PowerShell wrapper over this file — do not duplicate this
logic there.

Subcommands: render, step, smoke, check, golden, confidence, all, doctor. Run `build.py --help` or
`build.py <subcommand> --help` for details.

Requires Python 3.11+, stdlib + trimesh (see requirements.txt). `step` additionally needs a STEP
backend — `cadquery-ocp` (see requirements-step.txt) or FreeCAD's `freecadcmd` — see
`scripts/mesh_to_step.py`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    import trimesh
except ImportError:  # trimesh is optional for `doctor`; required for `check`/`golden`/`render`'s
    trimesh = None   # mesh measurement and for `all`.

import mesh_to_step  # sibling module in scripts/ — STL -> STEP conversion, both backends

# -----------------------------------------------------------------------------------------
# Constants (single source of truth for build-time policy numbers; keep this the only place
# these are defined so CI and local runs can never disagree).
# -----------------------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "lib"
MODELS_DIR = REPO_ROOT / "models"
COUPONS_DIR = MODELS_DIR / "coupons"
TESTS_DIR = REPO_ROOT / "tests"
GOLDEN_DIR = TESTS_DIR / "golden"
EXPORTS_DIR = REPO_ROOT / "exports"

WINDOWS_OPENSCAD_DEFAULT = Path(r"C:\Program Files\OpenSCAD (Nightly)\openscad.com")

MCC_BUILD_MM = 256.0        # Bambu X1C/P1S build cube edge, mm (architecture.md:44)
MCC_BED_MARGIN_MM = 6.0     # keep-out margin from the bed edge, mm (lib/mcc/constants.scad MCC_BED_MARGIN)
MAX_AXIS_MM = MCC_BUILD_MM - 2 * MCC_BED_MARGIN_MM  # 244 mm — Tier-3 `check` bbox ceiling per axis

GOLDEN_VOLUME_TOL = 0.005   # 0.5 % relative
GOLDEN_BBOX_TOL_MM = 0.1    # 0.1 mm absolute, per axis
GOLDEN_AREA_TOL = 0.01      # 1 % relative
# Facet-count differences are informational only (mesh tessellation can shift facet count for
# reasons that don't reflect intended geometry change) — never a golden failure by themselves.

RELEASE_WARNING_MARKER = "WARNING: unmeasured"

EXPORT_EXT = {"stl": ".stl", "3mf": ".3mf"}

# Mirrors lib/mcc/constants.scad:622 MCC_CONFIDENCE_ORDER. Python can't evaluate OpenSCAD, so
# `confidence` (below) reads device data files as text instead of asking OpenSCAD to render them —
# this list must be kept in sync with constants.scad by hand if that ever changes.
CONFIDENCE_ORDER = ["assumed", "photo", "manual", "drawing", "measured"]


# -----------------------------------------------------------------------------------------
# Data model
# -----------------------------------------------------------------------------------------

@dataclass
class Target:
    """One renderable thing: a coupon, a model (case), or an ad-hoc .scad path."""

    name: str            # e.g. "coupons/neutrik-tile", "pro-convert-hdmi-tx", or a bare path stem
    scad_path: Path
    parts: list[str]
    kind: str = "model"  # "coupon" | "model" | "adhoc"

    @property
    def export_dir(self) -> Path:
        return EXPORTS_DIR / self.name


@dataclass
class RenderResult:
    target: str
    part: str
    ok: bool
    outputs: list[Path] = field(default_factory=list)
    summary_path: Path | None = None
    manifest_path: Path | None = None
    error: str | None = None


@dataclass
class StepBuildResult:
    target: str
    part: str
    ok: bool
    backend: str | None = None
    step_path: Path | None = None
    faces_before_unify: int | None = None
    faces_after_unify: int | None = None
    size_bytes: int | None = None
    error: str | None = None


@dataclass
class MeshCheck:
    path: Path
    watertight: bool = False
    winding_consistent: bool = False
    volume_mm3: float = 0.0
    volume_ok: bool = False
    n_parts: int = -1
    parts_ok: bool = False
    extents: tuple[float, float, float] = (0.0, 0.0, 0.0)
    bbox_ok: bool = False
    error: str | None = None

    @property
    def ok(self) -> bool:
        return (
            self.error is None
            and self.watertight
            and self.winding_consistent
            and self.volume_ok
            and self.parts_ok
            and self.bbox_ok
        )


# -----------------------------------------------------------------------------------------
# Discovery
# -----------------------------------------------------------------------------------------

def discover_coupons() -> list[Target]:
    if not COUPONS_DIR.is_dir():
        return []
    targets = []
    for scad_path in sorted(COUPONS_DIR.glob("*.scad")):
        stem = scad_path.stem
        targets.append(Target(name=f"coupons/{stem}", scad_path=scad_path, parts=[stem], kind="coupon"))
    return targets


def discover_models() -> list[Target]:
    if not MODELS_DIR.is_dir():
        return []
    targets = []
    for case_path in sorted(MODELS_DIR.glob("*/case.scad")):
        slug = case_path.parent.name
        if slug == "coupons":
            continue
        parts = ["base", "lid"]
        try:
            text = case_path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if 'part == "panel"' in text:
            parts.append("panel")
        for extra in _extra_parts(text):
            if extra not in parts:
                parts.append(extra)
        targets.append(Target(name=slug, scad_path=case_path, parts=parts, kind="model"))
    return targets


# A model's case.scad can declare additional `-D part="..."` values beyond the hardcoded
# base/lid(/panel) set above via a `// build.py: extra_parts = <name>[, <name>...]` comment marker
# (issue #11 — e.g. `base_fan`, a fixed-config variant of an existing part=="base" branch, added so
# CI renders/checks/golden-tracks it like any other part without build.py needing to know what the
# variant actually configures — that stays entirely inside case.scad's own `if (part == ...)`
# dispatch). Each declared name becomes an ordinary Target.parts entry: rendered with plain
# `-D part="<name>"` (render_part() never needs a part-specific `-D` override — the .scad file's own
# dispatch is what makes "base_fan" behave differently from "base"), then checked and golden-tracked
# exactly like base/lid/panel.
_EXTRA_PARTS_MARKER_RE = re.compile(r"//\s*build\.py:\s*extra_parts\s*=\s*(.+)")


def _extra_parts(case_scad_text: str) -> list[str]:
    names: list[str] = []
    for m in _EXTRA_PARTS_MARKER_RE.finditer(case_scad_text):
        for raw in m.group(1).split(","):
            name = raw.strip()
            if name and name not in names:
                names.append(name)
    return names


def discover_all() -> list[Target]:
    return discover_coupons() + discover_models()


def resolve_targets(names: list[str], part_override: list[str] | None) -> list[Target]:
    """Resolve CLI target strings to Target objects: 'coupons/<name>', '<slug>', or a path."""

    catalog = {t.name: t for t in discover_all()}
    resolved: list[Target] = []
    for name in names:
        if name in catalog:
            t = catalog[name]
            if part_override:
                t = Target(name=t.name, scad_path=t.scad_path, parts=part_override, kind=t.kind)
            resolved.append(t)
            continue

        path = Path(name)
        if path.suffix == ".scad" and path.is_file():
            parts = part_override or [path.stem]
            resolved.append(Target(name=path.stem, scad_path=path.resolve(), parts=parts, kind="adhoc"))
            continue

        raise SystemExit(
            f"error: unknown target '{name}' — not a discovered coupon/model and not an "
            f"existing .scad path. Run `build.py doctor` to list discovered targets."
        )
    return resolved


# -----------------------------------------------------------------------------------------
# OpenSCAD location / git metadata
# -----------------------------------------------------------------------------------------

def find_openscad() -> Path:
    import os

    env = os.environ.get("MCC_OPENSCAD")
    if env:
        p = Path(env)
        if p.is_file():
            return p
        which = shutil.which(env)
        if which:
            return Path(which)
        raise SystemExit(f"error: MCC_OPENSCAD='{env}' does not exist and is not on PATH")

    if WINDOWS_OPENSCAD_DEFAULT.is_file():
        return WINDOWS_OPENSCAD_DEFAULT

    which = shutil.which("openscad")
    if which:
        return Path(which)

    raise SystemExit(
        "error: could not locate OpenSCAD. Set MCC_OPENSCAD, install the Windows nightly at "
        f"'{WINDOWS_OPENSCAD_DEFAULT}', or put 'openscad' on PATH."
    )


def openscad_version(exe: Path) -> str:
    proc = subprocess.run([str(exe), "--version"], capture_output=True, text=True, check=False)
    text = (proc.stdout or "") + (proc.stderr or "")
    return text.strip().splitlines()[-1] if text.strip() else "unknown"


def _git(args: list[str], cwd: Path) -> str | None:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def git_head_sha(repo_root: Path = REPO_ROOT) -> str | None:
    return _git(["rev-parse", "HEAD"], repo_root)


def git_dirty(repo_root: Path = REPO_ROOT) -> bool:
    out = _git(["status", "--porcelain"], repo_root)
    return bool(out)


def bosl2_sha(repo_root: Path = REPO_ROOT) -> str | None:
    bosl2_dir = repo_root / "lib" / "BOSL2"
    if not bosl2_dir.is_dir():
        return None
    return _git(["rev-parse", "HEAD"], bosl2_dir)


def _running_in_ci() -> bool:
    # GitHub Actions sets CI=true on every runner. Used to decide whether a missing STEP backend
    # is a warn-and-skip (local dev machine) or a hard failure (`step` must succeed in CI).
    return os.environ.get("CI", "").lower() == "true"


# -----------------------------------------------------------------------------------------
# OpenSCAD invocation
# -----------------------------------------------------------------------------------------

def _parse_defines(raw: list[str]) -> dict[str, str]:
    defines: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise SystemExit(f"error: -D '{item}' is not in k=v form")
        k, v = item.split("=", 1)
        defines[k] = v
    return defines


def run_openscad(
    exe: Path,
    scad_path: Path,
    defines: dict[str, str],
    outputs: list[Path],
    summary_file: Path | None,
) -> tuple[bool, list[str]]:
    """Run OpenSCAD, streaming stderr. Returns (ok, captured_stderr_lines)."""

    import os

    args = [str(exe), "--backend=Manifold"]
    for k, v in defines.items():
        args += ["-D", f"{k}={v}"]
    for out in outputs:
        out.parent.mkdir(parents=True, exist_ok=True)
        args += ["-o", str(out)]
    if summary_file is not None:
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        args += ["--summary", "all", "--summary-file", str(summary_file)]
    args.append(str(scad_path))

    env = dict(os.environ)
    env["OPENSCADPATH"] = str(LIB_DIR)

    proc = subprocess.Popen(
        args, cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    lines: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\n")
        print(f"    [openscad] {line}")
        lines.append(line)
    returncode = proc.wait()

    has_error = any("ERROR:" in ln for ln in lines)
    ok = returncode == 0 and not has_error
    return ok, lines


# -----------------------------------------------------------------------------------------
# Mesh measurement (trimesh) — used to augment OpenSCAD's summary (which does not emit
# volume/area for 3D solids in the pinned 2025.09.07 nightly build; confirmed by direct testing)
# and to back the `check` subcommand's Tier-3 mesh checks.
# -----------------------------------------------------------------------------------------

def _require_trimesh() -> None:
    if trimesh is None:
        raise SystemExit(
            "error: trimesh is not installed. Run: .venv\\Scripts\\python -m pip install -r requirements.txt"
        )


def measure_mesh(stl_path: Path) -> tuple[float, float, int]:
    """Returns (volume_mm3, area_mm2, facet_count) for an STL, via trimesh."""

    _require_trimesh()
    mesh = trimesh.load(str(stl_path), force="mesh")
    return float(mesh.volume), float(mesh.area), int(len(mesh.faces))


def check_mesh(path: Path) -> MeshCheck:
    _require_trimesh()
    check = MeshCheck(path=path)
    try:
        mesh = trimesh.load(str(path), force="mesh")
    except Exception as exc:  # noqa: BLE001 — surface any loader failure as a check failure
        check.error = f"load failed: {exc}"
        return check

    check.watertight = bool(mesh.is_watertight)
    check.winding_consistent = bool(mesh.is_winding_consistent)
    check.volume_mm3 = float(mesh.volume)
    check.volume_ok = check.volume_mm3 > 0

    try:
        parts = mesh.split(only_watertight=False)
        check.n_parts = len(parts)
    except Exception as exc:  # noqa: BLE001
        check.error = f"split() failed: {exc}"
        check.n_parts = -1
    check.parts_ok = check.n_parts == 1

    extents = tuple(float(x) for x in mesh.bounding_box.extents)
    check.extents = extents  # type: ignore[assignment]
    check.bbox_ok = all(x <= MAX_AXIS_MM + 1e-6 for x in extents)

    return check


# -----------------------------------------------------------------------------------------
# render
# -----------------------------------------------------------------------------------------

def render_part(
    target: Target,
    part: str,
    fmt: str,
    extra_defines: dict[str, str],
    release: bool,
    exe: Path,
) -> RenderResult:
    print(f"-> render {target.name} part={part} format={fmt}")

    formats = ["stl", "3mf"] if fmt == "both" else [fmt]
    export_dir = target.export_dir
    outputs = [export_dir / f"{part}{EXPORT_EXT[f]}" for f in formats]
    summary_path = export_dir / f"{part}.summary.json"
    manifest_path = export_dir / f"{part}.manifest.json"

    defines = {"part": f'"{part}"'}
    defines.update(extra_defines)

    # Ensure we always have an STL on disk to measure, even if only 3mf was requested — trimesh's
    # STL loader is the reliable path; 3MF loading pulls in extra optional deps.
    measure_stl = export_dir / f"{part}.stl" if "stl" in formats else export_dir / f"{part}._measure.stl"
    render_outputs = list(outputs)
    if "stl" not in formats:
        render_outputs = render_outputs + [measure_stl]

    ok, lines = run_openscad(exe, target.scad_path, defines, render_outputs, summary_path)

    if release:
        if any(RELEASE_WARNING_MARKER in ln for ln in lines):
            ok = False
            print(f"    [release] found '{RELEASE_WARNING_MARKER}' in OpenSCAD output — failing release build")

    if not ok:
        return RenderResult(target=target.name, part=part, ok=False, error="openscad failed (see log above)")

    # Augment the OpenSCAD summary with trimesh-measured volume/area/facets.
    try:
        volume_mm3, area_mm2, mesh_facets = measure_mesh(measure_stl)
    except Exception as exc:  # noqa: BLE001
        return RenderResult(target=target.name, part=part, ok=False, error=f"mesh measurement failed: {exc}")
    finally:
        if "stl" not in formats and measure_stl.exists():
            measure_stl.unlink()

    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    summary["mesh_volume_mm3"] = volume_mm3
    summary["mesh_area_mm2"] = area_mm2
    summary["mesh_facets"] = mesh_facets
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    bbox = summary.get("geometry", {}).get("bounding_box", {})
    manifest = {
        "target": target.name,
        "part": part,
        "git_head_sha": git_head_sha(),
        "git_dirty": git_dirty(),
        "bosl2_sha": bosl2_sha(),
        "openscad_version": openscad_version(exe),
        "defines": defines,
        "formats": formats,
        "outputs": [str(p.relative_to(REPO_ROOT).as_posix()) for p in outputs],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bbox": bbox,
        "volume_mm3": volume_mm3,
        "area_mm2": area_mm2,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return RenderResult(
        target=target.name, part=part, ok=True, outputs=outputs,
        summary_path=summary_path, manifest_path=manifest_path,
    )


def cmd_render(args: argparse.Namespace) -> int:
    exe = find_openscad()
    extra_defines = _parse_defines(args.defines or [])

    if args.all:
        targets = discover_all()
        if args.part:
            targets = [Target(name=t.name, scad_path=t.scad_path, parts=args.part, kind=t.kind) for t in targets]
    else:
        if not args.targets:
            raise SystemExit("error: render needs --all or at least one <target>")
        targets = resolve_targets(args.targets, args.part)

    if not targets:
        print("no targets discovered/resolved — nothing to render")
        return 0

    results: list[RenderResult] = []
    for target in targets:
        for part in target.parts:
            results.append(render_part(target, part, args.format, extra_defines, args.release, exe))

    _print_result_table("render", results)
    return 0 if all(r.ok for r in results) else 1


def _print_result_table(label: str, results: list[RenderResult]) -> None:
    print(f"\n{label} results:")
    width = max((len(f"{r.target}:{r.part}") for r in results), default=10)
    for r in results:
        status = "PASS" if r.ok else "FAIL"
        key = f"{r.target}:{r.part}".ljust(width)
        extra = f"  ({r.error})" if r.error else ""
        print(f"  [{status}] {key}{extra}")
    n_ok = sum(r.ok for r in results)
    print(f"  {n_ok}/{len(results)} passed")


# -----------------------------------------------------------------------------------------
# step  (STL -> STEP via scripts/mesh_to_step.py; see architecture.md §8 export policy)
# -----------------------------------------------------------------------------------------

def _update_manifest_with_step(target: Target, part: str, result) -> None:
    """Merge a `step` sub-object into the part's existing `<part>.manifest.json` (written by
    `render_part()`). Never overwrites the render-time fields — only adds/replaces `manifest["step"]`."""

    manifest_path = target.export_dir / f"{part}.manifest.json"
    manifest: dict = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}

    manifest["step"] = {
        "ok": result.ok,
        "backend": result.backend,
        "faces_before_unify": result.faces_before_unify,
        "faces_after_unify": result.faces_after_unify,
        "size_bytes": result.size_bytes,
        "validated": result.validated,
        "duration_s": round(result.duration_s, 2) if result.duration_s else None,
        "error": result.error,
        "path": (
            str(result.step_path.relative_to(REPO_ROOT).as_posix())
            if result.step_path is not None and result.step_path.is_file()
            else None
        ),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def cmd_step(args: argparse.Namespace) -> int:
    if args.all:
        targets = discover_all()
        if args.part:
            targets = [Target(name=t.name, scad_path=t.scad_path, parts=args.part, kind=t.kind) for t in targets]
    else:
        if not args.targets:
            raise SystemExit("error: step needs --all or at least one <target>")
        targets = resolve_targets(args.targets, args.part)

    if not targets:
        print("no targets discovered/resolved — nothing to convert")
        return 0

    backend, detail = mesh_to_step.backend_available()
    if backend is None:
        if _running_in_ci():
            print(f"error: no STEP backend available in CI — {detail}")
            return 1
        print(f"WARNING: no STEP backend available locally — {detail}")
        print("WARNING: skipping STEP export (local dev only; CI must succeed) — see scripts/mesh_to_step.py")
        return 0

    print(f"STEP backend: {backend} ({detail})")

    results: list[StepBuildResult] = []
    for target in targets:
        for part in target.parts:
            stl_path = target.export_dir / f"{part}.stl"
            if not stl_path.is_file():
                results.append(StepBuildResult(
                    target=target.name, part=part, ok=False,
                    error=f"no STL at {stl_path.relative_to(REPO_ROOT)} — run `render` first",
                ))
                continue

            step_path = target.export_dir / f"{part}.step"
            product_name = f"{target.name}/{part}"
            print(f"-> step {target.name} part={part}")
            r = mesh_to_step.convert(stl_path, step_path, product_name, backend=backend)
            _update_manifest_with_step(target, part, r)
            results.append(StepBuildResult(
                target=target.name, part=part, ok=r.ok, backend=r.backend, step_path=r.step_path,
                faces_before_unify=r.faces_before_unify, faces_after_unify=r.faces_after_unify,
                size_bytes=r.size_bytes, error=r.error,
            ))

    print("\nstep results:")
    width = max((len(f"{r.target}:{r.part}") for r in results), default=10)
    for r in results:
        status = "PASS" if r.ok else "FAIL"
        key = f"{r.target}:{r.part}".ljust(width)
        if r.ok:
            extra = f"  (faces {r.faces_before_unify}->{r.faces_after_unify}, {r.size_bytes} bytes)"
        else:
            extra = f"  ({r.error})"
        print(f"  [{status}] {key}{extra}")
    n_ok = sum(r.ok for r in results)
    print(f"  {n_ok}/{len(results)} passed")

    return 0 if all(r.ok for r in results) else 1


# -----------------------------------------------------------------------------------------
# smoke  (Tier 2 — headless smoke tests: -o *.csg evaluates the tree, asserts fire, no tessellation)
# -----------------------------------------------------------------------------------------

def cmd_smoke(_args: argparse.Namespace) -> int:
    exe = find_openscad()
    test_files = sorted(TESTS_DIR.glob("test_*.scad"))

    if not test_files:
        print("no tests/test_*.scad files found — nothing to smoke-test (this is not a failure)")
        return 0

    import tempfile

    results: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory(prefix="mcc_smoke_") as tmp:
        tmp_dir = Path(tmp)
        for test_file in test_files:
            print(f"-> smoke {test_file.relative_to(REPO_ROOT)}")
            csg_out = tmp_dir / f"{test_file.stem}.csg"
            ok, lines = run_openscad(exe, test_file, {}, [csg_out], None)
            err = "" if ok else "\n".join(ln for ln in lines if "ERROR:" in ln) or "openscad failed"
            results.append((str(test_file.relative_to(REPO_ROOT)), ok, err))

    print("\nsmoke results:")
    width = max(len(name) for name, _, _ in results)
    for name, ok, err in results:
        status = "PASS" if ok else "FAIL"
        extra = f"  ({err})" if err else ""
        print(f"  [{status}] {name.ljust(width)}{extra}")
    n_ok = sum(ok for _, ok, _ in results)
    print(f"  {n_ok}/{len(results)} passed")

    return 0 if all(ok for _, ok, _ in results) else 1


# -----------------------------------------------------------------------------------------
# check  (Tier 3 mesh checks via trimesh)
# -----------------------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    if args.all:
        paths = sorted(EXPORTS_DIR.glob("**/*.stl"))
    else:
        if not args.stl:
            raise SystemExit("error: check needs --all or at least one <stl> path")
        paths = [Path(p) for p in args.stl]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            raise SystemExit(f"error: file(s) not found: {', '.join(str(p) for p in missing)}")

    if not paths:
        print("no STL files found under exports/ — nothing to check (run `build.py render` first)")
        return 0

    checks = [check_mesh(p) for p in paths]

    print("\ncheck results:")
    width = max(len(str(c.path.relative_to(REPO_ROOT)) if _is_relative(c.path) else str(c.path)) for c in checks)
    for c in checks:
        status = "PASS" if c.ok else "FAIL"
        name = str(c.path.relative_to(REPO_ROOT)) if _is_relative(c.path) else str(c.path)
        if c.error:
            print(f"  [{status}] {name.ljust(width)}  ERROR: {c.error}")
            continue
        detail = (
            f"watertight={c.watertight} winding={c.winding_consistent} "
            f"volume={c.volume_mm3:.1f}mm3 parts={c.n_parts} "
            f"extents=({c.extents[0]:.1f},{c.extents[1]:.1f},{c.extents[2]:.1f})mm"
        )
        print(f"  [{status}] {name.ljust(width)}  {detail}")
    n_ok = sum(c.ok for c in checks)
    print(f"  {n_ok}/{len(checks)} passed  (bbox ceiling {MAX_AXIS_MM:.0f} mm per axis)")

    return 0 if all(c.ok for c in checks) else 1


def _is_relative(path: Path) -> bool:
    try:
        path.relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


# -----------------------------------------------------------------------------------------
# golden  (Tier 3 geometry goldens)
# -----------------------------------------------------------------------------------------

def golden_path(target_name: str, part: str) -> Path:
    """tests/golden/<slug>[.<part>].json — the `.part` suffix is dropped when the part name is
    already the target's own stem (i.e. coupons, whose single part == the file stem)."""

    stem = Path(target_name).name
    if part == stem:
        return GOLDEN_DIR / f"{target_name}.json"
    return GOLDEN_DIR / f"{target_name}.{part}.json"


def _golden_payload(summary: dict) -> dict:
    return {
        "bbox": summary.get("geometry", {}).get("bounding_box", {}),
        "volume_mm3": summary.get("mesh_volume_mm3"),
        "area_mm2": summary.get("mesh_area_mm2"),
        "facets": summary.get("mesh_facets"),
    }


def _compare_golden(current: dict, golden: dict) -> list[str]:
    mismatches: list[str] = []

    cur_size = current.get("bbox", {}).get("size")
    gold_size = golden.get("bbox", {}).get("size")
    if cur_size and gold_size:
        for axis, (c, g) in enumerate(zip(cur_size, gold_size)):
            if abs(c - g) > GOLDEN_BBOX_TOL_MM:
                mismatches.append(f"bbox axis {axis}: {c:.3f} vs golden {g:.3f} (tol {GOLDEN_BBOX_TOL_MM} mm)")
    elif cur_size != gold_size:
        mismatches.append(f"bbox size missing on one side: current={cur_size} golden={gold_size}")

    cur_vol, gold_vol = current.get("volume_mm3"), golden.get("volume_mm3")
    if cur_vol is not None and gold_vol:
        rel = abs(cur_vol - gold_vol) / gold_vol
        if rel > GOLDEN_VOLUME_TOL:
            mismatches.append(f"volume: {cur_vol:.2f} vs golden {gold_vol:.2f} ({rel * 100:.2f}% > {GOLDEN_VOLUME_TOL * 100:.1f}%)")

    cur_area, gold_area = current.get("area_mm2"), golden.get("area_mm2")
    if cur_area is not None and gold_area:
        rel = abs(cur_area - gold_area) / gold_area
        if rel > GOLDEN_AREA_TOL:
            mismatches.append(f"area: {cur_area:.2f} vs golden {gold_area:.2f} ({rel * 100:.2f}% > {GOLDEN_AREA_TOL * 100:.1f}%)")

    cur_facets, gold_facets = current.get("facets"), golden.get("facets")
    if cur_facets is not None and gold_facets is not None and cur_facets != gold_facets:
        print(f"    (informational) facets: {cur_facets} vs golden {gold_facets} — not a failure")

    return mismatches


def cmd_golden(args: argparse.Namespace) -> int:
    if args.targets:
        targets = resolve_targets(args.targets, None)
    else:
        targets = discover_all()

    if not targets:
        print("no targets discovered/resolved for golden comparison")
        return 0

    all_ok = True
    for target in targets:
        for part in target.parts:
            summary_path = target.export_dir / f"{part}.summary.json"
            gpath = golden_path(target.name, part)
            label = f"{target.name}:{part}"

            if not summary_path.exists():
                print(f"  [FAIL] {label}  no summary at {summary_path.relative_to(REPO_ROOT)} — run `render` first")
                all_ok = False
                continue

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            current = _golden_payload(summary)

            if args.update:
                gpath.parent.mkdir(parents=True, exist_ok=True)
                gpath.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
                print(f"  [UPDATED] {label}  -> {gpath.relative_to(REPO_ROOT)}")
                continue

            if not gpath.exists():
                print(f"  [FAIL] {label}  missing golden {gpath.relative_to(REPO_ROOT)} (run `golden --update` to create it)")
                all_ok = False
                continue

            golden = json.loads(gpath.read_text(encoding="utf-8"))
            mismatches = _compare_golden(current, golden)
            if mismatches:
                all_ok = False
                print(f"  [FAIL] {label}")
                for m in mismatches:
                    print(f"           {m}")
            else:
                print(f"  [PASS] {label}")

    return 0 if all_ok else 1


# -----------------------------------------------------------------------------------------
# confidence  (release-softener: reports ports below "measured", never fails — see issue #10.
# lib/mcc/devices/*.scad is DATA ONLY (architecture.md §3), so this reads it as text rather than
# asking OpenSCAD to evaluate it; ports.scad's own mcc_warn_unmeasured() is the OpenSCAD-side
# source of truth for the *format* of an unmeasured warning, but nothing in lib/models/**
# currently calls it at render time, so its echo() output can't be relied on here.)
# -----------------------------------------------------------------------------------------

_DEVICE_INCLUDE_RE = re.compile(r"include\s*<mcc/devices/([^>]+)\.scad>")
_PORT_ID_RE = re.compile(r'\[\s*"id"\s*,\s*"([^"]*)"\s*\]')
_PORT_CONFIDENCE_RE = re.compile(r'\[\s*"confidence"\s*,\s*"([^"]*)"\s*\]')


def confidence_rank(level: str) -> int:
    try:
        return CONFIDENCE_ORDER.index(level)
    except ValueError:
        return -1  # unrecognized level — treat as below everything ("definitely not measured")


def _find_matching_bracket(text: str, open_idx: int) -> int:
    """text[open_idx] must be '['. Returns the index of its matching ']'."""

    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced brackets")


def _extract_top_level_bracket_items(text: str) -> list[str]:
    """`text` is the inside of a `[ ... ]` list. Returns each top-level `[...]` item's substring
    (nested brackets are not split on)."""

    items = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "[":
            j = _find_matching_bracket(text, i)
            items.append(text[i:j + 1])
            i = j + 1
        else:
            i += 1
    return items


def parse_device_ports(device_path: Path) -> list[dict]:
    """Regex-parse a DATA-ONLY device file's `["ports", [...]]` list into
    `[{"id": ..., "confidence": ...}, ...]`, without evaluating any OpenSCAD."""

    text = device_path.read_text(encoding="utf-8")
    text = re.sub(r"//[^\n]*", "", text)  # strip line comments so commented-out examples don't match

    idx = text.find('"ports"')
    if idx == -1:
        return []
    bracket_start = text.find("[", idx)
    if bracket_start == -1:
        return []
    bracket_end = _find_matching_bracket(text, bracket_start)
    ports_list_text = text[bracket_start + 1:bracket_end]

    ports = []
    for item in _extract_top_level_bracket_items(ports_list_text):
        id_m = _PORT_ID_RE.search(item)
        conf_m = _PORT_CONFIDENCE_RE.search(item)
        if id_m and conf_m:
            ports.append({"id": id_m.group(1), "confidence": conf_m.group(1)})
    return ports


def device_file_for_model(target: Target) -> Path | None:
    text = target.scad_path.read_text(encoding="utf-8")
    m = _DEVICE_INCLUDE_RE.search(text)
    if not m:
        return None
    return LIB_DIR / "mcc" / "devices" / f"{m.group(1)}.scad"


def cmd_confidence(args: argparse.Namespace) -> int:
    measured_rank = confidence_rank("measured")
    report = []
    any_below_measured = False

    for target in discover_models():
        entry = {"target": target.name, "device_file": None, "ports_below_measured": [], "error": None}
        device_path = device_file_for_model(target)
        if device_path is None:
            entry["error"] = f"no `include <mcc/devices/...>` found in {target.scad_path.relative_to(REPO_ROOT)}"
        elif not device_path.is_file():
            entry["error"] = f"device file not found: {device_path}"
        else:
            entry["device_file"] = str(device_path.relative_to(REPO_ROOT).as_posix())
            for port in parse_device_ports(device_path):
                if confidence_rank(port["confidence"]) < measured_rank:
                    entry["ports_below_measured"].append(port)

        if entry["ports_below_measured"]:
            any_below_measured = True
        report.append(entry)

    if args.json:
        print(json.dumps({"prerelease": any_below_measured, "models": report}, indent=2, sort_keys=True))
    else:
        print("confidence report (ports below \"measured\"):")
        for entry in report:
            if entry["error"]:
                print(f"  [WARN] {entry['target']}: {entry['error']}")
            elif not entry["ports_below_measured"]:
                print(f"  [OK]   {entry['target']}: all ports >= measured")
            else:
                names = ", ".join(f"{p['id']}={p['confidence']}" for p in entry["ports_below_measured"])
                print(f"  [WARN] {entry['target']}: {names}")
        print(f"\nprerelease={'true' if any_below_measured else 'false'}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"prerelease={'true' if any_below_measured else 'false'}\n")

    return 0  # always 0 — this is a report, not a gate (issue #10 softens the release gate)


# -----------------------------------------------------------------------------------------
# all
# -----------------------------------------------------------------------------------------

def cmd_all(args: argparse.Namespace) -> int:
    overall_ok = True

    print("=== smoke ===")
    overall_ok &= cmd_smoke(args) == 0

    print("\n=== render --all ===")
    render_ns = argparse.Namespace(
        all=True, targets=[], format="stl", part=None, defines=[], release=args.release,
    )
    overall_ok &= cmd_render(render_ns) == 0

    print("\n=== check --all ===")
    check_ns = argparse.Namespace(all=True, stl=[])
    overall_ok &= cmd_check(check_ns) == 0

    print("\n=== golden ===")
    golden_ns = argparse.Namespace(update=False, targets=[])
    overall_ok &= cmd_golden(golden_ns) == 0

    if args.with_step:
        print("\n=== step --all ===")
        step_ns = argparse.Namespace(all=True, targets=[], part=None)
        overall_ok &= cmd_step(step_ns) == 0

    return 0 if overall_ok else 1


# -----------------------------------------------------------------------------------------
# doctor
# -----------------------------------------------------------------------------------------

def cmd_doctor(_args: argparse.Namespace) -> int:
    print("magewell-converter-cases build doctor")
    print("=" * 40)

    try:
        exe = find_openscad()
        print(f"OpenSCAD:      {exe}")
        print(f"  version:     {openscad_version(exe)}")
    except SystemExit as exc:
        print(f"OpenSCAD:      NOT FOUND ({exc})")

    print(f"OPENSCADPATH:  {LIB_DIR}")

    sha = bosl2_sha()
    print(f"BOSL2 SHA:     {sha or 'NOT FOUND (submodule not checked out?)'}")

    print(f"git HEAD:      {git_head_sha() or 'unknown'}  (dirty={git_dirty()})")

    venv_python = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    print(f"venv python:   {venv_python if venv_python.exists() else 'not found (expected ' + str(venv_python) + ')'}")

    if trimesh is not None:
        print(f"trimesh:       {trimesh.__version__}")
    else:
        print("trimesh:       NOT AVAILABLE — pip install -r requirements.txt")

    step_backend, step_detail = mesh_to_step.backend_available()
    print(f"STEP backend:  {step_backend or 'NOT FOUND'}  ({step_detail})")

    coupons = discover_coupons()
    models = discover_models()
    print(f"\nDiscovered targets: {len(coupons)} coupon(s), {len(models)} model(s)")
    for t in coupons + models:
        print(f"  {t.kind:7s} {t.name:30s} parts={t.parts}  ({t.scad_path.relative_to(REPO_ROOT)})")
    if not coupons and not models:
        print("  (none yet — models/coupons/*.scad and models/*/case.scad are still being authored)")

    return 0


# -----------------------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="build.py", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="render coupons/models to STL/3MF via OpenSCAD")
    p_render.add_argument("targets", nargs="*", help='coupons/<name>, <model-slug>, or a .scad path')
    p_render.add_argument("--all", action="store_true", help="render every discovered target")
    p_render.add_argument("--format", choices=["stl", "3mf", "both"], default="stl")
    p_render.add_argument("--part", action="append", help="override part list (repeatable)")
    p_render.add_argument("-D", "--define", dest="defines", action="append", metavar="k=v",
                           help="extra -D override forwarded to OpenSCAD (repeatable)")
    p_render.add_argument("--release", action="store_true",
                           help="fail if OpenSCAD emits 'WARNING: unmeasured'")
    p_render.set_defaults(func=cmd_render)

    p_step = sub.add_parser("step", help="convert rendered STL(s) to B-rep STEP via scripts/mesh_to_step.py")
    p_step.add_argument("targets", nargs="*", help='coupons/<name>, <model-slug>, or a .scad path')
    p_step.add_argument("--all", action="store_true", help="convert every discovered target")
    p_step.add_argument("--part", action="append", help="override part list (repeatable)")
    p_step.set_defaults(func=cmd_step)

    p_smoke = sub.add_parser("smoke", help="Tier 2: run every tests/test_*.scad with -o *.csg")
    p_smoke.set_defaults(func=cmd_smoke)

    p_check = sub.add_parser("check", help="Tier 3: trimesh mesh checks on exported STL(s)")
    p_check.add_argument("stl", nargs="*", help="STL file(s) to check")
    p_check.add_argument("--all", action="store_true", help="check every exports/**/*.stl")
    p_check.set_defaults(func=cmd_check)

    p_golden = sub.add_parser("golden", help="Tier 3: compare/update geometry goldens")
    p_golden.add_argument("targets", nargs="*", help="limit to these targets (default: all discovered)")
    p_golden.add_argument("--update", action="store_true", help="(re)write goldens from current exports")
    p_golden.set_defaults(func=cmd_golden)

    p_confidence = sub.add_parser(
        "confidence",
        help="list every model's ports below 'measured' confidence; sets prerelease=true if any "
             "(report only — exit code 0 always)",
    )
    p_confidence.add_argument("--json", action="store_true", help="emit JSON instead of a human-readable table")
    p_confidence.set_defaults(func=cmd_confidence)

    p_all = sub.add_parser("all", help="smoke -> render --all -> check --all -> golden")
    p_all.add_argument("--release", action="store_true")
    p_all.add_argument("--with-step", action="store_true", help="also run step --all at the end")
    p_all.set_defaults(func=cmd_all)

    p_doctor = sub.add_parser("doctor", help="print resolved tool paths/versions and discovered targets")
    p_doctor.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
