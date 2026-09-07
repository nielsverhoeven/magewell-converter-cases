# Patch-wall layout contract

Status: **derived 2026-09-07 by solution-architect from the user's fixed topology decision.**
Owner: solution-architect. Referenced from `architecture.md` §14.
This file is normative for `shell.scad`, `panel.scad`, `cradle.scad`, `mounts.scad`, `vents.scad`.
Every number is either cited to `knowledge/**:line` / `lib/mcc/constants.scad:line`, or marked
`assumed` / `unknown`. Nothing here is invented silently.

---

## 0. The decision this implements

**Side-exit, one patch wall.** All external connectors sit in a single long side wall. The device
lies lengthwise; its end-face ports connect via short patch cables that turn 90° in the end
("corner") zones and run into the connector bay that spans the patch wall. The opposite long wall
and both end walls carry no connectors.

Superseded: the in-line topology of `architecture.md` §1 (compact ~244 × 72 × 45, plus ~260 × 80 × 45).

---

## 1. Coordinate frame

Origin at the centre of the case's **outer** bounding box in X and Y, and at the case **underside**
(the bed plane) in Z. All shell/panel/cradle/mounts/vents geometry is authored in this frame.

| Axis | Direction | Range |
|---|---|---|
| X | along the device length; +X = "end B" side | `[-L/2, +L/2]` |
| Y | +Y = **towards the patch wall** | `[-W/2, +W/2]` |
| Z | up; z=0 is the printed underside of the base | `[0, H]` |

Derived planes:

| Plane | Expression | Notes |
|---|---|---|
| Interior floor (top of floor) | `z = MCC_FLOOR_T` = 3.0 | `constants.scad:23` |
| Lid underside | `z = MCC_FLOOR_T + H_int` = 46.0 | |
| Far (-Y) wall inner face | `y = -W/2 + MCC_WALL` | `constants.scad:22` |
| Patch (+Y) wall inner face | `y = +W/2 - MCC_T_PATCH` | `MCC_T_PATCH = 8.0`, §3 |
| End wall inner faces | `x = ±(L/2 - MCC_WALL)` | |

### Device placement

```
y_dev_lo = -W/2 + MCC_WALL + MCC_GAP_FAR          // MCC_GAP_FAR = 6.0 (assumed, §5 airflow duct)
y_dev_hi = y_dev_lo + dev_w
y_dev_c  = y_dev_lo + dev_w/2
x_dev_lo = -L/2 + MCC_WALL + ez_neg               // ez = end zone, §4
x_dev_c  = x_dev_lo + dev_l/2
z_dev_lo = MCC_FLOOR_T + MCC_CRADLE_DECK          // MCC_CRADLE_DECK = 9.8, §7
```

**Cradle deck height is not free.** It is fixed by requiring the device's end-face port centreline
to coincide with the panel-connector centreline, so every patch cable runs level:

```
z_conn_c   = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H/2 = 3 + 3 + 18.5 = 24.5
z_dev_lo   = z_conn_c - dev_h/2                      = 24.5 - 11.7 = 12.8   (Plus/compact, dev_h 23.3-23.4)
MCC_CRADLE_DECK = z_dev_lo - MCC_FLOOR_T             = 9.8   (7.8 mm cradle deck + 2.0 mm compliant pad)
```

Compliant pad 2.0 mm: EPDM anti-slip pad, `knowledge/components/fasteners-and-hardware.md:186`
(⌀12 × 2.5 mm listed; 2.0 mm used as the compressed working thickness, `assumed`).

Consequence for the Plus family: `z_dev_hi` = 12.8 + 23.4 = 36.2, leaving **9.8 mm of plenum above
the device's top "MAGEWELL" grille** (`knowledge/magewell/housing-families.md:69`) — which
`architecture.md` §12 Q10 forbids sealing.

---

## 2. Panel plate aperture in the patch wall

### 2.1 Wall stack in Y at the panel band

| Layer | Thickness | Source |
|---|---|---|
| Proud sacrificial bezel (shell stands proud of the Neutrik flange face) | 3.0 `assumed` | `architecture.md:185-187` recessed-connector principle; flange front protrusion is `unknown` |
| Plate seat (rabbet depth for the 2.0 mm plate) | 2.0 | `MCC_PANEL_SEAT_T`, `constants.scad:71`; `knowledge/neutrik/d-series-cutout.md:90` NAHDMI-W max 2 mm |
| Structural rabbet lip (the shell material the plate lands on, pierced by the aperture) | 3.0 | `MCC_WALL`, `constants.scad:22` |
| **`MCC_T_PATCH` total** | **8.0** | |

The plate front face therefore sits 3.0 mm inside the shell's outer face; the Neutrik flange sits on
the plate front face. `mcc_bay_depth(part)` is measured **from the flange face**
(`knowledge/neutrik/placement-and-depth.md:5-8`), so 5.0 mm of it (plate + lip) is material and only
`mcc_bay_depth(part) - 5.0` has to be free interior.

### 2.2 Plate in Z

The plate height is set by the rear heat-set boss, not by the flange:

```
boss_od   = MCC_BOSS_MIN_RATIO * insert_od = 1.8 * 4.6 = 8.28      constants.scad:97, 91-95
MCC_PLATE_H >= 2 * (MCC_D_SCREW_PITCH[1]/2 + boss_od/2 + 2.0)
            = 2 * (12.0 + 4.14 + 2.0) = 36.28  ->  MCC_PLATE_H = 37.0
```

- 12.0 = screw offset, `knowledge/neutrik/d-series-cutout.md:47`
- 2.0 = minimum material from an insert bore wall to a part edge,
  `knowledge/design/fdm-rugged-enclosure-guidelines.md:127`

Resulting web from the 31 mm flange to the plate edge = **(37 − 31)/2 = 3.0 mm**, i.e. below the
4 mm figure in `architecture.md` §9's assert table. See decision **D-06** (§10) — the assert is
relaxed to 3.0 mm **in Z only**, because in Z the plate edge is captured full-length in the rabbet on
both sides, unlike the X-direction webs between adjacent flanges which also have to survive driver
access and the connectors' own screw loads.

```
MCC_PANEL_BAND = 3.0    // continuous shell band above and below the aperture (= MCC_WALL)
H_int = MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND = 3 + 37 + 3 = 43.0
H     = MCC_FLOOR_T + H_int + MCC_LID_T = 3 + 43 + 3 = 49.0
```

Aperture Z range (interior coords): `z ∈ [6.0, 43.0]`; plate Z range identical; connector centreline
`z = 24.5`.

**Tongue-and-groove polarity is now fixed by this:** the **base carries the tongue (raised), the lid
carries the groove.** If the base carried the groove it would be cut into the 3 mm band above the
aperture, which would leave <1 mm of material. Record as decision **D-07**.

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
`MCC_PLATE_END_PAD` regions (two per end, at `z = z_conn_c ± 13`), into bosses standing rearward off
the rabbet lip. Those X positions are always outboard of every flange, so the bosses never intrude
into a connector bay.

### 2.4 Panel-plate summary (one long plate per case)

| Property | Value |
|---|---|
| Thickness | 2.0 mm at every flange seat; ribbed to 3.0 mm elsewhere (`architecture.md:174-176`) |
| Height | 37.0 mm |
| Length | `L - 26` |
| Slots | up to 4, `pitch = (L - 68)/(n_slots - 1)`, asserted ≥ `MCC_D_PITCH_H` (32, `constants.scad:65`) |
| Parts dispatchable | `NE8FDP-B`, `NAHDMI-W-B`, `NAUSB-W-B`, `NBB75DFGB`, `DBA-BL-B` only |
| Print orientation | flat, face-down (`architecture.md:177-180`) |
| Rim | 3 mm ribbed rim around the whole outline |

---

## 3. Slot assignment — `mcc_slot_for_port()` semantics

Pure, deterministic, data-only. No per-device hand placement anywhere.

```
mcc_slot_for_port(dev, port_id) -> integer 1..n_slots
```

**Algorithm**

1. `ext = mcc_ports_external(dev)` (`ports.scad:56`). `n_slots = len(ext)`.
   Assert `n_slots <= MCC_SLOTS_MAX` (4) and `n_slots >= 1`.
2. Assert every `p` in `ext` has `mcc_port_face(p)` equal to `[-1,0,0]` or `[+1,0,0]`.
   The side-exit topology has no answer for a port on a long face or on the top/bottom; fail loudly
   rather than guess.
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

`rank` is read straight out of `MCC_PANEL_PARTS` (`constants.scad:234-241`), so it needs no new
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

## 4. End zones and the corner bend envelope

The end zone is the X gap between the device's end face and the inner face of that end wall. It has
to hold the device-side plug **and** the start of the 90° turn.

```
ez(end) = max over ports on that end of mcc_dev_side_allow(kind),  floored at MCC_END_ZONE_MIN = 20 (assumed)
```

`mcc_dev_side_allow(kind)` — all figures from `knowledge/components/cables.md:117-129`, which is the
"space needed between device port face and case wall" table:

| kind | allow (mm) | Source |
|---|---|---|
| `bnc` | 41 | `cables.md:123` — Belden 4855R min bend radius 40.6, verified |
| `hdmi_a` | 30 | `cables.md:122` — right-angle HDMI adapter, "<1 inch" = 25.4 verified, +5 margin |
| `rj45` | 27 | `cables.md:119` — 21.5 max plug + 5 margin |
| `usb_a`, `usb_b` | 17 | `cables.md:125` — USB-A 12 verified + 5; **USB-B is `unknown`, assumed equal** |
| `minidin8` | 0 | internal, not cabled (D-01) |
| `rotary16`, LEDs, SD slot | 0 | not cabled |

**The 30 mm HDMI figure is only valid with a right-angle HDMI adapter fitted at the device end.**
A straight HDMI plug's axial length is explicitly `unknown` (`cables.md:121`) and the cable would
then also need its own turn radius inside the end zone — pushing `ez` to a figure this knowledge base
cannot supply. Consequence: **a right-angle HDMI adapter becomes a required BOM line for every
device-side HDMI port** (see risk R13). The panel-side HDMI plug is unaffected — it turns in the
70 mm-deep bay, not in the corner.

### Does the connector bay run the full device length?

**Yes.** With `n_slots` up to 4 and the pitch above, the outer slot centres sit at `±(L/2 - 21)`,
which for every priority SKU is outboard of or within a few mm of the device's end faces, but slots 2
and 3 sit over the device's X range. So the bay's Y depth must be clear for the whole plate span, not
just in the corners:

```
d_bay_free = max over external ports of mcc_bay_depth(panel) - (MCC_WALL + MCC_PANEL_SEAT_T)
           = 75.65 - 5.0 = 70.65   (HDMI-bearing devices; 74.6 - 5 = 69.6 for SDI-only)
W = MCC_T_PATCH + d_bay_free + MCC_GAP_DEV + dev_w + MCC_GAP_FAR + MCC_WALL
  = 8 + d_bay_free + 2 + dev_w + 6 + 3
```

`MCC_GAP_DEV = 2.0` (`assumed`) is the clearance between the deepest plug envelope and the device's
patch-side flank. Because it is only 2 mm, **cradle locating ribs on the patch-side flank are
permitted only at X positions outboard of the plate aperture** (`|x| > plate_l/2 - 3`); everywhere
else the patch flank is located by the far-side ribs and the through-bolt alone.

The BNC lateral bend envelope (40.6 mm, `cables.md:63`) is satisfied inside the bay in the Y–Z plane:
70.65 mm of free Y ≫ 40.6 mm. It does **not** force BNC onto an end slot. New assert:
`d_bay_free >= max(mcc_bend_envelope(part))`.

---

## 5. Fan bay, PoE-splitter bay, vents

Reserved in every variant even when disabled (`architecture.md` §6 reservation rule).

### Fan bay — **+X end wall**

- Default part `NF-A4x10` 40 × 40 × 10, mounting pitch 32 × 32 (`knowledge/components/fans.md:15-17`).
- Frame mounts on the **inside** face of the +X end wall; the wall aperture is **⌀36 max**, centred at
  `(x = L/2, y = y_dev_c, z = z_conn_c)`. A full 40 mm aperture would leave only 1.5 mm of wall above
  and below in a 43 mm interior — below `MCC_WALL`. ⌀36 leaves 3.5 mm. `assumed`.
- 4 × NA-AV3 through-holes at ±16 mm (`fans.md:86-91`; the mounts are the correct type for a
  closed-corner 10 mm fan and decouple motor vibration from the shell).
- Exhaust direction +X: **away from the patch wall**, so the fan is never behind the cable bundle.
- Assert: the fan bay may not be placed on the +Y face, and may not intersect the end-zone cable
  envelope of the +X end.

### PoE-splitter bay — **−X end, transverse slab**

Functionally correct: the splitter's three connections (PoE in from etherCON, data out to the device
RJ45, 5 V out to the device USB-B and the fan — `knowledge/components/poe-splitters.md:170-192`) all
terminate at the device's data/power end, which the slot rule puts at the −X end for every encoder.
It is also the intake end, satisfying R6 ("put the splitter bay in the intake airflow").

```
splitter_env = MCC_SPLITTERS[part].size, oriented [x, y, z] = [d, l, w]  // long axis across the case
bay_x = [-L/2 + MCC_WALL, -L/2 + MCC_WALL + env.x]
bay_y = [-W/2 + MCC_WALL, -W/2 + MCC_WALL + env.y]
bay_z = [MCC_FLOOR_T, MCC_FLOOR_T + env.z]
```

**The default placeholder does not fit — this is blocking for `shell.scad`, see R11.** With
`GAT-USBC` (114 × 51 × 25, `poe-splitters.md:58`) laid transversely, the bay reaches `y = +38.8`,
while slot 1's etherCON plug envelope reaches inward to `y = +10.6`. Overlap ≈ 28 mm. Rotating or
stacking it fails on height (25 + 23.4 > the 43 mm interior) or width. The geometry must stay
data-driven (`mcc_splitter_envelope(part)` + a hard intersection assert) so that whichever part the
user picks either fits or fails loudly; the *default part* is a user decision.

For reference, a "dongle class" 75 × 40 × 20 envelope (the UCTRONICS U6114/U6115 form factor —
dimensions **`unknown`**, `poe-splitters.md:129-136, 211-215`) does fit: it reaches `y = -0.2`, clear
of slot 1's plug envelope at `y = +10.6`, and costs `max(0, 40 - ez_neg)` extra mm of L.

### Vents (`vents.scad`) — chimney slots

`knowledge/design/thermal-guidelines.md:164-185` and
`knowledge/design/fdm-rugged-enclosure-guidelines.md:190-199`.

| Band | Face | Z range (interior) | Role |
|---|---|---|---|
| Intake, low | −X end wall | `[5, 17]` | cool air in low; mesh filter pocket on the inside (`thermal-guidelines.md:193-195`, filter on the inlet) |
| Intake, low | −Y far long wall, full device length | `[5, 17]` | feeds the 6 mm `MCC_GAP_FAR` duct along the device's metal flank |
| Exhaust, high | −Y far long wall, +X half only | `[30, 42]` | passive outlet when `fan=false`; offset in X from the intake to avoid short-circuiting (`thermal-guidelines.md:176-179`) |
| Exhaust | +X end wall | fan aperture, ⌀36 | forced outlet when `fan=true` |
| **None** | **+Y patch wall** | — | **assert: no vent may be cut in the patch wall** |

`MCC_GAP_FAR = 6.0` exists precisely so the far-wall slots open into a real duct rather than onto the
device skin. Slot geometry: vertical slots through the wall thickness (no bridging,
`fdm-rugged-enclosure-guidelines.md:199`), slot width ≥ 1.2 mm `assumed` (nearest verified analogues
0.8 mm minimum wall and 1.0 mm lattice gap, `fdm-...:197`), web ≥ 1.6 mm, any bridged span ≤ 10 mm
(`fdm-...:111`).

---

## 6. Lid fasteners (R7 resolution)

```
n_fast = (L > MCC_LID_SPAN_MAX) ? 6 : 4        MCC_LID_SPAN_MAX = 180 (architect-derived, R7)
e      = 10.0                                  // fastener ring inset from the outer faces
```

- 4 corners at `(±(L/2 - e), ±(W/2 - e))`.
- If `n_fast == 6`: one extra at `(0, -(W/2 - e))` on the far wall, and one on the patch wall at
  `x = x_gap`, the widest inter-slot gap centre that clears the nearest flange edge by
  `≥ boss_od/2 + 2.0 = 6.15 mm`. **If no such gap exists, the patch-side mid fastener is replaced by
  an internal buttress rib** tying the patch wall to the lid tongue at that X. (HDMI Plus falls into
  the buttress case: its centre gap clears by only 5.75 mm. SDI Plus clears by 7.58 mm and gets the
  boss.)
- Corner bosses always clear the outer flange by 11.0 mm by construction (`(L/2-10) - (L/2-21)`).

Captive M3 knurled thumbscrews into M3 heat-set inserts (`MCC_INSERT_M3`, `constants.scad:91-95`);
boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:97`), ≥ 2 mm material to any edge
(`fdm-rugged-enclosure-guidelines.md:127`).

Family outcome: **compact → 4 (L ≤ 174.9); plus → 6 (L ≥ 180.5).**

---

## 7. Cradle and floor features

### Cradle

| Property | Value | Source |
|---|---|---|
| Deck top (device underside) | `z = 12.8` | §1, port-centreline alignment |
| Deck slab | 7.8 mm, ribbed/hollow, 3 mm top plate on 3 mm webs | `MCC_WALL` |
| Compliant pad | 2.0 mm EPDM, footprint ≥ 40 × 40 centred on the through-bolt | `fasteners-and-hardware.md:186` |
| Locating ribs | 3.0 mm thick × 9.0 mm tall | `fdm-...:68` rib height ≤ 3 × thickness |
| Far-flank ribs | discrete fins at ≥ 3 X positions; must not block the far-wall intake slots | §5 |
| Patch-flank ribs | **only** where `|x| > plate_l/2 - 3` | §4, `MCC_GAP_DEV` = 2 mm |
| End ribs | partial only — must clear every end-face port cutout and the plug envelope | §4 |
| Floor penetration | requested from `mounts.scad`; `cradle.scad` never cuts the floor | `architecture.md` §6 |

### Floor keep-out zones (`mcc_floor_keepout()`, plan view, case coords)

| Feature | Zone | Position rule |
|---|---|---|
| Device retention 1/4"-20 through-bolt | ⌀18 disc | `(x_bolt, y_dev_c)`; `x_bolt` = the device's own tripod-hole X, **per-SKU, `confidence:"assumed"`** (`housing-families.md:70-72` Plus undocumented, `:132` TX "estimated from image") |
| Case 1/4"-20 insert | ⌀20 disc | `(0, 0)` — case plan centre, default |
| VESA 75 × 75 | 4 × ⌀12 discs at `vesa_pos + (±37.5, ±37.5)` | `vesa_pos` defaults to `(0,0)`; **it is a shell parameter, shiftable in X per SKU** when the device's tripod-hole position collides |
| Fishtail M4 pair | reserve a 60 × 20 band centred on `vesa_pos` | hole pitch is **`unknown`** — `knowledge/magewell/accessories.md:26` gives only "2× M4×12 screws, 2× M4 nuts", no dimensions |
| Strap slots | 2 × (25 × 5) through-slots | `x = ±(L/2 - 25)`, `y = ±(W/2 - 12)` — `assumed` |
| Splitter tie-down | 2 × ⌀8 | inside `bay_x` × `bay_y` (§5) |
| Stacking profile | recess mirroring the lid's proud features | must clear all of the above |

Bolt length: 3 (floor) + 7.8 (deck) + 2 (pad) + ~6 engagement ≈ **20 mm 1/4"-20**, with a
nylon-insert or thread-locking provision (R8, vibration).

Minimum separation between any two floor features: 15 mm centre-to-centre for the ⌀12–⌀20 class
features, or `(r1 + r2 + 2.0)` where that is larger. `mounts.scad` asserts it.

**Blocking exception, see R12:** on the NDI decoders the 1/4"-20 hole is on the **top** face
(`knowledge/magewell/housing-families.md:139` — "Top, near Face A: SD-card slot … + 1/4"-20 hole"),
not the bottom. A floor through-bolt cannot reach it on those SKUs.

---

## 8. Resulting envelopes

`L = max( 2*MCC_WALL + ez_neg + dev_l + ez_pos , L_panel_min )` where
`L_panel_min = 2*MCC_WALL + 2*MCC_PANEL_FRAME_MIN + (n_slots-1)*MCC_D_PITCH_H + MCC_D_FLANGE[0] + 2*MCC_PLATE_END_PAD`
(= 172 for 4 slots, 140 for 3 slots).

| SKU | family | slots | ez −X / +X | L | W | H | pitch |
|---|---|---|---|---|---|---|---|
| HDMI Plus, HDMI 4K Plus | plus | 4 | 27 / 30 | 180.5 | 156.4 | 49.0 | 37.5 |
| SDI Plus, SDI 4K Plus, 12G SDI 4K Plus | plus | 4 | 27 / 41 | 191.5 | 155.3 | 49.0 | 41.2 |
| NDI to HDMI 4K | plus | 4 | 30 / 27 | 180.5 | 156.4 | 49.0 | 37.5 |
| HDMI TX | compact | 3 | 30 / 27 | 163.9 | 149.9 | 49.0 | 48.0 |
| SDI TX | compact | 3 | 41 / 27 | 174.9 | 148.8 | 49.0 | 53.5 |
| NDI to HDMI | compact | 4 | 30 / 27 | 172.0 | 149.9 | 49.0 | 34.7 |
| NDI to SDI | compact | 4 | 41 / 27 | 174.9 | 148.8 | 49.0 | 35.6 |
| NDI to AIO | compact | 4 | 41 / 27 | 174.9 | 149.9 | 49.0 | 35.6 |

**Family envelopes (the number to quote and to print):**

| Family | L × W × H | Lid fasteners | Bed margin (256) |
|---|---|---|---|
| **compact** | **174.9 × 149.9 × 49.0** | 4 | 81.1 / 106.1 |
| **plus** | **191.5 × 156.4 × 49.0** | 6 | 64.5 / 99.6 |

Both families' largest part (the base) is well inside `MCC_BUILD - MCC_BED_MARGIN` = 250
(`constants.scad:25-26`).

---

## 9. New Tier-1 asserts this topology requires

Add to `architecture.md` §9's minimum set. All are cheap, pure, and fire at render.

| # | Assertion | Rationale / source |
|---|---|---|
| T1-01 | every external port's `face` is `[±1,0,0]` | §3 step 2 — side-exit has no answer otherwise |
| T1-02 | `n_slots = len(mcc_ports_external(dev)) <= MCC_SLOTS_MAX (4)` | user decision, ≤ 4 D ports per model |
| T1-03 | `mcc_slot_for_port()` is a bijection onto `1..n_slots` | no two ports share a slot |
| T1-04 | every slot carries exactly one part (external port or `DBA-BL-B`) | §3 step 6 |
| T1-05 | no port has `panel == "MINIDIN8"` | enforces D-01; `MINIDIN8` stays in `MCC_PANEL_PARTS` as reserved-future data only |
| T1-06 | `pitch >= MCC_D_PITCH_H (32)` | `constants.scad:65`, `placement-and-depth.md:42` |
| T1-07 | `d_bay_free >= max(mcc_bay_depth(part)) - (MCC_WALL + MCC_PANEL_SEAT_T)` | §4 |
| T1-08 | `d_bay_free >= max(mcc_bend_envelope(part))` | lateral keep-out, `architecture.md:295-297` |
| T1-09 | `ez(end) >= max(mcc_dev_side_allow(kind))` over ports on that end | §4 |
| T1-10 | `plate_l <= L - 2*MCC_WALL - 2*MCC_PANEL_FRAME_MIN` | §2.3 |
| T1-11 | `plate_h >= 2*(MCC_D_SCREW_PITCH[1]/2 + boss_od/2 + 2.0)` | §2.2, `fdm-...:127` |
| T1-12 | flange-to-plate-edge web ≥ 4.0 in X, ≥ 3.0 in Z | §2.2, D-06 |
| T1-13 | every lid-fastener boss clears every flange edge by ≥ `boss_od/2 + 2.0` | §6 |
| T1-14 | `H_int >= MCC_CRADLE_DECK + dev_h + MCC_LID_CLEAR` | §1 |
| T1-15 | `H_int >= fan_aperture_d + 2*MCC_WALL` when a fan bay is reserved | §5 |
| T1-16 | `splitter_envelope ∩ connector_bay_envelope == ∅` | §5, R11 — this is the one that currently fails |
| T1-17 | `splitter_envelope ∩ mcc_floor_keepout() == ∅` | §6 floor rule |
| T1-18 | fan bay face `!= [0,+1,0]`, and `fan_bay ∩ end_zone_cable_envelope == ∅` | §5 |
| T1-19 | no vent slot intersects the patch wall | §5 |
| T1-20 | patch-flank cradle ribs only where `|x| > plate_l/2 - 3` | §4 |
| T1-21 | `L <= MCC_BUILD - MCC_BED_MARGIN` and `W <= MCC_BUILD - MCC_BED_MARGIN` for base and lid | `util.scad:42-44` |

---

## 10. Decisions recorded here

| ID | Decision | Origin |
|---|---|---|
| D-01 | Mini-DIN-8 PTZ/Tally stays internal, `panel:"none"` on every SKU. `mcc_panel_cutout()` dispatches Neutrik D parts + `DBA-BL-B` only. | **User, 2026-09-07** |
| D-02 | Side-exit, one patch wall (this document). | **User, 2026-09-07** |
| D-03 | HDMI loop-out is brought outside on the Plus encoders. | **User, 2026-09-07** |
| D-04 | 4 captive M3 thumbscrews baseline; **6 for lids over 180 mm span**. | User (4) + architect-derived (6). **Flagged for user veto.** |
| D-05 | Slot assignment is computed from `mcc_bend_envelope`/`mcc_plug_len`, not hand-placed. | Architect-derived |
| D-06 | Flange-to-plate-edge web relaxed from 4.0 to **3.0 mm in Z only**; unchanged at 4.0 in X. Buys 4 mm of case height. | Architect-derived. **Flagged for user veto.** |
| D-07 | Tongue on the **base**, groove in the **lid**. | Architect-derived (forced by D-06 / the 3 mm band above the aperture) |
| D-08 | Right-angle HDMI adapter is a required BOM line at every device-side HDMI port. | Architect-derived from `cables.md:121-122`. **Flagged for user veto.** |
