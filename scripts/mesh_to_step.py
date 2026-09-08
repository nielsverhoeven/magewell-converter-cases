#!/usr/bin/env python3
"""Convert a watertight STL mesh to a B-rep STEP file (scripts/mesh_to_step.py).

OpenSCAD cannot write STEP directly, so this module turns an already-exported STL (produced by
`scripts/build.py render`) into a proper boundary-representation STEP: one planar face per
triangle, sewn into a shell/solid, then `ShapeUpgrade_UnifySameDomain` merges coplanar facets into
single planar faces (a flat wall becomes one face instead of hundreds of triangles; a cylindrical
bore stays faceted — there is no curve-fitting here, only planar merging).

Two backends, tried in this order:

1. **`cadquery-ocp`** (the `OCP` package — pip-installable OpenCASCADE bindings). Preferred: pure
   Python, no external process, fast. This is what CI uses (Python 3.12,
   `requirements-step.txt`).
2. **FreeCAD's `freecadcmd`**, shelled out to. Fallback for a local machine where no `cadquery-ocp`
   wheel is available for the venv's Python version. Located via the `MCC_FREECAD` environment
   variable or the default Windows install glob
   (`C:\\Program Files\\FreeCAD*\\bin\\freecadcmd.exe`).

If neither backend is available, `backend_available()` returns `(None, <reason>)` and callers
(`scripts/build.py step`) must decide whether that's fatal (always fatal in CI; a warning-and-skip
locally).

See `.claude/knowledge/architecture.md` §8 (export policy) — the STEP files this module writes are
release artefacts, never committed to the working tree (`exports/` is gitignored).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

# Sewing tolerance for stitching per-triangle faces back into a shell. STL vertices shared between
# adjacent triangles are bit-identical (or very nearly so) coming out of OpenSCAD/Manifold, so this
# only needs to be "small compared to any real feature," not fitted to float precision.
SEW_TOLERANCE_MM = 1e-4

WINDOWS_FREECAD_GLOB = r"C:\Program Files\FreeCAD*\bin\freecadcmd.exe"


@dataclass
class StepResult:
    ok: bool
    backend: str | None = None
    step_path: Path | None = None
    faces_before_unify: int | None = None
    faces_after_unify: int | None = None
    size_bytes: int | None = None
    validated: bool = False
    duration_s: float = 0.0
    error: str | None = None


# -----------------------------------------------------------------------------------------
# Backend detection
# -----------------------------------------------------------------------------------------

def _ocp_importable() -> tuple[bool, str]:
    try:
        import OCP  # noqa: F401
    except ImportError as exc:
        return False, f"import OCP failed: {exc}"
    return True, "OCP import OK"


def find_freecad() -> Path | None:
    """Locate freecadcmd via MCC_FREECAD, then the default Windows install glob, then PATH."""

    import glob as _glob

    env = os.environ.get("MCC_FREECAD")
    if env:
        p = Path(env)
        if p.is_file():
            return p
        which = shutil.which(env)
        if which:
            return Path(which)
        return None

    matches = sorted(_glob.glob(WINDOWS_FREECAD_GLOB), reverse=True)
    if matches:
        return Path(matches[0])

    which = shutil.which("freecadcmd")
    if which:
        return Path(which)
    return None


def backend_available() -> tuple[str | None, str]:
    """Returns (backend name or None, human-readable detail) — the pick `convert()` will make."""

    ok, detail = _ocp_importable()
    if ok:
        return "cadquery-ocp", detail

    freecad = find_freecad()
    if freecad is not None:
        return "freecad", f"freecadcmd at {freecad}"

    return None, (
        f"no STEP backend: {detail}; no freecadcmd found "
        f"(set MCC_FREECAD, or install FreeCAD: winget install --id FreeCAD.FreeCAD --exact)"
    )


# -----------------------------------------------------------------------------------------
# cadquery-ocp backend
# -----------------------------------------------------------------------------------------

def _convert_ocp(stl_path: Path, step_path: Path, product_name: str) -> StepResult:
    t0 = time.time()
    try:
        from OCP.BRepBuilderAPI import (
            BRepBuilderAPI_MakeFace,
            BRepBuilderAPI_MakePolygon,
            BRepBuilderAPI_MakeSolid,
            BRepBuilderAPI_Sewing,
        )
        from OCP.IFSelect import IFSelect_ReturnStatus
        from OCP.Interface import Interface_Static
        from OCP.RWStl import RWStl
        from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
        from OCP.STEPControl import STEPControl_StepModelType, STEPControl_Writer
        from OCP.TopAbs import TopAbs_ShapeEnum
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS
    except ImportError as exc:
        return StepResult(ok=False, backend="cadquery-ocp", error=f"OCP import failed: {exc}")

    def count_faces(shape) -> int:
        exp = TopExp_Explorer(shape, TopAbs_ShapeEnum.TopAbs_FACE)
        n = 0
        while exp.More():
            n += 1
            exp.Next()
        return n

    try:
        tri = RWStl.ReadFile_s(str(stl_path))
        if tri is None or tri.NbTriangles() == 0:
            return StepResult(ok=False, backend="cadquery-ocp", error="STL read produced 0 triangles")

        nodes = [tri.Node(i) for i in range(1, tri.NbNodes() + 1)]

        sew = BRepBuilderAPI_Sewing(SEW_TOLERANCE_MM)
        n_built = 0
        for i in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(i).Get()
            poly = BRepBuilderAPI_MakePolygon(nodes[a - 1], nodes[b - 1], nodes[c - 1], True)
            if not poly.IsDone():
                continue
            sew.Add(BRepBuilderAPI_MakeFace(poly.Wire()).Face())
            n_built += 1
        if n_built == 0:
            return StepResult(ok=False, backend="cadquery-ocp", error="no valid triangles produced a face")

        sew.Perform()
        sewed = sew.SewedShape()

        shell_exp = TopExp_Explorer(sewed, TopAbs_ShapeEnum.TopAbs_SHELL)
        shells = []
        while shell_exp.More():
            shells.append(TopoDS.Shell(shell_exp.Current()))
            shell_exp.Next()

        if len(shells) == 1:
            solid = BRepBuilderAPI_MakeSolid(shells[0]).Solid()
        elif sewed.ShapeType() == TopAbs_ShapeEnum.TopAbs_SHELL:
            solid = BRepBuilderAPI_MakeSolid(TopoDS.Shell(sewed)).Solid()
        else:
            # Not a single closed shell (mesh isn't watertight) — write what sewing produced rather
            # than failing outright; `build.py check` is the authority on watertightness, this is
            # STEP export, not a second watertight check.
            solid = sewed

        faces_before = count_faces(solid)

        unify = ShapeUpgrade_UnifySameDomain(solid, True, True, True)
        unify.Build()
        unified = unify.Shape()
        faces_after = count_faces(unified)

        step_path.parent.mkdir(parents=True, exist_ok=True)
        writer = STEPControl_Writer()
        Interface_Static.SetCVal_s("write.step.unit", "MM")
        Interface_Static.SetCVal_s("write.step.product.name", product_name)
        writer.Transfer(unified, STEPControl_StepModelType.STEPControl_AsIs)
        write_status = writer.Write(str(step_path))
        if write_status != IFSelect_ReturnStatus.IFSelect_RetDone:
            return StepResult(
                ok=False, backend="cadquery-ocp", error=f"STEPControl_Writer.Write returned {write_status}",
                duration_s=time.time() - t0,
            )
    except Exception as exc:  # noqa: BLE001 — surface any OCC failure as a conversion failure
        return StepResult(ok=False, backend="cadquery-ocp", error=f"conversion failed: {exc}", duration_s=time.time() - t0)

    if not step_path.is_file() or step_path.stat().st_size == 0:
        return StepResult(ok=False, backend="cadquery-ocp", error="STEP write produced no/empty file", duration_s=time.time() - t0)

    validated = _validate_step(step_path)
    return StepResult(
        ok=validated,
        backend="cadquery-ocp",
        step_path=step_path,
        faces_before_unify=faces_before,
        faces_after_unify=faces_after,
        size_bytes=step_path.stat().st_size,
        validated=validated,
        duration_s=time.time() - t0,
        error=None if validated else "post-write validation failed",
    )


# -----------------------------------------------------------------------------------------
# FreeCAD (freecadcmd) fallback backend
# -----------------------------------------------------------------------------------------

_FREECAD_SCRIPT = r"""
import sys
import Part
import Mesh

stl_path, step_path, product_name = sys.argv[1], sys.argv[2], sys.argv[3]

mesh = Mesh.Mesh(stl_path)
shape = Part.Shape()
shape.makeShapeFromMesh(mesh.Topology, 0.05)
faces_before = len(shape.Faces)

unified = shape.removeSplitter()
faces_after = len(unified.Faces)

solid = unified
if not solid.Solids:
    try:
        solid = Part.makeSolid(unified)
    except Exception:
        solid = unified  # not closed — export what we have rather than crash

solid.Label = product_name
Part.export([solid], step_path)
print("MCC_STEP_RESULT %d %d" % (faces_before, faces_after))
"""


def _convert_freecad(stl_path: Path, step_path: Path, product_name: str, freecad_exe: Path) -> StepResult:
    t0 = time.time()
    step_path.parent.mkdir(parents=True, exist_ok=True)

    script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(_FREECAD_SCRIPT)
            script_path = Path(f.name)

        proc = subprocess.run(
            [str(freecad_exe), str(script_path), str(stl_path), str(step_path), product_name],
            capture_output=True, text=True, check=False,
        )
    finally:
        if script_path is not None:
            script_path.unlink(missing_ok=True)

    faces_before = faces_after = None
    for line in proc.stdout.splitlines():
        if line.startswith("MCC_STEP_RESULT"):
            parts = line.split()
            try:
                faces_before, faces_after = int(parts[1]), int(parts[2])
            except (IndexError, ValueError):
                pass

    if proc.returncode != 0 or not step_path.is_file() or step_path.stat().st_size == 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-10:]
        return StepResult(
            ok=False, backend="freecad",
            error=f"freecadcmd failed (rc={proc.returncode}): {' | '.join(tail)}",
            duration_s=time.time() - t0,
        )

    validated = _validate_step(step_path)
    return StepResult(
        ok=validated,
        backend="freecad",
        step_path=step_path,
        faces_before_unify=faces_before,
        faces_after_unify=faces_after,
        size_bytes=step_path.stat().st_size,
        validated=validated,
        duration_s=time.time() - t0,
        error=None if validated else "post-write validation failed",
    )


# -----------------------------------------------------------------------------------------
# Validation (shared by both backends)
# -----------------------------------------------------------------------------------------

def _validate_step(step_path: Path) -> bool:
    """Re-read the STEP via OCP when available; otherwise just check the header magic bytes."""

    try:
        head = step_path.read_bytes()[:64]
    except OSError:
        return False
    if not head.startswith(b"ISO-10303-21"):
        return False

    try:
        from OCP.IFSelect import IFSelect_ReturnStatus
        from OCP.STEPControl import STEPControl_Reader
    except ImportError:
        return True  # OCP not available (e.g. FreeCAD-only machine) — header check is all we can do

    try:
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(step_path))
        if status != IFSelect_ReturnStatus.IFSelect_RetDone:
            return False
        return reader.TransferRoots() > 0
    except Exception:  # noqa: BLE001 — any re-read failure means validation failed, not a crash
        return False


# -----------------------------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------------------------

def convert(stl_path: Path, step_path: Path, product_name: str, backend: str | None = None) -> StepResult:
    """Convert one STL to STEP. `backend` overrides auto-detection (`backend_available()`)."""

    if backend is None:
        backend, detail = backend_available()
        if backend is None:
            return StepResult(ok=False, backend=None, error=detail)

    if backend == "cadquery-ocp":
        return _convert_ocp(stl_path, step_path, product_name)
    if backend == "freecad":
        freecad_exe = find_freecad()
        if freecad_exe is None:
            return StepResult(ok=False, backend="freecad", error="freecadcmd not found")
        return _convert_freecad(stl_path, step_path, product_name, freecad_exe)

    return StepResult(ok=False, backend=backend, error=f"unknown backend '{backend}'")


# -----------------------------------------------------------------------------------------
# CLI (ad-hoc single-file conversion, mainly for local testing)
# -----------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="mesh_to_step.py",
        description="Convert one STL to STEP. Normally invoked via `scripts/build.py step` — this "
                     "CLI is for ad-hoc/manual conversion or backend debugging.",
    )
    p.add_argument("stl", type=Path, help="input STL path")
    p.add_argument("step", type=Path, help="output STEP path")
    p.add_argument("--product", default=None, help="STEP product name (default: derived from the STL stem)")
    p.add_argument("--backend", choices=["cadquery-ocp", "freecad"], default=None, help="force a backend")
    args = p.parse_args(argv)

    if not args.stl.is_file():
        raise SystemExit(f"error: input STL not found: {args.stl}")

    product_name = args.product or args.stl.stem
    result = convert(args.stl, args.step, product_name, backend=args.backend)

    if result.error and not result.ok:
        print(f"error: {result.error}", file=sys.stderr)
    print(
        f"backend={result.backend} ok={result.ok} "
        f"faces={result.faces_before_unify}->{result.faces_after_unify} "
        f"size={result.size_bytes} validated={result.validated} "
        f"duration={result.duration_s:.2f}s"
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
