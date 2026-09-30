"""Export manifest, schema 1. Pure Python, standard library only.
"""
import hashlib
import json
import os

SCHEMA = 1
KIND = "fusion-export"
REQUIRED = ("schema", "kind", "document", "run_id", "created_utc", "input_digest", "plan", "git", "fusion", "runtime",
            "inventory", "parameters", "export_settings", "configurations", "aba", "files", "result")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def file_record(path, role, base_dir):
    rel = os.path.relpath(path, base_dir).replace("\\", "/")
    return {"role": role, "path": rel, "bytes": os.path.getsize(path), "sha256": sha256_file(path)}


def validate(m):
    problems = ["missing key %s" % k for k in REQUIRED if k not in m]
    if problems:
        return problems
    if m["schema"] != SCHEMA or m["kind"] != KIND:
        problems.append("schema or kind is wrong")
    if m["result"] not in ("complete", "diagnostic"):
        problems.append("result must be complete or diagnostic")
    if len(m["input_digest"].get("value", "")) != 64 or len(m["inventory"].get("sha256", "")) != 64:
        problems.append("input digest or inventory hash is not a SHA-256")
    seen = set()
    for c in m["configurations"]:
        for key in ("id", "values", "suppress", "health", "gates", "apply_seconds", "parts"):
            if key not in c:
                problems.append("configuration %s lacks %s" % (c.get("id"), key))
        for part in c.get("parts", []):
            for f in part.get("files", []):
                if f["path"] in seen:
                    problems.append("file %s is listed twice" % f["path"])
                seen.add(f["path"])
                if len(f.get("sha256", "")) != 64:
                    problems.append("file %s has no SHA-256" % f["path"])
    if m["result"] == "complete":
        for c in m["configurations"]:
            if c.get("health", {}).get("problems"):
                problems.append("configuration %s is not healthy but the manifest says complete" % c.get("id"))
            if not c.get("gates", {}).get("passed") or c.get("gates", {}).get("violations"):
                problems.append("configuration %s has failed gates but the manifest says complete" % c.get("id"))
        inv = m["inventory"]
        if not (inv.get("sha256") == inv.get("recorded_sha256") == inv.get("committed_sha256")):
            problems.append("the three inventory hashes differ but the manifest says complete")
        if m["runtime"].get("backend") != "fusion" or not m["fusion"].get("version"):
            problems.append("only a run of Fusion can be complete")
    return problems


def write(path, m):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(m, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)
