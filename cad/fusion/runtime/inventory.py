"""Inventory schema 1: the text listing of a document's components, planes, sketches and features.

Pure Python, standard library only. Two emitters produce it: the record of a builder (raw) and the read-back
of a design. Both go through normalise(), and their hashes are compared.
"""
import hashlib
import json

from . import expr

SCHEMA = 1
KINDS = ("component", "plane", "sketch", "feature")
ROOT = "."
ORIGIN_PLANES = ("origin:XY", "origin:XZ", "origin:YZ")
PHASES = ("enhance",)
RECORD_ONLY = ("within", "phase")
_KEY_ORDER = ("kind", "name", "component", "type", "on", "expressions", "texts", "within", "phase")


class InventoryError(ValueError):
    pass


def normalise(raw):
    """Validate a raw inventory and return its canonical form (a new dict)."""
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise InventoryError("inventory schema must be %d" % SCHEMA)
    document = raw.get("document")
    if not isinstance(document, str) or not document:
        raise InventoryError("inventory needs a document name")
    items, seen = [], {}
    for n, item in enumerate(raw.get("items") or []):
        kind, name = item.get("kind"), item.get("name")
        if kind not in KINDS:
            raise InventoryError("item %d: unknown kind %r" % (n, kind))
        if not isinstance(name, str) or not name:
            raise InventoryError("item %d: no name" % n)
        if name in seen:
            raise InventoryError("item %d: duplicate name %r" % (n, name))
        out = {"kind": kind, "name": name, "component": item.get("component") or ROOT}
        if kind == "feature":
            if not isinstance(item.get("type"), str) or not item["type"]:
                raise InventoryError("feature %r needs a type" % name)
            out["type"] = item["type"]
        if kind in ("plane", "sketch"):
            if not isinstance(item.get("on"), str) or not item["on"]:
                raise InventoryError("%s %r needs 'on'" % (kind, name))
            out["on"] = item["on"]
        if kind != "component":
            normal = []
            for e in item.get("expressions") or []:
                try:
                    if expr.references(e):               # pure literals are not part of the listing
                        normal.append(expr.normalise(e))
                except expr.ExprError as exc:
                    raise InventoryError("%s: %s" % (name, exc))
            out["expressions"] = sorted(normal)
        texts = sorted(item.get("texts") or [])
        if texts:
            out["texts"] = texts
        within = item.get("within")
        if within is not None:
            target = seen.get(within)
            if kind != "feature" or target is None or target["kind"] != "feature" \
                    or target["component"] != out["component"]:
                raise InventoryError("%s: 'within' must name an earlier feature of the same component, not %r"
                                     % (name, within))
            out["within"] = within
        phase = item.get("phase")
        if phase is not None:
            if kind == "component" or phase not in PHASES:
                raise InventoryError("%s: phase %r is not allowed here" % (name, phase))
            out["phase"] = phase
        seen[name] = out
        items.append(out)
    return {"schema": SCHEMA, "document": document, "items": items}


def canonical_bytes(inv):
    return json.dumps(normalise(inv), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def inventory_hash(inv):
    """SHA-256 over the canonical JSON of the normalised inventory."""
    return hashlib.sha256(canonical_bytes(inv)).hexdigest()


def dumps(inv):
    """The committed file: one item per line, fixed key order, LF line ends."""
    inv = normalise(inv)
    lines = ["{", ' "schema": %d,' % SCHEMA, ' "document": %s,' % json.dumps(inv["document"], ensure_ascii=False),
             ' "items": [']
    rows = []
    for item in inv["items"]:
        ordered = {k: item[k] for k in _KEY_ORDER if k in item}
        rows.append("  " + json.dumps(ordered, separators=(",", ":"), ensure_ascii=False))
    lines.append(",\n".join(rows))
    lines += [" ]", "}"]
    return "\n".join(lines) + "\n"


def loads(text):
    return normalise(json.loads(text))


def diff(a, b):
    """Differences between two inventories as readable lines (empty list = equal)."""
    a, b = normalise(a), normalise(b)
    out = []
    if a["document"] != b["document"]:
        out.append("document: %r != %r" % (a["document"], b["document"]))
    ia = {i["name"]: i for i in a["items"]}
    ib = {i["name"]: i for i in b["items"]}
    for name in sorted(set(ia) - set(ib)):
        out.append("only in first: %s" % name)
    for name in sorted(set(ib) - set(ia)):
        out.append("only in second: %s" % name)
    for name in sorted(set(ia) & set(ib)):
        if ia[name] != ib[name]:
            for key in _KEY_ORDER:
                if ia[name].get(key) != ib[name].get(key):
                    out.append("%s.%s: %r != %r" % (name, key, ia[name].get(key), ib[name].get(key)))
    if not out:
        oa = [i["name"] for i in a["items"]]
        ob = [i["name"] for i in b["items"]]
        if oa != ob:
            first = next(n for n, (x, y) in enumerate(zip(oa, ob)) if x != y)
            out.append("order differs from item %d: %s != %s" % (first, oa[first], ob[first]))
    return out


def suppress_members(inv, flag):
    """Names of the items that a suppress flag <Owner>_<Set> switches: every item named <flag>_*."""
    prefix = flag + "_"
    return [i["name"] for i in inv["items"] if i["kind"] != "component" and i["name"].startswith(prefix)]


def annotations(raw):
    """{name: {"within": .., "phase": ..}}: the record-only fields of a raw inventory.

    A design has no place for them, so the read-back takes them from the builder's record by item name."""
    out = {}
    for item in (raw or {}).get("items") or []:
        note = {k: item[k] for k in RECORD_ONLY if item.get(k) is not None}
        if note:
            out[item.get("name")] = note
    return out


def strip_phase(inv, phase):
    """The inventory without the items of one phase."""
    inv = normalise(inv)
    return {"schema": SCHEMA, "document": inv["document"],
            "items": [i for i in inv["items"] if i.get("phase") != phase]}


def from_snapshot(snapshot, notes=None):
    """The inventory of a document as read back through the document port. `notes` is annotations(raw)."""
    items, notes = [], notes or {}
    for t in snapshot["timeline"]:
        kind = "feature" if t["kind"] == "other" else t["kind"]
        item = {"kind": kind, "name": t["name"], "component": t.get("component") or ROOT}
        if kind == "feature":
            item["type"] = t.get("type") or "Unknown"
        if kind in ("plane", "sketch"):
            item["on"] = t.get("on") or "other:unknown"
        if kind != "component":
            item["expressions"] = [p["expression"] for p in t.get("parameters", [])]
        if t.get("texts"):
            item["texts"] = list(t["texts"])
        item.update(notes.get(t["name"], {}))
        items.append(item)
    return normalise({"schema": SCHEMA, "document": snapshot["document"], "items": items})
