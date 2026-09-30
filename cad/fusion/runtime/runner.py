"""Job-side entry point of the runtime. Both hosts call run(job) and nothing else.

This module imports no adsk: the adsk modules are imported inside the functions that need them, so the same
file serves `fusion_run.py plan` without Fusion.

A result is a JSON-able dict with "ok": true or false. The client turns ok=false into exit code 1.
"""
import contextlib
import importlib
import json
import os
import time

from . import pipeline, plan as planmod, recording, registry

FACTS_FILE = "fusion_facts.json"


def load_facts():
    """What the probe run taught us about this Fusion version (committed data, empty until the first probe)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FACTS_FILE)
    facts = {"implicit_literals": [], "minmax_in_fusion": True, "suppress_kinds": ["plane", "sketch", "feature"]}
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            facts.update(json.load(fh))
    return facts


def _session(job):
    if job["args"].get("backend") == "recording":
        return contextlib.nullcontext(None)
    from . import fusion_app
    return fusion_app.Session(keep_documents=bool(job["args"].get("keep_documents")))


def run(job):
    registry.reset()                 # no parameter data cached by an earlier job in this process
    kind, args = job["kind"], job["args"]
    deadline = job.get("deadline_monotonic")

    def check_deadline():
        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError("the job's time budget is used up")

    with _session(job) as session:
        if kind == "call":
            module = importlib.import_module(args["module"])
            value = getattr(module, args.get("entry", "run"))(job)
            return {"ok": True, "kind": "call", "value": value, "runner_file": os.path.abspath(__file__)}
        if kind == "build":
            return run_build(job, session, check_deadline)
        if kind == "probe":
            from . import probe
            return probe.run(job, session)
    raise ValueError("unknown job kind %r" % kind)


def run_build(job, session, check_deadline=lambda: None, log=print, committed="check"):
    args, checkout = job["args"], job["checkout"]
    plan = planmod.load(checkout, args["plan"])
    if args.get("options"):
        plan["builder"].setdefault("options", {}).update(args["options"])
    run_dir = os.path.join(checkout, "exports", "fusion", plan["document"], job["job_id"])
    facts = load_facts()
    offline = args.get("backend") == "recording"
    if offline:
        port = recording.RecordingDocument(plan["document"])
    else:
        from . import fusion_port
        doc, design = session.new_document(plan["document"])
        port = fusion_port.FusionDocument(doc, design)
    try:
        m = pipeline.build_document(plan, port, checkout=checkout, out_dir=run_dir, run_id=job["job_id"],
                                    configurations=args.get("configurations"), gates_mode=args.get("gates", "enforce"),
                                    regression=bool(args.get("regression")), diagnostic=bool(args.get("options")),
                                    implicit=facts["implicit_literals"], suppress_kinds=facts["suppress_kinds"],
                                    minmax_in_fusion=facts["minmax_in_fusion"],
                                    facts_version=facts.get("fusion_version"), committed=committed,
                                    forbidden_modules=() if offline else (planmod.REPLAY_MODULE,),
                                    client_git=(job.get("client") or {}).get("git"),
                                    host=(job.get("host") or {}).get("mode"), check_deadline=check_deadline, log=log)
    except pipeline.BuildFailed as exc:
        return {"ok": False, "kind": "build", "result": "failed", "stage": exc.stage, "violations": exc.violations,
                "run_dir": None, "document": plan["document"], "runner_file": os.path.abspath(__file__)}
    finally:
        if not args.get("keep_documents"):
            port.close()
    out = {"ok": m["result"] in ("complete", "recorded"), "kind": "build", "result": m["result"],
           "document": plan["document"], "run_dir": run_dir if m["result"] != "recorded" else None,
           "input_digest": m["input_digest"]["value"], "inventory_sha256": m["inventory"]["sha256"],
           "configurations": [{"id": c["id"], "gates_passed": c["gates"]["passed"], "apply_seconds": c["apply_seconds"],
                               "violations": c["gates"]["violations"], "health": c["health"]["counts"],
                               "parts": [{k: p[k] for k in ("target", "part", "volume_mm3", "area_mm2", "bbox")}
                                         for p in c["parts"]]} for c in m["configurations"]],
           "regression": {"checked": m["regression"]["checked"], "passed": m["regression"]["passed"]},
           "aba": m["aba"], "runner_file": os.path.abspath(__file__)}
    if m["result"] == "recorded":
        out["inventory_text"] = m["inventory"]["text"]
    return out
