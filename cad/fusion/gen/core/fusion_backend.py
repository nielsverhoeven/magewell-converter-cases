"""The Fusion backend of the modelling kit (issue #81, plan sections 2.6, 3.11 and 3.14; milestone K5a).

``FusionBackend.execute(spec)`` turns one spec of ``spec.py`` into real Autodesk Fusion API calls.  It executes
what the facade decided and takes no decision: every dimension is an expression of parameter names, written with
``adsk.core.ValueInput.createByString`` or ``dim.parameter.expression`` and always through ``expr.fusion`` (which
is ``cad.params.emit_fusion``).  ``createByReal`` is never called (it is centimetres and radians).

The one place where this module handles a number is ``_Sketcher.model_point``: it seeds sketch geometry with the
value of the expressions (mm, times 0.1 for Fusion's centimetres), and a driving dimension then owns the geometry.

This file is written offline against the installed API stubs and is **UNVERIFIED until a live run** (risk R81.1,
probes G1 to G18 of plan section 10).  Stub evidence is quoted as ``api:N`` (``adsk/fusion.py``) and ``core:N``
(``adsk/core.py``) line numbers of the stub of the installed version; the list sits in the pull request body and in
``tests/fixtures/adsk_members.json``, which the static test checks against this file and, where the stubs are
installed, against the stubs.

``adsk`` is imported here and in ``probes.py``, ``enhance_fusion.py`` and the runtime only (verdict A8 rule 1).  This
module is imported by ``Kit.__init__`` behind ``ctx.backend == "fusion"`` and by nothing else in ``gen``.
"""
from __future__ import annotations

import adsk.core
import adsk.fusion

from . import expr, facade
from . import spec as specs
from .names import KitError
from .record import RecordingBackend

MM_TO_CM = 0.1  # Fusion's database unit is the centimetre; the only conversion of a number in this module
TEXT_OFFSET_CM = 0.5  # where a dimension's text sits beside the geometry; it carries no meaning (plan 3.6)
TOL = 1e-6

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
# origin plane name -> (its normal axis, its in-plane axes (u, v) in the order of facade.UV_INDEX)
PLANES = {"XY": ("Z", ("X", "Y")), "XZ": ("Y", ("X", "Z")), "YZ": ("X", ("Y", "Z"))}


class BackendError(KitError):
    """Fusion did not do what the spec said (a failed assertion of plan 3.11) or the spec cannot be executed."""


# ---- small helpers: every adsk call sits in a lambda or a method so the static test sees every member name ------------------


def _origin_plane(comp, name):
    """The origin construction plane (api:89156, 89160, 89164)."""
    if name == "XY":
        return comp.xYConstructionPlane
    if name == "XZ":
        return comp.xZConstructionPlane
    return comp.yZConstructionPlane


def _origin_axis(comp, axis):
    """The origin construction axis (api:89168, 89172, 89176)."""
    if axis == "X":
        return comp.xConstructionAxis
    if axis == "Y":
        return comp.yConstructionAxis
    return comp.zConstructionAxis


def _operation(op):
    """FeatureOperations (api:2296-2299); a re-join is a join (plan 3.11)."""
    ops = adsk.fusion.FeatureOperations
    return {"new": ops.NewBodyFeatureOperation, "join": ops.JoinFeatureOperation, "cut": ops.CutFeatureOperation,
            "rejoin": ops.JoinFeatureOperation}[op]


def _value(text):
    """A ValueInput from an expression (core:26143); never createByReal."""
    return adsk.core.ValueInput.createByString(expr.fusion(text))


def _axis_of(vector, where):
    """``(letter, sign)`` of a vector that must be a unit vector along a model axis (Vector3D.x, y, z: core:26688-26704)."""
    comps = [vector.x, vector.y, vector.z]
    i = max(range(3), key=lambda k: abs(comps[k]))
    others = [abs(c) for k, c in enumerate(comps) if k != i]
    if abs(abs(comps[i]) - 1.0) > TOL or any(o > TOL for o in others):
        raise BackendError(f"{where}: the vector {comps} is not along a model axis")
    return "XYZ"[i], 1 if comps[i] > 0 else -1


class _Made:
    """What the backend keeps of a sketch it built: the sketch, its spec, its sketch points by spec name, and the
    sketch text of a text sketch."""

    def __init__(self, sketch, sketch_spec, points):
        self.sketch, self.spec, self.points, self.text = sketch, sketch_spec, points, None


class _Sketcher:
    """The steps of plan 3.11 'Sketch spec' for one sketch."""

    def __init__(self, backend, s):
        self.b, self.s = backend, s
        self.comp = backend.component(s.component)
        self.plane_entity, self.plane = backend.plane_for(self.comp, s.on)
        self.normal_axis, (self.u_axis, self.v_axis) = PLANES[self.plane]
        self.uv: dict[str, tuple[float, float]] = {}  # spec point name -> in-plane model coordinates (u, v) in cm
        self.radius: dict[str, float] = {}  # spec circle name -> radius in cm

    # -- the frame of the sketch -------------------------------------------------------------------------------------

    def read_frame(self, sk):
        """Step 3: the sketch axes from ``xDirection`` and ``yDirection`` (api:68623, 68627), checked against
        ``facade.PLANE_NORMAL`` (the placeholder that probe G1 fills in)."""
        where = f"sketch {self.s.name}"
        self.h_axis, _ = _axis_of(sk.xDirection, f"{where}: xDirection")
        _axis_of(sk.yDirection, f"{where}: yDirection")  # along a model axis too
        cross = sk.xDirection.crossProduct(sk.yDirection)  # core:26597
        want = facade.PLANE_NORMAL[self.plane]
        got = _axis_of(cross, f"{where}: normal")
        if got != (self.normal_axis, want):
            raise BackendError(f"{where}: the sketch normal is {got[1]:+d} {got[0]}, facade.PLANE_NORMAL[{self.plane!r}] "
                               f"says {want:+d} {self.normal_axis}; fill facade.PLANE_NORMAL from probe G1")
        # the facade takes the sketch origin O for the model origin of the plane
        origin = sk.origin  # api:68619
        model = [origin.x, origin.y, origin.z]
        self.origin_model = model
        for axis in (self.u_axis, self.v_axis):
            if abs(model[AXIS_INDEX[axis]]) > TOL:
                raise BackendError(f"{where}: the sketch origin is not the model origin in {axis} ({model})")

    def is_horizontal(self, ax):
        """Whether the in-plane model axis behind ``u`` or ``v`` is the sketch's horizontal direction."""
        return (self.u_axis if ax == "u" else self.v_axis) == self.h_axis

    # -- numbers: the one place ---------------------------------------------------------------------------------------

    def cm(self, text):
        return 0.0 if text is None else self.b.env.value(text) * MM_TO_CM

    def model_point(self, sk, u, v):
        """A sketch-space point for in-plane model coordinates (u, v) in cm (api:68552); z of the result is dropped."""
        coords = list(self.origin_model)
        coords[AXIS_INDEX[self.u_axis]] = u
        coords[AXIS_INDEX[self.v_axis]] = v
        p = sk.modelToSketchSpace(adsk.core.Point3D.create(*coords))
        return adsk.core.Point3D.create(p.x, p.y, 0.0)

    def seed(self):
        """Where every named point of the spec lies, from the loops under the build values."""
        s = self.s
        self.uv["O"] = (0.0, 0.0)
        du, dv = s.datum
        self.uv["P0"] = (self.cm(du), self.cm(dv))
        for i, loop in enumerate(tuple(s.loops) + tuple(s.holes)):
            if loop.kind == "rect":
                u0, u1, v0, v1 = (self.cm(a) for a in loop.args)
                for k, pt in enumerate(((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                    self.uv[f"p{i}_{k}"] = pt
            elif loop.kind == "circle":
                cu, cv, d = loop.args
                self.uv[f"c{i}"] = (self.cm(cu), self.cm(cv))
                self.radius[f"k{i}"] = self.cm(d) / 2
            else:
                for k, (pu, pv) in enumerate(loop.args):
                    self.uv[f"q{i}_{k}"] = (self.cm(pu), self.cm(pv))

    # -- build --------------------------------------------------------------------------------------------------------

    def text_point(self, sk, name_a, name_b, ax):
        """A point for the dimension text beside the geometry (it carries no meaning)."""
        (ua, va), (ub, vb) = self.uv[name_a], self.uv[name_b]
        mid_u, mid_v = (ua + ub) / 2, (va + vb) / 2
        if ax == "u":
            return self.model_point(sk, mid_u, max(va, vb) + TEXT_OFFSET_CM)
        return self.model_point(sk, max(ua, ub) + TEXT_OFFSET_CM, mid_v)

    def build(self):
        s = self.s
        sk = self.comp.sketches.add(self.plane_entity)  # api:71361
        self.b.name(sk, s.name, "sketch")  # api:68414
        sk.isComputeDeferred = True  # api:68668; only while creating
        self.read_frame(sk)
        self.seed()
        pts, lines, circles = {"O": sk.originPoint}, {}, {}  # api:68797

        def point(name):
            return self.model_point(sk, *self.uv[name])

        if "P0" in s.points:
            pts["P0"] = sk.sketchPoints.add(point("P0"))  # api:72472
        curves = sk.sketchCurves  # api:68426
        for name, a, b in s.lines:
            line = curves.sketchLines.addByTwoPoints(pts[a] if a in pts else point(a),
                                                     pts[b] if b in pts else point(b))  # api:72162
            pts.setdefault(a, line.startSketchPoint)  # api:151696
            pts.setdefault(b, line.endSketchPoint)  # api:151703
            lines[name] = line
            if s.rule == "text":
                line.isConstruction = True  # api:151761: the frame of a text is construction geometry
        for name, centre in s.circles:
            circle = curves.sketchCircles.addByCenterRadius(point(centre), self.radius[name])  # api:69702, cm
            pts[centre] = circle.centerSketchPoint  # api:149088
            circles[name] = circle
        missing = [p for p in s.points if p not in pts]
        if missing:
            raise BackendError(f"sketch {s.name}: the spec names points that no line or circle made: {missing}")
        self.constrain(sk, pts, lines)
        self.dimension(sk, pts, circles)
        sk.isComputeDeferred = False
        self.check(sk)
        return _Made(sk, s, pts)

    def constrain(self, sk, pts, lines):
        cons = sk.geometricConstraints  # api:68443
        for c in self.s.constraints:
            if c.kind in ("parallel_u", "parallel_v"):
                if self.is_horizontal(c.kind[-1]):
                    cons.addHorizontal(lines[c.a])  # api:39458
                else:
                    cons.addVertical(lines[c.a])  # api:39475
            elif c.kind in ("same_u", "same_v"):
                # the two points share their u (or v) coordinate: on the sketch's horizontal axis that is the same x,
                # a vertical alignment of the points
                if self.is_horizontal(c.kind[-1]):
                    cons.addVerticalPoints(pts[c.a], pts[c.b])  # api:39483
                else:
                    cons.addHorizontalPoints(pts[c.a], pts[c.b])  # api:39466
            else:
                raise BackendError(f"sketch {self.s.name}: unknown constraint kind {c.kind!r}")

    def dimension(self, sk, pts, circles):
        dims = sk.sketchDimensions  # api:68435
        orientations = adsk.fusion.DimensionOrientations  # api:2058-2072
        for d in self.s.dims:
            if d.kind == "distance":
                orientation = (orientations.HorizontalDimensionOrientation if self.is_horizontal(d.axis)
                               else orientations.VerticalDimensionOrientation)
                dim = dims.addDistanceDimension(pts[d.a], pts[d.b], orientation,
                                                self.text_point(sk, d.a, d.b, d.axis))  # api:70547
            elif d.kind == "diameter":
                cu, cv = self.uv[self.centre_of(d.a)]
                r = self.radius[d.a]
                dim = dims.addDiameterDimension(circles[d.a], self.model_point(sk, cu + r + TEXT_OFFSET_CM, cv + r))  # api:70593
            elif d.kind == "text_height":
                continue  # the height of a text is bound by SketchTexts.createInput3 when the text is made
            else:
                raise BackendError(f"sketch {self.s.name}: unknown dimension kind {d.kind!r}")
            dim.parameter.expression = expr.fusion(d.text)  # api:70263, api:113941

    def centre_of(self, circle_name):
        for name, centre in self.s.circles:
            if name == circle_name:
                return centre
        raise BackendError(f"sketch {self.s.name}: no circle {circle_name!r}")

    def check(self, sk):
        """Step 6: fully constrained, healthy, the expected number of profiles (api:68804, 68828, 68712, 60894)."""
        s = self.s
        constrained, health, count = sk.isFullyConstrained, sk.healthState, sk.profiles.count
        if (not constrained or health != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
                or count != s.profiles):
            raise BackendError(f"sketch {s.name}: fully constrained {constrained}, health {health} "
                               f"({sk.errorOrWarningMessage}), profiles {count} (expected {s.profiles})")  # api:68832


# ---- the backend ------------------------------------------------------------------------------------------------------


class FusionBackend:
    """``FusionBackend(ctx)`` is how the facade reaches it (``Kit.__init__``).  ``ctx.design`` is the open
    ``adsk.fusion.Design`` (contract C2 of #79), ``ctx.registry`` and ``ctx.values`` are the same the facade uses."""

    def __init__(self, ctx):
        design = getattr(ctx, "design", None)
        if design is None:
            raise BackendError("ctx.design is None: the Fusion backend needs the open Fusion design")
        self.ctx = ctx
        self.design = design
        self.root = design.rootComponent  # api:103187
        self.env = expr.Env(ctx.registry, ctx.values)
        self.recorded = RecordingBackend(getattr(ctx, "document", ""))  # the raw inventory and the build record
        self._components: dict = {}
        self._roles: dict[str, str] = {}
        self._planes: dict[str, tuple] = {}  # construction plane name -> (plane, origin plane name)
        self._sketches: dict[str, _Made] = {}

    # -- what Kit.inventory() asks for ----------------------------------------------------------------------------------

    def raw_inventory(self) -> dict:
        return self.recorded.raw_inventory()

    def build_record(self, api: int = 1) -> dict:
        return self.recorded.build_record(api)

    # -- lookups ----------------------------------------------------------------------------------------------------------

    def component(self, name):
        try:
            return self._components[name]
        except KeyError:
            raise BackendError(f"component {name!r} was not created") from None

    def plane_for(self, comp, on):
        """``(construction plane, origin plane name)`` for ``origin:XY`` or ``plane:<name>``."""
        kind, _, name = on.partition(":")
        if kind == "origin" and name in PLANES:
            return _origin_plane(comp, name), name
        if kind == "plane" and name in self._planes:
            return self._planes[name]
        raise BackendError(f"a sketch on {on!r}: no such plane")

    def name(self, obj, want, what):
        """Give an object its name and read it back (probe G17: Fusion may rename a duplicate)."""
        obj.name = want  # api:68414, 27157, 35914, 16676, 89679
        if obj.name != want:
            raise BackendError(f"{what} {want!r}: Fusion named it {obj.name!r}")

    # -- dispatch ---------------------------------------------------------------------------------------------------------

    def execute(self, item) -> None:
        if isinstance(item, specs.SharedCall):
            self.recorded.execute(item)  # a shared call has no effect in Fusion: it is bookkeeping
            return
        if item.phase != "build":
            raise BackendError(f"{type(item).__name__} {getattr(item, 'name', '')!r} has phase {item.phase!r}; the "
                               "executor of the enhancement phase is enhance_fusion.py of #85")
        handler = {specs.ComponentSpec: self._component, specs.SketchSpec: self._sketch, specs.PlaneSpec: self._plane,
                   specs.ExtrudeSpec: self._extrude, specs.LoftSpec: self._loft, specs.PatternSpec: self._pattern,
                   specs.TextSpec: self._text}.get(type(item))
        if handler is None:
            raise BackendError(f"the Fusion backend has no executor for {type(item).__name__}")
        handler(item)
        self.recorded.execute(item)

    # -- component, plane, sketch -----------------------------------------------------------------------------------------

    def _component(self, s):
        occurrence = self.root.occurrences.addNewComponent(adsk.core.Matrix3D.create())  # api:53546, core:16525
        comp = occurrence.component  # api:52679
        self.name(comp, s.name, "component")
        occurrence.isGroundToParent = True  # api:53064
        self._components[s.name] = comp
        self._roles[s.name] = s.role

    def _plane(self, s):
        comp = self.component(s.component)
        kind, _, base = s.base.partition(":")
        if kind != "origin" or base not in PLANES or s.offset is None:
            raise BackendError(f"plane {s.name}: a plane is an offset from an origin plane, got base {s.base!r}, "
                               f"offset {s.offset!r}")
        inp = comp.constructionPlanes.createInput()  # api:27966
        inp.setByOffset(_origin_plane(comp, base), _value(s.offset))  # api:27575
        plane = comp.constructionPlanes.add(inp)  # api:27976
        self.name(plane, s.name, "construction plane")
        self._planes[s.name] = (plane, base)

    def _sketch(self, s):
        self._sketches[s.name] = _Sketcher(self, s).build()

    # -- features ---------------------------------------------------------------------------------------------------------

    def _made(self, name):
        try:
            return self._sketches[name]
        except KeyError:
            raise BackendError(f"sketch {name!r} was not built") from None

    def _profiles(self, made):
        """Step 1 of the extrude spec: every profile, or for a ring the one profile with ``1 + holes`` loops."""
        sk, s = made.sketch, made.spec
        if s.rule == "text":
            return made.text
        profiles = sk.profiles  # api:68712
        if s.rule == "ring":
            want = 1 + len(s.holes)
            ring = [profiles.item(i) for i in range(profiles.count) if profiles.item(i).profileLoops.count == want]  # api:60885, 60266, 60798
            if len(ring) != 1:
                raise BackendError(f"sketch {s.name}: {len(ring)} profiles have {want} loops, expected exactly one")
            return ring[0]
        collection = adsk.core.ObjectCollection.create()  # core:17678
        for i in range(profiles.count):
            collection.add(profiles.item(i))  # core:17725
        return collection

    def _only_body(self, comp, what):
        bodies = comp.bRepBodies  # api:89743
        if bodies.count != 1:  # api:16528
            raise BackendError(f"{what}: component {comp.name!r} holds {bodies.count} bodies, a cut or re-join needs exactly one")
        return bodies.item(0)  # api:16512

    def _healthy(self, feature, name):
        state = feature.healthState  # api:36024
        if state != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:  # api:2268
            raise BackendError(f"feature {name}: health {state}: {feature.errorOrWarningMessage}")  # api:36028

    def _finish(self, feature, name, comp_name, op):
        """Name, health, and in a part the one-body rule (plan 3.11 extrude steps 6 and 7)."""
        self.name(feature, name, "feature")
        if op == "new":
            body = feature.bodies.item(0)  # api:35991, 16512
            self.name(body, comp_name if self._roles[comp_name] == "part" else name, "body")  # api:16676
        self._healthy(feature, name)
        if self._roles[comp_name] == "part" and self.component(comp_name).bRepBodies.count != 1:
            raise BackendError(f"feature {name}: part {comp_name} holds {self.component(comp_name).bRepBodies.count} bodies")

    def _extrude_of(self, name, comp_name, profile, op, start_offset, distance, direction):
        comp = self.component(comp_name)
        features = comp.features.extrudeFeatures  # api:89097, 36275
        inp = features.createInput(profile, _operation(op))  # api:35553
        if start_offset is not None:
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(_value(start_offset))  # api:35235, 116239
        extents = adsk.fusion.ExtentDirections  # api:2216-2217
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(_value(distance)),
                             extents.PositiveExtentDirection if direction == "positive"
                             else extents.NegativeExtentDirection)  # api:104422, 35245
        if op in ("cut", "rejoin"):
            inp.participantBodies = [self._only_body(comp, name)]  # api:35336
        self._finish(features.add(inp), name, comp_name, op)  # api:35568

    def _extrude(self, s):
        self._extrude_of(s.name, s.component, self._profiles(self._made(s.sketch)), s.op, s.start_offset, s.distance,
                         s.direction)

    def _loft(self, s):
        comp = self.component(s.component)
        features = comp.features.loftFeatures  # api:36547
        inp = features.createInput(_operation(s.op))  # api:46097
        for sketch_name in s.sketches:
            sk = self._made(sketch_name).sketch
            inp.loftSections.add(sk.profiles.item(0))  # api:45825, 46409, 60885
        if s.op == "cut":
            inp.participantBodies = [self._only_body(comp, s.name)]  # api:45903
        self._finish(features.add(inp), s.name, s.component, s.op)  # api:46107

    def _pattern(self, s):
        comp = self.component(s.component)
        seed = comp.features.itemByName(s.seed)  # api:36564
        if seed is None:
            raise BackendError(f"pattern {s.name}: no feature named {s.seed!r} to repeat")
        entities = adsk.core.ObjectCollection.create()  # core:17678
        entities.add(seed)  # core:17725
        inp = comp.features.rectangularPatternFeatures.createInput(
            entities, _origin_axis(comp, s.axis), _value(s.count), _value(s.pitch),
            adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)  # api:36338, 61517, 3734
        if s.axis2 is not None:
            inp.setDirectionTwo(_origin_axis(comp, s.axis2), _value(s.count2), _value(s.pitch2))  # api:61237
        feature = comp.features.rectangularPatternFeatures.add(inp)  # api:61540
        self.name(feature, s.name, "feature")
        self._healthy(feature, s.name)

    def _text(self, s):
        made = self._made(s.sketch)
        sk = made.sketch
        quoted = "'" + s.string + "'"  # Fusion's quoting of a plain string (the facade refuses a single quote)
        ti = sk.sketchTexts.createInput3(quoted, _value(s.height))  # api:68789, 72981; the height is an expression
        halign, valign = adsk.core.HorizontalAlignments, adsk.core.VerticalAlignments  # core:1195-1197, 2425-2427
        ti.setAsMultiLine(made.points["p0_0"], made.points["p0_2"],
                          {"left": halign.LeftHorizontalAlignment, "center": halign.CenterHorizontalAlignment,
                           "right": halign.RightHorizontalAlignment}[s.halign],
                          {"bottom": valign.BottomVerticalAlignment, "middle": valign.MiddleVerticalAlignment,
                           "top": valign.TopVerticalAlignment}[s.valign], 0)  # api:72747: the two corners of the frame
        ti.fontName = s.font  # api:72670
        if s.style == "bold":
            ti.textStyle = adsk.fusion.TextStyles.TextStyleBold  # api:72703, 5204
        # the text reads unmirrored from plus axis: flipped when plus axis points against the sketch normal
        ti.isHorizontalFlip = s.direction == "negative"  # api:72714
        made.text = sk.sketchTexts.add(ti)  # api:72954
        if made.text is None:
            raise BackendError(f"text {s.name}: Fusion did not create the sketch text")
        self._extrude_of(s.name, s.component, made.text, s.op, s.start_offset, s.distance, s.direction)
