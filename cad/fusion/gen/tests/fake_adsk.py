"""A small fake of the parts of ``adsk.core`` and ``adsk.fusion`` that ``fusion_backend.py`` calls (plan K5a step 3).

It lets the tests run the pure translation logic (spec to call plan) without Fusion.  It is deliberately not a
model of Fusion: a sketch is a list of points, lines, circles, constraints and dimensions, and a feature is a record
of the input it was given.  ``installed()`` puts the fakes into ``sys.modules`` as ``adsk``, ``adsk.core`` and
``adsk.fusion`` for the length of a ``with`` block and removes them (and any module that imported them) afterwards.

The behaviour that only a live run can show (plan section 10) is a knob here, not a guess: ``Design.frames`` is how a
sketch lies on each origin plane (probe G1), ``unconstrained``, ``profile_loops``, ``feature_health`` and ``rename`` make
Fusion answer unfavourably.  Every adsk call is also appended to ``Design.log`` as a plain tuple.
"""
from __future__ import annotations

import contextlib
import sys
import types

# How a sketch lies on each origin plane: (x direction, y direction) in model space.  With these, the sketch normal is
# +Z on XY, -Y on XZ and +X on YZ (x cross y); tests set facade.PLANE_NORMAL to match.
FRAMES = {"XY": ((1, 0, 0), (0, 1, 0)), "XZ": ((1, 0, 0), (0, 0, 1)), "YZ": ((0, 1, 0), (0, 0, 1))}
NORMALS = {"XY": 1, "XZ": -1, "YZ": 1}


def _enum(name, *members):
    return type(name, (), {m: f"{name}.{m}" for m in members})


FeatureOperations = _enum("FeatureOperations", "NewBodyFeatureOperation", "JoinFeatureOperation", "CutFeatureOperation")
ExtentDirections = _enum("ExtentDirections", "PositiveExtentDirection", "NegativeExtentDirection")
DimensionOrientations = _enum("DimensionOrientations", "HorizontalDimensionOrientation", "VerticalDimensionOrientation",
                              "AlignedDimensionOrientation")
FeatureHealthStates = _enum("FeatureHealthStates", "HealthyFeatureHealthState", "ErrorFeatureHealthState")
PatternDistanceType = _enum("PatternDistanceType", "SpacingPatternDistanceType")
TextStyles = _enum("TextStyles", "TextStyleBold")
HorizontalAlignments = _enum("HorizontalAlignments", "LeftHorizontalAlignment", "CenterHorizontalAlignment",
                             "RightHorizontalAlignment")
VerticalAlignments = _enum("VerticalAlignments", "TopVerticalAlignment", "MiddleVerticalAlignment", "BottomVerticalAlignment")

HEALTHY = FeatureHealthStates.HealthyFeatureHealthState
ERROR = FeatureHealthStates.ErrorFeatureHealthState


# ---- adsk.core ------------------------------------------------------------------------------------------------------------


class Vector3D:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def crossProduct(self, o):
        return Vector3D(self.y * o.z - self.z * o.y, self.z * o.x - self.x * o.z, self.x * o.y - self.y * o.x)

    def dot(self, p):
        return self.x * p.x + self.y * p.y + self.z * p.z


class Point3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z

    @staticmethod
    def create(x=0.0, y=0.0, z=0.0):
        return Point3D(x, y, z)


class Matrix3D:
    @staticmethod
    def create():
        return Matrix3D()


class ValueInput:
    def __init__(self, text):
        self.text = text

    @staticmethod
    def createByString(text):
        return ValueInput(text)


class ObjectCollection:
    def __init__(self):
        self.items = []

    @staticmethod
    def create():
        return ObjectCollection()

    def add(self, item):
        self.items.append(item)
        return True


# ---- adsk.fusion ----------------------------------------------------------------------------------------------------------


class _Named:
    """``name`` that Fusion may change on the way in (``Design.rename``, probe G17)."""

    def __init__(self, design, name=""):
        self._design, self._name = design, name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = self._design.rename.get(value, value)


class Parameter:
    expression = None


class Dimension:
    def __init__(self, kind, orientation, a, b):
        self.kind, self.orientation, self.a, self.b, self.parameter = kind, orientation, a, b, Parameter()


class SketchPoint:
    def __init__(self, x, y):
        self.x, self.y = x, y

    @property
    def at(self):
        return (round(self.x, 9), round(self.y, 9))


class SketchLine:
    def __init__(self, start, end):
        self.startSketchPoint, self.endSketchPoint, self.isConstruction = start, end, False


class SketchCircle:
    def __init__(self, centre, radius):
        self.centerSketchPoint, self.radius = centre, radius


class SketchText:
    def __init__(self, text_input):
        self.input = text_input


class TextInput:
    def __init__(self, expression, height):
        self.expression, self.height = expression, height
        self.multi_line = None
        self.fontName = None
        self.textStyle = None
        self.isHorizontalFlip = False

    def setAsMultiLine(self, corner, diagonal, horizontal, vertical, spacing):
        self.multi_line = (corner, diagonal, horizontal, vertical, spacing)
        return True


class _Collection:
    def __init__(self, items):
        self.items = list(items)

    @property
    def count(self):
        return len(self.items)

    def item(self, i):
        return self.items[i]


class Profile:
    def __init__(self, loops):
        self.profileLoops = _Collection([None] * loops)


class ConstructionPlane(_Named):
    def __init__(self, design, origin_name=None, offset=None):
        super().__init__(design)
        self.origin_name, self.offset = origin_name, offset


class Sketch(_Named):
    def __init__(self, design, plane):
        super().__init__(design)
        self.plane = plane
        self.design = design
        x, y = design.frames[plane.origin_name]
        self._x, self._y = Vector3D(*x), Vector3D(*y)
        self.deferred_history = []
        self._deferred = False
        self.origin = Point3D(*design.sketch_origin)
        self.originPoint = SketchPoint(0.0, 0.0)
        self.points, self.lines, self.circles = [], [], []
        self.constraints, self.dimensions, self.texts = [], [], []
        self.sketchPoints = types.SimpleNamespace(add=self._add_point)
        self.sketchCurves = types.SimpleNamespace(
            sketchLines=types.SimpleNamespace(addByTwoPoints=self._add_line),
            sketchCircles=types.SimpleNamespace(addByCenterRadius=self._add_circle))
        self.geometricConstraints = types.SimpleNamespace(
            addHorizontal=lambda ln: self._con("horizontal", ln), addVertical=lambda ln: self._con("vertical", ln),
            addHorizontalPoints=lambda a, b: self._con("horizontalPoints", a, b),
            addVerticalPoints=lambda a, b: self._con("verticalPoints", a, b))
        self.sketchDimensions = types.SimpleNamespace(addDistanceDimension=self._distance, addDiameterDimension=self._diameter)
        self.sketchTexts = types.SimpleNamespace(createInput3=self._text_input, add=self._add_text)

    @property
    def isComputeDeferred(self):
        return self._deferred

    @isComputeDeferred.setter
    def isComputeDeferred(self, value):
        self._deferred = value
        self.deferred_history.append(value)

    # -- frame --
    @property
    def xDirection(self):
        return self._x

    @property
    def yDirection(self):
        return self._y

    def modelToSketchSpace(self, p):
        return Point3D(self._x.dot(p), self._y.dot(p), self._x.crossProduct(self._y).dot(p))

    # -- geometry --
    def _point(self, p):
        return p if isinstance(p, SketchPoint) else self._new_point(p)

    def _new_point(self, p):
        point = SketchPoint(p.x, p.y)
        self.points.append(point)
        return point

    def _add_point(self, p):
        self.design.log.append(("sketchPoints.add", self.name))
        return self._new_point(p)

    def _add_line(self, a, b):
        line = SketchLine(self._point(a), self._point(b))
        self.lines.append(line)
        self.design.log.append(("addByTwoPoints", self.name))
        return line

    def _add_circle(self, centre, radius):
        circle = SketchCircle(self._point(centre), radius)
        self.circles.append(circle)
        self.design.log.append(("addByCenterRadius", self.name))
        return circle

    def _con(self, kind, *args):
        if kind in ("horizontal", "vertical"):
            ln = args[0]
            self.constraints.append((kind, ln.startSketchPoint.at, ln.endSketchPoint.at))
        else:
            self.constraints.append((kind, args[0].at, args[1].at))

    def _distance(self, a, b, orientation, text_point):
        dim = Dimension("distance", orientation, a.at, b.at)
        self.dimensions.append(dim)
        return dim

    def _diameter(self, circle, text_point):
        dim = Dimension("diameter", None, circle.centerSketchPoint.at, None)
        dim.radius = circle.radius
        self.dimensions.append(dim)
        return dim

    def _text_input(self, expression, height):
        return TextInput(expression, height)

    def _add_text(self, text_input):
        text = SketchText(text_input)
        self.texts.append(text)
        return text

    # -- state asked for after the sketch is built --
    @property
    def isFullyConstrained(self):
        return self.name not in self.design.unconstrained

    @property
    def healthState(self):
        return self.design.sketch_health.get(self.name, HEALTHY)

    errorOrWarningMessage = "fake sketch message"

    @property
    def profiles(self):
        loops = self.design.profile_loops.get(self.name)
        if loops is None:
            solid = [ln for ln in self.lines if not ln.isConstruction]  # a construction line bounds no profile
            loops = [1] * (len(solid) // 4 + len(self.circles))
        return _Collection(Profile(n) for n in loops)


class Body(_Named):
    pass


class Feature(_Named):
    errorOrWarningMessage = "fake feature message"

    def __init__(self, comp, kind, inp, bodies=()):
        super().__init__(comp.design)
        self.comp, self.kind, self.input, self.bodies = comp, kind, inp, _Collection(bodies)

    @property
    def healthState(self):
        return self.design_health()

    def design_health(self):
        return self.comp.design.feature_health.get(self.name, HEALTHY)


class _Input:
    """Whatever ``createInput`` hands out: it keeps what the backend sets on it."""

    def __init__(self, **fields):
        self.__dict__.update(fields)
        self.startExtent = None
        self.participantBodies = None
        self.loftSections = _Sections()

    def setOneSideExtent(self, extent, direction):
        self.extent, self.direction = extent, direction
        return True

    def setByOffset(self, plane, value):
        self.plane, self.value = plane, value
        return True

    def setDirectionTwo(self, axis, count, pitch):
        self.direction_two = (axis, count, pitch)
        return True


class _Sections:
    def __init__(self):
        self.items = []

    def add(self, profile):
        self.items.append(profile)


class Component(_Named):
    def __init__(self, design):
        super().__init__(design)
        self.design = design
        self.bodies = []
        self.timeline = []
        self.planes = {n: ConstructionPlane(design, n) for n in FRAMES}
        self.axes = {n: types.SimpleNamespace(axis=n) for n in "XYZ"}
        self.xYConstructionPlane, self.xZConstructionPlane = self.planes["XY"], self.planes["XZ"]
        self.yZConstructionPlane = self.planes["YZ"]
        self.xConstructionAxis, self.yConstructionAxis, self.zConstructionAxis = (self.axes[n] for n in "XYZ")
        self.sketches = types.SimpleNamespace(add=self._add_sketch)
        self.constructionPlanes = types.SimpleNamespace(createInput=lambda: _Input(), add=self._add_plane)
        self.features = types.SimpleNamespace(
            extrudeFeatures=types.SimpleNamespace(createInput=self._extrude_input, add=self._add_feature("extrude")),
            loftFeatures=types.SimpleNamespace(createInput=lambda op: _Input(operation=op), add=self._add_feature("loft")),
            rectangularPatternFeatures=types.SimpleNamespace(
                createInput=self._pattern_input, add=self._add_feature("pattern")),
            itemByName=self._item_by_name)

    @property
    def bRepBodies(self):
        return _Collection(self.bodies)

    def _add_sketch(self, plane):
        sketch = Sketch(self.design, plane)
        self.design.sketches.append(sketch)
        self.design.log.append(("sketches.add", plane.origin_name if plane.offset is None else f"{plane.origin_name}+{plane.offset}"))
        return sketch

    def _add_plane(self, inp):
        plane = ConstructionPlane(self.design, inp.plane.origin_name, inp.value.text)
        self.design.log.append(("constructionPlanes.add", inp.plane.origin_name, inp.value.text))
        self.design.planes.append(plane)
        return plane

    def _extrude_input(self, profile, operation):
        return _Input(profile=profile, operation=operation)

    def _pattern_input(self, entities, axis, count, pitch, distance_type):
        return _Input(entities=entities, axis=axis, count=count, pitch=pitch, distance_type=distance_type)

    def _add_feature(self, kind):
        def add(inp):
            bodies = []
            if kind != "pattern" and inp.operation == FeatureOperations.NewBodyFeatureOperation:
                body = Body(self.design)
                self.bodies.append(body)
                bodies = [body]
            feature = Feature(self, kind, inp, bodies)
            self.timeline.append(feature)
            self.design.features.append(feature)
            self.design.log.append((f"{kind}.add", inp.operation if kind != "pattern" else None))
            return feature
        return add

    def _item_by_name(self, name):
        return next((f for f in self.timeline if f.name == name), None)


class Occurrence:
    def __init__(self, component):
        self.component, self.isGroundToParent = component, False


class Design:
    def __init__(self):
        self.log: list[tuple] = []
        self.frames = dict(FRAMES)
        self.rename: dict[str, str] = {}
        self.unconstrained: set[str] = set()
        self.profile_loops: dict[str, list[int]] = {}
        self.feature_health: dict[str, str] = {}
        self.sketch_health: dict[str, str] = {}
        self.sketch_origin = (0.0, 0.0, 0.0)
        self.sketches, self.features, self.planes, self.components, self.occurrences = [], [], [], [], []
        self.rootComponent = types.SimpleNamespace(
            occurrences=types.SimpleNamespace(addNewComponent=self._add_component))

    def _add_component(self, matrix):
        comp = Component(self)
        self.components.append(comp)
        occurrence = Occurrence(comp)
        self.occurrences.append(occurrence)
        self.log.append(("addNewComponent",))
        return occurrence

    def sketch(self, name):
        return next(s for s in self.sketches if s.name == name)

    def feature(self, name):
        return next(f for f in self.features if f.name == name)


# ---- installing -----------------------------------------------------------------------------------------------------------


def _module(name, **members):
    module = types.ModuleType(name)
    module.__dict__.update(members)
    return module


@contextlib.contextmanager
def installed(*dependents):
    """``adsk``, ``adsk.core`` and ``adsk.fusion`` as fakes in ``sys.modules``; ``dependents`` are dotted module names
    that import them (they are removed on the way out, with the attribute their package holds)."""
    core = _module("adsk.core", Vector3D=Vector3D, Point3D=Point3D, Matrix3D=Matrix3D, ValueInput=ValueInput,
                   ObjectCollection=ObjectCollection, HorizontalAlignments=HorizontalAlignments,
                   VerticalAlignments=VerticalAlignments)
    fusion = _module(
        "adsk.fusion", FeatureOperations=FeatureOperations, ExtentDirections=ExtentDirections,
        DimensionOrientations=DimensionOrientations, FeatureHealthStates=FeatureHealthStates,
        PatternDistanceType=PatternDistanceType, TextStyles=TextStyles,
        OffsetStartDefinition=types.SimpleNamespace(create=lambda v: ("offset", v)),
        DistanceExtentDefinition=types.SimpleNamespace(create=lambda v: ("distance", v)))
    adsk = _module("adsk", core=core, fusion=fusion)
    fakes = {"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion}
    saved = {name: sys.modules.get(name) for name in (*fakes, *dependents)}
    sys.modules.update(fakes)
    for name in dependents:
        sys.modules.pop(name, None)
    try:
        yield
    finally:
        for name in dependents:
            sys.modules.pop(name, None)
            parent, _, leaf = name.rpartition(".")
            if parent in sys.modules and hasattr(sys.modules[parent], leaf):
                delattr(sys.modules[parent], leaf)
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
