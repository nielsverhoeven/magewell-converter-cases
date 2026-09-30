"""The live probes of the modelling kit (issue #81, plan section 10, milestone K5b; verdict A11 adds G19).

``PROBES = [(id, title, function), ...]`` is the registration of contract C6 of #79: the probe job of the runtime
imports this module (``fusion_run.py probe`` sends every ``cad/fusion/gen/**/probes.py`` of the checkout) and calls
``function(env)`` for each entry.  ``env`` has ``app``, ``ui``, ``new_design(name)``, ``out_dir``, ``log(text)`` and a
``cache`` dict.  Each function opens its own scratch design (``SCRATCH-<id>``, never exported) and returns a plain
dict::

    {"id": "G1", "status": "pass" | "fail" | "info", "answer": {...named facts...},
     "covers": [...], "copy_into": "where the answer is copied to", "if_unfavourable": "what a bad answer means"}

``answer`` has the same keys on every run (the keys a probe declares); a step that Fusion refuses is recorded in the
answer as ``{"ok": False, "error": "<type>: <message>"}`` and never raises, so one unfavourable answer does not hide
the next.  ``status`` is ``pass`` when the favourable answer of plan section 10 holds, ``fail`` when it does not,
``info`` for a measurement that only has to be copied (G1's ``PLANE_NORMAL``, the times of G18).  An exception that
escapes a function is a wrong use of the API in this file; the runtime reports it as ``error`` with the traceback.

Nothing here runs without Fusion: the offline tests (``tests/test_probes.py``) run every probe against a permissive
fake, check the registry against G1 to G19 and the UNVERIFIED list of PR #99, and scan this file's adsk member names
against ``tests/fixtures/probe_members.json`` (and the stub where it is installed).

Units: Fusion's database unit is the centimetre (``_mm`` converts); every expression here is a string.  ``adsk`` is
imported here, in ``fusion_backend.py``, in ``enhance_fusion.py`` and in the runtime only (verdict A8 rule 1).  The
kit probes (G5 to G13, G15, G18, G19 and the text probe) build through the kit itself (``Kit`` with the Fusion
backend), so they test the code that will build the case; the raw probes (G1 to G4, G14, G16, G17, the dimension text
points) call the API directly.
"""
from __future__ import annotations

import contextlib
import math
import re
import time
import types

import adsk.core
import adsk.fusion

from . import expr, facade
from .facade import Kit

STATUSES = ("pass", "fail", "info")
PLANES = ("XY", "XZ", "YZ")
NORMAL_AXIS = {"XY": "Z", "XZ": "Y", "YZ": "X"}
AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
TOL = 1e-6

PROBES: list = []  # (id, title, function): contract C6
META: dict[str, dict] = {}  # id -> {"keys", "covers", "copy_into", "if_unfavourable"}
COVERS: dict[str, list[str]] = {}  # id -> the UNVERIFIED items of PR #99 (and the plan 10 rows) the probe answers


# ---- registration and plain-data helpers ---------------------------------------------------------------------------


def _json(x):
    """Plain JSON data: numbers rounded to 6 decimals, NaN and infinity as None, everything unknown as its repr."""
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return round(x, 6) if math.isfinite(x) else None
    if isinstance(x, dict):
        return {str(k): _json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set, frozenset)):
        return [_json(v) for v in (sorted(x, key=str) if isinstance(x, (set, frozenset)) else x)]
    return repr(x)


def _probe(pid, title, *, keys, covers, copy_into, unfavourable):
    def register(fn):
        def run(env):
            status, answer = fn(env)
            missing = [k for k in keys if k not in answer]
            if missing or status not in STATUSES:
                raise AssertionError(f"probe {pid}: status {status!r}, answer lacks {missing}")
            return _json({"id": pid, "status": status, "answer": answer, "covers": list(covers),
                          "copy_into": copy_into, "if_unfavourable": unfavourable})

        run.__name__ = fn.__name__
        run.__doc__ = fn.__doc__
        PROBES.append((pid, title, run))
        META[pid] = {"keys": list(keys), "covers": list(covers), "copy_into": copy_into, "if_unfavourable": unfavourable}
        COVERS[pid] = list(covers)
        return run

    return register


def _err(exc) -> str:
    return f"{type(exc).__name__}: {exc}"[:400]


def _attempt(fn, *args):
    """``(True, value)`` or ``(False, "Type: message")``; a time-out of the runtime passes through."""
    try:
        return True, fn(*args)
    except TimeoutError:
        raise
    except Exception as exc:  # noqa: BLE001  a refusal of Fusion is an answer
        if type(exc).__name__ == "JobTimeout":
            raise
        return False, _err(exc)


def _step(fn, *args) -> dict:
    """An attempt as a record: ``{"ok": True, "value": v}`` or ``{"ok": False, "error": text}``."""
    ok, value = _attempt(fn, *args)
    return {"ok": True, "value": value} if ok else {"ok": False, "error": value}


def _close(a, b, tol=0.05) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def _mm(cm) -> float:
    return float(cm) * 10.0


def _vi(text):
    return adsk.core.ValueInput.createByString(text)  # core:26143


def _vec(v) -> list:
    return [round(float(v.x), 9), round(float(v.y), 9), round(float(v.z), 9)]  # core:26688, 26696, 26704


def _point(p) -> list:
    return [_mm(p.x), _mm(p.y), _mm(p.z)]  # core:18954, 18962, 18970


def _axis_sign(v):
    """``(letter, sign)`` of a vector along a model axis, else None."""
    comps = [float(v.x), float(v.y), float(v.z)]
    i = max(range(3), key=lambda k: abs(comps[k]))
    if abs(abs(comps[i]) - 1.0) > 1e-6 or any(abs(c) > 1e-6 for k, c in enumerate(comps) if k != i):
        return None
    return "XYZ"[i], 1 if comps[i] > 0 else -1


def _short(object_type) -> str:
    return str(object_type).rsplit("::", 1)[-1]


# ---- designs, parameters and the kit ---------------------------------------------------------------------------------

# every parameter the probes use: name -> (value, unit); mm unless "none" (a count) or "deg"
BASE = {
    "V_PL": (100.0, "mm"), "V_PW": (60.0, "mm"), "V_PT": (3.0, "mm"), "V_BH": (30.0, "mm"),
    "V_SX": (10.0, "mm"), "V_SW": (4.0, "mm"), "V_SV0": (10.0, "mm"), "V_SV1": (18.0, "mm"),
    "V_PITCH": (20.0, "mm"), "V_PITCH2": (30.0, "mm"), "V_N_SLOTS": (3, "none"), "V_N_ROWS": (2, "none"),
    "V_N_POSTS": (3, "none"), "V_RH": (5.0, "mm"), "V_RX": (10.0, "mm"), "V_RW": (4.0, "mm"),
    "V_RV0": (10.0, "mm"), "V_RV1": (18.0, "mm"), "V_IX": (20.0, "mm"), "V_IW": (10.0, "mm"),
    "V_CX": (50.0, "mm"), "V_CY": (30.0, "mm"), "V_D": (20.0, "mm"), "V_DX": (15.0, "mm"), "V_DY": (12.0, "mm"),
    "V_OD": (40.0, "mm"), "V_ID": (24.0, "mm"), "V_BARW": (6.0, "mm"),
    "V_PU0": (10.0, "mm"), "V_PU1": (40.0, "mm"), "V_PU2": (50.0, "mm"), "V_PU3": (25.0, "mm"), "V_PU4": (5.0, "mm"),
    "V_PV0": (10.0, "mm"), "V_PV1": (10.0, "mm"), "V_PV2": (30.0, "mm"), "V_PV3": (45.0, "mm"), "V_PV4": (30.0, "mm"),
    "V_LA0": (10.0, "mm"), "V_LA1": (50.0, "mm"), "V_LB0": (20.0, "mm"), "V_LB1": (40.0, "mm"),
    "V_LV0": (10.0, "mm"), "V_LV1": (30.0, "mm"), "V_LH": (10.0, "mm"), "V_DA": (20.0, "mm"),
    "V_XL": (40.0, "mm"), "V_XW": (30.0, "mm"), "V_XH": (10.0, "mm"), "V_HD": (10.0, "mm"),
    "V_TU0": (10.0, "mm"), "V_TU1": (50.0, "mm"), "V_TV0": (5.0, "mm"), "V_TV1": (25.0, "mm"),
    "V_TD": (2.0, "mm"), "V_TH": (12.0, "mm"),
    "V_PWL": (400.0, "mm"), "V_ROW": (7.0, "mm"), "V_RS": (4.0, "mm"),
    "V_A": (10.0, "mm"), "V_B": (4.0, "mm"), "MCC_B": (1.0, "mm"), "V_ANG": (30.0, "deg"),
}


def _new(env, pid):
    """A scratch design (the runtime never exports a ``SCRATCH-`` document and closes it after the probe)."""
    made = env.new_design(f"SCRATCH-{pid}")
    if isinstance(made, tuple):  # the runtime's probe env returns (document, design)
        made = made[1]
    return made if hasattr(made, "rootComponent") else made.design


def _params(*names) -> dict:
    return {n: BASE[n] for n in names}


def _add_params(design, params) -> None:
    """User parameters, every expression a string with its unit (``UserParameters.add``: api:80917)."""
    units = {"mm": "mm", "deg": "deg", "none": ""}
    for name, (value, unit) in params.items():
        text = f"{value} {unit}" if unit in ("mm", "deg") else f"{value}"
        design.userParameters.add(name, _vi(text), units[unit], "probe")  # api:103225, 80917


def _row(name, unit):
    return {"name": name, "unit": unit, "kind": "solver", "expression": None, "fusion": None, "comment": "",
            "description": "probe parameter", "src": "probes", "conf": None}


class _Doc:
    """A scratch design with user parameters and a kit on the Fusion backend."""

    def __init__(self, env, pid, params):
        self.design = _new(env, pid)
        self.params = dict(params)
        _add_params(self.design, params)
        rows = [_row(n, "none" if u == "none" else u) for n, (v, u) in params.items() if u != "deg"]
        values = {n: v for n, (v, u) in params.items() if u != "deg"}
        self.kit = Kit(types.SimpleNamespace(backend="fusion", design=self.design, document=f"SCRATCH-{pid}",
                                             registry=rows, values=values, options={}, log=env.log))

    def comp(self, name):
        return _comp(self.design, name)

    def start(self, build):
        """The kit component of a build (raises a KitError for a wrong call, which is a bug of this file)."""
        return self.kit.component(build.comp, role=build.role, datum=build.datum)

    def run(self, build) -> dict:
        """Every step of a build; ``{"built": bool, "errors": {step: "Type: message"}}``.  A refusal of Fusion is an
        answer, so the next step still runs."""
        ok, c = _attempt(self.start, build)
        if not ok:
            return {"built": False, "errors": {"component": c}}
        errors = {}
        for label, fn in build.steps:
            ok, error = _attempt(fn, c)
            if not ok:
                errors[label] = error
        return {"built": not errors, "errors": errors}

    def set(self, name, text) -> None:
        self.design.userParameters.itemByName(name).expression = text  # api:80900, 54435

    def mm3(self, comp_name):
        body = self.comp(comp_name).bRepBodies.item(0)
        return float(body.volume) * 1000.0  # api:16652, cm3 to mm3


def _comp(design, name):
    occurrences = design.rootComponent.occurrences  # api:103187, 89686
    for i in range(occurrences.count):  # api:53524
        component = occurrences.item(i).component  # api:53516, 52679
        if component.name == name:
            return component
    return None


def _healthy(state) -> bool:
    return state == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState  # api:2268


def _sketch_facts(sk) -> dict:
    profiles = sk.profiles  # api:68712
    healthy = _healthy(sk.healthState)  # api:68828
    return {"sketch": sk.name, "fully_constrained": bool(sk.isFullyConstrained), "healthy": healthy,  # api:68804
            "message": None if healthy else str(sk.errorOrWarningMessage),  # api:68832
            "profiles": profiles.count,  # api:60894
            "loops_per_profile": sorted(profiles.item(i).profileLoops.count for i in range(profiles.count)),  # api:60885, 60266, 60798
            "constraints": sk.geometricConstraints.count,  # api:68443, 39395
            "dimensions": sk.sketchDimensions.count,  # api:68435, 70543
            "points": sk.sketchPoints.count}  # api:68418, 72468


def _last_sketch_facts(comp) -> dict | None:
    if comp is None or comp.sketches.count == 0:  # api:89089, 71357
        return None
    return _sketch_facts(comp.sketches.item(comp.sketches.count - 1))  # api:71340


def _feature_health(comp, name):
    feature = comp.features.itemByName(name)  # api:36564
    if feature is None:
        return "missing"
    return "healthy" if _healthy(feature.healthState) else f"unhealthy: {feature.errorOrWarningMessage}"  # api:36024, 36028


def _box_mm(body) -> dict:
    box = body.boundingBox  # api:16636
    return {"min": _point(box.minPoint), "max": _point(box.maxPoint)}  # core:6209, 6217


# ---- raw building blocks ---------------------------------------------------------------------------------------------


def _origin_plane(comp, name):
    return {"XY": comp.xYConstructionPlane, "XZ": comp.xZConstructionPlane, "YZ": comp.yZConstructionPlane}[name]  # api:89156, 89160, 89164


def _offset_plane(comp, base, text):
    inp = comp.constructionPlanes.createInput()  # api:27966
    inp.setByOffset(_origin_plane(comp, base), _vi(text))  # api:27575
    return comp.constructionPlanes.add(inp)  # api:27976


def _circle_profile(comp, plane, radius_cm=1.0):
    sk = comp.sketches.add(plane)  # api:71361
    sk.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), radius_cm)  # api:68426, 69702, core:18894
    return sk.profiles.item(0)  # api:68712, 60885


def _extrude(comp, profile, start, distance, positive=True, operation=None):
    features = comp.features.extrudeFeatures  # api:89097, 36275
    inp = features.createInput(profile, operation or adsk.fusion.FeatureOperations.NewBodyFeatureOperation)  # api:35553, 2296
    if start is not None:
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(_vi(start))  # api:35235, 116239
    directions = adsk.fusion.ExtentDirections  # api:2216, 2217
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(_vi(distance)),  # api:35245, 104422
                         directions.PositiveExtentDirection if positive else directions.NegativeExtentDirection)
    return features.add(inp)  # api:35568


def _origin_normals(comp) -> dict:
    """Per origin plane: the sketch's x and y direction, their cross product, and its sign along the plane's axis."""
    out = {}
    for plane in PLANES:
        sk = comp.sketches.add(_origin_plane(comp, plane))  # api:71361
        x, y = sk.xDirection, sk.yDirection  # api:68623, 68627
        normal = x.crossProduct(y)  # core:26597
        found = _axis_sign(normal)
        axis = NORMAL_AXIS[plane]
        out[plane] = {"x": _vec(x), "y": _vec(y), "normal": _vec(normal),
                      "sign": found[1] if found and found[0] == axis else None,
                      "origin_model_mm": _point(sk.origin)}  # api:68619
    return out


def _along_normal(lo, hi, sign):
    """The interval ``[lo, hi]`` of a model axis seen along the sketch normal of sign ``sign``."""
    return (lo, hi) if sign == 1 else (-hi, -lo)


def _measured_normals(env) -> dict:
    """``{plane: +1 | -1}`` measured on a scratch design (G1's answer), cached in ``env.cache``."""
    cache = getattr(env, "cache", None)
    if cache is not None and "PLANE_NORMAL" in cache:
        return cache["PLANE_NORMAL"]
    design = _new(env, "FRAMES")
    found = _origin_normals(design.rootComponent)
    normals = {p: found[p]["sign"] for p in PLANES}
    if cache is not None:
        cache["PLANE_NORMAL"] = normals
    return normals


@contextlib.contextmanager
def _plane_normal(env):
    """``facade.PLANE_NORMAL`` set to the measured values for the length of a block (the placeholder says +1 on all
    three planes, and the backend refuses a sketch on XZ or YZ until G1 has filled it in); restored afterwards."""
    normals = _measured_normals(env)
    saved = dict(facade.PLANE_NORMAL)
    if all(normals.get(p) in (1, -1) for p in PLANES):
        facade.PLANE_NORMAL.update(normals)
    try:
        yield normals
    finally:
        facade.PLANE_NORMAL.clear()
        facade.PLANE_NORMAL.update(saved)


# ---- kit building blocks -----------------------------------------------------------------------------------------------
# A build is one kit component with its steps (kit calls).  The probes run them on the Fusion backend; the offline test
# runs every registered build on the recording backend, which checks names, phases, expressions and the facade's rules.


class _Build:
    def __init__(self, comp, role, steps, datum=(None, None, None)):
        self.comp, self.role, self.steps, self.datum = comp, role, list(steps), datum

    def fn(self, label):
        return dict(self.steps)[label]


BUILDS: list = []  # (probe id, build, parameter names): the offline test builds each one on the recording backend


def _register(pid, names, build) -> _Build:
    BUILDS.append((pid, build, tuple(names)))
    return build


def _plate(c, tag, length="V_PL", width="V_PW", height="V_PT"):
    c.extrude(f"{tag}_Plate_Body", axis="Z", loops=[c.rect(None, length, None, width)], start=None, end=height, op="new")


def _slot(c, tag):
    c.extrude(f"{tag}_Slot_Cut", axis="Z", loops=[c.rect("V_SX", "V_SX + V_SW", "V_SV0", "V_SV1")], start=None, end="V_PT", op="cut")


SLAB_NAMES = ("V_PL", "V_PW", "V_PT", "V_SX", "V_SW", "V_SV0", "V_SV1", "V_PITCH", "V_PITCH2", "V_N_SLOTS", "V_N_ROWS")


def _slab_build(pid, tag, axis="X", axis2=None) -> _Build:
    """A plate, one slot through it and a pattern of the slot along ``axis`` (and ``axis2``): G9, G12, G13, G15."""

    def pattern(c):
        if axis2 is None:
            c.pattern(f"{tag}_Slot_Pat", seed=f"{tag}_Slot_Cut", axis=axis, count="V_N_SLOTS", pitch="V_PITCH")
        else:
            c.pattern(f"{tag}_Slot_Pat", seed=f"{tag}_Slot_Cut", axis=axis, count="V_N_SLOTS", pitch="V_PITCH",
                      axis2=axis2, count2="V_N_ROWS", pitch2="V_PITCH2")

    return _register(pid, SLAB_NAMES, _Build(tag, "part", [("plate", lambda c: _plate(c, tag)), ("slot", lambda c: _slot(c, tag)),
                                                             ("pattern", pattern)]))


def _facts(doc, comp_name) -> dict:
    comp = doc.comp(comp_name)
    return {"sketch": _last_sketch_facts(comp), "bodies": comp.bRepBodies.count if comp is not None else None}



# ---- G1 to G4: frames, offsets, expressions -------------------------------------------------------------------------


@_probe("G1", "Sketch frames on the three origin planes and on an offset plane",
        keys=["PLANE_NORMAL", "frames", "offset_plane_origin_is_model_origin_projection", "offset_plane_sketch_origin_mm"],
        covers=["G1", "PLANE_NORMAL", "offset-sketch-origin"],
        copy_into="cad/fusion/gen/core/facade.py: PLANE_NORMAL = answer.PLANE_NORMAL",
        unfavourable="None needed for the signs; if a normal is not along its axis the backend cannot run and the kit's "
                     "sketch frame model has to be revisited.")
def g1(env):
    """One sketch per origin plane; x, y and x cross y; then a sketch on an offset plane per plane."""
    design = _new(env, "G1")
    comp = design.rootComponent
    frames = _origin_normals(comp)
    normals = {p: frames[p]["sign"] for p in PLANES}
    cache = getattr(env, "cache", None)
    if cache is not None:
        cache["PLANE_NORMAL"] = normals  # the kit probes that sketch on XZ or YZ read it (_plane_normal)
    offset = {}
    for plane in PLANES:
        def on_offset(plane=plane):
            sk = comp.sketches.add(_offset_plane(comp, plane, "10 mm"))  # api:71361
            origin = _point(sk.origin)  # api:68619
            axis = AXIS_INDEX[NORMAL_AXIS[plane]]
            return {"origin_mm": origin,
                    "in_plane_zero": all(abs(o) < 1e-6 for k, o in enumerate(origin) if k != axis),
                    "out_of_plane_mm": origin[axis]}

        offset[plane] = _step(on_offset)
    projection = all(o["ok"] and o["value"]["in_plane_zero"] for o in offset.values())
    good = all(n in (1, -1) for n in normals.values())
    return ("pass" if good and projection else "fail"), {
        "PLANE_NORMAL": normals, "frames": frames,
        "offset_plane_origin_is_model_origin_projection": projection,
        "offset_plane_sketch_origin_mm": offset}


@_probe("G2", "OffsetStartDefinition with positive, negative and zero expressions, and the extent direction",
        keys=["per_plane", "positive_offset_along_sketch_normal", "negative_offset_accepted", "zero_offset_accepted",
              "positive_extent_along_sketch_normal"],
        covers=["G2", "G2-offset-start"],
        copy_into="facade.Component._signed and the direction rule of the extrude spec (plan 3.7); the backend needs "
                  "a change only if a flag below is false",
        unfavourable="Start on an offset construction plane instead; the facade contract does not change.")
def g2(env):
    """Six extrudes of a circle per origin plane; the bounding box says where each started and which way it went."""
    design = _new(env, "G2")
    comp = design.rootComponent
    frames = _origin_normals(comp)
    per_plane, positive, negative_ok, zero_ok, extent = {}, [], [], [], []
    for plane in PLANES:
        profile = _circle_profile(comp, _origin_plane(comp, plane))
        sign = frames[plane]["sign"]
        axis = AXIS_INDEX[NORMAL_AXIS[plane]]
        record = {"sketch_normal_sign": sign}
        cases = {"start_plus_5": ("5 mm", True), "start_minus_5": ("-5 mm", True), "start_zero": ("0 mm", True),
                 "no_offset_positive": (None, True), "no_offset_negative": (None, False)}
        for label, (start, forward) in cases.items():
            def one(start=start, forward=forward):
                body = _extrude(comp, profile, start, "10 mm", forward).bodies.item(0)  # api:35991, 16512
                box = _box_mm(body)
                lo, hi = _along_normal(box["min"][axis], box["max"][axis], sign or 1)
                return {"along_normal_mm": [lo, hi]}

            record[label] = _step(one)
        per_plane[plane] = record

        def span(label, record=record):
            return record[label]["value"]["along_normal_mm"] if record[label]["ok"] else None

        def matches(label, want, record=record):
            got = span(label, record)
            return got is not None and _close(got[0], want[0]) and _close(got[1], want[1])

        positive.append(matches("start_plus_5", (5, 15)))
        negative_ok.append(record["start_minus_5"]["ok"] and matches("start_minus_5", (-5, 5)))
        zero_ok.append(record["start_zero"]["ok"] and matches("start_zero", (0, 10)))
        extent.append(matches("no_offset_positive", (0, 10)) and matches("no_offset_negative", (-10, 0)))
    answer = {"per_plane": per_plane, "positive_offset_along_sketch_normal": dict(zip(PLANES, positive)),
              "negative_offset_accepted": dict(zip(PLANES, negative_ok)), "zero_offset_accepted": dict(zip(PLANES, zero_ok)),
              "positive_extent_along_sketch_normal": dict(zip(PLANES, extent))}
    good = all(positive) and all(negative_ok) and all(zero_ok) and all(extent)
    return ("pass" if good else "fail"), answer


@_probe("G3", "setByOffset with positive, negative and zero expressions, and which way positive lies",
        keys=["per_plane", "positive_offset_along_sketch_normal", "negative_offset_accepted", "zero_offset_accepted"],
        covers=["G3", "G3-setByOffset"],
        copy_into="facade.Component.loft (plane offsets use _signed); a false flag changes the loft sections' sign rule",
        unfavourable="Loft sections offset from the opposite side with a positive expression.")
def g3(env):
    """Offset planes at +5, -5 and 0 mm from each origin plane; ``geometry.origin`` says where they lie."""
    design = _new(env, "G3")
    comp = design.rootComponent
    frames = _origin_normals(comp)
    per_plane, positive, negative_ok, zero_ok = {}, [], [], []
    for plane in PLANES:
        sign = frames[plane]["sign"] or 1
        axis = AXIS_INDEX[NORMAL_AXIS[plane]]
        record = {}
        for label, text in (("plus_5", "5 mm"), ("minus_5", "-5 mm"), ("zero", "0 mm")):
            def one(text=text):
                geometry = _offset_plane(comp, plane, text).geometry  # api:27146
                origin = _point(geometry.origin)  # core:39585
                return {"origin_mm": origin, "along_normal_mm": origin[axis] * sign, "normal": _vec(geometry.normal)}  # core:39593

            record[label] = _step(one)
        per_plane[plane] = record

        def along(label, record=record):
            return record[label]["value"]["along_normal_mm"] if record[label]["ok"] else None

        positive.append(_close(along("plus_5"), 5.0, 1e-3))
        negative_ok.append(_close(along("minus_5"), -5.0, 1e-3))
        zero_ok.append(_close(along("zero"), 0.0, 1e-3))
    answer = {"per_plane": per_plane, "positive_offset_along_sketch_normal": dict(zip(PLANES, positive)),
              "negative_offset_accepted": dict(zip(PLANES, negative_ok)), "zero_offset_accepted": dict(zip(PLANES, zero_ok))}
    return ("pass" if all(positive) and all(negative_ok) and all(zero_ok) else "fail"), answer


def _dimension_rig(env, pid, samples, params):
    """One distance dimension per expression on its own line of a sketch; the expression is set as the backend sets
    it (``dim.parameter.expression``) and read back with its value."""
    design = _new(env, pid)
    _add_params(design, params)
    sk = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)  # api:103187, 71361, 89156
    rows = []
    for k, (text, want_mm) in enumerate(samples):
        given = expr.fusion(text)
        y = float(k + 1)

        def one(given=given, y=y):
            line = sk.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0, y, 0),
                                                             adsk.core.Point3D.create(1, y, 0))  # api:68426, 72162
            dim = sk.sketchDimensions.addDistanceDimension(  # api:68435, 70547
                line.startSketchPoint, line.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,  # api:151696, 151703, 2071
                adsk.core.Point3D.create(0.5, y + 0.5, 0))
            dim.parameter.expression = given  # api:70263, 113941
            return {"echo": dim.parameter.expression, "value_mm": _mm(dim.parameter.value)}  # api:113917, 54415

        result = _step(one)
        row = {"neutral": text, "given": given, "expected_mm": want_mm, **result}
        if result["ok"]:
            row["echo_same_text"] = re.sub(r"\s+", "", result["value"]["echo"]) == re.sub(r"\s+", "", given)
            row["value_ok"] = _close(result["value"]["value_mm"], want_mm, 1e-4)
        rows.append(row)
    return rows


@_probe("G4", "Dimension expressions bind and how Fusion echoes them",
        keys=["samples", "all_bound", "all_values_right", "echoes_differing_from_given"],
        covers=["G4", "G4-echo"],
        copy_into="the normal form of cad/fusion/runtime/expr.py (extend it with every echo that differs from given)",
        unfavourable="The runtime's normal form absorbs the echo (probe P75.5 of #79 records more).")
def g4(env):
    """Five sample expressions set on dimensions and read back."""
    samples = [("V_A / 2 - MCC_B", 4.0), ("V_A * 2", 20.0), ("(V_A + V_B) / 2", 7.0), ("-(V_B) + V_A", 6.0),
               ("V_A * 3 / 4", 7.5)]
    rows = _dimension_rig(env, "G4", samples, _params("V_A", "V_B", "MCC_B"))
    bound = all(r["ok"] for r in rows)
    values = all(r.get("value_ok") for r in rows)
    differing = [{"given": r["given"], "echo": r["value"]["echo"]} for r in rows if r["ok"] and not r["echo_same_text"]]
    return ("pass" if bound and values else "fail"), {"samples": rows, "all_bound": bound, "all_values_right": values,
                                                      "echoes_differing_from_given": differing}


@_probe("G16", "cos, sin, tan of a deg parameter and min, max with ; inside a dimension expression",
        keys=["samples", "all_bound", "all_values_right"],
        covers=["G16"],
        copy_into="cad.params: minmax_in_fusion and the trigonometric helpers (fusion_facts.json of the runtime)",
        unfavourable="The solver delivers the value as a V_* number instead of the expression.")
def g16(env):
    """Five functional expressions as dimensions; values against the closed form."""
    samples = [("V_A * tan(V_ANG)", 10.0 * math.tan(math.radians(30))), ("V_A * cos(V_ANG)", 10.0 * math.cos(math.radians(30))),
               ("V_A * sin(V_ANG)", 5.0), ("max(V_A, V_B)", 10.0), ("min(V_A, V_B)", 4.0)]
    rows = _dimension_rig(env, "G16", samples, _params("V_A", "V_B", "V_ANG"))
    bound = all(r["ok"] for r in rows)
    values = all(r.get("value_ok") for r in rows)
    return ("pass" if bound and values else "fail"), {"samples": rows, "all_bound": bound, "all_values_right": values}


# ---- G5, G6: sketches and profiles ---------------------------------------------------------------------------------------

G5_NAMES = ("V_PL", "V_PW", "V_PT", "V_CX", "V_CY", "V_D", "V_OD", "V_ID", "V_DX", "V_DY", "V_PU0", "V_PU1", "V_PU2", "V_PU3",
            "V_PU4", "V_PV0", "V_PV1", "V_PV2", "V_PV3", "V_PV4")


def _g5(comp, loops, holes=None, datum=(None, None, None)):
    tag = comp.capitalize()
    return _register("G5", G5_NAMES, _Build(comp, "part", [("body", lambda c: c.extrude(
        f"{tag}_Plate_Body", axis="Z", loops=loops(c), holes=holes(c) if holes else None, start=None, end="V_PT", op="new"))],
                                            datum=datum))


G5_RECT = _g5("Rect", lambda c: [c.rect(None, "V_PL", None, "V_PW")])
G5_CIRCLE = _g5("Circ", lambda c: [c.circle("V_CX", "V_CY", "V_D")])
G5_POLYGON = _g5("Poly", lambda c: [c.polygon([(f"V_PU{k}", f"V_PV{k}") for k in range(5)])])
G5_RING = _g5("Ring", lambda c: [c.circle("V_CX", "V_CY", "V_OD")], holes=lambda c: [c.circle("V_CX", "V_CY", "V_ID")])
G5_DATUM = _g5("Datum", lambda c: [c.rect("V_DX", "V_PL", "V_DY", "V_PW")], datum=("V_DX", "V_DY", None))


@_probe("G5", "Sketches built by plan 3.6 are fully constrained (rectangle, circle, polygon, ring, datum point)",
        keys=["cases", "all_built", "new_point_at_origin"],
        covers=["G5", "G5-shapes", "G5-origin-point"],
        copy_into="nothing if all built; otherwise the error text of the failing case names what to add in fusion_backend.py",
        unfavourable="Add the missing coincident constraints in the backend.")
def g5(env):
    """Five shapes through the kit (the backend asserts fully constrained, healthy and the profile count), plus a
    datum point made where the sketch origin lies."""
    doc = _Doc(env, "G5", _params(*G5_NAMES))
    cases = {}
    for label, build in (("rect", G5_RECT), ("circle", G5_CIRCLE), ("polygon", G5_POLYGON), ("ring", G5_RING),
                         ("datum_off_origin", G5_DATUM)):
        cases[label] = {**doc.run(build), **_facts(doc, build.comp)}

    def origin_point():
        root = doc.design.rootComponent
        sk = root.sketches.add(root.xYConstructionPlane)  # api:71361
        before = sk.sketchPoints.count  # api:72468
        point = sk.sketchPoints.add(adsk.core.Point3D.create(0, 0, 0))  # api:72472
        return {"points_before": before, "points_after": sk.sketchPoints.count,
                "distinct_from_origin_point": point.entityToken != sk.originPoint.entityToken}  # api:130950, 68797

    made = _step(origin_point)
    built = all(case["built"] for case in cases.values())
    merged = made["ok"] and made["value"]["distinct_from_origin_point"]
    return ("pass" if built and merged else "fail"), {"cases": cases, "all_built": built, "new_point_at_origin": made}


G6_NAMES = ("V_PT", "V_SX", "V_SW", "V_SV0", "V_SV1", "V_PITCH", "V_CX", "V_CY", "V_D", "V_OD")
G6_SEPARATE = _register("G6", G6_NAMES, _Build("Sep", "reserve", [("body", lambda c: c.extrude(
    "Sep_Plate_Body", axis="Z", start=None, end="V_PT", op="new",
    loops=[c.rect(f"V_SX + V_PITCH * {k}", f"V_SX + V_PITCH * {k} + V_SW", "V_SV0", "V_SV1") for k in range(3)]))]))
G6_RING_ONE = _register("G6", G6_NAMES, _Build("One", "part", [("body", lambda c: c.extrude(
    "One_Plate_Body", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_OD")], holes=[c.circle("V_CX", "V_CY", "V_D")],
    start=None, end="V_PT", op="new"))]))
G6_RING_TWO = _register("G6", G6_NAMES, _Build("Two", "part", [("body", lambda c: c.extrude(
    "Two_Plate_Body", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_OD")], start=None, end="V_PT", op="new",
    holes=[c.circle("V_CX - V_D / 2", "V_CY", "V_D / 2"), c.circle("V_CX + V_D / 2", "V_CY", "V_D / 2")]))]))


@_probe("G6", "Profile counts: N loops give N profiles, a ring gives one with 1 + holes loops",
        keys=["cases", "counts_as_planned"],
        covers=["G6", "G6-profiles"],
        copy_into="nothing if counts_as_planned; otherwise the backend picks the ring profile by area properties",
        unfavourable="Pick the ring profile by area properties instead.")
def g6(env):
    """Three separate rectangles, a ring with one hole and a ring with two."""
    doc = _Doc(env, "G6", _params(*G6_NAMES))
    records = {}
    for label, build, want in (("three_rectangles", G6_SEPARATE, [1, 1, 1]), ("ring_one_hole", G6_RING_ONE, [1, 2]),
                               ("ring_two_holes", G6_RING_TWO, [1, 1, 3])):
        case = {**doc.run(build), **_facts(doc, build.comp), "expected_loops_per_profile": want}
        case["as_planned"] = bool(case["built"] and case["sketch"] and case["sketch"]["loops_per_profile"] == want)
        records[label] = case
    good = all(r["as_planned"] for r in records.values())
    return ("pass" if good else "fail"), {"cases": records, "counts_as_planned": good}


# ---- G7, G8, G19: joins, cuts, re-joins ------------------------------------------------------------------------------------

G7_NAMES = ("V_PL", "V_PW", "V_PT", "V_RX", "V_RW", "V_RV0", "V_RV1", "V_RH", "V_IX", "V_IW", "V_SV0", "V_SV1")
G7_JOIN = _register("G7", G7_NAMES, _Build("Join", "part", [
    ("plate", lambda c: _plate(c, "Join")),
    ("touching", lambda c: c.extrude("Join_Rib_Add", axis="Z", loops=[c.rect("V_RX", "V_RX + V_RW", "V_RV0", "V_RV1")],
                                     start="V_PT", end="V_PT + V_RH", op="join")),
    ("enclosed", lambda c: c.extrude("Join_Inside_Add", axis="Z", loops=[c.rect("V_IX", "V_IX + V_IW", "V_SV0", "V_SV1")],
                                     start="V_PT / 3", end="V_PT / 3 * 2", op="join"))]))


@_probe("G7", "A join keeps one body; a join fully inside the body is healthy or an error",
        keys=["touching_join", "enclosed_join"],
        covers=["G7"],
        copy_into="nothing if both are ok; if the enclosed join errors the builders avoid fully enclosed joins",
        unfavourable="Builders avoid fully enclosed joins (none is planned).")
def g7(env):
    """A rib on the plate, then a block that lies strictly inside the plate."""
    doc = _Doc(env, "G7", _params(*G7_NAMES))
    c = doc.start(G7_JOIN)
    _step(G7_JOIN.fn("plate"), c)
    answer = {}
    for label, step in (("touching_join", "touching"), ("enclosed_join", "enclosed")):
        result = _step(G7_JOIN.fn(step), c)
        result.pop("value", None)
        comp = doc.comp("Join")
        answer[label] = {**result, "bodies": comp.bRepBodies.count, "volume_mm3": doc.mm3("Join")}
    good = answer["touching_join"]["ok"] and answer["touching_join"]["bodies"] == 1 and answer["enclosed_join"]["ok"]
    return ("pass" if good else "fail"), answer


G8_NAMES = ("V_PL", "V_PW", "V_PT", "V_RH", "V_SX", "V_SW", "V_SV0", "V_SV1")
G8_CUT = _register("G8", G8_NAMES, _Build("Cut", "part", [
    ("plate", lambda c: _plate(c, "Cut")),
    ("slot", lambda c: _slot(c, "Cut")),
    ("air", lambda c: c.extrude("Cut_Air_Cut", axis="Z", loops=[c.rect("V_SX", "V_SX + V_SW", "V_SV0", "V_SV1")],
                                start="V_PT + V_RH", end="V_PT + V_RH * 2", op="cut"))]))


@_probe("G8", "A cut with participantBodies set, and a cut that removes nothing",
        keys=["cut", "empty_cut"],
        covers=["G8"],
        copy_into="documented text only: the error text of empty_cut goes into the kit's notes",
        unfavourable="Documented text only.")
def g8(env):
    """A slot through the plate, then a cut in the air above it."""
    doc = _Doc(env, "G8", _params(*G8_NAMES))
    c = doc.start(G8_CUT)
    _step(G8_CUT.fn("plate"), c)
    before = doc.mm3("Cut")
    cut = _step(G8_CUT.fn("slot"), c)
    cut.pop("value", None)
    cut.update({"volume_before_mm3": before, "volume_after_mm3": doc.mm3("Cut"), "expected_removed_mm3": 4 * 8 * 3})
    empty = _step(G8_CUT.fn("air"), c)
    empty.pop("value", None)
    empty.update({"volume_after_mm3": doc.mm3("Cut"), "bodies": doc.comp("Cut").bRepBodies.count})
    good = cut["ok"] and _close(before - cut["volume_after_mm3"], 96.0, 0.5)
    return ("pass" if good else "fail"), {"cut": cut, "empty_cut": empty}


def _chord_strip_area(radius, width):
    """Area of the part of a disc of ``radius`` that lies in a strip of ``width`` centred on a diameter."""
    h = width / 2.0
    return 2.0 * (h * math.sqrt(radius * radius - h * h) + radius * radius * math.asin(h / radius))


def _ring_bar_added_mm3(od, idia, bar, thickness):
    """Volume a ring (outer ``od``, inner ``idia``) and a bar of width ``bar`` across the opening add inside a round cut."""
    ring = math.pi / 4.0 * (od * od - idia * idia)
    return (ring + _chord_strip_area(idia / 2.0, bar)) * thickness


G19_NAMES = ("V_PL", "V_PW", "V_PT", "V_CX", "V_CY", "V_OD", "V_ID", "V_BARW")
G19_FAN = _register("G19", G19_NAMES, _Build("Fan", "part", [
    ("plate", lambda c: _plate(c, "Fan")),
    ("opening", lambda c: c.extrude("Fan_Open_Cut", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_OD")], start=None,
                                    end="V_PT", op="cut")),
    ("ring", lambda c: c.extrude("Fan_Ring_Rejoin", axis="Z", loops=[c.circle("V_CX", "V_CY", "V_OD")],
                                 holes=[c.circle("V_CX", "V_CY", "V_ID")], start=None, end="V_PT", op="rejoin",
                                 within="Fan_Open_Cut")),
    ("bar", lambda c: c.extrude("Fan_Bar_Rejoin", axis="Z",
                                loops=[c.rect("V_CX - V_OD / 2", "V_CX + V_OD / 2", "V_CY - V_BARW / 2", "V_CY + V_BARW / 2")],
                                start=None, end="V_PT", op="rejoin", within="Fan_Open_Cut"))]))


@_probe("G19", "A ring and a bar re-joined inside a round cut give one healthy body (participantBodies on a join)",
        keys=["rejoin_ring", "rejoin_bar", "bodies", "volume_mm3", "expected_volume_mm3", "volume_matches"],
        covers=["G19", "rejoin-participantBodies"],
        copy_into="nothing if one body; otherwise the re-join phase of the kit needs another strategy (verdict A11)",
        unfavourable="A join may reject or ignore participantBodies; the re-join then drops it in the backend, or the "
                     "ring and bar become one sketch.")
def g19(env):
    """Plate with a round opening; a ring at the rim and a bar across it re-joined through the kit's ``rejoin`` op."""
    doc = _Doc(env, "G19", _params(*G19_NAMES))
    c = doc.start(G19_FAN)
    _step(G19_FAN.fn("plate"), c)
    _step(G19_FAN.fn("opening"), c)
    opening = doc.mm3("Fan")
    first, second = _step(G19_FAN.fn("ring"), c), _step(G19_FAN.fn("bar"), c)
    for step in (first, second):
        step.pop("value", None)
    comp = doc.comp("Fan")
    expected = opening + _ring_bar_added_mm3(40.0, 24.0, 6.0, 3.0)
    volume = doc.mm3("Fan") if comp.bRepBodies.count else None
    matches = _close(volume, expected, 1.0)
    good = first["ok"] and second["ok"] and comp.bRepBodies.count == 1 and matches
    return ("pass" if good else "fail"), {
        "rejoin_ring": {**first, "health": _feature_health(comp, "Fan_Ring_Rejoin")},
        "rejoin_bar": {**second, "health": _feature_health(comp, "Fan_Bar_Rejoin")},
        "bodies": comp.bRepBodies.count, "volume_mm3": volume, "expected_volume_mm3": expected, "volume_matches": matches}


# ---- G9, G10: patterns --------------------------------------------------------------------------------------------------

SLAB_X = _slab_build("G9", "Slab")
SLAB_Y = _slab_build("G9", "Rows", axis="Y")
SLAB_GRID = _slab_build("G9", "Grid", axis2="Y")


@_probe("G9", "Linear pattern of a cut: bare count name, count 1, spacing expression, origin axis, two directions",
        keys=["x_direction", "y_direction", "grid", "falls_back_to_second_set"],
        covers=["G9", "G9-pattern-cut"],
        copy_into="nothing if falls_back_to_second_set is false; otherwise the A11 fallback: the pattern object moves to a "
                  "second set <Owner>_<Set>Rep with its own flag and its count parked at 2",
        unfavourable="Ruled at the gate (A11): the pattern object moves to a second set `<Owner>_<Set>Rep` with its own "
                     "flag, count parked at 2.")
def g9(env):
    """Slots of 96 mm3 in a plate of 18000 mm3; the volume says how many copies lie inside and on which side."""
    doc = _Doc(env, "G9", _params(*SLAB_NAMES))
    plate, slot = 18000.0, 96.0

    def line(build, factor):
        built = doc.run(build)
        name = build.comp
        if not built["built"]:
            return {"build": built}
        pattern = f"{name}_Slot_Pat"
        record = {"build": built, "volume_count_3_mm3": doc.mm3(name), "health_count_3": _feature_health(doc.comp(name), pattern),
                  "expected_count_3_mm3": plate - slot * 3 * factor}
        for count in (1, 3):
            doc.set("V_N_SLOTS", str(count))
            record[f"after_count_{count}"] = {"volume_mm3": doc.mm3(name), "health": _feature_health(doc.comp(name), pattern),
                                              "expected_mm3": plate - slot * count * factor}
        record["count_1_accepted"] = _close(record["after_count_1"]["volume_mm3"], record["after_count_1"]["expected_mm3"], 0.5)
        record["direction_and_count_right"] = _close(record["volume_count_3_mm3"], record["expected_count_3_mm3"], 0.5)
        return record

    x, y, grid = line(SLAB_X, 1), line(SLAB_Y, 1), line(SLAB_GRID, 2)
    good = all(r.get("direction_and_count_right") and r.get("count_1_accepted") for r in (x, y, grid))
    return ("pass" if good else "fail"), {"x_direction": x, "y_direction": y, "grid": grid, "falls_back_to_second_set": not good}


G10_NAMES = ("V_PL", "V_PW", "V_PT", "V_RX", "V_RW", "V_RV0", "V_RV1", "V_RH", "V_PITCH", "V_N_SLOTS", "V_N_POSTS")


def _fin(tag, axis, count, pitch, set_name):
    def seed(c):
        c.extrude(f"{tag}_{set_name}_Add", axis="Z", loops=[c.rect("V_RX", "V_RX + V_RW", "V_RV0", "V_RV1")], start="V_PT",
                  end="V_PT + V_RH", op="join")

    def pattern(c):
        c.pattern(f"{tag}_{set_name}_Pat", seed=f"{tag}_{set_name}_Add", axis=axis, count=count, pitch=pitch)

    return _register("G10", G10_NAMES, _Build(tag, "part", [("plate", lambda c: _plate(c, tag)), ("seed", seed), ("pattern", pattern)]))


G10_RIBS = _fin("Rib", "X", "V_N_SLOTS", "V_PITCH", "Fin")
G10_POSTS = _fin("Post", "Z", "V_N_POSTS", "V_RH", "Stack")


@_probe("G10", "Linear pattern of a join: ribs along X and a stack of posts along Z",
        keys=["ribs", "posts", "explicit_instances_needed"],
        covers=["G10", "G10-pattern-join"],
        copy_into="nothing if explicit_instances_needed is false",
        unfavourable="Explicit instances up to the capacity.")
def g10(env):
    """Rib joins on a plate (18000 mm3, 160 mm3 per rib); posts stacked along plus Z (a wrong direction changes the volume)."""
    doc = _Doc(env, "G10", _params(*G10_NAMES))
    answer = {}
    for label, build, pattern in (("ribs", G10_RIBS, "Rib_Fin_Pat"), ("posts", G10_POSTS, "Post_Stack_Pat")):
        record = doc.run(build)
        comp = doc.comp(build.comp)
        record["bodies"] = comp.bRepBodies.count if comp is not None else None
        if record["built"]:
            record.update(volume_mm3=doc.mm3(build.comp), expected_mm3=18000.0 + 3 * 160.0, health=_feature_health(comp, pattern))
        answer[label] = record
    good = all(r["built"] and r["bodies"] == 1 and _close(r["volume_mm3"], r["expected_mm3"], 0.5) for r in answer.values())
    return ("pass" if good else "fail"), {**answer, "explicit_instances_needed": not good}


# ---- G11: lofts ------------------------------------------------------------------------------------------------------------

G11_NAMES = ("V_PL", "V_PW", "V_PT", "V_LA0", "V_LA1", "V_LB0", "V_LB1", "V_LV0", "V_LV1", "V_LH", "V_CX", "V_CY", "V_DA")


def _trapezoid_area(p):
    """Area of the section polygon (bottom edge A0..A1, top edge B0..B1, from V0 to V1) in mm2."""
    return ((p["V_LA1"] - p["V_LA0"]) + (p["V_LB1"] - p["V_LB0"])) / 2.0 * (p["V_LV1"] - p["V_LV0"])


def _frustum(a1, a2, h):
    """Volume of a frustum between similar parallel sections of areas ``a1`` and ``a2`` a distance ``h`` apart."""
    return h / 3.0 * (a1 + a2 + math.sqrt(a1 * a2))


def _loft_expected(kind, values, h):
    """Volume of the loft solid of height ``h``: section B is section A scaled by one half about the origin."""
    a1 = _trapezoid_area(values) if kind == "trap" else math.pi * (values["V_DA"] / 2.0) ** 2
    return _frustum(a1, a1 / 4.0, h)


def _loft(tag, kind, op, at_a, at_b):
    name = f"{tag}_Loft_{'Add' if op == 'join' else 'Cut'}"

    def step(c):
        if kind == "trap":
            a = c.polygon([("V_LA0", "V_LV0"), ("V_LA1", "V_LV0"), ("V_LB1", "V_LV1"), ("V_LB0", "V_LV1")])
            b = c.polygon([("V_LA0 / 2", "V_LV0 / 2"), ("V_LA1 / 2", "V_LV0 / 2"), ("V_LB1 / 2", "V_LV1 / 2"), ("V_LB0 / 2", "V_LV1 / 2")])
        else:
            a, b = c.circle("V_CX", "V_CY", "V_DA"), c.circle("V_CX", "V_CY", "V_DA / 2")
        c.loft(name, axis="Z", loop_a=a, at_a=at_a, loop_b=b, at_b=at_b, op=op)

    return _register("G11", G11_NAMES, _Build(tag, "part", [("plate", lambda c: _plate(c, tag)), ("loft", step)])), name


G11_CASES = [
    ("trapezoid_join", "trap", "join", "V_LH", "20 mm", *_loft("Tj", "trap", "join", "V_PT", "V_PT + V_LH")),
    ("trapezoid_cut", "trap", "cut", "V_LA1", "60 mm", *_loft("Tc", "trap", "cut", None, "V_PT")),
    ("circle_join", "circle", "join", "V_LH", "20 mm", *_loft("Cj", "circle", "join", "V_PT", "V_PT + V_LH")),
    ("circle_cut", "circle", "cut", "V_DA", "30 mm", *_loft("Cc", "circle", "cut", None, "V_PT")),
]


@_probe("G11", "Lofts between two similar sections as join and as cut: volume, face types, health after a change",
        keys=["cases", "all_match_closed_form", "face_types_are_ruled"],
        covers=["G11", "G11-loft"],
        copy_into="nothing if the volumes match; otherwise risk R81.4 of the plan",
        unfavourable="See R81.4.")
def g11(env):
    """Two trapezoid lofts and two circle lofts (join on top of the plate, cut through it), each against its closed form."""
    base = _params(*G11_NAMES)
    doc = _Doc(env, "G11", base)
    values = {n: v for n, (v, u) in base.items()}
    plate = 18000.0
    cases, matches, ruled = {}, [], []
    for label, kind, op, change, new, build, feature in G11_CASES:
        record = doc.run(build)
        comp = doc.comp(build.comp)
        record["bodies"] = comp.bRepBodies.count if comp is not None else None
        if record["built"]:
            def expected(v):
                solid = _loft_expected(kind, v, v["V_LH"] if op == "join" else v["V_PT"])
                return plate + solid if op == "join" else plate - solid

            record["volume_mm3"], record["expected_mm3"] = doc.mm3(build.comp), expected(values)
            body = comp.bRepBodies.item(0)
            seen = {}
            for i in range(body.faces.count):  # api:16620, 19055
                kind_of = str(body.faces.item(i).geometry.surfaceType)  # api:19047, 18544, core:23134
                seen[kind_of] = seen.get(kind_of, 0) + 1
            record["surface_types"] = seen
            record["planar_faces"] = seen.get(str(adsk.core.SurfaceTypes.PlaneSurfaceType), 0)  # core:2098
            record["cone_faces"] = seen.get(str(adsk.core.SurfaceTypes.ConeSurfaceType), 0)  # core:2100
            record["health"] = _feature_health(comp, feature)
            doc.set(change, new)
            after = {**values, change: float(new.split()[0])}
            record["after_change"] = {"parameter": change, "expression": new, "volume_mm3": doc.mm3(build.comp),
                                      "expected_mm3": expected(after), "health": _feature_health(comp, feature)}
            doc.set(change, f"{values[change]} mm")
            fits = [_close(record["volume_mm3"], record["expected_mm3"], max(1.0, 0.002 * record["expected_mm3"])),
                    _close(record["after_change"]["volume_mm3"], record["after_change"]["expected_mm3"],
                           max(1.0, 0.002 * record["after_change"]["expected_mm3"]))]
            matches.append(all(fits))
            ruled.append(record["planar_faces"] >= 6 if kind == "trap" else record["cone_faces"] >= 1)
        else:
            matches.append(False)
            ruled.append(False)
        cases[label] = record
    return ("pass" if all(matches) else "fail"), {"cases": cases, "all_match_closed_form": all(matches),
                                                  "face_types_are_ruled": all(ruled)}


# ---- G12, G13: suppression and parameter sets --------------------------------------------------------------------------


def _suppress(timeline_object, flag) -> None:
    timeline_object.isSuppressed = flag  # api:77985 (setter)


@_probe("G12", "Suppression through TimelineObject.isSuppressed: sketch, cut, pattern and construction plane",
        keys=["suppressible", "rest_healthy_when_set_suppressed", "volume_when_suppressed_mm3", "restored",
              "volume_restored_mm3", "plane"],
        covers=["G12"],
        copy_into="cad/fusion/runtime/fusion_facts.json: suppress_kinds (the kinds that report true)",
        unfavourable="The runtime suppresses features and patterns only; parked values keep sketches valid (R81.3).")
def g12(env):
    """Suppress every member of one set (pattern, cut, sketch), check the plate, unsuppress, compare volumes."""
    doc = _Doc(env, "G12", _params(*SLAB_NAMES))
    doc.run(SLAB_X)
    comp = doc.comp("Slab")
    before = doc.mm3("Slab")
    timeline = doc.design.timeline  # api:103221
    objects = [timeline.item(i) for i in range(timeline.count)]  # api:77786, 77773
    members = [o for o in objects if o.name.startswith("Slab_Slot_")]  # api:78073
    kinds = {}
    for obj in reversed(members):
        kinds[_short(obj.entity.objectType)] = _step(_suppress, obj, True)  # api:78030, core:584
    rest = [o for o in objects if not o.name.startswith("Slab_Slot_")]  # names, not proxies: SWIG hands out new objects
    states = [_attempt(lambda o=o: _healthy(o.entity.healthState)) for o in rest]  # api:36024, 68828
    healthy = [state for ok, state in states if ok]  # an entity with no health state is left out
    suppressed = doc.mm3("Slab") if comp.bRepBodies.count else None
    for obj in members:
        _attempt(_suppress, obj, False)
    restored = doc.mm3("Slab") if comp.bRepBodies.count else None

    def plane():
        made = _offset_plane(doc.design.rootComponent, "XY", "50 mm")
        step = _step(_suppress, made.timelineObject, True)  # api:27238
        _attempt(_suppress, made.timelineObject, False)
        return step

    plane_step = _step(plane)
    everything = all(s["ok"] for s in kinds.values()) and len(kinds) >= 3
    good = everything and all(healthy) and _close(suppressed, 18000.0, 0.5) and _close(restored, before, 0.5)
    return ("pass" if good else "fail"), {
        "suppressible": {k: v["ok"] for k, v in kinds.items()}, "details": kinds, "rest_healthy_when_set_suppressed": all(healthy),
        "volume_when_suppressed_mm3": suppressed, "restored": _close(restored, before, 0.5), "volume_restored_mm3": restored,
        "plane": plane_step}


@_probe("G13", "Apply a second parameter set and the first again: same volume",
        keys=["volume_a_mm3", "volume_b_mm3", "volume_a_again_mm3", "same_after_round_trip", "b_as_expected"],
        covers=["G13"],
        copy_into="nothing if same_after_round_trip; otherwise fundamental, reported to the architect",
        unfavourable="Fundamental; reported to the architect.")
def g13(env):
    """Set A (3 slots at pitch 20), set B (1 slot at pitch 30), set A again."""
    doc = _Doc(env, "G13", _params(*SLAB_NAMES))
    doc.run(SLAB_X)
    a = doc.mm3("Slab")
    doc.set("V_N_SLOTS", "1")
    doc.set("V_PITCH", "30 mm")
    b = doc.mm3("Slab")
    doc.set("V_N_SLOTS", "3")
    doc.set("V_PITCH", "20 mm")
    again = doc.mm3("Slab")
    same = _close(a, again, 1e-3)
    expected = _close(b, 18000.0 - 96.0, 0.5)
    return ("pass" if same and expected else "fail"), {"volume_a_mm3": a, "volume_b_mm3": b, "volume_a_again_mm3": again,
                                                      "same_after_round_trip": same, "b_as_expected": expected}


# ---- G14, G15, G18: numbers, parameters, time --------------------------------------------------------------------------

G14_NAMES = ("V_XL", "V_XW", "V_XH", "V_HD")
G14_BOX = _register("G14", G14_NAMES, _Build("Box", "part", [
    ("body", lambda c: c.extrude("Box_Main_Body", axis="Z", loops=[c.rect(None, "V_XL", None, "V_XW")], start=None, end="V_XH", op="new")),
    ("hole", lambda c: c.extrude("Box_Hole_Cut", axis="Z", loops=[c.circle("V_XL / 2", "V_XW / 2", "V_HD")], start=None,
                                 end="V_XH", op="cut"))]))


@_probe("G14", "Accuracy of BRepBody.volume and getPhysicalProperties on a box with a cylinder hole",
        keys=["exact_mm3", "body_volume_mm3", "by_accuracy", "best_relative_error"],
        covers=["G14"],
        copy_into="the runtime's measure gate (tolerances of P79.6): choose the accuracy level whose error fits",
        unfavourable="The runtime measures on the exported mesh only.")
def g14(env):
    """Box 40 x 30 x 10 with a through hole of 10 mm: 12000 - pi * 25 * 10 mm3."""
    doc = _Doc(env, "G14", _params(*G14_NAMES))
    built = doc.run(G14_BOX)
    exact = 12000.0 - math.pi * 25.0 * 10.0
    comp = doc.comp("Box")
    if comp is None or comp.bRepBodies.count == 0:
        return "fail", {"exact_mm3": exact, "body_volume_mm3": None, "by_accuracy": {}, "best_relative_error": None, "build": built}
    body = comp.bRepBodies.item(0)
    levels = {"low": adsk.fusion.CalculationAccuracy.LowCalculationAccuracy,  # api:1368
              "medium": adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy,  # api:1369
              "high": adsk.fusion.CalculationAccuracy.HighCalculationAccuracy,  # api:1370
              "very_high": adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy}  # api:1371
    by = {}
    for label, level in levels.items():
        step = _step(lambda level=level: float(body.getPhysicalProperties(level).volume) * 1000.0)  # api:16992, 56187
        by[label] = {**step, "relative_error": abs(step["value"] - exact) / exact if step["ok"] else None}
    default = float(body.volume) * 1000.0  # api:16652
    errors = [v["relative_error"] for v in by.values() if v["relative_error"] is not None]
    return "info", {"exact_mm3": exact, "body_volume_mm3": default, "body_volume_relative_error": abs(default - exact) / exact,
                    "by_accuracy": by, "best_relative_error": min(errors) if errors else None, "build": built}


_LITERAL = re.compile(r"^\s*-?[0-9]+(\.[0-9]+)?\s*[a-z]*\s*$")
G15_NAMES = tuple(dict.fromkeys(SLAB_NAMES + G11_NAMES))
G15_CONE = _register("G15", G15_NAMES, _Build("Cone", "part", [
    ("plate", lambda c: _plate(c, "Cone")),
    ("loft", lambda c: c.loft("Cone_Loft_Cut", axis="Z",
                              loop_a=c.polygon([("V_LA0", "V_LV0"), ("V_LA1", "V_LV0"), ("V_LB1", "V_LV1"), ("V_LB0", "V_LV1")]), at_a=None,
                              loop_b=c.polygon([("V_LA0 / 2", "V_LV0 / 2"), ("V_LA1 / 2", "V_LV0 / 2"), ("V_LB1 / 2", "V_LV1 / 2"),
                                                ("V_LB0 / 2", "V_LV1 / 2")]), at_b="V_PT", op="cut"))]))


@_probe("G15", "Model parameters that Fusion creates by itself (role, created by, expression)",
        keys=["parameters", "implicit_literals"],
        covers=["G15"],
        copy_into="cad/fusion/runtime/fusion_facts.json: implicit_literals (type, role, expression of each)",
        unfavourable="Feeds the allow-list of the runtime's literal gate.")
def g15(env):
    """Every parameter of a document with a two-direction pattern and a loft; the literal model parameters are listed."""
    doc = _Doc(env, "G15", _params(*G15_NAMES))
    built = [doc.run(SLAB_GRID), doc.run(G15_CONE)]
    every = doc.design.allParameters  # api:103229
    rows, literals = [], []
    for i in range(every.count):  # api:54730
        p = every.item(i)  # api:54713
        kind = _short(p.objectType)  # core:584
        row = {"name": p.name, "kind": kind, "expression": p.expression}  # api:54483, 54435
        if kind == "ModelParameter":
            role = _step(lambda p=p: str(p.role))  # api:113872
            owner = _step(lambda p=p: _short(p.createdBy.objectType))  # api:113879
            row["role"] = role.get("value", role.get("error"))
            row["created_by"] = owner.get("value", owner.get("error"))
            row["literal"] = bool(_LITERAL.match(str(p.expression)))
            if row["literal"]:
                literals.append({"type": row["created_by"], "role": row["role"], "expression": row["expression"]})
        rows.append(row)
    unique = [dict(t) for t in {tuple(sorted(d.items())) for d in literals}]
    return "info", {"parameters": rows, "implicit_literals": sorted(unique, key=str), "builds": built}


def _set_name(obj, name):
    """Set ``obj.name`` and read it back (how Fusion treats a duplicate is the answer)."""
    obj.name = name  # api:68414, 27157, 35914
    return obj.name


@_probe("G17", "Names: three-token names are accepted, what a duplicate becomes, the occurrence's own name",
        keys=["accepted", "duplicate", "occurrence_name_after_component_rename"],
        covers=["G17", "G17-names", "occurrence-name"],
        copy_into="nothing if accepted is all true and a duplicate is refused or renamed visibly (the backend reads names back)",
        unfavourable="The facade already forbids duplicates.")
def g17(env):
    """Sketch, plane and feature names set and read back; a duplicate set on a second object."""
    design = _new(env, "G17")
    comp = design.rootComponent
    plane = comp.xYConstructionPlane
    accepted, duplicate = {}, {}
    sketches = [comp.sketches.add(plane) for _ in range(2)]  # api:71361
    planes = [_offset_plane(comp, "XY", f"{5 * (k + 1)} mm") for k in range(2)]
    features = [_extrude(comp, _circle_profile(comp, plane, 1.0 + k), None, "5 mm") for k in range(2)]
    for label, pair in (("sketch", sketches), ("plane", planes), ("feature", features)):
        wanted = f"Test_{label.capitalize()}_Name"
        pair[0].name = wanted  # api:68414, 27157, 35914
        accepted[label] = pair[0].name == wanted
        second = _step(_set_name, pair[1], wanted)
        duplicate[label] = {"second_name": second.get("value"), "refused": not second["ok"], "error": second.get("error"),
                            "renamed": second["ok"] and second["value"] != wanted}
    occurrence = comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())  # api:89686, 53546, core:16525
    occurrence.component.name = "Base"  # api:89679
    return ("pass" if all(accepted.values()) else "fail"), {
        "accepted": accepted, "duplicate": duplicate,
        "occurrence_name_after_component_rename": occurrence.name,  # api:52683
        "component_name": occurrence.component.name}


G18_NAMES = ("V_PL", "V_PWL", "V_PT", "V_SX", "V_SW", "V_PITCH", "V_N_SLOTS", "V_ROW", "V_RS")


def _row_step(k):
    def step(c):
        tag = f"R{k:02d}"
        c.extrude(f"Rows_{tag}_Cut", axis="Z", loops=[c.rect("V_SX", "V_SX + V_SW", f"V_ROW * {k}", f"V_ROW * {k} + V_RS")],
                  start=None, end="V_PT", op="cut")
        c.pattern(f"Rows_{tag}_Pat", seed=f"Rows_{tag}_Cut", axis="X", count="V_N_SLOTS", pitch="V_PITCH")

    return step


G18_ROWS = _register("G18", G18_NAMES, _Build("Rows", "part", [
    ("plate", lambda c: c.extrude("Rows_Plate_Body", axis="Z", loops=[c.rect(None, "V_PL", None, "V_PWL")], start=None,
                                  end="V_PT", op="new"))] + [(f"row{k:02d}", _row_step(k)) for k in range(1, 51)]))


@_probe("G18", "Time to build about 150 timeline objects (50 patterned cuts) and to recompute after a parameter change",
        keys=["timeline_objects", "build_seconds", "seconds_per_object", "recompute_seconds", "volume_after_mm3",
              "expected_after_mm3", "healthy_after_change"],
        covers=["G18"],
        copy_into="the time-out default of the build job; if recompute is slow, set the pattern compute option to Identical",
        unfavourable="Pattern compute option Identical; fewer, larger sketches.")
def g18(env):
    """A plate of 400 mm and 50 rows of three slots; then the pitch and the count change."""
    doc = _Doc(env, "G18", _params(*G18_NAMES))
    started = time.perf_counter()
    built = doc.run(G18_ROWS)
    build_seconds = time.perf_counter() - started
    comp = doc.comp("Rows")
    objects = doc.design.timeline.count  # api:103221, 77786
    after = recompute = None
    if built["built"]:
        started = time.perf_counter()
        doc.set("V_PITCH", "22 mm")
        doc.set("V_N_SLOTS", "2")
        recompute = time.perf_counter() - started
        after = doc.mm3("Rows")
    expected = 100.0 * 400.0 * 3.0 - 50 * 2 * 4 * 4 * 3  # the plate less 50 rows of two slots of 4 x 4 x 3 mm
    healthy = built["built"] and all(_feature_health(comp, f"Rows_R{k:02d}_Pat") == "healthy" for k in (1, 25, 50))
    return "info", {"build": built, "timeline_objects": objects, "build_seconds": build_seconds,
                    "seconds_per_object": build_seconds / objects if objects else None, "recompute_seconds": recompute,
                    "volume_after_mm3": after, "expected_after_mm3": expected, "healthy_after_change": healthy}


# ---- the dimension text point and the text ------------------------------------------------------------------------------


@_probe("U-DIMTEXT", "A dimension's text point is accepted wherever it falls",
        keys=["positions", "all_accepted"],
        covers=["dimension-text-points"],
        copy_into="nothing if all_accepted; otherwise _Sketcher.text_point of fusion_backend.py needs a rule",
        unfavourable="A rule for the text point of the backend.")
def u_dimtext(env):
    """The same dimension with its text point beside, on, far from and at the origin of the geometry."""
    design = _new(env, "U-DIMTEXT")
    sk = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)  # api:71361
    positions = {"beside": (0.5, 0.5), "on_geometry": (0.5, 0.0), "far_away": (500.0, -500.0), "at_origin": (0.0, 0.0)}
    out = {}
    for k, (label, (x, y)) in enumerate(positions.items()):
        def one(k=k, x=x, y=y):
            line = sk.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0, 5.0 * (k + 1), 0),
                                                             adsk.core.Point3D.create(1, 5.0 * (k + 1), 0))  # api:72162
            dim = sk.sketchDimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint,
                                                           adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                                                           adsk.core.Point3D.create(x, 5.0 * (k + 1) + y, 0))  # api:70547, 2071
            return {"value_mm": _mm(dim.parameter.value)}  # api:70263, 54415

        out[label] = _step(one)
    everything = all(v["ok"] for v in out.values())
    return ("pass" if everything else "fail"), {"positions": out, "all_accepted": everything}


# expected stem side (sign along the first in-plane model axis) of a capital L read from plus axis (plan 3.14):
# the viewer looks against plus axis, right = forward x up; foot at the bottom, so the v sign is -1 for all three
TEXT_FACES = {"Z": {"u": "X", "v": "Y", "stem": -1}, "Y": {"u": "X", "v": "Z", "stem": 1}, "X": {"u": "Y", "v": "Z", "stem": -1}}
FACE_PARAM = {"Z": "V_BH", "Y": "V_PW", "X": "V_PL"}
FACE_CM = {"Z": 3.0, "Y": 6.0, "X": 10.0}  # the faces of the box (V_BH, V_PW, V_PL) in centimetres
TEXT_NAMES = ("V_PL", "V_PW", "V_BH", "V_TU0", "V_TU1", "V_TV0", "V_TV1", "V_TD", "V_TH")


def _text_build(font="Arial") -> _Build:
    def text(axis):
        top = FACE_PARAM[axis]
        return lambda c: c.text(f"Box_Text{axis}_TextCut", axis=axis, frame=c.rect("V_TU0", "V_TU1", "V_TV0", "V_TV1"),
                                start=f"{top} - V_TD", end=top, string="L", height="V_TH", halign="center", valign="middle",
                                font=font, style="regular", op="cut")

    return _Build("Box", "part", [("body", lambda c: c.extrude("Box_Main_Body", axis="Z", loops=[c.rect(None, "V_PL", None, "V_PW")],
                                                               start=None, end="V_BH", op="new")),
                                  ("textZ", text("Z")), ("textY", text("Y")), ("textX", text("X"))])


G_TEXT = _register("U-TEXT", TEXT_NAMES, _text_build())


def _pocket_face(body, axis, depth_cm):
    """The planar face of a pocket whose plane lies at ``depth_cm`` along ``axis``: its centroid and box centre (mm)."""
    index = AXIS_INDEX[axis]
    for i in range(body.faces.count):  # api:16620, 19055
        face = body.faces.item(i)  # api:19047
        geometry = face.geometry  # api:18544
        if geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:  # core:23134, 2098
            continue
        origin = geometry.origin  # core:39585
        if abs([origin.x, origin.y, origin.z][index] - depth_cm) > 1e-4:
            continue
        box = face.boundingBox  # api:18627
        centre = [(a + b) / 2.0 for a, b in zip((box.minPoint.x, box.minPoint.y, box.minPoint.z),
                                                (box.maxPoint.x, box.maxPoint.y, box.maxPoint.z))]
        c = face.centroid  # api:18631
        return [_mm(v) for v in (c.x, c.y, c.z)], [_mm(v) for v in centre], _mm(face.area)  # api:18623
    return None


def _font(env):
    names = list(env.app.fontNames)  # core:5340
    for wanted in ("Arial", "Segoe UI", "Liberation Sans"):
        if wanted in names:
            return wanted
    return str(names[0]) if names else "Arial"


@_probe("U-TEXT", "Sketch text: createInput3, multi-line frame, construction lines, flip rule, cut through a SketchText",
        keys=["font", "faces", "all_unmirrored", "all_upright", "sketch_after_text"],
        covers=["text"],
        copy_into="fusion_backend.py _text: the flip rule (isHorizontalFlip from PLANE_NORMAL) is right when all_unmirrored; "
                  "otherwise the answer names which face is mirrored",
        unfavourable="Text and the height are taken from the builder's record only; #83 is told before it builds the coupons.")
def u_text(env):
    """A box with a capital L cut into three faces (plus X, Y, Z); the pocket floor's centroid against its box centre
    says which way the L reads from outside."""
    with _plane_normal(env) as normals:
        doc = _Doc(env, "U-TEXT", _params(*TEXT_NAMES))
        font = _font(env)
        build = _text_build(font)
        c = doc.start(build)
        _step(build.fn("body"), c)
        faces, unmirrored, upright = {}, [], []
        for axis in ("Z", "Y", "X"):
            record = _step(build.fn(f"text{axis}"), c)
            record.pop("value", None)
            body = doc.comp("Box").bRepBodies.item(0)
            found = _pocket_face(body, axis, FACE_CM[axis] - 0.2) if record["ok"] else None  # the pocket floor, V_TD = 2 mm deep
            record["pocket_found"] = found is not None
            if found is not None:
                centroid, centre, area = found
                plane = TEXT_FACES[axis]
                du = centroid[AXIS_INDEX[plane["u"]]] - centre[AXIS_INDEX[plane["u"]]]
                dv = centroid[AXIS_INDEX[plane["v"]]] - centre[AXIS_INDEX[plane["v"]]]
                record.update(area_mm2=area, centroid_minus_box_centre_mm={plane["u"]: du, plane["v"]: dv},
                              stem_side=f"{'+' if du > 0 else '-'}{plane['u']}",
                              expected_stem_side=f"{'+' if plane['stem'] > 0 else '-'}{plane['u']}",
                              unmirrored=(du > 0) == (plane["stem"] > 0) and abs(du) > 0.05, upright=dv < -0.05)
            faces[axis] = record
            unmirrored.append(bool(record.get("unmirrored")))
            upright.append(bool(record.get("upright")))
        comp = doc.comp("Box")
        sketch = comp.sketches.item(comp.sketches.count - 1)  # api:71340
        lines = sketch.sketchCurves.sketchLines  # api:68426
        after = {"sketch": sketch.name, "fully_constrained": bool(sketch.isFullyConstrained),  # api:68804
                 "texts": sketch.sketchTexts.count,  # api:68789, 72932
                 "text_flip_read_back": _step(lambda: bool(sketch.sketchTexts.item(0).isHorizontalFlip)),  # api:72924, 131727
                 "frame_lines_construction": [bool(lines.item(i).isConstruction) for i in range(lines.count)]}  # api:72150, 72158, 151757
        good = all(unmirrored) and all(upright)
        return ("pass" if good else "fail"), {"font": font, "plane_normal_used": normals, "faces": faces, "all_unmirrored": all(unmirrored),
                                              "all_upright": all(upright), "sketch_after_text": after}
