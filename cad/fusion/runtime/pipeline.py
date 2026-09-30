"""The build pipeline: registry, builder, then per configuration apply, gates, measure and export, then the manifest.

Pure Python, standard library only. It reaches a document only through the document port, so it runs unchanged
on Fusion and on the recording backend. It knows no product: everything product-specific comes from the
document plan.
"""
import importlib
import json
import os
import shutil
import sys
import time

from . import RUNTIME_VERSION, digest, expr, gates, inventory, manifest, paramset, port as portmod, registry

EXT = {"step": ".step", "stl": ".model.stl", "3mf": ".model.3mf"}
SAME_CORNER_TOL_MM = 1e-6          # order independence and A-B-A: box corners
SAME_REL_TOL = 1e-6                # order independence and A-B-A: volume and area, relative


class BuildFailed(Exception):
    def __init__(self, stage, violations):
        Exception.__init__(self, "%s: %d problem(s)" % (stage, len(violations)))
        self.stage, self.violations = stage, violations


def health_of(snapshot):
    counts = {"items": len(snapshot["timeline"]), "healthy": 0, "suppressed": 0, "unknown": 0, "error": 0,
              "warning": 0, "rolled_back": 0}
    problems = []
    for item in snapshot["timeline"]:
        h = item.get("health", "unknown")
        counts[h] = counts.get(h, 0) + 1
        if h in ("error", "warning", "rolled_back"):
            problems.append({"name": item["name"], "state": h, "message": item.get("message", "")})
    return {"counts": counts, "problems": problems}


def same_measure(a, b):
    """True, False, or None when the backend has no measures."""
    if a is None or b is None or a.get("bbox") is None or b.get("bbox") is None:
        return None
    for corner in ("min", "max"):
        if any(abs(x - y) > SAME_CORNER_TOL_MM for x, y in zip(a["bbox"][corner], b["bbox"][corner])):
            return False
    return all(abs(a[k] - b[k]) <= SAME_REL_TOL * max(abs(a[k]), 1.0) for k in ("volume_mm3", "area_mm2"))


def apply_set(port, rows, pset, members, switchable):
    """One parameter set: ONE modifyParameters call, then the flags, then a compute. Returns (texts, seconds)."""
    texts = paramset.set_texts(pset["values"], rows)
    t0 = time.monotonic()
    port.modify_parameters(texts)
    down = sorted({n for flag, on in pset["suppress"].items() if on for n in members.get(flag, [])})
    up = sorted(set(switchable) - set(down))
    if up:
        port.set_suppressed(up, False)
    if down:
        port.set_suppressed(down, True)
    port.compute()
    return texts, round(time.monotonic() - t0, 3)


def build_document(plan, port, *, checkout, out_dir, run_id, configurations=None, gates_mode="enforce",
                   regression=False, diagnostic=False, implicit=(), suppress_kinds=gates.SUPPRESS_KINDS,
                   minmax_in_fusion=True, facts_version=None, committed="check", forbidden_modules=(),
                   client_git=None, host=None, check_deadline=lambda: None, log=print):
    """Build one document, apply its configurations, export the allow-listed components. Returns the manifest.

    Fusion backend: the run directory `out_dir` appears in one step, and only when every gate passed (or
    gates_mode is "report"). Recording backend: nothing is written; the returned dict has result "recorded".
    `committed="ignore"` leaves the committed inventory out of the gates (the inventory writer uses it).
    `forbidden_modules` are module names that must not be loaded once the builder has run.
    Raises BuildFailed (then nothing was exported); PortError and PlanError pass through.
    """
    log_lines, print_log = [], log

    def log(text):
        log_lines.append(str(text))
        print_log(text)
    rows = registry.rows(plan, checkout, minmax_in_fusion)
    problems = paramset.check_rows(rows)
    if problems:
        raise BuildFailed("registry", problems)
    input_digest = digest.input_digest(os.path.join(checkout, *plan["_path"].split("/")), checkout)
    sets = {c["id"]: registry.parameter_set(plan, checkout, c["id"]) for c in plan["configurations"]}
    first_id = plan["configurations"][0]["id"]
    problems = ["configuration %s has other keys than %s" % (cid, first_id) for cid, s in sets.items()
                if set(s["values"]) != set(sets[first_id]["values"])
                or set(s["suppress"]) != set(sets[first_id]["suppress"])]
    if problems:
        raise BuildFailed("sets", problems)
    selected = [c for c in plan["configurations"] if configurations is None or c["id"] in configurations]
    if not selected:
        raise BuildFailed("configurations", ["none of %r is in the plan" % (configurations,)])

    build_values = sets[plan["build_configuration"]]["values"]
    ordered = paramset.order_rows(rows)
    port.add_parameters(ordered, {r["name"]: paramset.initial_text(r, build_values) for r in ordered})
    check_deadline()
    module = importlib.import_module(plan["builder"]["module"])
    ctx = portmod.BuildContext(port.backend, getattr(port, "design", None), plan["document"], rows,
                               dict(build_values), dict(plan["builder"].get("options", {})), log)
    raw = getattr(module, plan["builder"].get("entry", "build"))(ctx)
    loaded = sorted(m for m in sys.modules for f in forbidden_modules if m == f or m.startswith(f + "."))
    if loaded:
        raise BuildFailed("layering", ["%s is loaded in this process" % m for m in loaded])
    undeclared = digest.undeclared_modules(checkout, plan["inputs"], sys.modules)
    if undeclared:                      # the digest would not notice a change in this code
        raise BuildFailed("inputs", ["%s is loaded by the build and no input pattern of the plan matches it" % f
                                     for f in undeclared])
    if port.backend == "recording":
        if raw is None:
            raise BuildFailed("builder", ["the builder returned no inventory on the recording backend"])
        port.load_inventory(raw)
    check_deadline()

    snapshot = port.snapshot()
    notes = inventory.annotations(raw)
    try:
        inv = inventory.from_snapshot(snapshot, notes)
        recorded_hash = inventory.inventory_hash(raw) if raw is not None else None
    except inventory.InventoryError as exc:
        raise BuildFailed("inventory", [str(exc)])
    inv_hash = inventory.inventory_hash(inv)
    inv_results = []
    if recorded_hash is not None and port.backend != "recording":
        diff = inventory.diff(raw, inv)[:50] if recorded_hash != inv_hash else []
        inv_results.append({"gate": "inventory_recorded", "status": "fail" if diff else "pass", "violations": diff})
    committed_hash, committed_path = None, plan.get("inventory")
    committed_file = os.path.join(checkout, *committed_path.split("/")) if committed_path else None
    if committed == "check" and committed_file and os.path.isfile(committed_file):
        try:
            with open(committed_file, "r", encoding="utf-8") as fh:
                committed_inv = inventory.loads(fh.read())
        except ValueError as exc:
            raise BuildFailed("inventory", ["%s is not a valid inventory: %s" % (committed_path, exc)])
        committed_hash = inventory.inventory_hash(committed_inv)
        diff = inventory.diff(committed_inv, inv)[:50] if committed_hash != inv_hash else []
        inv_results.append({"gate": "inventory_committed", "status": "fail" if diff else "pass", "violations": diff})
    else:
        inv_results.append({"gate": "inventory_committed", "status": "not_checked", "violations": []})

    members = gates.flags_in(snapshot, suppress_kinds)
    switchable = [i["name"] for i in snapshot["timeline"] if i["kind"] in suppress_kinds]
    export_cfg = plan.get("export", {})
    formats = export_cfg.get("formats", ["step", "stl"])
    settings = {"stl_refinement": export_cfg.get("stl_refinement", "high")}
    staging = out_dir + ".partial"
    exporting = port.backend != "recording"
    if exporting:
        if os.path.exists(out_dir):
            raise BuildFailed("run_dir", ["%s exists already" % out_dir])
        shutil.rmtree(staging, ignore_errors=True)
        os.makedirs(staging)
    all_passed = True

    def one(config, export):
        """Apply one configuration, run the gates, measure, and export when asked. Returns its record."""
        nonlocal all_passed
        check_deadline()
        pset = sets[config["id"]]
        texts, seconds = apply_set(port, rows, pset, members, switchable)
        snap = port.snapshot()
        results = gates.run_all(snap, plan, rows, texts, pset["suppress"], config["exports"], list(implicit),
                                suppress_kinds, notes) + inv_results
        bad = gates.failed(results)
        all_passed = all_passed and not bad
        if bad and gates_mode == "enforce":
            raise BuildFailed("gates in configuration %s" % config["id"],
                              ["%s: %s" % (r["gate"], v) for r in bad for v in r["violations"]])
        parts = []
        for e in config["exports"]:
            check_deadline()
            measure = port.measure(e["component"])
            files = []
            for fmt in formats if export and exporting else []:
                path = os.path.join(staging, *e["target"].split("/"), e["part"] + EXT[fmt])
                os.makedirs(os.path.dirname(path), exist_ok=True)
                used = port.export(e["component"], fmt, path, settings)
                if used is None or not os.path.isfile(path):
                    raise BuildFailed("export", ["%s of %s was not written" % (fmt, e["component"])])
                used_settings.update(used)
                files.append(manifest.file_record(path, "model_stl" if fmt == "stl" else fmt, staging))
            part = {"target": e["target"], "part": e["part"], "component": e["component"], "files": files}
            part.update(measure or {"bbox": None, "volume_mm3": None, "area_mm2": None, "solids": None})
            parts.append(part)
        shots = []
        for view in export_cfg.get("captures", []) if export and exporting else []:
            path = os.path.join(staging, "captures", "%s.%s.png" % (config["id"].replace("/", "_"), view))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                if port.capture(path, view, 1600, 1200) is not None and os.path.isfile(path):
                    shots.append(manifest.file_record(path, "png", staging))
            except portmod.PortError as exc:                  # a picture is a convenience, never a gate
                log("capture %s of %s failed: %s" % (view, config["id"], exc))
        return {"id": config["id"], "set": config.get("set"), "values": dict(pset["values"]),
                "suppress": dict(pset["suppress"]), "health": health_of(snap),
                "gates": {"passed": not bad, "violations": ["%s: %s" % (r["gate"], v) for r in bad
                                                            for v in r["violations"]],
                          "results": [{"gate": r["gate"], "status": r["status"]} for r in results]},
                "apply_seconds": seconds, "parts": parts, "captures": shots}

    def same_parts(a, b):
        verdicts = [same_measure(x, y) for x, y in zip(a["parts"], b["parts"])]
        return None if any(v is None for v in verdicts) else all(verdicts)

    used_settings = {"units": "mm", "stl_binary": True, "stl_refinement": settings["stl_refinement"]}
    try:
        pass1 = [one(c, True) for c in selected]
        by_id = {r["id"]: r for r in pass1}
        reg = {"checked": False, "passed": None, "pass2": [], "sets_live_in_one_configuration": []}
        if regression and exporting:
            for config in reversed(selected):
                again = one(config, False)
                reg["pass2"].append({"id": config["id"], "health": again["health"],
                                     "equal_to_pass1": same_parts(by_id[config["id"]], again)})
            reg["checked"] = True
            reg["passed"] = all(r["equal_to_pass1"] is not False for r in reg["pass2"])
            live = {}
            for config in selected:
                for flag, on in sets[config["id"]]["suppress"].items():
                    live.setdefault(flag, [])
                    if not on:
                        live[flag].append(config["id"])
            reg["sets_live_in_one_configuration"] = sorted(f for f, ids in live.items() if len(ids) == 1
                                                           and len(selected) > 1)
        aba = {"checked": False, "passed": False}
        with_exports = [c for c in selected if c["exports"]]
        if plan.get("aba") and len(with_exports) > 1 and exporting:
            wish = plan["aba"] if isinstance(plan["aba"], dict) else {}
            a = next((c for c in with_exports if c["id"] == wish.get("a")), with_exports[0])
            b = next((c for c in with_exports if c["id"] == wish.get("b")), with_exports[-1])
            first, _, second = one(a, False), one(b, False), one(a, False)
            aba = {"checked": True, "a": a["id"], "b": b["id"],
                   "passed": same_parts(first, second) is True and same_parts(by_id[a["id"]], second) is True}
        if reg["passed"] is False or (aba["checked"] and not aba["passed"]):
            all_passed = False
            if gates_mode == "enforce":
                raise BuildFailed("regression", ["a configuration does not come back to the same measures: "
                                                 "pass2 %s, A-B-A %s" % (reg["passed"], aba["passed"])])
        info = port.info()
        if facts_version is not None and facts_version != info.get("fusion_version"):
            log("warning: fusion_facts.json was measured on %s, this is %s" % (facts_version, info.get("fusion_version")))
        final = port.snapshot()
        fresh = recorded_hash == inv_hash and committed_hash == inv_hash     # both exist and both are equal
        if not exporting:
            result = "recorded"
        else:
            result = "complete" if port.backend == "fusion" and all_passed and fresh and not diagnostic \
                and configurations is None else "diagnostic"
        used_settings.update({"formats": list(formats), "archive": bool(export_cfg.get("archive"))})
        git = {k: v for k, v in (client_git or {}).items() if v is not None}
        out = {"schema": manifest.SCHEMA, "kind": manifest.KIND, "document": plan["document"], "run_id": run_id,
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "input_digest": input_digest,
               "plan": {"path": plan["_path"], "sha256": plan["_sha256"]},
               "git": git,
               "fusion": {"version": info.get("fusion_version"), "python": info.get("python"),
                          "design_intent": info.get("design_intent"), "unsaved": info.get("unsaved"),
                          "hub_version": info.get("hub_version"), "up_axis": info.get("up_axis")},
               "runtime": {"version": RUNTIME_VERSION, "backend": port.backend, "host": host or "offline",
                           "gates_mode": gates_mode},
               "inventory": {"sha256": inv_hash, "items": len(inv["items"]), "recorded_sha256": recorded_hash,
                             "committed_sha256": committed_hash},
               "parameters": {p["name"]: expr.normalise(p["expression"]) for p in final["user_parameters"]},
               "export_settings": used_settings, "configurations": pass1, "regression": reg, "aba": aba,
               "files": [], "result": result}
        if not exporting:
            out["inventory"]["text"] = inventory.dumps(inv)
            return out
        if export_cfg.get("archive"):
            archive = os.path.join(staging, plan["document"] + ".f3d")
            if port.export_archive(archive) is None or not os.path.isfile(archive):
                raise BuildFailed("archive", ["the F3D archive was not written"])
            out["files"].append(manifest.file_record(archive, "f3d", staging))
        with open(os.path.join(staging, "inventory.json"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(inventory.dumps(inv))
        with open(os.path.join(staging, "audit.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(final, fh, indent=1, sort_keys=True, ensure_ascii=False)
        with open(os.path.join(staging, "regression.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(regression_text(out))
        with open(os.path.join(staging, "log.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(log_lines) + "\n")
        for c in pass1:
            out["files"] += c.pop("captures")
        for name, role in (("inventory.json", "inventory"), ("audit.json", "audit"), ("log.txt", "log"),
                           ("regression.txt", "report")):
            out["files"].append(manifest.file_record(os.path.join(staging, name), role, staging))
        problems = manifest.validate(out)
        if problems:
            raise BuildFailed("manifest", problems)
        manifest.write(os.path.join(staging, "manifest.json"), out)     # last: everything it lists exists
        os.replace(staging, out_dir)                                    # the run directory appears in one step
        return out
    except BaseException:
        if exporting:
            shutil.rmtree(staging, ignore_errors=True)
        raise


def regression_text(m):
    """The readable report of a run."""
    lines = ["%s regression | fusion %s | input digest %s | inventory %s | %s" % (
        m["document"], m["fusion"]["version"], m["input_digest"]["value"], m["inventory"]["sha256"], m["created_utc"]),
        "pass 1, plan order"]
    for c in m["configurations"]:
        h = c["health"]
        h = h["counts"]
        lines.append("  %s | values %d | flags set %d | healthy %d | suppressed %d | warning %d | error %d | apply %s s"
                     % (c["id"], len(c["values"]), sum(1 for v in c["suppress"].values() if v), h["healthy"],
                        h["suppressed"], h["warning"], h["error"], c["apply_seconds"]))
        for p in c["parts"]:
            box = p["bbox"]
            if box is None:
                lines.append("    %s | no solid" % p["component"])
                continue
            lines.append("    %s | V %.2f | A %.2f | box %s to %s | %s" % (
                p["component"], p["volume_mm3"], p["area_mm2"], " ".join("%g" % v for v in box["min"]),
                " ".join("%g" % v for v in box["max"]), "exported" if p["files"] else "not exported"))
    reg = m["regression"]
    if reg["checked"]:
        equal = sum(1 for r in reg["pass2"] if r["equal_to_pass1"] is not False)
        lines.append("pass 2, reverse order | equal to pass 1: %d of %d" % (equal, len(reg["pass2"])))
        lines.append("sets live in one configuration only: %s" % (", ".join(reg["sets_live_in_one_configuration"]) or "none"))
    else:
        lines.append("pass 2, reverse order | not run")
    aba = m["aba"]
    lines.append("A-B-A | A %s | B %s | %s" % (aba.get("a"), aba.get("b"), "equal" if aba["passed"] else "DIFFERENT")
                 if aba["checked"] else "A-B-A | not run")
    parts = sum(len(c["parts"]) for c in m["configurations"])
    lines.append("result: %s, %d parts" % ("CLEAN" if m["result"] == "complete" else m["result"].upper(), parts))
    return "\n".join(lines) + "\n"
