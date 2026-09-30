"""Expressions of the Fusion modelling kit (issue #81, plan section 3.4).

A builder writes a dimension as an expression string in the neutral grammar of ``cad.params`` (arguments
separated by commas), restricted to arch brief D.5::

    expr   := term (("+" | "-") term)*
    term   := unary (("*" | "/") unary)*
    unary  := "-" unary | atom
    atom   := NAME | FACTOR | FUNC "(" expr ("," expr)* ")" | "(" expr ")"
    NAME   := any name of the document's registry (the kit holds no prefix list)
    FACTOR := an unsigned number without unit, allowed only as a direct operand of "*" or "/"
    FUNC   := min | max | sin | cos | tan

Standard library only.  ``cad.params`` is imported inside the two wrappers at the bottom (``Env`` and
``fusion``), the only users of it in the generator, so the rest of this module runs without it.
"""
from __future__ import annotations

import re

from .names import KitError


class LiteralError(KitError):
    """A typed number: no parameter name in the expression, a number with a unit, or a number that is not a
    direct operand of * or /."""


class UnknownNameError(KitError):
    """A NAME that is not in the registry of the document."""


class GrammarError(KitError):
    """Any token or shape the grammar above does not allow (floor, ceil, round, if, sqrt, ^, a comparison, ...)."""


FUNCS = ("min", "max", "sin", "cos", "tan")
UNITS = ("mm", "deg")

_TOKEN = re.compile(
    r"\s*(?:(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>[-+*/(),]))"
)


def _where(where: str) -> str:
    return f"{where}: " if where else ""


def _need_str(text, what: str = "an expression") -> str:
    if not isinstance(text, str):
        raise TypeError(f"{what} is a str (a parameter expression), got {type(text).__name__}: {text!r}")
    return text


def _tokens(text: str, where: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    i = 0
    while text[i:].strip():
        m = _TOKEN.match(text, i)
        if not m:
            raise GrammarError(f"{_where(where)}cannot tokenize {text[i:].strip()[:20]!r} in {text!r}")
        i = m.end()
        out.append((m.lastgroup, m.group(m.lastgroup)))
    return out


# node shapes: ("num", text) ("name", n) ("neg", x) ("paren", x) ("bin", op, l, r) ("call", fn, [args])
class _Parser:
    def __init__(self, text: str, where: str):
        self.text, self.where = text, where
        self.toks = _tokens(text, where)
        self.i = 0

    def _err(self, msg: str) -> GrammarError:
        return GrammarError(f"{_where(self.where)}{msg} in {self.text!r}")

    def peek(self) -> tuple[str | None, str | None]:
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, want: str | None = None) -> tuple[str, str]:
        t = self.peek()
        if t[0] is None or (want is not None and t[1] != want):
            raise self._err(f"expected {want!r}" if want else "unexpected end")
        self.i += 1
        return t

    def parse(self):
        if not self.toks:
            raise self._err("empty expression")
        node = self.sum()
        if self.peek()[0] is not None:
            raise self._err(f"unexpected token {self.peek()[1]!r}")
        return node

    def sum(self):
        n = self.term()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            n = ("bin", op, n, self.term())
        return n

    def term(self):
        n = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            n = ("bin", op, n, self.unary())
        return n

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take()
            return ("neg", self.unary())
        return self.atom()

    def atom(self):
        kind, tok = self.take()
        if kind == "num":
            nxt = self.peek()
            if nxt[0] == "name":
                if nxt[1] in UNITS:
                    raise LiteralError(f"{_where(self.where)}the number {tok} carries the unit {nxt[1]!r} in {self.text!r}; "
                                       "a dimension is a parameter name, a number is only a factor")
                raise self._err(f"unexpected token {nxt[1]!r} after the number {tok}")
            return ("num", tok)
        if kind == "name":
            if self.peek() == ("op", "("):
                if tok not in FUNCS:
                    raise self._err(f"function {tok}() is not allowed (only {', '.join(FUNCS)})")
                self.take("(")
                args = [self.sum()]
                while self.peek() == ("op", ","):
                    self.take(",")
                    args.append(self.sum())
                self.take(")")
                if tok in ("sin", "cos", "tan") and len(args) != 1:
                    raise self._err(f"{tok}() takes one argument")
                return ("call", tok, args)
            return ("name", tok)
        if tok == "(":
            inner = self.sum()
            self.take(")")
            return ("paren", inner)
        raise self._err(f"unexpected token {tok!r}")


def _parse(text: str, where: str = ""):
    return _Parser(_need_str(text), where).parse()


def _names(node) -> set[str]:
    kind = node[0]
    if kind == "name":
        return {node[1]}
    if kind == "num":
        return set()
    if kind in ("neg", "paren"):
        return _names(node[1])
    if kind == "bin":
        return _names(node[2]) | _names(node[3])
    return set().union(*(_names(a) for a in node[2]))


def _placement(node, direct_operand: bool, text: str, where: str) -> None:
    """A number is allowed only as a direct operand of * or /."""
    kind = node[0]
    if kind == "num":
        if not direct_operand:
            raise LiteralError(f"{_where(where)}the number {node[1]} in {text!r} is not a direct operand of * or /; "
                               "a length is a parameter name")
    elif kind in ("neg", "paren"):
        _placement(node[1], False, text, where)
    elif kind == "bin":
        ok = node[1] in ("*", "/")
        _placement(node[2], ok, text, where)
        _placement(node[3], ok, text, where)
    elif kind == "call":
        for a in node[2]:
            _placement(a, False, text, where)


def check(text, names, where: str = "") -> None:
    """Validate a builder expression against the grammar above and the registry ``names``.

    ``where`` names the feature and the argument (``"Cradle_Deck_FrameAdd.start"``) and starts every message.
    Raises TypeError (not a str), GrammarError, LiteralError, UnknownNameError."""
    node = _parse(text, where)
    used = _names(node)
    if not used:
        raise LiteralError(f"{_where(where)}{text!r} names no parameter; a dimension is an expression of registry names")
    _placement(node, False, text, where)
    for n in sorted(used):
        if n not in names:
            raise UnknownNameError(f"{_where(where)}unknown name {n!r} in {text!r}")


def names_in(text) -> set[str]:
    """The parameter names an expression refers to (grammar errors raise; nothing else is checked)."""
    return _names(_parse(text))


def _norm_tokens(text) -> list[tuple[str, str]] | None:
    if text is None:
        return None
    toks = _tokens(_need_str(text))
    while len(toks) >= 2 and toks[0] == ("op", "(") and toks[-1] == ("op", ")"):
        depth = 0
        for i, t in enumerate(toks):
            depth += t == ("op", "(")
            depth -= t == ("op", ")")
            if depth == 0 and i < len(toks) - 1:
                return toks  # the first "(" closes before the end: not an outer pair
        toks = toks[1:-1]
    return toks


def same(a, b) -> bool:
    """Equal token lists after dropping outer parentheses; ``None`` equals ``None`` only."""
    return _norm_tokens(a) == _norm_tokens(b)


# ---- composition helpers: pure string functions that add the parentheses that are needed ------------------------


def _prec(text: str) -> int:
    """1 sum at top level, 2 product at top level, 3 leading unary minus, 4 atom, call or parenthesis."""
    toks = _tokens(text)
    depth, prod = 0, False
    for i, (kind, val) in enumerate(toks):
        if kind != "op":
            continue
        if val == "(":
            depth += 1
        elif val == ")":
            depth -= 1
        elif depth == 0:
            binary = i > 0 and (toks[i - 1][0] in ("num", "name") or toks[i - 1][1] == ")")
            if val in ("+", "-") and binary:
                return 1
            if val in ("*", "/"):
                prod = True
    if prod:
        return 2
    return 3 if toks and toks[0] == ("op", "-") else 4


def _wrap(text: str, below: int) -> str:
    return f"({text})" if _prec(text) <= below else text


def add(*parts):
    """Sum of the parts; ``None`` stands for zero (``add(None, "V_X")`` is ``"V_X"``); all ``None`` gives ``None``."""
    kept = [_need_str(p) for p in parts if p is not None]
    return " + ".join(kept) if kept else None


def sub(a, b):
    """``a - b``; ``None`` stands for zero (``sub(None, "V_X")`` is ``"-(V_X)"``)."""
    if b is None:
        return None if a is None else _need_str(a)
    if a is None:
        return f"-({_need_str(b)})"
    return f"{_need_str(a)} - {_wrap(_need_str(b), 1)}"


def neg(a):
    return f"-({_need_str(a)})"


def mul(a, b):
    return f"{_wrap(_need_str(a), 1)} * {_wrap(_need_str(b), 1)}"


def div(a, b):
    return f"{_wrap(_need_str(a), 1)} / {_wrap(_need_str(b), 2)}"


def half(a):
    return div(a, "2")


def twice(a):
    return mul(a, "2")


def mn(a, b):
    return f"min({_need_str(a)}, {_need_str(b)})"


def mx(a, b):
    return f"max({_need_str(a)}, {_need_str(b)})"


# ---- the two wrappers around cad.params (the only ones in the generator) -----------------------------------------


class Env:
    """The numbers of one parameter set: ``Env(registry_rows, values)``.

    ``registry_rows`` are the registry rows the runtime hands a builder (dicts with ``name``, ``unit``, ``kind``,
    ``expression``, ``fusion``); ``values`` are the solver outputs of the configuration.  ``names`` is the set of
    registry names; ``value(text)`` is the number of one expression."""

    def __init__(self, registry_rows, values):
        from cad import params  # inside the body: the rest of this module needs no cad.params

        rows = list(registry_rows)
        self.names = frozenset(row["name"] for row in rows)
        self.units = {row["name"]: row["unit"] for row in rows if row["kind"] == "solver"}
        self._env = params.environment(rows, {"values": dict(values), "units": self.units})
        self._params = params

    def value(self, text) -> float:
        return self._params.evaluate_number(_need_str(text), self._env)


def fusion(text) -> str:
    """The expression in Fusion's spelling (arguments separated by ``;``): the one emitter is ``cad.params``."""
    from cad import params

    return params.emit_fusion(_need_str(text))
