"""RecordingDocument: the document port without Fusion. It holds what a builder recorded and answers the runner.

Pure Python, standard library only. It cannot compute geometry: measure() and export() return None, and
health is always healthy or suppressed.
"""
import sys

from . import expr, port


class RecordingDocument(port.DocumentPort):
    backend = "recording"

    def __init__(self, document):
        self.document = document
        self.params = []                 # [{"name","unit","expression"}]
        self.items = []                  # timeline items, snapshot form
        self.components = [{"name": ".", "parent": None, "solids": None, "identity_placement": True}]
        self.closed = False
        self.calls = []                  # for tests: the sequence of port calls

    def info(self):
        return {"backend": "recording", "fusion_version": None, "python": sys.version.split()[0],
                "design_intent": None, "unsaved": True, "hub_version": None, "up_axis": "Z"}

    def add_parameters(self, rows, texts):
        self.calls.append(("add_parameters", len(rows)))
        known = {p["name"] for p in self.params}
        for row in rows:
            text = texts[row["name"]]
            missing = [n for n in expr.references(text) if n not in known]
            if missing:
                raise port.PortError("%s: %r references %s before it exists" % (row["name"], text, missing))
            self.params.append({"name": row["name"], "unit": row["unit"], "expression": text})
            known.add(row["name"])

    def modify_parameters(self, texts):
        self.calls.append(("modify_parameters", len(texts)))
        by_name = {p["name"]: p for p in self.params}
        unknown = sorted(set(texts) - set(by_name))
        if unknown:
            raise port.PortError("unknown parameter(s): %s" % ", ".join(unknown))
        for text in texts.values():
            expr.parse(text)
        for name, text in texts.items():
            by_name[name]["expression"] = text

    def load_inventory(self, raw):
        """Take over what the kit recorded (raw inventory, contract C1)."""
        self.items = []
        for n, item in enumerate(raw["items"]):
            rec = {"index": n, "kind": item["kind"], "name": item["name"], "component": item.get("component") or ".",
                   "type": item.get("type") or {"component": "Occurrence", "plane": "ConstructionPlane",
                                                "sketch": "Sketch"}.get(item["kind"]),
                   "suppressed": False, "health": "healthy", "message": ""}
            if item["kind"] == "component":
                rec["health"] = "unknown"
                self.components.append({"name": item["name"], "parent": rec["component"], "solids": None,
                                        "identity_placement": True})
            else:
                rec["parameters"] = [{"name": "", "role": "", "expression": e}
                                     for e in item.get("expressions") or []]
            if item["kind"] in ("plane", "sketch"):
                rec["on"] = item.get("on")
            if item["kind"] == "sketch":
                rec["fully_constrained"] = None          # not knowable without Fusion
                rec["texts"] = list(item.get("texts") or [])
            self.items.append(rec)

    def set_suppressed(self, names, suppressed):
        self.calls.append(("set_suppressed", len(names), suppressed))
        by_name = {i["name"]: i for i in self.items}
        unknown = sorted(set(names) - set(by_name))
        if unknown:
            raise port.PortError("unknown timeline object(s): %s" % ", ".join(unknown))
        for name in names:
            by_name[name]["suppressed"] = bool(suppressed)
            by_name[name]["health"] = "suppressed" if suppressed else "healthy"

    def compute(self):
        self.calls.append(("compute",))

    def snapshot(self):
        return {"schema": 1, "document": self.document, "backend": "recording", "design_type": "parametric",
                "length_unit": "mm", "up_axis": "Z", "marker_at_end": True, "groups": 0,
                "components": [dict(c) for c in self.components],
                "user_parameters": [dict(p, value=None) for p in self.params],
                "timeline": [dict(i) for i in self.items]}

    def measure(self, component):
        return None

    def export(self, component, fmt, path, settings):
        return None

    def export_archive(self, path):
        return None

    def capture(self, path, view, width, height):
        return None

    def close(self):
        self.closed = True
