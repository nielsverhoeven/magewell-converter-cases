"""Translate the derived-constant expressions of lib/mcc/constants.scad into Fusion syntax
(transition tool).

Input is the right-hand-side SOURCE TEXT of one statement; output is an expression of the NEUTRAL
grammar of cad/params.py (no Fusion syntax: arguments stay comma separated; cad.params.emit_fusion()
is the only Fusion emitter) in which
  * vector components are flat parameters              MCC_D_FLANGE[1]     -> MCC_D_FLANGE_H
  * a one-record table lookup is a flat parameter      struct_val(MCC_INSERT_M3, "od")
                                                                           -> MCC_INSERT_M3_OD
  * every bare number that meets a dimensioned operand gets that operand's unit
        MCC_A + MCC_B + 1.0          -> MCC_A + MCC_B + 1.0 mm
        max(0, MCC_A - MCC_B)        -> max(0 mm, MCC_A - MCC_B)
        MCC_X - 2 * MCC_D / tan(MCC_ANGLE)   (angle parameter feeds tan unchanged)
Anything the translator does not understand raises ScadExprError, so a new statement shape is
reported instead of mistranslated.  The result is always re-evaluated by cad.params and compared
with OpenSCAD's own value before it is written (scad_export.py).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from cad.params import ANGLE, LENGTH, NONE, Dim


class ScadExprError(ValueError):
    pass


# ----- AST ----------------------------------------------------------------------------------------


@dataclass
class Num:
    text: str


@dataclass
class Name:
    name: str


@dataclass
class Str:
    text: str


@dataclass
class Index:
    base: "Node"
    index: int


@dataclass
class Call:
    fn: str
    args: list


@dataclass
class Bin:
    op: str
    left: "Node"
    right: "Node"


@dataclass
class Neg:
    operand: "Node"


@dataclass
class Paren:
    inner: "Node"


Node = Num | Name | Str | Index | Call | Bin | Neg | Paren

_TOK = re.compile(r'\s*(?:(?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)'
                  r'|(?P<str>"[^"]*")|(?P<op>[-+*/()\[\],]))')


def _tokens(text: str) -> list[tuple[str, str]]:
    out, i = [], 0
    while i < len(text) and text[i:].strip():
        m = _TOK.match(text, i)
        if not m:
            raise ScadExprError(f"cannot tokenize {text[i:i + 25]!r}")
        i = m.end()
        out.append((m.lastgroup, m.group(m.lastgroup)))
    return out


class _P:
    def __init__(self, text: str):
        self.t, self.i = _tokens(text), 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, want=None):
        k, v = self.peek()
        if k is None or (want is not None and v != want):
            raise ScadExprError(f"expected {want!r}")
        self.i += 1
        return k, v

    def parse(self) -> Node:
        n = self.sum()
        if self.peek()[0] is not None:
            raise ScadExprError(f"trailing token {self.peek()[1]!r}")
        return n

    def sum(self) -> Node:
        n = self.term()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            n = Bin(op, n, self.term())
        return n

    def term(self) -> Node:
        n = self.unary()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            n = Bin(op, n, self.unary())
        return n

    def unary(self) -> Node:
        if self.peek()[1] == "-":
            self.take()
            return Neg(self.unary())
        return self.postfix()

    def postfix(self) -> Node:
        n = self.atom()
        while self.peek()[1] == "[":
            self.take("[")
            k, v = self.take()
            if k != "num":
                raise ScadExprError("only numeric literal indices are supported")
            self.take("]")
            n = Index(n, int(v))
        return n

    def atom(self) -> Node:
        k, v = self.take()
        if k == "num":
            return Num(v)
        if k == "str":
            return Str(v[1:-1])
        if k == "name":
            if self.peek()[1] == "(":
                self.take("(")
                args = [self.sum()]
                while self.peek()[1] == ",":
                    self.take(",")
                    args.append(self.sum())
                self.take(")")
                return Call(v, args)
            return Name(v)
        if v == "(":
            inner = self.sum()
            self.take(")")
            return Paren(inner)
        raise ScadExprError(f"unexpected token {v!r}")


def parse(text: str) -> Node:
    return _P(text).parse()


# ----- rewriting of lookups -------------------------------------------------------------------------


def _rewrite(n: Node, vectors: dict[str, tuple[str, ...]], flat_tables: dict[str, dict[str, str]]) -> Node:
    """Replace NAME[i] by the flat component parameter and struct_val(TABLE, "field") by the flat
    table parameter.  `flat_tables[TABLE][field]` is the flat parameter name."""
    if isinstance(n, Index) and isinstance(n.base, Name):
        comps = vectors.get(n.base.name)
        if comps is None:
            raise ScadExprError(f"{n.base.name}[{n.index}]: not a known numeric vector")
        return Name(comps[n.index])
    if isinstance(n, Call):
        if n.fn == "struct_val":
            if len(n.args) == 2 and isinstance(n.args[0], Name) and isinstance(n.args[1], Str):
                tbl = flat_tables.get(n.args[0].name)
                if tbl is None or n.args[1].text not in tbl:
                    raise ScadExprError(f"struct_val({n.args[0].name}, {n.args[1].text!r}) is not a flat table")
                return Name(tbl[n.args[1].text])
            raise ScadExprError("struct_val with a computed table is not supported")
        return Call(n.fn, [_rewrite(a, vectors, flat_tables) for a in n.args])
    if isinstance(n, Bin):
        return Bin(n.op, _rewrite(n.left, vectors, flat_tables), _rewrite(n.right, vectors, flat_tables))
    if isinstance(n, Neg):
        return Neg(_rewrite(n.operand, vectors, flat_tables))
    if isinstance(n, Paren):
        return Paren(_rewrite(n.inner, vectors, flat_tables))
    if isinstance(n, (Num, Name, Str)):
        return n
    raise ScadExprError(f"unsupported node {n!r}")


# ----- dimension inference and printing -------------------------------------------------------------

UNIT_OF_DIM = {LENGTH: "mm", ANGLE: "deg"}


def _infer(n: Node, dims: dict[str, Dim]) -> Dim | None:
    """Dimension of a node; None = bare number (literal-only subtree, takes the dimension it meets)."""
    if isinstance(n, Num):
        return None
    if isinstance(n, Name):
        if n.name not in dims:
            raise ScadExprError(f"unknown parameter {n.name}")
        return dims[n.name]
    if isinstance(n, Paren):
        return _infer(n.inner, dims)
    if isinstance(n, Neg):
        return _infer(n.operand, dims)
    if isinstance(n, Bin):
        dl, dr = _infer(n.left, dims), _infer(n.right, dims)
        if n.op in "+-":
            if dl is None:
                return dr
            if dr is None or dr == dl:
                return dl
            raise ScadExprError(f"unit mismatch {dl} {n.op} {dr}")
        a, b = dl or NONE, dr or NONE
        if dl is None and dr is None:
            return None
        if n.op == "*":
            return (a[0] + b[0], a[1] + b[1])
        return (a[0] - b[0], a[1] - b[1])
    if isinstance(n, Call):
        ds = [_infer(a, dims) for a in n.args]
        if n.fn in ("max", "min"):
            known = {d for d in ds if d is not None}
            if len(known) > 1:
                raise ScadExprError(f"{n.fn}() arguments differ in unit: {sorted(known)}")
            return known.pop() if known else None
        if n.fn in ("sin", "cos", "tan"):
            if ds[0] not in (None, ANGLE):
                raise ScadExprError(f"{n.fn}() needs an angle argument, got {ds[0]}")
            return NONE
        if n.fn == "abs":
            return ds[0]
        raise ScadExprError(f"function {n.fn}() is not supported")
    raise ScadExprError(f"cannot infer {n!r}")


def _emit(n: Node, dims: dict[str, Dim], want: Dim | None) -> str:
    """Print a node; `want` is the dimension a bare number must be given here (None = plain)."""
    if isinstance(n, Num):
        if want is not None and want != NONE:
            return f"{n.text} {UNIT_OF_DIM[want]}"
        return n.text
    if isinstance(n, Name):
        return n.name
    if isinstance(n, Paren):
        return f"({_emit(n.inner, dims, want)})"
    if isinstance(n, Neg):
        return f"-{_emit(n.operand, dims, want)}"
    if isinstance(n, Bin):
        dl, dr = _infer(n.left, dims), _infer(n.right, dims)
        if n.op in "+-":
            d = dl if dl is not None else dr
            d = d if d is not None else want
            return f"{_emit(n.left, dims, d)} {n.op} {_emit(n.right, dims, d)}"
        # * and /: a bare side stays plain, except that a bare-only product/quotient that must
        # carry a unit puts it on its right-most number
        if dl is None and dr is None:
            if want is not None and want != NONE:
                return f"{_emit(n.left, dims, None)} {n.op} {_emit(n.right, dims, want)}"
            return f"{_emit(n.left, dims, None)} {n.op} {_emit(n.right, dims, None)}"
        return f"{_emit(n.left, dims, None)} {n.op} {_emit(n.right, dims, None)}"
    if isinstance(n, Call):
        if n.fn in ("max", "min"):
            ds = [_infer(a, dims) for a in n.args]
            d = next((x for x in ds if x is not None), want)
            return f"{n.fn}({', '.join(_emit(a, dims, d) for a in n.args)})"
        if n.fn in ("sin", "cos", "tan"):
            return f"{n.fn}({_emit(n.args[0], dims, ANGLE)})"
        return f"{n.fn}({', '.join(_emit(a, dims, want) for a in n.args)})"
    raise ScadExprError(f"cannot print {n!r}")


def translate(rhs: str, *, dims: dict[str, Dim], vectors: dict[str, tuple[str, ...]],
              flat_tables: dict[str, dict[str, str]]) -> tuple[str, Dim]:
    """OpenSCAD right-hand side -> (Fusion expression, dimension).  `dims` maps every parameter
    name the expression may use (flat names included) to its dimension."""
    node = _rewrite(parse(rhs), vectors, flat_tables)
    dim = _infer(node, dims)
    if dim is None:
        raise ScadExprError("expression has no parameter in it (a literal): not a derived row")
    return _emit(node, dims, dim), dim
