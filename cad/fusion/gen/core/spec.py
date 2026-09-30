"""Specs: what the facade decides and a backend executes (issue #81, plan sections 3.1, 3.6 to 3.9, 3.14).

The facade validates names and expressions once, decides which dimensions and constraints a sketch gets and
writes them into these frozen dataclasses.  The recording backend stores them; the Fusion backend executes
them.  Both therefore see the same design.  Standard library only.

Every spec has the field ``phase`` (default ``"build"``; ``"enhance"`` is reserved for the enhancement
surface of #85, verdict A9) and a method ``to_json()`` that returns plain dicts, lists, strings and numbers.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from .names import KitError

PHASES = ("build", "enhance")


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return value


class _Spec:
    """Mixin: the phase check and ``to_json``."""

    def __post_init__(self):
        if self.phase not in PHASES:
            raise KitError(f"{type(self).__name__}: phase {self.phase!r} is not one of {PHASES}")

    def to_json(self) -> dict:
        return _plain(self)


@dataclass(frozen=True)
class Loop(_Spec):
    """One closed outline: ``kind`` is ``rect``, ``circle`` or ``polygon``; ``args`` are expression strings
    (a polygon: a tuple of ``(u, v)`` pairs)."""

    kind: str
    args: tuple
    phase: str = "build"


@dataclass(frozen=True)
class Dim(_Spec):
    """A driving dimension of a sketch; ``text`` is the expression, ``a`` and ``b`` name what it measures."""

    kind: str
    a: str
    b: str
    axis: str
    text: str
    phase: str = "build"


@dataclass(frozen=True)
class Constraint(_Spec):
    kind: str
    a: str
    b: str
    phase: str = "build"


@dataclass(frozen=True)
class SketchSpec(_Spec):
    name: str
    component: str
    on: str
    datum: tuple
    loops: tuple
    holes: tuple
    points: tuple
    lines: tuple
    circles: tuple
    constraints: tuple
    dims: tuple
    profiles: int
    rule: str
    texts: tuple = ()
    phase: str = "build"


@dataclass(frozen=True)
class PlaneSpec(_Spec):
    name: str
    component: str
    base: str
    offset: str | None
    phase: str = "build"


@dataclass(frozen=True)
class ExtrudeSpec(_Spec):
    name: str
    component: str
    sketch: str
    start_offset: str | None
    distance: str
    direction: str
    op: str
    within: str | None = None
    phase: str = "build"


@dataclass(frozen=True)
class LoftSpec(_Spec):
    name: str
    component: str
    sketches: tuple
    planes: tuple
    op: str
    phase: str = "build"


@dataclass(frozen=True)
class PatternSpec(_Spec):
    name: str
    component: str
    seed: str
    axis: str
    count: str
    pitch: str
    axis2: str | None = None
    count2: str | None = None
    pitch2: str | None = None
    phase: str = "build"


@dataclass(frozen=True)
class TextSpec(_Spec):
    name: str
    component: str
    sketch: str
    frame: Loop
    string: str
    height: str
    halign: str
    valign: str
    font: str
    style: str
    start_offset: str | None
    distance: str
    direction: str
    op: str
    phase: str = "build"


@dataclass(frozen=True)
class ComponentSpec(_Spec):
    name: str
    role: str
    datum: tuple
    phase: str = "build"


@dataclass(frozen=True)
class SharedCall(_Spec):
    """One call of a shared builder (3.10): the builder id, its arguments, which of them are placement, the names
    produced inside the call, and the parent call when it was opened inside another."""

    builder_id: str
    arguments: dict
    placement: tuple
    produced: list = field(default_factory=list)
    parent: str | None = None
    phase: str = "build"
