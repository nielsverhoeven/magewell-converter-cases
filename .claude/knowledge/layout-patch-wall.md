# Patch-wall layout contract

Status: **revision 5, 2026-09-08.** Rev 5 is the L2 architecture gate for
`docs/plans/2026-09-08-l2-first-case.md`: it rules on that plan's eight `PLAN-ASSUMPTION`s, **replaces
the §3 worked-results slot table (it was wrong on six of eight rows)**, adds §2.5 (the patch-wall
aperture is one rabbet + `n_slots` discrete windows), re-scopes T1-18, adds T1-23b/T1-32/T1-33/T1-34,
corrects the HDMI-bearing `W` figures to 159.85 / 166.35, and records ten further corrections. **All
rev-5 rulings are collected in §15** — read that first if you are implementing.

Rev 3 history follows. Derived 2026-09-07 by solution-architect from the user's fixed
topology decision; rev 2 recorded the user's decisions on the dongle-class PoE splitter (D-10),
**side-bolt device retention** (D-09), D-04 accepted, **D-06 vetoed** (case height 51 mm) and
**D-08 vetoed** (straight-plug end zones). **Rev 3 records the last two user decisions and their
consequences:**

- **D-12 (R15 accepted).** The reserved PoE-splitter bay and the −X cable allowance **sum**:
  `ez_neg = 27 + 20 = 47`. Every `L` grows 20 mm → compact 194.9, plus 211.5 → **both** families
  cross the 180 mm span threshold, so **6 lid thumbscrews on compact as well**.
- **D-13 (R18 → flush, not proud).** No lug outside the far wall. `MCC_GAP_FAR` 6 → **16**,
  `MCC_SIDE_BOLT_PROUD` 10 → **0**. Every `W` grows 10 mm → compact 159.9, plus 166.4 — which is
  exactly rev 2's printed bbox, so **the bed footprint is unchanged by D-13**; the 10 mm simply moved
  from outside the wall to inside it, where it becomes a 16 mm airflow duct.
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
**Since D-13 nothing protrudes from any wall**, so `bbox_W == W` and `bbox_L == L`. The
`bbox_W = W + MCC_SIDE_BOLT_PROUD` expression is retained in §8 and in T1-21 only because
`MCC_SIDE_BOLT_PROUD` remains a *parameter* (a future variant may deliberately go proud); it evaluates
to `W` on every current variant.

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
| Far (−Y) wall outer face | `y = -W/2` | **flat everywhere — D-13, no lug** |
| Device far flank (= pad face + `MCC_PAD_T`) | `y = -W/2 + MCC_WALL + MCC_GAP_FAR` | `= -W/2 + 19`, §7.1 |
| Patch (+Y) wall inner face | `y = +W/2 - MCC_T_PATCH` | `MCC_T_PATCH = 8.0`, §2.1 |
| End wall inner faces | `x = ±(L/2 - MCC_WALL)` | |

### Device placement — zero yaw, by construction

```
y_dev_lo = -W/2 + MCC_WALL + MCC_GAP_FAR          // MCC_GAP_FAR = 16.0 (DERIVED, §7.1 / D-13)
y_dev_hi = y_dev_lo + dev_w
y_dev_c  = y_dev_lo + dev_w/2
x_dev_lo = -L/2 + MCC_WALL + ez_neg               // ez = end zone, §4;  ez_neg = 47 since D-12
x_dev_c  = x_dev_lo + dev_l/2
z_dev_lo = MCC_FLOOR_T + MCC_CRADLE_DECK          // MCC_CRADLE_DECK = 10.8, §7
```

**`MCC_GAP_FAR` is derived, not chosen (D-13).** It is whatever the captive bolt stack needs:

```
boss_len    = head_rec_h + web_t + pocket_h                    = 6 + 3 + 8 = 17.0     §7.1
MCC_GAP_FAR = max(MCC_GAP_FAR_DUCT_MIN, boss_len + MCC_PAD_T - MCC_WALL)
            = max(6.0, 17.0 + 2.0 - 3.0)                       = 16.0
```

`MCC_GAP_FAR_DUCT_MIN = 6.0` (`assumed`) is the old airflow-duct floor and is now non-binding. The
duct is a *consequence* of the fastener, not its justification — do not "optimise" the gap back to
6 mm, and if M5 shows a taller screw head, this formula grows `MCC_GAP_FAR` and therefore `W`.

**The device is not centred in X.** Since D-12, `ez_neg = 47 ≠ ez_pos = 40/41`, so
`x_dev_c = (ez_neg − ez_pos)/2 = +3.5` (HDMI-ended SKUs) or **+3.0** (BNC-ended SKUs) — see §8. Every
feature derived from `x_dev_c` (the side-bolt keep-out, the cradle, the fan's X-facing envelope)
inherits that offset. In particular it is why the far-wall mid-span lid fastener always has to move
(§6).

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
`MCC_PLATE_END_PAD` regions (two per end), into bosses standing rearward off
the rabbet lip. Those X positions are always outboard of every flange, so the bosses never intrude
into a connector bay.

> **Correction, rev 5 (2026-09-08).** Rev 1–3 said the retaining tabs sit at `z = z_conn_c ± 14` and
> implied an X of `±(plate_l/2 − MCC_PLATE_END_PAD/2)`. **Neither matches the plate that is already
> implemented.** `mcc_panel_plate()` (`lib/mcc/panel.scad:102-104`) cuts its four M3 clearance holes
> at `(±(w/2 − rim_w/2), ±(h/2 − rim_w/2))` = **`(±(plate_l/2 − 3), ±16.5)`** at the default
> `rim_w = 6`. The plate is the physical part; **the plate wins.** `shell.scad` must place its four
> heat-set bosses from the *same expression*, not from the numbers in this paragraph. To make drift
> impossible, that expression is published once as a pure function
> **`mcc_panel_fixing_pos(plate_size, rim_w)` in `layout.scad` (L1)**, `use`d by both `panel.scad`
> and `shell.scad`; `panel.scad` stops hardcoding it. (An L1 file is the right home — both consumers
> are L2, so the edge stays downward.)

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
| Length | `L - 26` — **rev 3: 167.9–168.9 compact, 184.5–185.5 plus** (was 147.9 / 164.5–165.5; D-12 added 20 mm) |
| Slots | up to 4, `pitch = (L - 68)/(n_slots - 1)`, asserted ≥ `MCC_D_PITCH_H` (32, `constants.scad:65`) |
| Parts dispatchable | `NE8FDP-B`, `NAHDMI-W-B`, `NAUSB-W-B`, `NBB75DFGB`, `DBA-BL-B` only |
| Print orientation | flat, face-down (`architecture.md` §5) |
| Rim | 3 mm ribbed rim around the whole outline (`mcc_panel_plate()` default `rim_t = MCC_WALL`, `rim_w = 6`) |

### 2.5 The patch-wall aperture — ONE rabbet, `n_slots` DISCRETE WINDOWS (new, rev 5, 2026-09-08)

Rev 1–4 said "the patch wall carries a full-length rectangular aperture with a rabbet" without saying
whether the *hole through the wall* is one opening or several. It cannot be one:

- `architecture.md` §5 is a hard shell rule — "the aperture roof is a ≤45° self-supporting chamfer,
  never a flat bridge … no unsupported horizontal span over 10 mm anywhere in the shell." A single
  161.9 mm-wide void 39 mm tall has no legal roof: a 45° chamfer converging from both top corners
  needs ~81 mm of rise and only 39 mm exists.
- §6's `n_fast = 6` mid-span lid fastener sits at `x_gap`, a *slot-gap centre* on the patch wall. Its
  boss runs floor-to-lid and needs solid wall material at that X across the whole aperture band.
- T1-13 ("every lid-fastener boss clears every flange edge by ≥ `boss_od/2 + 2`") only means anything
  if the boss is embedded in wall material *between* flanges.

**Normative:**

| Element | Ruling |
|---|---|
| Panel plate | **ONE** continuous `plate_l × MCC_PLATE_H` part. Do **not** split it into `n_slots` plates (§5 of `architecture.md`, §2.4 here). |
| Rabbet | **ONE** continuous pocket in the wall's outer layers, spanning the whole plate footprint + `MCC_CLR_SLIDE` per side. **Stepped, not flat-bottomed:** `MCC_PANEL_BEZEL_T (3) + rim_t (3) = 6 mm` deep over the plate's `rim_w` border ring, `MCC_PANEL_BEZEL_T (3) + MCC_PANEL_SEAT_T (2) = 5 mm` deep over the field. Rev 1–4's uniform 5 mm pocket is wrong — `mcc_panel_plate()`'s rim is 3 mm thick, not 2. |
| Structural lip behind the plate | 3 mm behind the field, **2 mm behind the rim ring**. Assert `residual lip >= 2.0`. |
| Windows | `n_slots` **discrete openings through the 3 mm structural lip only**, one per `slot_x(i)`, with solid lip material in the ~8 mm inter-slot webs and out to `MCC_PANEL_FRAME_MIN`. **Not one long opening, and NOT one rabbet per window.** |
| Window shape | The **minimal** clearance envelope, not a 34 × 39 rectangle: `⌀(mcc_cutout_d(part) + 2·MCC_CLR_SLIDE)` for the connector body at `z = z_conn_c`, **unioned with** two `⌀(boss_od + 2·MCC_CLR_SLIDE)` circles at the `mcc_neutrik_d_bosses()` positions `(∓9.5, ±12)`. Smaller windows leave more lip material, which both stiffens the wall and better supports the plate's 2 mm flange seat. |
| Window roof | Self-supporting (teardrop crown, or a ≤45° gable ending in a ≤10 mm flat bridge). **T1-34** asserts both the clearance and the ≤10 mm span. |
| Rabbet-pocket roof | A 5–6 mm-deep horizontal ledge, supported along its whole back edge by the lip — an overhang, not a bridge, and inside the 10 mm rule. A ≤45° relief chamfer is optional. |

**Why a plain rectangle + 45° top chamfer does not work** (this is the trap the first plan fell into):
with the window top at `z = 45` and a ≤45° roof, the clear width at height `z` is at most
`bridge + 2·(45 − z)`, **independent of the window's nominal width**. The plate's rear bosses reach
`z = z_conn_c + 12 + boss_od/2 = 41.64`, where that gives at most `10 + 6.72 = 16.72 mm` — but the
boss pair spans `2·(9.5 + 4.14) = 27.28 mm`. No rectangle width fixes it; the two local boss reliefs
are the fix.

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
3. Partition: `A = {p : face.x < 0}` (**block A = the case's −X end**), `B = {p : face.x > 0}`
   (**block B = the case's +X end**).
   > **Naming warning (rev 5, 2026-09-08).** "Block A / block B" here mean *the sign of `face.x` in the
   > case frame* and nothing else. They are **not** Magewell's "Face A / Face B" from
   > `knowledge/magewell/models/*.md`. On the encoders Magewell's Face A happens to be the −X
   > (data/power) end, so the two readings coincide; **on the four decoders Magewell's "Face A" is the
   > *video* end, which the device files author on `face [+1,0,0]`, i.e. block B.** Conflating the two
   > is what produced the wrong worked-results table that stood here until rev 5 — see §15 ruling 8.
4. Slot block allocation: **A takes slots `1 .. len(A)`; B takes slots `n_slots-len(B)+1 .. n_slots`.**
   Ports therefore never cross the case; a port on the −X end always lands in the −X half of the wall.
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

**Worked results for the priority SKUs — CORRECTED, rev 5 (2026-09-08).** Every row below is the
mechanical output of steps 1–6 above applied to the *actual* `face`/`pos`/`panel` fields in
`lib/mcc/devices/*.scad` (re-derived port by port by the architect, 2026-09-08). The rev-3 table that
stood here was wrong on **six of eight rows** and is superseded; see §15 ruling 8.

| SKU | slot 1 (−X) | slot 2 | slot 3 | slot 4 (+X) |
|---|---|---|---|---|
| HDMI Plus / HDMI 4K Plus | NE8FDP-B (etherCON) | NAUSB-W-B (USB-B 5 V) | NAHDMI-W-B (HDMI loop-OUT) | NAHDMI-W-B (HDMI IN) |
| SDI Plus / SDI 4K Plus / 12G SDI 4K Plus | NE8FDP-B | NAUSB-W-B | NBB75DFGB (SDI OUT) | NBB75DFGB (SDI IN) |
| HDMI TX | NE8FDP-B | NAUSB-W-B | NAHDMI-W-B (HDMI IN) | — (3 slots) |
| SDI TX | NE8FDP-B | NAUSB-W-B | NBB75DFGB (SDI IN) | — (3 slots) |
| **NDI to HDMI** | **NE8FDP-B (etherCON)** | **NAUSB-W-B (USB-B 5 V)** | **NAUSB-W-B (USB-A host)** | **NAHDMI-W-B (HDMI OUT)** |
| NDI to SDI | NE8FDP-B | NAUSB-W-B (USB-B) | NAUSB-W-B (USB-A host) | NBB75DFGB (SDI OUT) |
| NDI to AIO | NE8FDP-B | NAUSB-W-B (USB-B) | NAHDMI-W-B (HDMI OUT) | NBB75DFGB (SDI OUT) |
| NDI to HDMI 4K (Plus chassis) | NE8FDP-B | NAUSB-W-B (USB-B) | NAUSB-W-B (USB-A host) | NAHDMI-W-B (HDMI OUT) |

Cross-checks that confirm the corrected table is the intended design, not just the literal algorithm:

- **etherCON is slot 1 (−X) on every SKU.** §5 places the reserved PoE-splitter bay at the −X end
  precisely because "the splitter's three connections all terminate at the device's data/power end".
  Under the rev-3 table the decoders' etherCON sat at slot 4, i.e. at the opposite end of the case
  from the splitter that has to be fed from it — self-contradictory.
- **Every port reaches its slot with one 90° L, never an S.** That is the whole rationale in
  "Why 'stiffest outermost'" below; a −X port routed to a +X slot crosses the case.
- The two Plus encoder rows are unchanged in *parts*; only the HDMI Plus slot-3/4 identities swap
  (the `hdmi_in`/`hdmi_out` tie on `[bend, plug_len]` is broken by `pos[0]` ascending, so `hdmi_in`
  at `pos[0] = −22` sorts first and takes the outermost slot 4).

Note the Mini-DIN-8 PTZ/Tally port does **not** appear: `panel:"none"` on every SKU (decision D-01).

**No device file changes.** The four decoder files are correct as authored — Magewell's Face A really
is their video end. The defect was in this table, not in the data.

---

## 4. End zones and the corner bend envelope — **straight plugs (D-08 vetoed)**

The end zone is the X gap between the device's end face and the inner face of that end wall. It has
to hold the device-side plug **and** the start of the 90° turn.

```
ez_cable(end) = max over ports on that end of mcc_dev_side_allow(kind),
                floored at MCC_END_ZONE_MIN = 20 (assumed)

ez(end)       = ez_cable(end)
              + (end == -X && splitter bay reserved ? MCC_END_ZONE_NEG_EXTRA_SPLITTER : 0)
```

**The reserved-bay term ADDS; it is not `max`ed in (D-12, user decision 2026-09-08 — resolves R15).**
The device's own −X plugs need their 27 mm whether or not a splitter is fitted; with a splitter fitted
they simply terminate at the splitter instead of at the plate. Sharing the end zone is impossible in
both Y (the slab spans the full width) and Z (the slab spans `z ∈ [3,43]`, straight through the
`z ≈ 19.5–31.5` band the patch leads run in). Hence:

```
MCC_END_ZONE_NEG_EXTRA_SPLITTER = mcc_splitter_envelope(MCC_SPLITTER_DEFAULT)[2]   // on-edge X extent
                                = 20.0    for DONGLE-75x40x20 (constants.scad:164, `assumed`)
ez_neg = 27 + 20 = 47      ez_pos = 40 (HDMI) or 41 (BNC)
```

**Derived, not typed.** `MCC_END_ZONE_NEG_EXTRA_SPLITTER` reads `size[2]` out of `MCC_SPLITTERS`
(on edge: `size[2]`→X, `size[0]`→Y, `size[1]`→Z, §5), so measurement M3 propagates into `L`
automatically. Hard-typing `20.0` is a deviation.

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

**Yes.** With `n_slots` up to 4 and the pitch above, the outer slot **centres** sit at
`±span/2 = ±(L/2 - 34)` and their outer flange **edges** at `±(L/2 - 21)` (rev 2 conflated the two;
the `L/2 - 21` figure is the edge, and it is what §6's corner-boss clearance is derived from). At the
rev-3 lengths that puts the outer slots clearly outboard of the device's end faces — e.g. HDMI Plus:
slot centres ±71.25 vs. a device spanning `x ∈ [−55.25, +62.25]` — while slots 2 and 3 still sit over
the device's X range. So the bay's Y depth must be clear for the whole plate span, not just in the
corners:

```
d_bay_free = max over external ports of mcc_bay_depth(panel) - (MCC_WALL + MCC_PANEL_SEAT_T)
           = 75.65 - 5.0 = 70.65   (HDMI-bearing devices; 74.6 - 5 = 69.6 for BNC-without-HDMI)
W = MCC_T_PATCH + d_bay_free + MCC_GAP_DEV + dev_w + MCC_GAP_FAR + MCC_WALL
  = 8 + d_bay_free + 2 + dev_w + 16 + 3          // MCC_GAP_FAR = 16 since D-13
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
  `(x = L/2, y = fan_y, z = z_conn_c = 25.5)`. Derivation: `H_int - 2*MCC_WALL = 45 - 6 = 39`, so
  ⌀38 leaves exactly 3.5 mm of wall above and below. (Was ⌀36 at `H_int = 43`; the D-06 veto bought
  2 mm of aperture, i.e. measurably more free area.) `assumed`.
- **`fan_y` is a shell parameter, default `y_dev_c` (new, rev 3 — R20).** At `MCC_GAP_FAR = 16` the
  far-wall duct is a real 16 × 45 = 720 mm² channel, but the ⌀38 aperture centred on `y_dev_c`
  (`y = −30.85` on the plus family) spans `y ∈ [−49.85, −11.85]` and does **not** reach the duct mouth
  (`y ∈ [−80.2, −64.2]`). So the fan as drawn pulls from the plenum over/around the device, not
  through the duct. Both choices are defensible — device-centred gives even flow over the top grille
  (which §12 Q10 forbids sealing), duct-aligned gives a genuine through-path. **Parameterise now,
  decide by measurement**; do not silently move the default. Either way the aperture stays legal:
  at the default it clears the far wall's inner face by 30.35 mm and the patch wall by far more.
- 4 × NA-AV3 through-holes at ±16 mm (`fans.md:86-91`; the correct mount type for a closed-corner
  10 mm fan, and it decouples motor vibration from the shell).
- Exhaust direction +X: **away from the patch wall**, so the fan is never behind the cable bundle.
- Assert: the fan bay may not be placed on the +Y face, and may not intersect the end-zone cable
  envelope of the +X end.

### PoE-splitter bay — **−X end, on edge** (D-10; placement **RESOLVED by D-12**)

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
env    = MCC_SPLITTERS[part].size = [75, 40, 20]        // L, W, H — on edge: H->X, L->Y, W->Z
bay_x  = [-L/2 + MCC_WALL,          -L/2 + MCC_WALL + env[2]]   // = -L/2 + [3, 23]
bay_y  = [-W/2 + MCC_WALL,          -W/2 + MCC_WALL + env[0]]   // = -W/2 + [3, 78]
bay_z  = [MCC_FLOOR_T,              MCC_FLOOR_T + env[1]]       // = [3, 43]
```

- **Connector-bay check (T1-16) passes with room to spare.** `bay_y` reaches `y = −5.2` (plus family
  at `W = 166.4`); slot 1's etherCON plug envelope reaches inward only to `y = +15.6`
  (`W/2 − MCC_T_PATCH − mcc_bay_depth("NE8FDP-B") = 83.2 − 8 − 59.6`; the conservative convention of
  rev 2, which charges the full bay depth against free interior). **20.8 mm clear, up from 10.8 mm** —
  D-13's +10 mm of `W` doubled this margin.
- **End-zone check (T1-28) now passes by construction (D-12).** `ez_neg = 47`: the slab takes the
  outer 20 mm (`x ∈ −L/2 + [3, 23]`) and the device's −X patch leads keep their full 27 mm
  (`x ∈ −L/2 + [23, 50]`). The slab does not intrude on the cable band in X at all, so the Z overlap
  no longer matters.
- **The splitter does not touch the far-wall duct.** `bay_x` ends at `−L/2 + 23`, while the device —
  and therefore the duct that runs along its flank — starts at `x_dev_lo = −L/2 + 50`. 27 mm clear.
- Secondary, unchanged: the on-edge slab masks the −Y half of the −X end wall (it spans
  `y ∈ [−W/2+3, −W/2+78]`, i.e. up to `y = −5.2`), so that wall's intake vent band must sit in the
  **+Y half** only. At `W = 166.4` that leaves a ~78 mm-wide band, ~10 mm wider than at rev 2.
- Tie-downs: 2 × ⌀8 in the floor inside `bay_x × bay_y`, owned by `mounts.scad` (§7 floor rule).

### Vents (`vents.scad`) — chimney slots

`knowledge/design/thermal-guidelines.md:164-185` and
`knowledge/design/fdm-rugged-enclosure-guidelines.md:190-199`.

| Band | Face | Z range (case coords) | Role |
|---|---|---|---|
| Intake, low | −X end wall, **+Y half only** | **`[5, 23]`** (`MCC_VENT_INTAKE_BAND_H = 18.0`, rev 5) | cool air in low; mesh filter pocket on the inside (`thermal-guidelines.md:193-195`). +Y half because the splitter slab masks the −Y half |
| Intake, low | −Y far long wall, full device length | **`[5, 23]`** (rev 5 — 12 and 15 mm both fail T1-30) | feeds the **16 mm** `MCC_GAP_FAR` duct along the device's metal flank |
| Exhaust, high | −Y far long wall, +X half only, **and outboard of the side-bolt keep-out** | `[32, 44]` | passive outlet when `fan=false`; offset in X from the intake to avoid short-circuiting (`thermal-guidelines.md:176-179`) |
| Exhaust | +X end wall | fan aperture, ⌀38 at `y = fan_y` | forced outlet when `fan=true` |
| **None** | **+Y patch wall** | — | **assert: no vent may be cut in the patch wall** (T1-19) |
| **None** | **inside the side-bolt keep-out** | ⌀24 disc at `(x_bolt, z_bolt)` **∪ a 7 mm-wide strip from `z = MCC_FLOOR_T` up to `z_bolt`**, on the far wall | **assert T1-23.** The boss dams the duct at that X and its support web (§7.1, D-13) runs from the boss down to the floor, so a slot anywhere in that footprint opens into solid material |
| **None** | **inside the far-wall mid-span lid-fastener boss footprint** | a `(boss_od + 2·2.0)`-wide strip at `x = x_far_mid`, full height | **new, rev 5 — assert T1-23b.** With `n_fast = 6` the far-wall mid fastener sits at `x_far_mid = −12.64` on NDI to HDMI, i.e. *inside* the intake band's X run, and its boss + wall gusset run floor-to-lid. Slots cut there open into solid material, exactly as at the side bolt. Its lost area must also come off T1-30's net total |

**The duct is now 16 mm, and that changes what the vents are for.** `MCC_GAP_FAR = 6.0` used to exist
*for* the duct; since D-13 it is 16 mm because the fastener needs it, and the duct is the by-product.
Consequences for `vents.scad`:

- **The duct is no longer the restriction — the slots are.** Free areas at the rev-3 geometry: fan
  aperture ⌀38 = **1134 mm²**; duct cross-section 16 × 45 = **720 mm²** (was 270); total internal
  cross-section normal to X minus the device ≈ **5400 mm²**. The duct is one of several parallel paths
  and the case never starves the fan. But the far-wall intake band as specified (12 mm tall, 1.2 mm
  slot / 1.6 mm web, over the device length) yields only ≈ **590 mm²**, plus ≈ 400 mm² from the −X end
  wall's +Y half ≈ **990 mm² total — below the fan aperture**, and
  `knowledge/design/thermal-guidelines.md:104-109` says vent free area should be "comfortably larger
  than the fan's inlet/outlet duct area". **Widen the intake band in Z and/or raise
  the slot:web ratio until T1-30 passes.** Widening the duct further buys nothing.
- **Rev-5 resolution: `MCC_VENT_INTAKE_BAND_H = 18.0`, band `z ∈ [5, 23]` on both intake faces.**
  Worked at the NDI to HDMI geometry (far-wall run = `dev_l` = 100.9, −X end-wall run = `W/2 − MCC_WALL`
  = 76.925, duty = `1.2/(1.2+1.6)` = 0.4286): gross free area **1219 mm²**, minus the side-bolt
  keep-out (7 mm strip over the full band + the disc's overhang into `z ∈ [14.0, 23]`) ≈ **78 mm²**,
  minus the far-wall mid-span lid-fastener boss + gusset ≈ **64 mm²** → **≈ 1077 … 1141 mm²** net,
  against the ⌀38 fan aperture's **1134 mm²**. It is *marginal*, so **T1-30 must be evaluated on the
  NET area after every keep-out subtraction, and the module's own assert is the authority** — the
  hand figures above are illustrative. **12 mm fails outright (≈ 990 mm²) and 15 mm also fails once
  the keep-outs are subtracted (≈ 1084 mm²); do not use either.** If 18 mm still misses at render,
  the next lever is the slot:web ratio (slot 1.2 → 1.6 at web 1.6 raises duty 0.4286 → 0.50), not a
  deeper duct and not a taller band (23 mm is already close to the exhaust band's `z = 32` floor).
- Slot geometry unchanged: vertical slots through the wall thickness (no bridging,
  `fdm-rugged-enclosure-guidelines.md:199`), slot width ≥ 1.2 mm `assumed` (nearest verified analogues
  0.8 mm minimum wall and 1.0 mm lattice gap, `fdm-...:197`), web ≥ 1.6 mm, any bridged span ≤ 10 mm
  (`fdm-...:111`).
- **The side-bolt boss still dams the duct locally, and now more of it.** The boss reaches 14 mm into
  the 16 mm duct (rev 2: 4 mm into 6 mm) and its support web fills the remainder down to the floor, so
  at `x = x_bolt` the duct is effectively closed. `vents.scad` must place slots on *both* sides of it
  in X — the duct is two chimneys, not one — and the exhaust band's "+X half only" rule must be
  evaluated **against the boss position**, not blindly: with the `pos [0,0]` placeholder
  `x_bolt = +3.0…+3.5` sits inside the +X half, so the exhaust band's inner edge must start at
  `x ≥ x_bolt + keepout_d/2 = ~15.5`, not at `x = 0`.
- **The keep-out is no longer a plain disc.** `mcc_side_bolt_keepout()` returns the ⌀24 disc **∪** the
  support web's wall footprint (web thickness 3 + 2 × 2 mm clearance = 7 mm wide, from `z = 3` to the
  disc). See §7.1.

---

## 6. Lid fasteners (R7 resolution — **D-04 accepted by the user 2026-09-08**)

```
n_fast = (L > MCC_LID_SPAN_MAX) ? 6 : 4        MCC_LID_SPAN_MAX = 180
e      = 10.0                                  // fastener ring inset from the outer faces
```

**The 180 mm threshold stays the general rule** even though, after D-12, *both* current families are
over it. It is cheap, it is the right rule for a future short variant, and a `n_fast` that is a
constant `6` would silently break the first SKU that comes in under 180 mm.

- 4 corners at `(±(L/2 - e), ±(W/2 - e))`.
- If `n_fast == 6`: one extra on the far wall at `(x_far_mid, -(W/2 - e))`, and one on the patch wall
  at `x = x_gap`, the widest inter-slot gap centre that clears the nearest flange edge by
  `≥ boss_od/2 + 2.0 = 6.15 mm`. **If no such gap exists, the patch-side mid fastener is replaced by
  an internal buttress rib** tying the patch wall to the lid tongue at that X.
- **Tie-break for `x_gap` (new, rev 3 — required for the geometry goldens).** With evenly-spread slots
  every inter-slot gap is the same width, so "widest" does not decide. Rule: among the qualifying gap
  centres pick the one **nearest `x = 0`**; if two tie (an even number of gaps, i.e. an odd slot
  count), pick the **−X** one. Deterministic and stable under a slot-count change.
- **Clearances at the rev-3 pitches** (gap centre to nearest flange edge = `pitch/2 − 13`):

  | Family / slots | pitch | clearance | vs. the 6.15 mm minimum |
  |---|---|---|---|
  | plus, 4 slots (HDMI / SDI) | 47.50 / 47.83 | 10.75 / 10.92 | pass, 4.6 mm spare |
  | compact, 4 slots (NDI to HDMI / SDI / AIO) | 41.97 / 42.30 | **7.98 / 8.15** | pass, **1.83 mm spare — the tightest in the repo** |
  | compact, 3 slots (HDMI TX / SDI TX) | 62.95 / 63.45 | 18.48 / 18.73 | pass; `x_gap = −31.48 / −31.73` (off-centre by `pitch/2`, per the tie-break above) |

  So **the buttress fallback is still unused on every priority SKU** — but it is now only 1.8 mm away
  on the compact 4-slot SKUs, where rev 2 did not need a mid-span fastener at all. Keep the rule and
  keep T1-13.
- **The far-wall mid fastener always moves.** `x_far_mid` starts at `0` but must clear the side-bolt
  keep-out (T1-27), and since D-12 the device is offset (`x_dev_c = +3.0…+3.5`, §1), so with the
  `pos [0,0]` placeholder the keep-out is centred at `x ≈ +3.25` with radius `keepout_d/2 = 12`, while
  the boss radius is `8.28/2 = 4.14` — required separation 16.14 mm, actual 3.25 mm. **It collides on
  every current SKU.** The *fastener* moves, not the bolt (the bolt position is dictated by the
  device): candidates `x_bolt ± 16.14`, subject to `|x| ≤ L/2 − e − boss_od/2`; if both are legal pick
  the one **nearer `x = 0`** (for HDMI Plus: −12.64 rather than +19.64). Deterministic, and it must be
  the same rule in `shell.scad` and in the golden.
- Corner bosses always clear the outer flange by 11.0 mm by construction (`(L/2-10) - (L/2-21)`).

Captive M3 knurled thumbscrews into M3 heat-set inserts (`MCC_INSERT_M3`, `constants.scad:96`);
boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:102`), ≥ 2 mm material to any edge
(`fdm-rugged-enclosure-guidelines.md:127`).

Family outcome after D-12: **compact → 6 (L = 193.9–194.9); plus → 6 (L = 210.5–211.5).** Both
families are over the 180 mm threshold, so **every current SKU gets 6 thumbscrews** — a BOM change
(+2 M3 knurled thumbscrews, +2 M3 heat-set inserts per case) and a print-time change on the five
compact SKUs, and an accepted part of D-12's price. The threshold rule itself is unchanged.

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
| Far-flank ribs | discrete fins at ≥ 3 X positions; must not block the far-wall intake slots, **must not intersect the side-bolt keep-out**, and **must carry a flow relief** (see below) | §5, §7.1 |
| Patch-flank ribs | **only** where `|x| > plate_l/2 - 3` | §4, `MCC_GAP_DEV` = 2 mm |
| End ribs | partial only — must clear every end-face port cutout and the plug envelope | §4 |
| Anti-rotation | **carried entirely by the ribs.** One horizontal bolt is one point of restraint; ribs are structural, not cosmetic | R8 |
| Floor penetration | **none.** `cradle.scad` never cuts the floor | `architecture.md` §6 |

**Far-flank ribs must not dam the duct (new, rev 3 — a D-13 consequence).** A far-flank rib has to
reach the device's flank to locate it, so at `MCC_GAP_FAR = 16` each rib now spans the *whole* duct
(rev 2: 6 mm). Three ribs would chop the chimney into four dead segments. Rule: **below the device's
underside plane (`z < z_dev_lo`) each far-flank rib must be open**, and the opening must be a ≤45°
self-supporting arch or chamfered notch — not a flat bridge — with ≤ 3 mm legs at each end, so the
clear span stays ≤ 10 mm (`fdm-rugged-enclosure-guidelines.md:111`, `architecture.md` §5).
**Not acceptable:** three or more solid full-depth ribs. This is the only cradle
change D-13 forces; the ribs themselves print fine (their footprint sits on the floor, so they are
self-supporting vertical fins, not cantilevers).

> **Rev 5 correction (2026-09-08).** Rev 3 offered an alternative — "exactly two far-flank ribs
> placed at X positions outboard of the intake band" — which is **struck**: the intake band runs the
> *full device length* (§5), so "outboard of the intake band" is also outboard of the device, where a
> rib cannot reach the flank it exists to locate. The open-notch ≥3-rib design is the only sanctioned
> one.
>
> **Normative placement rule (replaces "≥ 3 X positions", which was not deterministic enough for the
> geometry goldens):**
> ```
> c        = MCC_SIDE_BOLT_KEEPOUT_D/2 + MCC_CRADLE_RIB_T/2 + 2.0        // = 15.5 at rev-5 defaults
> band     = [x_dev_lo + 8, x_dev_hi - 8]
> excl     = [x_bolt - c, x_bolt + c]
> segments = band \ excl                                                 // 0, 1 or 2 closed intervals
> ribs     = the two endpoints of each surviving segment, plus that segment's midpoint
>            if the segment is longer than 40 mm
> ```
> Assert `len(ribs) >= 3` and, per rib, `abs(x_rib - x_bolt) >= c`. For NDI to HDMI
> (`x_dev_lo = -46.95`, `x_dev_hi = 53.95`, `x_bolt = +3.5`) this yields **4 ribs at
> `x = -38.95, -12.0, +19.0, +45.95`**. If a future SKU loses a whole segment the assert fires —
> that is the correct failure mode; escalate rather than relaxing `c`.

### 7.1 Side-bolt boss — normative geometry (D-09, **flush per D-13**)

The one genuinely new mechanism in revision 2; **revision 3 makes it flush.** Everything below is
authored **along the local +Z axis** to match `fasteners.scad`'s existing convention (a boss stands
with its base at Z = 0 and grows toward +Z); `shell.scad` rotates it onto the far wall's outward
normal. **`Z = 0` is now the far wall's OUTER SURFACE** (it was "the outermost surface of the lug";
with `MCC_SIDE_BOLT_PROUD = 0` the two coincide), and +Z runs into the case.

**What D-13 changed and what it did not.** Every number in the axial stack below is **unchanged** —
because `proud + MCC_WALL + MCC_GAP_FAR = 19 mm` either way (0 + 3 + 16 = 10 + 3 + 6). What changed is
*where the material sits*:

| | rev 2 (proud 10) | rev 3 (flush, D-13) |
|---|---|---|
| Wall occupies local Z | `[10, 13]` | **`[0, 3]`** |
| Head recess `[0, 6]` ⌀12 | inside the lug, outside the wall | **pierces the whole wall**, then 3 mm beyond it |
| Retaining web `[6, 9]` ⌀6.6 | inside the lug | **3 mm inside the case**, carried by the boss |
| Boss material inside the duct | 4 mm (`[13, 17]`) | **14 mm (`[3, 17]`)** |
| Boss material outside the wall | 10 mm | **none** |
| Duct depth at that X | 6 mm, 2 mm clear behind the boss | 16 mm, 2 mm clear behind the boss |

So the boss is now a **local thickening on the inside of the far wall**: a ⌀20 (`MCC_SIDE_BOLT_BOSS_OD`)
cylinder running from the wall's inner face (`Z = 3`) to the pad face (`Z = 17`), coaxial with the
bolt, unioned into the wall. The wall itself carries **no material on the bolt axis** — it is fully
pierced by the ⌀12 head recess — so the boss and its support web are the entire load path (see R19).

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

**Axial stack** (Z from the far wall's outer surface, all `assumed` unless cited)

| Z range | Feature | ⌀ | Note |
|---|---|---|---|
| `[0, 3.0]` | *(the far wall itself)* | — | pierced by the head recess over its full thickness |
| `[0, 6.0]` | Slotted head recess | **12.0** | depth = head height + 1.5, so the head sits **≥ 1 mm below the outer surface** (no proud metal, drop rule). Head face lands at `Z = 1.5`, i.e. 1.5 mm inside the wall — a flat blade reaches it easily through a ⌀12 counterbore |
| `[6.0, 9.0]` | Retaining web, shank clearance bore | **6.6** | `MCC_TRIPOD_CLR_D`, `constants.scad:111`. `web_t = 3.0` — this shoulder is what the E-clip lands on. **Now 3 mm inboard of the wall**, carried by the boss |
| `[9.0, 17.0]` | E-clip clearance pocket | **13.0** | `pocket_h = 8.0` = engagement 6.0 + clip thickness 0.7 + 1.3 margin |
| `[17.0, 19.0]` | Compliant pad (EPDM annulus, OD 18 / ID 8) | — | bears on the device flank; provides the preload |
| `19.0` | Device side face | — | `= MCC_SIDE_BOLT_PROUD + MCC_WALL + MCC_GAP_FAR` = **0 + 3 + 16** (was 10 + 3 + 6 — same total) |
| `[19.0, 25.05]` | Thread engagement into the device | — | `e = 6.0`, **`assumed` — the device's thread depth is unmeasured** (M2) |

**Print orientation note (pre-existing, restated because the developer will hit it).** All four bores
are **horizontal** in the print orientation (base floor-down), so each has a droop at the top of the
circle. Only the ⌀6.6 shank bore is functional: model it with `$fn = 64`, `circum = true`
(`architecture.md` §3), and either teardrop it or add ~+0.3 mm (`assumed`, calibrate on
`tolerance-ladder`). The ⌀12 recess and ⌀13 pocket are clearance features and can droop freely.

**Derived quantities** (all of these are formulas, not magic numbers, and belong in `constants.scad`)

```
boss_len            = head_rec_h + web_t + pocket_h            = 6.0 + 3.0 + 8.0 = 17.0

// D-13: solve for the GAP first, then the proud amount falls out as zero.
MCC_GAP_FAR         = max(MCC_GAP_FAR_DUCT_MIN, boss_len + MCC_PAD_T - MCC_WALL)
                    = max(6.0, 17.0 + 2.0 - 3.0)              = 16.0     <- was 6.0
MCC_SIDE_BOLT_PROUD = max(0, boss_len + MCC_PAD_T - (MCC_WALL + MCC_GAP_FAR))
                    = max(0, 17.0 + 2.0 - 19.0)               =  0.0     <- was 10.0

screw_len_under_head= MCC_SIDE_BOLT_PROUD + MCC_WALL + MCC_GAP_FAR + e - head_rec_h
                    = 0 + 3 + 16 + 6 - 6                      = 19.0  -> stock 3/4" = 19.05 (unchanged)
groove_pos          = web_t + e + 1.0                         = 10.0  (from under the head, unchanged)
clip_travel         = groove_pos - web_t                      = 7.0   >= e + 0.5 = 6.5   OK
boss_od             = pocket_d + 2 * 3.5                      = 20.0  (unchanged)
web_support_t       = MCC_WALL                                =  3.0  (new, D-13 — see below)
keepout_d           = boss_od + 2 * 2.0                       = 24.0  (unchanged)
keepout_strip_w     = web_support_t + 2 * 2.0                 =  7.0  (new, D-13)
```

The two formulas are evaluated in that order and are not circular: `MCC_GAP_FAR` is solved from the
stack, then `MCC_SIDE_BOLT_PROUD` is solved from `MCC_GAP_FAR` and comes out exactly `0`. The `max(0,
…)` and the `proud` parameter both stay so a future variant can deliberately go proud, and so that a
larger measured head (M5) fails loudly through T1-26 rather than silently producing a lug.

**Zero margin is intentional but tight.** `boss_len + MCC_PAD_T = 19.0` exactly equals
`MCC_WALL + MCC_GAP_FAR`. T1-26 uses `<=`, so it passes — but there is **0.0 mm of slack**: any
increase in head height, web thickness or clip pocket depth pushes `MCC_GAP_FAR` (and `W`) up. That is
the intended failure mode; do not "fix" it by shaving the head recess.

**Screw and clip**

| Item | Spec | Confidence |
|---|---|---|
| Screw | 1/4"-20 UNC, **slotted** (flat-blade — deliberate: a tool everyone has, and it discourages power drivers), 19.05 mm (3/4") under the head, stainless; overall ≈ 23.5 mm | `assumed` |
| Head ⌀ / height | **10.0 / 4.5 mm assumed.** Nearest metric standard is ISO 1207 / DIN 84 cheese head **M6** (dk 10.0, k 3.9, slot n 1.6); the inch equivalents (fillister dk ≈ 9.53, k ≈ 4.37; pan dk ≈ 12.5, k ≈ 3.56) bracket it. **Not sourced in `knowledge/**`** — measure the screw actually bought (M5) and re-derive `head_rec_h`, which re-derives `MCC_SIDE_BOLT_PROUD` | `assumed` |
| Retaining groove | on the shank, **10.0 mm below the under-head face**; ⌀ and width per the clip below. On a fully-threaded stock screw this lands in the threads — acceptable, but see R16 | `assumed` |
| E-clip | **DIN 6799, nominal size 5** — the size normally listed for a 6–7 mm shaft. Groove ⌀ **5.0 mm**, groove width **0.8 mm**, clip OD ≈ **11.0 mm**, thickness **0.7 mm**. **NOT VERIFIED: DIN 6799 is not in `knowledge/**` and these figures were not read from the standard.** Confirm before ordering (M4) | `assumed` |
| Washer | stainless ⌀12–14 × 1 mm on the recess floor under the head, to stop the ASA web being scrubbed on every device swap | `assumed` (R19) |
| Pad | 2.0 mm EPDM annulus OD 18 / ID 8. Nearest sourced part is the ⌀12 × 2.5 mm EPDM pad, `fasteners-and-hardware.md:186` — a die-cut washer may be needed instead | `assumed` |

**Why the far wall moved out instead of growing a lug (D-13, user decision 2026-09-08).** The captive
stack needs 17 mm between the case's outer surface and the pad face, and at `MCC_GAP_FAR = 6` only
`3 + 6 − 2 = 7 mm` existed. Rev 2 took the 10 mm shortfall **locally, outward** as a proud lug. The
user chose instead to take it **globally, inward**: widen `MCC_GAP_FAR` to 16 so the whole stack fits
inside the wall. Rationale, recorded because it is a judgement call that will be re-asked:

- Nothing proud anywhere means the drop rule (`architecture.md` §5, recessed connectors + sacrificial
  bezel) holds on all six faces; a ⌀20 lug on the one previously-clean wall was a stress riser and a
  strap/stacking obstruction.
- **The printed bounding box is identical either way** (rev 2's `bbox_W` was already `W + 10`), so
  nothing was paid in bed margin. The cost is ASA in the floor and lid, and print time (R14).
- The 10 mm became a 16 mm airflow duct — a real, if secondary, gain (see §5 and R20).

**Blend and support rule (this is the part that got harder).** The boss is now a horizontal ⌀20
cylinder cantilevered 14 mm off a vertical wall, printed floor-down: its lower half is an unsupported
overhang. A pure ≤45° conical blend would need a **⌀48 root** at the wall, which collides with the
vent band, the cradle far-flank ribs and the lid-fastener boss — so that is **not** the solution here.
Normative:

- **A central vertical support web**: `web_support_t = MCC_WALL = 3.0 mm` thick in X, in the plane
  `x = x_bolt`, spanning the boss's full Y extent (wall inner face `Z = 3` → pad face `Z = 17`), and
  running in Z from the interior floor (`z = MCC_FLOOR_T`) up to the boss's underside
  (`z = z_bolt − boss_od/2`). Unioned into wall, floor and boss. It is a plain vertical fin sitting on
  the floor, therefore fully self-supporting.
- With that web, the largest unsupported horizontal step under the boss is
  `(boss_od − web_support_t)/2 = 8.5 mm`, inside the shell rule "no unsupported horizontal span over
  10 mm" (`architecture.md` §5, `fdm-rugged-enclosure-guidelines.md:111`).
- A ≤45° fillet at the boss/wall junction and at the web/floor junction is still required — for stress
  and for bed adhesion, no longer for support.
- **Airflow cost ≈ zero:** the boss already dams 14 of the 16 mm of duct at that X, so the web takes
  what was left. **Vent cost is real:** see the keep-out below.
- Fallback, if a developer would rather not carry the web: local slicer support under the boss (the
  base prints with its top open, so the boss is reachable for removal). Do not mix the two on one
  variant, and record the choice here if it changes.

**Keep-outs owned by this feature** (`mcc_side_bolt_keepout()`, published by `shell.scad`)

- ⌀24 disc on the far wall at `(x_bolt, z_bolt)`, **∪ a `keepout_strip_w = 7 mm` wide strip at
  `x = x_bolt` running from `z = MCC_FLOOR_T` up to the disc** (the support web's wall footprint) —
  **no vent slot inside either** (T1-23). A slot in the strip would open into the web, i.e. into solid
  material.
- The same union swept through the duct — **no cradle far-flank rib, no lid-fastener boss, no splitter
  bay inside it** (T1-27).
- The pad footprint must land wholly on the device's side face:
  `pad_od ≤ dev_h − 2·|v| − 2` and `|u| + pad_od/2 ≤ dev_l/2 − 2` (T1-24). With `pad_od = 18` and
  `dev_h = 23.4` this allows only `|v| ≤ 1.7 mm` — see R17, this is the tight one.

**Module contract** (to be added to `lib/mcc/fasteners.scad`; specification only — no code here)

```
mcc_captive_side_bolt_boss(proud, wall_t, gap_far, pad_t, od, blend_a,
                           support_web_t, support_web_z0)                // ADDITIVE
mcc_captive_side_bolt_cut (proud, wall_t, gap_far, pad_t,
                           head_d, head_h, head_rec_h, shank_d,
                           web_t, clip_pocket_d, pocket_h, engage)       // SUBTRACTIVE
```

**Parameter defaults that changed in rev 3 — for the developer implementing these now:**

| Parameter | rev 2 default | **rev 3 default** |
|---|---|---|
| `proud` | 10.0 | **0.0** (`MCC_SIDE_BOLT_PROUD`) |
| `gap_far` | 6.0 | **16.0** (`MCC_GAP_FAR`) |
| `support_web_t` | — (did not exist) | **3.0** (`MCC_WALL`) — new, required by D-13 |
| `support_web_z0` | — | **`MCC_FLOOR_T` = 3.0**, the interior floor the web stands on |

`support_web_*` are additive-only; `mcc_captive_side_bolt_cut()` is unchanged by D-13 (every figure in
its stack is the same). Keep `proud` a parameter rather than folding the zero in — a future variant
may want it, and the `max(0, …)` derivation is what makes the M5 measurement fail loudly.

Both share the local frame above. The cut runs from `Z = -EPS` through to `Z = proud + wall_t +
gap_far + EPS` so it also pierces the wall proper (at `proud = 0` the head recess alone already
pierces it); the caller `difference()`s it after unioning the boss into the shell. Asserts live in the
modules (see T1-24 … T1-27, T1-31) so a bad `pos` fails at render, not at the printer. All
`$fn = 64`, `circum = true` on every bore that must pass a real part (`architecture.md` §3 `$fn`
policy).

### Floor keep-out zones (`mcc_floor_keepout()`, plan view, case coords)

**The device-retention through-bolt row is deleted (D-09).** What remains:

| Feature | Zone | Position rule |
|---|---|---|
| Case 1/4"-20 **insert** (case → tripod/cheeseplate) | ⌀20 disc | `(0, 0)` — case plan centre, default. Note this is a *threaded* feature, not the ⌀6.6 clearance boss `mcc_tripod_boss()` currently models (deviation D2) |
| VESA 75 × 75 | 4 × ⌀12 discs at `vesa_pos + (±37.5, ±37.5)` | `vesa_pos` defaults to `(0,0)`; a shell parameter, shiftable per SKU |
| Fishtail M4 pair | reserve a 60 × 20 band centred on `vesa_pos` | hole pitch is **`unknown`** — `knowledge/magewell/accessories.md:26` gives only "2× M4×12 screws, 2× M4 nuts". Derive from `knowledge/magewell/assets/magewell-fishtail-bracket.stl` (M7) |
| Strap slots | 4 × (25 × 5) through-slots (2 straps) | `y = ±(W/2 - 12)`; `x = +(L/2 - 25)` on the +X pair and, on the −X pair, **`x = min(-(L/2 - 25), bay_x[1] + 25/2 + 2)`** — see the rev-5 correction below — `assumed` |
| Splitter tie-down | `mcc_splitter_tiedown()` — 2 × (4 × 1.5) zip-tie slots, **on-edge orientation** | inside `bay_x × bay_y` (§5). **Rev-5 correction: not "2 × ⌀8"** — a ⌀8 hole is not a tie-down. `mounts.scad` calls the module; it must not hand-roll holes |
| **Side-bolt support web footprint** | `MCC_SIDE_BOLT_SUPPORT_WEB_T × (MCC_WALL + MCC_GAP_FAR − MCC_SIDE_BOLT_PAD_T − MCC_WALL)` = **3 × 14 mm** rectangle at `x = x_bolt`, running from the far wall's *inner* face inward | **new (D-13), figure corrected rev 5** (rev 3 said "3 × 20", which is neither the boss OD nor its length). The boss ends at the pad face, `y = −W/2 + 17`; the web's floor footprint is `y ∈ [−W/2 + 3, −W/2 + 17]` |
| **Far-wall mid-span lid-fastener boss** | ⌀`MCC_BOSS_MIN_RATIO·insert_od` + its wall gusset, at `(x_far_mid, −(W/2 − e))` | **new, rev 5.** It stands *inside the far-wall duct*, in the intake band's X range, so it is both a floor feature **and** a far-wall vent keep-out (see §5 / T1-23b) |
| Stacking profile | recess mirroring the lid's proud features | must clear all of the above. **No longer has to dodge the side-bolt lug** — D-13 removed it; the far wall is flat |

Minimum separation between any two floor features: 15 mm centre-to-centre for the ⌀12–⌀20 class
features, or `(r1 + r2 + 2.0)` where that is larger. `mounts.scad` asserts it.

> **Rev-5 corrections to this table (2026-09-08), all found while validating the first full case:**
>
> 1. **The −X strap-slot pair collides with the reserved splitter bay (T1-17 fails as specified).**
>    At `L = 193.9` the rev-3 rule puts a slot centred at `x = −71.95` spanning `x ∈ [−84.45, −59.45]`
>    and `y = −67.925`, straight through `bay_x × bay_y = [−93.95, −73.95] × [−76.925, −1.925]`. The
>    **reserved bay wins** (§6 reservation rule); the strap slot is the movable feature. Deterministic
>    fix, above: the −X pair slides inboard to `x = bay_x[1] + slot_l/2 + 2` when the nominal position
>    would intersect the bay — `x = −59.45` for NDI to HDMI. Assert it rather than hand-typing it.
> 2. **`mcc_floor_keepout()` is NOT a nullary function.** Strap slots, the splitter bay and the
>    side-bolt web all depend on `L`, `W` and `x_bolt`. Its signature is `mcc_floor_keepout(dev, cfg)`.
> 3. **The case's own 1/4"-20 insert is a stack-height constraint, not just a plan-view keep-out.**
>    It is installed from the case underside, so its boss occupies `z ∈ [0, MCC_INSERT_1_4_20.len + 1]`
>    = `[0, 13.7]`, and the device underside is at `z_dev_lo = MCC_FLOOR_T + MCC_CRADLE_DECK` = **13.85**
>    (compact) / **13.8** (plus). The boss therefore has 0.15 / 0.10 mm of clearance and must be
>    unioned into the cradle deck's hollow. **New assert T1-32** (§9). Anything that shortens the
>    cradle deck breaks it silently — hence the assert.
> 4. **VESA 75 × 75 cannot be cut as M4 clearance through-holes on the compact family.** Two of the
>    four holes at `vesa_pos + (±37.5, ±37.5)` land inside the device/cradle footprint
>    (`x ∈ [−46.95, 53.95]`, `y ∈ [−60.925, −0.725]`), and no `vesa_pos` shift avoids it — a 75 mm
>    square cannot dodge a 100.9 × 60.2 device on a 193.9 × 159.85 floor. **Ruling: the VESA M4
>    features are blind M4 heat-set inserts in floor bosses that are unioned into the cradle deck's
>    hollow, not through-holes** (there is 13.85 mm of floor+deck stack, ample for a 5.7 mm insert).
>    `mounts.scad` owns the bosses; `cradle.scad` must leave room for them. If the user would rather
>    drop VESA on the compact family, that is a user decision — escalate, do not improvise.

---

## 8. Resulting envelopes

```
L = max( 2*MCC_WALL + ez_neg + dev_l + ez_pos , L_panel_min )
    ez_neg = ez_cable(-X) + MCC_END_ZONE_NEG_EXTRA_SPLITTER = 27 + 20 = 47   // D-12, §4
L_panel_min = 2*MCC_WALL + 2*MCC_PANEL_FRAME_MIN + (n_slots-1)*MCC_D_PITCH_H
              + MCC_D_FLANGE[0] + 2*MCC_PLATE_END_PAD
            = 164 for 4 slots, 132 for 3 slots        (corrected — see the note in §2.3)
W = MCC_T_PATCH + d_bay_free + MCC_GAP_DEV + dev_w + MCC_GAP_FAR + MCC_WALL
    MCC_GAP_FAR = 16.0                                                       // D-13, §7.1
H = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND + MCC_LID_T = 51.0
bbox_W = W + MCC_SIDE_BOLT_PROUD = W                   // D-13: nothing proud, so bbox == envelope
```

The device branch governs `L` on every priority SKU; `L_panel_min` is never binding.

**Per SKU** (`ez_neg` = the −X / data-power end incl. the splitter reservation, `ez_pos` = the
+X / video end, at zero yaw):

| SKU | family | slots | ez_neg | ez_pos | L | W | H | pitch | x_dev_c |
|---|---|---|---|---|---|---|---|---|---|
| HDMI Plus, HDMI 4K Plus | plus | 4 | 47 | 40 | 210.5 | 166.35 | 51.0 | 47.50 | +3.50 |
| SDI Plus, SDI 4K Plus, 12G SDI 4K Plus | plus | 4 | 47 | 41 | 211.5 | 165.30 | 51.0 | 47.83 | +3.00 |
| NDI to HDMI 4K | plus | 4 | 47 | 40 | 210.5 | 166.35 | 51.0 | 47.50 | +3.50 |
| HDMI TX | compact | 3 | 47 | 40 | 193.9 | 159.85 | 51.0 | 62.95 | +3.50 |
| SDI TX | compact | 3 | 47 | 41 | 194.9 | 158.80 | 51.0 | 63.45 | +3.00 |
| NDI to HDMI | compact | 4 | 47 | 40 | 193.9 | 159.85 | 51.0 | 41.97 | +3.50 |
| NDI to SDI | compact | 4 | 47 | 41 | 194.9 | 158.80 | 51.0 | 42.30 | +3.00 |
| NDI to AIO | compact | 4 | 47 | 41 | 194.9 | 159.85 | 51.0 | 42.30 | +3.00 |

(`W` differs by 1.05 mm within a family purely from `d_bay_free`: 70.65 for HDMI-bearing SKUs vs 69.60
for BNC-without-HDMI. `x_dev_c = (ez_neg − ez_pos)/2` — the device is off-centre since D-12.)

> **Correction, rev 5 (2026-09-08).** The HDMI-bearing `W` figures were 159.9 / 166.4 in rev 3. That
> came from `architecture.md` §1 rounding `mcc_bay_depth("NAHDMI-W-B")` to "75.7"; the exact value
> from `constants.scad` is `40.65 + 35 = 75.65`, so `d_bay_free = 70.65` and `W = 159.85 / 166.35`.
> **The code must compute 159.85/166.35 — do not round it back to match a doc.** ~0.05 mm,
> non-structural, but the golden files will carry the exact number.

**Family envelopes (the number to quote and to print) — rev 5:**

| Family | L × W × H = printed bbox | Lid fasteners | Bed margin vs 256 | vs the 250 assert limit |
|---|---|---|---|---|
| **compact** | **194.9 × 159.85 × 51.0** | **6** | 61.1 / 96.15 | 55.1 / 90.15 |
| **plus** | **211.5 × 166.35 × 51.0** | 6 | 44.5 / 89.65 | 38.5 / 83.65 |

Both families' largest part (the base) is inside `MCC_BUILD - MCC_BED_MARGIN` = 250
(`constants.scad:25-26`, asserted by `util.scad:41-43`) with ≥ 38.5 mm to spare. **The lid has the
same L × W footprint and is a separate part**, so it clears the same limit — but base and lid cannot
share a plate (2 × 166.4 = 332.8 > 250 in either orientation): **two build plates per case.** The
panel plate (`L − 26` × 39, printed flat) *does* fit alongside the base in the remaining
250 − 166.4 = 83.6 mm strip.

**Where the growth came from, vs. rev 2:**

| | rev 2 | rev 3 | cause |
|---|---|---|---|
| compact | 174.9 × 149.9 (bbox 159.9) | **194.9 × 159.9** | `L` +20 (D-12), `W` +10 (D-13) |
| plus | 191.5 × 156.4 (bbox 166.4) | **211.5 × 166.4** | same |
| compact lid fasteners | 4 | **6** | `L` crossed 180 mm (D-12 + D-04) |
| printed bbox in Y | already `W + 10` | `W` | unchanged in absolute terms (D-13) |

`H = 51.0` is unchanged by both decisions — it is set entirely by the panel plate (§2.2).

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
| T1-09 | `ez(end) >= max(mcc_dev_side_allow(kind))` over ports on that end, **plus the reserved-bay term on that end** (`ez_neg >= ez_cable(-X) + MCC_END_ZONE_NEG_EXTRA_SPLITTER`) | §4, **D-12** — the allowances sum, they are not `max`ed |
| T1-10 | `plate_l <= L - 2*MCC_WALL - 2*MCC_PANEL_FRAME_MIN` | §2.3 |
| T1-11 | `MCC_PLATE_H >= 2*(MCC_D_SCREW_PITCH[1]/2 + boss_od/2 + 2.0)` | §2.2, `fdm-...:127` |
| T1-12 | flange-to-plate-edge web **≥ 4.0 in X and ≥ 4.0 in Z** | §2.2 — **D-06 vetoed**, the Z exception is withdrawn |
| T1-13 | every lid-fastener boss clears every flange edge by ≥ `boss_od/2 + 2.0` | §6 |
| T1-14 | `H_int >= MCC_CRADLE_DECK + dev_h + MCC_LID_CLEAR` | §1 |
| T1-15 | `H_int >= fan_aperture_d + 2*MCC_WALL` when a fan bay is reserved | §5 (45 ≥ 38 + 6) |
| T1-16 | `splitter_envelope ∩ connector_bay_envelope == ∅` | §5, R11 — **now passes** with the dongle default |
| T1-17 | `splitter_envelope ∩ mcc_floor_keepout() == ∅` | §7 floor rule |
| T1-18 | ~~fan bay face `!= [0,+1,0]`, and `fan_bay ∩ end_zone_cable_envelope == ∅`~~ **RE-SCOPED rev 5 (2026-09-08): the second clause is unsatisfiable as written and is replaced.** New form: (a) fan bay face `!= [0,+1,0]`; (b) `fan_envelope ∩ device_envelope == ∅` and `fan_envelope ∩ splitter_bay == ∅`; (c) **axial cable clearance:** `x_dev_hi + axial_plug_len(worst +X port) <= L/2 − MCC_WALL − fan_envelope_depth` | §5. **Why:** `ez_pos = 40` is the *whole* +X end zone and the fan envelope (frame 10 + intake clearance 5 = 15) occupies its outer 15 mm, so `fan_bay ∩ end_zone` is non-empty on **every** SKU. But the two genuinely coexist: `ez_pos` = 25 mm of *axial* plug + 15 mm of *lateral* bend allowance, and the bend is spent in Y (turning toward the patch wall), not in X. Clause (c) is the real constraint. On NDI to HDMI: `53.95 + 25 = 78.95 <= 96.95 − 3 − 15 = 78.95` — **passes with exactly zero slack**, which is precisely why it must be an assert. **BNC-ended SKUs have no sourced axial plug-body term at all** (`ez(bnc) = 41` is a pure bend radius, §4) — clause (c) cannot be evaluated honestly there; use `mcc_plug_len("NBB75DFGB")` as the interim axial term and record it as `assumed` pending M6 |
| T1-19 | no vent slot intersects the patch wall | §5 |
| T1-20 | patch-flank cradle ribs only where `|x| > plate_l/2 - 3` | §4 |
| T1-21 | `L <= MCC_BUILD - MCC_BED_MARGIN` and `bbox_W <= MCC_BUILD - MCC_BED_MARGIN` for base and lid | `util.scad:41-43`. `bbox_W = W + MCC_SIDE_BOLT_PROUD`, which **since D-13 equals `W`** — keep the expression, the parameter still exists |
| **T1-22** | exactly one port per device has `kind == "tripod_1_4_20"`, and its `face == [0,-1,0]` | §1 yaw rule, `architecture.md` §7 `side_bolt` convention. **Replaces the floor-bolt asserts** |
| **T1-23** | `mcc_side_bolt_keepout() ∩ vent_slots == ∅`, where the keep-out is the ⌀24 disc **∪ the 7 mm support-web strip down to `z = MCC_FLOOR_T`** | §5, §7.1 — **extended by D-13.** Also catches the exhaust band, whose "+X half only" rule would otherwise put slots straight onto the boss at `x_bolt ≈ +3` |
| **T1-24** | bolt axis lands inside the device's −Y face: `pad_od <= dev_h - 2*abs(v) - 2` and `abs(u) + pad_od/2 <= dev_l/2 - 2` | §7.1, R17 — the assert that catches a bad measurement. **Unchanged by D-13**: the pad still lands in the same place on the device |
| **T1-25** | head fully recessed below the wall's **outer** surface: `head_rec_h >= head_h + 1.0` | §7.1, drop rule. **At `proud = 0` the reference surface is the wall's outer face**, so this is now what guarantees nothing protrudes; at rev-3 defaults `6.0 >= 4.5 + 1.0`, 0.5 mm spare |
| **T1-26** | clip pocket lies wholly inside the boss and the clip can travel far enough: `head_rec_h + web_t + pocket_h <= proud + MCC_WALL + MCC_GAP_FAR - pad_t` **and** `groove_pos - web_t >= engage + 0.5` | §7.1 — if this fails, the device cannot be removed without dropping the screw inside the case. **At rev-3 defaults the first term is an EQUALITY (17 ≤ 17): zero slack, by design.** A taller measured head (M5) must be answered by raising `MCC_GAP_FAR`, not by shaving the recess |
| **T1-27** | `mcc_side_bolt_keepout()` intersects no cradle far-flank rib, no lid-fastener boss, and not the splitter bay; **and the support web's floor footprint (3 × 20 at `x_bolt`) is in `mcc_floor_keepout()` and overlaps no other floor feature** | §5, §6, §7, §7.1 — **extended by D-13.** With the `pos [0,0]` placeholder this *always* fires on the far-wall mid-span fastener, which is why §6 gives that fastener a deterministic displacement rule |
| **T1-28** | `splitter_envelope ∩ end_zone_cable_envelope == ∅` | §5 — **now PASSES by construction** since D-12 makes `ez_neg = ez_cable + splitter_x`. Keep it: it is what catches a future SKU whose −X allowance changes |
| **T1-29** | flush rule (D-13): `MCC_GAP_FAR >= boss_len + MCC_PAD_T - MCC_WALL` **and** `MCC_SIDE_BOLT_PROUD == 0` unless the variant sets `proud` explicitly and the exception is recorded in §10 | §7.1 — stops a future edit from silently re-introducing a proud lug, and stops anyone "optimising" `MCC_GAP_FAR` back to 6 |
| **T1-30** | when a fan bay is reserved: total intake vent free area `>= MCC_VENT_AREA_RATIO * (π/4) * MCC_FAN_APERTURE_D²`, `MCC_VENT_AREA_RATIO = 1.0` `assumed` | `knowledge/design/thermal-guidelines.md:104-109` ("vent free area comfortably larger than the fan's inlet/outlet duct area"). **New, and it currently FAILS at the band geometry in §5** (≈ 990 vs 1134 mm²) — the fix is a taller intake band, not a deeper duct (R20). Note deliberately: the assert is on **slot area**, not duct depth; the duct is one of several parallel paths and never the restriction |
| **T1-31** | printability of the internal boss: `(MCC_SIDE_BOLT_BOSS_OD - support_web_t)/2 <= 10.0` | §7.1, `architecture.md` §5 "no unsupported horizontal span over 10 mm"; `fdm-rugged-enclosure-guidelines.md:111`. At rev-3 defaults `(20 − 3)/2 = 8.5` |
| **T1-23b** | no vent slot inside the far-wall mid-span lid-fastener boss + gusset strip | **new, rev 5** — §5 vent table. The `n_fast = 6` far-wall fastener lands inside the intake band's X run on every current SKU |
| **T1-32** | the case's own 1/4"-20 insert stack fits under the device: `MCC_INSERT_1_4_20.len + 1 <= MCC_FLOOR_T + mcc_cradle_deck(dev)` | **new, rev 5** — §7.1 floor correction 3. `13.7 <= 13.85` (compact) / `13.8` (plus): **0.15 / 0.10 mm of slack**. The insert is installed from the case underside and its boss must union into the cradle deck's hollow |
| **T1-33** | tongue-and-groove fits the lid: `MCC_TG_H + 1.0 <= MCC_LID_T` **and** `MCC_TG_W + 2*MCC_CLR_TG <= MCC_WALL - 0.8` (offset/shiplap tongue) | **new, rev 5** — §2.2 / D-07. The lid is a flat 3.0 mm slab and `H = 51.0` is a fixed user decision, so a 4 mm-deep groove is geometrically impossible and a *centred* tongue does not fit a 3 mm wall at all. See §15 ruling 4 |
| **T1-34** | every patch-wall window clears the connector's rear envelope: the window opening contains `⌀(mcc_cutout_d(part) + 2*MCC_CLR_SLIDE)` at `z = z_conn_c` **and** the two `mcc_neutrik_d_bosses()` circles `⌀(boss_od + 2*MCC_CLR_SLIDE)` at `(slot_x ∓ MCC_D_SCREW_PITCH[0]/2, z_conn_c ± MCC_D_SCREW_PITCH[1]/2)`; and no unsupported horizontal span in the window roof exceeds 10.0 mm | **new, rev 5** — §2.5, `architecture.md` §5. This is the assert that kills the naive "34 × 39 rectangle with a 45° top chamfer": the plate's rear bosses reach `z = 41.64`, where a 45°-gabled window whose top is at `z = 45` is only 16.7 mm wide |

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
| **D-10** | **PoE-splitter reservation defaults to a dongle-class 75 × 40 × 20 mm envelope** (`DONGLE-75x40x20`, `constants.scad:164`), `GAT-USBC` retained as a non-default alternative. | **User, 2026-09-08** | **fixed** in data; placement resolved by D-12 |
| **D-11** | **The `develop` branch is dropped.** `feature/*` → `main` by CI-green PR; releases are annotated `vX.Y.Z` tags on `main`. | **User, 2026-09-08** | **fixed**; `render.yml` conforms and the docs were rewritten on 2026-09-08 (deviation D3 **resolved**) |
| **D-12** | **The reserved splitter bay and the −X cable allowance SUM: `ez_neg = 27 + 20 = 47`.** §6's reservation rule is honoured unconditionally in every variant. Every `L` grows 20 mm (compact 194.9, plus 211.5); **both families cross the 180 mm span threshold, so all SKUs get 6 lid thumbscrews**; T1-28 passes by construction. `MCC_END_ZONE_NEG_EXTRA_SPLITTER` is derived from `MCC_SPLITTERS[part].size[2]`, so measurement M3 flows straight into `L`. | **User, 2026-09-08** (resolves R15; option (a) of three) | **fixed** |
| **D-13** | **The side-bolt boss is FLUSH — nothing protrudes from the far wall.** `MCC_GAP_FAR` 6 → **16** (derived: `boss_len + MCC_PAD_T − MCC_WALL`), `MCC_SIDE_BOLT_PROUD` 10 → **0**; the 17 mm captive stack sits inside `MCC_WALL + MCC_GAP_FAR = 19`. `W` grows 10 mm (compact 159.9, plus 166.4) — **the printed bbox is unchanged**, since rev 2's bbox already included the lug. The freed 10 mm becomes a 16 mm far-wall airflow duct. The boss becomes a ⌀20 internal thickening from the wall's inner face to the pad face, carried by a 3 mm central vertical support web down to the floor (a ≤45° conical blend alone would need a ⌀48 root and is rejected). Screw length, groove position and clip travel are all unchanged. | **User, 2026-09-08** (resolves R18) | **fixed** |

---

## 11. Constants this contract needs in `lib/mcc/constants.scad`

None of these exist yet (`constants.scad` currently stops at the panel-part table). They are listed
here so the shell milestone starts from a checklist rather than from invention. Every one carries a
citation or an `assumed` tag in the section noted.

**⚠ Rows marked NEW DEFAULT changed in rev 3 (D-12 / D-13). A developer is implementing
`mcc_captive_side_bolt_boss/cut()` against the rev-2 values — these three rows are the follow-up.**

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
| **`MCC_END_ZONE_NEG_EXTRA_SPLITTER`** | **NEW — 20.0, derived: `mcc_splitter_envelope(MCC_SPLITTER_DEFAULT)[2]` (the on-edge X extent). Do not hard-type 20** | §4, **D-12** |
| **`MCC_SPLITTER_DEFAULT`** | **NEW — `"DONGLE-75x40x20"` (`constants.scad:164`); today it is a literal inside `poe_splitter.scad`'s defaults, and `ez_neg` now depends on it, so it must become a named constant** | §5, D-10/D-12 |
| `MCC_GAP_DEV` | 2.0 `assumed` | §4 |
| **`MCC_GAP_FAR`** | **NEW DEFAULT — 16.0**, derived: `max(MCC_GAP_FAR_DUCT_MIN, boss_len + MCC_PAD_T - MCC_WALL)`. **Was 6.0** | §5, §7.1, **D-13** |
| **`MCC_GAP_FAR_DUCT_MIN`** | **NEW — 6.0 `assumed`**, the old airflow-duct floor; now non-binding but kept so the `max()` documents both drivers | §5, §7.1 |
| `MCC_FAN_APERTURE_D` | 38.0 (derived: `H_int - 2*MCC_WALL`, capped) | §5 |
| **`MCC_VENT_AREA_RATIO`** | **NEW — 1.0 `assumed`** (the source rule is qualitative: "comfortably larger", `thermal-guidelines.md:104-109`). Used by T1-30 | §5, R20 |
| `MCC_LID_SPAN_MAX` | 180.0 — **unchanged; both families are now over it, so `n_fast = 6` everywhere. Keep the rule, do not fold in the 6** | §6 |
| `MCC_CRADLE_DECK` | derived per family: `z_conn_c - dev_h/2 - MCC_FLOOR_T` | §1 |
| `MCC_PAD_T` | 2.0 `assumed` | §1, §7.1 |
| `MCC_SIDE_BOLT_HEAD_D` / `_HEAD_H` | 10.0 / 4.5 `assumed` (M5) | §7.1 |
| `MCC_SIDE_BOLT_HEAD_REC_D` / `_REC_H` | 12.0 / 6.0 | §7.1 |
| `MCC_SIDE_BOLT_WEB_T` | 3.0 (the *retaining* web the E-clip lands on — not the support web) | §7.1 |
| `MCC_SIDE_BOLT_CLIP` | struct: groove_d 5.0, groove_w 0.8, od 11.0, t 0.7 — all `assumed` (M4) | §7.1 |
| `MCC_SIDE_BOLT_POCKET_D` / `_POCKET_H` | 13.0 / 8.0 | §7.1 |
| `MCC_SIDE_BOLT_ENGAGE` | 6.0 `assumed` (M2) | §7.1 |
| `MCC_SIDE_BOLT_BOSS_OD` | 20.0 | §7.1 |
| **`MCC_SIDE_BOLT_PROUD`** | **NEW DEFAULT — 0.0**, derived: `max(0, boss_len + MCC_PAD_T - (MCC_WALL + MCC_GAP_FAR))`. **Was 10.0.** Stays a parameter | §7.1, **D-13** |
| **`MCC_SIDE_BOLT_SUPPORT_WEB_T`** | **NEW — 3.0 (`= MCC_WALL`)**, the vertical printability/support web under the internal boss | §7.1, **D-13** |
| **`MCC_SIDE_BOLT_KEEPOUT_STRIP_W`** | **NEW — 7.0**, derived: `MCC_SIDE_BOLT_SUPPORT_WEB_T + 2*2.0`; the vent keep-out strip below the ⌀24 disc | §5, §7.1, **D-13** |
| `MCC_SIDE_BOLT_PAD_OD` / `_PAD_ID` | 18.0 / 8.0 `assumed` | §7.1 |

### Ordering constraint

`MCC_GAP_FAR` must be defined **after** `boss_len`'s inputs (`_HEAD_REC_H`, `_WEB_T`, `_POCKET_H`)
and `MCC_PAD_T`, and **before** `MCC_SIDE_BOLT_PROUD` and anything that computes `W`. `constants.scad`
holds only variable assignments and pure functions (`architecture.md` §3), so this is a plain
top-to-bottom ordering requirement, not a module dependency.

### Rev-5 addendum (2026-09-08) — constants settled by the L2 architecture gate

| Constant | Value | Status |
|---|---|---|
| `MCC_LID_CLEAR` | **2.0** | **ACCEPTED** (§15 ruling 3). Minimum only — not the design plenum, which is 10.85 mm here and must never be sealed (`architecture.md` §12 Q10) |
| `MCC_TG_W` / `MCC_TG_H` | **1.6 / 2.0**, offset (shiplap) tongue flush with the wall's **inner** face | **CHANGED** from the plan's 3.0/4.0, which are geometrically impossible (§15 ruling 4, T1-33). `models/coupons/tg-ladder.scad`'s `T_W`/`T_H` must be re-cut to these before it is printed |
| `MCC_VENT_SLOT_W` / `MCC_VENT_WEB_W` | 1.2 / 1.6 `assumed` | unchanged, §5 |
| `MCC_VENT_INTAKE_BAND_H` | **18.0** | **CHANGED** from the plan's 15.0 (§15 ruling 5). 12 and 15 both fail T1-30 once the T1-23/T1-23b keep-outs are subtracted |
| `MCC_VENT_EXHAUST_Z` | `[32, 44]` | unchanged, §5 |
| `MCC_FAN_APERTURE_D` | **38.0** | already required by §11 above; **the plan omitted it while asserting against it** — it must be added, and it must agree with `mcc_fan_cutout()`'s own `frame[0] − 2` |
| `MCC_PANEL_BEZEL_T` | **3.0**, new | the proud sacrificial-bezel layer of `MCC_T_PATCH`; needed explicitly now that the rabbet is stepped (§2.5). `MCC_T_PATCH = MCC_PANEL_BEZEL_T + MCC_PANEL_SEAT_T + MCC_WALL` |
| `MCC_CRADLE_RIB_T` / `_RIB_H` | 3.0 / 9.0 | unchanged, §7 |
| `MCC_CRADLE_FLOOR_PAD_T` / `_MIN` | 2.0 / 40 | unchanged, §7 |
| `MCC_STRAP_SLOT` | `[25, 5]` `assumed` | unchanged, but the −X pair's X position is now derived (§7.1 correction 1), not `±(L/2 − 25)` |
| `MCC_FLOOR_FEATURE_MIN_SEP` | 15.0 | unchanged, §7.1 |

---

## 15. Rulings, 2026-09-08 — L2 architecture gate for `docs/plans/2026-09-08-l2-first-case.md`

Verdict on that plan: **APPROVED WITH CHANGES.** The envelope arithmetic, the coordinate frame, the
slot/pitch/end-zone maths, the lid-fastener placement and the `part=="assembly"` export exclusion are
all correct as written. Eight `PLAN-ASSUMPTION`s were raised; the rulings are below, together with
nine further defects found during validation that the plan did not raise.

| # | Assumption | Ruling |
|---|---|---|
| 1 | new L1 `lib/mcc/layout.scad` | **ACCEPT**, constrained: pure **functions only, no modules ever**; dependencies limited to `constants.scad` / `ports.scad` / `util.scad`; it may **not** `use` any L1 geometry provider — so `mcc_case_layout()` returns `side_bolt_x`/`side_bolt_z`, and callers fetch `mcc_side_bolt_keepout()` from `fasteners.scad` themselves. It also becomes the home of `mcc_panel_fixing_pos()` (§2.3) |
| 2 | patch-wall aperture = 4 discrete windows | **ACCEPT the 4 windows, REJECT the window shape.** One plate, **one continuous stepped rabbet**, `n_slots` windows through the 3 mm structural lip only. Full normative spec: §2.5 + T1-34 |
| 3 | `MCC_LID_CLEAR = 2.0` | **ACCEPT** |
| 4 | `MCC_TG_W/H = 3.0/4.0` | **REJECT.** `MCC_TG_H = 4.0 > MCC_LID_T = 3.0` — a 4 mm groove cuts clean through the lid, and `H = 51.0` is a fixed user decision so the lid cannot grow. A *centred* tongue also does not fit a 3 mm wall (`0.8 + 0.25 + w + 0.25 + 0.8 ≤ 3.0` → `w ≤ 0.9`). **Ruling: offset/shiplap tongue flush with the wall's inner face, `MCC_TG_W = 1.6`, `MCC_TG_H = 2.0`**, leaving 1.0 mm of lid above the groove. New assert T1-33. `tg-ladder` calibrates `MCC_CLR_TG` and must be re-cut to 1.6/2.0 |
| 5 | `MCC_VENT_INTAKE_BAND_H = 15.0` | **CHANGE to 18.0.** 15 mm gives ≈1143 mm² *gross* — but T1-23 (side-bolt strip + disc, ≈78 mm²) and the new T1-23b (far-wall mid lid boss, ≈64 mm²) must come off, leaving ≈1084 < 1134. See §5 |
| 6 | far-flank rib count/positions | **CHANGE.** The plan's §3.3 visibly hand-iterates and contradicts itself. Deterministic rule now normative in §7; for NDI to HDMI it yields **4 ribs at `x = −38.95, −12.0, +19.0, +45.95`**. The contract's "exactly two, outboard of the intake band" alternative is **struck** as unrealisable |
| 7 | splitter tie-down orientation | **CHANGE the fix, not the diagnosis.** The plan is right that `mcc_splitter_tiedown()` assumes a *flat* splitter — and so does `mcc_splitter_envelope()`, which additionally inflates `size[0]` by `2 × cable_allow` and would reserve a **115 mm** Y extent instead of §5's 75 mm. **Do not hand-roll holes in `mounts.scad`.** Add an `orient = "edge"` parameter to **both** modules in `poe_splitter.scad` (an approved L1 change, outside the plan's file list) and a `cable_allow = false` option on the envelope; `mounts.scad` then calls `mcc_splitter_tiedown(orient="edge")`. The tie-down stays **2 × (4 × 1.5) zip-tie slots**, not "2 × ⌀8" |
| 8 | slot-order contradiction | **The §3 rule text is right; the §3 worked-results table was wrong** — on **six of eight rows**, not just the four decoders. Table replaced (§3). The plan's own claim that "the encoder rows do match" is itself wrong: HDMI TX and SDI TX were reversed too, and HDMI Plus had slots 3/4 swapped. Root cause: "end A" in the rule means `face.x < 0` in the case frame, while the table was built from Magewell's "Face A", which is the *video* end on the decoders. **No device file changes.** Final order for NDI to HDMI: **1 = NE8FDP-B (rj45) · 2 = NAUSB-W-B (usb_b) · 3 = NAUSB-W-B (usb_host) · 4 = NAHDMI-W-B (hdmi_out)** |

**Further defects found by the architect (not raised by the plan):**

| # | Defect | Where |
|---|---|---|
| A | Plate-retention boss positions in the plan (`±(plate_l/2 − 4)`, `z_conn_c ± 14`) do not match the already-implemented `mcc_panel_plate()` (`±(plate_l/2 − 3)`, `±16.5`) — the screws would not line up | §2.3 correction |
| B | The rabbet must be **stepped** (6 mm over the plate's 3 mm rim, 5 mm over the 2 mm field); a uniform 5 mm pocket buries the rim | §2.5 |
| C | The plate's rear connector bosses reach `z = 41.64` and cannot pass a 45°-gabled window | §2.5, T1-34 |
| D | T1-18 (`fan_bay ∩ end_zone_cable_envelope == ∅`) is unsatisfiable on every SKU | §9 T1-18, re-scoped |
| E | The −X strap-slot pair intersects the reserved splitter bay (T1-17 would fire) | §7.1 correction 1 |
| F | `mcc_floor_keepout()` cannot be nullary — it depends on `L`, `W`, `x_bolt` | §7.1 correction 2 |
| G | The case's own 1/4"-20 insert stack (13.7 mm) barely fits under the device (13.85 mm) and must live inside the cradle deck | §7.1 correction 3, T1-32 |
| H | VESA 75 × 75 cannot be M4 clearance through-holes on the compact family — they land under the device | §7.1 correction 4 |
| I | The far-wall mid-span lid-fastener boss stands inside the intake vent band | §5 vent table, T1-23b |
| J | The side-bolt support web's floor footprint is 3 × 14, not 3 × 20 | §7.1 floor table |
