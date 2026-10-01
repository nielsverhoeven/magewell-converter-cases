"""FusionDocument: the document port on the Fusion API. The only module that reads or changes a design.

Imports adsk, so it loads only inside Fusion.
Units: Fusion holds lengths in cm and angles in rad. This module is the single place that converts what it
reads (cm to mm, cm2 to mm2, cm3 to mm3). It never turns a number into a dimension: texts go in as they are.
"""
import math
import os
import sys

import adsk.core
import adsk.fusion

from . import fusion_app, paramset, plan as planmod, port

REFINEMENT = {"high": "MeshRefinementHigh", "medium": "MeshRefinementMedium", "low": "MeshRefinementLow"}
IDENTITY = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def _short(entity):
    return entity.objectType.split("::")[-1]


class FusionDocument(port.DocumentPort):
    backend = "fusion"

    def __init__(self, doc, design):
        self.doc, self.design = doc, design

    # ---- facts -------------------------------------------------------------------------------------
    def info(self):
        a = fusion_app.app()
        data_file = self.doc.dataFile if self.doc.isSaved else None
        return {"backend": "fusion", "fusion_version": a.version, "python": sys.version.split()[0],
                "design_intent": {adsk.fusion.DesignIntentTypes.PartDesignIntentType: "part",
                                  adsk.fusion.DesignIntentTypes.AssemblyDesignIntentType: "assembly",
                                  adsk.fusion.DesignIntentTypes.HybridDesignIntentType: "hybrid"}.get(
                                      self.design.designIntent, "unknown"),
                "unsaved": not self.doc.isSaved,
                "hub_version": data_file.versionNumber if data_file is not None else None,
                "up_axis": "Z" if fusion_app.is_z_up() else "Y"}

    # ---- parameters --------------------------------------------------------------------------------
    def add_parameters(self, rows, texts):
        ups = self.design.userParameters
        for row in rows:
            text = texts[row["name"]]
            try:
                created = ups.add(row["name"], adsk.core.ValueInput.createByString(text), row["unit"],
                                  row.get("comment") or "")
            except RuntimeError as exc:
                raise port.PortError("user parameter %s = %r was not accepted: %s" % (row["name"], text, exc))
            if created is None:
                raise port.PortError("user parameter %s = %r was not accepted" % (row["name"], text))

    def modify_parameters(self, texts):
        ups = self.design.userParameters
        params, values = [], []
        for name in sorted(texts):
            p = ups.itemByName(name)                       # names are case sensitive
            if p is None:
                raise port.PortError("the document has no user parameter %s" % name)
            params.append(p)
            values.append(adsk.core.ValueInput.createByString(texts[name]))
        try:
            ok = self.design.modifyParameters(params, values)       # all or none
        except RuntimeError as exc:
            raise port.PortError("modifyParameters failed: %s" % exc)
        if not ok:
            raise port.PortError("modifyParameters rejected the set; nothing was changed")

    # ---- timeline ----------------------------------------------------------------------------------
    def _timeline(self):
        tl = self.design.timeline
        return [tl.item(i) for i in range(tl.count)]

    def set_suppressed(self, names, suppressed):
        wanted = set(names)
        objects = [o for o in self._timeline() if o.name in wanted]
        missing = sorted(wanted - {o.name for o in objects})
        if missing:
            raise port.PortError("no timeline object named %s" % ", ".join(missing))
        try:
            ok = self.design.setSuppressed(objects, bool(suppressed))   # one recompute, all or none
        except RuntimeError as exc:
            raise port.PortError("setSuppressed failed: %s" % exc)
        if not ok:
            raise port.PortError("setSuppressed rejected the change; nothing was changed")

    def compute(self):
        if not self.design.computeAll():                   # says nothing about health: snapshot() reads it
            raise port.PortError("computeAll did not complete")

    # ---- read back ---------------------------------------------------------------------------------
    def _component_name(self, comp):
        return "." if comp == self.design.rootComponent else comp.name

    def _plane_ref(self, comp, entity):
        if entity is None:
            return "other:none"
        for label, plane in (("XY", comp.xYConstructionPlane), ("XZ", comp.xZConstructionPlane),
                             ("YZ", comp.yZConstructionPlane)):
            if entity == plane:
                return "origin:" + label
        plane = adsk.fusion.ConstructionPlane.cast(entity)
        return "plane:" + plane.name if plane is not None else "other:" + _short(entity)

    @staticmethod
    def _health(state):
        h = adsk.fusion.FeatureHealthStates
        return {h.HealthyFeatureHealthState: "healthy", h.WarningFeatureHealthState: "warning",
                h.ErrorFeatureHealthState: "error", h.SuppressedFeatureHealthState: "suppressed",
                h.RolledBackFeatureHealthState: "rolled_back"}.get(state, "unknown")

    def _item(self, obj):
        rec = {"index": obj.index, "name": obj.name, "component": ".", "suppressed": bool(obj.isSuppressed),
               "health": self._health(obj.healthState), "message": obj.errorOrWarningMessage, "parameters": []}
        entity = None if obj.isGroup else obj.entity
        if entity is None:
            rec.update(kind="other", type="TimelineGroup" if obj.isGroup else "Unknown")
            return rec
        occ = adsk.fusion.Occurrence.cast(entity)
        sketch = adsk.fusion.Sketch.cast(entity)
        plane = adsk.fusion.ConstructionPlane.cast(entity)
        feature = adsk.fusion.Feature.cast(entity)
        if occ is not None:
            parent = occ.assemblyContext
            rec.update(kind="component", type="Occurrence", name=occ.component.name,
                       component="." if parent is None else parent.component.name)
        elif sketch is not None:
            comp = sketch.parentComponent
            texts = sketch.sketchTexts
            rec.update(kind="sketch", type="Sketch", component=self._component_name(comp),
                       on=self._plane_ref(comp, sketch.referencePlane),
                       fully_constrained=bool(sketch.isFullyConstrained),
                       texts=[texts.item(i).textParameter.textValue for i in range(texts.count)])
        elif plane is not None:
            comp = plane.component
            offset = adsk.fusion.ConstructionPlaneOffsetDefinition.cast(plane.definition)
            rec.update(kind="plane", type="ConstructionPlane", component=self._component_name(comp),
                       on=self._plane_ref(comp, offset.planarEntity) if offset is not None
                       else "other:" + _short(plane.definition))
        elif feature is not None:
            rec.update(kind="feature", type=_short(entity), component=self._component_name(feature.parentComponent))
        else:
            rec.update(kind="other", type=_short(entity))
        return rec

    @staticmethod
    def _owner_index(owner):
        """Timeline index of the object that a model parameter belongs to, or None."""
        if owner is None:
            return None
        dim = adsk.fusion.SketchDimension.cast(owner)
        if dim is not None:
            return dim.parentSketch.timelineObject.index
        text = adsk.fusion.SketchText.cast(owner)
        if text is not None:
            return text.parentSketch.timelineObject.index
        obj = getattr(owner, "timelineObject", None)
        return obj.index if obj is not None else None

    def snapshot(self):
        design, root = self.design, self.design.rootComponent
        items = [self._item(o) for o in self._timeline()]
        by_index = {i["index"]: i for i in items}
        orphans = []
        params = design.allParameters
        for n in range(params.count):
            mp = adsk.fusion.ModelParameter.cast(params.item(n))
            if mp is None:
                continue                                            # a user parameter
            if mp.valueType != adsk.fusion.ParameterValueTypes.NumericParameterValueType:
                continue                                            # a text: listed under "texts" of its sketch
            entry = {"name": mp.name, "role": mp.role, "unit": mp.unit, "expression": mp.expression,
                     "value": paramset.internal_to_user(mp.value, mp.unit)}
            index = self._owner_index(mp.createdBy)
            if index in by_index:
                by_index[index]["parameters"].append(entry)
            else:
                orphans.append(entry)
        ups, user = design.userParameters, []
        for n in range(ups.count):
            p = ups.item(n)
            numeric = p.valueType == adsk.fusion.ParameterValueTypes.NumericParameterValueType
            user.append({"name": p.name, "unit": p.unit, "expression": p.expression, "comment": p.comment,
                         "value": paramset.internal_to_user(p.value, p.unit) if numeric else None})
        comps = [{"name": ".", "parent": None, "solids": self._solids(root), "identity_placement": True}]
        everything = design.allComponents
        for n in range(everything.count):
            comp = everything.item(n)
            if comp == root:
                continue
            occs = root.allOccurrencesByComponent(comp)
            identity = occs.count == 1 and all(
                abs(a - b) < 1e-9 for a, b in zip(occs.item(0).transform2.asArray(), IDENTITY))
            comps.append({"name": comp.name, "parent": ".", "solids": self._solids(comp),
                          "identity_placement": identity})
        mm = design.fusionUnitsManager.distanceDisplayUnits == adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        parametric = design.designType == adsk.fusion.DesignTypes.ParametricDesignType
        return {"schema": 1, "document": self.doc.name, "backend": "fusion",
                "design_type": "parametric" if parametric else "direct", "length_unit": "mm" if mm else "other",
                "up_axis": "Z" if fusion_app.is_z_up() else "Y",
                "marker_at_end": design.timeline.markerPosition == design.timeline.count,
                "groups": sum(1 for i in items if i["type"] == "TimelineGroup"),
                "components": comps, "user_parameters": user, "timeline": items, "orphan_parameters": orphans}

    # ---- solids ------------------------------------------------------------------------------------
    def _component(self, name):
        if name == ".":
            return self.design.rootComponent
        comp = self.design.allComponents.itemByName(name)
        if comp is None:
            raise port.PortError("the document has no component %s" % name)
        return comp

    @staticmethod
    def _solid_bodies(comp):
        bodies = comp.bRepBodies
        return [bodies.item(i) for i in range(bodies.count) if bodies.item(i).isSolid]

    def _solids(self, comp):
        return len(self._solid_bodies(comp))

    def measure(self, component):
        bodies = self._solid_bodies(self._component(component))
        lo, hi, volume, area = [math.inf] * 3, [-math.inf] * 3, 0.0, 0.0
        for body in bodies:
            box = body.preciseBoundingBox                           # tight; cm
            for k, axis in enumerate("xyz"):
                lo[k] = min(lo[k], getattr(box.minPoint, axis) * 10.0)
                hi[k] = max(hi[k], getattr(box.maxPoint, axis) * 10.0)
            props = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
            volume += props.volume * 1000.0                         # cm3 -> mm3
            area += props.area * 100.0                              # cm2 -> mm2
        if not bodies:
            return {"bbox": None, "volume_mm3": 0.0, "area_mm2": 0.0, "solids": 0}
        return {"bbox": {"min": lo, "max": hi, "size": [h - l for l, h in zip(lo, hi)]},
                "volume_mm3": volume, "area_mm2": area, "solids": len(bodies)}

    # ---- export ------------------------------------------------------------------------------------
    def _refuse_scratch(self):
        if self.doc.name.startswith(planmod.SCRATCH_PREFIX):
            raise port.PortError("a scratch document is never exported")

    def export(self, component, fmt, path, settings):
        self._refuse_scratch()
        comp, manager = self._component(component), self.design.exportManager
        used = {"units": "mm"}
        if fmt == "step":
            options = manager.createSTEPExportOptions(path, comp)   # component coordinates = assembly frame
        elif fmt in ("stl", "3mf"):
            bodies = self._solid_bodies(comp)
            if len(bodies) != 1:
                raise port.PortError("%s has %d solids; exactly one is exported" % (component, len(bodies)))
            refinement = settings.get("stl_refinement", "high")
            if fmt == "stl":
                options = manager.createSTLExportOptions(bodies[0], path)
                options.isBinaryFormat = True
                options.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            else:
                options = manager.createC3MFExportOptions(bodies[0], path)
            options.sendToPrintUtility = False
            options.meshRefinement = getattr(adsk.fusion.MeshRefinementSettings, REFINEMENT[refinement])
            used.update({"stl_binary": True, "stl_refinement": refinement,
                         "stl_surface_deviation_mm": options.surfaceDeviation * 10.0,
                         "stl_normal_deviation_rad": options.normalDeviation,
                         "stl_max_edge_length_mm": options.maximumEdgeLength * 10.0,
                         "stl_aspect_ratio": options.aspectRatio})
        else:
            raise port.PortError("unknown export format %r" % fmt)
        try:
            ok = manager.execute(options)
        except RuntimeError as exc:
            raise port.PortError("export of %s as %s failed: %s" % (component, fmt, exc))
        if not ok or not os.path.isfile(path):
            raise port.PortError("export of %s as %s wrote no file" % (component, fmt))
        return used

    def export_archive(self, path):
        self._refuse_scratch()
        manager = self.design.exportManager
        try:
            ok = manager.execute(manager.createFusionArchiveExportOptions(path))
        except RuntimeError as exc:
            raise port.PortError("archive export failed: %s" % exc)
        if not ok or not os.path.isfile(path):
            raise port.PortError("archive export wrote no file")
        return {"format": "f3d"}

    def capture(self, path, view, width, height):
        from . import capture
        return capture.save_view(self.doc, self.measure_all(), path, view, width, height)

    def measure_all(self):
        """Bounding box (mm) over the solids of every component, for the camera."""
        lo, hi = [math.inf] * 3, [-math.inf] * 3
        everything = self.design.allComponents
        for n in range(everything.count):
            for body in self._solid_bodies(everything.item(n)):
                box = body.preciseBoundingBox
                for k, axis in enumerate("xyz"):
                    lo[k] = min(lo[k], getattr(box.minPoint, axis) * 10.0)
                    hi[k] = max(hi[k], getattr(box.maxPoint, axis) * 10.0)
        return lo, hi

    def close(self):
        try:
            if self.doc.isValid:
                self.doc.close(False)
        except RuntimeError:
            pass
