"""The single probe entry point: one job that answers every live unknown and writes one report.

Pure Python at import. A probe module has
    PROBES = [(id, title, function), ...]
and each function takes `env` and returns a JSON-able dict. An optional key "status" in that dict is
"pass", "fail" or "info" (default "info"). An exception becomes status "error" with its traceback; the
next probe still runs. Documents a probe opened through env.new_design() are closed after it.
"""
import importlib
import json
import os
import time
import traceback

DEFAULT_MODULES = ("cad.fusion.runtime.probe.core_probes",)
SCHEMA = 1


class Env:
    def __init__(self, job, session):
        self.job, self.session = job, session
        self.out_dir = job["out_dir"]
        self.checkout = job["checkout"]
        self.args = job["args"]
        self._docs = []

    @property
    def app(self):
        import adsk.core
        return adsk.core.Application.get()

    @property
    def ui(self):
        return self.app.userInterface

    def log(self, text):
        print(text)

    def new_design(self, name):
        """A new unsaved parametric design in mm. Returns (document, design). Closed when the probe ends."""
        doc, design = self.session.new_document(name)
        self._docs.append(doc)
        return doc, design

    def close_documents(self):
        for doc in self._docs:
            try:
                if doc.isValid:
                    doc.close(False)
            except RuntimeError:
                pass
        self._docs = []


def run(job, session):
    args = job["args"]
    only = set(args.get("only") or [])
    env = Env(job, session)
    records = []
    for modname in args.get("probes") or DEFAULT_MODULES:
        try:
            probes = list(importlib.import_module(modname).PROBES)
        except Exception:
            records.append({"id": modname, "title": "import of the probe module", "status": "error",
                            "data": None, "error": traceback.format_exc(), "seconds": 0.0})
            continue
        for pid, title, function in probes:
            if only and pid not in only:
                continue
            t0 = time.monotonic()
            rec = {"id": pid, "title": title, "module": modname, "status": "info", "data": None, "error": None}
            try:
                data = function(env)
                if isinstance(data, dict) and data.get("status") in ("pass", "fail", "info"):
                    rec["status"] = data.pop("status")
                json.dumps(data)
                rec["data"] = data
            except Exception:                               # JobTimeout is a BaseException and passes through
                rec["status"], rec["error"] = "error", traceback.format_exc()
            finally:
                env.close_documents()
            rec["seconds"] = round(time.monotonic() - t0, 3)
            records.append(rec)
    counts = {}
    for r in records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    report = {"schema": SCHEMA, "job_id": job["job_id"], "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "host": job.get("host"), "summary": counts, "probes": records}
    os.makedirs(env.out_dir, exist_ok=True)
    path = os.path.join(env.out_dir, "probe-report.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return {"ok": counts.get("error", 0) == 0 and counts.get("fail", 0) == 0, "kind": "probe", "report": path,
            "summary": counts, "failed": [r["id"] for r in records if r["status"] in ("fail", "error")]}
