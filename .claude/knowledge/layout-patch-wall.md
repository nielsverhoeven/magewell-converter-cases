# Patch-wall layout contract

Status: **revision 2, 2026-09-08.** Derived 2026-09-07 by solution-architect from the user's fixed
topology decision; revised 2026-09-08 to record the user's decisions on the dongle-class PoE splitter
(D-10), **side-bolt device retention** (D-09), D-04 accepted, **D-06 vetoed** (case height 51 mm) and
**D-08 vetoed** (straight-plug end zones).
Owner: solution-architect. Referenced from `architecture.md` §14.
This file is normative for `shell.scad`, `panel.scad`, `cradle.scad`, `mounts.scad`, `vents.scad` and
for the two new `fasteners.scad` modules in §7.1. None of those five L2 files exists yet — this
document is their specification.
Every number is either cited to `knowledge/**:line` / `lib/mcc/constants.scad:line`, or marked
`assumed` / `unknown`. Nothing here is invented silently.

---

## 0. The decision this implements

**Side-exit, one patch wall.** All external connectors sit in a single long side wall. The device
lies lengthwise; its end-face ports connect via short patch cables that turn 90° in the end
("corner") zones and run into the connector bay that spans the patch wall. The opposite long wall
and both end walls carry no connectors.

**The device is held by one horizontal captive 1/4"-20 bolt through that opposite (far) wall** into
the thread on the device's long side face — user-verified 2026-09-08. The floor through-bolt of the
original design is withdrawn.

Superseded: the in-line topology of `architecture.md` §1 (compact ~244 × 72 × 45, plus ~260 × 80 × 45).

---

## 1. Coordinate frame

Origin at the centre of the case's **outer** bounding box in X and Y, and at the case **underside**
(the bed plane) in Z. All shell/panel/cradle/mounts/vents geometry is authored in this frame.
`W` excludes the side-bolt lug of §7.1; the printed bbox in Y is `W + MCC_SIDE_BOLT_PROUD`.

| Axis | Direction | Range |
|---|---|---|
| X | along the device length; +X = "end B" side | `[-L/2, +L/2]` |
| Y | +Y = **towards the patch wall**; −Y = **the far wall, which carries the side bolt** | `[-W/2, +W/2]` |
| Z | up; z=0 is the printed underside of the base | `[0, H]` |

Derived planes (all changed by the D-06 veto — see §2.2):

| Plane | Expression | Value |
|---|---|---|
| Interior floor (top of floor) | `z = MCC_FLOOR_T` | 3.0 (`constants.scad:23`) |
| Lid underside | `z = MCC_FLOOR_T + H_int` | **48.0** |
| Outer height | `H = MCC_FLOOR_T + H_int + MCC_LID_T` | **51.0** |
| Far (−Y) wall inner face | `y = -W/2 + MCC_WALL` | `constants.scad:22` |
| Far (−Y) wall outer face, at the side-bolt boss only | `y = -W/2 - MCC_SIDE_BOLT_PROUD` | −10 mm proud, §7.1 |
| Patch (+Y) wall inner face | `y = +W/2 - MCC_T_PATCH` | `MCC_T_PATCH = 8.0`, §2.1 |
| End wall inner faces | `x = ±(L/2 - MCC_WALL)` | |

### Device placement — zero yaw, by construction

```
y_dev_lo = -W/2 + MCC_WALL + MCC_GAP_FAR          // MCC_GAP_FAR = 6.0 (assumed, §5 airflow duct)
y_dev_hi = y_dev_lo + dev_w
y_dev_c  = y_dev_lo + dev_w/2
x_dev_lo = -L/2 + MCC_WALL + ez_neg               // ez = end zone, §4
x_dev_c  = x_dev_lo + dev_l/2
z_dev_lo = MCC_FLOOR_T + MCC_CRADLE_DECK          // MCC_CRADLE_DECK = 10.8, §7
```

**Yaw rule (D-09).** The device is placed at **zero yaw**: device-local +X → case +X, device-local
−Y → case −Y. This is not a free choice — it is forced by the requirement that the 1/4"-20 side
thread faces the far wall. The invariant is pushed into the *data*: every device file is authored in
a frame where the side-bolt port is on `face [0,-1,0]` (`architecture.md` §7, the `side_bolt`
convention). If a measurement shows the hole on the other long side, **the device file is rewritten**
(negate `face.x` and `pos[0]` on every port = rotate the record 180° about Z); no rotation ever
enters `shell.scad`.

Consequences, all deliberate:
- L2 geometry has no `yaw` parameter and no orientation branch.
- **The envelope is yaw-invariant**: a flip only swaps `ez_neg` and `ez_pos` in
  `L = 2·MCC_WALL + ez_neg + dev_l + ez_pos`, and leaves `W` and `H` untouched. So the case size does
  not depend on the unmeasured hole side; only the mirror image of the slot order does.
- On HDMI TX / SDI TX the 16-position rotary switch is also authored on the −Y face
  (`pro-convert-hdmi-tx.scad:34`, `pro-convert-sdi-tx.scad:31`). The boss keep-out must clear it
  (T1-27). If those two SKUs flip, the rotary ends up facing the patch wall — acceptable while it is
  `panel:"none"`, but record it if the user ever wants access to it.

**Cradle deck height is not free.** It is fixed by requiring the device's end-face port centreline
to coincide with the panel-connector centreline, so every patch cable runs level:

```
z_conn_c   = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H/2 = 3 + 3 + 19.5 = 25.5
z_dev_lo   = z_conn_c - dev_h/2                           = 25.5 - 11.7 = 13.8   (plus,    dev_h 23.4)
                                                          = 25.5 - 11.65 = 13.85 (compact, dev_h 23.3)
MCC_CRADLE_DECK = z_dev_lo - MCC_FLOOR_T                  = 10.8 / 10.85
                                                          = 8.8 mm cradle deck + 2.0 mm compliant pad
```

Compliant pad 2.0 mm: EPDM anti-slip pad, `knowledge/components/fasteners-and-hardware.md:186`
(⌀12 × 2.5 mm listed; 2.0 mm used as the compressed working thickness, `assumed`).

Consequence for the Plus family: `z_dev_hi` = 13.8 + 23.4 = 37.2, leaving **10.8 mm of plenum above
the device's top "MAGEWELL" grille** (`knowledge/magewell/housing-families.md:69`) — which
`architecture.md` §12 Q10 forbids sealing. (Was 9.8 mm at H = 49; the D-06 veto bought 1 mm of extra
plenum, which is a small thermal win, not just a cost.)

---

## 2. Panel plate aperture in the patch wall

### 2.1 Wall stack in Y at the panel band

| Layer | Thickness | Source |
|---|---|---|
| Proud sacrificial bezel (shell stands proud of the Neutrik flange face) | 3.0 `assumed` | `architecture.md` §5 recessed-connector principle; flange front protrusion is `unknown` |
| Plate seat (rabbet depth for the 2.0 mm plate) | 2.0 | `MCC_PANEL_SEAT_T`, `constants.scad:76`; `knowledge/neutrik/d-series-cutout.md:90` NAHDMI-W max 2 mm |
| Structural rabbet lip (the shell material the plate lands on, pierced by the aperture) | 3.0 | `MCC_WALL`, `constants.scad:22` |
| **`MCC_T_PATCH` total** | **8.0** | |

The plate front face therefore sits 3.0 mm inside the shell's outer face; the Neutrik flange sits on
the plate front face. `mcc_bay_depth(part)` is measured **from the flange face**
(`knowledge/neutrik/placement-and-depth.md:5-8`), so 5.0 mm of it (plate + lip) is material and only
`mcc_bay_depth(part) - 5.0` has to be free interior.

### 2.2 Plate in Z — **D-06 vetoed, the plate is 39 mm and the case is 51 mm**

Two constraints; the **web** now governs, not the boss:

```
web rule (D-06 VETOED 2026-09-08 — 4.0 mm applies in Z as well as in X):
  MCC_PLATE_H >= MCC_D_FLANGE[1] + 2 * MCC_D_FLANGE_EDGE_MARGIN = 31 + 2*4.0 = 39.0

rear-boss rule (still satisfied, no longer binding):
  boss_od = MCC_BOSS_MIN_RATIO * insert_od = 1.8 * 4.6 = 8.28            constants.scad:102, 96-99
  MCC_PLATE_H >= 2 * (MCC_D_SCREW_PITCH[1]/2 + boss_od/2 + 2.0) = 36.28  constants.scad:58

  ->  MCC_PLATE_H = 39.0
```

- 12.0 = screw offset, `knowledge/neutrik/d-series-cutout.md:47`
- 4.0 = `MCC_D_FLANGE_EDGE_MARGIN`, `constants.scad:71`
- 2.0 = minimum material from an insert bore wall to a part edge,
  `knowledge/design/fdm-rugged-enclosure-guidelines.md:127`

```
MCC_PANEL_BAND = 3.0    // continuous shell band above and below the aperture (= MCC_WALL)
H_int = MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND = 3 + 39 + 3 = 45.0
H     = MCC_FLOOR_T + H_int + MCC_LID_T              = 3 + 45 + 3 = 51.0
```

Aperture Z range (case coords): `z ∈ [6.0, 45.0]`; plate Z range identical; connector centreline
`z = 25.5`. Resulting web from the 31 mm flange to the plate edge = **(39 − 31)/2 = 4.0 mm** in Z,
matching X. The `architecture.md` §9 assert table needs no exception any more.

**Tongue-and-groove polarity stays fixed by the same reasoning: the base carries the tongue (raised),
the lid carries the groove.** If the base carried the groove it would be cut into the 3 mm band above
the aperture, leaving < 1 mm of material. Decision **D-07**, unaffected by the D-06 veto.

### 2.3 Plate in X

```
MCC_PANEL_FRAME_MIN = 10.0     // shell frame band beyond each plate end
MCC_PLATE_END_PAD   =  8.0     // plate material outboard of the outer flange, carries the M3 retaining tabs
plate_l = L - 2*MCC_WALL - 2*MCC_PANEL_FRAME_MIN = L - 26
span    = plate_l - MCC_D_FLANGE[0] - 2*MCC_PLATE_END_PAD = plate_l - 42 = L - 68
pitch   = span / (n_slots - 1)
slot_x(i) = -span/2 + (i-1)*pitch          for i = 1..n_slots, left to right
```

The slots are spread **as wide as the wall allows** rather than packed at the minimum pitch. This is
deliberate: the widest possible pitch gives every cable the longest possible run to its 90° turn, and
puts the two outer slots as close as possible to the end-zone corners where the turns happen.

Plate retention: 4 × M3 into heat-set inserts, screws **along +Y**, through tabs in the plate's two
`MCC_PLATE_END_PAD` regions (two per end, at `z = z_conn_c ± 14`), into bosses standing rearward off
the rabbet lip. Those X positions are always outboard of every flange, so the bosses never intrude
into a connector bay.

> **Correction, 2026-09-08.** Revision 1 recorded `L_panel_min = 172` (4 slots) / `140` (3 slots).
> Those do not follow from the formula above, which gives **164** and **132**
> (`span + 68`, `span = (n_slots−1)·32`). The corrected figures are used in §8. It changes nothing
> in practice — with the straight-plug end zones every priority SKU is governed by the device branch
> of the `L` formula, not by `L_panel_min`.

### 2.4 Panel-plate summary (one long plate per case)

| Property | Value |
|---|---|
| Thickness | 2.0 mm at every flange seat; ribbed to 3.0 mm elsewhere (`architecture.md` §5) |
| Height | **39.0 mm** |
| Length | `L - 26` (147.9 compact, 164.5–165.5 plus) |
| Slots | up to 4, `pitch = (L - 68)/(n_slots - 1)`, asserted ≥ `MCC_D_PITCH_H` (32, `constants.scad:65`) |
| Parts dispatchable | `NE8FDP-B`, `NAHDMI-W-B`, `NAUSB-W-B`, `NBB75DFGB`, `DBA-BL-B` only |
| Print orientation | flat, face-down (`architecture.md` §5) |
| Rim | 3 mm ribbed rim around the whole outline |

---

## 3. Slot assignment — `mcc_slot_for_port()` semantics

Pure, deterministic, data-only. No per-device hand placement anywhere. **Unchanged by revision 2.**

```
mcc_slot_for_port(dev, port_id) -> integer 1..n_slots
```

**Algorithm**

1. `ext = mcc_ports_external(dev)` (`ports.scad:57`). `n_slots = len(ext)`.
   Assert `n_slots <= MCC_SLOTS_MAX` (4) and `n_slots >= 1`.
2. Assert every `p` in `ext` has `mcc_port_face(p)` equal to `[-1,0,0]` or `[+1,0,0]`.
   The side-exit topology has no answer for a port on a long face or on the top/bottom; fail loudly
   rather than guess. (The `side_bolt` port is *not* external — `panel:"none"` — so it is never in
   `ext` and never trips this assert.)
3. Partition: `A = {p : face.x < 0}` (end A, the −X end), `B = {p : face.x > 0}`.
4. Slot block allocation: **A takes slots `1 .. len(A)`; B takes slots `n_slots-len(B)+1 .. n_slots`.**
   Ports therefore never cross the case; a port on end A always lands in the −X half of the wall.
5. Ordering inside a block — **stiffest cable outermost**:
   `rank(p) = [ mcc_bend_envelope(panel(p)), mcc_plug_len(panel(p)) ]`, compared lexicographically,
   descending. Ties broken by `mcc_port_pos(p)[0]` ascending, then `mcc_port_id(p)` lexicographically
   (determinism is required for the geometry goldens).
   - Block A: highest rank → slot 1, next → slot 2, …
   - Block B: highest rank → slot `n_slots`, next → slot `n_slots-1`, …
6. Any slot left unallocated (only possible if the caller pads `n_slots` up to 4 for a spare) is
   `DBA-BL-B`. Unallocated slots are always the innermost ones, which is where a blank belongs.

**Why "stiffest outermost".** The outermost slot is the one whose rear plug sits in the end-zone
corner, directly opposite the device's end face. A cable to that slot makes exactly one 90° L. A
cable to an inboard slot has to leave the device along ∓X, turn, and come back along ±X — an S-bend
in a shallower space. The stiffest cable must get the L, not the S.

`rank` is read straight out of `MCC_PANEL_PARTS` (`constants.scad:242-248`), so it needs no new
hand-maintained table and updates automatically when the `depth-mockup` coupon replaces the assumed
`plug_len`/`bend` figures:

| Part | bend | plug_len | effective rank |
|---|---|---|---|
| `NBB75DFGB` | 40.6 | 40.6 | 1 (stiffest) — Belden 4855R bend radius, `knowledge/components/cables.md:63` |
| `NAHDMI-W-B` | 15 | 35 | 2 |
| `NE8FDP-B` | 10 | 25 | 3 |
| `NAUSB-W-B` | 8 | 20 | 4 |
| `DBA-BL-B` | 0 | 0 | 5 |

**Worked results for the priority SKUs** (end A = the device's data/power end for encoders, per
`knowledge/magewell/housing-families.md:57-67` and `:126-149`):

| SKU | slot 1 | slot 2 | slot 3 | slot 4 |
|---|---|---|---|---|
| HDMI Plus / HDMI 4K Plus | NE8FDP-B (etherCON) | NAUSB-W-B (USB-B 5 V) | NAHDMI-W-B (HDMI IN) | NAHDMI-W-B (HDMI loop-OUT) |
| SDI Plus / SDI 4K Plus / 12G SDI 4K Plus | NE8FDP-B | NAUSB-W-B | NBB75DFGB (SDI OUT) | NBB75DFGB (SDI IN) |
| HDMI TX | NAHDMI-W-B (HDMI IN) | NAUSB-W-B | NE8FDP-B | — (3 slots) |
| SDI TX | NBB75DFGB (SDI IN) | NAUSB-W-B | NE8FDP-B | — (3 slots) |
| NDI to HDMI | NAHDMI-W-B (HDMI OUT) | NAUSB-W-B (USB-A host) | NAUSB-W-B (USB-B) | NE8FDP-B |
| NDI to SDI | NBB75DFGB (SDI OUT) | NAUSB-W-B (USB-A host) | NAUSB-W-B (USB-B) | NE8FDP-B |
| NDI to AIO | NBB75DFGB (SDI OUT) | NAHDMI-W-B (HDMI OUT) | NAUSB-W-B (USB-B) | NE8FDP-B |
| NDI to HDMI 4K (Plus chassis) | NAHDMI-W-B (HDMI OUT) | NAUSB-W-B (USB-A host) | NAUSB-W-B (USB-B) | NE8FDP-B |

Note the Mini-DIN-8 PTZ/Tally port does **not** appear: `panel:"none"` on every SKU (decision D-01).

---

## 4. End zones and the corner bend envelope — **straight plugs (D-08 vetoed)**

The end zone is the X gap between the device's end face and the inner face of that end wall. It has
to hold the device-side plug **and** the start of the 90° turn.

```
ez(end) = max over ports on that end of mcc_dev_side_allow(kind),  floored at MCC_END_ZONE_MIN = 20 (assumed)
```

**Rule for `mcc_dev_side_allow(kind)`:** take the *Recommended minimum internal clearance* column of
`knowledge/components/cables.md:117-126` where the source gives one; where the source says `unknown`,
use `assumed straight-plug axial length + mcc_bend_envelope(part)`. Only `hdmi_a` falls into the
second case.

| kind | allow (mm) | Derivation / source | Confidence |
|---|---|---|---|
| `bnc` | 41 | `cables.md:123` — Belden 4855R min bend radius 40.6 mm, verified; the source uses the bend radius directly and notes "add more if the connector's own body length turns out to exceed this once measured" | bend radius verified, total `assumed` |
| `hdmi_a` | **40** | **25 (straight-plug axial, `assumed` — `cables.md:121` records it as `unknown — physically measure`) + 15 (`mcc_bend_envelope("NAHDMI-W-B")`, `constants.scad:244`, `assumed`)** | `assumed` |
| `rj45` | 27 | `cables.md:119` — 21.5 mm max plug (TIA-568.2-D, verified) + 5 mm margin | plug verified |
| `usb_a`, `usb_b` | 17 | `cables.md:125` — USB-A 12 mm verified + 5 mm margin; **USB-B is `unknown`, assumed equal** | mixed |
| `minidin8` | 0 | internal, not cabled (D-01) | — |
| `rotary16`, `button`, LEDs, SD slot | 0 | not cabled | — |
| `tripod_1_4_20` | 0 | the side bolt is on a long face, never an end face (D-09) | — |

**What changed and why it matters.** Revision 1 used `ez(hdmi_a) = 30`, valid only with a right-angle
adapter fitted at the device end (25.4 mm verified, `cables.md:122`). The user **vetoed** that adapter
in the default BOM (D-08), so the straight-plug figure applies: +10 mm of `L` on every HDMI-ended
SKU. It is the *weakest* number in this document — a 25 mm assumption with a 15 mm assumption stacked
on it. **The `depth-mockup` coupon must measure it before the shell is printed** (`architecture.md`
M6). A right-angle adapter remains a legal per-variant option; a variant that declares one drops back
to `ez = 30` and must list the adapter in its own BOM.

The BNC row is the other soft spot: it is a bend radius with **no plug-body term at all**, because
`cables.md:64` records the BNC male plug's overall length as `unknown`. If the measured plug body
exceeds ~0 mm of the arc — i.e. essentially always — the true allowance is larger than 41 mm. The
same coupon settles it. Recorded so nobody mistakes 41 for a measured figure.

### Does the connector bay run the full device length?

**Yes.** With `n_slots` up to 4 and the pitch above, the outer slot centres sit at `±(L/2 - 21)`,
which for every priority SKU is outboard of or within a few mm of the device's end faces, but slots 2
and 3 sit over the device's X range. So the bay's Y depth must be clear for the whole plate span, not
just in the corners:

```
d_bay_free = max over external ports of mcc_bay_depth(panel) - (MCC_WALL + MCC_PANEL_SEAT_T)
           = 75.65 - 5.0 = 70.65   (HDMI-bearing devices; 74.6 - 5 = 69.6 for BNC-without-HDMI)
W = MCC_T_PATCH + d_bay_free + MCC_GAP_DEV + dev_w + MCC_GAP_FAR + MCC_WALL
  = 8 + d_bay_free + 2 + dev_w + 6 + 3
```

`MCC_GAP_DEV = 2.0` (`assumed`) is the clearance between the deepest plug envelope and the device's
patch-side flank. Because it is only 2 mm, **cradle locating ribs on the patch-side flank are
permitted only at X positions outboard of the plate aperture** (`|x| > plate_l/2 - 3`); everywhere
else the patch flank is located by the far-side ribs and the side bolt alone.

The BNC lateral bend envelope (40.6 mm, `cables.md:63`) is satisfied inside the bay in the Y–Z plane:
70.65 mm of free Y ≫ 40.6 mm. It does **not** force BNC onto an end slot.

---

## 5. Fan bay, PoE-splitter bay, vents

Reserved in every variant even when disabled (`architecture.md` §6 reservation rule).

### Fan bay — **+X end wall**

- Default part `NF-A4x10` 40 × 40 × 10, mounting pitch 32 × 32 (`knowledge/components/fans.md:15-17`,
  `MCC_FANS`, `constants.scad:138`).
- Frame mounts on the **inside** face of the +X end wall; the wall aperture is **⌀38 max**, centred at
  `(x = L/2, y = y_dev_c, z = z_conn_c = 25.5)`. Derivation: `H_int - 2*MCC_WALL = 45 - 6 = 39`, so
  ⌀38 leaves exactly 3.5 mm of wall above and below. (Was ⌀36 at `H_int = 43`; the D-06 veto bought
  2 mm of aperture, i.e. measurably more free area.) `assumed`.
- 4 × NA-AV3 through-holes at ±16 mm (`fans.md:86-91`; the correct mount type for a closed-corner
  10 mm fan, and it decouples motor vibration from the shell).
- Exhaust direction +X: **away from the patch wall**, so the fan is never behind the cable bundle.
- Assert: the fan bay may not be placed on the +Y face, and may not intersect the end-zone cable
  envelope of the +X end.

### PoE-splitter bay — **−X end, on edge** (D-10; **placement still blocking, see R15**)

Functionally correct end: the splitter's three connections (PoE in from etherCON, data out to the
device RJ45, 5 V out to the device USB-B and the fan — `knowledge/components/poe-splitters.md:170-192`)
all terminate at the device's data/power end, which the slot rule puts at the −X end for every
encoder. It is also the intake end, satisfying R6.

**Default part (user decision 2026-09-08): `DONGLE-75x40x20`** — a dongle-class 802.3af/at → 5 V USB
splitter, UCTRONICS U6114/U6115 class, `MCC_SPLITTERS`, `constants.scad:164`. Its dimensions are
**`assumed`**: `poe-splitters.md:129-136, 211-215` records them as unpublished. The user will buy one
and measure (`architecture.md` M3). `GAT-USBC` (114 × 51 × 25, `poe-splitters.md:58`) stays in the
table as a named non-default alternative and does not fit this topology at all (R11).

**Orientation: on edge.** 20 mm in X, 75 mm in Y, 40 mm in Z — the only orientation of a 75 × 40 × 20
slab that fits a 45 mm interior at all (40 ≤ 45; laid flat it needs 40 mm of X, standing 75-up it
needs 75 mm of Z).

```
env    = MCC_SPLITTERS[part].size = [75, 40, 20]
bay_x  = [-L/2 + MCC_WALL,          -L/2 + MCC_WALL + 20]
bay_y  = [-W/2 + MCC_WALL,          -W/2 + MCC_WALL + 75]
bay_z  = [MCC_FLOOR_T,              MCC_FLOOR_T + 40]
```

- **Connector-bay check (T1-16) passes.** `bay_y` reaches `y = -0.2` (plus family); slot 1's etherCON
  plug envelope reaches inward only to `y = +10.6`. 10.8 mm clear. This is what R11 asked for.
- **End-zone check (T1-28) FAILS at `ez_neg = 27`.** The slab occupies the outer 20 mm of the 27 mm
  end zone, across the full width, at `z ∈ [3, 43]` — straight through the `z ≈ 19.5–31.5` band where
  the device's USB-B and RJ45 patch leads run. Those leads need their 17/27 mm **whether or not** a
  splitter is fitted (with a splitter they simply terminate at it instead of at the plate), so the
  allowances **sum**: `ez_neg = max(cable allow) + 20 = 47`. Cost **+20 mm of L**. See R15 — user
  decision required; §8 tabulates the envelope both ways.
- Secondary: the on-edge slab masks the −Y half of the −X end wall, so that wall's intake vent band
  must sit in the **+Y half** only.
- Tie-downs: 2 × ⌀8 in the floor inside `bay_x × bay_y`, owned by `mounts.scad` (§7 floor rule).

### Vents (`vents.scad`) — chimney slots

`knowledge/design/thermal-guidelines.md:164-185` and
`knowledge/design/fdm-rugged-enclosure-guidelines.md:190-199`.

| Band | Face | Z range (case coords) | Role |
|---|---|---|---|
| Intake, low | −X end wall, **+Y half only** | `[5, 17]` | cool air in low; mesh filter pocket on the inside (`thermal-guidelines.md:193-195`). +Y half because the splitter slab masks the −Y half |
| Intake, low | −Y far long wall, full device length | `[5, 17]` | feeds the 6 mm `MCC_GAP_FAR` duct along the device's metal flank |
| Exhaust, high | −Y far long wall, +X half only | `[32, 44]` | passive outlet when `fan=false`; offset in X from the intake to avoid short-circuiting (`thermal-guidelines.md:176-179`) |
| Exhaust | +X end wall | fan aperture, ⌀38 | forced outlet when `fan=true` |
| **None** | **+Y patch wall** | — | **assert: no vent may be cut in the patch wall** (T1-19) |
| **None** | **inside the side-bolt keep-out** | ⌀24 disc at `(x_bolt, z_bolt)` on the far wall | **assert T1-23**; the boss bridges the duct at that X, so a slot there would open into solid material anyway |

`MCC_GAP_FAR = 6.0` exists precisely so the far-wall slots open into a real duct rather than onto the
device skin. Slot geometry: vertical slots through the wall thickness (no bridging,
`fdm-rugged-enclosure-guidelines.md:199`), slot width ≥ 1.2 mm `assumed` (nearest verified analogues
0.8 mm minimum wall and 1.0 mm lattice gap, `fdm-...:197`), web ≥ 1.6 mm, any bridged span ≤ 10 mm
(`fdm-...:111`).

**The side-bolt boss blocks the duct locally.** It is a full-width plug across the 6 mm duct at one X
position. `vents.scad` must therefore place slots on *both* sides of it in X (the duct is not a
single continuous chimney any more), and the exhaust band's `+X half only` rule must be evaluated
against the boss position, not blindly.

---

## 6. Lid fasteners (R7 resolution — **D-04 accepted by the user 2026-09-08**)

```
n_fast = (L > MCC_LID_SPAN_MAX) ? 6 : 4        MCC_LID_SPAN_MAX = 180
e      = 10.0                                  // fastener ring inset from the outer faces
```

- 4 corners at `(±(L/2 - e), ±(W/2 - e))`.
- If `n_fast == 6`: one extra at `(0, -(W/2 - e))` on the far wall, and one on the patch wall at
  `x = x_gap`, the widest inter-slot gap centre that clears the nearest flange edge by
  `≥ boss_od/2 + 2.0 = 6.15 mm`. **If no such gap exists, the patch-side mid fastener is replaced by
  an internal buttress rib** tying the patch wall to the lid tongue at that X.
- With the straight-plug end zones the plus pitch is 40.83 mm (HDMI Plus) / 41.17 mm (SDI Plus), so
  the mid-span boss clears by 7.42 / 7.58 mm and **the buttress fallback is currently unused on every
  priority SKU**. Keep the rule; a future SKU may need it. (Revision 1's "HDMI Plus falls into the
  buttress case" no longer holds — it was true at pitch 37.5 mm.)
- The far-wall mid fastener at `(0, -(W/2 - e))` must clear the side-bolt keep-out (T1-27). With the
  default `pos [0,0]` placeholder they are at the same X, so **one of them moves**: the rule is that
  the *fastener* moves (to the nearest X clear of the keep-out), because the bolt position is dictated
  by the device.
- Corner bosses always clear the outer flange by 11.0 mm by construction (`(L/2-10) - (L/2-21)`).

Captive M3 knurled thumbscrews into M3 heat-set inserts (`MCC_INSERT_M3`, `constants.scad:96`);
boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:102`), ≥ 2 mm material to any edge
(`fdm-rugged-enclosure-guidelines.md:127`).

Family outcome: **compact → 4 (L ≤ 174.9); plus → 6 (L ≥ 190.5).**

---

## 7. Cradle and floor features

### Cradle

| Property | Value | Source |
|---|---|---|
| Deck top (device underside) | `z = 13.8` (plus) / `13.85` (compact) | §1, port-centreline alignment |
| Deck slab | 8.8 mm, ribbed/hollow, 3 mm top plate on 3 mm webs | `MCC_WALL` |
| Compliant pad, floor | 2.0 mm EPDM under the device, footprint ≥ 40 × 40 near the case centre | `fasteners-and-hardware.md:186` |
| Compliant pad, side bolt | 2.0 mm EPDM annulus, OD 18 / ID 8, on the boss face | §7.1 |
| Locating ribs | 3.0 mm thick × 9.0 mm tall | `fdm-...:68` rib height ≤ 3 × thickness |
| Far-flank ribs | discrete fins at ≥ 3 X positions; must not block the far-wall intake slots **and must not intersect the side-bolt keep-out** | §5, §7.1 |
| Patch-flank ribs | **only** where `|x| > plate_l/2 - 3` | §4, `MCC_GAP_DEV` = 2 mm |
| End ribs | partial only — must clear every end-face port cutout and the plug envelope | §4 |
| Anti-rotation | **carried entirely by the ribs.** One horizontal bolt is one point of restraint; ribs are structural, not cosmetic | R8 |
| Floor penetration | **none.** `cradle.scad` never cuts the floor | `architecture.md` §6 |

### 7.1 Side-bolt boss — normative geometry (D-09)

The one genuinely new mechanism in revision 2. Everything below is authored **along the local +Z
axis** to match `fasteners.scad`'s existing convention (a boss stands with its base at Z = 0 and
grows toward +Z); `shell.scad` rotates it onto the far wall's outward normal. `Z = 0` is the
**outermost surface of the lug**, and +Z runs into the case.

**Axis placement in case coordinates**

```
p        = the device's side_bolt port          (kind "tripod_1_4_20", face [0,-1,0])
x_bolt   = x_dev_c + mcc_port_pos(p)[0]         // +u = +X looking at the -Y face from outside
z_bolt   = z_conn_c + mcc_port_pos(p)[1]        // = 25.5 + v
y_axis   = the -Y wall's outward normal
```

Converting a physical measurement: `u = ±(dev_l/2 − X_from_that_short_end)` (sign per which end you
measured from), `v = Z_from_device_bottom − dev_h/2`. Every SKU is `confidence:"assumed"` with
`pos [0,0]` until measured (`architecture.md` M1).

**Axial stack** (Z from the lug's outer surface, all `assumed` unless cited)

| Z range | Feature | ⌀ | Note |
|---|---|---|---|
| `[0, 6.0]` | Slotted head recess | **12.0** | depth = head height + 1.5, so the head sits **≥ 1 mm below the outer surface** (no proud metal, drop rule) |
| `[6.0, 9.0]` | Retaining web, shank clearance bore | **6.6** | `MCC_TRIPOD_CLR_D`, `constants.scad:111`. `web_t = 3.0` — this shoulder is what the E-clip lands on |
| `[9.0, 17.0]` | E-clip clearance pocket | **13.0** | `pocket_h = 8.0` = engagement 6.0 + clip thickness 0.7 + 1.3 margin |
| `[17.0, 19.0]` | Compliant pad (EPDM annulus, OD 18 / ID 8) | — | bears on the device flank; provides the preload |
| `19.0` | Device side face | — | `= MCC_SIDE_BOLT_PROUD + MCC_WALL + MCC_GAP_FAR` = 10 + 3 + 6 |
| `[19.0, 25.05]` | Thread engagement into the device | — | `e = 6.0`, **`assumed` — the device's thread depth is unmeasured** (M2) |

**Derived quantities** (all of these are formulas, not magic numbers, and belong in `constants.scad`)

```
boss_len            = head_rec_h + web_t + pocket_h            = 6.0 + 3.0 + 8.0 = 17.0
MCC_SIDE_BOLT_PROUD = max(0, boss_len - (MCC_WALL + MCC_GAP_FAR - pad_t))
                    = max(0, 17.0 - (3 + 6 - 2))              = 10.0
screw_len_under_head= MCC_SIDE_BOLT_PROUD + MCC_WALL + MCC_GAP_FAR + e - head_rec_h
                    = 10 + 3 + 6 + 6 - 6                      = 19.0  -> stock 3/4" = 19.05
groove_pos          = web_t + e + 1.0                         = 10.0  (from under the head)
clip_travel         = groove_pos - web_t                      = 7.0   >= e + 0.5 = 6.5   OK
boss_od             = pocket_d + 2 * 3.5                      = 20.0
keepout_d           = boss_od + 2 * 2.0                       = 24.0
```

**Screw and clip**

| Item | Spec | Confidence |
|---|---|---|
| Screw | 1/4"-20 UNC, **slotted** (flat-blade — deliberate: a tool everyone has, and it discourages power drivers), 19.05 mm (3/4") under the head, stainless; overall ≈ 23.5 mm | `assumed` |
| Head ⌀ / height | **10.0 / 4.5 mm assumed.** Nearest metric standard is ISO 1207 / DIN 84 cheese head **M6** (dk 10.0, k 3.9, slot n 1.6); the inch equivalents (fillister dk ≈ 9.53, k ≈ 4.37; pan dk ≈ 12.5, k ≈ 3.56) bracket it. **Not sourced in `knowledge/**`** — measure the screw actually bought (M5) and re-derive `head_rec_h`, which re-derives `MCC_SIDE_BOLT_PROUD` | `assumed` |
| Retaining groove | on the shank, **10.0 mm below the under-head face**; ⌀ and width per the clip below. On a fully-threaded stock screw this lands in the threads — acceptable, but see R16 | `assumed` |
| E-clip | **DIN 6799, nominal size 5** — the size normally listed for a 6–7 mm shaft. Groove ⌀ **5.0 mm**, groove width **0.8 mm**, clip OD ≈ **11.0 mm**, thickness **0.7 mm**. **NOT VERIFIED: DIN 6799 is not in `knowledge/**` and these figures were not read from the standard.** Confirm before ordering (M4) | `assumed` |
| Washer | stainless ⌀12–14 × 1 mm on the recess floor under the head, to stop the ASA web being scrubbed on every device swap | `assumed` (R19) |
| Pad | 2.0 mm EPDM annulus OD 18 / ID 8. Nearest sourced part is the ⌀12 × 2.5 mm EPDM pad, `fasteners-and-hardware.md:186` — a die-cut washer may be needed instead | `assumed` |

**Why the wall grows a 10 mm lug.** The captive stack needs 17 mm between the case's outer surface
and the pad face, and `MCC_WALL + MCC_GAP_FAR − pad_t = 7 mm` is all that exists. The 10 mm shortfall
is taken **locally, outward** rather than by widening `MCC_GAP_FAR` (which would add 10 mm to `W`
along the whole case). The lug is a ⌀20 cylinder standing 10 mm proud of the far wall with a **≤45°
conical blend** on its underside so it stays self-supporting when the base prints floor-down. See
R18 — flagged for a user sanity check; the alternative is a full-length external spine.

**Keep-outs owned by this feature** (`mcc_side_bolt_keepout()`, published by `shell.scad`)

- ⌀24 disc on the far wall at `(x_bolt, z_bolt)` — **no vent slot inside it** (T1-23).
- The same disc swept through the duct — **no cradle far-flank rib, no lid-fastener boss, no splitter
  bay inside it** (T1-27).
- The pad footprint must land wholly on the device's side face:
  `pad_od ≤ dev_h − 2·|v| − 2` and `|u| + pad_od/2 ≤ dev_l/2 − 2` (T1-24). With `pad_od = 18` and
  `dev_h = 23.4` this allows only `|v| ≤ 1.7 mm` — see R17, this is the tight one.

**Module contract** (to be added to `lib/mcc/fasteners.scad`; specification only — no code here)

```
mcc_captive_side_bolt_boss(proud, wall_t, gap_far, pad_t, od, blend_a)   // ADDITIVE
mcc_captive_side_bolt_cut (proud, wall_t, gap_far, pad_t,
                           head_d, head_h, head_rec_h, shank_d,
                           web_t, clip_pocket_d, pocket_h, engage)       // SUBTRACTIVE
```

Both share the local frame above. The cut runs from `Z = -EPS` through to `Z = proud + wall_t +
gap_far + EPS` so it also pierces the wall proper; the caller `difference()`s it after unioning the
boss into the shell. Asserts live in the modules (see T1-24 … T1-27) so a bad `pos` fails at render,
not at the printer. All `$fn = 64`, `circum = true` on every bore that must pass a real part
(`architecture.md` §3 `$fn` policy).

### Floor keep-out zones (`mcc_floor_keepout()`, plan view, case coords)

**The device-retention through-bolt row is deleted (D-09).** What remains:

| Feature | Zone | Position rule |
|---|---|---|
| Case 1/4"-20 **insert** (case → tripod/cheeseplate) | ⌀20 disc | `(0, 0)` — case plan centre, default. Note this is a *threaded* feature, not the ⌀6.6 clearance boss `mcc_tripod_boss()` currently models (deviation D2) |
| VESA 75 × 75 | 4 × ⌀12 discs at `vesa_pos + (±37.5, ±37.5)` | `vesa_pos` defaults to `(0,0)`; a shell parameter, shiftable per SKU |
| Fishtail M4 pair | reserve a 60 × 20 band centred on `vesa_pos` | hole pitch is **`unknown`** — `knowledge/magewell/accessories.md:26` gives only "2× M4×12 screws, 2× M4 nuts". Derive from `knowledge/magewell/assets/magewell-fishtail-bracket.stl` (M7) |
| Strap slots | 2 × (25 × 5) through-slots | `x = ±(L/2 - 25)`, `y = ±(W/2 - 12)` — `assumed` |
| Splitter tie-down | 2 × ⌀8 | inside `bay_x × bay_y` (§5) |
| Stacking profile | recess mirroring the lid's proud features | must clear all of the above **and the side-bolt lug** |

Minimum separation between any two floor features: 15 mm centre-to-centre for the ⌀12–⌀20 class
features, or `(r1 + r2 + 2.0)` where that is larger. `mounts.scad` asserts it.

---

## 8. Resulting envelopes

```
L = max( 2*MCC_WALL + ez_neg + dev_l + ez_pos , L_panel_min )
L_panel_min = 2*MCC_WALL + 2*MCC_PANEL_FRAME_MIN + (n_slots-1)*MCC_D_PITCH_H
              + MCC_D_FLANGE[0] + 2*MCC_PLATE_END_PAD
            = 164 for 4 slots, 132 for 3 slots        (corrected — see the note in §2.3)
W = MCC_T_PATCH + d_bay_free + MCC_GAP_DEV + dev_w + MCC_GAP_FAR + MCC_WALL
H = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND + MCC_LID_T = 51.0
bbox_W = W + MCC_SIDE_BOLT_PROUD                       // the number that goes on the build plate
```

**Per SKU** (`ez_neg` = the −X / data-power end, `ez_pos` = the +X / video end, at zero yaw):

| SKU | family | slots | ez_neg | ez_pos | L | W | H | pitch |
|---|---|---|---|---|---|---|---|---|
| HDMI Plus, HDMI 4K Plus | plus | 4 | 27 | 40 | 190.5 | 156.4 | 51.0 | 40.83 |
| SDI Plus, SDI 4K Plus, 12G SDI 4K Plus | plus | 4 | 27 | 41 | 191.5 | 155.3 | 51.0 | 41.17 |
| NDI to HDMI 4K | plus | 4 | 27 | 40 | 190.5 | 156.4 | 51.0 | 40.83 |
| HDMI TX | compact | 3 | 27 | 40 | 173.9 | 149.9 | 51.0 | 52.95 |
| SDI TX | compact | 3 | 27 | 41 | 174.9 | 148.8 | 51.0 | 53.45 |
| NDI to HDMI | compact | 4 | 27 | 40 | 173.9 | 149.9 | 51.0 | 35.30 |
| NDI to SDI | compact | 4 | 27 | 41 | 174.9 | 148.8 | 51.0 | 35.63 |
| NDI to AIO | compact | 4 | 27 | 41 | 174.9 | 149.9 | 51.0 | 35.63 |

**Family envelopes (the number to quote and to print):**

| Family | L × W × H | bbox W (incl. lug) | Lid fasteners | Bed margin vs 256 | vs the 250 assert limit |
|---|---|---|---|---|---|
| **compact** | **174.9 × 149.9 × 51.0** | 159.9 | 4 | 81.1 / 96.1 | 75.1 / 90.1 |
| **plus** | **191.5 × 156.4 × 51.0** | 166.4 | 6 | 64.5 / 89.6 | 58.5 / 83.6 |

Both families' largest part (the base) is well inside `MCC_BUILD - MCC_BED_MARGIN` = 250
(`constants.scad:25-26`, asserted by `util.scad:41-43`).

**If R15 is resolved by option (a)** — the splitter reservation absorbed into `ez_neg`, which is what
`architecture.md` §6's reservation rule actually demands — then `ez_neg = 27 + 20 = 47` and every
`L` above grows by exactly 20 mm:

| Family | L × W × H | Lid fasteners | Bed margin vs 256 |
|---|---|---|---|
| compact | 194.9 × 149.9 × 51.0 | **6** (L > 180) | 61.1 / 96.1 |
| plus | 211.5 × 156.4 × 51.0 | 6 | 44.5 / 89.6 |

Note the second-order effect: at 194.9 mm the **compact family crosses the 180 mm D-04 threshold and
also goes to 6 lid thumbscrews**. That is a BOM and a print-time change on five SKUs, and it is part
of the price of option (a). Do not treat R15 as a purely cosmetic 20 mm.

---

## 9. Tier-1 asserts this topology requires

Add to `architecture.md` §9's minimum set. All are cheap, pure, and fire at render.

| # | Assertion | Rationale / source |
|---|---|---|
| T1-01 | every external port's `face` is `[±1,0,0]` | §3 step 2 — side-exit has no answer otherwise |
| T1-02 | `n_slots = len(mcc_ports_external(dev)) <= MCC_SLOTS_MAX (4)` | user decision, ≤ 4 D ports per model |
| T1-03 | `mcc_slot_for_port()` is a bijection onto `1..n_slots` | no two ports share a slot |
| T1-04 | every slot carries exactly one part (external port or `DBA-BL-B`) | §3 step 6 |
| T1-05 | no port has `panel == "MINIDIN8"` | enforces D-01; `MINIDIN8` is not a row in `MCC_PANEL_PARTS` |
| T1-06 | `pitch >= MCC_D_PITCH_H (32)` | `constants.scad:65`, `placement-and-depth.md:42` |
| T1-07 | `d_bay_free >= max(mcc_bay_depth(part)) - (MCC_WALL + MCC_PANEL_SEAT_T)` | §4 |
| T1-08 | `d_bay_free >= max(mcc_bend_envelope(part))` | lateral keep-out, `architecture.md` §7 |
| T1-09 | `ez(end) >= max(mcc_dev_side_allow(kind))` over ports on that end | §4 |
| T1-10 | `plate_l <= L - 2*MCC_WALL - 2*MCC_PANEL_FRAME_MIN` | §2.3 |
| T1-11 | `MCC_PLATE_H >= 2*(MCC_D_SCREW_PITCH[1]/2 + boss_od/2 + 2.0)` | §2.2, `fdm-...:127` |
| T1-12 | flange-to-plate-edge web **≥ 4.0 in X and ≥ 4.0 in Z** | §2.2 — **D-06 vetoed**, the Z exception is withdrawn |
| T1-13 | every lid-fastener boss clears every flange edge by ≥ `boss_od/2 + 2.0` | §6 |
| T1-14 | `H_int >= MCC_CRADLE_DECK + dev_h + MCC_LID_CLEAR` | §1 |
| T1-15 | `H_int >= fan_aperture_d + 2*MCC_WALL` when a fan bay is reserved | §5 (45 ≥ 38 + 6) |
| T1-16 | `splitter_envelope ∩ connector_bay_envelope == ∅` | §5, R11 — **now passes** with the dongle default |
| T1-17 | `splitter_envelope ∩ mcc_floor_keepout() == ∅` | §7 floor rule |
| T1-18 | fan bay face `!= [0,+1,0]`, and `fan_bay ∩ end_zone_cable_envelope == ∅` | §5 |
| T1-19 | no vent slot intersects the patch wall | §5 |
| T1-20 | patch-flank cradle ribs only where `|x| > plate_l/2 - 3` | §4 |
| T1-21 | `L <= MCC_BUILD - MCC_BED_MARGIN` and `bbox_W <= MCC_BUILD - MCC_BED_MARGIN` for base and lid | `util.scad:41-43`; note **`bbox_W`**, i.e. including the lug |
| **T1-22** | exactly one port per device has `kind == "tripod_1_4_20"`, and its `face == [0,-1,0]` | §1 yaw rule, `architecture.md` §7 `side_bolt` convention. **Replaces the floor-bolt asserts** |
| **T1-23** | `mcc_side_bolt_keepout() ∩ vent_slots == ∅` | §5, §7.1 |
| **T1-24** | bolt axis lands inside the device's −Y face: `pad_od <= dev_h - 2*abs(v) - 2` and `abs(u) + pad_od/2 <= dev_l/2 - 2` | §7.1, R17 — the assert that catches a bad measurement |
| **T1-25** | head fully recessed: `head_rec_h >= head_h + 1.0` | §7.1, drop rule (nothing proud) |
| **T1-26** | clip pocket lies wholly inside the boss and the clip can travel far enough: `head_rec_h + web_t + pocket_h <= proud + MCC_WALL + MCC_GAP_FAR - pad_t` **and** `groove_pos - web_t >= engage + 0.5` | §7.1 — if this fails, the device cannot be removed without dropping the screw inside the case |
| **T1-27** | `mcc_side_bolt_keepout()` intersects no cradle far-flank rib, no lid-fastener boss, and not the splitter bay | §5, §6, §7.1 |
| **T1-28** | `splitter_envelope ∩ end_zone_cable_envelope == ∅` | §5 — **currently FAILS at `ez_neg = 27`; this is R15** |

---

## 10. Decisions recorded here

| ID | Decision | Origin | Status |
|---|---|---|---|
| D-01 | Mini-DIN-8 PTZ/Tally stays internal, `panel:"none"` on every SKU. `mcc_panel_cutout()` dispatches Neutrik D parts + `DBA-BL-B` only. | User, 2026-09-07 | **fixed** |
| D-02 | Side-exit, one patch wall (this document). | User, 2026-09-07 | **fixed** |
| D-03 | HDMI loop-out is brought outside on the Plus encoders. | User, 2026-09-07 | **fixed** |
| D-04 | 4 captive M3 thumbscrews baseline; **6 for lids over 180 mm span**. | Architect-derived, user-reviewed | **ACCEPTED 2026-09-08** |
| D-05 | Slot assignment is computed from `mcc_bend_envelope`/`mcc_plug_len`, not hand-placed. | Architect-derived | **fixed** |
| D-06 | Relax the flange-to-plate-edge web from 4.0 to 3.0 mm in Z only (would have bought a 49 mm case). | Architect-derived | **VETOED 2026-09-08** — web stays 4.0 mm, plate 39 mm, **case height 51 mm** |
| D-07 | Tongue on the **base**, groove in the **lid**. | Architect-derived (the 3 mm band above the aperture) | **fixed**, unaffected by the D-06 veto |
| D-08 | Right-angle HDMI adapter as a required BOM line at every device-side HDMI port. | Architect-derived | **VETOED 2026-09-08** — end zones sized for **straight** plugs, `ez(hdmi_a) = 25 assumed + 15 = 40`, measured by `depth-mockup` before the shell is printed. A right-angle adapter is an explicit per-variant option only, and must appear in that variant's BOM |
| **D-09** | **Device retention is a captive 1/4"-20 *slotted* bolt through the far (−Y) wall into the device's *side* thread, held captive by a DIN 6799 E-clip in a groove on the shank behind the boss.** The floor through-bolt is withdrawn; the device lies flat on the floor in a ribbed cradle; the device is placed at zero yaw so the hole side faces −Y. | **User, 2026-09-08**, after physically verifying the hole is on a long side face | **fixed**; geometry §7.1, hole position unmeasured (M1/M2) |
| **D-10** | **PoE-splitter reservation defaults to a dongle-class 75 × 40 × 20 mm envelope** (`DONGLE-75x40x20`, `constants.scad:164`), `GAT-USBC` retained as a non-default alternative. | **User, 2026-09-08** | **fixed** in data; **placement blocked by R15** |
| **D-11** | **The `develop` branch is dropped.** `feature/*` → `main` by CI-green PR; releases are annotated `vX.Y.Z` tags on `main`. | **User, 2026-09-08** | **fixed**; `render.yml` already conforms, the docs do not (deviation D3) |

---

## 11. Constants this contract needs in `lib/mcc/constants.scad`

None of these exist yet (`constants.scad` currently stops at the panel-part table). They are listed
here so the shell milestone starts from a checklist rather than from invention. Every one carries a
citation or an `assumed` tag in the section noted.

| Constant | Value | Section |
|---|---|---|
| `MCC_T_PATCH` | 8.0 | §2.1 |
| `MCC_PANEL_BAND` | 3.0 | §2.2 |
| `MCC_PLATE_H` | 39.0 (derived: `MCC_D_FLANGE[1] + 2*MCC_D_FLANGE_EDGE_MARGIN`) | §2.2 |
| `MCC_PANEL_FRAME_MIN` | 10.0 | §2.3 |
| `MCC_PLATE_END_PAD` | 8.0 | §2.3 |
| `MCC_SLOTS_MAX` | 4 | §3 |
| `MCC_END_ZONE_MIN` | 20.0 `assumed` | §4 |
| `MCC_DEV_SIDE_ALLOW` | table: bnc 41, hdmi_a 40, rj45 27, usb 17, else 0 | §4 |
| `MCC_GAP_DEV` | 2.0 `assumed` | §4 |
| `MCC_GAP_FAR` | 6.0 `assumed` | §5 |
| `MCC_FAN_APERTURE_D` | 38.0 (derived: `H_int - 2*MCC_WALL`, capped) | §5 |
| `MCC_LID_SPAN_MAX` | 180.0 | §6 |
| `MCC_CRADLE_DECK` | derived per family: `z_conn_c - dev_h/2 - MCC_FLOOR_T` | §1 |
| `MCC_PAD_T` | 2.0 `assumed` | §1, §7.1 |
| `MCC_SIDE_BOLT_HEAD_D` / `_HEAD_H` | 10.0 / 4.5 `assumed` (M5) | §7.1 |
| `MCC_SIDE_BOLT_HEAD_REC_D` / `_REC_H` | 12.0 / 6.0 | §7.1 |
| `MCC_SIDE_BOLT_WEB_T` | 3.0 | §7.1 |
| `MCC_SIDE_BOLT_CLIP` | struct: groove_d 5.0, groove_w 0.8, od 11.0, t 0.7 — all `assumed` (M4) | §7.1 |
| `MCC_SIDE_BOLT_POCKET_D` / `_POCKET_H` | 13.0 / 8.0 | §7.1 |
| `MCC_SIDE_BOLT_ENGAGE` | 6.0 `assumed` (M2) | §7.1 |
| `MCC_SIDE_BOLT_BOSS_OD` | 20.0 | §7.1 |
| `MCC_SIDE_BOLT_PROUD` | 10.0 (derived) | §7.1 |
| `MCC_SIDE_BOLT_PAD_OD` / `_PAD_ID` | 18.0 / 8.0 `assumed` | §7.1 |
