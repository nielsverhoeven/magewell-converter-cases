#!/usr/bin/env python3
"""OpenSCAD CSG tree -> exact B-rep STEP (true cylinders and circles, not facets).

Why (user report 2026-09-28): the STEP files used to be converted from the rendered *mesh*
(scripts/mesh_to_step.py), so every hole and rounding arrived in CAD as dozens of flat facets — a
hole could not be selected as a cylinder, measured, or filleted. OpenSCAD can also export its
evaluated CSG tree (`-o part.csg`): the primitives (`cylinder`, `circle`, `cube`, `polygon`, ...),
the booleans and the transforms, before tessellation. This module rebuilds that tree with
OpenCascade (cadquery-ocp), so round things become real cylinders / cones / circles / arcs:

  cylinder, sphere, circle  -> analytic when they have >= FN_ANALYTIC_MIN fragments (a $fn=6 nut
                               trap stays a hexagon — that polygon is the design intent)
  cube, square, polygon     -> exact planar geometry; runs of polygon vertices that lie on one
                               circle (BOSL2 teardrops, rounded corners, ...) are refitted as arcs
  linear_extrude            -> prism (scale != 1 -> loft)
  rotate_extrude            -> revolution
  offset(r= | delta=)       -> exact 2-D offset (arcs for r)
  hull (2-D)                -> exact: arcs of the hulled circles joined by tangent segments
  hull (3-D)                -> the children fused with the convex hull of their points (faces of
                               the children that lie on the hull keep their exact surfaces)
  multmatrix                -> exact rigid/uniform transform; shear/non-uniform -> B-spline
  polyhedron                -> planar faces (threads, BOSL2 VNFs — faceted by nature)
  minkowski, projection, text, import, surface -> unsupported (a ConversionError names them)

Usage:
    python scripts/csg_to_step.py part.csg part.step [--product NAME] [--mesh part.model.stl]

`--mesh` compares the B-rep volume against the rendered mesh and fails when they differ by more
than VOLUME_TOL (a converter bug, not a design change). build.py `step`/`ci` drive this.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

FN_ANALYTIC_MIN = 16     # fragments at/above which a circle/cylinder/sphere becomes analytic
ARC_FIT_MIN_PTS = 5      # a polygon run needs this many vertices on one circle to become an arc
ARC_FIT_TOL = 2e-3       # mm, max vertex distance from the fitted circle
VOLUME_TOL = 0.01        # 1 % — B-rep vs rendered mesh
EPS = 1e-9


class ConversionError(RuntimeError):
    pass


# -----------------------------------------------------------------------------------------
# CSG parser (OpenSCAD's .csg export is a small, regular subset of the language)
# -----------------------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"""
    (?P<ws>\s+|//[^\n]*)
  | (?P<num>[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)
  | (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<id>[$A-Za-z_][A-Za-z0-9_]*)
  | (?P<sym>[()\[\]{},;=%*#!])
""", re.VERBOSE)


@dataclass
class Node:
    name: str
    args: dict
    children: list = field(default_factory=list)
    modifier: str = ""
    src: str = ""  # the node's own CSG source text (valid OpenSCAD), for OpenSCAD-evaluated leaves


def _tokens(text: str):
    pos, n = 0, len(text)
    out = []
    while pos < n:
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise ConversionError(f"CSG parse error at offset {pos}: {text[pos:pos + 40]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append((kind, m.group(kind), m.start(), m.end()))
    return out


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.t = _tokens(text)
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None, 0, 0)

    def take(self, value=None):
        tok = self.peek()
        if value is not None and tok[1] != value:
            raise ConversionError(f"CSG parse error: expected {value!r}, got {tok[1]!r}")
        self.i += 1
        return tok

    def value(self):
        kind, v = self.peek()[:2]
        if kind == "num":
            self.i += 1
            return float(v)
        if kind == "str":
            self.i += 1
            return v[1:-1]
        if kind == "id":
            self.i += 1
            return {"true": True, "false": False, "undef": None, "inf": math.inf, "nan": math.nan}.get(v, v)
        if v == "[":
            self.i += 1
            items = []
            while self.peek()[1] != "]":
                items.append(self.value())
                if self.peek()[1] == ",":
                    self.i += 1
            self.take("]")
            return items
        raise ConversionError(f"CSG parse error: unexpected {v!r} in a value")

    def node(self) -> Node | None:
        start = self.peek()[2]
        mod = ""
        while self.peek()[1] in ("%", "*", "#", "!"):
            mod += self.take()[1]
        kind, name = self.take()[:2]
        if kind != "id":
            raise ConversionError(f"CSG parse error: expected a module name, got {name!r}")
        self.take("(")
        args: dict = {}
        pos = 0
        while self.peek()[1] != ")":
            if self.peek()[0] == "id" and self.t[self.i + 1][1] == "=":
                key = self.take()[1]
                self.take("=")
                args[key] = self.value()
            else:
                args[pos] = self.value()
                pos += 1
            if self.peek()[1] == ",":
                self.i += 1
        self.take(")")
        children = []
        if self.peek()[1] == "{":
            self.i += 1
            while self.peek()[1] != "}":
                c = self.node()
                if c is not None:
                    children.append(c)
            self.take("}")
        else:
            self.take(";")
        if "%" in mod or "*" in mod:   # background / disabled subtrees are not part of the model
            return None
        return Node(name, args, children, mod, self.text[start:self.t[self.i - 1][3]])

    def program(self) -> list[Node]:
        nodes = []
        while self.i < len(self.t):
            n = self.node()
            if n is not None:
                nodes.append(n)
        return nodes


def parse_csg(text: str) -> list[Node]:
    return _Parser(text).program()


# -----------------------------------------------------------------------------------------
# OpenCascade builders
# -----------------------------------------------------------------------------------------

from OCP.BRep import BRep_Tool  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse  # noqa: E402
from OCP.BRepBuilderAPI import (  # noqa: E402
    BRepBuilderAPI_GTransform, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Sewing, BRepBuilderAPI_Transform,
)
from OCP.BRepCheck import BRepCheck_Analyzer  # noqa: E402
from OCP.BRepGProp import BRepGProp  # noqa: E402
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffset, BRepOffsetAPI_ThruSections  # noqa: E402
from OCP.BRepPrimAPI import (  # noqa: E402
    BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCone, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeRevol, BRepPrimAPI_MakeSphere,
)
from OCP.GC import GC_MakeArcOfCircle  # noqa: E402
from OCP.GeomAbs import GeomAbs_Arc, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Intersection, GeomAbs_Plane  # noqa: E402
from OCP.GProp import GProp_GProps  # noqa: E402
from OCP.gp import gp_Ax1, gp_Ax2, gp_Circ, gp_Dir, gp_GTrsf, gp_Mat, gp_Pnt, gp_Trsf, gp_Vec, gp_XYZ  # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Surface  # noqa: E402
from OCP.Interface import Interface_Static  # noqa: E402
from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid  # noqa: E402
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain  # noqa: E402
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer  # noqa: E402
from OCP.TopAbs import TopAbs_FACE, TopAbs_SHELL, TopAbs_SOLID, TopAbs_VERTEX  # noqa: E402
from OCP.TopExp import TopExp_Explorer  # noqa: E402
from OCP.TopoDS import TopoDS, TopoDS_Compound, TopoDS_Shape  # noqa: E402
from OCP.BRep import BRep_Builder  # noqa: E402
try:  # OCP >= 8 moved the NCollection lists to OCP.collections
    from OCP.TopTools import TopTools_ListOfShape  # noqa: E402
except ImportError:  # pragma: no cover - depends on the OCP build
    from OCP.collections import List_TopoDS_Shape as TopTools_ListOfShape  # noqa: E402


@dataclass
class Geo:
    shape: TopoDS_Shape
    dim: int  # 2 = planar face(s) in Z=0, 3 = solid(s)


def _fragments(r: float, a: dict) -> int:
    fn = float(a.get("$fn", 0) or 0)
    if fn > 0:
        return max(int(fn), 3)
    fa = float(a.get("$fa", 12) or 12)
    fs = float(a.get("$fs", 2) or 2)
    if r < 1e-12:
        return 3
    return int(math.ceil(max(min(360.0 / fa, r * 2 * math.pi / fs), 5)))


def _pnt(p) -> gp_Pnt:
    return gp_Pnt(float(p[0]), float(p[1]), float(p[2]) if len(p) > 2 else 0.0)


def _bool(op, a: TopoDS_Shape, tools: list[TopoDS_Shape]) -> TopoDS_Shape:
    if not tools:
        return a
    args, tl = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(a)
    for t in tools:
        tl.Append(t)
    b = op()
    b.SetArguments(args)
    b.SetTools(tl)
    b.SetFuzzyValue(1e-6)
    b.SetRunParallel(True)
    b.Build()
    if not b.IsDone():
        raise ConversionError(f"{op.__name__} failed")
    return b.Shape()


def _fuse(shapes: list[TopoDS_Shape]) -> TopoDS_Shape | None:
    shapes = [s for s in shapes if s is not None and not s.IsNull()]
    if not shapes:
        return None
    # Pairwise, not one Fuse with many tools: with several (mutually overlapping) tools OCCT's
    # fuse silently dropped material — the NDI-to-HDMI base came out at 71 of 294 cm3 before its
    # cuts. Pairwise is exact and, on these trees, no slower in practice.
    acc = shapes[0]
    for s in shapes[1:]:
        acc = _bool(BRepAlgoAPI_Fuse, acc, [s])
    return acc


# ---- 2-D ----------------------------------------------------------------------------------

def _circle_through(p1, p2, p3):
    ax, ay = p1
    bx, by = p2
    cx, cy = p3
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)


def _loop_edges(pts: list) -> list:
    """Edges for a closed 2-D loop, refitting runs of >= ARC_FIT_MIN_PTS vertices that lie on one
    circle (and turn consistently) as a single exact arc."""
    n = len(pts)
    P = [(float(p[0]), float(p[1])) for p in pts]
    # drop duplicate consecutive points
    P = [p for i, p in enumerate(P) if math.hypot(p[0] - P[i - 1][0], p[1] - P[i - 1][1]) > 1e-9]
    n = len(P)
    if n < 3:
        raise ConversionError("degenerate polygon")
    on_arc = [None] * n  # circle params for runs
    edges = []
    i = 0
    # find arc runs greedily starting from a vertex that is not mid-arc: rotate start so we do not
    # begin inside a run — try every start until a run boundary, cheap for our sizes
    def run_from(s):
        c = _circle_through(P[s % n], P[(s + 1) % n], P[(s + 2) % n])
        if c is None or c[2] > 1e4:
            return 1, None
        k = 3
        while k < n:
            q = P[(s + k) % n]
            if abs(math.hypot(q[0] - c[0], q[1] - c[1]) - c[2]) > ARC_FIT_TOL:
                break
            k += 1
        return (k - 1, c) if k >= ARC_FIT_MIN_PTS else (1, None)

    # choose a start that is a corner (not on a fitted run through its neighbours)
    start = 0
    for s in range(n):
        c = _circle_through(P[(s - 1) % n], P[s], P[(s + 1) % n])
        if c is None or c[2] > 1e4:
            start = s
            break
    s = start
    covered = 0
    while covered < n:
        steps, c = run_from(s)
        steps = min(steps, n - covered)
        a, b = P[s % n], P[(s + steps) % n]
        if c is not None and steps >= ARC_FIT_MIN_PTS - 1:
            mid = P[(s + steps // 2) % n]
            arc = GC_MakeArcOfCircle(gp_Pnt(a[0], a[1], 0), gp_Pnt(mid[0], mid[1], 0), gp_Pnt(b[0], b[1], 0))
            edges.append(BRepBuilderAPI_MakeEdge(arc.Value()).Edge())
        else:
            for j in range(steps):
                u, v = P[(s + j) % n], P[(s + j + 1) % n]
                edges.append(BRepBuilderAPI_MakeEdge(gp_Pnt(u[0], u[1], 0), gp_Pnt(v[0], v[1], 0)).Edge())
        s += steps
        covered += steps
    return edges


def _wire(edges):
    w = BRepBuilderAPI_MakeWire()
    for e in edges:
        w.Add(e)
    if not w.IsDone():
        raise ConversionError("could not build a wire")
    return w.Wire()


def _area_signed(pts):
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))


def _polygon_face(points, paths) -> TopoDS_Shape:
    pts = [(float(p[0]), float(p[1])) for p in points]
    loops = [[pts[int(i)] for i in path] for path in paths] if paths else [pts]
    faces = []
    for loop in loops:
        f = BRepBuilderAPI_MakeFace(_wire(_loop_edges(loop)), True)
        faces.append((abs(_area_signed(loop)), f.Face()))
    return _even_odd([(a, f, l) for (a, f), l in zip(faces, loops)])


def _point_in_loop(pt, loop) -> bool:
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(loop, loop[1:] + loop[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _even_odd(items) -> TopoDS_Shape:
    """items = [(area, face, loop)]. Even-odd fill like OpenSCAD: a loop nested inside an even number
    of other loops is material, inside an odd number a hole — so several separate outlines (text,
    multi-path polygons) and islands inside holes all come out right. Largest first, so every loop
    is added/removed after the loops that contain it."""
    items = sorted(items, key=lambda t: -t[0])
    res = None
    for i, (_, face, loop) in enumerate(items):
        probe = loop[0]
        depth = sum(1 for j, (_, _, other) in enumerate(items) if j != i and items[j][0] > items[i][0]
                    and _point_in_loop(probe, other))
        if depth % 2 == 0:
            res = face if res is None else _bool(BRepAlgoAPI_Fuse, res, [face])
        elif res is not None:
            res = _bool(BRepAlgoAPI_Cut, res, [face])
    return res


def _openscad_2d_loops(src: str) -> list[list[tuple[float, float]]]:
    """Evaluate one 2-D CSG leaf (e.g. a text() call) with OpenSCAD itself and return its outline
    loops from the SVG export. Used for text(): glyph outlines are font curves OpenSCAD already
    flattens, and an engraved label gains nothing from being exact."""
    import subprocess
    import tempfile
    import build  # sibling module: the pinned OpenSCAD
    with tempfile.TemporaryDirectory(prefix="mcc_csg2d_") as tmp:
        scad, svg = Path(tmp) / "leaf.scad", Path(tmp) / "leaf.svg"
        scad.write_text(src.rstrip().rstrip(";") + ";\n", encoding="utf-8")
        proc = subprocess.run([str(build.find_openscad()), "-o", str(svg), str(scad)],
                              capture_output=True, text=True, check=False)
        if proc.returncode != 0 or not svg.is_file():
            raise ConversionError(f"OpenSCAD could not evaluate 2-D leaf: {src[:60]}")
        d = " ".join(re.findall(r'd="([^"]*)"', svg.read_text(encoding="utf-8")))
    loops, cur = [], []
    for cmd, body in re.findall(r"([MLz])([^MLz]*)", d):
        if cmd == "M" and cur:
            loops.append(cur); cur = []
        if cmd in "ML":
            for xs, ys in re.findall(r"(-?[\d.eE+-]+),(-?[\d.eE+-]+)", body):
                cur.append((float(xs), -float(ys)))  # OpenSCAD writes SVG with y flipped
        elif cmd == "z" and cur:
            loops.append(cur); cur = []
    if cur:
        loops.append(cur)
    return [l for l in loops if len(l) >= 3]


def _loops_face(loops) -> TopoDS_Shape:
    items = []
    for loop in loops:
        edges = [BRepBuilderAPI_MakeEdge(gp_Pnt(p[0], p[1], 0), gp_Pnt(q[0], q[1], 0)).Edge()
                 for p, q in zip(loop, loop[1:] + loop[:1]) if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 1e-12]
        items.append((abs(_area_signed(loop)), BRepBuilderAPI_MakeFace(_wire(edges), True).Face(), loop))
    return _even_odd(items)


def _circle_face(r: float, a: dict) -> TopoDS_Shape:
    fr = _fragments(r, a)
    if fr >= FN_ANALYTIC_MIN:
        e = BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), r)).Edge()
        return BRepBuilderAPI_MakeFace(_wire([e]), True).Face()
    pts = [(r * math.cos(2 * math.pi * i / fr), r * math.sin(2 * math.pi * i / fr)) for i in range(fr)]
    return _polygon_face(pts, None)


def _unify(shape: TopoDS_Shape) -> TopoDS_Shape:
    """Merge coplanar neighbouring faces (and collinear edges) left behind by booleans."""
    up = ShapeUpgrade_UnifySameDomain(shape, True, True, False)
    up.Build()
    return up.Shape()


def _offset_face(shape: TopoDS_Shape, amount: float, round_: bool) -> TopoDS_Shape:
    out = []
    # One face per connected region: a 2-D union comes back from the boolean as several adjacent
    # coplanar faces, and offsetting those one by one and fusing the overlapping results hung OCCT
    # (rail-latch coupon).
    shape = _unify(shape)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face(exp.Current())
        mk = BRepOffsetAPI_MakeOffset(face, GeomAbs_Arc if round_ else GeomAbs_Intersection)
        mk.Perform(amount)
        if not mk.IsDone():
            raise ConversionError("2-D offset failed")
        res = mk.Shape()
        # result = wire(s): rebuild faces (outer + holes) via even-odd like polygons
        wires = []
        wexp = TopExp_Explorer(res, TopAbs_FACE)
        from OCP.TopAbs import TopAbs_WIRE
        wexp = TopExp_Explorer(res, TopAbs_WIRE)
        while wexp.More():
            wires.append(TopoDS.Wire(wexp.Current()))
            wexp.Next()
        fs = []
        for w in wires:
            f = BRepBuilderAPI_MakeFace(w, True).Face()
            fs.append((abs(_face_area(f)), f))
        fs.sort(key=lambda t: -t[0])
        r = fs[0][1]
        for _, f in fs[1:]:
            r = _bool(BRepAlgoAPI_Cut, r, [f])
        out.append(r)
        exp.Next()
    return _fuse(out)


def _face_area(shape) -> float:
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(shape, props)
    return props.Mass()


# ---- sampling for hulls ----------------------------------------------------------------------

def _sample_points(shape: TopoDS_Shape, dim: int) -> np.ndarray:
    """Points on the boundary of `shape`, dense on curved edges/faces (for hull construction)."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopLoc import TopLoc_Location
    BRepMesh_IncrementalMesh(shape, 0.002, False, 0.02, True)
    pts = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            for i in range(1, tri.NbNodes() + 1):
                p = tri.Node(i).Transformed(trsf)
                pts.append((p.X(), p.Y(), p.Z()))
        exp.Next()
    a = np.array(pts)
    return a[:, :2] if dim == 2 else a


def _hull2d(children: list[Geo]) -> TopoDS_Shape:
    """Exact 2-D hull: the children fused with the convex polygon of their dense boundary samples.
    Where the hull follows a circle, the child's exact arc is the boundary (the sampled chords lie
    inside it); elsewhere the hull edges are straight, as they should be."""
    from scipy.spatial import ConvexHull
    pts = np.vstack([_sample_points(c.shape, 2) for c in children])
    h = ConvexHull(pts)
    loop = [tuple(pts[i]) for i in h.vertices]
    poly = BRepBuilderAPI_MakeFace(_wire([
        BRepBuilderAPI_MakeEdge(gp_Pnt(p[0], p[1], 0), gp_Pnt(q[0], q[1], 0)).Edge()
        for p, q in zip(loop, loop[1:] + loop[:1])]), True).Face()
    return _fuse([poly] + [c.shape for c in children])


def _hull3d(children: list[Geo]) -> TopoDS_Shape:
    from scipy.spatial import ConvexHull
    pts = np.vstack([_sample_points(c.shape, 3) for c in children])
    h = ConvexHull(pts)
    solid = _polyhedron([tuple(p) for p in pts], [list(s) for s in h.simplices], outward_ccw=True)
    return _fuse([solid] + [c.shape for c in children])


def _polyhedron(points, faces, outward_ccw=False) -> TopoDS_Shape:
    sew = BRepBuilderAPI_Sewing(1e-6)
    P = [_pnt(p) for p in points]
    for f in faces:
        idx = [int(i) for i in f]
        if not outward_ccw:
            idx = idx[::-1]  # OpenSCAD faces are clockwise seen from outside
        poly = BRepBuilderAPI_MakePolygon()
        for i in idx:
            poly.Add(P[i])
        poly.Close()
        if not poly.IsDone():
            continue
        mf = BRepBuilderAPI_MakeFace(poly.Wire(), True)
        if mf.IsDone():
            sew.Add(mf.Face())
    sew.Perform()
    sewed = sew.SewedShape()
    exp = TopExp_Explorer(sewed, TopAbs_SHELL)
    if not exp.More():
        raise ConversionError("polyhedron did not sew into a closed shell")
    solids = []
    while exp.More():  # one solid per shell: a transformed child may hold several disjoint bodies
        fix = ShapeFix_Solid(BRepBuilderAPI_MakeSolid(TopoDS.Shell(exp.Current())).Solid())
        fix.Perform()
        solids.append(fix.Solid())
        exp.Next()
    if len(solids) == 1:
        return solids[0]
    comp = TopoDS_Compound()
    b = BRep_Builder()
    b.MakeCompound(comp)
    for so in solids:
        b.Add(comp, so)
    return comp


# ---- transforms ------------------------------------------------------------------------------

def _is_polyhedral(shape: TopoDS_Shape) -> bool:
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_Line
    from OCP.TopAbs import TopAbs_EDGE
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        if BRepAdaptor_Surface(TopoDS.Face(exp.Current())).GetType() != GeomAbs_Plane:
            return False
        exp.Next()
    exp = TopExp_Explorer(shape, TopAbs_EDGE)
    while exp.More():
        if BRepAdaptor_Curve(TopoDS.Edge(exp.Current())).GetType() != GeomAbs_Line:
            return False
        exp.Next()
    return True


def _affine_polyhedral(shape: TopoDS_Shape, R: np.ndarray, t: np.ndarray) -> TopoDS_Shape:
    """Exact affine image of a flat-faced, straight-edged solid: triangulate it (exact for planar
    polygons), map the vertices, re-sew. Coplanar triangles merge back at the final
    UnifySameDomain."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location
    BRepMesh_IncrementalMesh(shape, 1.0, False, 0.5, True)
    flip = np.linalg.det(R) < 0
    pts, faces = [], []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is None:
            raise ConversionError("could not triangulate a face for an affine transform")
        trsf = loc.Transformation()
        base = len(pts)
        for i in range(1, tri.NbNodes() + 1):
            q = tri.Node(i).Transformed(trsf)
            pts.append(R @ np.array([q.X(), q.Y(), q.Z()]) + t)
        rev = (face.Orientation() == TopAbs_REVERSED) != flip
        for i in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(i).Get()
            idx = [base + a - 1, base + b - 1, base + c - 1]
            faces.append(idx[::-1] if rev else idx)
        exp.Next()
    return _polyhedron(pts, faces, outward_ccw=True)


def _transform(shape: TopoDS_Shape, m) -> TopoDS_Shape:
    M = np.array(m, dtype=float)[:3, :4]
    R = M[:, :3]
    t = M[:, 3]
    if np.allclose(R, np.eye(3)) and np.allclose(t, 0):
        return shape
    RtR = R.T @ R
    s2 = RtR[0, 0]
    if np.allclose(RtR, s2 * np.eye(3), atol=1e-9) and s2 > 0:
        s = math.sqrt(s2)
        Rn = R / s
        trsf = gp_Trsf()
        if np.linalg.det(Rn) < 0:
            # mirror: gp_Trsf can hold it via SetValues
            pass
        trsf.SetValues(R[0, 0], R[0, 1], R[0, 2], t[0],
                       R[1, 0], R[1, 1], R[1, 2], t[1],
                       R[2, 0], R[2, 1], R[2, 2], t[2])
        return BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    if _is_polyhedral(shape):
        # Shear / non-uniform scale of a flat-faced solid (e.g. BOSL2's sheared rail flank): an
        # affine map keeps planes planar and lines straight, so transforming the vertices of an
        # exact triangulation is exact. BRepBuilderAPI_GTransform would turn every face into a
        # B-spline and the booleans after it crawl (rail-latch: >10 min).
        return _affine_polyhedral(shape, R, t)
    g = gp_GTrsf()
    g.SetVectorialPart(gp_Mat(*[float(x) for x in R.flatten()]))
    g.SetTranslationPart(gp_XYZ(*[float(x) for x in t]))
    return BRepBuilderAPI_GTransform(shape, g, True).Shape()


# ---- evaluator -------------------------------------------------------------------------------

class Converter:
    def __init__(self):
        self.stats = {"analytic_circles": 0, "polygonal_circles": 0, "polyhedra": 0, "hulls": 0,
                      "sheared": 0}

    def eval_list(self, nodes: list[Node]) -> list[Geo]:
        out = []
        for n in nodes:
            g = self.eval(n)
            if g is not None:
                out.append(g)
        return out

    def _group(self, nodes) -> Geo | None:
        gs = self.eval_list(nodes)
        if not gs:
            return None
        dims = {g.dim for g in gs}
        if len(dims) > 1:
            gs = [g for g in gs if g.dim == 3]  # OpenSCAD ignores 2-D siblings of 3-D in a union
        return Geo(_fuse([g.shape for g in gs]), gs[0].dim)

    def eval(self, n: Node) -> Geo | None:
        a = n.args
        name = n.name
        if name in ("group", "union", "render", "color", "parent_module"):
            return self._group(n.children)
        if name == "difference":
            gs = self.eval_list(n.children)
            if not gs:
                return None
            return Geo(_bool(BRepAlgoAPI_Cut, gs[0].shape, [g.shape for g in gs[1:] if g.dim == gs[0].dim]), gs[0].dim)
        if name == "intersection":
            gs = self.eval_list(n.children)
            if not gs:
                return None
            s = gs[0].shape
            for g in gs[1:]:
                s = _bool(BRepAlgoAPI_Common, s, [g.shape])
            return Geo(s, gs[0].dim)
        if name == "multmatrix":
            g = self._group(n.children)
            if g is None:
                return None
            M = np.array(a[0] if 0 in a else a.get("m"), dtype=float)
            R = M[:3, :3]
            if not np.allclose(R.T @ R, (R.T @ R)[0, 0] * np.eye(3), atol=1e-9):
                self.stats["sheared"] += 1
            return Geo(_transform(g.shape, M), g.dim)
        if name == "cube":
            size = a.get("size", 1)
            size = [size] * 3 if not isinstance(size, list) else size
            sx, sy, sz = (max(float(v), 1e-9) for v in size)
            s = BRepPrimAPI_MakeBox(sx, sy, sz).Shape()
            if a.get("center"):
                s = _transform(s, [[1, 0, 0, -sx / 2], [0, 1, 0, -sy / 2], [0, 0, 1, -sz / 2]])
            return Geo(s, 3)
        if name == "cylinder":
            h = float(a.get("h", 1))
            r1 = float(a.get("r1", a.get("r", 1)))
            r2 = float(a.get("r2", a.get("r", 1)))
            fr = _fragments(max(r1, r2), a)
            if fr >= FN_ANALYTIC_MIN:
                self.stats["analytic_circles"] += 1
                if abs(r1 - r2) < 1e-12:
                    s = BRepPrimAPI_MakeCylinder(r1, h).Shape()
                else:
                    s = BRepPrimAPI_MakeCone(r1, r2, h).Shape()
            else:
                self.stats["polygonal_circles"] += 1
                pts, faces = [], []
                for i in range(fr):
                    ang = 2 * math.pi * i / fr
                    pts.append((r1 * math.cos(ang), r1 * math.sin(ang), 0))
                for i in range(fr):
                    ang = 2 * math.pi * i / fr
                    pts.append((r2 * math.cos(ang), r2 * math.sin(ang), h))
                faces.append(list(range(fr - 1, -1, -1)) if True else [])
                faces.append(list(range(fr, 2 * fr)))
                for i in range(fr):
                    j = (i + 1) % fr
                    faces.append([i, j, fr + j, fr + i])
                s = _polyhedron(pts, faces, outward_ccw=True)
            if a.get("center"):
                s = _transform(s, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -h / 2]])
            return Geo(s, 3)
        if name == "sphere":
            r = float(a.get("r", 1))
            if _fragments(r, a) < FN_ANALYTIC_MIN:
                raise ConversionError("low-$fn sphere not supported")
            self.stats["analytic_circles"] += 1
            return Geo(BRepPrimAPI_MakeSphere(r).Shape(), 3)
        if name == "polyhedron":
            self.stats["polyhedra"] += 1
            return Geo(_polyhedron(a["points"], a["faces"]), 3)
        if name == "square":
            size = a.get("size", 1)
            size = [size] * 2 if not isinstance(size, list) else size
            sx, sy = float(size[0]), float(size[1])
            x0, y0 = (-sx / 2, -sy / 2) if a.get("center") else (0.0, 0.0)
            return Geo(_polygon_face([(x0, y0), (x0 + sx, y0), (x0 + sx, y0 + sy), (x0, y0 + sy)], None), 2)
        if name == "circle":
            r = float(a.get("r", 1))
            if _fragments(r, a) >= FN_ANALYTIC_MIN:
                self.stats["analytic_circles"] += 1
            else:
                self.stats["polygonal_circles"] += 1
            return Geo(_circle_face(r, a), 2)
        if name == "polygon":
            return Geo(_polygon_face(a["points"], a.get("paths")), 2)
        if name == "text":
            loops = _openscad_2d_loops(n.src)
            self.stats["text"] = self.stats.get("text", 0) + 1
            return Geo(_loops_face(loops), 2) if loops else None
        if name == "offset":
            g = self._group(n.children)
            if g is None:
                return None
            if a.get("r") not in (None, 0, 0.0):
                return Geo(_offset_face(g.shape, float(a["r"]), True), 2)
            d = float(a.get("delta", 0) or 0)
            if abs(d) < 1e-12:
                return g
            return Geo(_offset_face(g.shape, d, False), 2)
        if name == "linear_extrude":
            g = self._group(n.children)
            if g is None:
                return None
            h = float(a.get("height", 1))
            if float(a.get("twist", 0) or 0) != 0:
                raise ConversionError("linear_extrude with twist is not supported")
            sc = a.get("scale", 1)
            sc = [sc, sc] if not isinstance(sc, list) else sc
            if abs(float(sc[0]) - 1) < 1e-12 and abs(float(sc[1]) - 1) < 1e-12:
                s = BRepPrimAPI_MakePrism(g.shape, gp_Vec(0, 0, h)).Shape()
            else:
                top = _transform(g.shape, [[float(sc[0]), 0, 0, 0], [0, float(sc[1]), 0, 0], [0, 0, 1, h]])
                loft = BRepOffsetAPI_ThruSections(True, True)
                from OCP.BRepTools import BRepTools
                loft.AddWire(BRepTools.OuterWire_s(TopoDS.Face(_first_face(g.shape))))
                loft.AddWire(BRepTools.OuterWire_s(TopoDS.Face(_first_face(top))))
                loft.Build()
                s = loft.Shape()
            if a.get("center"):
                s = _transform(s, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -h / 2]])
            return Geo(s, 3)
        if name == "rotate_extrude":
            g = self._group(n.children)
            if g is None:
                return None
            ang = float(a.get("angle", 360) or 360)
            prof = _transform(g.shape, [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]])  # XY -> XZ
            return Geo(BRepPrimAPI_MakeRevol(prof, gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.radians(ang)).Shape(), 3)
        if name == "hull":
            gs = self.eval_list(n.children)
            if not gs:
                return None
            self.stats["hulls"] += 1
            if all(g.dim == 2 for g in gs):
                return Geo(_hull2d(gs), 2)
            return Geo(_hull3d([g for g in gs if g.dim == 3]), 3)
        raise ConversionError(f"unsupported CSG node '{name}'")


def _first_face(shape):
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    return exp.Current()


# -----------------------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------------------

@dataclass
class Result:
    ok: bool
    volume: float = 0.0
    mesh_volume: float | None = None
    faces: int = 0
    cylindrical: int = 0
    conical: int = 0
    planar: int = 0
    other: int = 0
    valid: bool = False
    seconds: float = 0.0
    stats: dict = field(default_factory=dict)
    error: str | None = None


def convert(csg_path: Path, step_path: Path, product: str, mesh_path: Path | None = None) -> Result:
    t0 = time.time()
    try:
        tree = parse_csg(csg_path.read_text(encoding="utf-8"))
        conv = Converter()
        g = conv._group(tree)
        if g is None or g.dim != 3:
            raise ConversionError("the CSG tree has no 3-D geometry")
        shape = g.shape
        up = ShapeUpgrade_UnifySameDomain(shape, True, True, False)
        up.Build()
        shape = up.Shape()
        fix = ShapeFix_Shape(shape)
        fix.Perform()
        shape = fix.Shape()
    except ConversionError as exc:
        return Result(ok=False, error=str(exc), seconds=time.time() - t0)

    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    res = Result(ok=True, volume=props.Mass(), stats=conv.stats)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        t = BRepAdaptor_Surface(TopoDS.Face(exp.Current())).GetType()
        res.faces += 1
        if t == GeomAbs_Cylinder:
            res.cylindrical += 1
        elif t == GeomAbs_Cone:
            res.conical += 1
        elif t == GeomAbs_Plane:
            res.planar += 1
        else:
            res.other += 1
        exp.Next()
    res.valid = BRepCheck_Analyzer(shape).IsValid()
    if not res.valid:
        res.ok = False
        res.error = "the B-rep does not pass BRepCheck (would import badly in CAD)"

    if mesh_path is not None and mesh_path.is_file():
        import trimesh
        res.mesh_volume = float(trimesh.load(str(mesh_path), force="mesh").volume)
        if res.mesh_volume > 0 and abs(res.volume - res.mesh_volume) / res.mesh_volume > VOLUME_TOL:
            res.ok = False
            res.error = (f"B-rep volume {res.volume:.1f} differs from the rendered mesh {res.mesh_volume:.1f} "
                         f"by more than {VOLUME_TOL:.0%}")

    Interface_Static.SetCVal_s("write.step.schema", "AP214")
    Interface_Static.SetCVal_s("write.step.product.name", product)
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    w = STEPControl_Writer()
    w.Transfer(shape, STEPControl_AsIs)
    step_path.parent.mkdir(parents=True, exist_ok=True)
    if int(w.Write(str(step_path))) != 1:
        res.ok = False
        res.error = "STEP writer failed"
    res.seconds = time.time() - t0
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="csg_to_step.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csg", type=Path)
    ap.add_argument("step", type=Path)
    ap.add_argument("--product", default=None)
    ap.add_argument("--mesh", type=Path, default=None, help="rendered mesh to cross-check the volume")
    args = ap.parse_args(argv)
    r = convert(args.csg, args.step, args.product or args.csg.stem, args.mesh)
    mv = f" mesh={r.mesh_volume:.1f}" if r.mesh_volume else ""
    print(f"ok={r.ok} valid={r.valid} volume={r.volume:.1f}{mv} faces={r.faces} "
          f"cylindrical={r.cylindrical} conical={r.conical} planar={r.planar} other={r.other} "
          f"stats={r.stats} time={r.seconds:.1f}s" + (f" error={r.error}" if r.error else ""))
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
