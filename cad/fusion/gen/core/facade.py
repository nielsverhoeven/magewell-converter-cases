"""The facade of the Fusion modelling kit: the only API a builder calls (issue #81, plan sections 3.2 to 3.8).

The facade does all the thinking once, in plain Python: it validates names and expressions, decides which
dimensions and constraints a sketch gets (3.6), builds the feature spec (3.7) and hands both to its backend in
timeline order.  A backend only executes a spec.  This module is milestone K2a: components, loops, ``extrude``
with its phase rule and ``within``, ``shared_call`` and the reserved ``Kit.enhance``.  Loft, pattern and text are
milestone K2b.

Standard library only; ``cad.params`` is reached through ``expr.Env`` (which imports it inside its body).

Conventions of the specs this module writes (shared by every backend and by the checks):

* ``u`` and ``v`` are the two in-plane model axes of the sketch, in the order of 3.3: ``(y, z)`` for axis X,
  ``(x, z)`` for Y, ``(x, y)`` for Z.  ``"O"`` is the sketch's own origin point, ``"P0"`` the datum point (or
  ``"O"`` itself when the datum is zero on both axes).
* constraint kinds: ``parallel_u`` / ``parallel_v`` (a line along u or v), ``same_u`` / ``same_v`` (two points
  share that coordinate).  Dimension kinds: ``distance`` (between two points, measured along ``axis`` u or v) and
  ``diameter`` (``a`` is the circle).
* ``direction`` of a feature is ``"positive"`` when plus ``axis`` points along the normal of the sketch plane
  (``PLANE_NORMAL``), else ``"negative"``.
"""
from __future__ import annotations

import contextlib

from . import expr, names
from .names import KitError
from .record import RecordingBackend
from .spec import (ComponentSpec, Constraint, Dim, ExtrudeSpec, Loop, SharedCall, SketchSpec)

API = 1

# Sign of the normal of each origin plane along its own axis.  Placeholder values until probe G1 fills them in
# (one line to change); the Fusion backend asserts them at run time, so the recording backend writes the same text.
PLANE_NORMAL = {"XY": 1, "XZ": 1, "YZ": 1}

AXES = ("X", "Y", "Z")
PLANE_OF = {"X": "YZ", "Y": "XZ", "Z": "XY"}
# index into the datum (dx, dy, dz) of the two in-plane axes u and v
UV_INDEX = {"X": (1, 2), "Y": (0, 2), "Z": (0, 1)}
OPS = ("new", "join", "cut", "rejoin")
RANK = {"new": 0, "join": 1, "cut": 2, "rejoin": 3}
ROLES = ("part", "reserve", "ghost")
EPS = 1e-6


class PhaseError(KitError):
    """A call that goes back in the order new, joins, cuts, re-joins of a part component (3.2 rule 6, 3.8)."""


class DuplicateNameError(KitError):
    """A component, sketch, plane or feature name that occurs twice in the document (3.5)."""


class ZeroOffsetError(KitError):
    """An offset from the datum that is not textually zero but evaluates to less than 1e-6 mm (3.6 step 5)."""


class _AnyOwner:
    """Owner list used when the context carries none: the grammar is still checked, the owner is checked by CK1."""

    def __contains__(self, item):
        return True

    def __iter__(self):
        return iter(())


class _Enhance:
    """``Kit.enhance``: reserved for #85 (verdict A9).  Any attribute access raises NotImplementedError."""

    def __getattr__(self, name):
        raise NotImplementedError(f"Kit.enhance.{name}: the enhancement surface is reserved for #85 and not implemented by #81")


# ---- geometry helpers ------------------------------------------------------------------------------------------------


def _bbox(loop: Loop, val) -> tuple[float, float, float, float]:
    """``(u_lo, u_hi, v_lo, v_hi)`` of a loop under the build values; ``val`` evaluates an expression or None."""
    if loop.kind == "rect":
        u0, u1, v0, v1 = (val(a) for a in loop.args)
        return min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1)
    if loop.kind == "circle":
        cu, cv, d = (val(a) for a in loop.args)
        return cu - d / 2, cu + d / 2, cv - d / 2, cv + d / 2
    us = [val(p[0]) for p in loop.args]
    vs = [val(p[1]) for p in loop.args]
    return min(us), max(us), min(vs), max(vs)


def _touch(a, b) -> bool:
    """Bounding boxes that touch or overlap."""
    return a[0] <= b[1] and b[0] <= a[1] and a[2] <= b[3] and b[2] <= a[3]


def _inside(inner, outer) -> bool:
    """``inner`` lies strictly inside ``outer``."""
    return outer[0] < inner[0] and inner[1] < outer[1] and outer[2] < inner[2] and inner[3] < outer[3]


class _SketchBuilder:
    """The six steps of 3.6.  Collects points, lines, circles, constraints and dimensions in creation order."""

    def __init__(self, env: expr.Env, where: str, du, dv):
        self.env, self.where, self.du, self.dv = env, where, du, dv
        self.points: list[str] = []
        self.lines: list[tuple] = []
        self.circles: list[tuple] = []
        self.constraints: list[Constraint] = []
        self.dims: list[Dim] = []
        self.p0 = "O"
        self._datum_point()

    def val(self, text) -> float:
        return 0.0 if text is None else self.env.value(text)

    def _datum_point(self) -> None:
        """Step 1: the datum point P0."""
        if self.du is None and self.dv is None:
            return
        self.p0 = "P0"
        self.points.append("P0")
        for ax, d in (("u", self.du), ("v", self.dv)):
            if d is None:
                self.constraints.append(Constraint(f"same_{ax}", "O", "P0"))
                continue
            value = self.val(d)
            if abs(value) < EPS:
                raise ZeroOffsetError(f"{self.where}: the datum {d!r} on {ax} evaluates to zero, a dimension cannot hold it")
            # the only place where an expression is negated by evaluation; CK5/CK6 prove the sign is the same everywhere
            self.dims.append(Dim("distance", "O", "P0", ax, d if value > 0 else expr.neg(d)))

    def place(self, point: str, ax: str, coord) -> None:
        """Steps 2 to 5: fix one coordinate of ``point`` against P0 (a dimension, or a constraint when it equals the datum)."""
        datum = self.du if ax == "u" else self.dv
        if expr.same(coord, datum):
            self.constraints.append(Constraint(f"same_{ax}", self.p0, point))
            return
        offset = self.val(coord) - self.val(datum)
        if abs(offset) < EPS:
            raise ZeroOffsetError(f"{self.where}: {coord!r} minus the datum {datum!r} evaluates to zero on {ax}; "
                                  "a sketch dimension cannot hold a zero offset")
        self.dims.append(Dim("distance", self.p0, point, ax, expr.sub(coord, datum)))

    def size(self, a: str, b: str, ax: str, hi, lo) -> None:
        text = expr.sub(hi, lo)
        if text is None:
            raise KitError(f"{self.where}: both ends of a size on {ax} are None")
        self.dims.append(Dim("distance", a, b, ax, text))

    def rect(self, i: int, loop: Loop) -> None:
        u0, u1, v0, v1 = loop.args
        p = [f"p{i}_{k}" for k in range(4)]
        self.points += p
        self.lines += [(f"l{i}_{k}", p[k], p[(k + 1) % 4]) for k in range(4)]
        for k in range(4):
            self.constraints.append(Constraint("parallel_u" if k % 2 == 0 else "parallel_v", f"l{i}_{k}", ""))
        self.place(p[0], "u", u0)
        self.place(p[0], "v", v0)
        self.size(p[0], p[1], "u", u1, u0)
        self.size(p[1], p[2], "v", v1, v0)

    def circle(self, i: int, loop: Loop) -> None:
        cu, cv, d = loop.args
        self.points.append(f"c{i}")
        self.circles.append((f"k{i}", f"c{i}"))
        self.place(f"c{i}", "u", cu)
        self.place(f"c{i}", "v", cv)
        self.dims.append(Dim("diameter", f"k{i}", "", "", d))

    def polygon(self, i: int, loop: Loop) -> None:
        pts = loop.args
        q = [f"q{i}_{k}" for k in range(len(pts))]
        self.points += q
        self.lines += [(f"m{i}_{k}", q[k], q[(k + 1) % len(q)]) for k in range(len(q))]
        for k, (u, v) in enumerate(pts):
            for ax, coord, idx in (("u", u, 0), ("v", v, 1)):
                if k > 0 and expr.same(coord, pts[k - 1][idx]):
                    self.constraints.append(Constraint(f"same_{ax}", q[k - 1], q[k]))
                else:
                    self.place(q[k], ax, coord)

    def add(self, i: int, loop: Loop) -> None:
        getattr(self, loop.kind)(i, loop)


# ---- the kit ---------------------------------------------------------------------------------------------------------


class Kit:
    """One build: owns the backend, the evaluator for the build values and the names used so far."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.env = expr.Env(ctx.registry, ctx.values)
        backend = ctx.backend
        document = getattr(ctx, "document", "")
        if backend == "recording":
            self._backend = RecordingBackend(document)
        elif backend == "fusion":
            from .fusion_backend import FusionBackend  # imported only here: adsk must not load for a recording run

            self._backend = FusionBackend(ctx)
        else:
            raise KitError(f"ctx.backend is 'recording' or 'fusion', got {backend!r}")
        owners = getattr(ctx, "owners", None)
        self._owners = owners if owners else _AnyOwner()
        self._used: set[str] = set()
        self._components: dict[str, Component] = {}
        self._calls: list[SharedCall] = []
        self.enhance = _Enhance()

    def component(self, name, *, role, datum):
        """A component with the identity transform under the root.  ``datum`` is ``(dx, dy, dz)``, each an
        expression or None for zero."""
        names.component_check(name)
        if role not in ROLES:
            raise KitError(f"{name}: role is one of {ROLES}, got {role!r}")
        if name in self._components:
            raise DuplicateNameError(f"component {name!r} exists already")
        try:
            dx, dy, dz = datum
        except (TypeError, ValueError):
            raise KitError(f"{name}: datum is (dx, dy, dz), got {datum!r}") from None
        for label, d in zip("xyz", (dx, dy, dz)):
            if d is not None:
                expr.check(d, self.env.names, f"{name}.datum_{label}")
        comp = Component(self, name, role, (dx, dy, dz))
        self._components[name] = comp
        self._backend.execute(ComponentSpec(name, role, (dx, dy, dz)))
        return comp

    def inventory(self) -> dict:
        """The raw inventory (schema 1 of #79).  The builder entry point returns it."""
        return self._backend.raw_inventory()

    def _register(self, *used: str) -> None:
        for n in used:
            if n in self._used:
                raise DuplicateNameError(f"{n!r} occurs twice in the document")
        self._used.update(used)
        if self._calls:
            self._calls[-1].produced.extend(used)


class Component:
    def __init__(self, kit: Kit, name: str, role: str, datum: tuple):
        self._kit, self.name, self.role, self.datum = kit, name, role, datum
        self._rank = -1  # RANK of the last feature of a part; -1 before the first
        self._features: dict[str, str] = {}  # feature name -> op, for `within`

    # ---- loops: value objects, no side effect --------------------------------------------------------------------

    def _coord(self, text, where: str):
        if text is not None:
            expr.check(text, self._kit.env.names, where)
        return text

    def rect(self, u0, u1, v0, v1) -> Loop:
        return Loop("rect", tuple(self._coord(t, f"rect.{a}") for t, a in zip((u0, u1, v0, v1), ("u0", "u1", "v0", "v1"))))

    def circle(self, cu, cv, d) -> Loop:
        expr.check(d, self._kit.env.names, "circle.d")
        return Loop("circle", (self._coord(cu, "circle.cu"), self._coord(cv, "circle.cv"), d))

    def polygon(self, points) -> Loop:
        pts = tuple(tuple(p) for p in points)
        if len(pts) < 3 or any(len(p) != 2 for p in pts):
            raise KitError(f"polygon: three or more (u, v) points, got {points!r}")
        return Loop("polygon", tuple((self._coord(u, f"polygon[{k}].u"), self._coord(v, f"polygon[{k}].v"))
                                     for k, (u, v) in enumerate(pts)))

    # ---- phases --------------------------------------------------------------------------------------------------

    def _phase(self, name: str, op: str) -> int:
        """The phase rule of 3.8; returns the new rank (the caller stores it once the feature is built)."""
        if self.role != "part":
            if op != "new":
                raise PhaseError(f"{name}: a {self.role} component holds bodies only, every feature is op='new', got {op!r}")
            return 0
        rank = RANK[op]
        if self._rank < 0 and op != "new":
            raise PhaseError(f"{name}: the first feature of part {self.name} is op='new', got {op!r}")
        if self._rank >= 0 and op == "new":
            raise PhaseError(f"{name}: part {self.name} has its body already (one body per part), got op='new'")
        if rank < self._rank:
            order = {v: k for k, v in RANK.items()}
            raise PhaseError(f"{name}: op={op!r} after op={order[self._rank]!r} in {self.name}; the order is new, join, cut, rejoin")
        return rank

    def _within(self, name: str, op: str, within) -> None:
        if op != "rejoin":
            if within is not None:
                raise KitError(f"{name}: within is only for op='rejoin', got op={op!r}")
            return
        if within is None:
            raise KitError(f"{name}: op='rejoin' needs within=<an earlier cut of the same component>")
        if within not in self._features:
            raise KitError(f"{name}: within={within!r} is not an earlier feature of component {self.name}")
        if self._features[within] != "cut":
            raise KitError(f"{name}: within={within!r} is a {self._features[within]!r}, a re-join names a cut")

    # ---- features ------------------------------------------------------------------------------------------------

    def _sketch(self, name: str, axis: str, loops, holes) -> SketchSpec:
        kit = self._kit
        if not loops or not all(isinstance(loop, Loop) for loop in loops):
            raise KitError(f"{name}: loops is a list of rect/circle/polygon values")
        holes = tuple(holes or ())
        if not all(isinstance(loop, Loop) for loop in holes):
            raise KitError(f"{name}: holes is a list of rect/circle/polygon values")
        if holes and len(loops) != 1:
            raise KitError(f"{name}: with holes, loops has exactly one outer loop, got {len(loops)}")
        iu, iv = UV_INDEX[axis]
        du, dv = self.datum[iu], self.datum[iv]
        b = _SketchBuilder(kit.env, name, du, dv)
        boxes = [_bbox(loop, b.val) for loop in loops]
        hole_boxes = [_bbox(h, b.val) for h in holes]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if _touch(boxes[i], boxes[j]):
                    raise KitError(f"{name}: loops {i} and {j} touch or overlap under the build values")
        for i, hb in enumerate(hole_boxes):
            if not _inside(hb, boxes[0]):
                raise KitError(f"{name}: hole {i} does not lie strictly inside the outer loop under the build values")
            for j in range(i + 1, len(hole_boxes)):
                if _touch(hb, hole_boxes[j]):
                    raise KitError(f"{name}: holes {i} and {j} touch or overlap under the build values")
        for i, loop in enumerate(list(loops) + list(holes)):
            b.add(i, loop)
        return SketchSpec(
            name=names.derived(name, "Sk"), component=self.name, on=f"origin:{PLANE_OF[axis]}", datum=(du, dv),
            loops=tuple(loops), holes=holes, points=tuple(b.points), lines=tuple(b.lines), circles=tuple(b.circles),
            constraints=tuple(b.constraints), dims=tuple(b.dims),
            profiles=1 + len(holes) if holes else len(loops), rule="ring" if holes else "all")

    def extrude(self, name, *, axis, loops, start, end, op, holes=None, within=None):
        """One sketch and one extrude feature (3.6, 3.7).  Returns the feature's name."""
        kit = self._kit
        if axis not in AXES:
            raise KitError(f"{name}: axis is one of {AXES}, got {axis!r}")
        if op not in OPS:
            raise KitError(f"{name}: op is one of {OPS}, got {op!r}")
        names.check(name, kit._owners, op)
        rank = self._phase(name, op)
        self._within(name, op, within)
        for label, text in (("start", start), ("end", end)):
            if text is not None:
                expr.check(text, kit.env.names, f"{name}.{label}")
        distance = expr.sub(end, start)
        if distance is None:
            raise KitError(f"{name}: start and end are both None")
        sketch = self._sketch(name, axis, loops, holes)
        kit._register(name, sketch.name)
        plane = PLANE_OF[axis]
        sign = PLANE_NORMAL[plane]
        start_offset = None if start is None else (start if sign == 1 else expr.neg(start))
        feature = ExtrudeSpec(name=name, component=self.name, sketch=sketch.name, start_offset=start_offset,
                              distance=distance, direction="positive" if sign == 1 else "negative", op=op, within=within)
        kit._backend.execute(sketch)
        kit._backend.execute(feature)
        self._rank = max(self._rank, rank)
        self._features[name] = op
        return name

    # ---- bookkeeping for shared builders ----------------------------------------------------------------------------

    @contextlib.contextmanager
    def shared_call(self, builder_id, arguments, placement):
        """The context manager behind ``@shared`` (3.10).  Records the builder id, the arguments, which of them are
        placement, the names produced directly inside the block (an inner call gets its own) and the parent call
        (its builder id) when entered inside another shared_call."""
        kit = self._kit
        if not isinstance(builder_id, str) or not builder_id:
            raise KitError(f"shared_call: builder_id is a non-empty str, got {builder_id!r}")
        arguments, placement = dict(arguments), tuple(placement)
        for p in placement:
            if p not in arguments:
                raise KitError(f"shared_call {builder_id}: placement argument {p!r} is not among the arguments")
        call = SharedCall(builder_id, arguments, placement, [], kit._calls[-1].builder_id if kit._calls else None)
        kit._backend.execute(call)
        kit._calls.append(call)
        try:
            yield call
        finally:
            kit._calls.pop()
