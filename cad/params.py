"""The one reader of every cad/ data format (issues #75, #76).  P0 of the layering in
01-ARCH-BRIEF section B: data plus this accessor module, no geometry, no rule.

Standard library only, Python 3.12 and 3.14 (CI and the local venv) and Fusion's own interpreter.

Formats read here (nobody else parses them):

    cad/parameters/constants.csv     the registry: name,unit,expression,comment
    cad/data/<table>.json            data tables (selection tables, per-kind maps, options)
    cad/devices/<slug>.json          device facts (size, ports with confidence)
    cad/cases/<slug>.json            case definitions (options only)

NEUTRAL EXPRESSION GRAMMAR (no Fusion syntax in data; one evaluator, one Fusion emitter):

    expression := sum
    sum        := term (('+' | '-') term)*
    term       := unary (('*' | '/') unary)*
    unary      := '-' unary | atom
    atom       := NUMBER [UNIT] | NAME | FUNC '(' expression (',' expression)* ')' | '(' expression ')'
    UNIT       := 'mm' | 'deg'                       (nothing in cm or inches)
    FUNC       := 'min' | 'max' | 'sin' | 'cos' | 'tan'      (trigonometry takes an angle)

`3 mm + 2` is an error, as in Fusion ("Units don't Evaluate"): additive operands, min/max arguments
and every row's Unit column must agree.  `emit_fusion()` is the only place that knows Fusion's
dialect (arguments separated by ';').  Never floor, ceil, round or if: a value that needs one is a
solver output (01-ARCH-BRIEF section D).
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

from cad.numeric import cos_deg, sin_deg, tan_deg

CAD_DIR = Path(__file__).resolve().parent
CONSTANTS_CSV = CAD_DIR / "parameters" / "constants.csv"
DATA_DIR = CAD_DIR / "data"
DEVICES_DIR = CAD_DIR / "devices"
CASES_DIR = CAD_DIR / "cases"

CSV_HEADER = ["name", "unit", "expression", "comment"]
CONF_LEVELS = ("measured", "drawing", "manual", "photo", "assumed", "decided")
UNITS_IN_CSV = ("mm", "deg", "none")
NAME_PREFIXES = ("MCC_", "BRK_", "CPN_")

Dim = tuple[int, int]  # (length exponent, angle exponent)
NONE: Dim = (0, 0)
LENGTH: Dim = (1, 0)
ANGLE: Dim = (0, 1)
UNIT_DIM: dict[str, Dim] = {"mm": LENGTH, "deg": ANGLE, "none": NONE}
UNIT_WORDS = {"mm": LENGTH, "deg": ANGLE}


class ExpressionError(ValueError):
    """Syntax error, unknown name or function, or a unit mismatch in an expression."""


@dataclass(frozen=True)
class Quantity:
    value: float  # mm for lengths, deg for angles, plain for dimensionless
    dim: Dim = NONE


# ---------------------------------------------------------------------------------------------
# parser -> small AST
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Num:
    text: str            # the literal as written ('3.0', '0.60', '1e-3')
    unit: str = ""       # '' | 'mm' | 'deg'


@dataclass(frozen=True)
class Name:
    name: str


@dataclass(frozen=True)
class Neg:
    operand: Any


@dataclass(frozen=True)
class Bin:
    op: str
    left: Any
    right: Any


@dataclass(frozen=True)
class Call:
    fn: str
    args: tuple


@dataclass(frozen=True)
class Paren:
    inner: Any


_TOKEN = re.compile(r"\s*(?:(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>[-+*/(),]))")


def _tokenize(text: str) -> list[tuple[str, str]]:
    out, i = [], 0
    while text[i:].strip():
        m = _TOKEN.match(text, i)
        if not m:
            raise ExpressionError(f"cannot tokenize {text[i:i + 20]!r} in {text!r}")
        i = m.end()
        out.append((m.lastgroup, m.group(m.lastgroup)))
    return out


FUNCTION_NAMES = ("min", "max", "sin", "cos", "tan")


class _Parser:
    def __init__(self, text: str):
        self.text, self.toks, self.i = text, _tokenize(text), 0

    def peek(self) -> tuple[str | None, str | None]:
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, want: str | None = None) -> tuple[str, str]:
        t = self.peek()
        if t[0] is None or (want is not None and t[1] != want):
            raise ExpressionError(f"expected {want!r} in {self.text!r}")
        self.i += 1
        return t

    def parse(self):
        n = self.sum()
        if self.peek()[0] is not None:
            raise ExpressionError(f"unexpected {self.peek()[1]!r} in {self.text!r}")
        return n

    def sum(self):
        n = self.term()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            n = Bin(op, n, self.term())
        return n

    def term(self):
        n = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            n = Bin(op, n, self.unary())
        return n

    def unary(self):
        if self.peek()[0] == "op" and self.peek()[1] == "-":
            self.take()
            return Neg(self.unary())
        return self.atom()

    def atom(self):
        kind, tok = self.take()
        if kind == "num":
            nxt = self.peek()
            if nxt[0] == "name" and nxt[1] in UNIT_WORDS:
                self.take()
                return Num(tok, nxt[1])
            if nxt[0] == "name":
                raise ExpressionError(f"unknown unit {nxt[1]!r} in {self.text!r} (only mm and deg)")
            return Num(tok)
        if kind == "name":
            if self.peek()[1] == "(":
                self.take("(")
                args = [self.sum()]
                while self.peek()[1] == ",":
                    self.take(",")
                    args.append(self.sum())
                self.take(")")
                if tok not in FUNCTION_NAMES:
                    raise ExpressionError(f"function {tok}() is not allowed (only {FUNCTION_NAMES})")
                return Call(tok, tuple(args))
            return Name(tok)
        if tok == "(":
            inner = self.sum()
            self.take(")")
            return Paren(inner)
        raise ExpressionError(f"unexpected {tok!r} in {self.text!r}")


def parse(text: str):
    """Parse a neutral-grammar expression into an AST (raises ExpressionError)."""
    return _Parser(text).parse()


def names_in(node_or_text) -> set[str]:
    """Parameter names an expression refers to."""
    node = parse(node_or_text) if isinstance(node_or_text, str) else node_or_text
    if isinstance(node, Name):
        return {node.name}
    if isinstance(node, Num):
        return set()
    if isinstance(node, Neg):
        return names_in(node.operand)
    if isinstance(node, Paren):
        return names_in(node.inner)
    if isinstance(node, Bin):
        return names_in(node.left) | names_in(node.right)
    if isinstance(node, Call):
        return set().union(*(names_in(a) for a in node.args))
    raise ExpressionError(f"unknown node {node!r}")


def is_literal(text: str) -> bool:
    """True for a bare number with an optional unit and sign ('3.0 mm', '-23.5 mm', '1.8', '60 deg')."""
    node = parse(text)
    if isinstance(node, Neg):
        node = node.operand
    return isinstance(node, Num)


def _trig(fn: Callable[[float], float], name: str) -> Callable[[Quantity], Quantity]:
    def f(x: Quantity) -> Quantity:
        if x.dim != ANGLE:
            raise ExpressionError(f"{name}() needs an angle (write '60 deg', not a bare number)")
        return Quantity(fn(x.value), NONE)
    return f


def _same(args: list[Quantity], fn: str) -> Dim:
    dims = {q.dim for q in args}
    if len(dims) != 1:
        raise ExpressionError(f"{fn}(): arguments differ in unit: {sorted(dims)}")
    return dims.pop()


_FUNCS: dict[str, Callable[..., Quantity]] = {
    "max": lambda *a: Quantity(max(q.value for q in a), _same(list(a), "max")),
    "min": lambda *a: Quantity(min(q.value for q in a), _same(list(a), "min")),
    "sin": _trig(sin_deg, "sin"), "cos": _trig(cos_deg, "cos"), "tan": _trig(tan_deg, "tan"),
}


def evaluate(node_or_text, scope: Mapping[str, Quantity] | None = None) -> Quantity:
    """Evaluate an expression with units; raises ExpressionError."""
    node = parse(node_or_text) if isinstance(node_or_text, str) else node_or_text
    scope = scope or {}
    if isinstance(node, Num):
        return Quantity(float(node.text), UNIT_WORDS.get(node.unit, NONE))
    if isinstance(node, Name):
        if node.name not in scope:
            raise ExpressionError(f"unknown name {node.name!r}")
        return scope[node.name]
    if isinstance(node, Paren):
        return evaluate(node.inner, scope)
    if isinstance(node, Neg):
        q = evaluate(node.operand, scope)
        return Quantity(-q.value, q.dim)
    if isinstance(node, Call):
        return _FUNCS[node.fn](*(evaluate(a, scope) for a in node.args))
    if isinstance(node, Bin):
        a, b = evaluate(node.left, scope), evaluate(node.right, scope)
        if node.op in "+-":
            if a.dim != b.dim:
                raise ExpressionError(f"units don't evaluate: {a.dim} {node.op} {b.dim}")
            return Quantity(a.value + b.value if node.op == "+" else a.value - b.value, a.dim)
        if node.op == "*":
            return Quantity(a.value * b.value, (a.dim[0] + b.dim[0], a.dim[1] + b.dim[1]))
        return Quantity(a.value / b.value, (a.dim[0] - b.dim[0], a.dim[1] - b.dim[1]))
    raise ExpressionError(f"unknown node {node!r}")


def emit_fusion(node_or_text) -> str:
    """The ONE Fusion emitter: the neutral expression in Fusion's dialect.  The grammar is a subset of
    Fusion's, so the only difference is the argument separator: max(a, b) -> max(a; b)."""
    node = parse(node_or_text) if isinstance(node_or_text, str) else node_or_text

    def em(n) -> str:
        if isinstance(n, Num):
            return f"{n.text} {n.unit}" if n.unit else n.text
        if isinstance(n, Name):
            return n.name
        if isinstance(n, Paren):
            return f"({em(n.inner)})"
        if isinstance(n, Neg):
            return f"-{em(n.operand)}"
        if isinstance(n, Call):
            return f"{n.fn}({'; '.join(em(a) for a in n.args)})"
        return f"{em(n.left)} {n.op} {em(n.right)}"

    return em(node)


# ---------------------------------------------------------------------------------------------
# the registry: constants.csv
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Row:
    name: str
    unit: str         # 'mm' | 'deg' | 'none'
    expression: str   # neutral grammar; the source of truth
    description: str
    src: str          # 'file:line' or a record id
    conf: str | None  # CONF_LEVELS for a literal row; None for an expression row (it carries none)

    @property
    def dim(self) -> Dim:
        return UNIT_DIM[self.unit]

    @property
    def comment(self) -> str:
        return format_comment(self.description, self.src, self.conf)

    @property
    def is_literal(self) -> bool:
        return is_literal(self.expression)

    @property
    def is_unused(self) -> bool:
        """True when the description starts with `unused:` (the geometry does not use the row, F76.5)."""
        return self.description.startswith("unused:")


def format_comment(description: str, src: str, conf: str | None) -> str:
    """'description | src=<...> | conf=<...>'  (an expression row has no conf field)"""
    parts = [description, f"src={src}"]
    if conf is not None:
        parts.append(f"conf={conf}")
    return " | ".join(parts)


def parse_comment(comment: str) -> tuple[str, str, str | None]:
    parts = [p.strip() for p in comment.split(" | ")]
    src = next((p[4:] for p in parts if p.startswith("src=")), "")
    conf = next((p[5:] for p in parts if p.startswith("conf=")), None)
    desc = " | ".join(p for p in parts if not p.startswith(("src=", "conf=")))
    return desc, src, conf


def read_registry(path: Path | None = None) -> list[Row]:
    path = path or CONSTANTS_CSV
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        if header != CSV_HEADER:
            raise ValueError(f"{path}: header {header} != {CSV_HEADER}")
        rows = []
        for r in reader:
            if not r:
                continue
            name, unit, expression, comment = r
            desc, src, conf = parse_comment(comment)
            rows.append(Row(name, unit, expression, desc, src, conf))
    return rows


def write_registry(rows: list[Row], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(CSV_HEADER)
        for r in rows:
            w.writerow([r.name, r.unit, r.expression, r.comment])


def check_registry(rows: list[Row]) -> list[str]:
    """Structural problems of a registry (empty list = fine).  Used by the permanent tests."""
    problems: list[str] = []
    seen: set[str] = set()
    for r in rows:
        if r.name in seen:
            problems.append(f"{r.name}: duplicate name")
        seen.add(r.name)
        if not re.fullmatch(r"(?:MCC|BRK|CPN)_[A-Z0-9_]+", r.name):
            problems.append(f"{r.name}: name must match (MCC|BRK|CPN)_[A-Z0-9_]+")
        if r.unit not in UNITS_IN_CSV:
            problems.append(f"{r.name}: unit {r.unit!r} not in {UNITS_IN_CSV}")
        if not r.description.strip():
            problems.append(f"{r.name}: empty description")
        if not r.src.strip():
            problems.append(f"{r.name}: missing src")
        try:
            lit = r.is_literal
        except ExpressionError as exc:
            problems.append(f"{r.name}: {exc}")
            continue
        if lit and r.conf not in CONF_LEVELS:
            problems.append(f"{r.name}: literal row needs conf in {CONF_LEVELS}, has {r.conf!r}")
        if not lit and r.conf is not None:
            problems.append(f"{r.name}: an expression row carries no confidence (has {r.conf!r})")
        if lit and r.unit == "mm" and "mm" not in r.expression:
            problems.append(f"{r.name}: literal length without a unit: {r.expression!r}")
        if lit and r.unit == "deg" and "deg" not in r.expression:
            problems.append(f"{r.name}: literal angle without a unit: {r.expression!r}")
    unused = {r.name for r in rows if r.is_unused}
    for r in rows:
        try:
            if r.is_literal:
                continue
            used = sorted(names_in(r.expression) & unused)
        except ExpressionError:
            continue
        if used:
            problems.append(f"{r.name}: expression names unused row(s) {used}")
    return problems


def evaluate_registry(rows: list[Row]) -> dict[str, Quantity]:
    """Evaluate every row (a row may refer to any other row: fixpoint iteration).  Raises
    ExpressionError for a cycle, an unknown name, or an expression whose dimension differs from the
    row's Unit column."""
    scope: dict[str, Quantity] = {}
    pending = {r.name: r for r in rows}
    asts = {r.name: parse(r.expression) for r in rows}
    while pending:
        progressed = False
        for name in list(pending):
            if not names_in(asts[name]) <= scope.keys():
                continue
            q = evaluate(asts[name], scope)
            if q.dim != pending[name].dim:
                raise ExpressionError(f"{name}: {pending[name].expression!r} has dimension {q.dim}, "
                                      f"Unit column says {pending[name].unit!r}")
            scope[name] = q
            del pending[name]
            progressed = True
        if not progressed:
            missing = {n: sorted(names_in(asts[n]) - scope.keys()) for n in pending}
            raise ExpressionError(f"unresolvable rows (cycle or unknown name): {missing}")
    return scope


@lru_cache(maxsize=None)
def _constants_cached(path: str) -> Mapping[str, float]:
    scope = evaluate_registry(read_registry(Path(path)))
    return MappingProxyType({k: v.value for k, v in scope.items()})


def clear_cache() -> None:
    """Forget what constants() and table() cached.  A long-lived process (the Fusion runtime) calls it first."""
    _constants_cached.cache_clear()
    _table_cached.cache_clear()


def constants(path: Path | None = None) -> Mapping[str, float]:
    """name -> value (mm, deg or plain).  Read-only; the same object on every call."""
    return _constants_cached(str(path or CONSTANTS_CSV))


def fusion_parameter(row: Row) -> tuple[str, str, str, str]:
    """(name, api unit, Fusion expression, comment) for the runtime: the unit is the `units` argument of
    UserParameters.add ('' = unitless), the expression is emit_fusion() of the row."""
    return row.name, {"mm": "mm", "deg": "deg", "none": ""}[row.unit], emit_fusion(row.expression), row.comment


# ---------------------------------------------------------------------------------------------
# data tables, devices, cases
# ---------------------------------------------------------------------------------------------


def _resolve(value: Any, scope: Mapping[str, Quantity]) -> Any:
    """{"expr": "<neutral expression>"} -> float (a length or a plain number); other values unchanged."""
    if isinstance(value, dict) and set(value) == {"expr"}:
        q = evaluate(value["expr"], scope)
        if q.dim not in (LENGTH, NONE):
            raise ExpressionError(f"table expression {value['expr']!r} is neither a length nor unitless")
        return q.value
    if isinstance(value, dict):
        return {k: _resolve(v, scope) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, scope) for v in value]
    return value


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("schema") != 1:
        raise ValueError(f"{path.name}: unsupported schema {doc.get('schema')!r}")
    return doc


def table_doc(name: str, data_dir: Path | None = None) -> dict:
    """The whole cad/data/<name>.json (schema, provenance, rows) as written."""
    return _load_json((data_dir or DATA_DIR) / f"{name}.json")


@lru_cache(maxsize=None)
def _table_cached(name: str, data_dir: str, constants_path: str) -> Any:
    doc = _load_json(Path(data_dir) / f"{name}.json")
    scope = evaluate_registry(read_registry(Path(constants_path)))
    rows = _resolve(doc["rows"], scope)
    return MappingProxyType(rows) if isinstance(rows, dict) else tuple(rows)


def table(name: str, data_dir: Path | None = None, constants_path: Path | None = None) -> Any:
    """`rows` of cad/data/<name>.json with every {"expr": ...} evaluated.  A dict keeps the JSON key order
    (the search order of the legacy tables)."""
    return _table_cached(name, str(data_dir or DATA_DIR), str(constants_path or CONSTANTS_CSV))


def device_slugs(devices_dir: Path | None = None) -> list[str]:
    return sorted(p.stem for p in (devices_dir or DEVICES_DIR).glob("*.json"))


def device_doc(slug: str, devices_dir: Path | None = None) -> dict:
    """A fresh dict of cad/devices/<slug>.json (the caller may keep and change it)."""
    return _load_json((devices_dir or DEVICES_DIR) / f"{slug}.json")


def case_slugs(cases_dir: Path | None = None) -> list[str]:
    return sorted(p.stem for p in (cases_dir or CASES_DIR).glob("*.json"))


# tripod_insert left the list (P2-81 Q81.3 default, T1-81.7): the master has no floor insert boss
CASE_OPTIONS = ("fan", "splitter", "fan_switch", "lid_vents", "rail", "fan_y")


def case_doc(slug: str, cases_dir: Path | None = None) -> dict:
    """A fresh dict of cad/cases/<slug>.json: {slug, device, options, configurations, test_configurations}.
    `configurations` holds the extras that are exported (a part of their own, e.g. base_fan); `test_configurations`
    holds those that are never exported (e.g. bare).  Options come from the closed list CASE_OPTIONS and nothing
    else (no dimension, constant, port, slot or feature name); a configuration name is unique across both keys and
    is never `default`."""
    doc = _load_json((cases_dir or CASES_DIR) / f"{slug}.json")
    extra = (set(doc) - {"schema", "slug", "device", "options", "configurations", "test_configurations"})
    if extra:
        raise ValueError(f"{slug}.json: unexpected keys {sorted(extra)}")
    doc.setdefault("configurations", {})
    doc.setdefault("test_configurations", {})
    scopes = [("options", doc["options"])]
    scopes += [(f"configurations.{n}", o) for n, o in doc["configurations"].items()]
    scopes += [(f"test_configurations.{n}", o) for n, o in doc["test_configurations"].items()]
    for scope_name, opts in scopes:
        bad = set(opts) - set(CASE_OPTIONS)
        if bad:
            raise ValueError(f"{slug}.json {scope_name}: option(s) {sorted(bad)} not in {CASE_OPTIONS}")
    names = list(doc["configurations"]) + list(doc["test_configurations"])
    if "default" in names:
        raise ValueError(f"{slug}.json: a configuration may not be called 'default'")
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise ValueError(f"{slug}.json: configuration name(s) {dup} appear in both `configurations` and `test_configurations`")
    return doc


def exported_configurations(slug: str, cases_dir: Path | None = None) -> list[str]:
    """The configurations of a case that are exported: `default` plus the keys of `configurations`, sorted.  A
    test configuration is never among them (export status is data in the case definition)."""
    return ["default"] + sorted(case_doc(slug, cases_dir)["configurations"])


# ---------------------------------------------------------------------------------------------
# parameter sets (written by cad/layout.py, issue #77; read ONLY here)
# ---------------------------------------------------------------------------------------------
#
# cad/parameters/variants/<slug>.json
#   {"schema": 1, "slug": ..., "solver": "cad/layout.py",
#    "configurations": {"<config>": {"parameters": {"V_CASE_L": "193.9 mm", "V_N_DECK_X": "4", ...},
#                                    "flags": {"Fan_Aperture": true, ...},          # true = suppressed
#                                    "slots": [{"slot": 1, "port": "rj45", "part": "NE8FDP-B"}, ...]}}}
#
# Values are strings exactly as the runtime hands them to Fusion: a length is '<shortest decimal> mm',
# a count is a bare integer >= 1.  Every configuration of every file carries the SAME parameter names and
# the SAME flag names (sets are total).  A parameter set holds no MCC_ constant and no expression.

VARIANTS_DIR = CAD_DIR / "parameters" / "variants"
CASE_OWNERS = ("Shell", "Patch", "Floor", "Cradle", "Vent", "Fan", "Switch", "SideBolt", "Fastener", "Rail",
               "Ghost", "Reserve")
_VALUE = re.compile(r"^(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(?: (mm|deg))?$")
_V_NAME = re.compile(r"^V_[A-Z][A-Z0-9_]*$")
_FLAG_NAME = re.compile(r"^([A-Z][A-Za-z0-9]*)_([A-Z][A-Za-z0-9]*)$")


def parse_value(text: str) -> tuple[float | int, str]:
    """'193.9 mm' -> (193.9, 'mm'); '60 deg' -> (60.0, 'deg'); '4' -> (4, 'none')."""
    m = _VALUE.match(text.strip())
    if not m:
        raise ValueError(f"not a parameter value: {text!r} (expected '<number> mm', '<number> deg' or an integer)")
    num, unit = m.groups()
    if unit is None:
        return int(num), "none"
    return float(num), unit


def parameter_set_doc(set_file: Path | str) -> dict:
    return _load_json(Path(set_file))


def parameter_set_configurations(set_file: Path | str) -> list[str]:
    return list(parameter_set_doc(set_file)["configurations"])


def parameter_set(set_file: Path | str, config: str = "default") -> dict:
    """{"values": {V_name: number}, "units": {V_name: 'mm'|'deg'|'none'}, "suppress": {flag: bool},
    "slots": [...]} of one configuration.  Numbers are floats (lengths, angles) or ints (counts).
    Raises ValueError for a malformed set."""
    return parameter_set_of(parameter_set_doc(set_file), config)


def parameter_set_of(doc: dict, config: str = "default") -> dict:
    """parameter_set() for an already parsed set-file document (validates exactly the same way)."""
    cfg = doc["configurations"][config]
    values: dict[str, float | int] = {}
    units: dict[str, str] = {}
    for name, text in cfg["parameters"].items():
        if not _V_NAME.match(name):
            raise ValueError(f"{name}: solver output names are V_<GROUP>_<NAME>")
        values[name], units[name] = parse_value(text)
        if name.startswith("V_N_") and not (units[name] == "none" and isinstance(values[name], int) and values[name] >= 1):
            raise ValueError(f"{name}: a count is an integer >= 1, got {text!r}")
        if not name.startswith("V_N_") and units[name] == "none":
            raise ValueError(f"{name}: only V_N_* counts are unitless, got {text!r}")
    for flag, on in cfg["flags"].items():
        m = _FLAG_NAME.match(flag)
        if not m or m.group(1) not in CASE_OWNERS or m.group(1) == "Reserve" or not isinstance(on, bool):
            raise ValueError(f"{flag}: a suppress flag is <Owner>_<Set> (Owner in {CASE_OWNERS}, never Reserve) "
                             f"with a boolean value")
    return {"values": values, "units": units, "suppress": dict(cfg["flags"]), "slots": list(cfg.get("slots", []))}


def check_parameter_sets(set_files: list[Path | str]) -> list[str]:
    """Problems across all configurations of all files: malformed values, key sets that differ."""
    problems: list[str] = []
    ref: tuple[str, dict, dict] | None = None
    for f in set_files:
        for config in parameter_set_configurations(f):
            label = f"{Path(f).stem}/{config}"
            try:
                ps = parameter_set(f, config)
            except (ValueError, KeyError) as exc:
                problems.append(f"{label}: {exc}")
                continue
            if ref is None:
                ref = (label, ps["units"], ps["suppress"])
                continue
            if set(ps["units"]) != set(ref[1]):
                diff = sorted(set(ps["units"]) ^ set(ref[1]))
                problems.append(f"{label}: parameter names differ from {ref[0]}: {diff[:6]}")
            elif ps["units"] != ref[1]:
                problems.append(f"{label}: units differ from {ref[0]}")
            if set(ps["suppress"]) != set(ref[2]):
                problems.append(f"{label}: flag names differ from {ref[0]}: {sorted(set(ps['suppress']) ^ set(ref[2]))[:6]}")
    return problems


def _has_call(node, names: tuple[str, ...]) -> bool:
    if isinstance(node, Call):
        return node.fn in names or any(_has_call(a, names) for a in node.args)
    if isinstance(node, Bin):
        return _has_call(node.left, names) or _has_call(node.right, names)
    if isinstance(node, (Neg,)):
        return _has_call(node.operand, names)
    if isinstance(node, Paren):
        return _has_call(node.inner, names)
    return False


def registry(csv_files: list[Path | str] | None = None, set_files: list[Path | str] | None = None,
             *, minmax_in_fusion: bool = True) -> list[dict]:
    """The registry of one document for the runtime (#79): rows
        {"name", "unit" ('mm' | 'deg' | ''), "kind" ('constant' | 'expression' | 'solver'),
         "expression" (the neutral text, None for a solver output), "fusion" (text for Fusion, None for a solver
         output), "comment", "description", "src", "conf"}
    in file order (CSV rows first, then the solver names sorted).  'fusion' is '3 mm' for a constant and
    emit_fusion(expression) for an expression row.  If a live probe shows that Fusion has no min()/max()
    (01-ARCH-BRIEF section I, live fact 3), pass minmax_in_fusion=False: an expression row that calls them
    is then emitted as its evaluated number with its unit and the CSV keeps the definition.  All CSV files are
    evaluated together (a product file may use MCC_ names); names must be unique across files; the solver
    names are the parameter names of the set files, which must all agree (check_parameter_sets)."""
    all_rows: list[Row] = []
    for f in csv_files or [CONSTANTS_CSV]:
        all_rows += read_registry(Path(f))
    names = [r.name for r in all_rows]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise ValueError(f"{dup}: defined in more than one registry file")
    scope = evaluate_registry(all_rows)
    out: list[dict] = []
    api_unit = {"mm": "mm", "deg": "deg", "none": ""}
    for r in all_rows:
        fusion = emit_fusion(r.expression)
        if not minmax_in_fusion and not r.is_literal and _has_call(parse(r.expression), ("min", "max")):
            v = scope[r.name].value
            fusion = repr(int(v) if float(v).is_integer() else float(v)) + (f" {r.unit}" if r.unit != "none" else "")
        out.append({"name": r.name, "unit": api_unit[r.unit], "kind": "constant" if r.is_literal else "expression",
                    "expression": r.expression, "fusion": fusion, "comment": r.comment, "description": r.description, "src": r.src, "conf": r.conf})
    if set_files:
        problems = check_parameter_sets(set_files)
        if problems:
            raise ValueError("parameter sets are inconsistent: " + " | ".join(problems[:4]))
        first = Path(set_files[0])
        ps = parameter_set(first, parameter_set_configurations(first)[0])
        for name in sorted(ps["values"]):
            if name in names:
                raise ValueError(f"{name}: a solver output may not reuse a constant's name")
            out.append({"name": name, "unit": api_unit[ps["units"][name]], "kind": "solver", "expression": None, "fusion": None,
                        "comment": "solver output of cad/layout.py | src=cad/layout.py",
                        "description": "solver output of cad/layout.py", "src": "cad/layout.py", "conf": None})
    return out


_SOLVED_DIM = {"mm": LENGTH, "deg": ANGLE, "none": NONE, "": NONE}


def environment(rows: list[Row] | list[dict] | None = None, solved: Mapping[str, Any] | None = None) -> dict[str, Quantity]:
    """Every registry name -> Quantity (value in mm, deg or plain, with its dimension): the constant and expression
    rows of `rows` (default cad/parameters/constants.csv) evaluated, then the solver outputs of `solved`, the dict
    parameter_set(set_file, config) returns (its "values" and "units").  `rows` may be `Row` objects or the list of dicts
    that registry() returns, which is what the runtime hands a builder: a row of kind constant or expression is then
    evaluated from its "expression" text (the neutral grammar; the Fusion dialect is never parsed back), a row of kind solver is
    skipped and its value comes from `solved`.  The generator kit evaluates its builder expressions with it:
    evaluate_number("V_CASE_L / 2 - V_SWITCH_PAD_T", environment(ctx.registry, solved)).  No name rule is applied here
    (a test document may use its own prefix); check_registry() is where MCC_, BRK_ and CPN_ are enforced."""
    if rows is None:
        rows = read_registry()
    elif rows and isinstance(rows[0], dict):
        api = {"mm": "mm", "deg": "deg", "none": "none", "": "none"}
        rows = [Row(r["name"], api[r["unit"]], r["expression"], r.get("description", ""), r.get("src", ""), r.get("conf"))
                for r in rows if r["kind"] != "solver"]
    env = dict(evaluate_registry(rows))
    for name, value in (solved["values"] if solved else {}).items():
        if name in env:
            raise ValueError(f"{name}: a solver output may not reuse a registry name")
        env[name] = Quantity(float(value), _SOLVED_DIM[solved["units"][name]])
    return env


def evaluate_number(text: str, env: Mapping[str, Quantity]) -> float:
    """The value (mm, deg or plain) of one expression of the neutral grammar in `env` (see environment())."""
    return evaluate(text, env).value
