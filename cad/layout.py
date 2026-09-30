"""The case solver (P1 of 01-ARCH-BRIEF section B), issue #77: a line-by-line Python port of the pure functions of

    lib/mcc/layout.scad      mcc_case_layout(), mcc_end_zone(), mcc_slot_assignment(), mcc_floor_keepout(), ...
    lib/mcc/ports.scad       the device and port accessors
    lib/mcc/constants.scad   the pure accessors (panel parts, fans, switches, per-kind maps)
    lib/mcc/poe_splitter.scad  mcc_splitter_spec()
    lib/mcc/vents.scad       _mcc_vent_slot_centers, _mcc_far_wall_excl, _mcc_lid_vent_field, the list logic of mcc_vents()
    lib/mcc/cradle.scad      _mcc_cradle_deck_grid, _mcc_far_flank_rib_x, the patch-flank rib rule
    lib/mcc/fasteners.scad   mcc_side_bolt_keepout(), the insert bore depth
    lib/mcc/fan.scad         the finger-guard ring arithmetic and the round opening
    lib/mcc/switch.scad      the pad and recess thickness, the bore
    lib/mcc/shell.scad       the top of the base walls, the boss diameter, the gusset web

and the writer of the generated parameter sets cad/parameters/variants/<slug>.json, whose key set is the contract
with the case master (P2-81 section 3.5: 99 V_ keys, 24 suppress flags).

Rules of this module
  * Pure functions over cad.params data; no adsk, no scripts/, no file writes except write_variants().
  * Same operations in the same order as the OpenSCAD source, so IEEE results are bit-identical where the
    source only adds, subtracts, multiplies and divides (tests compare with 1e-9 mm; integers and order exact).
  * The Tier-1 asserts inside the OpenSCAD functions are NOT here: a check has one home, cad/rules.py (#78) -- except
    the eight that mean "no total parameter set exists" (T1-02, T1-39, T1-81.2 to T1-81.7): their one home is
    capacity_problems() (gate B1 of #77).
    solve() raises SolverError only where it cannot compute; a case the master cannot hold is solved anyway
    and parameter_set() refuses it with CapacityError (capacity_problems() lists every reason).
  * Every literal that used to sit in the OpenSCAD functions is a registry row (MCC_STRAP_X_INSET, ...).
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cad import params
from cad.numeric import floor_, fmt_num, max_of, min_of, round_half_away, sort_lex

EPS_NAME = "MCC_EPS"


class SolverError(ValueError):
    """The solver cannot compute a result (an unknown table name, a port the side-exit topology cannot place).
    A design-rule violation is not an error here: those are the rules of cad/rules.py (#78)."""


class CapacityError(SolverError):
    """The solved case does not fit the master's fixed topology (P2-81 section 3.3), so no parameter set can
    be written for it.  Raised by parameter_set() only; solve() still returns the numbers."""


# ---------------------------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Port:
    id: str
    face: tuple[int, int, int]
    pos: tuple[float, float]
    kind: str
    dir: str
    panel: str
    confidence: str


@dataclass(frozen=True)
class Device:
    slug: str
    family: str
    size: tuple[float, float, float]
    ports: tuple[Port, ...]


@dataclass(frozen=True)
class Options:
    """The options of one solved case: the closed list of a case definition (params.CASE_OPTIONS) plus `tripod_insert`,
    which left that list (P2-81 Q81.3) but is still an OpenSCAD cfg key: a case that sets it is refused by
    capacity_problems() (T1-81.7).  `fan_switch` None = follow `fan` (mcc_fan_switch_enabled); `fan_y` None = the
    device's own Y centre (R20)."""
    fan: bool = False
    splitter: bool = False
    fan_switch: bool | None = None
    tripod_insert: bool = False
    lid_vents: bool = True
    rail: bool = True
    fan_y: float | None = None

    @property
    def sw_enabled(self) -> bool:
        return self.fan if self.fan_switch is None else self.fan_switch


@dataclass(frozen=True)
class Slot:
    slot: int               # 1-based
    port_id: str | None
    part: str


@dataclass(frozen=True)
class FloorFeature:
    cx: float
    cy: float
    kind: str               # 'rect'
    size: tuple[float, float]
    label: str


@dataclass(frozen=True)
class Layout:
    """mcc_case_layout() record.  Field names are the OpenSCAD keys, so the parity test compares by name."""
    L: float
    W: float
    H: float
    H_int: float
    ez_neg: float
    ez_pos: float
    x_dev_lo: float
    x_dev_c: float
    x_dev_hi: float
    y_dev_lo: float
    y_dev_c: float
    y_dev_hi: float
    z_dev_lo: float
    z_dev_hi: float
    z_conn_c: float
    plate_l: float
    plate_size: tuple[float, float]
    n_slots: int
    pitch: float
    slot_x: tuple[float, ...]
    d_bay_free: float
    fan_pos: tuple[float, float, float]
    fan_y: float
    fan_bay_x: tuple[float, float]
    fan_bay_y: tuple[float, float]
    fan_bay_z: tuple[float, float]
    switch_pos: tuple[float, float, float]
    splitter_bay_x: tuple[float, float]
    splitter_bay_y: tuple[float, float]
    splitter_bay_z: tuple[float, float]
    side_bolt_x: float
    side_bolt_z: float
    lid_n_fast: int
    lid_fastener_pos: tuple[tuple[float, float], ...]
    vent_intake_z: tuple[float, float]
    vent_exhaust_z: tuple[float, float]
    # not keys of mcc_case_layout(): the fan-switch band its body computes and asserts on (layout.scad:408-428)
    switch_y_lo: float
    switch_y_hi: float


LAYOUT_EXTRAS = ("switch_y_lo", "switch_y_hi")
LAYOUT_KEYS = tuple(f for f in Layout.__dataclass_fields__ if f not in LAYOUT_EXTRAS)   # the 36 OpenSCAD keys


def _tuple(v: Any) -> Any:
    return tuple(_tuple(x) for x in v) if isinstance(v, (list, tuple)) else v


def device_from_doc(d: dict) -> Device:
    """A Device from the JSON shape of cad/devices/<slug>.json (only the solver's fields are read)."""
    ports = tuple(Port(p["id"], tuple(p["face"]), tuple(p["pos"]), p["kind"], p["dir"], p["panel"], p["confidence"])
                  for p in d["ports"])
    return Device(d["slug"], d["family"], tuple(d["size"]), ports)


def load_device(slug: str) -> Device:
    return device_from_doc(params.device_doc(slug))


def _c() -> dict[str, float]:
    return params.constants()  # type: ignore[return-value]


# ---------------------------------------------------------------------------------------------
# ports.scad
# ---------------------------------------------------------------------------------------------


def ports_on_face(dev: Device, face: tuple) -> list[Port]:
    return [p for p in dev.ports if p.face == tuple(face)]                       # ports.scad:48


def ports_external(dev: Device) -> list[Port]:
    return [p for p in dev.ports if p.panel != "none"]                           # ports.scad:57


def port_by_id(dev: Device, port_id: str) -> Port:
    matches = [p for p in dev.ports if p.id == port_id]                          # ports.scad:65
    if len(matches) != 1:
        raise SolverError(f"port id {port_id!r} not found (or duplicated) on device {dev.slug!r}")
    return matches[0]


def warn_unmeasured(dev: Device) -> list[Port]:
    """Ports below confidence 'measured' (ports.scad:83; the WARNING echo is the caller's business)."""
    order = list(params.table("confidence_order"))
    rank = order.index("measured")
    return [p for p in dev.ports if order.index(p.confidence) < rank]


# ---------------------------------------------------------------------------------------------
# constants.scad: pure accessors
# ---------------------------------------------------------------------------------------------


def panel_part(part: str) -> dict:
    parts = params.table("panel_parts")                                          # constants.scad:1030
    if part not in parts:
        raise SolverError(f"unknown panel part {part!r}")
    return parts[part]


def panel_hole_d(part: str) -> float: return panel_part(part)["hole_d"]
def panel_depth(part: str) -> float: return panel_part(part)["depth"]
def panel_max_t(part: str) -> float: return panel_part(part)["max_panel_t"]
def plug_len(part: str) -> float: return panel_part(part)["plug_len"]
def bend_envelope(part: str) -> float: return panel_part(part)["bend"]
def panel_kind(part: str) -> str: return panel_part(part)["kind"]
def panel_confidence(part: str) -> str: return panel_part(part)["confidence"]


def bay_depth(part: str) -> float:
    return panel_depth(part) + plug_len(part)                                    # constants.scad:1044


def cutout_d(part: str) -> float:
    return panel_hole_d(part) + _c()["MCC_HOLE_COMP"]                            # constants.scad:1048


def dev_side_allow(kind: str) -> float:
    t = params.table("dev_side_allow")                                           # constants.scad:409
    if kind not in t:
        raise SolverError(f'unknown port kind "{kind}" in mcc_dev_side_allow()')
    return t[kind]


def plug_axial(kind_or_part: str) -> float:
    t = params.table("plug_axial")                                               # constants.scad:471
    if kind_or_part in t:
        return t[kind_or_part]
    kind = panel_kind(kind_or_part)
    if kind not in t:
        raise SolverError(f'unknown plug-axial kind/part "{kind_or_part}"')
    return t[kind]


def fan_spec(name: str) -> dict:
    t = params.table("fans")                                                     # constants.scad:750
    if name not in t:
        raise SolverError(f'unknown fan "{name}"')
    return t[name]


def switch_spec(name: str) -> dict:
    t = params.table("switches")                                                 # constants.scad:866
    if name not in t:
        raise SolverError(f'unknown switch "{name}"')
    return t[name]


def splitter_spec(name: str) -> dict:
    t = params.table("splitters")                                                # poe_splitter.scad:21
    if name not in t:
        raise SolverError(f'unknown splitter "{name}"')
    return t[name]


def side_bolt_keepout() -> dict:
    """fasteners.scad:310 with its default arguments: disc_d = od + 2 * 2.0 (== MCC_SIDE_BOLT_KEEPOUT_D)."""
    c = _c()
    return {"disc_d": c["MCC_SIDE_BOLT_KEEPOUT_D"], "strip_w": c["MCC_SIDE_BOLT_KEEPOUT_STRIP_W"]}


def _options_tbl() -> Any:
    return params.table("options")


# ---------------------------------------------------------------------------------------------
# layout.scad
# ---------------------------------------------------------------------------------------------


def end_zone(dev: Device, end: str) -> float:
    """layout.scad:39 (D-12: the splitter bay's on-edge X extent is ALWAYS added on the 'neg' end)."""
    if end not in ("neg", "pos"):
        raise SolverError(f'end must be "neg" or "pos", got {end!r}')
    c = _c()
    face = (-1, 0, 0) if end == "neg" else (1, 0, 0)
    ext_on_end = [p for p in ports_on_face(dev, face) if p.panel != "none"]
    allows = [dev_side_allow(p.kind) for p in ext_on_end]
    ez_cable = max_of([c["MCC_END_ZONE_MIN"]] + allows)
    return ez_cable + (c["MCC_END_ZONE_NEG_EXTRA_SPLITTER"] if end == "neg" else 0)


def slot_assignment(dev: Device) -> list[Slot]:
    """layout.scad:73.  Partition by the sign of face.x, order each block descending by [bend, plug_len]
    and ascending by pos.x (a stable lexicographic sort on [-bend, -plug_len, pos_x]); block A fills slots
    1..len(A) from the -X end, block B fills n..n-len(B)+1 from the +X end."""
    c = _c()
    ext = ports_external(dev)
    n_slots = len(ext)
    if n_slots < 1:
        raise SolverError(f"{dev.slug!r} has no external port")
    for p in ext:
        if p.face not in ((-1, 0, 0), (1, 0, 0)):
            raise SolverError(f"T1-01: port {p.id!r} on {dev.slug!r} has face {p.face}: side-exit topology needs [-1,0,0] or [1,0,0]")
    decorated = [[-bend_envelope(p.panel), -plug_len(p.panel), p.pos[0], i] for i, p in enumerate(ext)]
    block_a = [d for d in decorated if ext[int(d[3])].face[0] < 0]
    block_b = [d for d in decorated if ext[int(d[3])].face[0] > 0]
    sorted_a = sort_lex(block_a, [0, 1, 2]) if block_a else []
    sorted_b = sort_lex(block_b, [0, 1, 2]) if block_b else []
    filled: dict[int, Slot] = {}
    for i, d in enumerate(sorted_a):
        p = ext[int(d[3])]
        filled[i + 1] = Slot(i + 1, p.id, p.panel)
    for i, d in enumerate(sorted_b):
        p = ext[int(d[3])]
        filled[n_slots - i] = Slot(n_slots - i, p.id, p.panel)
    return [filled.get(i, Slot(i, None, "DBA-BL-B")) for i in range(1, n_slots + 1)]


def slot_for_port(dev: Device, port_id: str) -> int:
    matches = [s for s in slot_assignment(dev) if s.port_id == port_id]         # layout.scad:122
    if len(matches) != 1:
        raise SolverError(f"port id {port_id!r} not found among the external ports of {dev.slug!r}")
    return matches[0].slot


def aperture_window(part: str) -> float:
    """layout.scad:147: the body window behind the seat hole (0 for a genuinely solid blank)."""
    return 0 if panel_hole_d(part) == 0 else cutout_d(part) + 2 * _c()["MCC_CLR_SLIDE"]


def cradle_deck(dev: Device) -> float:
    return _c()["MCC_SIDE_BOLT_AXIS_Z"] - dev.size[2] / 2 - _c()["MCC_FLOOR_T"]  # layout.scad:163


def nearest_zero(vals: list[float]) -> float:
    """layout.scad:175; an exact |value| tie returns the smaller (more negative) one."""
    abs_vals = [abs(v) for v in vals]
    min_abs = min_of(abs_vals)
    candidates = [v for v in vals if abs(v) - min_abs < _c()[EPS_NAME]]
    return min_of(candidates)


def case_layout(dev: Device, opts: Options) -> Layout:
    """mcc_case_layout() (layout.scad:267), without its Tier-1 asserts (rules.py)."""
    c = _c()
    dev_l, dev_w, dev_h = dev.size
    wall = c["MCC_WALL"]

    ez_neg = end_zone(dev, "neg")
    ez_pos = end_zone(dev, "pos")

    ext = ports_external(dev)
    n_slots = len(ext)
    bay_depths = [bay_depth(p.panel) for p in ext]
    if not bay_depths:
        raise SolverError(f"T1-02: {dev.slug!r} has no external port")
    max_bay_depth = max_of(bay_depths)
    d_bay_free = max_bay_depth - (wall + c["MCC_PANEL_SEAT_T"])

    L = 2 * wall + ez_neg + dev_l + ez_pos
    W = c["MCC_T_PATCH"] + d_bay_free + c["MCC_GAP_DEV"] + dev_w + c["MCC_GAP_FAR"] + wall
    H_int = c["MCC_PANEL_BAND"] + c["MCC_PLATE_H"] + c["MCC_PANEL_BAND"]
    H = c["MCC_FLOOR_T"] + H_int + c["MCC_LID_T"]

    deck = cradle_deck(dev)

    x_dev_lo = -L / 2 + wall + ez_neg
    x_dev_c = x_dev_lo + dev_l / 2
    x_dev_hi = x_dev_lo + dev_l

    y_dev_lo = -W / 2 + wall + c["MCC_GAP_FAR"]
    y_dev_c = y_dev_lo + dev_w / 2
    y_dev_hi = y_dev_lo + dev_w

    z_dev_lo = c["MCC_FLOOR_T"] + deck
    z_dev_hi = z_dev_lo + dev_h
    z_conn_c = c["MCC_SIDE_BOLT_AXIS_Z"]

    plate_l = L - 2 * wall - 2 * c["MCC_PANEL_FRAME_MIN"]
    plate_size = (plate_l, c["MCC_PLATE_H"])

    span = plate_l - c["MCC_D_FLANGE_X"] - 2 * c["MCC_PLATE_END_PAD"]
    pitch = span / (n_slots - 1) if n_slots > 1 else 0
    slot_x = tuple((-span / 2 + i * pitch) if n_slots > 1 else 0 for i in range(n_slots))

    slots_assigned = slot_assignment(dev)
    if n_slots != len(slots_assigned):
        raise SolverError("internal: slot count mismatch")

    fan_y = y_dev_c if opts.fan_y is None else opts.fan_y
    fan_pos = (L / 2, fan_y, z_conn_c)

    fan_frame = fan_spec(_options_tbl()["fan_default"])["frame"]
    fan_bay_depth = fan_frame[2] + c["MCC_FAN_INTAKE_CLR"]
    fan_bay_x = (L / 2 - wall - fan_bay_depth, L / 2 - wall)
    fan_bay_y = (fan_y - fan_frame[1] / 2, fan_y + fan_frame[1] / 2)
    fan_bay_z = (z_conn_c - fan_frame[0] / 2, z_conn_c + fan_frame[0] / 2)

    splitter_env = splitter_spec(_options_tbl()["splitter_default"])["size"]
    splitter_bay_x = (-L / 2 + wall, -L / 2 + wall + splitter_env[2])
    splitter_bay_y = (-W / 2 + wall, -W / 2 + wall + splitter_env[0])
    splitter_bay_z = (c["MCC_FLOOR_T"], c["MCC_FLOOR_T"] + splitter_env[1])

    sb_pos = port_by_id(dev, "side_bolt").pos
    side_bolt_x = x_dev_c + sb_pos[0]
    side_bolt_z = z_conn_c + sb_pos[1]

    n_fast = c["MCC_LID_N_FAST_LARGE"] if L > c["MCC_LID_SPAN_MAX"] else c["MCC_LID_N_FAST_SMALL"]
    e = c["MCC_FASTENER_INSET"]
    corners = [(L / 2 - e, W / 2 - e), (L / 2 - e, -(W / 2 - e)), (-(L / 2 - e), W / 2 - e), (-(L / 2 - e), -(W / 2 - e))]
    gap_candidates_all = [(slot_x[i] + slot_x[i + 1]) / 2 for i in range(n_slots - 1)] if n_slots > 1 else []
    gap_clearance = pitch / 2 - c["MCC_D_FLANGE_X"] / 2 if n_slots > 1 else 0
    gap_candidates = gap_candidates_all if (n_fast == 6 and gap_clearance >= c["MCC_LID_FASTENER_CLR_MIN"]) else []
    x_gap = nearest_zero(gap_candidates) if gap_candidates else None
    boss_od_lid = c["MCC_BOSS_MIN_RATIO"] * c["MCC_INSERT_M3_OD"]
    far_sep = c["MCC_SIDE_BOLT_KEEPOUT_D"] / 2 + boss_od_lid / 2
    far_candidates = [side_bolt_x - far_sep, side_bolt_x + far_sep] if n_fast == 6 else []
    far_legal = [x for x in far_candidates if abs(x) <= L / 2 - e - boss_od_lid / 2]
    x_far_mid = nearest_zero(far_legal) if far_legal else None
    lid_fastener_pos = list(corners)
    if n_fast != 4:
        if x_gap is not None:
            lid_fastener_pos.append((x_gap, W / 2 - e))
        if x_far_mid is not None:
            lid_fastener_pos.append((x_far_mid, -(W / 2 - e)))

    sw_spec = switch_spec(_options_tbl()["switch_default"])
    sw_clr, sw_pad_d, sw_body_d = sw_spec["clr"], sw_spec["pad_d"], sw_spec["body_d"]
    fan_frame_sw = fan_spec(_options_tbl()["fan_default"])["frame"]
    corner_y = -(W / 2 - e)
    gusset_edge = corner_y + wall / 2
    boss_edge = corner_y + boss_od_lid / 2
    switch_y_hi = fan_y - fan_frame_sw[1] / 2 - sw_clr - sw_pad_d / 2
    switch_y_lo = max(gusset_edge + sw_clr + sw_pad_d / 2, boss_edge + sw_clr + sw_body_d / 2)
    switch_y = (switch_y_lo + switch_y_hi) / 2
    switch_pos = (L / 2, switch_y, z_conn_c)

    vent_intake_z = (c["MCC_VENT_INTAKE_Z0"], c["MCC_VENT_INTAKE_Z0"] + c["MCC_VENT_INTAKE_BAND_H"])
    vent_exhaust_z = (c["MCC_VENT_EXHAUST_Z_LO"], c["MCC_VENT_EXHAUST_Z_HI"])

    return Layout(
        L=L, W=W, H=H, H_int=H_int, ez_neg=ez_neg, ez_pos=ez_pos,
        x_dev_lo=x_dev_lo, x_dev_c=x_dev_c, x_dev_hi=x_dev_hi,
        y_dev_lo=y_dev_lo, y_dev_c=y_dev_c, y_dev_hi=y_dev_hi,
        z_dev_lo=z_dev_lo, z_dev_hi=z_dev_hi, z_conn_c=z_conn_c,
        plate_l=plate_l, plate_size=plate_size, n_slots=n_slots, pitch=pitch, slot_x=slot_x,
        d_bay_free=d_bay_free, fan_pos=fan_pos, fan_y=fan_y,
        fan_bay_x=fan_bay_x, fan_bay_y=fan_bay_y, fan_bay_z=fan_bay_z, switch_pos=switch_pos,
        splitter_bay_x=splitter_bay_x, splitter_bay_y=splitter_bay_y, splitter_bay_z=splitter_bay_z,
        side_bolt_x=side_bolt_x, side_bolt_z=side_bolt_z,
        lid_n_fast=int(n_fast), lid_fastener_pos=tuple(lid_fastener_pos),
        vent_intake_z=vent_intake_z, vent_exhaust_z=vent_exhaust_z,
        switch_y_lo=switch_y_lo, switch_y_hi=switch_y_hi,
    )


def case_dims(dev: Device, opts: Options) -> tuple[float, float, float]:
    l = case_layout(dev, opts)                                                    # layout.scad:481
    return l.L, l.W, l.H


def floor_keepout(dev: Device, opts: Options) -> list[FloorFeature]:
    """mcc_floor_keepout() (layout.scad:206): mount rail, four strap slots, side-bolt support web."""
    c = _c()
    l = case_layout(dev, opts)
    L, W = l.L, l.W
    bay_x = l.splitter_bay_x
    strap_x_pos = L / 2 - c["MCC_STRAP_X_INSET"]
    strap_x_neg_nominal = -(L / 2 - c["MCC_STRAP_X_INSET"])
    strap_x_neg = (bay_x[1] + c["MCC_STRAP_SLOT_X"] / 2 + c["MCC_STRAP_BAY_CLR"]
                   if strap_x_neg_nominal - c["MCC_STRAP_SLOT_X"] / 2 < bay_x[1] else strap_x_neg_nominal)
    strap_y = W / 2 - c["MCC_STRAP_Y_INSET"]
    web_y0 = -W / 2 + c["MCC_WALL"]
    web_len = c["MCC_GAP_FAR"] - c["MCC_SIDE_BOLT_PAD_T"]
    web_cy = web_y0 + web_len / 2
    slot = (c["MCC_STRAP_SLOT_X"], c["MCC_STRAP_SLOT_Y"])
    return [
        FloorFeature((L / 2 - c["MCC_RAIL_LEN"] / 2) / 2, c["MCC_RAIL_Y"], "rect",
                     (L / 2 + c["MCC_RAIL_LEN"] / 2, c["MCC_RAIL_ROOT_W"]), "mount_rail"),
        FloorFeature(strap_x_pos, strap_y, "rect", slot, "strap_pos_y"),
        FloorFeature(strap_x_pos, -strap_y, "rect", slot, "strap_pos_neg_y"),
        FloorFeature(strap_x_neg, strap_y, "rect", slot, "strap_neg_y"),
        FloorFeature(strap_x_neg, -strap_y, "rect", slot, "strap_neg_neg_y"),
        FloorFeature(l.side_bolt_x, web_cy, "rect", (c["MCC_SIDE_BOLT_SUPPORT_WEB_T"], web_len), "side_bolt_web"),
    ]


# ---------------------------------------------------------------------------------------------
# vents.scad: the list logic (slot centres with exclusions, far-wall bands, lid vent field)
# ---------------------------------------------------------------------------------------------


def in_any_range(lo: float, hi: float, ranges: list[tuple[float, float]]) -> bool:
    return any(hi > r[0] and lo < r[1] for r in ranges)                          # vents.scad:28


@dataclass(frozen=True)
class SlotGrid:
    """The uniform grid of slot centres tiling a run (vents.scad:46-54): centre i is start + i * pitch."""
    start: float
    pitch: float
    n: int


def vent_slot_grid(run_lo: float, run_hi: float, slot_w: float, web_w: float) -> SlotGrid:
    pitch = slot_w + web_w
    run = run_hi - run_lo
    n = int(floor_((run + web_w) / pitch))
    used = n * pitch - web_w
    start = run_lo + (run - used) / 2 + slot_w / 2
    return SlotGrid(start, pitch, n)


def vent_slot_centers(run_lo: float, run_hi: float, excl_ranges: list[tuple[float, float]] | None = None,
                      slot_w: float | None = None, web_w: float | None = None) -> list[float]:
    """_mcc_vent_slot_centers() (vents.scad:46): slots whose footprint overlaps an exclusion are DROPPED."""
    c = _c()
    slot_w = c["MCC_VENT_SLOT_W"] if slot_w is None else slot_w
    web_w = c["MCC_VENT_WEB_W"] if web_w is None else web_w
    g = vent_slot_grid(run_lo, run_hi, slot_w, web_w)
    allc = [g.start + i * g.pitch for i in range(g.n)]
    return [x for x in allc if not in_any_range(x - slot_w / 2, x + slot_w / 2, excl_ranges or [])]


@dataclass(frozen=True)
class Run:
    """One contiguous, evenly pitched run of slots: the first centre and the count (>= 1)."""
    x0: float
    n: int


def vent_segments(run_lo: float, run_hi: float, excl_ranges: list[tuple[float, float]],
                  slot_w: float, web_w: float) -> list[Run]:
    """The surviving slots of vent_slot_centers() as maximal runs of consecutive grid indices.  K exclusion
    ranges leave at most K + 1 runs; the first centre of a run is start + i0 * pitch, bit-identical to the
    entry of the OpenSCAD list."""
    g = vent_slot_grid(run_lo, run_hi, slot_w, web_w)
    keep = [not in_any_range(g.start + i * g.pitch - slot_w / 2, g.start + i * g.pitch + slot_w / 2, excl_ranges)
            for i in range(g.n)]
    runs: list[Run] = []
    i = 0
    while i < g.n:
        if keep[i]:
            j = i
            while j + 1 < g.n and keep[j + 1]:
                j += 1
            runs.append(Run(g.start + i * g.pitch, j - i + 1))
            i = j + 1
        else:
            i += 1
    return runs


def lid_far_mid_x(l: Layout) -> float | None:
    """_mcc_lid_far_mid_x() (vents.scad:189).  Reads index 5 of lid_fastener_pos, so a far-wall mid
    fastener at index 4 (no patch-wall mid) is NOT seen: replicated as is (finding F77.1)."""
    return l.lid_fastener_pos[5][0] if (l.lid_n_fast == 6 and len(l.lid_fastener_pos) == 6) else None


@dataclass(frozen=True)
class FarBand:
    name: str                                   # 'lower' | 'upper'
    z: tuple[float, float]
    excl: tuple[tuple[float, float], ...]


def far_wall_excl(l: Layout) -> list[FarBand]:
    """_mcc_far_wall_excl() (vents.scad:88): the intake band split at the side-bolt disc's lower edge."""
    c = _c()
    ko = side_bolt_keepout()
    sb_disc_d, sb_strip_w = ko["disc_d"], ko["strip_w"]
    x_bolt, z_bolt, intake_z = l.side_bolt_x, l.side_bolt_z, l.vent_intake_z
    disc_z0 = z_bolt - sb_disc_d / 2
    split_z = min(max(disc_z0, intake_z[0]), intake_z[1])
    strip_excl = (x_bolt - sb_strip_w / 2, x_bolt + sb_strip_w / 2)
    disc_excl = (x_bolt - sb_disc_d / 2, x_bolt + sb_disc_d / 2)
    boss_od_lid = c["MCC_BOSS_MIN_RATIO"] * c["MCC_INSERT_M3_OD"]
    mid_w = boss_od_lid + 2 * c["MCC_VENT_MID_EXCL_MARGIN"]
    x_far_mid = lid_far_mid_x(l)
    mid_excl = () if x_far_mid is None else ((x_far_mid - mid_w / 2, x_far_mid + mid_w / 2),)
    return [FarBand("lower", (intake_z[0], split_z), (strip_excl,) + mid_excl),
            FarBand("upper", (split_z, intake_z[1]), (disc_excl,) + mid_excl)]


@dataclass(frozen=True)
class LidVentField:
    x_lo: float
    x_hi: float
    y_lo: float
    y_hi: float
    h: float
    excl: tuple[tuple[float, float], ...]


def lid_vent_field(l: Layout) -> LidVentField:
    """_mcc_lid_vent_field() (vents.scad:233)."""
    c = _c()
    strip_w = side_bolt_keepout()["strip_w"]
    field_x_lo = l.x_dev_lo + c["MCC_LID_VENT_END_MARGIN"]
    field_x_hi = l.x_dev_hi - c["MCC_LID_VENT_END_MARGIN"]
    field_h = c["MCC_LID_VENT_ROWS"] * c["MCC_LID_VENT_SLOT_L"] + (c["MCC_LID_VENT_ROWS"] - 1) * c["MCC_LID_VENT_ROW_GAP"]
    field_y_lo = l.y_dev_c - field_h / 2
    return LidVentField(field_x_lo, field_x_hi, field_y_lo, field_y_lo + field_h, field_h,
                        ((l.side_bolt_x - strip_w / 2, l.side_bolt_x + strip_w / 2),))


@dataclass(frozen=True)
class VentPlan:
    """Every vent slot of a case as runs (first centre + count), in the order mcc_vents() draws them."""
    split_z: float
    lower_z: tuple[float, float]       # far-wall intake, lower sub-band (intake_z[0] .. split_z)
    upper_z: tuple[float, float]       # upper sub-band (split_z .. intake_z[1])
    negx_z: tuple[float, float]        # the -X wall's intake band
    far_low: tuple[Run, ...]           # empty when the sub-band has no height
    far_high: tuple[Run, ...]
    exhaust: tuple[Run, ...]
    negx: tuple[Run, ...]
    lid: tuple[Run, ...]
    lid_y0: float                      # lower Y edge of the first lid-vent row (field y_lo)
    lid_rows: int                      # MCC_LID_VENT_ROWS

    @property
    def n_far_low(self) -> int:
        return sum(r.n for r in self.far_low)

    @property
    def n_far_high(self) -> int:
        return sum(r.n for r in self.far_high)

    @property
    def n_exhaust(self) -> int:
        return sum(r.n for r in self.exhaust)

    @property
    def n_negx(self) -> int:
        return sum(r.n for r in self.negx)

    @property
    def n_lid(self) -> int:
        return sum(r.n for r in self.lid)


def vent_plan(l: Layout) -> VentPlan:
    c = _c()
    slot_w, web_w = c["MCC_VENT_SLOT_W"], c["MCC_VENT_WEB_W"]
    bands = far_wall_excl(l)
    far = {b.name: (vent_segments(l.x_dev_lo, l.x_dev_hi, list(b.excl), slot_w, web_w) if b.z[1] > b.z[0] else []) for b in bands}
    ko = side_bolt_keepout()
    ex_lo = max(l.side_bolt_x + ko["disc_d"] / 2, l.x_dev_lo)                      # vents.scad:140
    boss_od_lid = c["MCC_BOSS_MIN_RATIO"] * c["MCC_INSERT_M3_OD"]
    mid_w = boss_od_lid + 2 * c["MCC_VENT_MID_EXCL_MARGIN"]
    x_far_mid = lid_far_mid_x(l)
    mid_excl = [] if x_far_mid is None else [(x_far_mid - mid_w / 2, x_far_mid + mid_w / 2)]
    exhaust = vent_segments(ex_lo, l.x_dev_hi, mid_excl, slot_w, web_w) if l.x_dev_hi > ex_lo else []
    negx = vent_segments(0, l.W / 2 - c["MCC_WALL"], [], slot_w, web_w)            # vents.scad:148
    f = lid_vent_field(l)
    lid = vent_segments(f.x_lo, f.x_hi, list(f.excl), c["MCC_LID_VENT_SLOT_W"], c["MCC_LID_VENT_WEB_W"])
    return VentPlan(bands[0].z[1], bands[0].z, bands[1].z, l.vent_intake_z, tuple(far["lower"]), tuple(far["upper"]),
                    tuple(exhaust), tuple(negx), tuple(lid), f.y_lo, int(c["MCC_LID_VENT_ROWS"]))


# ---------------------------------------------------------------------------------------------
# cradle.scad: deck grid, far-flank ribs, patch-flank rule
# ---------------------------------------------------------------------------------------------


def cradle_deck_grid(lo: float, hi: float) -> list[float]:
    """_mcc_cradle_deck_grid() (cradle.scad:58): interior ladder-rib centres along one axis."""
    c = _c()
    span = (hi - lo) - 2 * c["MCC_WALL"]
    n_bays = max(1, round_half_away(span / c["MCC_CRADLE_DECK_GRID_PITCH"]))
    n_ribs = int(n_bays - 1)
    step = span / n_bays
    return [lo + c["MCC_WALL"] + i * step for i in range(1, n_ribs + 1)]


def far_flank_segments(x_dev_lo: float, x_dev_hi: float, x_bolt: float) -> list[tuple[float, float]]:
    """The closed intervals of _mcc_far_flank_rib_x() (cradle.scad:131): the band less the side-bolt exclusion."""
    c = _c()
    cc = c["MCC_SIDE_BOLT_KEEPOUT_D"] / 2 + c["MCC_CRADLE_RIB_T"] / 2 + c["MCC_CRADLE_FLANK_RIB_CLR"]
    m = c["MCC_CRADLE_FLANK_RIB_END_MARGIN"]
    band = (x_dev_lo + m, x_dev_hi - m)
    excl = (x_bolt - cc, x_bolt + cc)
    if excl[1] <= band[0] or excl[0] >= band[1]:
        segs_raw: list[tuple[float, float] | None] = [(band[0], band[1])]
    else:
        segs_raw = [(band[0], min(excl[0], band[1])) if excl[0] > band[0] else None,
                    (max(excl[1], band[0]), band[1]) if excl[1] < band[1] else None]
    return [s for s in segs_raw if s is not None and s[1] > s[0]]


def far_flank_rib_x(x_dev_lo: float, x_dev_hi: float, x_bolt: float) -> list[float]:
    span_mid = _c()["MCC_CRADLE_FLANK_RIB_MID_SPAN"]
    pts: list[float] = []
    for s0, s1 in far_flank_segments(x_dev_lo, x_dev_hi, x_bolt):
        pts += [s0, (s0 + s1) / 2, s1] if (s1 - s0 > span_mid) else [s0, s1]
    return pts


def patch_rib_x(l: Layout) -> list[float]:
    """cradle.scad:247 (T1-20): patch-flank ribs only where |x| > plate_l/2 - MCC_CRADLE_PATCH_RIB_EDGE."""
    c = _c()
    lip = c["MCC_WALL"]
    return [x for x in (l.x_dev_lo + lip, l.x_dev_hi - lip) if abs(x) > l.plate_l / 2 - c["MCC_CRADLE_PATCH_RIB_EDGE"]]


@dataclass(frozen=True)
class DeckGrid:
    """The interior ladder ribs along one axis: `n` ribs, the first at `x0`, spaced `pitch` (cradle.scad:58-65)."""
    n: int
    x0: float
    pitch: float


def deck_grid(lo: float, hi: float) -> DeckGrid:
    c = _c()
    span = (hi - lo) - 2 * c["MCC_WALL"]
    n_bays = max(1, round_half_away(span / c["MCC_CRADLE_DECK_GRID_PITCH"]))
    step = span / n_bays
    return DeckGrid(int(n_bays - 1), lo + c["MCC_WALL"] + 1 * step, step)


@dataclass(frozen=True)
class CradlePlan:
    deck_x: DeckGrid
    deck_y: DeckGrid
    far_ribs: tuple[float, ...]       # ascending
    patch_ribs: tuple[float, ...]     # expected empty: the master has no patch-flank rib (a rule refuses any)


def cradle_plan(l: Layout) -> CradlePlan:
    c = _c()
    lip = c["MCC_WALL"]
    ribs = far_flank_rib_x(l.x_dev_lo, l.x_dev_hi, l.side_bolt_x)
    return CradlePlan(deck_grid(l.x_dev_lo - lip, l.x_dev_hi + lip), deck_grid(l.y_dev_lo - lip, l.y_dev_hi + lip),
                      tuple(ribs), tuple(patch_rib_x(l)))


# ---------------------------------------------------------------------------------------------
# table look-ups and closed forms the builders need as numbers (fan.scad, switch.scad, fasteners.scad, shell.scad)
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FanGrille:
    opening_d: float                               # round opening: frame - MCC_FAN_OPENING_MARGIN (fan.scad:151)
    hole_d: float
    hole_pitch: float
    rings: tuple[tuple[float, float], ...]         # (outer d, inner d) of ring i (fan.scad:75,85,100-106)


def fan_grille() -> FanGrille:
    c = _c()
    spec = fan_spec(_options_tbl()["fan_default"])
    frame = spec["frame"]
    opening_d = frame[0] - c["MCC_FAN_OPENING_MARGIN"]
    r_max = opening_d / 2
    ring_w, gap_w = c["MCC_FAN_GRILLE_RING_W"], c["MCC_FAN_GRILLE_GAP_W"]
    n_rings = int(max(1, floor_(r_max / (ring_w + gap_w))))
    pitch = r_max / n_rings
    rings = []
    for i in range(1, n_rings + 1):
        r_out = i * pitch
        r_in = max(0, r_out - ring_w)
        rings.append((2 * r_out, 2 * r_in))
    return FanGrille(opening_d, spec["hole_d"], spec["pitch"], tuple(rings))


@dataclass(frozen=True)
class SwitchDims:
    bore_d: float      # through bore: hole_d + MCC_HOLE_COMP (switch.scad:136)
    body_d: float
    pad_d: float
    recess_t: float    # actuator_proud_h + MCC_SWITCH_FLUSH_CLR (switch.scad:102)
    pad_t: float       # recess_t + MCC_APERTURE_LIP_WEB_MIN: wall plus pad thickness (switch.scad:34-40)


def switch_dims() -> SwitchDims:
    c = _c()
    sw = switch_spec(_options_tbl()["switch_default"])
    recess_t = sw["actuator_proud_h"] + c["MCC_SWITCH_FLUSH_CLR"]
    return SwitchDims(sw["hole_d"] + c["MCC_HOLE_COMP"], sw["body_d"], sw["pad_d"], recess_t,
                      recess_t + c["MCC_APERTURE_LIP_WEB_MIN"])


@dataclass(frozen=True)
class InsertDims:
    boss_d: float      # MCC_BOSS_MIN_RATIO * sleeve diameter (fasteners.scad:53; shell.scad:232)
    hole_d: float
    depth: float       # insert length + MCC_INSERT_BORE_OVERDEPTH (fasteners.scad:33,54)


def insert_dims() -> InsertDims:
    c = _c()
    return InsertDims(c["MCC_BOSS_MIN_RATIO"] * c["MCC_INSERT_M3_OD"], c["MCC_INSERT_M3_HOLE_D"],
                      c["MCC_INSERT_M3_LEN"] + c["MCC_INSERT_BORE_OVERDEPTH"])


def web_tangent() -> tuple[float, float]:
    """Tangent point (u, v) of the gusset web's hull (shell.scad:84-97) in the boss frame, closed form of the
    hull of the circle of radius r = boss_r - MCC_WEB_HULL_INSET and the bar corner (b, a) with
    b = MCC_FASTENER_INSET - MCC_WEB_FACE_MARGIN, a = boss_r.  The 0.02 mm bar thickness is ignored."""
    c = _c()
    a = insert_dims().boss_d / 2
    b = c["MCC_FASTENER_INSET"] - c["MCC_WEB_FACE_MARGIN"]
    r = a - c["MCC_WEB_HULL_INSET"]
    d2 = a * a + b * b
    s = math.sqrt(d2 - r * r)
    return (r * r * b - r * a * s) / d2, (r * r * a + r * b * s) / d2


# ---------------------------------------------------------------------------------------------
# one solved configuration
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Solution:
    slug: str
    config: str
    options: Options
    device: Device
    layout: Layout
    slots: tuple[Slot, ...]
    floor: tuple[FloorFeature, ...]
    vents: VentPlan
    cradle: CradlePlan
    fan: FanGrille
    switch: SwitchDims
    insert: InsertDims
    web: tuple[float, float]


def case_options(case: dict, config: str = "default") -> Options:
    """Merge a case definition's options with one configuration's overrides."""
    merged = dict(case["options"])
    if config != "default":
        extras = {**case.get("configurations", {}), **case.get("test_configurations", {})}
        if config not in extras:
            raise SolverError(f"case {case['slug']!r} has no configuration {config!r}")
        merged.update(extras[config])
    return Options(**merged)


def solution_for(dev: Device, opts: Options, slug: str = "", config: str = "default") -> Solution:
    """Everything the solver computes for one device and one option set (no files read except the registry)."""
    l = case_layout(dev, opts)
    return Solution(slug or dev.slug, config, opts, dev, l, tuple(slot_assignment(dev)), tuple(floor_keepout(dev, opts)),
                    vent_plan(l), cradle_plan(l), fan_grille(), switch_dims(), insert_dims(), web_tangent())


def solve(slug: str, config: str = "default") -> Solution:
    case = params.case_doc(slug)
    return solution_for(load_device(case["device"]), case_options(case, config), slug, config)


def configurations(slug: str) -> list[str]:
    doc = params.case_doc(slug)
    return ["default"] + sorted(set(doc.get("configurations", {})) | set(doc.get("test_configurations", {})))


# ---------------------------------------------------------------------------------------------
# the parameter set of one configuration  (cad/parameters/variants/<slug>.json)
# ---------------------------------------------------------------------------------------------
#
# The key set is the contract with the generator: it IS section 3.5 of P2-81-case-master.md, implemented
# here (issue #77) and frozen together with #81.  Mechanism: V_<GROUP>_<NAME> lengths as '<decimal> mm',
# V_N_<NAME> counts (integer >= 1), one suppress flag <Owner>_<Set> per switchable feature set (true =
# suppressed), a fixed number of contiguous segments for every run with gaps, and a PARKING RULE that keeps
# the values of a switched-off instance valid geometry: repeat the last live instance of the group (count 1
# for a run); a mid fastener without a position: x = 0; an empty intake sub-band: the z pair of the other
# one; a group with no live instance at all: the centre of the device box.

# CAPACITY is the capacity of the master: for every group the largest count the solver can return for ANY side-bolt
# position on ANY device in scope (P2-81 D81.7), proven in both directions by the committed sweep
# cad/tests/test_layout_master.py::test_capacity_is_the_reachable_maximum.  It is never a counting bound.  `fan_rings` is
# the ring count of the grille (two inner rings are features, the outermost gives the opening).
CAPACITY = {"slots": 4, "far_ribs": 5, "far_low": 3, "far_high": 2, "exhaust": 1, "negx": 1, "lid": 2, "fan_rings": 3}
RUN_GROUPS = {"FARLO": ("far_low", "FarLo"), "FARUP": ("far_high", "FarUp"), "EXH": ("exhaust", "Exh"),
              "NEGX": ("negx", "NegX"), "LID": ("lid", "Lid")}          # key token: (CAPACITY entry, flag token)


def run_letters(group: str) -> str:
    """The segment letters of a vent group: 'ABC' cut to its capacity."""
    return "ABC"[:CAPACITY[RUN_GROUPS[group][0]]]


def _num(v: float) -> str:
    """Decimal text of a float rounded to 12 decimals (rounding error <= 5e-13 mm, far below the 1e-9 parity
    tolerance), trailing zeros stripped: '3', '159.85', '41.966666666667'.  Removes the 1e-14 noise of the
    OpenSCAD arithmetic ('159.85000000000002') from the committed text."""
    return fmt_num(v, 12)


def mm(v: float) -> str:
    return f"{_num(v)} mm"


def cnt(n: int) -> str:
    if int(n) != n or n < 1:
        raise CapacityError(f"T1-39: a count is an integer >= 1, got {n!r}")
    return str(int(n))


def capacity_problems(sol: Solution) -> list[str]:
    """Every reason why `sol` cannot be written as a parameter set of the master (P2-81 D81.7, sections 3.3 and 3.5);
    empty when it fits.  Each reason starts with its rule id.  If no total set can mean what the solution says, the
    solver refuses: T1-02, T1-39 and T1-81.2 to T1-81.7 have their ONLY implementation here (D77.1, gate B1);
    cad/rules.py lists these ids by calling this function and implements none of them again."""
    l, v, cr = sol.layout, sol.vents, sol.cradle
    cap = CAPACITY
    out: list[str] = []
    if not 1 <= l.n_slots <= cap["slots"]:
        out.append(f"T1-02: {l.n_slots} connector slots, the master holds {cap['slots']}")
    if cr.deck_x.n < 1 or cr.deck_y.n < 1:
        out.append(f"T1-39: deck ladder counts {cr.deck_x.n} x {cr.deck_y.n}: a count is at least 1")
    if len(cr.far_ribs) > cap["far_ribs"]:
        out.append(f"T1-81.2: {len(cr.far_ribs)} far-flank ribs, the master holds {cap['far_ribs']}")
    for group, (entry, _flag) in RUN_GROUPS.items():
        runs = {"far_low": v.far_low, "far_high": v.far_high, "exhaust": v.exhaust, "negx": v.negx, "lid": v.lid}[entry]
        if len(runs) > cap[entry]:
            out.append(f"T1-81.3: vent group {group} forms {len(runs)} runs, the master holds {cap[entry]}")
    if cr.patch_ribs:
        out.append(f"T1-81.4: patch-flank ribs at x = {list(cr.patch_ribs)} are required, the master has none")
    rings = sol.fan.rings
    if len(rings) != cap["fan_rings"]:
        out.append(f"T1-81.5: the fan grille has {len(rings)} rings, the master models {cap['fan_rings']}")
    elif any(inner_d <= 0 for _, inner_d in rings):
        out.append("T1-81.5: a fan grille ring without a hole")
    e = _c()["MCC_FASTENER_INSET"]
    for x, y in l.lid_fastener_pos:
        d_min = min(l.L / 2 - x, l.L / 2 + x, l.W / 2 - y, l.W / 2 + y)
        if abs(d_min - e) > 1e-9:
            out.append(f"T1-81.6: lid fastener at ({x:.4f}, {y:.4f}) is {d_min:.4f} from its wall, not MCC_FASTENER_INSET {e}")
    if sol.options.tripod_insert:
        out.append("T1-81.7: option tripod_insert is true, the master has no floor insert boss")
    return out


def _parked_runs(runs: tuple[Run, ...], names: str, fallback: float) -> list[tuple[str, float, int, bool]]:
    """[(letter, x0, n, live)] for every segment of a group: live runs as they are, the rest parked on the
    last live run's first centre (or `fallback`, the device-box centre) with count 1."""
    out = []
    last = runs[-1].x0 if runs else fallback
    for k, letter in enumerate(names):
        if k < len(runs):
            out.append((letter, runs[k].x0, runs[k].n, True))
        else:
            out.append((letter, last, 1, False))
    return out


def parameter_set(sol: Solution) -> dict:
    """{"parameters": {V_*: '<n> mm' | '<n>'}, "flags": {<Owner>_<Set>: bool}, "slots": [...]} of one configuration.
    Raises CapacityError when the solved case does not fit the master (see capacity_problems)."""
    problems = capacity_problems(sol)
    if problems:
        raise CapacityError(f"{sol.slug}/{sol.config}: " + "; ".join(problems))
    c, l, o, v = _c(), sol.layout, sol.options, sol.vents
    p: dict[str, str] = {}
    f: dict[str, bool] = {}

    # envelope, connector height, device box, connector recess
    p["V_CASE_L"], p["V_CASE_W"] = mm(l.L), mm(l.W)
    p["V_CASE_Z_TOP"] = mm(c["MCC_FLOOR_T"] + l.H_int)
    p["V_CONN_Z"] = mm(l.z_conn_c)
    p.update(V_DEV_X_LO=mm(l.x_dev_lo), V_DEV_X_HI=mm(l.x_dev_hi), V_DEV_Y_LO=mm(l.y_dev_lo), V_DEV_Y_HI=mm(l.y_dev_hi),
             V_DEV_Z_LO=mm(l.z_dev_lo), V_DEV_Z_HI=mm(l.z_dev_hi))
    p["V_PLATE_L"] = mm(l.plate_l)

    # connector slots: used slots carry the OpenSCAD positions and the panel part's diameters; an unused slot
    # repeats the last live slot (parking rule) and its flag is set
    last = l.n_slots - 1
    for i in range(1, CAPACITY["slots"] + 1):
        used = i <= l.n_slots
        j = i - 1 if used else last
        part = sol.slots[j].part
        p[f"V_SLOT{i}_X"] = mm(l.slot_x[j])
        p[f"V_SLOT{i}_SEAT_D"] = mm(cutout_d(part))
        p[f"V_SLOT{i}_WIN_D"] = mm(aperture_window(part))
        f[f"Patch_Slot{i}"] = not used

    # lid fasteners: the four corners are expressions; the boss, the bore and the two optional mids are solver values
    ins = sol.insert
    p.update(V_BOSS_D=mm(ins.boss_d), V_INSERT_HOLE_D=mm(ins.hole_d), V_INSERT_DEPTH=mm(ins.depth))
    mid_patch = next((x for x, y in l.lid_fastener_pos[4:] if y > 0), None)
    mid_far = next((x for x, y in l.lid_fastener_pos[4:] if y < 0), None)
    p["V_FAST_PATCH_MID_X"] = mm(0 if mid_patch is None else mid_patch)
    p["V_FAST_FAR_MID_X"] = mm(0 if mid_far is None else mid_far)
    p["V_WEB_TAN_U"], p["V_WEB_TAN_V"] = mm(sol.web[0]), mm(sol.web[1])
    f["Fastener_PatchMid"] = mid_patch is None
    f["Fastener_FarMid"] = mid_far is None

    # cradle: deck ladder (count, first position, pitch per axis), far-flank ribs (five instances, ascending)
    cr = sol.cradle
    p.update(V_N_DECK_X=cnt(cr.deck_x.n), V_DECK_X0=mm(cr.deck_x.x0), V_DECK_PITCH_X=mm(cr.deck_x.pitch),
             V_N_DECK_Y=cnt(cr.deck_y.n), V_DECK_Y0=mm(cr.deck_y.x0), V_DECK_PITCH_Y=mm(cr.deck_y.pitch))
    ribs = list(cr.far_ribs)
    for i in range(1, CAPACITY["far_ribs"] + 1):
        live = i <= len(ribs)
        p[f"V_FARRIB{i}_X"] = mm(ribs[i - 1] if live else (ribs[-1] if ribs else l.x_dev_c))
        f[f"Cradle_FarRib{i}"] = not live

    # floor strap pockets (the -X pair moves off the reserved splitter bay), side bolt
    straps = {ff.label: ff for ff in sol.floor}
    p.update(V_STRAP_POS_X=mm(straps["strap_pos_y"].cx), V_STRAP_NEG_X=mm(straps["strap_neg_y"].cx),
             V_STRAP_Y=mm(straps["strap_pos_y"].cy))
    p.update(V_SIDEBOLT_X=mm(l.side_bolt_x), V_SIDEBOLT_Z=mm(l.side_bolt_z))

    # vents: sub-band heights (an empty sub-band takes the other one's pair), then the runs
    lower_live, upper_live = v.lower_z[1] > v.lower_z[0], v.upper_z[1] > v.upper_z[0]
    lo_z = v.lower_z if lower_live else (v.upper_z if upper_live else v.negx_z)
    up_z = v.upper_z if upper_live else lo_z
    p.update(V_VENT_FARLO_Z_LO=mm(lo_z[0]), V_VENT_FARLO_Z_HI=mm(lo_z[1]),
             V_VENT_FARUP_Z_LO=mm(up_z[0]), V_VENT_FARUP_Z_HI=mm(up_z[1]),
             V_VENT_NEGX_Z_LO=mm(v.negx_z[0]), V_VENT_NEGX_Z_HI=mm(v.negx_z[1]))
    groups = {"FARLO": (v.far_low, l.x_dev_c), "FARUP": (v.far_high, l.x_dev_c), "EXH": (v.exhaust, l.x_dev_c),
              "NEGX": (v.negx, l.y_dev_c), "LID": (v.lid, l.x_dev_c)}
    for group, (runs, fallback) in groups.items():
        for letter, x0, n, live in _parked_runs(runs, run_letters(group), fallback):
            key = f"{group}{letter}"
            p[f"V_VENT_{key}_{'Y0' if group == 'NEGX' else 'X0'}"] = mm(x0)
            p[f"V_N_VENT_{key}"] = cnt(n)
            f[f"Vent_{RUN_GROUPS[group][1]}{letter}"] = (not live) or (group == "LID" and not o.lid_vents)
    p["V_VENT_LID_Y0"] = mm(v.lid_y0)
    p["V_N_VENT_LID_ROWS"] = cnt(v.lid_rows)

    # fan aperture, fan bay (reserved in every configuration), splitter bay (reserved), fan switch
    fg = sol.fan
    p["V_FAN_Y"] = mm(l.fan_y)
    p.update(V_FAN_OPENING_D=mm(fg.opening_d), V_FAN_HOLE_D=mm(fg.hole_d), V_FAN_HOLE_PITCH=mm(fg.hole_pitch))
    for i, (od, idd) in enumerate(fg.rings[:-1], start=1):                  # the two inner rings are features
        p[f"V_FAN_RING{i}_OD"], p[f"V_FAN_RING{i}_ID"] = mm(od), mm(idd)
    p[f"V_FAN_RING{len(fg.rings)}_ID"] = mm(fg.rings[-1][1])                # the outermost ring is the opening's edge: no OD key
    p.update(V_FANBAY_X_LO=mm(l.fan_bay_x[0]), V_FANBAY_X_HI=mm(l.fan_bay_x[1]),
             V_FANBAY_Y_LO=mm(l.fan_bay_y[0]), V_FANBAY_Y_HI=mm(l.fan_bay_y[1]),
             V_FANBAY_Z_LO=mm(l.fan_bay_z[0]), V_FANBAY_Z_HI=mm(l.fan_bay_z[1]))
    p.update(V_SPLITBAY_X_LO=mm(l.splitter_bay_x[0]), V_SPLITBAY_X_HI=mm(l.splitter_bay_x[1]),
             V_SPLITBAY_Y_LO=mm(l.splitter_bay_y[0]), V_SPLITBAY_Y_HI=mm(l.splitter_bay_y[1]),
             V_SPLITBAY_Z_LO=mm(l.splitter_bay_z[0]), V_SPLITBAY_Z_HI=mm(l.splitter_bay_z[1]))
    sw = sol.switch
    p.update(V_SWITCH_Y=mm(l.switch_pos[1]), V_SWITCH_BORE_D=mm(sw.bore_d), V_SWITCH_BODY_D=mm(sw.body_d),
             V_SWITCH_PAD_D=mm(sw.pad_d), V_SWITCH_RECESS_T=mm(sw.recess_t), V_SWITCH_PAD_T=mm(sw.pad_t))
    f["Fan_Aperture"] = not o.fan
    f["Switch_Toggle"] = not o.sw_enabled
    f["Floor_RailSill"] = f["Rail_Female"] = not o.rail

    slots = [{"slot": s.slot, "port": s.port_id, "part": s.part} for s in sol.slots]
    return {"parameters": p, "flags": f, "slots": slots}


# ---------------------------------------------------------------------------------------------
# derived sets: a real configuration plus overrides (P2-81 verdict B3)
# ---------------------------------------------------------------------------------------------
#
# The case master is built once with every feature created live (brief D.1).  No real configuration can do that (far-flank
# rib 5, for one, is live in none), so its build configuration is a DERIVED set: a real configuration with every flag clear
# and a few parameters moved to free positions.  The hand-written input is a spec file (issue #81:
# cad/fusion/gen/case/build_overrides.json); the generated output is a set file in the format of the variant files
# (cad/fusion/gen/case/build_set.json) that the runtime reads like any set.  Spec format (schema 1):
#
#   {"schema": 1, "name": "mcc-case-build", "configuration": "_build",
#    "base": {"slug": "pro-convert-hdmi-plus", "configuration": "default"},
#    "flags": "clear",                                  # or "keep": the base flags unchanged
#    "overrides": {"V_FARRIB5_X": {"value": "-30 mm", "reason": "why this key moves"}}}

SPEC_KEYS = {"schema", "name", "configuration", "base", "flags", "overrides"}


def derive_document(spec: dict, variants_dir: Path | None = None) -> dict:
    """The set-file document derived from a parsed spec.  Raises ValueError (naming the problem) for a malformed spec, an
    unknown base or key, a value whose unit differs from the base value's, a count below 1, or a missing reason."""
    if not isinstance(spec, dict) or spec.get("schema") != 1 or set(spec) - SPEC_KEYS or SPEC_KEYS - set(spec):
        raise ValueError(f"spec: expected exactly the keys {sorted(SPEC_KEYS)} with schema 1, got {sorted(spec) if isinstance(spec, dict) else spec!r}")
    name, config = spec["name"], spec["configuration"]
    if not (isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", name)):
        raise ValueError(f"spec: name {name!r} must be lower-case letters, digits and '-'")
    if not (isinstance(config, str) and re.fullmatch(r"[A-Za-z0-9_]+", config)):
        raise ValueError(f"spec: configuration {config!r} must be letters, digits and '_'")
    if spec["flags"] not in ("clear", "keep"):
        raise ValueError(f"spec: flags must be 'clear' or 'keep', got {spec['flags']!r}")
    base = spec["base"]
    if not (isinstance(base, dict) and set(base) == {"slug", "configuration"}):
        raise ValueError("spec: base must be {\"slug\": ..., \"configuration\": ...}")
    path = (variants_dir or params.VARIANTS_DIR) / f"{base['slug']}.json"
    if not path.is_file():
        raise ValueError(f"spec: base set {base['slug']!r} does not exist ({path.name})")
    base_doc = params.parameter_set_doc(path)
    if base["configuration"] not in base_doc["configurations"]:
        raise ValueError(f"spec: base {base['slug']!r} has no configuration {base['configuration']!r}")
    cfg = base_doc["configurations"][base["configuration"]]
    parameters = dict(cfg["parameters"])
    overrides = spec["overrides"]
    if not isinstance(overrides, dict):
        raise ValueError("spec: overrides must be an object")
    record: dict[str, dict] = {}
    for key, entry in overrides.items():
        if key not in parameters:
            raise ValueError(f"spec: override {key!r} is not a parameter of {base['slug']}/{base['configuration']} (a flag is never overridden)")
        if not (isinstance(entry, dict) and set(entry) == {"value", "reason"} and isinstance(entry["value"], str)
                and isinstance(entry["reason"], str) and entry["reason"].strip()):
            raise ValueError(f"spec: override {key!r} needs a string value and a non-empty reason")
        new, new_unit = params.parse_value(entry["value"])
        _old, old_unit = params.parse_value(parameters[key])
        if new_unit != old_unit:
            raise ValueError(f"spec: override {key!r} is {entry['value']!r} ({new_unit}), the base value {parameters[key]!r} is {old_unit}")
        if key.startswith("V_N_") and new < 1:
            raise ValueError(f"spec: override {key!r} is a count and must be at least 1")
        parameters[key] = entry["value"]
        record[key] = {"value": entry["value"], "reason": entry["reason"]}
    flags = {k: (False if spec["flags"] == "clear" else v) for k, v in cfg["flags"].items()}
    doc = {"schema": 1, "slug": name, "solver": "cad/layout.py",
           "derived": {"base": f"{base['slug']}/{base['configuration']}", "flags": spec["flags"], "overrides": record},
           "configurations": {config: {"parameters": parameters, "flags": flags, "slots": list(cfg.get("slots", []))}}}
    params.parameter_set_of(doc, config)                      # the result is a valid set by the same reader the runtime uses
    return doc


def derive_text(spec_path: Path | str, variants_dir: Path | None = None) -> str:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    return json.dumps(derive_document(spec, variants_dir), indent=2, ensure_ascii=False) + "\n"


def write_derived(spec_path: Path | str, out_path: Path | str, variants_dir: Path | None = None) -> None:
    Path(out_path).write_text(derive_text(spec_path, variants_dir), encoding="utf-8", newline="\n")


def check_derived(spec_path: Path | str, out_path: Path | str, variants_dir: Path | None = None) -> list[str]:
    """Freshness of a derived set: byte-identical to a fresh derivation, and total with the variant files."""
    out = Path(out_path)
    if not out.is_file():
        return [f"{out.name}: missing (run python -m cad.layout derive {spec_path} --out {out_path})"]
    if out.read_text(encoding="utf-8") != derive_text(spec_path, variants_dir):
        return [f"{out.name}: stale (run python -m cad.layout derive {spec_path} --out {out_path})"]
    vdir = variants_dir or params.VARIANTS_DIR
    return params.check_parameter_sets([out] + sorted(vdir.glob("*.json")))


# ---------------------------------------------------------------------------------------------
# the committed parameter-set files
# ---------------------------------------------------------------------------------------------


def variant_doc(slug: str) -> dict:
    return {"schema": 1, "slug": slug, "solver": "cad/layout.py",
            "configurations": {cfg: parameter_set(solve(slug, cfg)) for cfg in configurations(slug)}}


def variant_text(slug: str) -> str:
    return json.dumps(variant_doc(slug), indent=2, ensure_ascii=False) + "\n"


def write_variants(out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or params.VARIANTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for slug in params.case_slugs():
        path = out_dir / f"{slug}.json"
        path.write_text(variant_text(slug), encoding="utf-8", newline="\n")
        written.append(path)
    return written


def check_variants(out_dir: Path | None = None) -> list[str]:
    """Freshness: the committed files must be byte-identical to what the solver writes now."""
    out_dir = out_dir or params.VARIANTS_DIR
    problems = []
    slugs = params.case_slugs()
    for slug in slugs:
        path = out_dir / f"{slug}.json"
        if not path.is_file():
            problems.append(f"{path.name}: missing (run python -m cad.layout write)")
        elif path.read_text(encoding="utf-8") != variant_text(slug):
            problems.append(f"{path.name}: stale (run python -m cad.layout write)")
    extra = sorted(p.name for p in out_dir.glob("*.json") if p.stem not in slugs)
    if extra:
        problems.append(f"files without a case definition: {extra}")
    files = [out_dir / f"{s}.json" for s in slugs if (out_dir / f"{s}.json").is_file()]
    return problems + params.check_parameter_sets(files)


def main(argv: list[str] | None = None) -> int:
    usage = ("usage: python -m cad.layout write | check\n"
             "       python -m cad.layout derive SPEC --out OUT [--check]     (SPEC: a build_overrides file, see derive_document)")
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("write", "check", "derive"):
        print(usage)
        return 2
    if args[0] == "derive":
        rest = args[1:]
        check_only = "--check" in rest
        rest = [a for a in rest if a != "--check"]
        if len(rest) != 3 or rest[1] != "--out":
            print(usage)
            return 2
        spec, out = rest[0], rest[2]
        try:
            if check_only:
                problems = check_derived(spec, out)
                for pr in problems:
                    print("STALE:", pr)
                print("derived set is fresh and total" if not problems else f"{len(problems)} problem(s)")
                return 1 if problems else 0
            write_derived(spec, out)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            print("ERROR:", exc)
            return 2
        print("wrote", out)
        return 0
    if args[0] == "write":
        for p in write_variants():
            print("wrote", p)
        return 0
    problems = check_variants()
    for pr in problems:
        print("STALE:", pr)
    print("parameter sets are fresh and total" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
