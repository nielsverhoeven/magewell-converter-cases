"""The plan checks of the Fusion modelling kit (issue #81, plan section 3.9, verdict amendments A2 and A6).

``run`` checks one build record (``RecordingBackend.build_record()``, plain dicts) against the registry and the
parameter sets of the document; ``definitions`` checks the shared calls of several records against each other.
Both return a list of ``Finding``; an empty list is a pass.  Nothing here raises for a wrong design: a wrong design
is a finding.

=====  ===========================================================================================================
CK1    names: grammar, known owner, unique, suffix matches the operation
CK2    expressions: grammar of 3.4, closed over the registry, a count is a bare ``V_N_*`` name
CK3    phases: new, joins, cuts, re-joins per part component (specs of phase ``enhance`` are skipped)
CK4    sets: every flag has members, no flag names a protected prefix, nothing feeds an object of another set
CK5    numbers, for every parameter set (suppressed sets too): sizes, distances and pitches positive, counts >= 1
CK6    start and plane offsets: the same sign in every parameter set, never zero
CK7    sketches live in a set: loops do not touch, holes lie inside, loft sections have equal vertex counts
CK9    re-joins: ``within`` names an earlier cut of the same component that is live wherever the re-join is live
CK10   definitions (``definitions``): equal non-placement arguments of a shared builder in all product documents
CK11   owners: every ``Rail_*`` object comes from a ``rail.*`` call; every ``neutrik.*`` call has a ``panel.*`` parent
=====  ===========================================================================================================

CK8 (the inventory writer) does not exist in the kit (verdict A7).  Standard library only; the numbers come from
``expr.Env``, which reaches ``cad.params`` inside its body.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from . import expr, names
from .facade import COUNT_NAME, _bbox, _inside, _touch
from .names import DERIVED_TAGS, RESERVED_SUFFIX, KitError
from .spec import Loop

EPS = 1e-6
FEATURES = ("ExtrudeSpec", "LoftSpec", "PatternSpec", "TextSpec")
OBJECTS = ("SketchSpec", "PlaneSpec") + FEATURES
RANK = {"new": 0, "join": 1, "cut": 2, "rejoin": 3}
_ABSENT = "<absent>"
# arguments that name an instance, not a definition: never compared by CK10
IDENTITY_ARGUMENTS = ("name",)


@dataclass(frozen=True)
class Finding:
    id: str
    name: str
    text: str

    def __str__(self) -> str:
        return f"{self.id} {self.name}: {self.text}"


class _AnyOwner:
    """Owner list used when the caller has none: the grammar is checked, the owner is not."""

    def __contains__(self, item):
        return True

    def __iter__(self):
        return iter(())


class _EvalFailure(Exception):
    pass


# ---- helpers ---------------------------------------------------------------------------------------------------------


def _key(text) -> str:
    """How an expression is remembered in ``_Run.bad``: a str as it is, anything else by its repr."""
    return text if isinstance(text, str) else repr(text)


def _set(name: str) -> str | None:
    try:
        return names.set_of(name)
    except KitError:
        return None


def _live(suppress: dict, name: str) -> bool:
    """The set of ``name`` is live in a configuration unless its flag is true (suppressed)."""
    flag = _set(name)
    return flag is None or not suppress.get(flag, False)


def _op_of(spec: dict, by_name: dict) -> str | None:
    """The operation of a feature for the phase rule; a pattern takes the operation of its seed."""
    if spec["spec"] in ("ExtrudeSpec", "LoftSpec", "TextSpec"):
        return spec["op"]
    seed = by_name.get(spec["seed"])
    return None if seed is None or seed["spec"] == "PatternSpec" else _op_of(seed, by_name)


def _loop_exprs(loop: dict) -> list[tuple[str, object, bool]]:
    """``(label, text, none_ok)`` of every coordinate of a loop dict; None is a coordinate on the datum."""
    kind, args = loop["kind"], loop["args"]
    if kind == "rect":
        return [(label, a, True) for label, a in zip(("u0", "u1", "v0", "v1"), args)]
    if kind == "circle":
        return [("cu", args[0], True), ("cv", args[1], True), ("d", args[2], False)]
    out: list[tuple[str, object, bool]] = []
    for i, point in enumerate(args):
        out += [(f"[{i}].u", point[0], True), (f"[{i}].v", point[1], True)]
    return out


def _as_loop(loop: dict) -> Loop:
    return Loop(loop["kind"], tuple(loop["args"]))


def _sketch_loops(sketch: dict) -> tuple[list[dict], list[dict]]:
    return list(sketch["loops"]), list(sketch["holes"])


class _Run:
    """One run of the checks: the record, the registry names, the configurations and the findings."""

    def __init__(self, record, registry_rows, sets, owners, protected_prefixes):
        self.record = record
        self.rows = list(registry_rows)
        self.names = frozenset(row["name"] for row in self.rows)
        self.sets = dict(sets)
        self.owners = _AnyOwner() if owners is None else owners
        self.protected = tuple(protected_prefixes)
        self.specs = list(record["specs"])
        self.objects = [s for s in self.specs if s["spec"] in OBJECTS]
        self.by_name = {s["name"]: s for s in self.objects}
        self.components = {c["name"]: c for c in record["components"]}
        self.bad: set[str] = set()  # expressions CK2 refused; the numeric checks skip them
        self.findings: list[Finding] = []
        self._envs: dict[str, expr.Env] = {}

    def add(self, check_id: str, name: str, text: str) -> None:
        finding = Finding(check_id, name, text)
        if finding not in self.findings:
            self.findings.append(finding)

    def env(self, config: str) -> expr.Env:
        if config not in self._envs:
            self._envs[config] = expr.Env(self.rows, self.sets[config]["values"])
        return self._envs[config]

    def value(self, config: str, text) -> float:
        if text is None:
            return 0.0
        try:
            return self.env(config).value(text)
        except (KitError, TypeError, ValueError, KeyError, ArithmeticError) as exc:
            raise _EvalFailure(f"{text!r} cannot be evaluated in configuration {config}: {exc}") from None

    # ---- CK1 -----------------------------------------------------------------------------------------------------

    def ck1(self) -> None:
        seen: dict[str, int] = {}
        for comp in self.record["components"]:
            try:
                names.component_check(comp["name"])
            except KitError as exc:
                self.add("CK1", str(comp["name"]), str(exc))
            seen["component:" + comp["name"]] = seen.get("component:" + comp["name"], 0) + 1
        for s in self.objects:
            name, phase = s["name"], s.get("phase", "build")
            try:
                if s["spec"] in ("SketchSpec", "PlaneSpec"):
                    names.check(name, self.owners, None, phase)
                    if not any(name.endswith(tag) for tag in DERIVED_TAGS):
                        raise KitError(f"{name!r}: a sketch or plane name ends with one of {DERIVED_TAGS}")
                else:
                    names.check(name, self.owners, self._kind(s, name), phase)
            except KitError as exc:
                self.add("CK1", name, str(exc))
            seen[name] = seen.get(name, 0) + 1
        for name, count in seen.items():
            if count > 1:
                self.add("CK1", name.split(":")[-1], f"occurs {count} times in the document")

    def _kind(self, s: dict, name: str) -> str:
        if s.get("phase", "build") == "enhance":  # #81 creates none; the kind is the reserved suffix the name ends with
            for suffix in RESERVED_SUFFIX:
                if name.endswith(suffix):
                    return suffix.lower()
            raise KitError(f"{name!r}: a spec of phase 'enhance' ends with one of {RESERVED_SUFFIX}")
        if s["spec"] == "TextSpec":
            return "text_" + s["op"]
        return "pattern" if s["spec"] == "PatternSpec" else s["op"]

    # ---- CK2 -----------------------------------------------------------------------------------------------------

    def _expr(self, owner: str, label: str, text, none_ok: bool = True, count: bool = False) -> None:
        if text is None:
            if not none_ok:
                self.add("CK2", owner, f"{label} is missing")
            return
        try:
            if count and (not isinstance(text, str) or not COUNT_NAME.fullmatch(text)):
                raise KitError(f"{label}: {text!r} is not the bare name of a V_N_* parameter")
            expr.check(text, self.names, label)
        except (KitError, TypeError) as exc:
            self.bad.add(_key(text))
            self.add("CK2", owner, str(exc))

    def ck2(self) -> None:
        for comp in self.record["components"]:
            for label, d in zip(("datum_x", "datum_y", "datum_z"), comp["datum"]):
                self._expr(comp["name"], f"{comp['name']}.{label}", d)
        for s in self.objects:
            name, kind = s["name"], s["spec"]
            if kind == "SketchSpec":
                for where, loops in (("loop", s["loops"]), ("hole", s["holes"])):
                    for i, loop in enumerate(loops):
                        for label, text, none_ok in _loop_exprs(loop):
                            self._expr(name, f"{where}[{i}].{label}", text, none_ok)
                for i, d in enumerate(s["dims"]):
                    self._expr(name, f"dim[{i}]", d["text"], False)
                for label, d in zip(("datum_u", "datum_v"), s["datum"]):
                    self._expr(name, label, d)
            elif kind == "PlaneSpec":
                self._expr(name, "offset", s["offset"])
            elif kind in ("ExtrudeSpec", "TextSpec"):
                self._expr(name, "start_offset", s["start_offset"])
                self._expr(name, "distance", s["distance"], False)
                if kind == "TextSpec":
                    self._expr(name, "height", s["height"], False)
            elif kind == "PatternSpec":
                self._expr(name, "count", s["count"], False, count=True)
                self._expr(name, "pitch", s["pitch"], False)
                if s["axis2"] is not None:
                    self._expr(name, "count2", s["count2"], False, count=True)
                    self._expr(name, "pitch2", s["pitch2"], False)

    # ---- CK3 -----------------------------------------------------------------------------------------------------

    def ck3(self) -> None:
        last: dict[str, tuple[int, str]] = {}  # component -> (rank, op) of its last feature
        for s in self.objects:
            if s["spec"] not in FEATURES or s.get("phase", "build") == "enhance":
                continue
            name, cname = s["name"], s["component"]
            comp = self.components.get(cname)
            if comp is None:
                self.add("CK3", name, f"component {cname!r} is not in the record")
                continue
            op = _op_of(s, self.by_name)
            if op not in RANK:
                self.add("CK3", name, f"its operation cannot be determined (seed {s.get('seed')!r} is not an earlier feature)")
                continue
            if comp["role"] != "part":
                if s["spec"] == "PatternSpec" or op != "new":
                    self.add("CK3", name, f"a {comp['role']} component holds bodies only, every feature is op='new', got {op!r}")
                continue
            rank = RANK[op]
            prev = last.get(cname)
            if s["spec"] == "PatternSpec":
                pass  # a pattern repeats its seed: only the order matters
            elif prev is None and op != "new":
                self.add("CK3", name, f"the first feature of part {cname} is op='new', got {op!r}")
            elif prev is not None and op == "new":
                self.add("CK3", name, f"part {cname} has its body already (one body per part), got op='new'")
            if prev is not None and rank < prev[0]:
                self.add("CK3", name, f"op={op!r} after op={prev[1]!r} in {cname}; the order is new, join, cut, rejoin")
            if prev is None or rank >= prev[0]:
                last[cname] = (rank, op)

    # ---- CK4 -----------------------------------------------------------------------------------------------------

    def ck4(self) -> None:
        members: dict[str, list[str]] = {}
        for s in self.objects:
            flag = _set(s["name"])
            if flag is not None:
                members.setdefault(flag, []).append(s["name"])
        for config, one in self.sets.items():
            for flag in one.get("suppress", {}):
                try:
                    parts = flag.split("_")
                    if len(parts) != 2 or not all(names.TOKEN.fullmatch(p) for p in parts):
                        raise KitError("a flag is <Owner>_<Set>")
                except (KitError, AttributeError) as exc:
                    self.add("CK4", str(flag), f"{exc} (configuration {config})")
                    continue
                if any(flag.startswith(prefix) for prefix in self.protected):
                    self.add("CK4", flag, f"the flag names a protected prefix {list(self.protected)} (configuration {config})")
                if flag not in members:
                    self.add("CK4", flag, f"the flag has no member in the document (configuration {config})")
        for s in self.objects:
            name, kind = s["name"], s["spec"]
            refs: list[str] = []
            if kind in ("ExtrudeSpec", "TextSpec"):
                refs = [s["sketch"]]
            elif kind == "LoftSpec":
                refs = list(s["sketches"]) + list(s["planes"])
            elif kind == "PatternSpec":
                refs = [s["seed"]]
            elif kind == "SketchSpec" and s["on"].startswith("plane:"):
                refs = [s["on"][len("plane:"):]]
            for ref in refs:
                mine, theirs = _set(name), _set(ref)
                if mine is not None and theirs is not None and mine != theirs:
                    self.add("CK4", name, f"{ref!r} feeds it from another set ({theirs}; its own is {mine}): "
                                          "one flag would switch one of them and not the other")

    # ---- CK5 -----------------------------------------------------------------------------------------------------

    def _quantities(self):
        """``(owner, label, text, kind)``: ``size`` positive, ``pitch`` positive, ``count`` a whole number of at least 1."""
        for s in self.objects:
            name, kind = s["name"], s["spec"]
            if kind == "SketchSpec":
                for i, d in enumerate(s["dims"]):
                    yield name, f"dim[{i}] ({d['kind']} {d['a']} {d['b']})", d["text"], "size"
            elif kind in ("ExtrudeSpec", "TextSpec"):
                yield name, "distance", s["distance"], "size"
            elif kind == "PatternSpec":
                yield name, "count", s["count"], "count"
                yield name, "pitch", s["pitch"], "pitch"
                if s["axis2"] is not None:
                    yield name, "count2", s["count2"], "count"
                    yield name, "pitch2", s["pitch2"], "pitch"

    def ck5(self) -> None:
        for config in self.sets:
            for owner, label, text, kind in self._quantities():
                if text is None or _key(text) in self.bad:
                    continue
                try:
                    v = self.value(config, text)
                except _EvalFailure as exc:
                    self.add("CK5", owner, f"{label}: {exc}")
                    continue
                if kind == "count":
                    if v < 1 or abs(v - round(v)) > EPS:
                        self.add("CK5", owner, f"{label} {text} is {v:g} in configuration {config}; a count is a whole number of at least 1")
                elif v <= EPS:
                    self.add("CK5", owner, f"{label} {text!r} is {v:g} in configuration {config}; it must be positive")

    # ---- CK6 -----------------------------------------------------------------------------------------------------

    def ck6(self) -> None:
        for s in self.objects:
            texts = []
            if s["spec"] in ("ExtrudeSpec", "TextSpec"):
                texts = [("start_offset", s["start_offset"])]
            elif s["spec"] == "PlaneSpec":
                texts = [("offset", s["offset"])]
            for label, text in texts:
                if text is None or _key(text) in self.bad:
                    continue  # None is textually zero
                signs: dict[int, list[str]] = {}
                for config in self.sets:
                    try:
                        v = self.value(config, text)
                    except _EvalFailure as exc:
                        self.add("CK6", s["name"], f"{label}: {exc}")
                        continue
                    if abs(v) < EPS:
                        self.add("CK6", s["name"], f"{label} {text!r} is zero in configuration {config} and is not textually zero")
                    else:
                        signs.setdefault(1 if v > 0 else -1, []).append(config)
                if len(signs) > 1:
                    self.add("CK6", s["name"], f"{label} {text!r} is positive in {signs[1]} and negative in {signs[-1]}")

    # ---- CK7 -----------------------------------------------------------------------------------------------------

    def _boxes(self, config: str, loops: list[dict]):
        return [_bbox(_as_loop(loop), lambda text: self.value(config, text)) for loop in loops]

    def ck7(self) -> None:
        for s in self.objects:
            name = s["name"]
            if s["spec"] == "SketchSpec":
                loops, holes = _sketch_loops(s)
                for config, one in self.sets.items():
                    if not _live(one.get("suppress", {}), name):
                        continue
                    try:
                        boxes, hole_boxes = self._boxes(config, loops), self._boxes(config, holes)
                    except _EvalFailure as exc:
                        self.add("CK7", name, str(exc))
                        continue
                    for i in range(len(boxes)):
                        for j in range(i + 1, len(boxes)):
                            if _touch(boxes[i], boxes[j]):
                                self.add("CK7", name, f"loops {i} and {j} touch or overlap in configuration {config}")
                    for i, hb in enumerate(hole_boxes):
                        if not _inside(hb, boxes[0]):
                            self.add("CK7", name, f"hole {i} does not lie strictly inside the outer loop in configuration {config}")
                        for j in range(i + 1, len(hole_boxes)):
                            if _touch(hb, hole_boxes[j]):
                                self.add("CK7", name, f"holes {i} and {j} touch or overlap in configuration {config}")
            elif s["spec"] == "LoftSpec":
                if not any(_live(one.get("suppress", {}), name) for one in self.sets.values()):
                    continue
                shapes = []
                for sketch_name in s["sketches"]:
                    sketch = self.by_name.get(sketch_name)
                    if sketch is None or not sketch["loops"]:
                        shapes.append(None)
                        continue
                    loop = sketch["loops"][0]
                    shapes.append((loop["kind"], len(loop["args"]) if loop["kind"] == "polygon" else 0))
                if None in shapes or len(set(shapes)) != 1:
                    self.add("CK7", name, f"the loft sections differ in kind or vertex count: {shapes}")

    # ---- CK9 -----------------------------------------------------------------------------------------------------

    def ck9(self) -> None:
        position = {s["name"]: i for i, s in enumerate(self.objects)}
        for s in self.objects:
            if s["spec"] != "ExtrudeSpec":
                continue
            name, within = s["name"], s.get("within")
            if s["op"] != "rejoin":
                if within is not None:
                    self.add("CK9", name, f"within is only for op='rejoin', got op={s['op']!r}")
                continue
            cut = self.by_name.get(within) if within is not None else None
            if within is None:
                self.add("CK9", name, "a re-join needs within=<an earlier cut of the same component>")
            elif cut is None or cut["spec"] not in ("ExtrudeSpec", "LoftSpec"):
                self.add("CK9", name, f"within={within!r} is not a feature of the document")
            elif cut["component"] != s["component"]:
                self.add("CK9", name, f"within={within!r} is in component {cut['component']}, the re-join in {s['component']}")
            elif cut["op"] != "cut":
                self.add("CK9", name, f"within={within!r} is a {cut['op']!r}, a re-join names a cut")
            elif position[within] > position[name]:
                self.add("CK9", name, f"within={within!r} comes after the re-join")
            else:
                for config, one in self.sets.items():
                    suppress = one.get("suppress", {})
                    if _live(suppress, name) and not _live(suppress, within):
                        self.add("CK9", name, f"the re-join is live in configuration {config} while its cut {within} is suppressed")

    # ---- CK11 ----------------------------------------------------------------------------------------------------

    def ck11(self) -> None:
        calls = self.record["shared_calls"]
        produced_by_rail = {n for c in calls if c["builder_id"].startswith("rail.") for n in c["produced"]}
        for s in self.objects:
            if s["name"].split("_")[0] == "Rail" and s["name"] not in produced_by_rail:
                self.add("CK11", s["name"], "a Rail_* object is produced inside a rail.* call only")
        for c in calls:
            if c["builder_id"].startswith("neutrik.") and not str(c.get("parent") or "").startswith("panel."):
                self.add("CK11", c["builder_id"], f"a neutrik.* call has a panel.* parent, this one has {c.get('parent')!r}")


def run(record: dict, registry_rows, sets: dict, shared_exceptions=(), *, owners=None, protected_prefixes=()) -> list[Finding]:
    """CK1 to CK7, CK9 and CK11 over one build record.

    ``sets`` maps a configuration id to ``{"values": .., "suppress": ..}`` (contract C4).  ``owners`` and
    ``protected_prefixes`` are the plan keys of the same names (with ``owners=None`` the owner of a name is not
    checked).  ``shared_exceptions`` is accepted for the signature of the plan and unused here: CK10 runs over
    several records, in ``definitions``."""
    r = _Run(record, registry_rows, sets, owners, protected_prefixes)
    for check in (r.ck1, r.ck2, r.ck3, r.ck4, r.ck5, r.ck6, r.ck7, r.ck9, r.ck11):
        check()
    return r.findings


# ---- CK10 ------------------------------------------------------------------------------------------------------------


def exception_pairs(exceptions) -> set[tuple[str, str]]:
    """The ``(builder id, argument)`` pairs of a ``shared_exceptions`` list.  An entry is ``{"builder": id,
    "argument": name}`` (more keys, such as ``reason``, are allowed) or the string ``"id:argument"``."""
    if not isinstance(exceptions, (list, tuple)):
        raise KitError(f"shared_exceptions is a list, got {type(exceptions).__name__}: {exceptions!r}")
    out: set[tuple[str, str]] = set()
    for entry in exceptions:
        if isinstance(entry, dict) and isinstance(entry.get("builder"), str) and isinstance(entry.get("argument"), str):
            out.add((entry["builder"], entry["argument"]))
        elif isinstance(entry, str) and entry.count(":") == 1 and all(entry.split(":")):
            out.add(tuple(entry.split(":")))  # type: ignore[arg-type]
        else:
            raise KitError(f"a shared_exceptions entry is {{'builder': id, 'argument': name}} or 'id:argument', got {entry!r}")
    return out


def definitions(records, exceptions=()) -> list[Finding]:
    """CK10: every shared builder has equal non-placement arguments in all the records (the product documents),
    except the declared ``(builder, argument)`` pairs.  A missing argument counts as a value of its own, so the
    call that leaves out an optional argument differs from the call that passes it.  The argument ``name`` (the
    identity of the instance) is never compared."""
    declared = exception_pairs(exceptions)
    records = list(records)
    definition_args: dict[str, set[str]] = {}  # builder -> every non-placement argument any call passes
    for record in records:
        for call in record["shared_calls"]:
            definition_args.setdefault(call["builder_id"], set()).update(
                a for a in call["arguments"] if a not in call["placement"])
    seen: dict[tuple[str, str], dict[str, list[str]]] = {}  # (builder, argument) -> value text -> documents
    for record in records:
        for call in record["shared_calls"]:
            builder = call["builder_id"]
            for arg in sorted(definition_args[builder]):
                if arg in IDENTITY_ARGUMENTS or (builder, arg) in declared:
                    continue
                value = json.dumps(call["arguments"][arg], sort_keys=True) if arg in call["arguments"] else _ABSENT
                docs = seen.setdefault((builder, arg), {}).setdefault(value, [])
                if record["document"] not in docs:
                    docs.append(record["document"])
    findings = []
    for (builder, arg), values in sorted(seen.items()):
        if len(values) > 1:
            parts = "; ".join(f"{value} in {', '.join(docs)}" for value, docs in sorted(values.items()))
            findings.append(Finding("CK10", builder, f"the non-placement argument {arg!r} is not equal in all product documents: {parts}"))
    return findings
