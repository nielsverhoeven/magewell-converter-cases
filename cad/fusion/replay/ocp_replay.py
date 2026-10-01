"""Offline replay of a build record with OpenCascade (issue #81, milestone K4b, plan section 3.12, verdict A1 and ruling a).

The recording backend of the kit writes ``record.json`` (``cad.fusion.gen.core.record``): the specs of one build in timeline
order, with every dimension still an expression.  This module is an interpreter of that record, not a backend: for one
parameter set it evaluates the expressions with ``cad.params``, executes the feature semantics of plan section 3.7 with
OpenCascade (polygon and circle faces, prisms, ruled lofts, pairwise fuse and cut, translated copies for patterns, suppress
flags skip the members of a set) and writes one STEP and one STL per exported component.  The builders can then be compared
with the OpenSCAD oracle (``scripts/parity.py``) without Fusion.

What a replay may claim: the builders describe the oracle's geometry, no dead feature under a configuration, re-join
containment.  What it may not claim: anything that needs Fusion itself (health, constraint state, Fusion's own volume).  A replay
export is never a release candidate.  Where replay and Fusion disagree, plan section 3.7 decides.

Run at the repository root::

    python -m cad.fusion.replay.ocp_replay RECORD (--configuration ID | --all) [--out DIR] [--plan PLANFILE]
                                           [--stage K] [--facet [SIDES]]

The tree written is ``OUT/<configuration>/exports/<target>/<part>.step`` and ``.model.stl`` (the layout of the runtime's
exports) plus ``OUT/replay.json``; ``OUT`` defaults to ``build/replay/<document>``.  Exit code 0: replayed, every re-join
inside its cut.  1: a re-join added volume outside its cut.  2: an unusable record, plan or command line.

Imports the standard library, ``cad.params`` and ``OCP`` only.  Never part of an input digest; nothing outside tests and
``scripts/`` imports it.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

from OCP.Bnd import Bnd_Box
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon,
                                BRepBuilderAPI_MakeWire, BRepBuilderAPI_Transform)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Ax2, gp_Circ, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec
from OCP.GProp import GProp_GProps
from OCP.Interface import Interface_Static
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.StlAPI import StlAPI_Writer
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Compound
try:  # OCP >= 8 moved the NCollection lists to OCP.collections
    from OCP.TopTools import TopTools_ListOfShape
except ImportError:  # pragma: no cover - depends on the OCP build
    from OCP.collections import List_TopoDS_Shape as TopTools_ListOfShape

from cad import params

FUZZY = 1e-6              # mm, the fuzzy value of every boolean
LINEAR_DEFLECTION = 0.005  # mm, the STL meshing tolerance
ANGULAR_DEFLECTION = 0.5   # rad
REJOIN_TOL = 1e-3          # mm3: a re-join may add at most this much outside its cut (rounding of the booleans)
DEAD_TOL = 1e-6            # mm3: a feature that changes the volume by less than this is dead
FACET_DEFAULT = 64         # sides of a circle in the diagnostic facet mode (the oracle's $fn with circum)

AXIS_OF_PLANE = {"YZ": "X", "XZ": "Y", "XY": "Z"}
AXIS_DIR = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
# direction of the normal u x v of the sketch plane of each axis; a circle is made counter-clockwise about it
CIRCLE_NORMAL = {"X": (1, 0, 0), "Y": (0, -1, 0), "Z": (0, 0, 1)}
FEATURE_SPECS = ("ExtrudeSpec", "LoftSpec", "PatternSpec", "TextSpec")


class ReplayError(Exception):
    """A record, plan or option that cannot be replayed."""


# ---- measuring -------------------------------------------------------------------------------------------------------


def _volume(shape) -> float:
    if shape is None:
        return 0.0
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def _count(shape, kind) -> int:
    n, explorer = 0, TopExp_Explorer(shape, kind)
    while explorer.More():
        n += 1
        explorer.Next()
    return n


def measure(shape) -> dict:
    """Volume, area, box corners, solid and shell count and validity of a shape (``Bnd_Box.Get`` is not bound: corners)."""
    area = GProp_GProps()
    BRepGProp.SurfaceProperties_s(shape, area)
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box, False, False)
    lo, hi = box.CornerMin(), box.CornerMax()
    return {"volume_mm3": _volume(shape), "area_mm2": area.Mass(),
            "bbox_min": [lo.X(), lo.Y(), lo.Z()], "bbox_max": [hi.X(), hi.Y(), hi.Z()],
            "solids": _count(shape, TopAbs_SOLID), "shells": _count(shape, TopAbs_SHELL),
            "valid": bool(BRepCheck_Analyzer(shape).IsValid())}


# ---- booleans (pairwise: one fuse with many tools silently drops material, plan 2.7) ---------------------------------------


def _boolean(op, a, tool, what: str):
    args, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(a)
    tools.Append(tool)
    algo = op()
    algo.SetArguments(args)
    algo.SetTools(tools)
    algo.SetFuzzyValue(FUZZY)
    algo.SetRunParallel(True)
    algo.Build()
    if not algo.IsDone():
        raise ReplayError(f"{what}: {op.__name__} failed")
    return algo.Shape()


def _fuse_all(shapes: list, what: str):
    acc = shapes[0]
    for shape in shapes[1:]:
        acc = _boolean(BRepAlgoAPI_Fuse, acc, shape, what)
    return acc


# ---- geometry of a sketch --------------------------------------------------------------------------------------------------


def _point(axis: str, u: float, v: float, w: float) -> gp_Pnt:
    """The model point of the in-plane coordinates ``u``, ``v`` at ``w`` along ``axis`` (u, v as in the facade: X: y z; Y: x z; Z: x y)."""
    x, y, z = {"Z": (u, v, w), "Y": (u, w, v), "X": (w, u, v)}[axis]
    return gp_Pnt(x, y, z)


class _Loop:
    """One closed outline in model coordinates: ``points`` for a polygon, or a circle ``(cu, cv, r)``."""

    def __init__(self, points=None, circle=None):
        self.points, self.circle = points, circle

    def sign(self) -> int:
        """+1 counter-clockwise in (u, v), -1 clockwise."""
        if self.circle is not None:
            return 1
        pts = self.points
        area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        return 1 if area >= 0 else -1


def _loop(spec: dict, val, facet: int | None) -> _Loop:
    kind, args = spec["kind"], spec["args"]
    if kind == "rect":
        u0, u1, v0, v1 = (val(a) for a in args)
        return _Loop(points=[(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    if kind == "polygon":
        return _Loop(points=[(val(u), val(v)) for u, v in args])
    if kind == "circle":
        cu, cv, d = (val(a) for a in args)
        if facet:  # diagnostic: the n-gon OpenSCAD makes with circum=true (radius over cos(pi/n), turned half a step)
            rr, phase = d / 2 / math.cos(math.pi / facet), math.pi / facet
            return _Loop(points=[(cu + rr * math.cos(phase + 2 * math.pi * i / facet),
                                  cv + rr * math.sin(phase + 2 * math.pi * i / facet)) for i in range(facet)])
        return _Loop(circle=(cu, cv, d / 2))
    raise ReplayError(f"unknown loop kind {kind!r}")


def _wire(axis: str, loop: _Loop, w: float, reverse: bool = False):
    """The wire of a loop at ``w``; ``reverse`` runs it clockwise (a hole against its outer loop)."""
    if loop.circle is not None:
        cu, cv, r = loop.circle
        centre = _point(axis, cu, cv, w)
        normal = [-c if reverse else c for c in CIRCLE_NORMAL[axis]]
        edge = BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(centre, gp_Dir(*normal)), r)).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()
    poly = BRepBuilderAPI_MakePolygon()
    for u, v in (reversed(loop.points) if reverse else loop.points):
        poly.Add(_point(axis, u, v, w))
    poly.Close()
    return poly.Wire()


def _face(axis: str, outer: _Loop, holes: list, w: float):
    maker = BRepBuilderAPI_MakeFace(_wire(axis, outer, w), True)
    for hole in holes:
        maker.Add(_wire(axis, hole, w, reverse=hole.sign() == outer.sign()))  # a hole runs against its outer loop
    return maker.Face()


def _prism(face, axis: str, lo: float, hi: float, what: str):
    dx, dy, dz = AXIS_DIR[axis]
    shape = BRepPrimAPI_MakePrism(face, gp_Vec(dx * (hi - lo), dy * (hi - lo), dz * (hi - lo))).Shape()
    if _volume(shape) < 0:  # a face whose normal opposes the sweep makes an inside-out solid
        shape = shape.Reversed()
    if _volume(shape) <= 0:
        raise ReplayError(f"{what}: the extrusion has no volume")
    return shape


def _translated(shape, vector):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(*vector))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


# ---- the interpreter -------------------------------------------------------------------------------------------------------


class ComponentResult:
    """What the replay made of one component: its shape (a compound of bodies for a reserve or ghost) and a report."""

    def __init__(self, name: str, role: str):
        self.name, self.role = name, role
        self.bodies: list = []
        self.features: list[dict] = []
        self.rejoins: list[dict] = []
        self.skipped: list[dict] = []

    @property
    def shape(self):
        if not self.bodies:
            return None
        if len(self.bodies) == 1:
            return self.bodies[0]
        compound, builder = TopoDS_Compound(), BRep_Builder()
        builder.MakeCompound(compound)
        for body in self.bodies:
            builder.Add(compound, body)
        return compound

    @property
    def dead_features(self) -> list[str]:
        return [f["name"] for f in self.features if f["dead"]]

    def to_json(self) -> dict:
        out = {"role": self.role}
        if self.shape is not None:
            out.update({k: ([round(x, 6) for x in v] if isinstance(v, list) else round(v, 6) if isinstance(v, float) else v)
                        for k, v in measure(self.shape).items()})
        out.update({"features": self.features, "rejoins": self.rejoins, "skipped": self.skipped})
        return out


def _plane_normals(record: dict) -> dict:
    """Sign of the normal of each origin plane along its axis: +1 unless the record says otherwise (key ``plane_normal``) or
    an extrude on that plane records a negative direction (the only place the specs carry it)."""
    normals = {"XY": 1, "XZ": 1, "YZ": 1}
    normals.update(record.get("plane_normal", {}))
    by_name = {s["name"]: s for s in record["specs"]}
    for spec in record["specs"]:
        if spec["spec"] in ("ExtrudeSpec", "TextSpec"):
            on = by_name[spec["sketch"]]["on"]
            if on.startswith("origin:"):
                normals[on[7:]] = 1 if spec["direction"] == "positive" else -1
    return normals


class _Interpreter:
    def __init__(self, record: dict, env, suppress: dict, facet: int | None):
        self.record, self.suppress, self.facet = record, suppress or {}, facet
        self.env = env
        self.by_name = {s["name"]: s for s in record["specs"]}
        self.normals = _plane_normals(record)
        self.rejoin_cuts = {s["within"] for s in record["specs"] if s["spec"] == "ExtrudeSpec" and s.get("within")}

    def val(self, text) -> float:
        return 0.0 if text is None else params.evaluate_number(text, self.env)

    def suppressed(self, name: str) -> bool:
        return bool(self.suppress.get("_".join(name.split("_")[:2]), False))

    # -- sketches and planes --------------------------------------------------------------------------------------------

    def frame(self, sketch: dict) -> tuple[str, float]:
        """``(axis, w)``: the model axis normal to the sketch plane and the sketch's coordinate along it."""
        on = sketch["on"]
        if on.startswith("origin:"):
            return AXIS_OF_PLANE[on[7:]], 0.0
        plane = self.by_name[on[6:]]
        base = plane["base"][7:]
        return AXIS_OF_PLANE[base], self.normals[base] * self.val(plane["offset"])

    def faces(self, sketch: dict, w: float, axis: str) -> list:
        if sketch["rule"] == "text":
            raise ReplayError(f"{sketch['name']}: a text sketch has no replay")
        loops = [_loop(spec, self.val, self.facet) for spec in sketch["loops"]]
        if sketch["rule"] == "ring":
            holes = [_loop(spec, self.val, self.facet) for spec in sketch["holes"]]
            return [_face(axis, loops[0], holes, w)]
        return [_face(axis, loop, [], w) for loop in loops]

    # -- features -------------------------------------------------------------------------------------------------------

    def extrude_tools(self, spec: dict) -> list:
        sketch = self.by_name[spec["sketch"]]
        axis, w = self.frame(sketch)
        start = (1 if spec["direction"] == "positive" else -1) * self.val(spec["start_offset"])
        end = start + self.val(spec["distance"])
        lo, hi = min(start, end), max(start, end)
        return [_prism(face, axis, lo, hi, spec["name"]) for face in self.faces(sketch, lo, axis)]

    def loft_tool(self, spec: dict):
        sections, axes = [], set()
        for name in spec["sketches"]:
            sketch = self.by_name[name]
            axis, w = self.frame(sketch)
            axes.add(axis)
            if len(sketch["loops"]) != 1:
                raise ReplayError(f"{spec['name']}: a loft section is one loop")
            sections.append(_wire(axis, _loop(sketch["loops"][0], self.val, self.facet), w))
        if len(axes) != 1:
            raise ReplayError(f"{spec['name']}: the two sections lie on different axes")
        loft = BRepOffsetAPI_ThruSections(True, True)  # a solid, ruled: straight generators, a cone frustum for two circles
        for wire in sections:
            loft.AddWire(wire)
        loft.Build()
        if not loft.IsDone():
            raise ReplayError(f"{spec['name']}: the loft failed")
        shape = loft.Shape()
        if _volume(shape) < 0:
            shape = shape.Reversed()
        return shape

    def run(self, component: dict, specs: list, stage) -> ComponentResult:
        result = ComponentResult(component["name"], component["role"])
        tools: dict[str, list] = {}      # feature name -> its tool solids (a pattern repeats them)
        ops: dict[str, str] = {}
        removed: dict[str, object] = {}  # cut name -> the material that cut removed (kept for the cuts a re-join names)
        done = 0
        for spec in specs:
            kind = spec["spec"]
            if kind not in FEATURE_SPECS:
                continue
            name = spec["name"]
            if stage is not None:
                if isinstance(stage, int):
                    if done >= stage:
                        break
                done += 1
            if spec.get("phase", "build") != "build":
                result.skipped.append({"component": result.name, "name": name, "reason": "phase 'enhance' has no replay"})
                continue
            if kind == "TextSpec":
                result.skipped.append({"component": result.name, "name": name, "reason": "a text feature has no replay"})
                continue
            op = spec["op"] if kind != "PatternSpec" else ops.get(spec["seed"], "")
            if self.suppressed(name):
                result.features.append({"name": name, "op": op, "suppressed": True, "volume_change_mm3": 0.0, "dead": False})
                continue
            try:
                self.apply(result, spec, tools, ops, removed)
            except ReplayError:
                raise
            except Exception as exc:  # an OpenCascade failure names the feature
                raise ReplayError(f"{name}: {type(exc).__name__}: {exc}") from exc
            if isinstance(stage, str) and name == stage:
                break
        return result

    def apply(self, result: ComponentResult, spec: dict, tools: dict, ops: dict, removed: dict) -> None:
        kind, name = spec["spec"], spec["name"]
        if kind == "PatternSpec":
            seed, op = spec["seed"], ops[spec["seed"]]
            if seed not in tools:
                raise ReplayError(f"{name}: its seed {seed} was not replayed")
            instances = self.pattern_tools(spec, tools[seed])
            self.combine(result, name, op, instances, removed, spec.get("within"), keep_region=seed in self.rejoin_cuts,
                         region_key=seed)
            return
        made = [self.loft_tool(spec)] if kind == "LoftSpec" else self.extrude_tools(spec)
        tools[name], ops[name] = made, spec["op"]
        self.combine(result, name, spec["op"], made, removed, spec.get("within"), keep_region=name in self.rejoin_cuts,
                     region_key=name)

    def pattern_tools(self, spec: dict, seed_tools: list) -> list:
        """The copies of the seed at ``k * pitch`` for k from 1 (k = 0 is the seed itself, already applied)."""
        count = int(round(self.val(spec["count"])))
        pitch = self.val(spec["pitch"])
        steps = [(i, 0) for i in range(1, count)]
        second = None
        if spec.get("axis2"):
            second = (AXIS_DIR[spec["axis2"]], int(round(self.val(spec["count2"]))), self.val(spec["pitch2"]))
            steps = [(i, j) for i in range(count) for j in range(second[1]) if (i, j) != (0, 0)]
        first = AXIS_DIR[spec["axis"]]
        out = []
        for i, j in steps:
            vector = [first[k] * i * pitch + (second[0][k] * j * second[2] if second else 0.0) for k in range(3)]
            out += [_translated(tool, vector) for tool in seed_tools]
        return out

    def combine(self, result: ComponentResult, name: str, op: str, made: list, removed: dict, within, keep_region: bool,
                region_key: str) -> None:
        if op == "new":
            before = sum(_volume(b) for b in result.bodies)
            result.bodies.append(_fuse_all(made, name))
            change = sum(_volume(b) for b in result.bodies) - before
        else:
            if not result.bodies:
                raise ReplayError(f"{name}: op {op!r} on component {result.name}, which has no body (its 'new' feature is suppressed?)")
            if result.role != "part":
                raise ReplayError(f"{name}: a {result.role} component holds bodies only, op {op!r}")
            body = result.bodies[0]
            before = _volume(body)
            if op == "rejoin":
                result.rejoins.append(self.rejoin(name, within, made, body, removed))
            for tool in made:
                if op == "cut" and keep_region:
                    region = _boolean(BRepAlgoAPI_Common, body, tool, name)
                    if _volume(region) > 0:
                        removed[region_key] = region if region_key not in removed else \
                            _boolean(BRepAlgoAPI_Fuse, removed[region_key], region, name)
                body = _boolean(BRepAlgoAPI_Cut if op == "cut" else BRepAlgoAPI_Fuse, body, tool, name)
            result.bodies[0] = body
            change = _volume(body) - before
        result.features.append({"name": name, "op": op, "suppressed": False, "volume_change_mm3": round(change, 6),
                                "dead": op != "new" and abs(change) < DEAD_TOL})

    @staticmethod
    def rejoin(name: str, within: str, made: list, body, removed: dict) -> dict:
        """The volume the re-join adds, and the part of it outside the material its ``within`` cut removed."""
        added = _fuse_all([_boolean(BRepAlgoAPI_Cut, tool, body, name) for tool in made], name) if made else None
        added_volume = _volume(added)
        region = removed.get(within)
        if region is None or added_volume <= 0:
            outside = added_volume  # no material was removed there (its cut is suppressed): all of it is outside
        else:
            outside = _volume(_boolean(BRepAlgoAPI_Cut, added, region, name))
        return {"name": name, "within": within, "added_mm3": round(added_volume, 6), "outside_mm3": round(max(outside, 0.0), 6)}


def replay(record: dict, env, suppress: dict | None = None, stage=None, facet: int | None = None, components=None) -> dict:
    """Replay a build record for one parameter set.

    ``env`` is ``cad.params.environment(rows, solved)`` of that configuration and ``suppress`` its flags (``Owner_Set``: true
    means suppressed).  ``stage`` stops each component after that many features (an int) or after the feature of that name (a
    str).  ``facet`` is the diagnostic mode: every circle becomes that many sides, as the oracle tessellates it.  ``components``
    limits the replay to those component names.  Returns ``{component name: ComponentResult}`` in record order: the shape, the
    volume change of every feature, per re-join the volume it added outside its cut, and what was skipped."""
    interpreter = _Interpreter(record, env, suppress or {}, facet)
    out = {}
    for component in record["components"]:
        if components is not None and component["name"] not in components:
            continue
        specs = [s for s in record["specs"] if s.get("component") == component["name"]]
        out[component["name"]] = interpreter.run(component, specs, stage)
    return out


# ---- export and report ---------------------------------------------------------------------------------------------------


def _clean(shape):
    """Merge the coplanar faces the booleans leave behind; the shape itself when that fails."""
    try:
        unify = ShapeUpgrade_UnifySameDomain(shape, True, True, False)
        unify.Build()
        return unify.Shape()
    except Exception:  # pragma: no cover - cosmetic only
        return shape


def _configuration(plan: dict, configuration_id: str) -> dict:
    for configuration in plan.get("configurations", []):
        if configuration.get("id") == configuration_id:
            return configuration
    raise ReplayError(f"the plan has no configuration {configuration_id!r}")


def export(shapes: dict, plan: dict, configuration_id: str, out_dir) -> list[dict]:
    """Write ``(out_dir)/(target)/(part).step`` and ``.model.stl`` for every entry of the configuration's allow-list
    (``plan["configurations"][i]["exports"]``).  ``shapes`` maps a component name to a ``ComponentResult`` or a shape.
    Returns one record per entry: component, target, part and the files written, relative to ``out_dir``."""
    out_dir = Path(out_dir)
    records = []
    for entry in _configuration(plan, configuration_id).get("exports", []):
        item = shapes.get(entry["component"])
        shape = getattr(item, "shape", item)
        if shape is None:
            raise ReplayError(f"{entry['component']}: nothing to export (not replayed, or no body)")
        shape = _clean(shape)
        stem = out_dir.joinpath(*entry["target"].split("/"), entry["part"])
        stem.parent.mkdir(parents=True, exist_ok=True)
        step, stl = Path(f"{stem}.step"), Path(f"{stem}.model.stl")
        Interface_Static.SetCVal_s("write.step.schema", "AP214")
        Interface_Static.SetCVal_s("write.step.product.name", entry["part"])
        Interface_Static.SetCVal_s("write.step.unit", "MM")
        writer = STEPControl_Writer()
        writer.Transfer(shape, STEPControl_AsIs)
        if int(writer.Write(str(step))) != 1:
            raise ReplayError(f"{entry['component']}: the STEP writer failed")
        BRepMesh_IncrementalMesh(shape, LINEAR_DEFLECTION, False, ANGULAR_DEFLECTION, True)
        mesh_writer = StlAPI_Writer()
        mesh_writer.ASCIIMode = False
        if not mesh_writer.Write(shape, str(stl)):
            raise ReplayError(f"{entry['component']}: the STL writer failed")
        records.append({"component": entry["component"], "target": entry["target"], "part": entry["part"],
                        "files": [p.relative_to(out_dir).as_posix() for p in (step, stl)]})
    return records


def report(out_dir, configuration_id: str, results: dict, exports: list | None = None, document: str = "",
           values: dict | None = None, suppress: dict | None = None) -> dict:
    """Add or replace the entry of one configuration in ``(out_dir)/replay.json``; returns that entry."""
    out_dir = Path(out_dir)
    path = out_dir / "replay.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"schema": 1, "kind": "builder-replay", "configurations": {}}
    if document:
        doc["document"] = document
    entry = {"suppress": dict(suppress or {}), "components": {n: r.to_json() for n, r in results.items()},
             "exports": list(exports or []),
             "skipped": [s for r in results.values() for s in r.skipped],
             "dead_features": [f for r in results.values() for f in r.dead_features],
             "rejoin_outside_mm3": round(sum(j["outside_mm3"] for r in results.values() for j in r.rejoins), 6)}
    if values is not None:
        entry["values"] = dict(values)
    doc["configurations"][configuration_id] = entry
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return entry


# ---- the command -----------------------------------------------------------------------------------------------------------


def _load_json(path, what: str) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReplayError(f"{path}: cannot read the {what}: {exc}") from None
    if not isinstance(data, dict):
        raise ReplayError(f"{path}: the {what} is a JSON object")
    return data


def _inputs(plan: dict, configuration_id: str):
    """``(env, parameter set)`` of one configuration, read the way the kit's plan command reads them (``cad.params``)."""
    try:
        csv_files = list(plan["registry"]["csv"])
        set_files = sorted({f for pattern in plan["registry"]["sets"] for f in glob.glob(pattern, recursive=True)})
        rows = params.registry(csv_files, set_files)
        one = _configuration(plan, configuration_id)["set"]
        pset = params.parameter_set(one["file"], one.get("config", "default"))
        return params.environment(rows, {"values": pset["values"], "units": pset["units"]}), pset
    except (KeyError, OSError, ValueError) as exc:
        raise ReplayError(f"cannot read the registry or the parameter set of {configuration_id!r}: {exc}") from None


def run_configuration(record: dict, plan: dict, configuration_id: str, out_dir, stage=None, facet=None) -> dict:
    """Replay, export and report one configuration; returns its report entry."""
    env, pset = _inputs(plan, configuration_id)
    exported = {e["component"] for e in _configuration(plan, configuration_id).get("exports", [])}
    results = replay(record, env, pset["suppress"], stage=stage, facet=facet, components=exported or None)
    out_dir = Path(out_dir)
    safe = configuration_id.replace("/", "_")
    exports = export(results, plan, configuration_id, out_dir / safe / "exports")
    for item in exports:
        item["files"] = [f"{safe}/exports/{f}" for f in item["files"]]
    return report(out_dir, configuration_id, results, exports, record.get("document", ""), pset["values"], pset["suppress"])


def _stage(text: str):
    return int(text) if text.lstrip("-").isdigit() else text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cad.fusion.replay.ocp_replay", description=__doc__.split("\n\n")[0])
    parser.add_argument("record", help="the build record (record.json) of the recording backend")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--configuration", metavar="ID", help="replay this configuration of the plan")
    which.add_argument("--all", action="store_true", help="replay every configuration of the plan")
    parser.add_argument("--out", metavar="DIR", help="output directory (default build/replay/<document>)")
    parser.add_argument("--plan", metavar="PLANFILE", help="the document plan (default: the key 'plan' of the record)")
    parser.add_argument("--stage", type=_stage, metavar="K", help="stop each component after K features or after the feature named K")
    parser.add_argument("--facet", nargs="?", type=int, const=FACET_DEFAULT, metavar="SIDES",
                        help="diagnostic: circles as n-gons like the oracle's tessellation (default 64 sides); never a verdict")
    args = parser.parse_args(argv)
    try:
        record = _load_json(args.record, "record")
        plan_path = args.plan or record.get("plan")
        if not plan_path:
            raise ReplayError("no plan: pass --plan, or record the build with the key 'plan'")
        plan = _load_json(plan_path, "plan")
        out_dir = Path(args.out or Path("build") / "replay" / record.get("document", "document"))
        ids = [c["id"] for c in plan.get("configurations", [])] if args.all else [args.configuration]
        if not ids:
            raise ReplayError("the plan has no configuration")
        failed = False
        for configuration_id in ids:
            entry = run_configuration(record, plan, configuration_id, out_dir, args.stage, args.facet)
            files = sum(len(e["files"]) for e in entry["exports"])
            print(f"{configuration_id}: {len(entry['components'])} component(s), {files} file(s), "
                  f"re-join outside its cut {entry['rejoin_outside_mm3']} mm3")
            for name in entry["dead_features"]:
                print(f"  dead feature (changes no volume): {name}")
            for item in entry["skipped"]:
                print(f"  skipped {item['name']}: {item['reason']}")
            if entry["rejoin_outside_mm3"] > REJOIN_TOL:
                failed = True
                print(f"  FAIL: a re-join adds volume outside its cut in {configuration_id}")
        return 1 if failed else 0
    except ReplayError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
