"""Export-time gates as pure functions over a snapshot. No adsk, no product knowledge.

Every gate returns {"gate": id, "status": "pass" | "fail" | "not_checked", "violations": [text, ...]}.
"not_checked" is used when the backend cannot know (the recording backend has no solids and no solver).
"""
import re

from . import expr, paramset

TOKEN = r"[A-Z][A-Za-z0-9]*"
ITEM_RE = re.compile(r"^(%s)_(%s)_(%s)$" % (TOKEN, TOKEN, TOKEN))
FLAG_RE = re.compile(r"^(%s)_(%s)$" % (TOKEN, TOKEN))
COMPONENT_RE = re.compile(r"^%s(_%s)?$" % (TOKEN, TOKEN))
FORBIDDEN_TYPES = ("BaseFeature",)
VALUE_TOL = 1e-9


def _result(gate, violations, checked=True):
    if not checked:
        return {"gate": gate, "status": "not_checked", "violations": []}
    return {"gate": gate, "status": "fail" if violations else "pass", "violations": violations}


def flag_of(name):
    m = ITEM_RE.match(name)
    return "%s_%s" % (m.group(1), m.group(2)) if m else None


SUPPRESS_KINDS = ("plane", "sketch", "feature")


def flags_in(snapshot, kinds=SUPPRESS_KINDS):
    """{flag: [member names]} for every <Owner>_<Set> that has at least one member of the given kinds."""
    out = {}
    for item in snapshot["timeline"]:
        if item["kind"] in kinds:
            flag = flag_of(item["name"])
            if flag:
                out.setdefault(flag, []).append(item["name"])
    return out


def gate_frame(snapshot):
    v = []
    if snapshot.get("up_axis") != "Z":
        v.append("modelling orientation is %r, not Z up" % snapshot.get("up_axis"))
    if snapshot.get("length_unit") != "mm":
        v.append("document unit is %r, not mm" % snapshot.get("length_unit"))
    if snapshot.get("design_type") != "parametric":
        v.append("design type is %r, not parametric" % snapshot.get("design_type"))
    return _result("frame", v)


def gate_names(snapshot, owners):
    v, seen = [], set()
    if snapshot.get("groups"):
        v.append("the timeline has %d group(s); groups are not used" % snapshot["groups"])
    for comp in snapshot["components"]:
        if comp["name"] != "." and not COMPONENT_RE.match(comp["name"]):
            v.append("component name %r is not PascalCase[_PascalCase]" % comp["name"])
    for item in snapshot["timeline"]:
        name = item["name"]
        if name in seen:
            v.append("duplicate name %s" % name)
        seen.add(name)
        if item["kind"] == "component":
            continue
        if item["kind"] == "other":
            v.append("timeline object %s has an unsupported type %s" % (name, item.get("type")))
            continue
        m = ITEM_RE.match(name)
        if not m:
            v.append("name %r is not <Owner>_<Set>_<What>" % name)
        elif m.group(1) not in owners:
            v.append("owner %r of %s is not in the owner list" % (m.group(1), name))
        if item.get("type") in FORBIDDEN_TYPES:
            v.append("%s is a %s, which is not allowed" % (name, item["type"]))
    return _result("names", v)


def gate_placement(snapshot):
    """Sketches lie on an origin plane or on a named construction plane; planes are offsets of an origin plane."""
    v = []
    planes = {i["name"] for i in snapshot["timeline"] if i["kind"] == "plane"}
    for item in snapshot["timeline"]:
        on = item.get("on")
        if item["kind"] == "sketch":
            if not (on in ("origin:XY", "origin:XZ", "origin:YZ") or (on or "").startswith("plane:")
                    and on[6:] in planes):
                v.append("sketch %s lies on %r" % (item["name"], on))
        elif item["kind"] == "plane":
            if on not in ("origin:XY", "origin:XZ", "origin:YZ"):
                v.append("plane %s is defined on %r, not as an offset of an origin plane" % (item["name"], on))
            if not [p for p in item.get("parameters", []) if _refs(p["expression"])]:
                v.append("plane %s has no offset expression of parameters" % item["name"])
    return _result("placement", v)


def _refs(text):
    try:
        return expr.references(text)
    except expr.ExprError:
        return []


def gate_dimensions(snapshot, registry_names, implicit):
    """No dimension without a parameter reference; every expression inside the allowed subset and the registry."""
    v = []
    allowed = {(e["type"], e["role"], e["expression"]) for e in implicit}
    for item in snapshot["timeline"]:
        for p in item.get("parameters", []):
            text = p["expression"]
            label = "%s (%s %s)" % (item["name"], p.get("name") or "?", p.get("role") or "?")
            try:
                refs = expr.references(text)
            except expr.ExprError as exc:
                v.append("%s: %s" % (label, exc))
                continue
            if not refs:
                if (item.get("type"), p.get("role", ""), expr.normalise(text)) not in allowed:
                    v.append("%s: literal %r without a parameter reference" % (label, text))
                continue
            for problem in expr.violations(text):
                v.append("%s: %s in %r" % (label, problem, text))
            for name in refs:
                if name not in registry_names:
                    v.append("%s: %r is not in the registry" % (label, name))
    return _result("dimensions", v)


def gate_sketches(snapshot):
    items = [i for i in snapshot["timeline"] if i["kind"] == "sketch"]
    if any(i.get("fully_constrained") is None for i in items):
        return _result("sketches", [], checked=False)
    return _result("sketches", ["sketch %s is not fully constrained" % i["name"] for i in items
                                 if not i["fully_constrained"]])


def gate_parameters(snapshot, rows, texts):
    """Every user parameter equals git: same names, constants and expressions equal, solver values equal."""
    v = []
    by_name = {r["name"]: r for r in rows}
    have = {p["name"]: p for p in snapshot["user_parameters"]}
    for name in sorted(set(have) - set(by_name)):
        v.append("user parameter %s is not in the registry" % name)
    for name in sorted(set(by_name) - set(have)):
        v.append("registry parameter %s is missing in the document" % name)
    for name in sorted(set(by_name) & set(have)):
        row, got = by_name[name], have[name]
        want = texts[name] if row["kind"] == "solver" else row["fusion"]
        if got["unit"] != row["unit"]:
            v.append("%s: unit %r, registry %r" % (name, got["unit"], row["unit"]))
        try:
            same = expr.normalise(got["expression"]) == expr.normalise(want)
        except expr.ExprError as exc:
            v.append("%s: %s" % (name, exc))
            continue
        if not same and got.get("value") is not None and expr.is_literal(got["expression"]):
            # a plain number may be echoed with another number of digits: compare the value instead
            node = expr.parse(want)
            if node[0] == "neg" and node[1][0] == "num":
                node = ("num", "-" + node[1][1], node[1][2])
            same = node[0] == "num" and abs(float(node[1]) - got["value"]) <= VALUE_TOL
        if not same:
            v.append("%s: document has %r, git has %r" % (name, got["expression"], want))
    return _result("parameters", v)


def gate_required(snapshot, required):
    comps = {c["name"]: c for c in snapshot["components"]}
    v, unknown = [], False
    for name in required:
        if name not in comps:
            v.append("required component %s is missing" % name)
        elif comps[name].get("solids") is None:
            unknown = True
        elif comps[name]["solids"] < 1:
            v.append("required component %s has no solid" % name)
    return _result("required_components", v) if v or not unknown else _result("required_components", [], False)


def gate_flags(snapshot, suppress, protected_prefixes, kinds=SUPPRESS_KINDS):
    members = flags_in(snapshot, kinds)
    v = paramset.check_flags(suppress, members)
    for flag in suppress:
        if not FLAG_RE.match(flag):
            v.append("flag %r is not <Owner>_<Set>" % flag)
        if any(flag.startswith(p) for p in protected_prefixes):
            v.append("flag %s names a protected set" % flag)
    return _result("flags", v)


def gate_health(snapshot, suppress, kinds=SUPPRESS_KINDS):
    """No error, no warning, nothing rolled back; exactly the members of the true flags are suppressed."""
    v = []
    if not snapshot.get("marker_at_end", True):
        v.append("the timeline marker is not at the end")
    for p in snapshot.get("orphan_parameters", []):
        v.append("model parameter %s (%r) belongs to no timeline object" % (p.get("name"), p.get("expression")))
    members = flags_in(snapshot, kinds)
    expected = {n for flag, on in suppress.items() if on for n in members.get(flag, [])}
    for item in snapshot["timeline"]:
        health = item.get("health")
        if health in ("error", "warning"):
            v.append("%s: %s %s" % (item["name"], health, item.get("message", "")))
        elif health == "rolled_back":
            v.append("%s is rolled back" % item["name"])
        if item["kind"] in kinds and bool(item.get("suppressed")) != (item["name"] in expected):
            v.append("%s is %ssuppressed, the set says otherwise" % (item["name"], "" if item.get("suppressed") else "not "))
    return _result("health", v)


def gate_exports(snapshot, exports):
    comps = {c["name"]: c for c in snapshot["components"]}
    v, unknown = [], False
    for e in exports:
        c = comps.get(e["component"])
        if c is None:
            v.append("exported component %s does not exist" % e["component"])
        elif c.get("solids") is None:
            unknown = True
        else:
            if c["solids"] != 1:
                v.append("exported component %s has %d solids, not 1" % (e["component"], c["solids"]))
            if not c.get("identity_placement", False):
                v.append("exported component %s is not placed at the document origin" % e["component"])
    return _result("exports", v) if v or not unknown else _result("exports", [], False)


def gate_rejoin(snapshot, notes):
    """A re-join names the cut it refills: that cut exists, comes first and is live whenever the re-join is."""
    v = []
    items = {i["name"]: i for i in snapshot["timeline"]}
    for name in sorted(n for n, note in notes.items() if note.get("within")):
        item, cut = items.get(name), items.get(notes[name]["within"])
        if item is None:
            continue                                   # the inventory gates report a missing item
        if cut is None:
            v.append("%s refills %s, which is not in the document" % (name, notes[name]["within"]))
        elif cut["index"] >= item["index"]:
            v.append("%s comes before the cut %s that it refills" % (name, cut["name"]))
        elif cut.get("suppressed") and not item.get("suppressed"):
            v.append("%s is live while the cut %s that it refills is suppressed" % (name, cut["name"]))
    return _result("rejoin", v)


def run_all(snapshot, plan, rows, texts, suppress, exports, implicit, kinds=SUPPRESS_KINDS, notes=None):
    registry_names = {r["name"] for r in rows}
    return [gate_frame(snapshot), gate_names(snapshot, plan["owners"]), gate_placement(snapshot),
            gate_dimensions(snapshot, registry_names, implicit), gate_sketches(snapshot),
            gate_parameters(snapshot, rows, texts), gate_required(snapshot, plan.get("required_components", [])),
            gate_flags(snapshot, suppress, plan.get("protected_prefixes", []), kinds),
            gate_health(snapshot, suppress, kinds),
            gate_exports(snapshot, exports), gate_rejoin(snapshot, notes or {})]


def failed(results):
    return [r for r in results if r["status"] == "fail"]
