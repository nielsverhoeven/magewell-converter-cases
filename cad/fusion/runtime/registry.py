"""The runtime's only door to the parameter data; `cad/params.py` stays the only reader of the file formats.

Pure Python, standard library only. A plan with registry.source "inline" carries its rows and sets itself.
"""
import glob
import importlib
import os
import sys


def _params():
    return importlib.import_module("cad.params")


def reset():
    """Forget what cad.params cached. A job runs on the files as they are now, not as an earlier job in the same
    process read them. A process that never imported cad.params has nothing to forget and imports nothing here."""
    loaded = sys.modules.get("cad.params")
    if loaded is not None:
        loaded.clear_cache()


def _expand(checkout, patterns):
    out = []
    for pattern in patterns:
        out += sorted(glob.glob(pattern, root_dir=checkout, recursive=True))
    return [f.replace("\\", "/") for f in out]


def rows(plan, checkout, minmax_in_fusion=True):
    """Registry rows of the plan's document: {"name", "unit", "kind", "fusion", "comment"}, and for source
    cad.params also the keys that cad.params.registry returns ("expression", "description", "src", "conf"), because a
    builder evaluates its expressions from them."""
    reg = plan["registry"]
    if reg["source"] == "inline":
        return [dict(r) for r in reg["rows"]]
    found = _params().registry([os.path.join(checkout, f) for f in _expand(checkout, reg.get("csv", []))],
                               [os.path.join(checkout, f) for f in _expand(checkout, reg.get("sets", []))],
                               minmax_in_fusion=minmax_in_fusion)
    return [dict(r, comment=r.get("comment") or "") for r in found]


def parameter_set(plan, checkout, config_id):
    """{"values": {name: number}, "suppress": {flag: bool}} of one configuration of the plan."""
    config = next(c for c in plan["configurations"] if c["id"] == config_id)
    reg = plan["registry"]
    if reg["source"] == "inline":
        found = reg["sets"][config["set"]["config"]]
    else:
        found = _params().parameter_set(os.path.join(checkout, *config["set"]["file"].split("/")),
                                        config["set"].get("config", "default"))
    return {"values": dict(found["values"]), "suppress": dict(found.get("suppress", {}))}


def set_configurations(plan, checkout):
    """[(set file relative to the checkout, configuration name)] of every parameter-set file that a plan with the
    source cad.params refers to: the files its registry.sets patterns match and the files its configurations name.
    Empty for an inline plan."""
    reg = plan["registry"]
    if reg["source"] == "inline":
        return []
    files = set(_expand(checkout, reg.get("sets", [])))
    files |= {c["set"]["file"] for c in plan["configurations"] if isinstance(c.get("set"), dict) and c["set"].get("file")}
    found = []
    for rel in sorted(files):
        for name in _params().parameter_set_configurations(os.path.join(checkout, *rel.split("/"))):
            found.append((rel, name))
    return found
