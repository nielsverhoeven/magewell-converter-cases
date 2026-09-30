"""The recording backend of the Fusion modelling kit (issue #81, plan section 3.9).

It appends every spec the facade hands it and answers with nothing: the facade has already decided the whole
design.  Two outputs, both plain data; this module writes no file:

* ``raw_inventory()``: the raw inventory of contract C1 of #79 (schema 1), one item per timeline object;
* ``build_record()``: the full specs and the shared calls, the input of the checks (K3) and of the replay (K4b).

Standard library only.
"""
from __future__ import annotations

from . import spec as _spec
from .names import KitError


class RecordingBackend:
    def __init__(self, document: str = ""):
        self.document = document
        self.timeline: list = []  # every spec but a shared call, in the order the facade executed it
        self.shared: list = []  # the shared calls, in the order they were opened

    def execute(self, item) -> None:
        if isinstance(item, _spec.SharedCall):
            self.shared.append(item)
        else:
            self.timeline.append(item)

    # ---- raw inventory (contract C1, the table of 3.9) ------------------------------------------------------------

    @staticmethod
    def _item(s) -> dict:
        if isinstance(s, _spec.ComponentSpec):
            return {"kind": "component", "name": s.name, "component": "."}
        if isinstance(s, _spec.SketchSpec):
            item = {"kind": "sketch", "name": s.name, "component": s.component, "on": s.on,
                    "expressions": [d.text for d in s.dims]}
            if s.texts:
                item["texts"] = list(s.texts)
            return item
        if isinstance(s, _spec.ExtrudeSpec):
            exprs = ([s.start_offset] if s.start_offset is not None else []) + [s.distance]
            item = {"kind": "feature", "name": s.name, "component": s.component, "type": "ExtrudeFeature",
                    "expressions": exprs}
            if s.within is not None:
                item["within"] = s.within
            if s.phase != "build":
                item["phase"] = s.phase
            return item
        raise KitError(f"the recording backend has no inventory row for {type(s).__name__} yet (milestone K2b)")

    def raw_inventory(self) -> dict:
        return {"schema": 1, "document": self.document, "items": [self._item(s) for s in self.timeline]}

    # ---- build record ---------------------------------------------------------------------------------------------

    def build_record(self, api: int = 1) -> dict:
        components = [s.to_json() for s in self.timeline if isinstance(s, _spec.ComponentSpec)]
        specs = []
        for s in self.timeline:
            if not isinstance(s, _spec.ComponentSpec):
                specs.append({"spec": type(s).__name__, **s.to_json()})
        return {"schema": 1, "api": api, "document": self.document, "components": components, "specs": specs,
                "shared_calls": [c.to_json() for c in self.shared]}
