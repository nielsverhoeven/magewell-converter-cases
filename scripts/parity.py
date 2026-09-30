#!/usr/bin/env python3
"""Compare two model-frame parts and say where they differ (issue #80, phase P1).

Normally the candidate is a Fusion export and the oracle is the OpenSCAD part of the same name,
but any two watertight meshes work (STL, or STEP through OpenCascade). It needs neither Fusion nor
OpenSCAD: trimesh, numpy, scipy and manifold3d are enough (requirements.txt); a STEP input needs
cadquery-ocp (requirements-step.txt); the PNG needs matplotlib.

    python scripts/parity.py compare CANDIDATE ORACLE [--name N] [--out DIR] [--png]
                                     [--golden tests/golden/x.json] [--mask masks.json --mask-key K]
    python scripts/parity.py noise-floor MESH.stl MESH.step [MESH2.stl MESH2.step ...]
    python scripts/parity.py release-diff --exports exports --from-dir DIR | --tag TAG [--out DIR]

The pass criteria are the architect's (01-ARCH-BRIEF.md section E), all of them must hold:

  frame     every bounding-box corner coordinate of the two parts agrees within 0.02 mm;
  residual  the symmetric difference of the two solids (manifold3d booleans) is split into connected
            pieces; no piece may be both larger than 0.5 mm3 and thicker than 0.05 mm, where
            thickness = 2 x volume / area; the residual in total is at most 0.2 % of the part volume;
  golden    (with --golden) the committed golden passes unchanged: 0.1 mm, 0.5 %, 1 %.

Pieces that fail are merged into regions (bounding box, centroid, volume, touched bounding-box faces)
so a person or an agent sees WHERE the parts differ. Everything below the thresholds is summed up as
the noise floor (a polygon against a true circle produces thousands of such pieces). Label glyphs on
coupons are masked: pieces that lie inside a mask box are counted but never fail.

Also in the JSON: hints for the usual frame mistakes (units, swapped axes, shifted origin) and the
sampled maximum distance between the two surfaces in both directions.

Exit code: 0 pass, 1 differences found, 2 an input is unusable.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import manifold3d as m3d
    import trimesh
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"error: {exc}. Run: .venv\\Scripts\\python -m pip install -r requirements.txt")

SCHEMA = "parity-report/1"

FRAME_TOL_MM = 0.02        # every bounding-box corner coordinate (2 x MCC_EPS)
PIECE_MIN_VOLUME_MM3 = 0.5  # a residual piece must exceed this ...
PIECE_MIN_THICKNESS_MM = 0.05   # ... and this (2 V / A) to fail
TOTAL_RESIDUAL_REL = 0.002  # residual volume / part volume
# Golden tolerances, the same numbers as build.py GOLDEN_BBOX_TOL_MM / GOLDEN_VOLUME_TOL / GOLDEN_AREA_TOL
# (scripts/tests/test_parity.py fails when they drift apart; build.py imports this module, not the reverse).
GOLDEN_BBOX_MM = 0.1
GOLDEN_VOLUME_REL = 0.005
GOLDEN_AREA_REL = 0.01
CLUSTER_GAP_MM = 3.0       # failing pieces closer than this (per axis) form one region
MAX_LISTED = 40            # regions listed individually in the JSON
SAMPLES = 3000             # surface samples per direction for the distance metric
STEP_DEFLECTION_MM = 0.005
STEP_ANGULAR_RAD = 0.05
MASK_EPS_MM = 1e-3
DEGENERATE_AREA_MM2 = 1e-9  # triangles below this area are dropped before anything is compared
DEGENERATE_SHELL_MM3 = 0.01  # a shell that encloses less than this is a zero-volume void (the legacy csg-exact STEP files carry six per case base)
# Trees under exports/ that are not the OpenSCAD oracle (build.py has the same tuple: test_cad_import.py fails when they drift apart).
NON_ORACLE_TREES = ("import", "candidate", "replay", "builder-replay", "fusion", "parity")


class ParityError(Exception):
    """An input cannot be compared (not watertight, not a manifold, unreadable)."""


# -----------------------------------------------------------------------------------------
# Loading and scalar metrics
# -----------------------------------------------------------------------------------------

def _shapes(shape, kind, cast) -> list:
    from OCP.TopExp import TopExp_Explorer
    explorer, out = TopExp_Explorer(shape, kind), []
    while explorer.More():
        out.append(cast(explorer.Current()))
        explorer.Next()
    return out


def shape_volume(shape) -> float:
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def solid_shells(solid) -> tuple[list, list]:
    """(kept, void): the shells of one solid; void means an absolute volume below DEGENERATE_SHELL_MM3."""
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopoDS import TopoDS
    kept, void = [], []
    for shell in _shapes(solid, TopAbs_SHELL, TopoDS.Shell):
        (kept if abs(shape_volume(shell)) >= DEGENERATE_SHELL_MM3 else void).append(shell)
    return kept, void


def drop_void_shells(shape) -> tuple[object, int]:
    """The shape without its zero-volume shells and how many there were; the shape itself and 0 when it has none.
    The legacy csg-exact STEP files hold six such shells inside every case base (390.5 mm2 of faces, no cylinder): no
    area, shell count or mesh is taken from an oracle STEP before they are dropped. A clean STEP passes unchanged."""
    from OCP.BRep import BRep_Builder
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopoDS import TopoDS, TopoDS_Compound
    groups = [solid_shells(s) for s in _shapes(shape, TopAbs_SOLID, TopoDS.Solid)]
    dropped = sum(len(void) for _, void in groups)
    if not dropped:
        return shape, 0
    builder, compound = BRep_Builder(), TopoDS_Compound()
    builder.MakeCompound(compound)
    for kept, _ in groups:
        maker = BRepBuilderAPI_MakeSolid()
        for shell in kept:
            maker.Add(shell)
        builder.Add(compound, maker.Solid())
    return compound, dropped


def mesh_from_step(path: Path, deflection_mm: float = STEP_DEFLECTION_MM,
                   angular_rad: float = STEP_ANGULAR_RAD, drop_void: bool = True) -> "trimesh.Trimesh":
    """Tessellate a STEP file finely with OpenCascade: the exact B-rep sampled at `deflection_mm`, without its zero-volume
    shells (`mesh.metadata["void_shells_dropped"]` says how many)."""
    try:
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.STEPControl import STEPControl_Reader
    except ImportError as exc:
        raise ParityError(f"reading STEP needs cadquery-ocp (requirements-step.txt): {exc}")
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise ParityError(f"{path}: not a readable STEP file")
    reader.TransferRoots()
    shape, dropped = drop_void_shells(reader.OneShape()) if drop_void else (reader.OneShape(), 0)
    mesh = mesh_from_shape(shape, deflection_mm, angular_rad)
    mesh.metadata["void_shells_dropped"] = dropped
    return mesh


def mesh_from_shape(shape, deflection_mm: float = STEP_DEFLECTION_MM,
                    angular_rad: float = STEP_ANGULAR_RAD) -> "trimesh.Trimesh":
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    BRepMesh_IncrementalMesh(shape, deflection_mm, False, angular_rad, True)
    verts: list[np.ndarray] = []
    faces: list[np.ndarray] = []
    offset = 0
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            n = tri.NbNodes()
            pts = np.empty((n, 3))
            for i in range(1, n + 1):
                p = tri.Node(i).Transformed(trsf)
                pts[i - 1] = (p.X(), p.Y(), p.Z())
            reverse = face.Orientation() == TopAbs_REVERSED
            tris = np.empty((tri.NbTriangles(), 3), dtype=np.int64)
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                tris[i - 1] = (a - 1, c - 1, b - 1) if reverse else (a - 1, b - 1, c - 1)
            verts.append(pts)
            faces.append(tris + offset)
            offset += n
        exp.Next()
    if not verts:
        raise ParityError("the shape has no faces to tessellate")
    mesh = trimesh.Trimesh(np.vstack(verts), np.vstack(faces), process=False)
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    return mesh


def load_mesh(path: Path | str) -> "trimesh.Trimesh":
    p = Path(path)
    if not p.is_file():
        raise ParityError(f"{p}: file not found")
    if p.suffix.lower() in (".step", ".stp"):
        return mesh_from_step(p)
    try:
        return trimesh.load(str(p), force="mesh")
    except Exception as exc:  # noqa: BLE001
        raise ParityError(f"{p}: cannot load ({exc})")


def step_bbox(path: Path | str) -> dict:
    """Exact bounding box of a STEP file's B-rep (a true circle reaches its full radius; a mesh only to its sagitta)."""
    try:
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import BRepBndLib
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.STEPControl import STEPControl_Reader
    except ImportError as exc:
        raise ParityError(f"reading STEP needs cadquery-ocp (requirements-step.txt): {exc}")
    reader = STEPControl_Reader()
    if not Path(path).is_file() or reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise ParityError(f"{path}: not a readable STEP file")
    reader.TransferRoots()
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(reader.OneShape(), box, False, False)
    lo, hi = box.CornerMin(), box.CornerMax()
    return _box_metrics([lo.X(), lo.Y(), lo.Z()], [hi.X(), hi.Y(), hi.Z()])


def _box_metrics(lo, hi) -> dict:
    lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
    return {"bbox_min": lo.tolist(), "bbox_max": hi.tolist(), "size": (hi - lo).tolist(), "center": ((lo + hi) / 2).tolist()}


def frame_of(path: Path | str) -> dict:
    """Bounding box used for the frame test: exact for STEP, the mesh's for anything else."""
    if Path(path).suffix.lower() in (".step", ".stp"):
        return step_bbox(path)
    mesh = load_mesh(path)
    return _box_metrics(mesh.bounds[0], mesh.bounds[1])


def clean_mesh(mesh: "trimesh.Trimesh") -> tuple["trimesh.Trimesh", int]:
    """Drop zero-area triangles, but only when that turns an open mesh into a closed one. A staged oracle mesh (a groove root
    edge) carries two of them: they make an edge belong to three faces, trimesh then calls the sound solid open, and dropping
    them restores a watertight single body. A closed mesh is left alone: an exporter's STL (float32 vertices) holds zero-area
    triangles that fill T-junctions, and dropping those would open it."""
    if mesh.is_watertight:
        return mesh, 0
    degenerate = mesh.area_faces < DEGENERATE_AREA_MM2
    if not degenerate.any():
        return mesh, 0
    cleaned = mesh.copy()
    cleaned.update_faces(~degenerate)
    cleaned.remove_unreferenced_vertices()
    if not cleaned.is_watertight:
        return mesh, 0
    return cleaned, int(degenerate.sum())


def validate_mesh(mesh: "trimesh.Trimesh", label: str) -> None:
    if not mesh.is_watertight:
        raise ParityError(f"{label}: mesh is not watertight; run `build.py check` on it first")
    if not mesh.is_winding_consistent or mesh.volume <= 0:
        raise ParityError(f"{label}: inconsistent or inverted winding (volume {mesh.volume:.1f})")


def metrics_of(mesh: "trimesh.Trimesh") -> dict:
    lo, hi = (np.asarray(x, dtype=float) for x in mesh.bounds)
    return {"bbox_min": lo.tolist(), "bbox_max": hi.tolist(), "size": (hi - lo).tolist(),
            "center": ((lo + hi) / 2).tolist(), "volume_mm3": float(mesh.volume),
            "area_mm2": float(mesh.area), "faces": int(len(mesh.faces))}


def metrics_of_golden(golden: dict) -> dict:
    """The same shape from a tests/golden/*.json file (bbox min/max/size, volume_mm3, area_mm2, facets)."""
    bb = golden["bbox"]
    lo, hi = np.asarray(bb["min"], dtype=float), np.asarray(bb["max"], dtype=float)
    return {"bbox_min": lo.tolist(), "bbox_max": hi.tolist(), "size": (hi - lo).tolist(),
            "center": ((lo + hi) / 2).tolist(), "volume_mm3": float(golden["volume_mm3"]),
            "area_mm2": float(golden["area_mm2"]), "faces": golden.get("facets")}


def _check(name: str, cand: float, oracle: float, delta: float, tol: float, unit: str) -> dict:
    return {"name": name, "candidate": round(cand, 4), "oracle": round(oracle, 4),
            "delta": round(delta, 5), "tolerance": tol, "unit": unit, "ok": bool(abs(delta) <= tol)}


def frame_checks(c: dict, o: dict, tol: float = FRAME_TOL_MM) -> list[dict]:
    """The six bounding-box corner coordinates, each within `tol` of the oracle's."""
    out = []
    for key, tag in (("bbox_min", "min"), ("bbox_max", "max")):
        for i, ax in enumerate("xyz"):
            out.append(_check(f"corner_{tag}_{ax}", c[key][i], o[key][i], c[key][i] - o[key][i], tol, "mm"))
    return out


def golden_checks(c: dict, o: dict) -> list[dict]:
    """tests/golden/README.md tolerances: bbox size 0.1 mm per axis, volume 0.5 %, area 1 %."""
    out = [_check(f"golden_size_{ax}", c["size"][i], o["size"][i], c["size"][i] - o["size"][i], GOLDEN_BBOX_MM, "mm")
           for i, ax in enumerate("xyz")]
    for key, tol in (("volume_mm3", GOLDEN_VOLUME_REL), ("area_mm2", GOLDEN_AREA_REL)):
        rel = (c[key] - o[key]) / o[key] if o[key] else float("inf")
        out.append(_check(f"golden_{key}", c[key], o[key], rel, tol, "relative"))
    return out


_SCALE_HINTS = ((0.1, "10 times smaller: exported in cm instead of mm?"),
                (10.0, "10 times larger: exported in mm but read as cm?"),
                (1 / 25.4, "25.4 times smaller: inches read as mm?"),
                (25.4, "25.4 times larger: mm read as inches?"),
                (0.001, "1000 times smaller: exported in metres?"),
                (1000.0, "1000 times larger: exported in micrometres?"))


def frame_hints(c: dict, o: dict, tol: float = FRAME_TOL_MM) -> list[str]:
    """Plain-language guesses when the two parts disagree in one of the usual ways."""
    hints: list[str] = []
    cs, os_ = np.asarray(c["size"]), np.asarray(o["size"])
    if np.all(os_ > 0):
        ratio = cs / os_
        for k, text in _SCALE_HINTS:
            if np.all(np.abs(ratio / k - 1.0) < 0.02):
                hints.append(f"candidate is {text}")
    if not np.allclose(cs, os_, atol=10 * tol):
        for perm in itertools.permutations(range(3)):
            if perm != (0, 1, 2) and np.allclose(cs[list(perm)], os_, atol=10 * tol):
                hints.append(f"candidate axes look permuted: its sizes (x, y, z) = {np.round(cs, 2).tolist()} equal the "
                             f"oracle's {np.round(os_, 2).tolist()} in the order {perm}; a Y-up export instead of Z-up?")
                break
    else:
        off = np.asarray(c["center"]) - np.asarray(o["center"])
        if np.abs(off).max() > tol:
            hints.append(f"same size but shifted by {np.round(off, 3).tolist()} mm: the model origin differs")
    return hints


# -----------------------------------------------------------------------------------------
# Residual pieces
# -----------------------------------------------------------------------------------------

@dataclass
class Pieces:
    """All connected pieces of one residual solid, as arrays (a fine tessellation gives thousands)."""
    side: str                  # "extra" (only in the candidate) | "missing" (only in the oracle)
    vertices: np.ndarray       # (n, 3)
    faces: np.ndarray          # (m, 3)
    face_label: np.ndarray     # (m,) piece index per face
    volume: np.ndarray         # (k,)
    area: np.ndarray
    bbox_min: np.ndarray       # (k, 3)
    bbox_max: np.ndarray
    centroid: np.ndarray
    fails: np.ndarray          # (k,) bool: larger than PIECE_MIN_VOLUME_MM3 and thicker than PIECE_MIN_THICKNESS_MM
    masked: np.ndarray         # (k,) bool: inside a mask box

    @property
    def thickness(self) -> np.ndarray:
        return 2.0 * self.volume / np.maximum(self.area, 1e-12)

    def __len__(self) -> int:
        return len(self.volume)


def to_manifold(mesh: "trimesh.Trimesh") -> "m3d.Manifold":
    mf = m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
                               tri_verts=np.asarray(mesh.faces, dtype=np.uint32)))
    if mf.status() != m3d.Error.NoError:
        raise ParityError(f"mesh is not a valid manifold solid ({mf.status()})")
    return mf


def split_pieces(solid: "m3d.Manifold", side: str, masks: list[tuple[np.ndarray, np.ndarray]],
                 min_volume: float = PIECE_MIN_VOLUME_MM3, min_thickness: float = PIECE_MIN_THICKNESS_MM) -> Pieces:
    """Connected pieces of a residual solid with volume, area, bounding box and centroid, in one vectorised pass."""
    empty = Pieces(side, np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64), np.zeros(0, dtype=np.int64), *(np.zeros(0),) * 2,
                   np.zeros((0, 3)), np.zeros((0, 3)), np.zeros((0, 3)), np.zeros(0, dtype=bool), np.zeros(0, dtype=bool))
    if solid.is_empty():
        return empty
    mm = solid.to_mesh()
    v = np.asarray(mm.vert_properties, dtype=np.float64)[:, :3]
    f = np.asarray(mm.tri_verts, dtype=np.int64)
    n = len(v)
    rows = np.concatenate([f[:, 0], f[:, 1], f[:, 2]])
    cols = np.concatenate([f[:, 1], f[:, 2], f[:, 0]])
    _, vlabel = connected_components(coo_matrix((np.ones(len(rows), dtype=bool), (rows, cols)), shape=(n, n)), directed=False)
    flabel_raw = vlabel[f[:, 0]]
    t = v[f]
    vol6 = np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2]))
    tri_area = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
    order = np.argsort(flabel_raw, kind="stable")
    ls = flabel_raw[order]
    starts = np.flatnonzero(np.r_[True, ls[1:] != ls[:-1]])
    vol = np.add.reduceat(vol6[order], starts) / 6.0
    area = np.add.reduceat(tri_area[order], starts)
    bmin = np.minimum.reduceat(t.min(axis=1)[order], starts, axis=0)
    bmax = np.maximum.reduceat(t.max(axis=1)[order], starts, axis=0)
    cen = np.add.reduceat(((t.sum(axis=1) / 4.0) * vol6[:, None])[order], starts, axis=0) / np.where(
        np.abs(np.add.reduceat(vol6[order], starts)) < 1e-12, 1.0, np.add.reduceat(vol6[order], starts))[:, None]
    keep = vol > 0                      # a negative piece is the inner shell of a cavity: ignored
    remap = np.full(len(starts), -1, dtype=np.int64)
    remap[keep] = np.arange(int(keep.sum()))
    label_of_raw = np.full(int(flabel_raw.max()) + 1, -1, dtype=np.int64)
    label_of_raw[ls[starts]] = remap
    face_label = label_of_raw[flabel_raw]
    vol, area, bmin, bmax, cen = vol[keep], area[keep], bmin[keep], bmax[keep], cen[keep]
    thickness = 2.0 * vol / np.maximum(area, 1e-12)
    masked = np.zeros(len(vol), dtype=bool)
    for lo, hi in masks:
        masked |= np.all(bmin >= lo - MASK_EPS_MM, axis=1) & np.all(bmax <= hi + MASK_EPS_MM, axis=1)
    fails = (vol > min_volume) & (thickness > min_thickness) & ~masked
    return Pieces(side, v, f, face_label, vol, area, bmin, bmax, cen, fails, masked)


def cluster_regions(bmin: np.ndarray, bmax: np.ndarray, gap_mm: float) -> list[list[int]]:
    n = len(bmin)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        gap = np.maximum(bmin[i + 1:] - bmax[i], bmin[i] - bmax[i + 1:])
        for j in (np.where(np.all(gap <= gap_mm, axis=1))[0] + i + 1):
            parent[find(int(j))] = find(i)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


_FACE_NAMES = ("-X", "+X", "-Y", "+Y", "-Z", "+Z")


def _touches(lo: np.ndarray, hi: np.ndarray, o_lo: np.ndarray, o_hi: np.ndarray, eps: float = 0.5) -> list[str]:
    out = []
    for ax in range(3):
        if lo[ax] <= o_lo[ax] + eps:
            out.append(_FACE_NAMES[2 * ax])
        if hi[ax] >= o_hi[ax] - eps:
            out.append(_FACE_NAMES[2 * ax + 1])
    return out


def _vec(a) -> list[float]:
    return [round(float(x), 3) for x in a]


def build_regions(parts: list[Pieces], oracle_bounds: np.ndarray, gap_mm: float) -> list[dict]:
    regions = []
    for p in parts:
        idx = np.flatnonzero(p.fails)
        if not len(idx):
            continue
        for grp in cluster_regions(p.bbox_min[idx], p.bbox_max[idx], gap_mm):
            sel = idx[grp]
            vol = float(p.volume[sel].sum())
            lo, hi = p.bbox_min[sel].min(axis=0), p.bbox_max[sel].max(axis=0)
            cen = (p.centroid[sel] * p.volume[sel][:, None]).sum(axis=0) / vol
            regions.append({
                "side": p.side, "volume_mm3": round(vol, 3), "pieces": int(len(sel)),
                "bbox_min": _vec(lo), "bbox_max": _vec(hi), "centroid": _vec(cen),
                "max_thickness_mm": round(float(p.thickness[sel].max()), 4),
                "touches_bbox_faces": _touches(lo, hi, oracle_bounds[0], oracle_bounds[1]),
                "piece_indices": [int(i) for i in sel],
            })
    regions.sort(key=lambda r: -r["volume_mm3"])
    for i, r in enumerate(regions, 1):
        r["id"] = i
    return regions


def sub_threshold_summary(p: Pieces) -> dict:
    sub = ~p.fails & ~p.masked
    vol, th = p.volume[sub], p.thickness[sub]
    small_thick = sub & (p.volume <= PIECE_MIN_VOLUME_MM3) & (p.thickness > PIECE_MIN_THICKNESS_MM)
    big_thin = sub & (p.volume > PIECE_MIN_VOLUME_MM3) & (p.thickness <= PIECE_MIN_THICKNESS_MM)
    return {"pieces": int(sub.sum()), "volume_mm3": round(float(vol.sum()), 4),
            "max_thickness_mm": round(float(th.max()) if len(th) else 0.0, 5),
            "max_piece_volume_mm3": round(float(vol.max()) if len(vol) else 0.0, 4),
            "small_but_thick": int(small_thick.sum()), "large_but_thin": int(big_thin.sum()),
            "masked_pieces": int(p.masked.sum()), "masked_volume_mm3": round(float(p.volume[p.masked].sum()), 4)}


# -----------------------------------------------------------------------------------------
# Surface distance
# -----------------------------------------------------------------------------------------

def distance_to(mesh: "trimesh.Trimesh", points: np.ndarray, chunk: int = 20000) -> np.ndarray:
    """Exact distance of each point to the mesh surface (trimesh/rtree: about 5000 points per second)."""
    out = np.empty(len(points))
    for i in range(0, len(points), chunk):
        out[i:i + chunk] = trimesh.proximity.closest_point(mesh, points[i:i + chunk])[1]
    return out


def _worst_points(points: np.ndarray, dist: np.ndarray, n: int = 3, sep: float = 2.0) -> list[dict]:
    out: list[dict] = []
    for i in np.argsort(-dist):
        if all(np.linalg.norm(points[i] - np.asarray(w["point"])) > sep for w in out):
            out.append({"point": _vec(points[i]), "distance_mm": round(float(dist[i]), 4)})
        if len(out) == n:
            break
    return out


def surface_distance(cand: "trimesh.Trimesh", oracle: "trimesh.Trimesh", parts: list[Pieces],
                     samples: int = SAMPLES, seed: int = 1) -> dict:
    """Both directions: area-weighted surface samples plus every vertex of a failing residual piece (the
    largest distance sits on the residual's boundary, where the two surfaces part)."""
    out = {}
    for label, src, dst, side in (("candidate_to_oracle", cand, oracle, "extra"), ("oracle_to_candidate", oracle, cand, "missing")):
        pts = [trimesh.sample.sample_surface(src, samples, seed=seed)[0]] if samples > 0 else []
        for p in parts:
            if p.side == side and p.fails.any():
                on_failing_piece = (p.face_label >= 0) & p.fails[np.clip(p.face_label, 0, None)]
                pts.append(p.vertices[np.unique(p.faces[on_failing_piece])])
        if not pts:
            out[label] = {"points": 0}
            continue
        allp = np.vstack(pts)
        d = distance_to(dst, allp)
        out[label] = {"points": int(len(allp)), "max_mm": round(float(d.max()), 4),
                      "p99_mm": round(float(np.percentile(d, 99)), 4), "mean_mm": round(float(d.mean()), 5),
                      "worst": _worst_points(allp, d)}
    return out


# -----------------------------------------------------------------------------------------
# The comparison
# -----------------------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_meshes(cand: "trimesh.Trimesh", oracle: "trimesh.Trimesh", *, name: str = "", samples: int = SAMPLES,
                   masks: list[tuple[np.ndarray, np.ndarray]] | None = None, golden: dict | None = None,
                   frame_c: dict | None = None, frame_o: dict | None = None, mode: str = "full",
                   gap_mm: float = CLUSTER_GAP_MM, seed: int = 1) -> tuple[dict, list[Pieces]]:
    """The full report (see the module docstring) and the residual pieces (for the PNG).

    frame_c / frame_o: bounding boxes for the corner test when the meshes are not the right source (exact
    boxes of the two STEP files: a polygon that circumscribes a circle overshoots it by R / cos(pi / n) - R,
    0.024 mm for R = 20 and n = 64, more than the 0.02 mm the corner test allows).
    mode "pieces": only the piece criterion (no corner test, no total limit), for a mesh against its own STEP."""
    t0 = time.time()
    cand, dropped_c = clean_mesh(cand)
    oracle, dropped_o = clean_mesh(oracle)
    validate_mesh(cand, "candidate")
    validate_mesh(oracle, "oracle")
    mc, mo = metrics_of(cand), metrics_of(oracle)
    mc["dropped_degenerate_faces"], mo["dropped_degenerate_faces"] = dropped_c, dropped_o
    mc["void_shells_dropped"] = int(cand.metadata.get("void_shells_dropped", 0))
    mo["void_shells_dropped"] = int(oracle.metadata.get("void_shells_dropped", 0))
    fc, fo = {**mc, **(frame_c or {})}, {**mo, **(frame_o or {})}
    checks = frame_checks(fc, fo) if mode == "full" else []
    hints = frame_hints(fc, fo) if mode == "full" else []
    if golden is not None:
        checks += golden_checks(mc, metrics_of_golden(golden))

    a, b = to_manifold(cand), to_manifold(oracle)
    masks = masks or []
    extra = split_pieces(a - b, "extra", masks)
    missing = split_pieces(b - a, "missing", masks)
    t_res = time.time() - t0
    parts = [extra, missing]
    v_extra, v_missing = float(extra.volume.sum()), float(missing.volume.sum())
    v_masked = float(extra.volume[extra.masked].sum() + missing.volume[missing.masked].sum())
    counted = v_extra + v_missing - v_masked
    res_rel = counted / mo["volume_mm3"]
    regions = build_regions(parts, np.asarray(oracle.bounds), gap_mm)
    dist = surface_distance(cand, oracle, parts, samples=samples, seed=seed)

    failures = [f"{c['name']}: {c['candidate']} vs {c['oracle']} (delta {c['delta']}, tolerance {c['tolerance']} {c['unit']})"
                for c in checks if not c["ok"]]
    if mode == "full" and res_rel > TOTAL_RESIDUAL_REL:
        failures.append(f"residual volume {counted:.1f} mm3 = {res_rel * 100:.3f} % of the part "
                        f"(limit {TOTAL_RESIDUAL_REL * 100:.1f} %)")
    if regions:
        failures.append(f"{len(regions)} residual region(s) with a piece larger than {PIECE_MIN_VOLUME_MM3} mm3 and "
                        f"thicker than {PIECE_MIN_THICKNESS_MM} mm, see residual.regions")
    sub = {"extra": sub_threshold_summary(extra), "missing": sub_threshold_summary(missing)}
    warnings = []
    for s in ("extra", "missing"):
        if sub[s]["small_but_thick"]:
            warnings.append(f"{sub[s]['small_but_thick']} {s} piece(s) of at most {PIECE_MIN_VOLUME_MM3} mm3 but thicker "
                            f"than {PIECE_MIN_THICKNESS_MM} mm (below the failing volume, so they pass)")
    report = {
        "schema": SCHEMA, "name": name,
        "thresholds": {"frame_mm": FRAME_TOL_MM, "piece_min_volume_mm3": PIECE_MIN_VOLUME_MM3,
                       "piece_min_thickness_mm": PIECE_MIN_THICKNESS_MM, "total_residual_rel": TOTAL_RESIDUAL_REL,
                       "cluster_gap_mm": gap_mm},
        "candidate": mc, "oracle": mo, "checks": checks, "frame_hints": hints,
        "residual": {
            "extra_volume_mm3": round(v_extra, 3), "missing_volume_mm3": round(v_missing, 3),
            "counted_volume_mm3": round(counted, 3), "counted_rel": round(res_rel, 6),
            "sub_threshold": sub, "regions_total": len(regions),
            "regions": [{k: v for k, v in r.items() if k != "piece_indices"} for r in regions[:MAX_LISTED]],
        },
        "surface_distance": dist,
        "verdict": {"status": "fail" if failures else "pass", "failures": failures, "warnings": warnings},
        "timing_s": {"residual": round(t_res, 2), "total": round(time.time() - t0, 2)},
    }
    report["_regions_full"] = regions          # stripped before writing; the PNG needs the piece indices
    return report, parts


TEXT_RE = re.compile(r"^[ \t]*text\(text = .*?\);[ \t]*\r?\n", re.M)
MASK_PAD_XY_MM, MASK_PAD_Z_MM, MASK_GAP_MM, MASK_MIN_VOLUME_MM3 = 1.0, 0.3, 2.0, 0.5


def derive_masks(exports: Path) -> dict:
    """Label mask boxes of the coupons, from the oracle only: render each coupon's .csg without its text() statements
    (written to a temporary directory: no .scad or .csg file enters git) and take the residual against the oracle STL.
    Needs OpenSCAD (build.find_openscad). Key: "<target>:<part>" as in cad/fixtures/step-cylinders.json."""
    import build      # lazily: build.py imports this module
    exe = build.find_openscad()
    out: dict[str, list[dict]] = {}
    for csg in sorted(Path(exports).glob("coupons/*/*.csg")):
        text = csg.read_text(encoding="utf-8")
        nodes = len(TEXT_RE.findall(text))
        if not nodes:
            continue
        part = csg.stem
        with tempfile.TemporaryDirectory(prefix="mcc_mask_") as tmp:
            reduced, stl = Path(tmp) / "nolabel.csg", Path(tmp) / "nolabel.stl"
            reduced.write_text(TEXT_RE.sub("", text), encoding="utf-8")
            ok, _ = build.run_openscad(exe, reduced, {}, [stl], None)
            if not ok or not stl.is_file():
                raise ParityError(f"{csg}: OpenSCAD could not render the coupon without its text")
            plain = trimesh.load(str(stl), force="mesh")
        oracle = load_mesh(csg.with_name(f"{part}.model.stl"))
        a, b = to_manifold(plain), to_manifold(oracle)
        boxes = []
        for solid, side in ((a - b, "engraved"), (b - a, "embossed")):
            pieces = split_pieces(solid, side, [])
            for grp in (cluster_regions(pieces.bbox_min, pieces.bbox_max, MASK_GAP_MM) if len(pieces) else []):
                if pieces.volume[grp].sum() < MASK_MIN_VOLUME_MM3:
                    continue
                lo, hi = pieces.bbox_min[grp].min(axis=0), pieces.bbox_max[grp].max(axis=0)
                boxes.append({"min": [round(float(lo[0] - MASK_PAD_XY_MM), 2), round(float(lo[1] - MASK_PAD_XY_MM), 2),
                                      round(float(lo[2] - MASK_PAD_Z_MM), 2)],
                              "max": [round(float(hi[0] + MASK_PAD_XY_MM), 2), round(float(hi[1] + MASK_PAD_XY_MM), 2),
                                      round(float(hi[2] + MASK_PAD_Z_MM), 2)]})
        if not 1 <= len(boxes) <= 4 * nodes:       # a label of two words can give two boxes, never none
            raise ParityError(f"{csg}: {len(boxes)} mask boxes for {nodes} text nodes")
        out[f"coupons/{csg.parent.name}:{part}"] = sorted(boxes, key=lambda bx: (bx["min"][0], bx["min"][1], bx["min"][2]))
    return out


def cmd_derive_masks(args: argparse.Namespace) -> int:
    try:
        fresh = derive_masks(Path(args.exports))
    except ParityError as exc:
        print(f"error: {exc}")
        return 2
    out = Path(args.out)
    if args.check:
        committed = json.loads(out.read_text(encoding="utf-8"))
        problems = []
        for key, boxes in fresh.items():
            old = committed.get(key)
            if old is None or len(old) != len(boxes) or any(
                    max(abs(x - y) for x, y in zip(n["min"] + n["max"], o["min"] + o["max"])) > 0.01 for n, o in zip(boxes, old)):
                problems.append(f"{key}: the committed mask boxes differ from the oracle's")
        print("\n".join(problems) if problems else f"{out} is fresh for {len(fresh)} coupon(s)")
        return 1 if problems else 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out}: " + ", ".join(f"{k.split(':')[0]} {len(v)}" for k, v in fresh.items()))
    return 0


def load_masks(path: Path | None, key: str | None) -> list[tuple[np.ndarray, np.ndarray]]:
    if not path or not key:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(np.asarray(b["min"], dtype=float), np.asarray(b["max"], dtype=float)) for b in data.get(key, [])]


def compare_files(candidate: Path, oracle: Path, *, name: str = "", golden_path: Path | None = None,
                  mask_path: Path | None = None, mask_key: str | None = None, candidate_frame: Path | None = None,
                  oracle_frame: Path | None = None, **kw):
    """candidate / oracle: STL or STEP (a STEP is tessellated finely). candidate_frame / oracle_frame: the file whose
    bounding box feeds the corner test (normally the STEP of each side, exact)."""
    cand, ora = load_mesh(candidate), load_mesh(oracle)
    golden = json.loads(Path(golden_path).read_text(encoding="utf-8")) if golden_path else None
    report, parts = compare_meshes(cand, ora, name=name, golden=golden, masks=load_masks(mask_path, mask_key),
                                   frame_c=frame_of(candidate_frame) if candidate_frame else None,
                                   frame_o=frame_of(oracle_frame) if oracle_frame else None, **kw)
    report["candidate"]["file"] = {"path": str(candidate), "sha256": sha256_of(Path(candidate))}
    report["oracle"]["file"] = {"path": str(oracle), "sha256": sha256_of(Path(oracle))}
    return report, parts, cand, ora


# -----------------------------------------------------------------------------------------
# PNG
# -----------------------------------------------------------------------------------------

_COLOURS = {"extra": "#d62728", "missing": "#1f77b4"}


def _piece_triangles(p: Pieces, idx: np.ndarray, ij) -> np.ndarray:
    sel = np.isin(p.face_label, idx)
    return p.vertices[p.faces[sel]][:, :, list(ij)]


def render_png(report: dict, cand: "trimesh.Trimesh", oracle: "trimesh.Trimesh", parts: list[Pieces],
               out_png: Path, zoom_regions: int = 3) -> Path | None:
    """Row 1: top, front and side projection of the oracle (grey) with every failing piece on top (red = extra
    in the candidate, blue = missing from it). Row 2: one face-on zoom per region (largest first), looking along
    the region's thinnest axis, with the oracle (black) and candidate (green) cross-section through its centre."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import PolyCollection
    except ImportError:
        return None
    by_side = {p.side: p for p in parts}
    regions = report.get("_regions_full", [])
    failing = {side: np.flatnonzero(p.fails) for side, p in by_side.items()}
    views = (("top, looking down (X right, Y up)", (0, 1)), ("front (X right, Z up)", (0, 2)), ("side (Y right, Z up)", (1, 2)))
    fig, axes = plt.subplots(2, 3, figsize=(16, 10.5))
    for ax, (title, ij) in zip(axes[0], views):
        ax.add_collection(PolyCollection(oracle.vertices[oracle.faces][:, :, list(ij)], facecolor="#dcdcdc",
                                         edgecolor="none", rasterized=True))
        for side, p in by_side.items():
            if len(failing[side]):
                ax.add_collection(PolyCollection(_piece_triangles(p, failing[side], ij), facecolor=_COLOURS[side],
                                                 edgecolor=_COLOURS[side], linewidth=0.4, alpha=0.85))
        lo, hi = oracle.bounds[0][list(ij)], oracle.bounds[1][list(ij)]
        pad = 0.04 * (hi - lo).max()
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[1] - pad, hi[1] + pad)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=10)
    fig.suptitle(f"{report.get('name', '')}  {report['verdict']['status'].upper()}   grey: oracle   red: extra in candidate   "
                 f"blue: missing from candidate   (pieces below the thresholds are not drawn)", fontsize=11)
    for ax in axes[1]:
        ax.axis("off")
    for ax, reg in zip(axes[1], regions[:zoom_regions]):
        ax.axis("on")
        lo, hi = np.array(reg["bbox_min"]), np.array(reg["bbox_max"])
        k = int(np.argmin(hi - lo))
        ij = [i for i in range(3) if i != k]
        normal = np.zeros(3)
        normal[k] = 1.0
        for mesh, colour, style in ((oracle, "black", "-"), (cand, "#2ca02c", "--")):
            try:
                sec = mesh.section(plane_origin=np.array(reg["centroid"]), plane_normal=normal)
            except Exception:  # noqa: BLE001
                sec = None
            if sec is not None:
                for line in sec.discrete:
                    ax.plot(line[:, ij[0]], line[:, ij[1]], color=colour, linestyle=style, linewidth=0.9)
        p = by_side[reg["side"]]
        ax.add_collection(PolyCollection(_piece_triangles(p, np.array(reg["piece_indices"]), ij), facecolor=_COLOURS[reg["side"]],
                                         edgecolor="none", alpha=0.45))
        ax.set_xlim(lo[ij[0]] - 6.0, hi[ij[0]] + 6.0)
        ax.set_ylim(lo[ij[1]] - 6.0, hi[ij[1]] + 6.0)
        ax.set_aspect("equal")
        ax.set_title(f"region {reg['id']} ({reg['side']}): {reg['volume_mm3']} mm3, {reg['pieces']} pieces, looking along "
                     f"{'xyz'[k]}\nblack = oracle section, green = candidate section", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_png), dpi=110)
    plt.close(fig)
    return out_png


# -----------------------------------------------------------------------------------------
# Text summary, geometry diff and CLI
# -----------------------------------------------------------------------------------------

def summary_text(report: dict) -> str:
    v = report["verdict"]
    lines = [f"parity {report.get('name') or '(unnamed)'}: {v['status'].upper()}"]
    worst = max((abs(c["delta"]) for c in report["checks"] if c["name"].startswith("corner")), default=0.0)
    lines.append(f"  frame: largest corner difference {worst:.4f} mm (limit {FRAME_TOL_MM})")
    for c in report["checks"]:
        if not c["ok"] and c["name"].startswith("golden"):
            lines.append(f"  FAIL {c['name']} {c['candidate']} vs {c['oracle']}")
    for h in report.get("frame_hints", []):
        lines.append(f"  hint: {h}")
    res = report["residual"]
    sub = res["sub_threshold"]
    n = sub["extra"]["pieces"] + sub["missing"]["pieces"]
    lines.append(f"  residual {res['counted_volume_mm3']} mm3 = {res['counted_rel'] * 100:.4f} % of the part (extra "
                 f"{res['extra_volume_mm3']}, missing {res['missing_volume_mm3']}); below the thresholds: {n} pieces, "
                 f"{round(sub['extra']['volume_mm3'] + sub['missing']['volume_mm3'], 3)} mm3, thickest "
                 f"{max(sub['extra']['max_thickness_mm'], sub['missing']['max_thickness_mm'])} mm")
    for r in res["regions"][:8]:
        what = "candidate has extra material" if r["side"] == "extra" else "candidate lacks material"
        lines.append(f"  region {r['id']} {what}: {r['volume_mm3']} mm3 in {r['pieces']} piece(s), x {r['bbox_min'][0]}..{r['bbox_max'][0]} "
                     f"y {r['bbox_min'][1]}..{r['bbox_max'][1]} z {r['bbox_min'][2]}..{r['bbox_max'][2]}, thickness "
                     f"{r['max_thickness_mm']} mm" + (f", on {','.join(r['touches_bbox_faces'])} face" if r["touches_bbox_faces"] else ""))
    d = report["surface_distance"]
    lines.append(f"  surface distance max: candidate->oracle {d.get('candidate_to_oracle', {}).get('max_mm')} mm, "
                 f"oracle->candidate {d.get('oracle_to_candidate', {}).get('max_mm')} mm")
    lines += [f"  - {f}" for f in v["failures"]] + [f"  (warning) {w}" for w in v["warnings"]]
    return "\n".join(lines)


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "parity"


def write_report(report: dict, out: Path, stem: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    clean = {k: v for k, v in report.items() if not k.startswith("_")}
    text = json.dumps(clean, indent=2)
    text = re.sub(r"\[\s+([-\d.,\s e]+?)\s+\]", lambda m: "[" + re.sub(r"\s+", " ", m.group(1)) + "]", text)   # short lists on one line
    path = out / f"{stem}.json"
    path.write_text(text + "\n", encoding="utf-8")
    return path


def cmd_compare(args: argparse.Namespace) -> int:
    name = args.name or f"{Path(args.candidate).stem} vs {Path(args.oracle).stem}"
    try:
        report, parts, cand, ora = compare_files(Path(args.candidate), Path(args.oracle), name=name, samples=args.samples,
                                                 golden_path=Path(args.golden) if args.golden else None,
                                                 mask_path=Path(args.mask) if args.mask else None, mask_key=args.mask_key,
                                                 candidate_frame=Path(args.candidate_frame) if args.candidate_frame else None,
                                                 oracle_frame=Path(args.oracle_frame) if args.oracle_frame else None,
                                                 mode=args.mode)
    except ParityError as exc:
        print(f"error: {exc}")
        return 2
    print(summary_text(report))
    if args.out:
        out, stem = Path(args.out), f"parity-{_slug(name)}"
        if args.png:
            png = render_png(report, cand, ora, parts, out / f"{stem}.png")
            report["png"] = png.name if png else None
        print(f"  report: {write_report(report, out, stem)}")
    return 0 if report["verdict"]["status"] == "pass" else 1


def cmd_noise_floor(args: argparse.Namespace) -> int:
    """How much residual does tessellation alone produce: a mesh against the fine tessellation of its own STEP.
    Prints one line per pair and the ceilings' headroom."""
    if len(args.files) % 2:
        print("error: give pairs MESH STEP")
        return 2
    worst_corner = worst_mesh_corner = worst_rel = worst_t = 0.0
    n_fail = 0
    for mesh_p, step_p in zip(args.files[::2], args.files[1::2]):
        try:
            mesh, step_mesh = load_mesh(mesh_p), load_mesh(step_p)
            exact = step_bbox(step_p)
            # candidate = the exact B-rep, oracle = the mesh; the corner test uses the exact box on both sides
            report, _ = compare_meshes(step_mesh, mesh, name=Path(mesh_p).stem, samples=0, frame_c=exact, frame_o=exact)
        except ParityError as exc:
            print(f"error: {mesh_p}: {exc}")
            return 2
        res, sub = report["residual"], report["residual"]["sub_threshold"]
        mesh_corner = float(max(np.abs(np.asarray(mesh.bounds[0]) - exact["bbox_min"]).max(),
                                np.abs(np.asarray(mesh.bounds[1]) - exact["bbox_max"]).max()))
        t = max(sub["extra"]["max_thickness_mm"], sub["missing"]["max_thickness_mm"])
        worst_mesh_corner, worst_rel, worst_t = max(worst_mesh_corner, mesh_corner), max(worst_rel, res["counted_rel"]), max(worst_t, t)
        n_fail += report["verdict"]["status"] != "pass"
        print(f"{mesh_p}: {report['verdict']['status']}  mesh corners off the exact box by {mesh_corner:.5f} mm  residual "
              f"{res['counted_volume_mm3']} mm3 ({res['counted_rel'] * 100:.4f} %)  pieces {sub['extra']['pieces'] + sub['missing']['pieces']}  "
              f"thickest {t} mm  largest piece {max(sub['extra']['max_piece_volume_mm3'], sub['missing']['max_piece_volume_mm3'])} mm3")
    print(f"worst: mesh corners {worst_mesh_corner:.5f} mm (corner limit {FRAME_TOL_MM}), residual {worst_rel * 100:.4f} % "
          f"(limit {TOTAL_RESIDUAL_REL * 100}), thickness {worst_t} mm (limit {PIECE_MIN_THICKNESS_MM}); failing parts {n_fail}")
    return 1 if n_fail else 0


def cmd_release_diff(args: argparse.Namespace) -> int:
    """Geometry diff report against a release: every candidate part against the loose STEP asset of the same part
    (dist/step/<slug>-<part>.step in a release, model frame). An empty report means the geometry did not change."""
    exports = Path(args.exports)
    units = []
    for stl in sorted(exports.glob("**/*.model.stl")):
        rel = stl.relative_to(exports).as_posix()[: -len(".model.stl")]          # e.g. pro-convert-hdmi-tx/base
        if rel.split("/")[0] in NON_ORACLE_TREES:
            continue                                                               # only the oracle tree (or the tree given)
        target, _, part = rel.rpartition("/")
        slug = target.replace("/", "-")                                            # package_release._step_asset_name
        units.append((rel, stl, f"{slug}.step" if part == Path(target).name else f"{slug}-{part}.step"))
    if args.from_dir:
        src = Path(args.from_dir)
    else:
        src = Path(tempfile.mkdtemp(prefix="mcc_release_"))
        tag = args.tag
        if tag == "latest":      # every release of this repository is a pre-release, so `gh release view` (the API's "latest") finds none
            found = subprocess.run(["gh", "release", "list", "--exclude-drafts", "--limit", "1", "--json", "tagName", "--jq", ".[0].tagName"],
                                   capture_output=True, text=True, check=False)
            tag = found.stdout.strip()
            if not tag:
                print("error: no published release found")
                return 2
        cmd = ["gh", "release", "download", tag, "--dir", str(src), "--clobber"]
        for _, _, name in units:
            cmd += ["--pattern", name]                                             # only the assets of the parts that exist
        if not units or subprocess.run(cmd, check=False).returncode != 0:
            print(f"error: could not download the STEP assets of release {tag}")
            return 2
    rows, changed = [], 0
    for rel, stl, name in units:
        asset = src / name
        if not asset.is_file():
            rows.append((rel, "no release asset", []))
            continue
        cand_step = stl.with_name(stl.name[: -len(".model.stl")] + ".step")      # exact boxes on both sides when the STEP is there
        report, parts = compare_meshes(load_mesh(stl), load_mesh(asset), name=rel, samples=0,
                                       frame_c=step_bbox(cand_step) if cand_step.is_file() else None, frame_o=step_bbox(asset))
        regions = report["residual"]["regions"]
        changed += bool(regions) or report["verdict"]["status"] != "pass"
        rows.append((rel, report["verdict"]["status"], regions))
        if args.out and (regions or report["verdict"]["status"] != "pass"):
            write_report(report, Path(args.out), f"diff-{_slug(rel)}")
    for rel, status, regions in rows:
        print(f"  {rel:<52} {'unchanged' if status == 'pass' else status}")
        for r in regions[:5]:
            print(f"      {r['side']:<8} {r['volume_mm3']:>9} mm3  bbox {r['bbox_min']} .. {r['bbox_max']}")
    print(f"{changed} of {len(rows)} part(s) changed against the release")
    return 1 if changed and args.fail_on_change else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="parity.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compare", help="compare a candidate part with an oracle part")
    c.add_argument("candidate")
    c.add_argument("oracle")
    c.add_argument("--name", default="")
    c.add_argument("--out", help="directory for parity-<name>.json (and .png)")
    c.add_argument("--png", action="store_true", help="also write the PNG (needs matplotlib)")
    c.add_argument("--samples", type=int, default=SAMPLES, help="surface samples per direction (0 = failing residual vertices only)")
    c.add_argument("--golden", help="also run the golden tolerances against this tests/golden/*.json")
    c.add_argument("--mask", help="JSON file of label mask boxes")
    c.add_argument("--mask-key", help="key of this part in the mask file, e.g. coupons/tg-ladder:tg-ladder")
    c.add_argument("--candidate-frame", help="file whose bounding box feeds the corner test (the candidate STEP: exact)")
    c.add_argument("--oracle-frame", help="file whose bounding box feeds the corner test (the oracle STEP: exact)")
    c.add_argument("--mode", choices=("full", "pieces"), default="full",
                   help="pieces = only the piece criterion, for a mesh against the tessellation of its own STEP")
    c.set_defaults(func=cmd_compare)
    m = sub.add_parser("derive-masks", help="label mask boxes of the coupons from the oracle (needs OpenSCAD)")
    m.add_argument("--exports", default="exports")
    m.add_argument("--out", default="cad/fixtures/parity-masks.json")
    m.add_argument("--check", action="store_true", help="compare with the committed file for the coupons that are rendered")
    m.set_defaults(func=cmd_derive_masks)
    n = sub.add_parser("noise-floor", help="tessellation noise: each MESH against the fine tessellation of its own STEP")
    n.add_argument("files", nargs="+", metavar="MESH STEP")
    n.set_defaults(func=cmd_noise_floor)
    r = sub.add_parser("release-diff", help="geometry diff of the exports against the last release")
    r.add_argument("--exports", default="exports")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--tag", help="release tag whose loose STEP assets are the baseline (downloads with gh)")
    g.add_argument("--from-dir", help="directory that already holds the baseline STEP files")
    r.add_argument("--out")
    r.add_argument("--fail-on-change", action="store_true")
    r.set_defaults(func=cmd_release_diff)
    return p


COMMANDS = ("compare", "noise-floor", "release-diff", "derive-masks")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "compare")                # `parity.py CANDIDATE ORACLE` is `parity.py compare CANDIDATE ORACLE`
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
