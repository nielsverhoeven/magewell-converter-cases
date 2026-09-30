"""Registry rows and parameter sets: ordering, value text, totality. Names and units only, no geometry.

Pure Python, standard library only.
A registry row is {"name", "unit" ("mm"|"deg"|""), "kind" ("constant"|"expression"|"solver"), "fusion", "comment"}.
"""
import math
import re
from decimal import Decimal

from . import expr

UNITS = ("mm", "deg", "")
KINDS = ("constant", "expression", "solver")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESERVED = expr.UNITS | expr.ALLOWED_FUNCTIONS | expr.FORBIDDEN_FUNCTIONS


class ParamError(ValueError):
    pass


def number_text(x):
    """Shortest decimal text of a number, never with an exponent: 60.0 -> '60', 0.1 -> '0.1', 1e-7 -> '0.0000001'."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ParamError("not a number: %r" % (x,))
    if isinstance(x, float) and not math.isfinite(x):
        raise ParamError("not a finite number: %r" % (x,))
    text = format(Decimal(repr(x)).normalize(), "f")
    return "0" if text in ("-0", "") else text


def value_text(x, unit):
    """The text that is handed to Fusion for a solver value: '<number> <unit>', or '<number>' without unit."""
    return number_text(x) if unit == "" else "%s %s" % (number_text(x), unit)


def internal_to_user(value, unit):
    """Fusion's internal value (cm, rad) in the unit of the registry (mm, deg)."""
    if unit == "mm":
        return value * 10.0
    if unit == "deg":
        return math.degrees(value)
    return value


def check_rows(rows):
    seen, problems = set(), []
    for row in rows:
        name = row.get("name")
        if not isinstance(name, str) or not NAME_RE.match(name) or name in RESERVED:
            problems.append("bad parameter name %r" % (name,))
            continue
        if name in seen:
            problems.append("duplicate parameter %s" % name)
        seen.add(name)
        if row.get("unit") not in UNITS:
            problems.append("%s: unit %r is not mm, deg or empty" % (name, row.get("unit")))
        if row.get("kind") not in KINDS:
            problems.append("%s: unknown kind %r" % (name, row.get("kind")))
        elif row["kind"] == "solver":
            if row.get("fusion") is not None:
                problems.append("%s: a solver row carries no text" % name)
        else:
            try:
                refs = expr.references(row.get("fusion"))
            except expr.ExprError as exc:
                problems.append("%s: %s" % (name, exc))
                continue
            if row["kind"] == "constant" and refs:
                problems.append("%s: a constant must not reference %s" % (name, refs))
    return problems


def order_rows(rows):
    """Rows in an order in which each can be created: an expression row after every row it references.

    Stable: rows keep their given order unless a reference forces a move. Raises ParamError for a reference
    to an unknown name and for a cycle.
    """
    by_name = {r["name"]: r for r in rows}
    deps = {}
    for r in rows:
        refs = expr.references(r["fusion"]) if r["kind"] == "expression" else []
        unknown = [n for n in refs if n not in by_name]
        if unknown:
            raise ParamError("%s references unknown parameter(s) %s" % (r["name"], ", ".join(unknown)))
        deps[r["name"]] = set(refs)
    out, placed, pending = [], set(), list(rows)
    while pending:
        rest = []
        for r in pending:
            if deps[r["name"]] <= placed:
                out.append(r)
                placed.add(r["name"])
            else:
                rest.append(r)
        if len(rest) == len(pending):
            raise ParamError("cyclic parameter references: %s" % ", ".join(r["name"] for r in rest))
        pending = rest
    return out


def initial_text(row, values):
    """The text a row is created with. A solver row takes its value from the build configuration."""
    if row["kind"] != "solver":
        return row["fusion"]
    if row["name"] not in values:
        raise ParamError("the build configuration has no value for %s" % row["name"])
    return value_text(values[row["name"]], row["unit"])


def set_texts(values, rows):
    """{name: text} for one modifyParameters call. The set must hold exactly the solver rows."""
    solver = {r["name"]: r for r in rows if r["kind"] == "solver"}
    missing = sorted(set(solver) - set(values))
    extra = sorted(set(values) - set(solver))
    if missing or extra:
        raise ParamError("parameter set is not total: missing %s, not in the registry %s" % (missing, extra))
    for name, value in values.items():
        if name.startswith("V_N_") and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
            raise ParamError("%s must be an integer of at least 1, got %r" % (name, value))
    return {name: value_text(values[name], solver[name]["unit"]) for name in sorted(values)}


def check_flags(suppress, flags_in_document):
    """Problems of a set's suppress flags against the flags that have members in the document."""
    problems = []
    for flag in sorted(set(suppress) - set(flags_in_document)):
        problems.append("flag %s has no member in the document" % flag)
    for flag, value in suppress.items():
        if not isinstance(value, bool):
            problems.append("flag %s must be true or false" % flag)
    return problems
