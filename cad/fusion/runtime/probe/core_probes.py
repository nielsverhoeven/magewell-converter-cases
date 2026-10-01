"""Probes of the runtime: what only a live Fusion can answer. One run answers all of them.

Imports adsk. Order matters: P79.7 measures Fusion's implicit literals, P75.1 builds the test document with
that list.
"""
import math
import os
import re
import struct
import sys
import threading
import time

import adsk.core
import adsk.fusion

from .. import build, expr, fusion_app, fusion_port, plan as planmod, registry
from ..testdoc import builder as testdoc_builder, expected

TESTDOC_PLAN = "cad/fusion/runtime/testdoc/plan.json"
ECHO_SAMPLES = ["PRB_A*2+PRB_B", "( PRB_A + PRB_B ) / 2", "PRB_A - (PRB_B - PRB_A)", "PRB_A / 2", "2 * PRB_A",
                "PRB_A * 1.50", "PRB_A + PRB_B + PRB_A", "-PRB_A + PRB_B * 2", "PRB_A / (PRB_B / PRB_A)",
                "12.345678901 mm", "3.0 mm"]


def _vi(text):
    return adsk.core.ValueInput.createByString(text)


def _add(design, name, text, unit="mm"):
    try:
        return design.userParameters.add(name, _vi(text), unit, "")
    except RuntimeError:
        return None


def _cache(env):
    if not hasattr(env, "cache"):
        env.cache = {}
    return env.cache


# ---- P79.1 ----------------------------------------------------------------------------------------------------
def host(env):
    a = env.app
    ui = a.userInterface
    workspace = ui.activeWorkspace
    return {"fusion_version": a.version, "python": sys.version, "executable": sys.executable,
            "adsk_core_file": adsk.core.__file__, "thread": threading.current_thread().name,
            "is_main_thread": threading.current_thread() is threading.main_thread(),
            "original_stdout": type(sys.__stdout__).__name__, "open_documents": a.documents.count,
            "active_command": ui.activeCommand, "active_workspace": workspace.id if workspace else None,
            "is_startup_complete": a.isStartupComplete, "z_up": fusion_app.is_z_up(),
            "host": env.job.get("host")}


# ---- P79.2 ----------------------------------------------------------------------------------------------------
def document_lifecycle(env):
    a = env.app
    before = a.documents.count
    previous = a.activeDocument
    doc, design = env.new_design("mcc-probe-lifecycle")
    facts = {"count_before": before, "count_open": a.documents.count, "is_saved": doc.isSaved,
             "is_active": doc.isActive, "name": doc.name, "creation_id_present": bool(doc.creationId),
             "design_type_parametric": design.designType == adsk.fusion.DesignTypes.ParametricDesignType,
             "design_intent_hybrid": design.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType,
             "unit_mm": design.fusionUnitsManager.distanceDisplayUnits == adsk.fusion.DistanceUnits.MillimeterDistanceUnits,
             "default_length_units": design.fusionUnitsManager.defaultLengthUnits}
    facts["closed"] = bool(doc.close(False))
    facts["count_after"] = a.documents.count
    if previous is not None and previous.isValid:
        facts["previous_reactivated"] = bool(previous.activate()) if not previous.isActive else True
    ok = facts["closed"] and facts["count_after"] == before and not facts["is_saved"] \
        and facts["design_type_parametric"] and facts["unit_mm"]
    return dict(facts, status="pass" if ok else "fail")


# ---- P79.3 ----------------------------------------------------------------------------------------------------
def frame(env):
    doc, design = env.new_design("mcc-probe-frame")
    viewport = env.app.activeViewport
    up, eye = viewport.frontUpDirection, viewport.frontEyeDirection
    data = {"preference_z_up": fusion_app.is_z_up(), "front_up": [up.x, up.y, up.z],
            "front_eye": [eye.x, eye.y, eye.z], "viewport_belongs_to_document":
                viewport.parentDocument.creationId == doc.creationId,
            "viewport_size": [viewport.width, viewport.height]}
    return dict(data, status="pass" if data["preference_z_up"] and abs(up.z - 1.0) < 1e-6 else "fail")


# ---- P79.4 ----------------------------------------------------------------------------------------------------
def modal_guard(env):
    try:
        env.ui.messageBox("If you can read this, the modal guard does not work. Click OK.")
    except fusion_app.ModalBlocked:
        return {"status": "pass", "blocked": True}
    return {"status": "fail", "blocked": False}


# ---- P79.5 ----------------------------------------------------------------------------------------------------
def parameters(env):
    doc, design = env.new_design("mcc-probe-parameters")
    ups = design.userParameters
    out = {"add_mm": _add(design, "PRB_A", "3 mm") is not None,
           "add_deg": _add(design, "PRB_ANGLE", "30 deg", "deg") is not None,
           "add_unitless": _add(design, "PRB_N", "4", "") is not None,
           "add_expression": _add(design, "PRB_B", "PRB_A * 2") is not None,
           "forward_reference_rejected": _add(design, "PRB_C", "PRB_LATER / 2") is None}
    try:
        long_comment = ups.add("PRB_LONG", _vi("1 mm"), "mm", "x" * 300)
        out["comment_300_chars"] = long_comment is not None and len(long_comment.comment)
    except RuntimeError as exc:
        out["comment_300_chars"] = "rejected: %s" % exc
    a, b = ups.itemByName("PRB_A"), ups.itemByName("PRB_B")
    out["units_read_back"] = {"PRB_A": a.unit, "PRB_ANGLE": ups.itemByName("PRB_ANGLE").unit,
                              "PRB_N": ups.itemByName("PRB_N").unit}
    out["value_is_cm"] = abs(a.value - 0.3) < 1e-12
    try:
        ok = design.modifyParameters([a, b], [_vi("4 mm"), _vi("PRB_NOPE * 2")])
    except RuntimeError as exc:
        ok, out["modify_bad_exception"] = False, str(exc)
    out["modify_bad_returns_false"] = not ok
    out["modify_bad_changed_nothing"] = abs(a.value - 0.3) < 1e-12
    out["modify_good"] = bool(design.modifyParameters([a], [_vi("4 mm")])) and abs(a.value - 0.4) < 1e-12
    t0 = time.monotonic()
    for n in range(200):
        ups.add("PRB_T%03d" % n, _vi("%d mm" % (n + 1)), "mm", "")
    out["seconds_200_adds"] = round(time.monotonic() - t0, 3)
    good = out["add_mm"] and out["add_deg"] and out["add_unitless"] and out["add_expression"] \
        and out["forward_reference_rejected"] and out["modify_bad_changed_nothing"] and out["modify_good"]
    return dict(out, status="pass" if good else "fail")


# ---- P75.3 ----------------------------------------------------------------------------------------------------
def min_max(env):
    doc, design = env.new_design("mcc-probe-minmax")
    _add(design, "PRB_A", "3 mm")
    _add(design, "PRB_B", "5 mm")
    _add(design, "PRB_ANGLE", "30 deg", "deg")
    out = {}
    for name, text, want_cm in (("PRB_MAX_SEMI", "max(PRB_A; PRB_B)", 0.5), ("PRB_MIN_SEMI", "min(PRB_A; PRB_B)", 0.3),
                                ("PRB_MAX_COMMA", "max(PRB_A, PRB_B)", 0.5), ("PRB_TAN", "PRB_B * tan(PRB_ANGLE)",
                                                                              0.5 * math.tan(math.radians(30))),
                                ("PRB_COS", "PRB_B * cos(PRB_ANGLE)", 0.5 * math.cos(math.radians(30)))):
        p = _add(design, name, text)
        out[name] = {"text": text, "accepted": p is not None, "echo": p.expression if p else None,
                     "value_ok": p is not None and abs(p.value - want_cm) < 1e-9}
    ok = out["PRB_MAX_SEMI"]["value_ok"] and out["PRB_MIN_SEMI"]["value_ok"]
    _cache(env)["minmax_in_fusion"] = ok
    return dict(out, status="pass" if ok else "fail")


# ---- P75.5 ----------------------------------------------------------------------------------------------------
def expression_echo(env):
    doc, design = env.new_design("mcc-probe-echo")
    _add(design, "PRB_A", "3 mm")
    _add(design, "PRB_B", "5 mm")
    rows, all_same = [], True
    for n, text in enumerate(ECHO_SAMPLES):
        p = _add(design, "PRB_E%02d" % n, text)
        echo = p.expression if p is not None else None
        try:
            same = echo is not None and expr.normalise(echo) == expr.normalise(text)
            normal = expr.normalise(echo) if echo is not None else None
        except expr.ExprError as exc:
            same, normal = False, "not parsed: %s" % exc
        all_same = all_same and same
        rows.append({"given": text, "echo": echo, "normal_form_of_echo": normal, "same_normal_form": same})
    angle = _add(design, "PRB_ANGLE", "45.0 deg", "deg")
    rows.append({"given": "45.0 deg", "echo": angle.expression if angle else None})
    return {"status": "pass" if all_same else "fail", "samples": rows}


# ---- P79.7 ----------------------------------------------------------------------------------------------------
def implicit_literals(env):
    """Every model parameter of the test document. The literal ones are Fusion's own defaults: the builder
    binds every dimension it sets to a parameter expression."""
    doc, design = env.new_design("mcc-probe-literals")
    _add_testdoc_parameters(env, design)
    testdoc_builder._build_fusion(design)
    snap = fusion_port.FusionDocument(doc, design).snapshot()
    listed, literals = [], []
    for item in snap["timeline"]:
        for p in item.get("parameters", []):
            row = {"owner": item["name"], "type": item.get("type"), "role": p["role"], "name": p["name"],
                   "expression": p["expression"], "unit": p["unit"]}
            listed.append(row)
            if not expr.references(p["expression"]):
                entry = {"type": item.get("type"), "role": p["role"], "expression": expr.normalise(p["expression"])}
                if entry not in literals:
                    literals.append(entry)
    _cache(env)["implicit_literals"] = literals
    return {"model_parameters": listed, "implicit_literals": literals, "orphans": snap["orphan_parameters"],
            "timeline": [{k: i.get(k) for k in ("index", "kind", "type", "name", "component", "on", "health",
                                                "fully_constrained")} for i in snap["timeline"]]}


def _add_testdoc_parameters(env, design):
    from .. import paramset
    plan = planmod.load(env.checkout, TESTDOC_PLAN)
    rows = paramset.order_rows(registry.rows(plan, env.checkout))
    values = registry.parameter_set(plan, env.checkout, plan["build_configuration"])["values"]
    port = fusion_port.FusionDocument(design.parentDocument, design)
    port.add_parameters(rows, {r["name"]: paramset.initial_text(r, values) for r in rows})


# ---- P79.9 ----------------------------------------------------------------------------------------------------
def suppress_kinds(env):
    doc, design = env.new_design("mcc-probe-suppress")
    _add_testdoc_parameters(env, design)
    testdoc_builder._build_fusion(design)
    timeline = design.timeline
    by_name = {timeline.item(i).name: timeline.item(i) for i in range(timeline.count)}
    out, kinds = {}, []
    for kind, names in (("feature", ["Test_Pin_Pattern", "Test_Pin_Extrude"]), ("sketch", ["Test_Pin_Sketch"]),
                        ("plane", ["Test_Pin_Plane"])):
        objects = [by_name[n] for n in names]
        try:
            ok = bool(design.setSuppressed(objects, True))
        except RuntimeError as exc:
            ok, out[kind + "_exception"] = False, str(exc)
        state = [o.isSuppressed for o in objects]
        out[kind] = {"accepted": ok, "suppressed_after": state}
        if ok and all(state):
            kinds.append(kind)
    design.computeAll()
    out["health_with_pin_set_suppressed"] = {timeline.item(i).name: fusion_port.FusionDocument._health(
        timeline.item(i).healthState) for i in range(timeline.count)}
    back = [by_name[n] for n in ("Test_Pin_Plane", "Test_Pin_Sketch", "Test_Pin_Extrude", "Test_Pin_Pattern")]
    out["unsuppress_accepted"] = bool(design.setSuppressed(back, False))
    design.computeAll()
    out["health_after_unsuppress"] = {timeline.item(i).name: fusion_port.FusionDocument._health(
        timeline.item(i).healthState) for i in range(timeline.count)}
    _cache(env)["suppress_kinds"] = kinds
    healthy = all(v in ("healthy", "unknown") for v in out["health_after_unsuppress"].values())
    return dict(out, suppress_kinds=kinds, status="pass" if "feature" in kinds and healthy else "fail")


# ---- P75.1 (and the data for P75.2, P75.4, P75.6, P75.7, P79.10) ----------------------------------------------
def unsaved_build_apply_export(env):
    cache = _cache(env)
    plan = planmod.load(env.checkout, TESTDOC_PLAN)
    plan["export"]["captures"] = ["iso", "top", "front"]
    out = {}
    for mode in ("enforce", "report"):
        doc, design = env.new_design(plan["document"])
        port = fusion_port.FusionDocument(doc, design)
        run_dir = os.path.join(env.checkout, "exports", "fusion", plan["document"],
                               env.job["job_id"] + ("" if mode == "enforce" else "-report"))
        try:
            manifest = build.build_document(plan, port, checkout=env.checkout, out_dir=run_dir,
                                            run_id=os.path.basename(run_dir), gates_mode=mode,
                                            implicit=cache.get("implicit_literals", []),
                                            suppress_kinds=cache.get("suppress_kinds") or ("plane", "sketch", "feature"),
                                            client_git=(env.job.get("client") or {}).get("git"),
                                            host=(env.job.get("host") or {}).get("mode"), log=env.log)
            out.update({"mode": mode, "run_dir": run_dir, "result": manifest["result"]})
            cache["manifest"], cache["run_dir"] = manifest, run_dir
            for key, call in (("f3d_from_unsaved", lambda: port.export_archive(
                                  os.path.join(env.out_dir, "unsaved-probe.f3d"))),
                              ("3mf_from_unsaved", lambda: port.export(
                                  "TestBlock", "3mf", os.path.join(env.out_dir, "unsaved-probe.3mf"),
                                  {"stl_refinement": "high"}))):
                try:                                    # outside the run directory: facts, not exports
                    out[key] = call() is not None
                except Exception as exc:
                    out[key] = "failed: %s" % exc
            break
        except build.BuildFailed as exc:
            out["%s_failed" % mode] = {"stage": exc.stage, "violations": exc.violations[:40]}
        finally:
            port.close()
    ok = out.get("mode") == "enforce" and out.get("result") == "complete"
    return dict(out, status="pass" if ok else "fail")


def _need_manifest(env):
    manifest = _cache(env).get("manifest")
    if manifest is None:
        raise RuntimeError("P75.1 produced no manifest; this probe has no data")
    return manifest


def pattern_quantity(env):
    m = _need_manifest(env)
    b = next(c for c in m["configurations"] if c["values"].get("V_N_TEST_PINS") == 1)
    want = expected.measures({"V_TEST_L": 80, "V_TEST_W": 30, "V_TEST_H": 12, "V_TEST_HOLE_D": 12,
                              "V_N_TEST_PINS": 1}, True)
    got = b["parts"][0]
    ok = not b["health"]["problems"] and abs(got["volume_mm3"] - want["volume_mm3"]) <= 1e-3 * want["volume_mm3"]
    return {"status": "pass" if ok else "fail", "quantity_text": "V_N_TEST_PINS", "value_in_set_b": 1,
            "health": b["health"], "volume_mm3": got["volume_mm3"], "analytic_mm3": want["volume_mm3"]}


def suppress_set(env):
    m = _need_manifest(env)
    b = next(c for c in m["configurations"] if c["suppress"].get("Test_Hole"))
    return {"status": "pass" if not b["health"]["problems"] else "fail",
            "health": b["health"], "aba": m["aba"]}


def export_frame_units(env):
    """Reads the exported binary STL with the standard library and compares its box with Fusion's measure."""
    m, run_dir = _need_manifest(env), _cache(env)["run_dir"]
    out, ok = {"export_settings": m["export_settings"], "parts": []}, True
    for c in m["configurations"]:
        for part in c["parts"]:
            rec = {"part": part["part"], "measure_bbox": part["bbox"], "volume_mm3": part["volume_mm3"]}
            for f in part["files"]:
                path = os.path.join(run_dir, *f["path"].split("/"))
                if f["role"] == "model_stl":
                    with open(path, "rb") as fh:
                        data = fh.read()
                    count = struct.unpack_from("<I", data, 80)[0]
                    binary = len(data) == 84 + 50 * count
                    lo, hi = [math.inf] * 3, [-math.inf] * 3
                    if binary:
                        for k in range(count):
                            v = struct.unpack_from("<12f", data, 84 + 50 * k)[3:]
                            for axis in range(3):
                                lo[axis] = min(lo[axis], v[axis], v[axis + 3], v[axis + 6])
                                hi[axis] = max(hi[axis], v[axis], v[axis + 3], v[axis + 6])
                    same = binary and all(abs(a - b) < 0.05 for a, b in zip(lo + hi, part["bbox"]["min"] + part["bbox"]["max"]))
                    ok = ok and same
                    rec["stl"] = {"binary": binary, "triangles": count, "min": lo, "max": hi, "box_equals_measure": same}
                elif f["role"] == "step":
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                    points = [tuple(float(x) for x in g.split(",")) for g in
                              re.findall(r"CARTESIAN_POINT\('[^']*',\(([^)]*)\)\)", text)]
                    rec["step"] = {"millimetre": ".MILLI." in text, "schema": re.findall(r"FILE_SCHEMA\s*\(\(([^)]*)\)\)", text),
                                   "points_min": [min(p[i] for p in points) for i in range(3)] if points else None,
                                   "points_max": [max(p[i] for p in points) for i in range(3)] if points else None}
                    ok = ok and rec["step"]["millimetre"]
            out["parts"].append(rec)
    return dict(out, status="pass" if ok else "fail")


def apply_time(env):
    m = _need_manifest(env)
    return {"apply_seconds_test_document": {c["id"]: c["apply_seconds"] for c in m["configurations"]},
            "note": "the time on the full case master is the field apply_seconds of its first manifest"}


def captures(env):
    m, run_dir = _need_manifest(env), _cache(env)["run_dir"]
    shots = [dict(s, exists=os.path.isfile(os.path.join(run_dir, *s["path"].split("/"))))
             for s in m["files"] if s["role"] == "png"]
    return {"status": "pass" if shots and all(s["exists"] and s["bytes"] > 1000 for s in shots) else "fail",
            "captures": shots}


# ---- P75.8 ----------------------------------------------------------------------------------------------------
def fonts(env):
    names = list(env.app.fontNames)
    return {"count": len(names), "liberation_sans": "Liberation Sans" in names, "arial": "Arial" in names,
            "names": names}


# ---- P79.15 ---------------------------------------------------------------------------------------------------
def sketch_text(env):
    """The string and the height of a sketch text are model parameters of its sketch, and both read back."""
    doc, design = env.new_design("mcc-probe-text")
    _add(design, "PRB_TEXT_H", "5 mm")
    root = design.rootComponent
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = "Probe_Text_Sketch"
    texts = sketch.sketchTexts
    text_input = texts.createInput3("'MCC 79'", _vi("PRB_TEXT_H"))
    text_input.setAsMultiLine(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(4, 1, 0),
                              adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                              adsk.core.VerticalAlignments.BottomVerticalAlignment, 0)
    text = texts.add(text_input)
    height, content = text.heightParameter, text.textParameter
    owner = height.createdBy
    snap = fusion_port.FusionDocument(doc, design).snapshot()
    item = next(i for i in snap["timeline"] if i["name"] == "Probe_Text_Sketch")
    out = {"text_value": content.textValue, "text_expression": content.expression,
           "text_is_a_text_parameter":
               content.valueType == adsk.fusion.ParameterValueTypes.TextParameterValueType,
           "height_expression": height.expression, "height_role": height.role,
           "height_created_by": owner.objectType if owner is not None else None,
           "snapshot_texts": item.get("texts"), "snapshot_parameters": item.get("parameters"),
           "orphans": snap["orphan_parameters"], "fully_constrained": item.get("fully_constrained")}
    ok = item.get("texts") == ["MCC 79"] and not snap["orphan_parameters"] and any(
        expr.normalise(p["expression"]) == "PRB_TEXT_H" for p in item.get("parameters", []))
    return dict(out, status="pass" if ok else "fail")


# ---- P79.6 ----------------------------------------------------------------------------------------------------
def measure_accuracy(env):
    m = _need_manifest(env)
    rows, ok = [], True
    sets = {"runtime-test/a": ({"V_TEST_L": 60, "V_TEST_W": 30, "V_TEST_H": 10, "V_TEST_HOLE_D": 12,
                                "V_N_TEST_PINS": 3}, False),
            "runtime-test/b": ({"V_TEST_L": 80, "V_TEST_W": 30, "V_TEST_H": 12, "V_TEST_HOLE_D": 12,
                                "V_N_TEST_PINS": 1}, True)}
    for c in m["configurations"]:
        want, got = expected.measures(*sets[c["id"]]), c["parts"][0]
        corners = max(abs(a - b) for a, b in zip(got["bbox"]["min"] + got["bbox"]["max"],
                                                 want["bbox"]["min"] + want["bbox"]["max"]))
        dv = abs(got["volume_mm3"] - want["volume_mm3"]) / want["volume_mm3"]
        da = abs(got["area_mm2"] - want["area_mm2"]) / want["area_mm2"]
        good = corners <= 0.02 and dv <= 1e-3 and da <= 1e-3
        ok = ok and good
        rows.append({"id": c["id"], "corner_error_mm": corners, "volume_error_rel": dv, "area_error_rel": da,
                     "ok": good})
    return {"status": "pass" if ok else "fail", "configurations": rows}


# ---- P79.12 ---------------------------------------------------------------------------------------------------
def long_block(env):
    seconds = float(env.args.get("block_seconds") or 0)
    if seconds <= 0:
        return {"skipped": True, "how": "run the probe with --block-seconds 90 and watch Fusion for a dialog"}
    time.sleep(seconds)
    return {"blocked_seconds": seconds, "question": "Did Fusion show a hang or 'not responding' dialog?"}


# ---- P79.14 ---------------------------------------------------------------------------------------------------
def hosts_registered(env):
    out = {}
    base = os.path.join(env.job["host"].get("checkout", env.checkout), "cad", "fusion", "runtime", "host")
    for name in ("MccRun", "MccFusionBridge"):
        script = env.app.scripts.itemByPath(os.path.join(base, name))
        out[name] = None if script is None else {"is_add_in": script.isAddIn, "is_running": script.isRunning,
                                                 "run_on_startup": script.isRunOnStartup if script.isAddIn else None}
    return out


PROBES = [
    ("P79.1", "Host facts: versions, thread, idle state", host),
    ("P79.2", "New unsaved document: parametric, mm, closes without a prompt, previous document restored", document_lifecycle),
    ("P79.3", "Frame: Z up preference and the view cube of a new document", frame),
    ("P79.4", "The modal guard blocks UserInterface.messageBox", modal_guard),
    ("P79.5", "User parameters: units, forward reference, all-or-none modifyParameters, speed", parameters),
    ("P75.3", "min and max exist in expressions; trigonometry of a deg parameter", min_max),
    ("P75.5", "Expressions read back in a form the normal form absorbs", expression_echo),
    ("P79.7", "Model parameters that Fusion creates by itself (roles and literals)", implicit_literals),
    ("P79.9", "setSuppressed on features, sketches and planes; health after suppress and unsuppress", suppress_kinds),
    ("P75.1", "Build, apply A-B-A and export in an unsaved document; Fusion archive from an unsaved document", unsaved_build_apply_export),
    ("P75.2", "A pattern takes a bare parameter name as quantity and accepts 1", pattern_quantity),
    ("P75.4", "Suppressing all members of a set leaves the rest healthy", suppress_set),
    ("P75.6", "Frame, unit and refinement of the exported STEP and STL", export_frame_units),
    ("P75.7", "Time of one apply (test document; hook for the case master)", apply_time),
    ("P79.6", "Bounding box, volume and area against the closed form", measure_accuracy),
    ("P79.10", "Viewport captures were written", captures),
    ("P75.8", "Fonts available to sketch text", fonts),
    ("P79.15", "Sketch text: the string and the height expression read back", sketch_text),
    ("P79.14", "The two hosts as Fusion sees them", hosts_registered),
    ("P79.12", "Long blocking job (optional): does Fusion show a hang dialog?", long_block),
]
