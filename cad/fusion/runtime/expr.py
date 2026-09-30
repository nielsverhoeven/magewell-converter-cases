"""Fusion expression subset: tokeniser, parser, normal form, reference and literal analysis.

Pure Python, standard library only.

Grammar (what a dimension may use, plus what is needed to read Fusion's echo):
    expr  := term (('+' | '-') term)*
    term  := unary (('*' | '/') unary)*
    unary := ('-' | '+') unary | atom
    atom  := NUMBER [UNIT] | NAME '(' expr ((';' | ',') expr)* ')' | NAME | '(' expr ')'
A UNIT is a name from UNITS that directly follows a NUMBER (white space allowed).
"""
import re
from decimal import Decimal, InvalidOperation

UNITS = frozenset({"mm", "cm", "m", "in", "ft", "deg", "rad"})
ALLOWED_UNITS = frozenset({"mm", "deg"})
ALLOWED_FUNCTIONS = frozenset({"min", "max", "sin", "cos", "tan", "asin", "acos", "atan"})
FORBIDDEN_FUNCTIONS = frozenset({"floor", "ceil", "round", "if"})

_TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>[-+*/^();,])
""", re.VERBOSE)


class ExprError(ValueError):
    pass


def tokenize(text):
    out, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if m is None:
            raise ExprError("unexpected character %r at %d in %r" % (text[pos], pos, text))
        pos = m.end()
        kind = m.lastgroup
        if kind != "ws":
            out.append((kind, m.group(kind)))
    return out


# AST nodes are tuples: ("num", "2.5", unit|None) ("ref", name) ("neg", x) ("bin", op, a, b) ("call", fn, [args])
class _Parser:
    def __init__(self, text):
        self.text, self.toks, self.i = text, tokenize(text), 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect(self, value):
        kind, val = self.take()
        if val != value:
            raise ExprError("expected %r, found %r in %r" % (value, val, self.text))

    def parse(self):
        if not self.toks:
            raise ExprError("empty expression")
        node = self.expr()
        if self.i != len(self.toks):
            raise ExprError("unexpected %r in %r" % (self.peek()[1], self.text))
        return node

    def expr(self):
        node = self.term()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            node = ("bin", op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            node = ("bin", op, node, self.unary())
        return node

    def unary(self):
        if self.peek()[1] == "-":
            self.take()
            return ("neg", self.unary())
        if self.peek()[1] == "+":
            self.take()
            return self.unary()
        return self.atom()

    def atom(self):
        kind, val = self.take()
        if kind == "num":
            unit = None
            nk, nv = self.peek()
            if nk == "name" and nv in UNITS:
                self.take()
                unit = nv
            return ("num", _canon_number(val), unit)
        if kind == "name":
            if self.peek()[1] == "(":
                self.take()
                args = [self.expr()]
                while self.peek()[1] in (";", ","):
                    self.take()
                    args.append(self.expr())
                self.expect(")")
                return ("call", val, args)
            return ("ref", val)
        if val == "(":
            node = self.expr()
            self.expect(")")
            return node
        raise ExprError("unexpected %r in %r" % (val, self.text))


def _canon_number(text):
    try:
        d = Decimal(text)
    except InvalidOperation:
        raise ExprError("bad number %r" % text)
    s = format(d.normalize(), "f")
    return "0" if s in ("-0", "") else s


def parse(text):
    if not isinstance(text, str):
        raise ExprError("an expression is a string, got %r" % (text,))
    return _Parser(text).parse()


_PREC = {"+": 1, "-": 1, "*": 2, "/": 2}


def _prec(node):
    if node[0] == "bin":
        return _PREC[node[1]]
    if node[0] == "neg":
        return 3
    return 4


def emit(node):
    kind = node[0]
    if kind == "num":
        return node[1] if node[2] is None else "%s %s" % (node[1], node[2])
    if kind == "ref":
        return node[1]
    if kind == "neg":
        inner = emit(node[1])
        return "-(%s)" % inner if _prec(node[1]) < 3 else "-" + inner
    if kind == "call":
        return "%s(%s)" % (node[1], "; ".join(emit(a) for a in node[2]))
    op, a, b = node[1], node[2], node[3]
    left = emit(a)
    if _prec(a) < _PREC[op]:
        left = "(%s)" % left
    right = emit(b)
    if _prec(b) < _PREC[op] or (_prec(b) == _PREC[op] and b[0] == "bin" and op in ("-", "/")):
        right = "(%s)" % right
    return "%s %s %s" % (left, op, right)


def normalise(text):
    """Canonical text of an expression: single spaces, shortest numbers, minimal parentheses, ';' separators."""
    return emit(parse(text))


def references(text):
    """Sorted parameter names that the expression refers to (function names and units excluded)."""
    found = set()

    def walk(node):
        kind = node[0]
        if kind == "ref":
            found.add(node[1])
        elif kind == "neg":
            walk(node[1])
        elif kind == "bin":
            walk(node[2])
            walk(node[3])
        elif kind == "call":
            for a in node[2]:
                walk(a)
    walk(parse(text))
    return sorted(found)


def is_literal(text):
    """True when the expression references no parameter at all (for example '3 mm', '2 * 1.5')."""
    return not references(text)


def violations(text):
    """Reasons why the expression is outside the allowed subset. Empty list = allowed."""
    out = []

    def walk(node, factor):
        kind = node[0]
        if kind == "num":
            if node[2] is not None and node[2] not in ALLOWED_UNITS:
                out.append("unit %r is not allowed" % node[2])
            if not factor:
                out.append("number %s is used as a dimension, not as a factor" % emit(node))
            elif node[2] is not None:
                out.append("factor %s carries a unit" % emit(node))
        elif kind == "neg":
            walk(node[1], factor)
        elif kind == "bin":
            mult = node[1] in ("*", "/")
            walk(node[2], mult)
            walk(node[3], mult)
        elif kind == "call":
            if node[1] in FORBIDDEN_FUNCTIONS:
                out.append("function %r is forbidden" % node[1])
            elif node[1] not in ALLOWED_FUNCTIONS:
                out.append("function %r is not in the allowed list" % node[1])
            for a in node[2]:
                walk(a, False)
    try:
        tree = parse(text)
    except ExprError as exc:
        return [str(exc)]
    if tree[0] == "num" or (tree[0] == "neg" and tree[1][0] == "num"):
        return ["expression is a bare number"]
    walk(tree, False)
    return out
