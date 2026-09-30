"""Builder of the runtime's own test document "MCC-RuntimeTest" (product-free, no kit).

Every dimension is an expression of user parameters, every sketch is fully constrained and lies on an origin
plane or on a plane offset by a parameter, nothing references a body face or edge, everything is named.
"""

RECORDED = {"schema": 1, "document": "MCC-RuntimeTest", "items": [
    {"kind": "component", "name": "TestBlock", "component": "."},
    {"kind": "sketch", "name": "Test_Block_Sketch", "component": "TestBlock", "on": "origin:XY",
     "expressions": ["V_TEST_L", "V_TEST_W"]},
    {"kind": "feature", "name": "Test_Block_Extrude", "component": "TestBlock", "type": "ExtrudeFeature",
     "expressions": ["V_TEST_H"]},
    {"kind": "sketch", "name": "Test_Hole_Sketch", "component": "TestBlock", "on": "origin:XY",
     "expressions": ["V_TEST_HOLE_D", "V_TEST_L / 2", "V_TEST_W - TST_WALL - V_TEST_HOLE_D / 2"]},
    {"kind": "feature", "name": "Test_Hole_Cut", "component": "TestBlock", "type": "ExtrudeFeature",
     "expressions": []},
    {"kind": "plane", "name": "Test_Pin_Plane", "component": "TestBlock", "on": "origin:XY",
     "expressions": ["V_TEST_H"]},
    {"kind": "sketch", "name": "Test_Pin_Sketch", "component": "TestBlock", "on": "plane:Test_Pin_Plane",
     "expressions": ["TST_PIN_D", "TST_WALL + TST_PIN_D / 2", "TST_WALL + TST_PIN_D / 2"]},
    {"kind": "feature", "name": "Test_Pin_Extrude", "component": "TestBlock", "type": "ExtrudeFeature",
     "expressions": ["TST_PIN_H"]},
    {"kind": "feature", "name": "Test_Pin_Pattern", "component": "TestBlock", "type": "RectangularPatternFeature",
     "expressions": ["V_N_TEST_PINS", "TST_PITCH"]},
    {"kind": "component", "name": "Reserve_TestBay", "component": "."},
    {"kind": "sketch", "name": "Reserve_TestBay_Sketch", "component": "Reserve_TestBay", "on": "origin:XY",
     "expressions": ["TST_WALL", "TST_WALL"]},
    {"kind": "feature", "name": "Reserve_TestBay_Extrude", "component": "Reserve_TestBay",
     "type": "ExtrudeFeature", "expressions": ["TST_WALL"]},
]}


def build(ctx):
    if ctx.backend == "recording":
        return RECORDED
    _build_fusion(ctx.design)
    return RECORDED


# ------------------------------------------------------------------------------------------------------------
def _build_fusion(design):
    import adsk.core
    import adsk.fusion

    fops = adsk.fusion.FeatureOperations
    positive = adsk.fusion.ExtentDirections.PositiveExtentDirection
    units = design.unitsManager
    root = design.rootComponent

    def vi(text):
        return adsk.core.ValueInput.createByString(text)

    def cm(text):
        """The current value of an expression in cm. Used only to place sketch points before a dimension binds."""
        return units.evaluateExpression(text, "mm")

    def new_component(name):
        occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())   # identity: assembly frame
        occurrence.component.name = name
        return occurrence.component

    class Frame:
        """Maps model X and Y (cm) into a sketch that lies parallel to the XY plane."""

        def __init__(self, sketch, z_cm):
            self.sketch, self.z = sketch, z_cm
            x_dir = sketch.xDirection
            self.x_is_horizontal = abs(x_dir.x) > 0.9
            orient = adsk.fusion.DimensionOrientations
            self.along_x = orient.HorizontalDimensionOrientation if self.x_is_horizontal \
                else orient.VerticalDimensionOrientation
            self.along_y = orient.VerticalDimensionOrientation if self.x_is_horizontal \
                else orient.HorizontalDimensionOrientation

        def point(self, x_cm, y_cm):
            return self.sketch.modelToSketchSpace(adsk.core.Point3D.create(x_cm, y_cm, self.z))

        def constrain_along_x(self, line):
            c = self.sketch.geometricConstraints
            return c.addHorizontal(line) if self.x_is_horizontal else c.addVertical(line)

        def constrain_along_y(self, line):
            c = self.sketch.geometricConstraints
            return c.addVertical(line) if self.x_is_horizontal else c.addHorizontal(line)

        def dimension(self, p1, p2, orientation, x_cm, y_cm, text):
            dim = self.sketch.sketchDimensions.addDistanceDimension(p1, p2, orientation, self.point(x_cm, y_cm))
            dim.parameter.expression = text
            return dim

    def rectangle_from_origin(sketch, z_cm, size_x, size_y):
        """A rectangle with one corner on the sketch origin, sizes given as expressions."""
        f = Frame(sketch, z_cm)
        sx, sy = cm(size_x), cm(size_y)
        lines = sketch.sketchCurves.sketchLines
        l0 = lines.addByTwoPoints(f.point(0, 0), f.point(sx, 0))
        l1 = lines.addByTwoPoints(l0.endSketchPoint, f.point(sx, sy))
        l2 = lines.addByTwoPoints(l1.endSketchPoint, f.point(0, sy))
        l3 = lines.addByTwoPoints(l2.endSketchPoint, l0.startSketchPoint)
        f.constrain_along_x(l0)
        f.constrain_along_y(l1)
        f.constrain_along_x(l2)
        f.constrain_along_y(l3)
        sketch.geometricConstraints.addCoincident(l0.startSketchPoint, sketch.originPoint)
        f.dimension(l0.startSketchPoint, l0.endSketchPoint, f.along_x, sx / 2, -0.5, size_x)
        f.dimension(l1.startSketchPoint, l1.endSketchPoint, f.along_y, sx + 0.5, sy / 2, size_y)

    def circle_from_origin(sketch, z_cm, centre_x, centre_y, diameter):
        """A circle whose centre is dimensioned from the sketch origin, all three values as expressions."""
        f = Frame(sketch, z_cm)
        cx, cy, d = cm(centre_x), cm(centre_y), cm(diameter)
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(f.point(cx, cy), d / 2)
        dim = sketch.sketchDimensions.addDiameterDimension(circle, f.point(cx + d, cy + d))
        dim.parameter.expression = diameter
        f.dimension(sketch.originPoint, circle.centerSketchPoint, f.along_x, cx / 2, -0.5, centre_x)
        f.dimension(sketch.originPoint, circle.centerSketchPoint, f.along_y, -0.5, cy / 2, centre_y)

    def check(sketch):
        if not sketch.isFullyConstrained:
            raise RuntimeError("sketch %s is not fully constrained" % sketch.name)
        if sketch.profiles.count != 1:
            raise RuntimeError("sketch %s has %d profiles, expected 1" % (sketch.name, sketch.profiles.count))

    def extrude(comp, sketch, name, operation, distance=None, body=None):
        features = comp.features.extrudeFeatures
        inp = features.createInput(sketch.profiles.item(0), operation)
        if distance is None:
            inp.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(), positive)
        else:
            inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(distance)), positive)
        if body is not None:
            inp.participantBodies = [body]
        feature = features.add(inp)
        feature.name = name
        if feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            raise RuntimeError("feature %s: %s" % (name, feature.errorOrWarningMessage))
        return feature

    # ---- component TestBlock -------------------------------------------------------------------------
    block = new_component("TestBlock")
    sk = block.sketches.add(block.xYConstructionPlane)
    sk.name = "Test_Block_Sketch"
    rectangle_from_origin(sk, 0.0, "V_TEST_L", "V_TEST_W")
    check(sk)
    base = extrude(block, sk, "Test_Block_Extrude", fops.NewBodyFeatureOperation, "V_TEST_H")
    body = base.bodies.item(0)
    body.name = "TestBlock"

    sk = block.sketches.add(block.xYConstructionPlane)
    sk.name = "Test_Hole_Sketch"
    circle_from_origin(sk, 0.0, "V_TEST_L / 2", "V_TEST_W - TST_WALL - V_TEST_HOLE_D / 2", "V_TEST_HOLE_D")
    check(sk)
    extrude(block, sk, "Test_Hole_Cut", fops.CutFeatureOperation, None, body)

    planes = block.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(block.xYConstructionPlane, vi("V_TEST_H"))
    plane = planes.add(plane_input)
    plane.name = "Test_Pin_Plane"

    sk = block.sketches.add(plane)
    sk.name = "Test_Pin_Sketch"
    circle_from_origin(sk, cm("V_TEST_H"), "TST_WALL + TST_PIN_D / 2", "TST_WALL + TST_PIN_D / 2", "TST_PIN_D")
    check(sk)
    pin = extrude(block, sk, "Test_Pin_Extrude", fops.JoinFeatureOperation, "TST_PIN_H")

    entities = adsk.core.ObjectCollection.create()
    entities.add(pin)
    patterns = block.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(entities, block.xConstructionAxis, vi("V_N_TEST_PINS"), vi("TST_PITCH"),
                                         adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    pattern = patterns.add(pattern_input)
    pattern.name = "Test_Pin_Pattern"

    # ---- component Reserve_TestBay (never exported) --------------------------------------------------
    bay = new_component("Reserve_TestBay")
    sk = bay.sketches.add(bay.xYConstructionPlane)
    sk.name = "Reserve_TestBay_Sketch"
    rectangle_from_origin(sk, 0.0, "TST_WALL", "TST_WALL")
    check(sk)
    cube = extrude(bay, sk, "Reserve_TestBay_Extrude", fops.NewBodyFeatureOperation, "TST_WALL")
    cube.bodies.item(0).name = "Reserve_TestBay"
