"""Document plan, schema 1: load and validate. Pure Python, standard library only."""
import hashlib
import json
import os
import re

from . import registry

SCHEMA = 1
KEYS = ("schema", "document", "builder", "registry", "build_configuration", "configurations", "owners",
        "required_components", "protected_prefixes", "never_export", "inventory", "inputs", "export", "aba",
        "shared_exceptions")
BUILDER_KEYS = ("module", "entry", "options")
REGISTRY_KEYS = ("source", "csv", "sets", "rows")
CONFIGURATION_KEYS = ("id", "set", "exports")
SET_KEYS = ("file", "config")
EXPORT_ENTRY_KEYS = ("component", "target", "part")
EXPORT_KEYS = ("formats", "stl_refinement", "archive", "captures")
FORMATS = ("step", "stl", "3mf")
VIEWS = ("iso", "iso_back", "iso_bottom", "top", "bottom", "front", "back", "left", "right")
DOC_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")
ID_RE = re.compile(r"^[a-z0-9_][a-z0-9_./-]*$")
PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
MODULE_RE = re.compile(r"^cad\.fusion(\.[A-Za-z_][A-Za-z0-9_]*)+$")
SCRATCH_PREFIX = "SCRATCH-"
REPLAY_MODULE = "cad.fusion.replay"
REPLAY_PATH = "cad/fusion/replay"


class PlanError(ValueError):
    pass


def load(checkout, rel_path):
    """Read a plan file and validate it, also against the parameter-set files of the checkout."""
    full = os.path.join(checkout, *rel_path.split("/"))
    with open(full, "rb") as fh:
        raw = fh.read()
    plan = json.loads(raw.decode("utf-8"))
    problems = validate(plan, checkout)
    if problems:
        raise PlanError("%s: %s" % (rel_path, "; ".join(problems)))
    plan["_path"] = rel_path
    plan["_sha256"] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return plan


def _inside(path):
    parts = path.replace("\\", "/").split("/")
    return not os.path.isabs(path) and ".." not in parts and parts[0] != ""


def _closed(where, value, allowed, problems):
    """True when `value` is an object with no key outside `allowed`; otherwise a problem is recorded."""
    if not isinstance(value, dict):
        problems.append("%s must be an object" % where)
        return False
    unknown = sorted(k for k in value if k not in allowed and not k.startswith("_"))
    if unknown:
        problems.append("%s: unknown key(s): %s" % (where, ", ".join(unknown)))
    return True


def validate(plan, checkout=None):
    """The problems of a plan. With `checkout`, a plan with the source cad.params is also checked against its
    parameter-set files: every configuration of every set file it refers to must appear in `configurations`,
    exported or with empty exports (a configuration that is left out would be neither gated nor exported, silently)."""
    p = []
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        return ["schema must be %d" % SCHEMA]
    _closed("plan", plan, KEYS, p)
    document = plan.get("document")
    if not isinstance(document, str) or not DOC_RE.match(document):
        p.append("document name missing or not [A-Za-z][A-Za-z0-9-]*")
    elif document.startswith(SCRATCH_PREFIX):
        p.append("a document name that starts with %s is reserved for scratch documents" % SCRATCH_PREFIX)
    b = plan.get("builder")
    if _closed("builder", b, BUILDER_KEYS, p):
        module = b.get("module")
        if not isinstance(module, str) or not MODULE_RE.match(module):
            p.append("builder.module must be a module under cad.fusion")
        elif module == REPLAY_MODULE or module.startswith(REPLAY_MODULE + "."):
            p.append("builder.module must not lie under %s" % REPLAY_MODULE)
        if not isinstance(b.get("entry", "build"), str) or not b.get("entry", "build").isidentifier():
            p.append("builder.entry must be an identifier")
        if not isinstance(b.get("options", {}), dict):
            p.append("builder.options must be an object")
    reg = plan.get("registry")
    if _closed("registry", reg, REGISTRY_KEYS, p) and reg.get("source") not in ("cad.params", "inline"):
        p.append("registry.source must be cad.params or inline")
    configs = plan.get("configurations")
    if not isinstance(configs, list) or not configs:
        p.append("configurations must be a non-empty list")
        configs = []
    ids, outputs = set(), set()
    for c in configs:
        if not _closed("a configuration", c, CONFIGURATION_KEYS, p):
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not ID_RE.match(cid) or cid in ids:
            p.append("configuration id %r is missing, malformed or repeated" % (cid,))
        ids.add(cid)
        if "set" in c:
            _closed("%s: set" % cid, c["set"], SET_KEYS, p)
        if not isinstance(c.get("exports"), list):
            p.append("%s: exports must be a list" % cid)
            continue
        for e in c["exports"]:
            if not _closed("%s: an export" % cid, e, EXPORT_ENTRY_KEYS, p):
                continue
            if not all(isinstance(e.get(k), str) and e.get(k) for k in EXPORT_ENTRY_KEYS):
                p.append("%s: an export needs component, target and part" % cid)
                continue
            if not PART_RE.match(e["part"]) or not ID_RE.match(e["target"]) or ".." in e["target"]:
                p.append("%s: bad target or part name in %r" % (cid, e))
            key = (e["target"], e["part"].lower())               # file names do not differ by case alone
            if key in outputs:
                p.append("%s/%s is exported twice" % (e["target"], e["part"]))
            outputs.add(key)
    if plan.get("build_configuration") not in ids:
        p.append("build_configuration must be one of the configuration ids")
    if not isinstance(plan.get("owners"), list) or not plan.get("owners"):
        p.append("owners must be a non-empty list")
    for key in ("required_components", "protected_prefixes", "never_export", "shared_exceptions"):
        if not isinstance(plan.get(key, []), list):
            p.append("%s must be a list" % key)
    never = plan.get("never_export", [])
    if isinstance(never, list) and not all(isinstance(x, str) and x for x in never):
        p.append("never_export must be a list of component-name prefixes")
    elif isinstance(never, list):
        for c in configs:
            for e in c.get("exports", []) if isinstance(c, dict) and isinstance(c.get("exports"), list) else []:
                component = e.get("component") if isinstance(e, dict) else None
                if isinstance(component, str) and component.startswith(tuple(never)):
                    p.append("%s: component %s starts with a never_export prefix and cannot be exported"
                             % (c.get("id"), component))
    inventory = plan.get("inventory")
    if inventory is not None and not (isinstance(inventory, str) and inventory and _inside(inventory)):
        p.append("inventory must be a path inside the checkout")
    inputs = plan.get("inputs")
    if not isinstance(inputs, list) or not inputs or not all(isinstance(i, str) and i for i in inputs):
        p.append("inputs must be a non-empty list of glob patterns")
    elif any(i.replace("\\", "/").startswith(REPLAY_PATH) for i in inputs):
        p.append("inputs must not name %s: the replay is no build input" % REPLAY_PATH)
    ex = plan.get("export", {})
    if _closed("export", ex, EXPORT_KEYS, p):
        if not set(ex.get("formats", ["step", "stl"])) <= set(FORMATS):
            p.append("export.formats may hold %s" % ", ".join(FORMATS))
        if ex.get("stl_refinement", "high") not in ("high", "medium", "low"):
            p.append("export.stl_refinement must be high, medium or low")
        if not set(ex.get("captures", [])) <= set(VIEWS):
            p.append("export.captures may hold %s" % ", ".join(VIEWS))
    if checkout is not None and isinstance(reg, dict) and reg.get("source") == "cad.params" and not p:
        listed = {(c["set"].get("file"), c["set"].get("config", "default")) for c in configs if isinstance(c.get("set"), dict)}
        try:
            found = registry.set_configurations(plan, checkout)
        except (OSError, ValueError, KeyError) as exc:
            found = []
            p.append("cannot read the parameter-set files: %s" % exc)
        for file, config in found:
            if (file, config) not in listed:
                p.append("configuration %s of %s is not in configurations (list it, with empty exports if nothing "
                         "leaves the document)" % (config, file))
    aba = plan.get("aba", False)
    if not isinstance(aba, bool) and not (isinstance(aba, dict) and set(aba) <= {"a", "b"}
                                          and all(v in ids for v in aba.values())):
        p.append("aba must be true, false or {a, b} with configuration ids")
    return p
