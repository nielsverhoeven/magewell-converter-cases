"""Turn the prose comments of a constants.scad statement into the registry comment
    '<description> | src=<file:line or record id> | conf=<level>'
without inventing anything (transition tool, removed at the cutover).

Levels are the architect's: measured, drawing, manual, photo, assumed, decided.  Rules (mechanical,
every decision is listed by the exporter's report):

  text         the statement's own comments (trailing + continuation); the leading block above it only
               when it has no own text.  Whitespace collapsed.
  src          the FIRST citation in the own text, verbatim: a path ending in .md with an optional
               ':line[-line]', ' §section' (+ ' D41') or ' D41'/' R29' record id, or a bare '<name>.md'
               of the same shapes.  No citation -> 'lib/mcc/constants.scad:<line>' (the statement's own
               first line: a fact, not an invention) and the row is listed as src-defaulted.
  conf         literal rows only (an expression row carries none):
                 'assumed'  the own text or the leading block contains the word "assumed"
                 OVERRIDES  where the source states a level outside the row's own text (each entry quotes
                            its basis); only 'drawing' is used, for the Neutrik figures
                 'decided'  the OWN text says "user decision" / "fixed user decision" / "ACCEPTED"
                 'assumed'  otherwise: the default, listed as conf-defaulted for the manual pass
  description  the first clause of the text up to ', mm' / '. ' / ' -- ' / ' - ' / ';' (max 100 chars);
               DESCRIPTIONS[name] replaces it where it reads badly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_DESC = 100
CONSTANTS_SCAD = "lib/mcc/constants.scad"

_CITE = re.compile(
    r"(?:(?:\.claude/)?(?:knowledge|docs)/[\w./-]+\.md|[\w-]+\.md)"
    r"(?::\d+(?:-\d+)?"
    r"|\s?§\s?\d+(?:\.\d+)*[a-z]?(?:\s+[DRMQ]\d+(?:\.\d+)?)?"
    r"|\s+[DRMQ]\d+(?:\.\d+)?)?")
_DECIDED = re.compile(r"\buser decision\b|\bUSER DECISION\b|\bfixed user decision\b|\bACCEPTED\b", re.I)

# The source states a level outside the row's own comment.  basis = where.
OVERRIDES: dict[str, dict[str, str]] = {
    # constants.scad:49-50 banner "All figures cross-checked from five official Neutrik drawings"
    # applies to the flange footprint / corner radius / screw pitch / screw hole rows, each of which
    # cites its drawing line; the pitch and margin rows below them are recommendations, not drawings.
    "MCC_D_FLANGE_X": {"conf": "drawing", "basis": "constants.scad:49-50 banner + row cites d-series-cutout.md:74"},
    "MCC_D_FLANGE_Y": {"conf": "drawing", "basis": "constants.scad:49-50 banner + row cites d-series-cutout.md:74"},
    "MCC_D_FLANGE_R": {"conf": "drawing", "basis": "constants.scad:49-50 banner + row cites d-series-cutout.md:75-76"},
    "MCC_D_SCREW_PITCH_X": {"conf": "drawing", "basis": "constants.scad:49-50 banner + row cites d-series-cutout.md:47"},
    "MCC_D_SCREW_PITCH_Y": {"conf": "drawing", "basis": "constants.scad:49-50 banner + row cites d-series-cutout.md:47"},
    "MCC_D_SCREW_D": {"conf": "drawing", "basis": "constants.scad:49-50 banner + row cites d-series-cutout.md:49-52"},
}

DESCRIPTIONS: dict[str, str] = {
    # the automatic clause reads badly or is cut; each is a paraphrase of the row's own clause
    "MCC_HOLE_COMP": "hole compensation added to a connector's minimum hole diameter (FDM hole shrink)",
    "MCC_SIDE_BOLT_KEEPOUT_STRIP_W": "width of the vent/rib keep-out strip below the side-bolt keep-out disc",
    "MCC_FLOOR_FEATURE_EDGE_MIN": "minimum edge-to-edge clearance between a floor feature and a non-concentric disc keep-out",
    "MCC_RAIL_SILL_H": "local floor thickening the dovetail groove is cut into (groove depth + residual floor)",
    "MCC_RAIL_Y": "rail/groove centre line Y in case coordinates",
    "MCC_RAIL_LEADIN": "45-degree lead-in where the groove leaves the +X wall (flanks, mouth and roof)",
    "MCC_RAIL_CLR_HORIZ": "per-side horizontal offset of the female groove from the male profile",
    "MCC_RAIL_ROOF_CLR": "gap between the male's flat top (and the lock strips) and the groove roof",
    "MCC_FAN_BAY_CLR": "minimum clearance between the reserved fan bay and any other feature",
    "MCC_VENT_AREA_RATIO": "minimum intake vent free area as a multiple of the fan aperture area",
    "MCC_LID_VENT_AREA_RATIO": "minimum lid-vent free area as a multiple of the fan aperture area",
    "MCC_SWITCH_WELL_DEPTH_MAX": "stop-and-report guard: maximum fan-switch recess depth",
    "MCC_END_ZONE_NEG_EXTRA_SPLITTER": "extra -X end-zone allowance of the reserved splitter bay (size[2] of the default splitter)",
    # defined but not what the geometry uses: the cut computes its own value (see the harvested rows)
    "MCC_SIDE_BOLT_HEAD_REC_D": "unused: head recess of the design notes; the cut makes MCC_SIDE_BOLT_HEAD_CUT_D",
    "MCC_INSERT_BORE_EXTRA": "unused: extra bore depth of the design notes; the bore adds MCC_INSERT_BORE_OVERDEPTH",
}

# Rows that exist only because a one-record table is flattened (MCC_INSERT_M3 -> MCC_INSERT_M3_OD ...).
# The table's comment block states source and level PER FIELD, which prose rules cannot split, so they
# are transcribed here: name -> (description, src, conf, basis).  src '-' = no citation in the block
# (the exporter then uses the table statement's own line).  Nothing is added that the block does not
# say; `basis` names the lines of constants.scad the entry transcribes.  'unspecified' is not a level:
# a field whose block names a source but no level gets the default 'assumed' (conf None here).
FLAT_ROW_META: dict[str, tuple[str, str, str | None, str]] = {
    "MCC_INSERT_M3_HOLE_D": ("M3 heat-set insert (Ruthex RX-M3x5.7): print/drill hole diameter",
                             "knowledge/components/fasteners-and-hardware.md:22", None, "constants.scad:85-90"),
    "MCC_INSERT_M3_OD": ("M3 heat-set insert: sleeve outer diameter", "-", "assumed", "constants.scad:91-94"),
    "MCC_INSERT_M3_LEN": ("M3 heat-set insert: length",
                          "knowledge/components/fasteners-and-hardware.md:17", None, "constants.scad:95"),
    "MCC_INSERT_1_4_20_HOLE_D": ("1/4\"-20 heat-set insert (opt-in floor feature): hole diameter", "-", "assumed",
                                 "constants.scad:102-112"),
    "MCC_INSERT_1_4_20_OD": ("1/4\"-20 heat-set insert: sleeve outer diameter", "-", "assumed", "constants.scad:102-112"),
    "MCC_INSERT_1_4_20_LEN": ("1/4\"-20 heat-set insert: length", "-", "assumed", "constants.scad:102-112"),
    "MCC_INSERT_M4_HOLE_D": ("M4 heat-set insert (unused in lib/mcc): hole diameter", "-", "assumed", "constants.scad:115-126"),
    "MCC_INSERT_M4_OD": ("M4 heat-set insert (unused in lib/mcc): sleeve outer diameter", "-", "assumed",
                         "constants.scad:115-126"),
    "MCC_INSERT_M4_LEN": ("M4 heat-set insert (unused in lib/mcc): length", "-", "assumed", "constants.scad:115-126"),
    "MCC_SIDE_BOLT_CLIP_GROOVE_D": ("DIN 6799 size 5 E-clip: retaining groove diameter", "layout-patch-wall.md §7.1",
                                    "assumed", "constants.scad:183-187"),
    "MCC_SIDE_BOLT_CLIP_GROOVE_W": ("DIN 6799 size 5 E-clip: groove width", "layout-patch-wall.md §7.1",
                                    "assumed", "constants.scad:183-187"),
    "MCC_SIDE_BOLT_CLIP_OD": ("DIN 6799 size 5 E-clip: clip outer diameter", "layout-patch-wall.md §7.1",
                              "assumed", "constants.scad:183-187"),
    "MCC_SIDE_BOLT_CLIP_T": ("DIN 6799 size 5 E-clip: clip thickness", "layout-patch-wall.md §7.1",
                             "assumed", "constants.scad:183-187"),
}


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def first_citation(text: str) -> str:
    m = _CITE.search(text)
    return collapse(m.group(0)) if m else "-"


def has_assumed(text: str) -> bool:
    return re.search(r"\bassumed\b", text, re.I) is not None


_CUT = re.compile(r",\s*(?:mm|deg)\b|\s+\(mm\)|\.\s|\s--\s|\s—\s|;\s|\s-\s")


def first_clause(text: str, limit: int = MAX_DESC) -> str:
    t = collapse(text)
    t = re.sub(r"^=\s*[-\d.]+\.?\s*", "", t)            # '= 7.0. Local floor ...' -> 'Local floor ...'
    t = re.sub(r"^(?:assumed|derived)\s*(?:--|—|-)\s*", "", t, flags=re.I)
    m = _CUT.search(t)
    clause = t[: m.start()] if m else t
    clause = clause.rstrip(" ,:;.")
    if len(clause) > limit:
        clause = clause[: limit - 3].rsplit(" ", 1)[0].rstrip(" ,:;.") + "..."
    return clause


@dataclass(frozen=True)
class Meta:
    description: str
    src: str
    conf: str | None           # None for an expression row
    src_defaulted: bool        # no citation: src is the constants.scad line
    conf_defaulted: bool       # no level stated: default 'assumed'
    decided_basis: str = ""    # the phrase that made the row 'decided'


def meta_for(name: str, own: str, leading: str, line: int, *, literal: bool, scad_file: str = CONSTANTS_SCAD) -> Meta:
    desc = DESCRIPTIONS.get(name) or first_clause(own or leading) or name
    cite = first_citation(own) if own else first_citation(leading)
    src_defaulted = cite == "-"
    src = f"{scad_file}:{line}" if src_defaulted else cite
    if not literal:
        return Meta(desc, src, None, src_defaulted, False)
    if has_assumed(own + " " + leading):
        return Meta(desc, src, "assumed", src_defaulted, False)
    if name in OVERRIDES:
        return Meta(desc, src, OVERRIDES[name]["conf"], src_defaulted, False)
    m = _DECIDED.search(own)
    if m:
        return Meta(desc, src, "decided", src_defaulted, False, decided_basis=m.group(0))
    return Meta(desc, src, "assumed", src_defaulted, True)
