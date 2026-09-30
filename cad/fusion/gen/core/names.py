"""Names of the Fusion modelling kit (issue #81, plan section 3.5).

Standard library only.  A feature, sketch or plane name is ``<Owner>_<Set>_<What>``: three tokens, each
matching ``[A-Z][A-Za-z0-9]*``.  ``What`` of a feature ends with a kind suffix that matches the operation.
The *set* of a name is its first two tokens; one suppress flag switches every object of a set.
"""
from __future__ import annotations

import re


class KitError(Exception):
    """Base class of every error the kit raises for a wrong call (name, expression, phase, ...)."""


class KitNameError(KitError):
    """A name with a wrong grammar, an unknown owner, or a suffix that does not match the operation."""


TOKEN = re.compile(r"[A-Z][A-Za-z0-9]*")

# kind of the call -> suffix of the `What` token (3.5)
SUFFIX = {
    "new": "Body",
    "join": "Add",
    "cut": "Cut",
    "rejoin": "Rejoin",
    "pattern": "Pat",
    "text_cut": "TextCut",
    "text_join": "TextAdd",
}

# Reserved for the enhancement surface of #85 (verdict A9).  #81 creates no such spec: a name with one of
# these suffixes is accepted only on a spec whose phase is "enhance".
RESERVED_SUFFIX = ("Thread", "Fillet", "Chamfer")

# The eight names of `Kit.enhance` that #85 implements (verdict A9); reserved here, not implemented.
ENHANCE_NAMES = ("after", "side_faces", "faces", "edges", "require_thread", "thread", "rule_fillet", "chamfer")

# Tags of the derived names: the sketch of feature N is N + "Sk", the two loft sections N + "SkA" and
# N + "SkB", their planes N + "PlA" and N + "PlB" (3.5).
DERIVED_TAGS = ("Sk", "SkA", "SkB", "PlA", "PlB")

_SET_TOKEN = r"[A-Z][A-Za-z0-9]*"

# Frozen anchor names of 3.3: features that #85 selects by name; a rename is a signature change.
ANCHORS = (
    re.compile(r"Shell_Floor_Body"),
    re.compile(r"Shell_Walls_Add"),
    re.compile(r"Shell_Lid_Body"),
    re.compile(rf"Fastener_{_SET_TOKEN}_BossAdd"),
    re.compile(rf"Fastener_{_SET_TOKEN}_WebAdd"),
    re.compile(rf"Patch_{_SET_TOKEN}_BoreCut"),
)


def _phase_ok(phase: str) -> None:
    if phase not in ("build", "enhance"):
        raise KitNameError(f"unknown phase {phase!r} (build or enhance)")


def parse(name: str) -> tuple[str, str, str]:
    """The three tokens ``(owner, set, what)`` of a name; KitNameError for any other grammar."""
    if not isinstance(name, str):
        raise KitNameError(f"a name is a str, got {type(name).__name__}: {name!r}")
    tokens = name.split("_")
    if len(tokens) != 3 or not all(TOKEN.fullmatch(t) for t in tokens):
        raise KitNameError(f"{name!r}: a name is <Owner>_<Set>_<What>, three tokens matching [A-Z][A-Za-z0-9]*")
    return tokens[0], tokens[1], tokens[2]


def set_of(name: str) -> str:
    """The set of a name: its first two tokens joined by ``_``."""
    owner, set_name, _ = parse(name)
    return f"{owner}_{set_name}"


def check(name: str, owners, kind: str | None, phase: str = "build") -> tuple[str, str, str]:
    """Validate a feature name; returns its three tokens.

    ``owners`` is the owner list of the document (contract C3 of #79).  ``kind`` is a key of SUFFIX, or,
    for ``phase="enhance"`` only, one of ``thread``, ``fillet``, ``chamfer``; ``None`` checks grammar and
    owner only (a sketch or plane name).  Raises KitNameError for a wrong grammar, an unknown owner or a
    suffix that does not match ``kind``."""
    _phase_ok(phase)
    owner, set_name, what = parse(name)
    if owner not in owners:
        raise KitNameError(f"{name!r}: owner {owner!r} is not in the owner list {sorted(owners)}")
    if kind is None:
        return owner, set_name, what
    reserved = {s.lower(): s for s in RESERVED_SUFFIX}
    if kind in reserved:
        if phase != "enhance":
            raise KitNameError(f"{name!r}: the suffix {reserved[kind]} is reserved for the enhancement phase of #85")
        suffix = reserved[kind]
    elif kind in SUFFIX:
        suffix = SUFFIX[kind]
    else:
        raise KitNameError(f"{name!r}: unknown kind {kind!r} (one of {sorted(SUFFIX)})")
    if phase == "build":
        for s in RESERVED_SUFFIX:
            if what.endswith(s):
                raise KitNameError(f"{name!r}: the suffix {s} is reserved for the enhancement phase of #85")
    elif kind in SUFFIX:
        raise KitNameError(f"{name!r}: a spec of phase 'enhance' takes kind thread, fillet or chamfer, not {kind!r}")
    if not what.endswith(suffix):
        raise KitNameError(f"{name!r}: kind {kind!r} needs the suffix {suffix}, '{what}' does not end with it")
    if kind in ("join", "cut") and what.endswith("Text" + suffix):
        raise KitNameError(f"{name!r}: '{what}' ends with Text{suffix}, which belongs to a text feature, not to {kind!r}")
    return owner, set_name, what


def derived(name: str, tag: str) -> str:
    """The name of a sketch or plane derived from a feature name: ``name + tag``; still three tokens."""
    if tag not in DERIVED_TAGS:
        raise KitNameError(f"unknown tag {tag!r} (one of {DERIVED_TAGS})")
    out = name + tag
    parse(out)
    return out


def component_check(name: str) -> str:
    """A component is named in PascalCase, with ``_`` between group and part: ``Base``, ``Reserve_FanBay``."""
    if not isinstance(name, str):
        raise KitNameError(f"a component name is a str, got {type(name).__name__}: {name!r}")
    tokens = name.split("_")
    if len(tokens) not in (1, 2) or not all(TOKEN.fullmatch(t) for t in tokens):
        raise KitNameError(f"{name!r}: a component is PascalCase, optionally <Group>_<Part>")
    return name
