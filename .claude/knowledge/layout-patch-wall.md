# Patch-wall layout contract

Status: **revision 12, 2026-09-09.** Rev 12 is the architecture gate for
`docs/plans/2026-09-09-fan-bay-reservation.md` (**deviation D23** — the fan bay's Y/Z footprint is
reserved by nothing, and the 5 mm intake clearance is a bare literal in two files). Verdict:
**APPROVED WITH CHANGES — 6 blocking, no user decision**; full ruling in **§19** below and in that
plan's **§11 "Architect verdict"**.

**Nothing in this contract's envelopes moves** and no golden may move — the ghost this adds is
`%`-ed and `MCC_SHOW_GHOST`-gated, so it emits nothing. What changes here:

1. **§5's fan-bay bullets gain the reserved world AABB** (`fan_bay_x/y/z`) and, with it, a
   **correction to a rev-11 number**: the `fan_y` +Y cap is **−20.7, not −25.7**, and the available
   +Y travel on compact is **10.1 mm, not 5.1** — rev 11 charged the full `mcc_bay_depth` instead of
   `d_bay_free`, double-counting `MCC_WALL + MCC_PANEL_SEAT_T`, and folded in an unnamed 2 mm
   clearance. See §18.6 for what that does (and does **not**) do to the #32 ruling.
2. **§9 gains T1-46a–d** — the fan bay's Y/Z footprint. Next free ID checked against §9 itself, per
   rev 11's own lesson.
3. **§11 gains a rev-12 addendum**: `MCC_FAN_DEFAULT`, `MCC_FAN_INTAKE_CLR`, `MCC_FAN_BAY_CLR`.

Rev 11 history follows. Rev 11 is the architecture gate for
`docs/plans/2026-09-09-fan-switch.md` (**#32** — an external manual fan on/off switch in the +X end
wall beside the ⌀38 fan aperture). Verdict: **APPROVED WITH CHANGES — 8 blocking + 1 user
decision**; full ruling in **§18** below and in that plan's **§9 "Architect verdict"**.

**Nothing in this contract's envelopes moves.** The switch pad is an *internal* thickening of the +X
wall (the D-13 pattern — material moves inward, never outward), so §1/§8's `L`/`W`/`H` are untouched
on every SKU and `bbox` is unchanged on every part. What changes here:

1. **§5 gains a "Fan switch" subsection** — the two-band placement contract (`pad` band vs the 3 mm
   gusset strip near the wall; `body` band vs the corner lid-fastener boss deeper in) and the
   band-solved `switch_y`.
2. **§9 gains T1-43 / T1-44 / T1-45.** The plan proposed "T1-38/T1-39" — **both were already taken by
   rev 9** (rail-groove floor thickness, deck-ladder grid), and rev 10 went to T1-42c. Third
   consecutive plan to collide on assert numbering: **the next free ID is always the maximum in §9,
   not the maximum a plan remembers.**
3. **§10 gains decision D-18** (flush actuator, plus-family only).

Rev 10 history follows. Rev 10 is the architecture gate for
`docs/plans/2026-09-09-printed-m3-threads.md` (**#30** — the Neutrik D-flange fixing holes become
printed M3×0.5 internal threads in the existing rear pad, replacing the heat-set inserts). Verdict:
**APPROVED WITH CHANGES — 7 blocking**; the full verdict lives in that plan's **§9 "Architect
verdict"** and the design record in `architecture.md` **§5 "Connector fixing" bullet 3**.

**Nothing in this contract's geometry moves.** §1's frame, §2/§2.5's aperture spec, §3's slot rule,
§4's end zones, §7/§7.1 and §8's envelopes are all untouched, and **no `L`/`W`/`H` figure changes on
any SKU** — because `MCC_THREAD_M3_PAD_D` (8.28) and `MCC_THREAD_M3_PAD_H` (7.0) are **pinned equal
to the pre-#30 heat-set boss**. What changes here:

1. **§9 gains T1-42a/b/c** (thread-pad wall, engaged turns, residual radial engagement vs `$slop`).
   **T1-36 … T1-41 were already taken by rev 9** — the plan's own "T1-36a/T1-36b" numbering
   collided and was renumbered.
2. **One single-source fix in `lib/mcc/layout.scad:189`:** `d_rel` must be derived from
   `MCC_THREAD_M3_PAD_D + 2·MCC_CLR_SLIDE`, **not** from
   `MCC_BOSS_MIN_RATIO · MCC_INSERT_M3.od + 2·MCC_CLR_SLIDE`. Numerically identical today (8.88), so
   §2.5 and T1-34a–d are invariant — but after #30 the pad is no longer built from `MCC_INSERT_M3`,
   while `MCC_INSERT_M3` stays in live use for the plate-fixing bosses. Leaving both would give one
   physical diameter two independent sources; this is the same rule that put
   `mcc_panel_fixing_pos()` in `layout.scad` (D6) and that named `rail.scad` after its interface.
   **`layout.scad:395`'s `insert_hole_r` (T1-34d) correctly stays on `MCC_INSERT_M3`** — that is the
   shell's own plate-fixing boss, which is out of #30's scope.
3. **No new neighbour-collision assert is needed, and the arithmetic is recorded so nobody adds
   one.** The two pads of a connector sit on the *diagonal* (±9.5, ∓12). At the 32 mm minimum slot
   pitch the nearest pads of two adjacent slots are `Δx = 32 − 19 = 13`, `Δy = 24` → **27.3 mm
   apart**, against an 8.28 mm OD. Achieved pitch today is 41.97–63.45 mm. T1-34c/T1-34d plus the
   ≥32 mm slot-pitch assert already bound this.

**Not changed by rev 10:** everything else in this file. Rev-9 history follows.

Status: **revision 9, 2026-09-09.** Rev 9 is the architecture gate for the mount rail (#25), the TV
and truss brackets (#26/#27), the cradle-deck lattice (#29) and the lid vents (#24). Verdicts,
`PLAN-ASSUMPTION` rulings, the required changes and the ordered developer dispatch are all in the
new **§17**. What moves in *this* contract:

1. **§7's cradle table** — the "Deck slab | 8.8 mm, ribbed/hollow, 3 mm top plate on 3 mm webs" row
   was aspirational and was never built; it is replaced by the real, implemented lattice (**D-17**).
2. **§7.1's floor keep-out table** — the VESA 75 × 75 row is **struck** (**D-15**, user decision) and
   replaced by the mount-rail band; the ⌀20 case-insert row stays (**D-16**: `cfg.tripod_insert`
   defaults **true**). The concentric `case_tripod_insert` / `fishtail_reserve` pair is called out
   explicitly, because it breaks the pairwise assert D16 asks for (`architecture.md` §13 **D19**).
3. **§9** gains **T1-36 … T1-41**.
4. **§10** gains **D-15** (rail replaces VESA), **D-16** (tripod insert default true), **D-17** (deck
   lattice).

**Not changed by rev 9:** §1's frame, §2 in its entirety, §3, §4, §5, §6, §7.1's side-bolt geometry,
§8's envelopes — **no envelope figure and no `L`/`W`/`H` moves on any SKU.** All three plans are
interior/floor/lid work inside the existing shell. Rev-8 history follows.

Rev 8 carries the user's fan-power decision (**D-14**, §10) into
this contract. Two things change here and nothing else does:

1. **§2.5 gains the `DBA-BL-B` ruling.** A blanked slot is a **reserved** slot, not a deleted one:
   `MCC_PANEL_PARTS["DBA-BL-B"].hole_d` goes `0 → 24.0`, so the plate gets its full ⌀24.2 cutout and
   the wall gets its full `d_win = 24.8` teardrop + two reliefs, and a purchased `DBA-BL-B` blanking
   plate covers them. Any D connector can be fitted later **without reprinting anything**.
   `depth`/`plug_len`/`bend` stay 3.2/0/0, so the blank still costs no bay depth and still ranks
   `[0, 0]` — **innermost, §3 step 6 is unaffected.**
2. **§16.6 is new**: the per-SKU consequences. The three decoders' **slot 3 becomes `DBA-BL-B`**;
   **slot order is unchanged on all three**, and **every envelope figure in §16.1 is unchanged**.

**Not changed by rev 8:** §1 (frame), §2.1–§2.4, §3's algorithm, §4 (end zones), §5 (bay/vent
geometry), §6, §7, §7.1, §8's envelopes, and every T1-xx except the note added to T1-04. **One
BLOCKING item** is recorded against the two Plus encoders — the internally-cabled Mini-DIN-8 plug
vs. the fan bay (`architecture.md` §11 **R23**, measurement **M12**) — and it is a measurement, not
a contract change. Rev-7 history follows.

Rev 7 is the pre-implementation architecture gate for the seven
remaining SKUs (GitHub issues #3–#9), built in parallel on seven branches. It adds **§16** (the
per-SKU fit-check table, the per-SKU ruling, and the parallel-work rules), and makes two record
corrections: **§2.5's boss-relief positions** (the *placed* plate puts its rear bosses at
`(−9.5, −12)` and `(+9.5, +12)` relative to the slot centre — rev 6's `(∓9.5, ±12)` described the
mirrored pattern; the code was corrected in `shell.scad` on 2026-09-08, commit 2a7e0b0, after the
user saw the mirror), and **D10's resolution** (the four patch-wall plate-fixing bosses carry a
genuine *through*-bore, insert side at the rear tip — §15 ruling 2026-09-08c). One **BLOCKING**
library defect was found: **T1-18(c) fails on all four BNC-ended SKUs** (§16.3). Rev-6 history
follows.

Rev 6 answers the user's rejection of the first rendered case's
connector openings (Pro Convert for NDI to HDMI). It **replaces §2.5**: the lip window stops being a
`hull()`-ed "crown" and becomes a **plain round hole (truncated-teardrop above the 45° line) plus two
separate boss reliefs**, so the only thing visible through the plate's own D cutout is ≤ 1.5 mm of
relief crescent. It **retires T1-34** in favour of T1-34a–d and adds T1-35 (the connector screw must
actually reach its insert). It **rejects the proposed top-open (U-notch) aperture** — reasons in §15
ruling 2026-09-08b. §2.3 fixing positions are **unchanged**. Rev-5 history follows.

Rev 5 is the L2 architecture gate for
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

> **Rev 6, 2026-09-08 — the fixing positions are UNCHANGED.** The user's rejection of the connector
> openings does not touch plate retention: it stays **4 × M3 at `mcc_panel_fixing_pos(plate_size,
> rim_w)` = `(±(plate_l/2 − 3), ±16.5)`**, through the plate's rim into heat-set bosses standing
> rearward off the rabbet lip. The top-open aperture that would have forced this down to "2 lower
> bosses + lid capture" is rejected (§15 ruling 2026-09-08b). Rev 6 recorded those four shell bosses
> as plain UNBORED solids — deviation **D10**, a print blocker. **RESOLVED 2026-09-08 (rev 7): the
> four plate-fixing bosses carry a genuine THROUGH-bore** — `MCC_INSERT_M3.len +
> MCC_INSERT_BORE_EXTRA` at `MCC_INSERT_M3.hole_d` open at the **rear tip**, then `MCC_M3_CLR_D`
> the rest of the way out through the front (plate-facing) face
> (`lib/mcc/shell.scad:289-321`). It is a through-bore, not the blind pocket T1-35 nominally
> describes, because Manifold on the pinned OpenSCAD 2025.09.07 cannot union a *blind-bored* boss
> flush against a wall face. Full reasoning and the consequence for assembly: **§15 ruling
> 2026-09-08c**. Assert **T1-35** stands and is satisfied.

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

### 2.5 The patch-wall aperture — ONE rabbet, `n_slots` ROUND WINDOWS + 2 BOSS RELIEFS (rev 6, 2026-09-08)

> **Rev 6 replaces rev 5's `hull()`ed "crown" window.** Rev 5's shape was the convex hull of the
> connector circle and the two rear-boss relief circles — a 27.9 × 32.4 mm diagonal blob. The user
> rejected it on sight ("the 4 D-slots must be exactly round — not the weird round/diamond-like
> shape they have now"), and the user is right on the merits as well as on looks. See §15 ruling
> 2026-09-08b for the full ruling, including why the proposed **top-open U-notch aperture is
> rejected**.

**What the assembled patch wall must look like from outside — the acceptance criterion.** A flat
plate face recessed `MCC_PANEL_BEZEL_T` (3.0 mm) behind the wall's outer face, carrying `n_slots`
**exactly round** ⌀`mcc_cutout_d(part)` cutouts (24.2 for `NE8FDP-B`, 23.8 for the 23.6-class parts)
and, per slot, two ⌀`MCC_M3_CLR_D` (3.4) screw holes on the Neutrik diagonal **`(−9.5, −12)` and
`(+9.5, +12)`** in case `(x, z)` — see the frame rule below. Each
26 × 31 flange seats flat on that plate face and screws into an M3 heat-set insert in the plate's own
rear boss. **Nothing else may be visible through a D cutout** except the two relief crescents
quantified in T1-34b, which the fitted connector body covers completely.

The wall itself still cannot be one long opening — the three rev-5 reasons stand and are not
re-litigated:

- `architecture.md` §5 is a hard shell rule — "the aperture roof is a ≤45° self-supporting chamfer,
  never a flat bridge … no unsupported horizontal span over 10 mm anywhere in the shell." A single
  161.9 mm-wide void 39 mm tall has no legal roof: a 45° chamfer converging from both top corners
  needs ~81 mm of rise and only 39 mm exists.
- §6's `n_fast = 6` mid-span lid fastener sits at `x_gap`, a *slot-gap centre* on the patch wall. Its
  boss runs floor-to-lid and its gusset needs solid wall material at that X across the aperture band.
- T1-13 ("every lid-fastener boss clears every flange edge by ≥ `boss_od/2 + 2`") only means anything
  if the boss is embedded in wall material *between* flanges.

> ### The frame rule — write this down once and stop re-deriving it (rev 7, 2026-09-08)
>
> **The outside viewer's right is world −X, and a "front-view" `+y` on the plate becomes world −Z.**
>
> The plate is authored in `mcc_panel_plate()`/`mcc_neutrik_d_cutout()` in the Neutrik **front view**:
> local `+x` right, local `+y` up, screw holes and rear bosses at local `(−9.5, +12)` and
> `(+9.5, −12)` (`lib/mcc/neutrik.scad:72-73,137`). `models/<slug>/case.scad` places it with
> `rotate([-90,0,0])`, which maps **local `(x, y)` → world `(x, z = −y)`**. So on the assembled case
> the plate's rear bosses sit at
>
> ```
> world (x, z) = (slot_x(i) − 9.5, z_conn_c − 12)   and   (slot_x(i) + 9.5, z_conn_c + 12)
> ```
>
> i.e. the **lower-left / upper-right** diagonal when the case is viewed from *inside*, along +Y.
> `_mcc_patch_wall_window()` draws its two boss reliefs in a 2-D `(x, z)` frame
> (`rotate([90,0,0])` maps 2-D `y` → world `z`), so it must use `(−sx, −sz)` and `(+sx, +sz)` — which
> is what `lib/mcc/shell.scad:210-211` does since commit **2a7e0b0** (2026-09-08).
>
> **Rev 6 wrote the diagonal as `(∓9.5, ±12)`, which is the plate's *authored* pattern, not its
> *placed* pattern.** Following the doc literally produced reliefs mirrored about `z = z_conn_c`;
> the user saw it as "screw holes look rotated 90° vs the holes in the base" and the code was fixed
> on 2026-09-08. **The doc is now corrected.** Rules that follow from it, so this is not repeated:
>
> 1. Any position quoted for a patch-wall feature is in **case coordinates**, never in the plate's
>    authored front view. If a paragraph gives a plate-local figure it must say so explicitly.
> 2. A "left/right" in prose about the patch wall means **the outside viewer's** left/right, i.e.
>    `+X` is the viewer's *left*. Slot 1 (the −X block) is therefore on the viewer's **right**.
> 3. The window's *containment* and *clearance* asserts (T1-34c/T1-34d) are numerically invariant
>    under this mirror, because the four `mcc_panel_fixing_pos()` points are symmetric about both
>    `x = 0` and `z = z_conn_c` — which is exactly why the mirror survived every assert and had to be
>    caught by eye. `lib/mcc/layout.scad:388-391` still evaluates T1-34d against the *mirrored*
>    relief pair; harmless today, latent tomorrow (deviation **D14**, `architecture.md` §13).

**Normative:**

| Element | Ruling |
|---|---|
| Panel plate | **ONE** continuous `plate_l × MCC_PLATE_H` part, flat-printed face-down, retained by 4 × M3 at `mcc_panel_fixing_pos()` (§2.3, **unchanged by rev 6**). Do **not** split it into `n_slots` plates. |
| Rabbet | **ONE** continuous pocket in the wall's outer layers, spanning the whole plate footprint + `MCC_CLR_SLIDE` per side. **Stepped, not flat-bottomed:** `MCC_PANEL_BEZEL_T (3) + rim_t (3) = 6 mm` deep over the plate's `rim_w` border ring, `MCC_PANEL_BEZEL_T (3) + MCC_PANEL_SEAT_T (2) = 5 mm` deep over the field. Unchanged from rev 5 — it is correct and it is what puts the plate face 3.0 mm behind the wall face (the sacrificial bezel). |
| Structural lip behind the plate | 3 mm behind the field, **2 mm behind the rim ring**. Assert `residual lip >= 2.0`. Unchanged. |
| Windows | `n_slots` **discrete openings through the 3 mm structural lip only**, one per `slot_x(i)`, with solid lip material in the inter-slot webs and out to `MCC_PANEL_FRAME_MIN`. **Not one long opening, and NOT one rabbet per window.** Unchanged. |
| **Window shape (CHANGED, rev 6)** | A **`union()` of three separate 2-D profiles — never a `hull()`**: (i) the **body opening**, a plain circle `⌀ d_win = mcc_cutout_d(part) + 2·MCC_CLR_SLIDE` centred on `(slot_x(i), z_conn_c)`, **truncated-teardropped above the 45° tangent line** (below 45° it is exactly the circle); (ii) + (iii) two **boss reliefs**, plain circles `⌀ d_rel = boss_od + 2·MCC_CLR_SLIDE = 8.88` centred on the **placed** plate's rear-boss positions, **`(slot_x(i) − 9.5, z_conn_c − 12)` and `(slot_x(i) + 9.5, z_conn_c + 12)`** in case `(x, z)` — corrected rev 7; see the frame rule above. |
| **Body-opening apex (CHANGED, rev 6)** | Truncated teardrop: `cap_h = d_win/2 + MCC_APERTURE_CAP_RISE (0.4)` above the centre, flat bridge width `w_flat = 2·(d_win/2·√2 − cap_h)`. At `d_win = 24.8` (etherCON): `cap_h = 12.8`, `w_flat = 9.48`; at `d_win = 24.4`: `cap_h = 12.6`, `w_flat = 9.30`. Both ≤ `MCC_APERTURE_BRIDGE_MAX (10.0)`, so `architecture.md` §5's span rule holds **and** the apex stays hidden behind the plate (`cap_h > mcc_cutout_d(part)/2` by 0.7 mm). A full 45° teardrop apex (`r·√2` = 17.5) is **not** used: it would leave only 0.26 mm to the plate's top edge (T1-34c). |
| **Boss reliefs (CHANGED, rev 6)** | Plain circles, **no teardrop**: `d_rel = 8.88 < MCC_APERTURE_SELF_SUPPORT_MAX_D (10.0)`, so they are self-supporting by this repo's own 10 mm span rule. They stay **separate** from the body opening — they overlap it geometrically (centre distance `hypot(9.5,12) = 15.305`, sum of radii `12.4 + 4.44 = 16.84`), so the union is one connected void and the plate's bosses still slide straight in along −Y, but the *silhouette* is a circle with two small satellites instead of a diagonal blob. |
| Rabbet-pocket roof | A 5–6 mm-deep horizontal ledge, supported along its whole back edge by the lip — an overhang, not a bridge, and inside the 10 mm rule. A ≤45° relief chamfer on the **bezel layer only** (outer 3 mm, leaving the seat plane intact) is recommended; it improves the 168 mm-long top edge and costs nothing. Optional, not asserted. |

**Why `union` beats `hull` — three independent reasons, in priority order.**

1. **Roundness (the user's objection).** With `hull()`, the whole boundary of the diagonal blob is
   visible through the plate's ⌀23.8/24.2 cutout from any oblique angle: the blob is *smaller* than
   the plate hole along the two diagonal flanks. With `union()`, the body opening is a circle
   0.3 mm larger in radius than the plate hole and the teardrop apex is larger still, so **the whole
   body-opening boundary is hidden behind the plate.** Only the two relief circles intrude:
   `mcc_cutout_d/2 − (15.305 − 4.44)` = **1.04 mm** (23.6-class) / **1.24 mm** (etherCON) of crescent,
   2.0 mm behind the plate face and covered by the fitted connector body. That is T1-34b.
2. **Lip material.** The hull removes ~35 % more of the 3 mm structural lip than the union, and it
   removes it exactly on the diagonal flanks where the plate's 2 mm flange seat most needs backing
   against plug-insertion load (`architecture.md` §11 R4).
3. **The hull never bought printability.** The rev-5 code comment claims a "continuously-curved,
   self-supporting crown". It is not: the top of the hull near the upper relief circle is still a
   circular arc with a horizontal tangent — exactly the overhang a plain circle has. The
   self-supporting job is done by the truncated teardrop above, not by hulling.

**Why a plain rectangle + 45° top chamfer still does not work** (kept from rev 5 — the trap the
first plan fell into): with the window top at `z = 45` and a ≤45° roof, the clear width at height `z`
is at most `bridge + 2·(45 − z)`, **independent of the window's nominal width**. The plate's rear
bosses reach `z = z_conn_c + 12 + boss_od/2 = 41.64`, where that gives at most `10 + 6.72 = 16.72 mm`
— but the boss pair spans `2·(9.5 + 4.14) = 27.28 mm`. No rectangle width fixes it; the two local
boss reliefs are the fix.

**Where the flange-fixing bosses live, and why they stay on the plate (rev 6, settled).** The two M3
heat-set bosses per slot stay on the **rear of the panel plate** (`mcc_neutrik_d_bosses()`, called
from `mcc_panel_plate()`), at `(∓9.5, ±12)` in the front-view diagonal, `boss_h = 7` rearward from
the plate's rear face. The alternative — moving them into the shell's structural lip, which would
delete the reliefs and make the window a single perfect circle — was evaluated and **rejected**:
it forces 8 heat-set inserts to be set blind from inside a 45 mm-deep box against the wall instead of
on a flat bench plate, it needs longer non-stock M3 screws, and it destroys the "load the plate with
all four connectors on the bench, then drop it in" assembly sequence that makes a `L − 26` mm plate
handleable at all. The 1.0–1.24 mm crescent is the price and it is cheap. Recorded so it is not
re-opened (§15 ruling 2026-09-08b, option C).

### 2.5.1 `DBA-BL-B` — a blanked slot is a RESERVED slot (rev 8, 2026-09-09, D-14 part 4)

**Ruling: give `DBA-BL-B` a real hole.** `MCC_PANEL_PARTS["DBA-BL-B"].hole_d = **24.0**` (was 0),
class **etherCON/universal-D**; `depth 3.2`, `max_panel_t 4.0`, `plug_len 0`, `bend 0`,
`kind "blank"`, `confidence "drawing"` — **all unchanged**. Consequence, slot by slot:

| Where | With `hole_d = 0` (before) | With `hole_d = 24.0` (rev 8) |
|---|---|---|
| **Plate** (`mcc_panel_plate` → `mcc_panel_cutout` → `mcc_neutrik_d_cutout`) | 2 × ⌀3.4 M3 holes only; the field stays solid behind the blank | ⌀`24.0 + MCC_HOLE_COMP` = **⌀24.2** round cutout + the same 2 × ⌀3.4 holes + the same 2 rear bosses |
| **Wall window** (`_mcc_patch_wall_window`) | the 2 boss reliefs only | the full **`union()`**: truncated-teardrop body circle `d_win = 24.2 + 2·MCC_CLR_SLIDE = **24.8**`, `cap_h = 12.8`, `w_flat = 9.48`, plus the 2 × ⌀8.88 reliefs — i.e. **byte-for-byte the `NE8FDP-B` window** |
| **Bay depth** | 3.2 | **3.2, unchanged** — never the `max`, so `d_bay_free` and `W` do not move |
| **Slot rank** `[bend, plug_len]` | `[0, 0]` | **`[0, 0]`, unchanged** — still the lowest row in `MCC_PANEL_PARTS`, so a blank still sorts **innermost** in its block (§3 step 5/6) |
| **End zone / `L`** | keyed by port `kind`, not by `panel` | **unchanged** — `mcc_dev_side_allow()` never sees the part |

**Why 24.0 and not 23.6.** The whole point is that the slot stays convertible. ⌀23.8 accepts
`NAHDMI-W-B` / `NAUSB-W-B` / `NBB75DFGB` but **not** `NE8FDP-B`, whose documented minimum is ⌀24.0
(`knowledge/neutrik/d-series-cutout.md:36`). ⌀24.2 accepts all four, and the 26 × 31 flange still
overlaps it by ~0.9 mm per side — the identical margin every etherCON slot in this repo already has.

**Asserts.** `mcc_cutout_d = 24.2` lands inside `neutrik.scad:48`'s 24-class band `[24.0, 24.6]` ✓.
T1-34a: `w_flat = 9.48 ≤ MCC_APERTURE_BRIDGE_MAX (10.0)` ✓, `d_rel = 8.88 < 10.0` ✓,
`cap_h = 12.8 > mcc_cutout_d/2 = 12.1` ✓. T1-34b intrusion = **1.235 mm** ≤ 1.5 ✓ (the etherCON
figure — a blanked slot is now the etherCON case in every geometric respect). T1-34c/d are
positional and unchanged. **These are the same numbers §16.2 already records as "constant across all
seven"; a blank adds no new pass/fail.**

**Required with it (deviation D18, `architecture.md` §13).** `neutrik.scad:39` decides "is this a
blank?" from `kind == "blank"`, while `shell.scad:181` and `layout.scad:187` decide it from
`mcc_panel_hole_d(part) == 0`. **Unify on `hole_d == 0`.** Left as is, the shell opens the window
and the plate behind it stays solid — a slot that reads open from outside and is blind 3 mm in, with
no assert to catch it (only the head-on `−Y → +Y` elevation, D11).

**T1-04 note (rev 8).** "every slot carries exactly one part (external port or `DBA-BL-B`)" now has
a *second* way to be satisfied: not only a padded, unallocated slot, but a real port whose `panel`
is `"DBA-BL-B"`. Both are legal; the assert is unchanged.

**Nothing in the shell needs a relief for the plate's bosses other than the two window circles.** The
bosses run from `y = W/2 − 5` to `y = W/2 − 12`; the lip occupies `y ∈ [W/2 − 8, W/2 − 5]`, so the
reliefs must be **through-holes** in the lip (a blind pocket cannot work — the boss is 7 mm long and
the lip is 3 mm thick) and the remaining 4 mm sits in free interior. No other shell feature is
affected: the nearest neighbour is the plate-fixing boss at `mcc_panel_fixing_pos()`, whose insert
bore is **3.18 mm** clear of the outermost relief on NDI to HDMI (T1-34d).

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

> **Rev 8, 2026-09-09 — a blank can now also arrive from the *data*.** Since D-14 a device file may
> carry `["panel", "DBA-BL-B"]` on a port that is deliberately not brought out (the decoders'
> `usb_host`). Such a port is still **external** (`mcc_ports_external()` filters on
> `panel != "none"`, `ports.scad:58`), so it still consumes a slot and `n_slots` does not change —
> which is the whole point: the slot, its plate cutout and its wall window are all built and stay
> reusable (§2.5.1). **The algorithm needs no change:** `DBA-BL-B`'s rank is `[0, 0]`, the lowest
> row in `MCC_PANEL_PARTS`, so step 5 places it at the innermost end of its block automatically —
> exactly where step 6 already puts padded blanks. On all three decoders the blanked port was
> *already* the innermost of block B, so **the slot order does not move at all** (§16.6).
> The one thing a developer must not do is set `["panel", "none"]` instead: that drops the port out
> of `ext`, takes `n_slots` from 4 to 3, re-pitches the whole plate, moves the envelope, and leaves
> no slot to convert later — the opposite of what was asked for.

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

### Fan switch — **+X end wall, −Y of the fan aperture** (rev 11, #32, D-18)

An external manual on/off switch in series with the fan's +5 V lead. Gated by `cfg["fan_switch"]`,
defaulting to `cfg["fan"]`. Geometry: `lib/mcc/switch.scad`; part data: `MCC_SWITCHES` /
`MCC_SWITCH_DEFAULT` (L0); position: `switch_pos` from `mcc_case_layout()`.

**Two bands, at two depths — this is the whole placement problem.** The switch competes for the +X
wall's `−Y` region against the fan on one side and the `(+X, −Y)` corner lid fastener on the other,
and the corner fastener presents *two different* obstructions at *two different* X depths:

| Obstruction | Extent | Binds |
|---|---|---|
| Fan reservation | `y ∈ [fan_y − 20, fan_y + 20]` (the 40 mm `NF-A4x10` frame) | both bands, `+Y` side |
| Gusset strip (`_mcc_gusset_web`, `shell.scad:68`) | `MCC_WALL`-wide in Y at `y = −(W/2 − e)`, running in X **to the wall's outer face** | the **pad** band (`x ≳ L/2 − 6`) |
| Corner lid-fastener boss | ⌀`MCC_BOSS_MIN_RATIO·MCC_INSERT_M3.od` = 8.28 at `y = −(W/2 − e)`, `x ∈ L/2 − [14.14, 5.86]` | the **body** band (`x ≲ L/2 − 5.86`) |

Raw band widths (fan-frame edge → obstruction edge), both families at the default `fan_y = y_dev_c`:

| Family | `W` | `fan_y` | pad band (vs gusset) | body band (vs boss) |
|---|---|---|---|---|
| `compact` | 159.85 | −30.825 | **17.60 mm** | **14.96 mm** |
| `plus` | 166.35 | −30.825 | **20.85 mm** | **18.21 mm** |

`switch_y` is **solved as the centre of the feasible interval**, not offset a fixed distance from the
fan — a fixed offset spends all the slack on the fan side and leaves the binding constraint
unchecked:

```
y_hi = fan_y − fan_frame[1]/2 − clr − pad_d/2                  // fan side
y_lo = max( gusset_y_edge + clr + pad_d/2 ,                    // pad vs gusset strip
            boss_y_edge   + clr + body_d/2 )                   // body vs corner boss
switch_y = (y_lo + y_hi)/2          assert y_hi >= y_lo        // T1-43
switch_z = z_conn_c = 25.5                                     // universal, same as the fan
switch_pos = [L/2, switch_y, switch_z]                         // X = the wall's OUTER face
```

**`switch_pos[0]` is the outer-face plane, matching `fan_pos`.** Every call site subtracts
`MCC_WALL` itself (`vents.scad:146` is the reference). Getting this wrong removes **zero** material
and is invisible in every automated check — see `architecture.md` rev-11 header, finding B2.

**The pocket is a well, not a cosmetic dish.** `recess_t = actuator_proud_h + MCC_SWITCH_FLUSH_CLR`,
so the actuator tip finishes **below** the wall's outer face — the same rule T1-25 already imposes on
the side-bolt head. Since `MCC_WALL` is 3 mm, the wall is **locally thickened inward** by a pad
(`pad_t = recess_t + panel_t`, 45° blend on all four sides so it prints in a vertical wall); the
residual `panel_t` must be ≥ `MCC_APERTURE_LIP_WEB_MIN` **and** inside the part's own clamp range
(T1-44). Nothing protrudes and no envelope moves — D-13's pattern, applied again.

**Compact does not fit and must be switched off explicitly (D-18).** At `pad_d = 14.0` / `body_d =
10.0` (⌀6.4 toggle, nut pocket ⌀ ≈ 10) the compact interval is **empty** (`y_hi = −59.325 <
y_lo = −59.285`); plus has a 3.2 mm window. `fan_y` cannot rescue it: the `+Y` side is capped by the
connector bay at `fan_y ≤ −25.7` (compact), worth ≤ 5.1 mm, so **R20 stays closed** and the ⌀20.2
IP65 candidate stays recorded-but-unplaced. Compact variants — including the `base_fan` golden part
and `tests/test_shell.scad`'s `VARIANT_FAN` — carry `["fan_switch", false]` **explicitly**, with a
comment pointing here.

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
| Deck **height** (interior floor → device underside) | **10.80 mm (plus) / 10.85 mm (compact)** — `mcc_cradle_deck(dev) = MCC_SIDE_BOLT_AXIS_Z − dev_h/2 − MCC_FLOOR_T` (`layout.scad:208`). **DERIVED, not free**: shortening it means moving `z_conn_c`, which reopens the vetoed D-06 or thins the 3 mm shell. Escalate, never improvise | §1, §2.2 |
| Deck fill (**rev 9, D-17** — replaces "8.8 mm, ribbed/hollow, 3 mm top plate on 3 mm webs", which was aspirational and was never implemented; the 8.8 figure also predates D-13) | **`MCC_WALL`-wide perimeter frame + an interior ladder of X- and Y-running ribs on a `MCC_CRADLE_DECK_GRID_PITCH` (22.0 mm target) grid, full deck height, no top plate — the device rests on the rib top edges**, exactly as it already does on the far-flank ribs. Rib thickness is **`MCC_CRADLE_RIB_T` (3.0)**, the same constant the flank ribs use — *not* a derived per-family thickness (`architecture.md` §13 **D22**). Achieved pitch: 20.18 / 20.07 mm (compact), 23.50 / 22.23 mm (plus); asserted inside `[MCC_CRADLE_DECK_GRID_PITCH_MIN, _MAX]` = [16, 32] (**T1-39**) | issue #29; `fdm-rugged-enclosure-guidelines.md` §4 "ribs deliver most of the stiffness of a solid block for a fraction of the material" |
| Pad pocket in a lattice deck (**rev 9**) | the 40 × 40 × 2 mm pocket must land on **solid** material: the lattice keeps a solid island over the `MCC_CRADLE_FLOOR_PAD_MIN` footprint for at least `MCC_CRADLE_FLOOR_PAD_T + 1.0` mm below the deck top (**T1-40**). Cutting the pocket straight into the ladder leaves the EPDM pad bearing on ~15 % of its own area over open bays, and it dishes under the device | issue #29, this gate |
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
| Case 1/4"-20 **insert** (case → tripod/cheeseplate) | ⌀20 disc | `(0, 0)` = `floor_center`, case plan centre. A *threaded* feature (D2). **Rev 9 (D-16): behind `cfg["tripod_insert"]`, default `true`** — the user asked to keep every mounting option and dropped only VESA; the flag exists so a future SKU that cannot satisfy T1-32 can turn it off, not as a shipped default-off |
| ~~VESA 75 × 75~~ | ~~4 × ⌀12 discs at `vesa_pos + (±37.5, ±37.5)`~~ | **STRUCK, rev 9 (D-15, user decision 2026-09-09): the dovetail mount rail replaces VESA on the case floor.** The rev-5 correction 4 below (blind M4 inserts because two of the four holes land under the device) is **superseded, not deleted** — it is the record of why the pattern was awkward here in the first place. `MCC_VESA75_PITCH`, `MCC_VESA_HOLE_D`, `_mcc_vesa_positions()`, the four `vesa_*` rows and the `"vesa"` cfg key are all removed by issue #25 |
| **Mount rail (dovetail groove + sill)** | **`MCC_RAIL_LEN × MCC_RAIL_ROOT_W` = 150 × ≈14.6 rect at `(0, MCC_RAIL_Y)`, label `"mount_rail"`** | **new, rev 9 (D-15).** `MCC_RAIL_Y = **−20.0**` — ruled at this gate, **not** the plan's `+20.0`: symmetric about `y = 0`, so the keep-out arithmetic is identical (2.7 mm to the ⌀20 insert disc and to the Fishtail band, 20 mm centre-to-centre ≥ `MCC_FLOOR_FEATURE_MIN_SEP`), but `−20` puts the rail under the cradle deck and the device instead of free-standing in the cable bay, and puts the case's mass *below* the mount line when #26 hangs the patch wall downward (`architecture.md` §11 **R24**). Clearances at `−20`: splitter bay 9.6 mm (compact) / 12.9 (plus); side-bolt web ≥ 35; strap slots ≥ 40; stacking recesses ≥ 42. Z: groove `z ∈ [0, MCC_RAIL_DEPTH]` = [0, 4]; sill `z ∈ [0, MCC_RAIL_SILL_H]` = **[0, 7]**, i.e. `MCC_RAIL_DEPTH + MCC_FLOOR_T`, so **3.0 mm of floor survives over the groove** (T1-38) |
| Fishtail M4 pair | reserve a 60 × 20 band centred on `floor_center` | hole pitch is **`unknown`** — `knowledge/magewell/accessories.md:26` gives only "2× M4×12 screws, 2× M4 nuts". Derive from `knowledge/magewell/assets/magewell-fishtail-bracket.stl` (M7). **Rev 9:** this row is **concentric with the case-insert row by design** (both anchored on `floor_center`, and this one cuts no geometry). The pairwise non-overlap assert D16 requires must exempt exactly this pair — see `architecture.md` §13 **D19** |
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
| ~~**T1-34**~~ | ~~every patch-wall window clears the connector's rear envelope … and no unsupported horizontal span in the window roof exceeds 10.0 mm~~ | **RETIRED rev 6, 2026-09-08.** It was satisfied by the `hull()`ed crown the user rejected, and it under-specified the shape (any envelope containing the three circles passed, including the blob). Replaced by **T1-34a–d**, which pin the shape exactly. The *reason* T1-34 existed — a 45°-gabled rectangle cannot clear the bosses at `z = 41.64` — is preserved in §2.5's "why a plain rectangle still does not work" |
| **T1-34a** | the lip window is `union(body, relief_lo, relief_hi)` with `body = truncated teardrop ⌀(mcc_cutout_d(part) + 2*MCC_CLR_SLIDE)`, `cap_h = d_win/2 + MCC_APERTURE_CAP_RISE`, and `relief = ⌀(MCC_BOSS_MIN_RATIO*insert_od + 2*MCC_CLR_SLIDE)` at **`(−MCC_D_SCREW_PITCH[0]/2, −MCC_D_SCREW_PITCH[1]/2)` and `(+MCC_D_SCREW_PITCH[0]/2, +MCC_D_SCREW_PITCH[1]/2)`** relative to the slot centre, in case `(x, z)` (**corrected rev 7** — rev 6 quoted the plate's *authored* front-view diagonal, which is mirrored once `rotate([-90,0,0])` places the plate; see §2.5's frame rule). Asserts: `w_flat = 2*(d_win/2*sqrt(2) − cap_h) <= MCC_APERTURE_BRIDGE_MAX` **and** `d_rel <= MCC_APERTURE_SELF_SUPPORT_MAX_D` **and** `cap_h > mcc_cutout_d(part)/2` | **new, rev 6** — §2.5. The first clause is `architecture.md` §5's ≤10 mm span rule; the second says the reliefs are small enough not to need their own teardrop; the third is what hides the apex behind the plate. **`hull()` is forbidden in the aperture** — that is a code-review rule, not assertable |
| **T1-34b** | *roundness* — the only part of the lip window visible through the plate's own cutout is the two relief crescents: `mcc_cutout_d(part)/2 − (hypot(MCC_D_SCREW_PITCH/2) − d_rel/2) <= MCC_APERTURE_RELIEF_INTRUSION_MAX (1.5)` | **new, rev 6** — §2.5, and the direct expression of the user's requirement. Evaluates to **1.035 mm** for the 23.6-class parts and **1.235 mm** for `NE8FDP-B`. If a future insert or `MCC_BOSS_MIN_RATIO` change pushes this over 1.5 mm the window stops reading as round and the design must be revisited, not fudged |
| **T1-34c** | *containment* — the whole window stays inside the plate silhouette with `MCC_APERTURE_LIP_WEB_MIN (2.0)` of lip left all round: `cap_h + 2.0 <= MCC_PLATE_H/2`, `MCC_D_SCREW_PITCH[1]/2 + d_rel/2 + 2.0 <= MCC_PLATE_H/2`, and `abs(slot_x(i)) + MCC_D_SCREW_PITCH[0]/2 + d_rel/2 + 2.0 <= plate_l/2` | **new, rev 6** — §2.5. Z: `12.8 + 2 = 14.8 <= 19.5` ✓ and `12 + 4.44 + 2 = 18.44 <= 19.5` ✓ (1.06 mm spare — the binding one). X on NDI to HDMI: `62.95 + 13.94 + 2 = 78.89 <= 83.95` ✓. **This is why the apex is truncated:** a full 45° teardrop apex at `12.4*√2 = 17.54` leaves only 0.26 mm and fails |
| **T1-34d** | every lip window clears every plate-fixing boss's **insert bore** by ≥ 2.0 mm of lip material: `hypot(fix_x − (slot_x ∓ 9.5), fix_z − (z_conn_c ± 12)) − d_rel/2 − MCC_INSERT_M3.hole_d/2 >= 2.0` | **new, rev 6** — `fdm-rugged-enclosure-guidelines.md:127`. On NDI to HDMI the worst pair is the outer slot's lower relief `(72.45, 13.5)` vs. the fixing at `(80.95, 9.0)`: `9.617 − 4.44 − 2.0 = 3.18 mm` ✓. **Rev 7:** the four `mcc_panel_fixing_pos()` points are symmetric about `z = z_conn_c`, so this clearance is *invariant* under the §2.5 relief mirror — 3.18 mm is right either way, and this assert is therefore **not** what catches a mirrored relief pattern (only the head-on elevation is). Measured **to the bore, not to the boss OD** (boss-OD-to-relief is only 1.04 mm, which merely undercuts the boss root on that flank) |
| **T1-36** | *net lid-vent free area* — `mcc_lid_vent_area(dev, cfg) >= MCC_LID_VENT_AREA_RATIO * (π/4) * MCC_FAN_APERTURE_D²` (= 1134 mm² at `ratio = 1.0`), computed from the **same** slot-centre list `mcc_lid_vents_cut()` draws | **new, rev 9** (#24). Same heuristic and same reference area as T1-30 (`thermal-guidelines.md:104-109`), applied to the new top-exhaust path; applies on **every** SKU, fan or not, for the same reason T1-30 does (§6 reserves the fan bay unconditionally). Hand-check: ≈1840 mm² compact, ≈2240 mm² plus. **Must live in the model, not only in `tests/test_shell.scad`** — that is D15's whole lesson |
| **T1-37** | *lid-vent field keep-outs* — the field's `[field_x_lo, field_x_hi] × [field_y_lo, field_y_hi]` clears (a) the T&G groove band and the patch wall's `MCC_T_PATCH` stack on all four sides by ≥ `MCC_LID_VENT_EDGE_MIN`, and (b) **every** `lid_fastener_pos` inflated by `MCC_LID_VENT_FASTENER_KEEPOUT_R` | **new, rev 9** (#24). Both clear by a wide margin on all 8 SKUs today (≥ 15 mm to the nearest fastener, ≥ 16 mm to the nearest groove band); the assert exists because a future device record with a longer or offset device closes that margin silently. `MCC_LID_VENT_EDGE_MIN` is a **named constant** — the plan's inline `1.0` and `1.6` literals are magic numbers and are rejected (§3 parameter conventions) |
| **T1-38** | *the mount-rail groove never thins the floor* — `MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T`, and the `"mount_rail"` keep-out row overlaps no other row in `mcc_floor_keepout()` | **new, rev 9** (#25). The plan's `MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + 2.0 = 6.0` leaves **2.0 mm** of ASA over the groove — under the uniform 3 mm shell spec (`architecture.md` §9), on the surface that carries the entire case when it is bracket-mounted. Correct value **7.0**. The plan's own `MCC_RAIL_SILL_H > MCC_RAIL_DEPTH` is too weak: it passes at 4.1 mm |
| **T1-39** | *deck ladder grid is sane* — achieved interior pitch on each axis lies in `[MCC_CRADLE_DECK_GRID_PITCH_MIN, MCC_CRADLE_DECK_GRID_PITCH_MAX]` (16–32 mm), and each axis yields ≥ 1 interior rib | **new, rev 9** (#29). Guards a future SKU far outside today's size range producing a degenerate 1-bay or 50-rib deck. Today: 20.18/20.07 (compact), 23.50/22.23 (plus) |
| **T1-40** | *the compliant-pad pocket lands on solid material* — the deck lattice keeps a solid island over the `MCC_CRADLE_FLOOR_PAD_MIN` (40 × 40) footprint for ≥ `MCC_CRADLE_FLOOR_PAD_T + 1.0` below the deck top | **new, rev 9** (#29). Without it the pocket is cut into open bays and the EPDM pad bears on the ~15 % of its area that happens to sit over a rib top — it dishes under the device and the "level cable run" §1 derives collapses |
| **T1-41** | *the case tripod-insert boss is braced in a lattice deck* — when `cfg["tripod_insert"]` is true, solid material (a collar of radius ≥ `boss_od/2 + MCC_CRADLE_RIB_T`, or a grid line through `floor_center`) connects the boss to the lattice | **new, rev 9** (#29 × D-16). The boss used to be embedded in a solid block; in a lattice it becomes a lone ⌀17.1 × 13.85 post whose only connection is the 3 mm floor slab. `check`'s `len(split()) == 1` still passes (it *is* connected), so nothing else catches this — it is a stiffness defect, not a topology one |
| **T1-43** | *the fan switch has somewhere to go* — the feasible interval of §5's band solve is non-empty: `y_hi >= y_lo`, where `y_hi = fan_y − fan_frame[1]/2 − clr − pad_d/2` and `y_lo = max(gusset_y_edge, boss_y_edge + (body_d − pad_d)/2) + clr + pad_d/2`. Evaluated **only** when `mcc_fan_switch_enabled(cfg)` | **new, rev 11** (#32). Two-sided by construction, so unlike the plan's own T1-38 it *can* fail — and it does, on the compact family (§5, D-18), which is exactly the information the assert exists to deliver. Lives in `layout.scad` and reads the `MCC_SWITCHES` row directly: §3 forbids `layout.scad` from importing `switch.scad` |
| **T1-44** | *the actuator is fully recessed and the panel is legal* — (a) `recess_t >= actuator_proud_h + MCC_SWITCH_FLUSH_CLR`; (b) `panel_t = pad_t − recess_t >= MCC_APERTURE_LIP_WEB_MIN (2.0)`; (c) `panel_t_min <= panel_t <= panel_t_max` from the part row; (d) `pad_t >= MCC_WALL` (a pad may thicken the wall, never thin it); (e) `recess_t <= MCC_SWITCH_WELL_DEPTH_MAX` | **new, rev 11** (#32); replaces the plan's T1-39, which asserted (b) and (c) only. (a) is the **T1-25 analogue** and is the clause that makes the user's "no accidental switching, survives a 1 m drop" requirement geometric instead of aspirational — the plan's flat `recess_t = 1.0` under a ~10 mm lever fails it. (e) is the stop-and-report clause: if the **measured** (M17) actuator forces a well deeper than a fingertip can reach, the part is wrong and the ticket comes back — do not answer it by shaving the recess. Evaluated in `switch.scad` from pure numbers, like `_mcc_patch_wall_rabbet()`'s own residual-lip asserts |
| **T1-45** | *the switch body fits the +X end zone* — `MCC_WALL + pad_t_extra + body_depth <= L/2 − x_dev_hi`, and the body clears the corner lid-fastener boss in Y by ≥ `clr` | **new, rev 11** (#32). The plan left this as "a straight-line X check … confirm at implementation time", i.e. a hand-check on the one axis where T1-18(c) already passes with **exactly zero slack** on every HDMI-ended SKU. It is cheap and pure; it belongs in the model. Note the two asserts measure different things: T1-18(c) charges the *cable* budget at the fan's Y, T1-45 charges the *switch* at its own Y |
| **T1-35** | *the connector screw must reach its insert* — `mcc_neutrik_d_bosses()`'s bore is continuous from the boss's rear tip through to the panel's own screw clearance hole: `insert_bore_depth + thru_depth == boss_h` with `insert_bore_depth >= MCC_INSERT_M3.len + MCC_INSERT_BORE_EXTRA` and `thru_d >= MCC_M3_CLR_D`. **No solid material anywhere on the screw axis between the flange face and the insert.** Same rule for the 4 plate-fixing bosses in `shell.scad` | **new, rev 6** — the literal, mm-level form of the user's "there is no place to screw the D-connectors down". Today `bore_depth = len + 1 = 6.7` against `boss_h = 7`, leaving **0.3 mm of solid ASA** across the screw axis (`lib/mcc/neutrik.scad:117-120`), and the four `shell.scad` plate-fixing bosses have **no bore at all** (deviation D10). The `neutrik-tile` coupon exists precisely to catch this and has not been printed |
| **T1-42a** | *printed thread pad has enough wall* — `(MCC_THREAD_M3_PAD_D − (MCC_THREAD_M3_MAJOR_D + 4·$slop))/2 ≥ MCC_THREAD_WALL_MIN (2.0)` | **new, rev 10** (#30). At pad_d 8.28 and `$slop` 0.05 → **2.44 mm** ✓. Same 2 mm minimum-wall-around-a-bore convention as `mcc_heat_set_boss()` and `MCC_APERTURE_LIP_WEB_MIN` |
| **T1-42b** | *printed thread has enough engagement* — `(MCC_THREAD_M3_PAD_H − MCC_THREAD_M3_CHAMFER)/MCC_THREAD_M3_PITCH ≥ MCC_THREAD_ENGAGE_MIN_TURNS (3)` | **new, rev 10** (#30). At pad_h 7.0 and BOSL2's actual bevel size (`= pitch = 0.5`, `screws.scad:995`) → **13 turns** ✓. Note the chamfer constant is **0.5, sourced** — not the 1.0 the plan assumed |
| **T1-42c** | *`$slop` has not erased the thread* — `0.5·(MCC_THREAD_M3_MAJOR_D − MCC_THREAD_M3_MINOR_D) − 2·$slop ≥ MCC_THREAD_ENGAGE_MIN_RADIAL` (0.135, = 50 % of nominal). Needs `MCC_THREAD_M3_MINOR_D = 2.459` (ISO 68-1) | **new, rev 10** (#30) — **the assert that caught the plan's own defect.** BOSL2 enlarges an internal thread by **`4·$slop` in diameter** (`screws.scad:753`, `threading.scad:179`) = `2·$slop` per side, against only **0.2705 mm** of radial engagement on M3×0.5. The plan's `$slop = 0.15` removes 0.30 mm/side — the whole thread — leaving a plain ⌀3.6 bore that T1-42a, T1-42b, the mesh checks and the goldens all pass happily. At the corrected `$slop = 0.05` this evaluates to **0.1705 ≥ 0.135** ✓; at 0.15 it is **−0.0295** and fails loudly |

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
| **D-14** | **Fan power is device-sourced; a thermoswitch gates it; no PoE splitter by default; the decoders' host slot becomes a reusable blank.** (1) On stage everything is PoE from an 802.3at switch; the decoders' USB-A host port and the PTZ/Tally port are never used as such. (2) Fan = **NF-A4x10 5V plain** (0.05 A max) in series with a **KSD9700 45 °C normally-open** bimetal switch bonded to the device's metal top. (3) 5 V from the **USB-A host** port on the decoders, from **Mini-DIN-8 pin 8 (VCC, 5 V, 100 mA max) + pin 4 (GND)** on the encoders; **NDI to AIO stays passive** (it has neither port). **No splitter by default — the bay stays reserved per §6/D-12.** (4) The decoders' host slot becomes a **`DBA-BL-B` blank with the full ⌀24.0-class hole** (§2.5.1) so it stays convertible. **D-01 is untouched:** the Mini-DIN-8 is still `panel:"none"`, now internally cabled. | **User, 2026-09-09** | **fixed** in intent; **BLOCKING measurement M12** on `pro-convert-hdmi-plus` / `-sdi-plus` (R23), and the source ratings are unverified (R21/R22, M8–M11, M13) |
| **D-15** | **The floor mount is a dovetail rail; VESA 75 × 75 is removed outright.** The case carries the **female** groove (recessed up into the floor, on a local sill that keeps ≥ `MCC_FLOOR_T` of material over it — T1-38); every printable bracket carries the **male** rail plus the spring-lip latch. Forced, not preferred: the exterior floor face is the bed-contact face, so a protruding feature is unprintable without flipping the base, and D-13 already commits this repo to "nothing protrudes". Interface geometry lives in **one** L1 file, `lib/mcc/rail.scad` (not `bracket.scad` — `architecture.md` §3). `MCC_RAIL_Y = **−20.0**` (§7.1, R24). Single insertion direction: end stop at one end, latch + thumb release at the other. **Removed, not deprecated:** no code path reinstates VESA. | **User, 2026-09-09** (issue #25) | **fixed** in intent; every `MCC_RAIL_*` figure is `assumed` until coupon **M15** |
| **D-16** | **`cfg["tripod_insert"]` defaults to `true`.** The case keeps its own 1/4"-20 floor insert as a shipped feature alongside the rail; the flag exists so a future SKU that cannot satisfy T1-32 (0.10–0.15 mm of slack today, and the `ip_decoder` family at `dev_h = 24.5` will have less) can turn it off — **not** as a default-off opt-in. The researcher's plan proposed default `false`; that was **overruled**: the user asked to keep every mounting option and dropped only VESA. Set the key explicitly in all 8 `models/*/case.scad` for the same BOM/documentation-parity reason `fan` is explicit there. | **Teamlead, 2026-09-09**, on the user's stated scope | **fixed**; brings **T1-41** with it |
| **D-17** | **The cradle deck is a ribbed lattice, not a solid slab.** `MCC_WALL`-wide perimeter frame + interior X/Y ladder ribs on a ~22 mm grid at `MCC_CRADLE_RIB_T = 3.0`, full deck height, no top plate — the device rests on rib top edges. Deck **height** and **footprint** are unchanged (both derived, §1/§7). Saves ≈46,000 mm³ (compact, ≈16 % of the base) / ≈66,000 mm³ (plus, ≈21 %); `bbox` must not move on any SKU. Brings T1-39/T1-40/T1-41. | Architect-derived from issue #29, gated rev 9 | **fixed**; the §7 row it replaces was never implemented |
| **D-18** | **The external fan switch is a FLUSH, fully-recessed actuator in a locally thickened +X wall pad — and it ships on the `plus` family only.** (1) `recess_t` is derived from the actuator's proud height, not chosen (T1-44a); the wall gains an internal pad rather than an external guard, so no envelope moves (the D-13 pattern). (2) The part is a row in `MCC_SWITCHES`, not a hard-coded struct — three candidates are recorded in `knowledge/components/switches.md` and swapping is a data edit. (3) `switch_y` is **solved** between the fan reservation and the corner lid fastener's two obstructions (§5), never a fixed offset. (4) The compact family's feasible interval is **empty**; compact variants set `["fan_switch", false]` explicitly until the user rules otherwise. **`fan_y` does not move** — R20 stays closed, and the ⌀20.2 IP65 candidate stays recorded-but-unplaced. | Architect-derived from issue #32, gated rev 11 | **fixed** in intent; every `MCC_SWITCHES` figure is `assumed` until **M17**, and (4) is open to the user (`architecture.md` §12 Q19) |
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

### Rev-6 addendum (2026-09-08) — constants for the aperture ruling

All five are new; all are `assumed` (they are print-process figures, not sourced dimensions) and all
belong in the **"Patch-wall layout"** section of `constants.scad`, after `MCC_PANEL_BEZEL_T`. None of
them changes `L`, `W`, `H`, the plate size, the slot pitch or any fixing position — the rev-6 ruling
is shape-only.

| Constant | Value | Purpose / where used |
|---|---|---|
| **`MCC_APERTURE_BRIDGE_MAX`** | **NEW — 10.0** | The one place `architecture.md` §5's "no unsupported horizontal span over 10 mm" becomes a number instead of prose. Used by T1-34a (window apex) and available to T1-31. Do **not** duplicate the literal `10.0` in `shell.scad` or `fasteners.scad` |
| **`MCC_APERTURE_SELF_SUPPORT_MAX_D`** | **NEW — 10.0 `assumed`** | Round-hole diameter below which a horizontally-printed hole needs **no** teardrop. Same 10 mm span rule read as a diameter. Used by T1-34a to justify plain-circle boss reliefs (`d_rel = 8.88`) |
| **`MCC_APERTURE_CAP_RISE`** | **NEW — 0.4 `assumed`** | How far the truncated-teardrop cap sits above the body circle's top, mm. `cap_h = d_win/2 + MCC_APERTURE_CAP_RISE`. Chosen as the smallest rise that still hides the cap behind the plate (`cap_h > mcc_cutout_d/2`, margin 0.7 mm) while keeping `w_flat` under `MCC_APERTURE_BRIDGE_MAX`. Calibrate with `neutrik-tile` |
| **`MCC_APERTURE_RELIEF_INTRUSION_MAX`** | **NEW — 1.5 `assumed`** | Maximum radial intrusion of a boss relief inside the plate's own cutout silhouette, mm — the numeric form of "the D slots must read as exactly round". Actual worst case today 1.235 mm (`NE8FDP-B`). T1-34b |
| **`MCC_APERTURE_LIP_WEB_MIN`** | **NEW — 2.0** | Minimum lip material between any part of a window and the plate's edge, mm. `fdm-rugged-enclosure-guidelines.md:127`. T1-34c |
| **`MCC_INSERT_BORE_EXTRA`** | **NEW — 0.5 `assumed`** | Extra bore depth past a heat-set insert's own length so the insert seats fully, mm. Replaces the bare `+ 1` literal in `mcc_neutrik_d_bosses()`. T1-35 |
| **`MCC_PLATE_RIM_W`** | **NEW — 6.0** | The plate's rim (border) width. It is the *same* number in three places today — `mcc_panel_plate()`'s `rim_w = 6` default, `_mcc_patch_wall_aperture()`'s local `rim_w = 6`, and the literal `6` passed to `_mcc_patch_wall_fixing_bosses()` — across two L2 files, and it feeds `mcc_panel_fixing_pos()`. That is a §3 "no magic numbers in L2" deviation and the exact drift hazard that produced **D6**. Name it once and pass it |

### Rev-8 addendum (2026-09-09) — the fan-power decision (D-14)

| Constant | Value | Purpose / where used |
|---|---|---|
| **`MCC_PANEL_PARTS["DBA-BL-B"].hole_d`** | **CHANGED — `0` → `24.0`** (`constants.scad:673`) | §2.5.1. Everything else in that row stays: `depth 3.2`, `max_panel_t 4.0`, `plug_len 0`, `bend 0`, `kind "blank"`, `confidence "drawing"`. Confidence stays `drawing` because 24.0 is the sourced D-series standard hole (`knowledge/neutrik/d-series-cutout.md:36`), not an invention |
| **`MCC_PLUG_AXIAL` — new row `["blank", 0]`** | **NEW — 0** (`constants.scad:432-440`) | Defensive. `mcc_plug_axial()` accepts a *part number* as well as a kind and resolves it via `mcc_panel_kind()`; `"DBA-BL-B"` resolves to `"blank"`, which is **not** a row today, so any future caller passing the part asserts out. No current caller does — `shell.scad:374` passes the port's `kind` — so this is a trap-closer, not a fix |
| **`MCC_PLUG_AXIAL` — row `["minidin8", …]`** | **NOT ADDED — the figure is `unknown`** | **R23 / M12.** Deliberately withheld: too small and T1-18(c) lies, too large and it fails `pro-convert-hdmi-plus` + `-sdi-plus` on a number nobody measured. Add it only once M12 lands, together with the T1-18(c) scope change below |
| **T1-18(c) scope** | **NOT CHANGED YET** (`shell.scad:373`) | It filters `mcc_ports_external(dev)`, so an *internally cabled* port is invisible to it. That was correct while `panel:"none"` meant "not cabled"; D-14 breaks the equivalence. The fix (filter on "has a non-zero axial term" rather than on `panel`) needs every port `kind` to have a `MCC_PLUG_AXIAL` row — i.e. it is gated on M12 too. **Recorded, not implemented** |
| **Thermoswitch height budget** | **≤ 8.8 mm** (plus) / **≤ 8.85 mm** (compact), derived: `H_int − mcc_cradle_deck(dev) − dev_h − MCC_LID_CLEAR` = `45 − 10.8 − 23.4 − 2.0` | **A sourcing constraint, not a constant.** The KSD9700's package is `unknown` (`poe-splitter-verification.md:172`), so nothing is modelled and nothing is asserted; the number goes on the BOM row and into M11. Optionally expose it as a derived, echoed field of `mcc_case_layout()` — that is free and self-documenting |
| **Cable-management geometry** | **none added** | No zip-tie anchor, clip, channel or switch pocket. Free end-zone volume is already reserved; cable dressing stays the adhesive tie base at `BOM.md:67`. A printed anchor would be a new `mounts.scad` floor feature positioned from unmeasured cable geometry, guarded by a `mcc_floor_keepout()` pairwise assert that does not exist yet (**D16**). Deferred with an explicit trigger — see `architecture.md` §14 rev-8 verdict |

**Explicitly NOT added: `MCC_APERTURE_TOP_OPEN`.** The top-open (U-notch) aperture is rejected, not
parameterised — a flag for a rejected topology is an invitation to re-open a settled decision and to
ship an untested second geometry path. §15 ruling 2026-09-08b.

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

---

## Ruling 2026-09-08b — user feedback on the connector openings (rev 6)

**Trigger.** The user reviewed the first rendered case (`models/pro-convert-for-ndi-to-hdmi`) in a
3D viewer and rejected the patch-wall connector openings: *"the 4 D-slots must be exactly round — not
the weird round/diamond-like shape they have now. As they are now there is no place to screw the
D-connectors down."*

**What the user was actually looking at.** The rev-5 §2.5 window: `hull()` of the ⌀24.4 body circle
and the two ⌀8.88 rear-boss reliefs at `(∓9.5, ±12)` — a 27.9 × 32.4 mm diagonal blob through the
3 mm structural lip (`lib/mcc/shell.scad` `_mcc_patch_wall_window()`). Because that blob is *narrower
than the plate's own D cutout along the two diagonal flanks*, its outline shows through every plate
hole. The plate itself, 2.0 mm behind the plate face with the real round cutouts, the ⌀3.4 screw
holes and the M3 rear bosses, is geometrically correct and correctly placed — but it is not what the
eye lands on.

**Verdict — the complaint is upheld on all three counts.**

| Count | Finding |
|---|---|
| "not exactly round" | **Upheld.** The `hull()` is the cause and it buys nothing: it is not more self-supporting than a plain circle (its top near the upper relief is still a horizontal-tangent arc), it removes ~35 % more of the 3 mm lip than a `union()`, and it removes it exactly where the plate's 2 mm flange seat needs backing (R4). **Fix: `union()` of a truncated-teardrop body circle and two plain relief circles.** §2.5, T1-34a–c |
| "no place to screw the D-connectors down" — the connectors | **Upheld, and it is a real mm-level defect, not a perception issue.** `mcc_neutrik_d_bosses()` bores `insert_len + 1 = 6.7 mm` into a `boss_h = 7` boss from the **rear** tip, leaving **0.3 mm of solid ASA across the screw axis** between the plate's ⌀3.4 clearance hole and the insert (`lib/mcc/neutrik.scad:117-120`). The screw physically cannot reach the insert. **Fix: continuous bore — insert bore from the rear tip, `MCC_M3_CLR_D` through to the front.** T1-35 |
| "no place to screw the D-connectors down" — the plate | **Upheld.** The four shell-side plate-retention bosses are **plain unbored solids** (`shell.scad` `_mcc_patch_wall_fixing_bosses()`, self-documented as a known deviation), so the plate cannot be fastened either. Deviation **D10**. Two contradictory comments in `shell.scad` describe this bore as both "not modelled" and "resolved locally" — reconcile them |

**The proposed top-open (U-notch) aperture: REJECTED.** The proposal — a full-plate-width notch from
the wall's top edge down to the plate's bottom edge, plate slid in from above, lid rim capturing it —
does eliminate windows by eliminating the roof, and I credit that it also restores a bezel on the
fourth side (the lid overhangs the recessed plate by `MCC_PANEL_BEZEL_T`). It is still the wrong
trade, for five reasons, any two of which would be enough:

1. **It breaks the patch wall's top continuity over 168 of 194 mm** (86 % of the wall). The base
   becomes a ⊐-channel in plan. Racking and torsional stiffness — the properties that carry the 1 m
   drop-onto-concrete requirement (`architecture.md` §1, `fdm-rugged-enclosure-guidelines.md`) — and
   ASA warp resistance on a 194 × 160 mm first layer (R9/R14) both depend on that closed rim. The
   plate cannot substitute: it is a separate part sitting on `MCC_CLR_SLIDE = 0.3` mm of slide
   clearance and transfers no reliable shear.
2. **It destroys the tongue-and-groove closure along the whole patch side.** D-07 puts the tongue on
   the base's inner top perimeter; with the notch there is no base material to carry it for 168 mm.
   Moving the tongue onto the plate's top edge makes the T&G fit inherit the plate's own slide
   clearance — a sloppy tongue is worse than no tongue, and the dust/ingress function is lost.
3. **Plate retention drops from 4 fixings to 2 + lid capture.** On a 168 mm plate carrying four
   connectors and their cable loads that is a real reduction, and the plate becomes removable only
   with the lid off (it is currently serviceable from outside).
4. **The `n_fast = 6` patch-wall mid-span lid fastener loses its gusset.** Its boss at
   `(x_gap, W/2 − MCC_FASTENER_INSET)` currently gussets into the patch wall floor-to-lid
   (`_mcc_gusset_web()`); above `z ≈ 5.7` there would be no wall to gusset into, leaving a
   free-standing 45 mm pillar in the connector bay.
5. **It forces `MCC_PLATE_H` off its derivation** (39.0 = `MCC_D_FLANGE[1] + 2·MCC_D_FLANGE_EDGE_MARGIN`,
   the D-06 veto) up to ~42.3 to reach the wall top, or leaves a 2.7 mm open slot along 168 mm.
   Either way it perturbs `H_int`/`z_conn_c`, and `H = 51.0` is a **fixed user decision**.

All of that to remove a shape that one word of code (`hull` → `union`) removes. **Do not build it,
and do not add a `MCC_APERTURE_TOP_OPEN` flag** — see §11's rev-6 addendum.

**Option C, also rejected (recorded so it is not re-opened): move the flange-fixing bosses from the
plate into the shell's structural lip.** This is the only way to make the lip window a single
*perfect* circle with no relief crescents at all, and it would put the connector fixing into
wall-backed 3 mm shell material instead of a 2 mm plate field (attractive against R4). Rejected
because it costs more than it buys: 8 heat-set inserts per case would have to be set blind from
inside a 45 mm-deep box against the patch wall instead of on a flat bench plate; it needs
non-stock ~M3×14 screws (flange + 2 mm plate + 3 mm lip + engagement) instead of the screws Neutrik
supplies; and it destroys the "bolt all four connectors to the plate on the bench, then drop the
loaded plate into the rabbet" sequence, which is what makes an `L − 26` mm plate handleable. The
residual 1.0–1.24 mm relief crescent is 2 mm behind the plate face and is covered by the fitted
connector body — an acceptable price. §2.5.

**Process finding (the reason a rejected design reached the user at all).** The only patch-wall view
in `exports/` that shows the plate is `preview-rear.png`, an oblique ISO. There is no straight-on
outside elevation of the assembled patch wall, and `scripts/build.py` renders no previews at all —
they are ad-hoc. A geometry whose acceptance criterion is "what the user sees from outside" must be
reviewed in exactly that view. **Required, `architecture.md` §9 Tier-4 / the `print-check` skill:
every case variant publishes a straight-on `−Y → +Y` orthographic elevation of the assembled patch
wall (base + `panel_placed`) before it is shown to the user.** Cheap, and it prevents a repeat.

**Not changed by this ruling:** `L`, `W`, `H`, `plate_l`, `MCC_PLATE_H`, slot pitch, slot assignment,
the stepped rabbet, `MCC_PANEL_BEZEL_T`, `mcc_panel_fixing_pos()`, and every §9 assert other than
T1-34/T1-35. This is a shape-and-bore ruling, not an envelope ruling — no golden bbox moves, though
volumes will.

---

## Ruling 2026-09-08c — record corrections carried by rev 7

### C1. §2.5 boss-relief positions were the plate's *authored* pattern, not its *placed* pattern

**Corrected in §2.5, §9 T1-34a and §9 T1-34d.** The plate is authored in the Neutrik front view with
its screw holes and rear bosses at local `(−9.5, +12)` / `(+9.5, −12)`; `case.scad` places it with
`rotate([-90,0,0])`, i.e. **local `(x, y)` → world `(x, z = −y)`**, so on the assembled case the
bosses are at **`(slot_x − 9.5, z_conn_c − 12)` and `(slot_x + 9.5, z_conn_c + 12)`**. Rev 6 wrote
`(∓9.5, ±12)` — the mirror. `lib/mcc/shell.scad` was corrected on **2026-09-08 (commit 2a7e0b0)**
after the user reported the mirrored pattern on the first rendered case; **the doc is now corrected
to match the code, and §2.5 carries an explicit frame rule** — *"the outside viewer's right is world
−X"* — so this is not re-derived a third time.

Why it survived every assert: the four `mcc_panel_fixing_pos()` points are symmetric about both
`x = 0` and `z = z_conn_c`, so T1-34c and T1-34d are numerically **invariant** under the mirror. The
defect is only visible in the head-on `−Y → +Y` elevation — the same view whose absence produced
D11. This is the second defect in a row that only that view catches; it is why §16.4 makes the
elevation a required per-PR artefact rather than a recommendation.

Residual: `lib/mcc/layout.scad:388-391` still builds T1-34d's relief pair from the mirrored
diagonal. Harmless today (invariant, above), latent the moment a fixing position becomes asymmetric.
**Deviation D14** — fix by publishing the relief pair once as a pure function in `layout.scad` and
calling it from both `layout.scad` and `shell.scad`. Not urgent, and **not** work for the seven
parallel branches.

### C2. D10 resolution — the plate-fixing bosses carry a genuine THROUGH-bore

**Accepted as the resolution of deviation D10** (`architecture.md` §13), recorded here so it is not
"corrected" back to a blind pocket by someone reading T1-35 literally.

- **What is built.** Each of the four patch-wall plate-fixing bosses
  (`_mcc_patch_wall_fixing_bosses()`, `lib/mcc/shell.scad:289-321`) is bored end to end:
  `MCC_INSERT_M3.hole_d` for `MCC_INSERT_M3.len + MCC_INSERT_BORE_EXTRA` = **6.2 mm** from the
  boss's **rear tip**, then `MCC_M3_CLR_D` for the remaining **0.8 mm** out through the front,
  plate-facing face. Both ends are open.
- **Why not the blind pocket T1-35's wording implies.** Manifold on the pinned OpenSCAD
  **2025.09.07** cannot union a *blind-bored* boss flush against a face of another solid: the boss
  comes back as its own disconnected component (`build.py check`'s `n_parts` = 1 + one per bored
  boss). Diagnosed by isolated bisection — it reproduces with the aperture entirely absent, at every
  overlap depth from `MCC_EPS` to 2 mm, and the add-then-cut-in-the-outer-`difference()` pattern
  used for the tripod/VESA floor bosses does **not** fix it. A plain unbored cylinder unions
  cleanly; any blind cavity breaks it. This is a toolchain robustness limit, not a modelling error,
  and the through-bore is the smallest change that renders `parts=1` and watertight.
- **Why it costs nothing by design.** Unlike `mcc_neutrik_d_bosses()`, this boss carries no other
  feature at its rear tip, so opening it changes no function.
- **Consequence, and it must reach the build sheet: the M3 heat-set insert is installed from the
  boss's INTERIOR (rear) tip**, i.e. from inside the open base before the lid goes on, with the
  soldering iron pointing +Y toward the patch wall. The screw enters from the *plate* side, through
  the plate's own ⌀3.4 clearance hole and the boss's 0.8 mm clearance section, into the insert.
  A 0.8 mm clearance lead-in is short: the screw must be started square, and **the insert must not
  be over-driven past the 6.2 mm bore** or it will protrude out of the front face and stand the
  plate off its seat. Add both notes to `BOM.md`'s assembly section and to `print-check`.
- **Scope.** This resolution is specific to the four shell-side plate-fixing bosses.
  `mcc_neutrik_d_bosses()` keeps its own two-diameter bore (insert from the rear tip, `MCC_M3_CLR_D`
  through to the panel-side face) — also open at both ends, for the same toolchain reason, and
  already the rev-6 fix.
- **T1-35 wording stands** ("no solid material anywhere on the screw axis between the bearing face
  and its insert"). A through-bore satisfies it strictly. Nothing in §9 changes.

### C3. BLOCKING library defect found while gating the seven SKUs: T1-18(c)

See **§16.3**. `lib/mcc/shell.scad:360-366` charges the BNC cable's *lateral* bend radius against the
*axial* +X end-zone budget, so the assert fires on all four BNC-ended SKUs. It is a library fix, it
is one constant plus one expression, it moves no geometry — and it must land **before** any of the
seven branches is opened.

---

## 16. Pre-implementation gate for the seven remaining SKUs (rev 7, 2026-09-08)

Scope: GitHub issues **#3–#9** — `pro-convert-hdmi-tx`, `pro-convert-sdi-tx`,
`pro-convert-hdmi-plus`, `pro-convert-sdi-plus`, `pro-convert-for-ndi-to-hdmi-4k`,
`pro-convert-for-ndi-to-sdi`, `pro-convert-for-ndi-to-aio`, built in parallel on seven branches
against the library as it stands after `models/pro-convert-for-ndi-to-hdmi`.

**Method.** Every number below is the mechanical output of `lib/mcc/layout.scad`,
`lib/mcc/shell.scad`, `lib/mcc/cradle.scad`, `lib/mcc/vents.scad` and `lib/mcc/constants.scad`
applied by hand to each device record — the same evaluation `mcc_case_layout()` and
`mcc_shell_base()` perform. **It has not been executed through OpenSCAD** (this gate ran without a
shell); every figure is reproducible from the cited expression, and the one *failing* assert
(§16.3) is arithmetic simple enough to re-check by inspection. The first act of the pre-flight
branch (§16.5) is to render all eight devices and confirm this table.

### 16.1 Fit-check table

Common to all seven: `H = 51.0`, `H_int = 45.0`, `ez_neg = 47` (rj45 27 + splitter 20, D-12),
`n_fast = 6` (every `L` > `MCC_LID_SPAN_MAX` 180), `plate_l = L − 26`, `z_conn_c = 25.5`,
`side_bolt_x = x_dev_c` and `side_bolt_z = 25.5` (every SKU still carries the `pos [0,0]`
placeholder, M1), `MCC_GAP_FAR = 16`, `MCC_SIDE_BOLT_PROUD = 0`.

| # | SKU | family | external ports (from the device file) | slot 1 (−X) | slot 2 | slot 3 | slot 4 (+X) | n | L × W × H | ez_neg / ez_pos | governing bay depth → `d_bay_free` | pitch | `x_dev_c` | fasteners |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| #3 | pro-convert-hdmi-tx | compact | `hdmi_in`(+X) · `usb_b`(−X) · `rj45`(−X) | **NE8FDP-B** `rj45` | **NAUSB-W-B** `usb_b` | **NAHDMI-W-B** `hdmi_in` | — | **3** | 193.9 × 159.85 × 51.0 | 47 / 40 | HDMI 75.65 → **70.65** | 62.950 | +3.50 | 6 |
| #4 | pro-convert-sdi-tx | compact | `sdi_in`(+X) · `usb_b` · `rj45` | **NE8FDP-B** | **NAUSB-W-B** | **NBB75DFGB** `sdi_in` | — | **3** | 194.9 × 158.80 × 51.0 | 47 / 41 | BNC 74.60 → **69.60** | 63.450 | +3.00 | 6 |
| #5 | pro-convert-hdmi-plus | plus | `usb_b`·`rj45`(−X) · `hdmi_in`·`hdmi_out`(+X) | **NE8FDP-B** | **NAUSB-W-B** | **NAHDMI-W-B** `hdmi_out` | **NAHDMI-W-B** `hdmi_in` | 4 | 210.5 × 166.35 × 51.0 | 47 / 40 | HDMI 75.65 → **70.65** | 47.500 | +3.50 | 6 |
| #6 | pro-convert-sdi-plus | plus | `usb_b`·`rj45` · `sdi_in`·`sdi_out`(+X) | **NE8FDP-B** | **NAUSB-W-B** | **NBB75DFGB** `sdi_out` | **NBB75DFGB** `sdi_in` | 4 | 211.5 × 165.30 × 51.0 | 47 / 41 | BNC 74.60 → **69.60** | 47.833 | +3.00 | 6 |
| #7 | pro-convert-for-ndi-to-hdmi-4k | plus | `usb_host`·`hdmi_out`(+X) · `usb_b`·`rj45`(−X) | **NE8FDP-B** | **NAUSB-W-B** `usb_b` | **NAUSB-W-B** `usb_host` | **NAHDMI-W-B** `hdmi_out` | 4 | 210.5 × 166.35 × 51.0 | 47 / 40 | HDMI 75.65 → **70.65** | 47.500 | +3.50 | 6 |
| #8 | pro-convert-for-ndi-to-sdi | compact | `sdi_out`·`usb_host`(+X) · `usb_b`·`rj45`(−X) | **NE8FDP-B** | **NAUSB-W-B** `usb_b` | **NAUSB-W-B** `usb_host` | **NBB75DFGB** `sdi_out` | 4 | 194.9 × 158.80 × 51.0 | 47 / 41 | BNC 74.60 → **69.60** | 42.300 | +3.00 | 6 |
| #9 | pro-convert-for-ndi-to-aio | compact | `hdmi_out`·`sdi_out`(+X) · `usb_b`·`rj45`(−X) | **NE8FDP-B** | **NAUSB-W-B** | **NAHDMI-W-B** `hdmi_out` | **NBB75DFGB** `sdi_out` | 4 | 194.9 × **159.85** × 51.0 | 47 / 41 | **HDMI** 75.65 → **70.65** | 42.300 | +3.00 | 6 |

Notes on the slot column, all mechanical consequences of §3 and none of them a choice:

- **`NE8FDP-B` is slot 1 and `NAUSB-W-B` is slot 2 on all seven.** Every SKU's −X block is exactly
  `{rj45, usb_b}`, and `rank(rj45) = [10, 25] > rank(usb_b) = [8, 20]`. This is the cross-check §3
  demands: the etherCON sits at the same end as the reserved PoE-splitter bay that must be fed from
  it.
- **`hdmi_in` outboard of `hdmi_out` on HDMI Plus, `sdi_in` outboard of `sdi_out` on SDI Plus.** The
  two +X ports tie on `[bend, plug_len]`; the tie-break is `pos[0]` ascending, and the `_in` port is
  at `pos[0] = −22` on both. So the **IN** connector takes the outermost slot 4.
- **AIO puts the BNC outermost and the HDMI inboard** (`bend` 40.6 > 15), so slot 3 = `NAHDMI-W-B`.
- **Derived positions** (needed by the goldens; all from `mcc_case_layout()`):
  `x_gap` (patch-wall mid fastener) = **0** on every 4-slot SKU, **−31.475** on HDMI TX and
  **−31.725** on SDI TX (odd slot count → even gap count → the −X tie-break, §6);
  `x_far_mid` = **−12.64** where `x_dev_c = +3.50`, **−13.14** where `x_dev_c = +3.00`.
- **No `DBA-BL-B` anywhere.** See §16.2.

### 16.2 Expected assert outcomes, and the special handling each SKU was checked for

**Constant across all seven** (they depend only on `constants.scad`, so they are pass/fail once, not
per SKU): T1-34a (`w_flat` 9.30–9.48 ≤ 10.0; `d_rel` 8.88 < 10.0; `cap_h` clears
`mcc_cutout_d/2` by 0.7) ✓ · T1-34b (intrusion **1.235 mm** for `NE8FDP-B`, **1.035 mm** for the
23.6-class parts, ≤ 1.5) ✓ · T1-34c Z (`12 + 4.44 + 2 = 18.44 ≤ 19.5`, **1.06 mm** spare) ✓ ·
T1-34c X (spare is `(plate_l − span)/2 − 15.94 = 21 − 15.94 =` **5.06 mm**, independent of `L`) ✓ ·
T1-34d (**3.18 mm**) ✓ · T1-35 (`6.2 + 0.8 = 7.0 = boss_h`) ✓ · T1-25 (0.5 mm spare) ✓ ·
T1-26 / T1-29 (**equality, 19 ≤ 19, zero slack by design**) ✓ · T1-31 (8.5 ≤ 10) ✓ ·
T1-33 (`2.0 + 1.0 ≤ 3.0`; `1.6 + 0.5 ≤ 2.2`) ✓ · T1-11 (39.0 ≥ 36.28) ✓ · T1-15 (45 ≥ 44) ✓ ·
T1-19 (no `mcc_vents()` call for `[0,1,0]`) ✓ · T1-05 (no `MINIDIN8` port on any SKU) ✓ ·
T1-22 (one `tripod_1_4_20` on `[0,-1,0]` per device — all eight files fixed in commit bb1497f) ✓.

**Per SKU:**

| Assert | #3 hdmi-tx | #4 sdi-tx | #5 hdmi-plus | #6 sdi-plus | #7 ndi-hdmi-4k | #8 ndi-sdi | #9 ndi-aio |
|---|---|---|---|---|---|---|---|
| T1-01/02/03/04 (faces, `n_slots ≤ 4`, bijection) | ✓ 3 | ✓ 3 | ✓ 4 | ✓ 4 | ✓ 4 | ✓ 4 | ✓ 4 |
| T1-06 `pitch ≥ 32` | ✓ 62.95 | ✓ 63.45 | ✓ 47.50 | ✓ 47.83 | ✓ 47.50 | ✓ 42.30 | ✓ 42.30 |
| T1-07 / T1-08 (bay depth, lateral bend) | ✓ 70.65 ≥ 15 | ✓ 69.60 ≥ 40.6 | ✓ | ✓ 69.60 ≥ 40.6 | ✓ | ✓ 69.60 ≥ 40.6 | ✓ 70.65 ≥ 40.6 |
| T1-09 `ez_neg` incl. splitter term | ✓ 47 | ✓ 47 | ✓ 47 | ✓ 47 | ✓ 47 | ✓ 47 | ✓ 47 |
| T1-10 `plate_l` | ✓ 167.9 | ✓ 168.9 | ✓ 184.5 | ✓ 185.5 | ✓ 184.5 | ✓ 168.9 | ✓ 168.9 |
| T1-13 lid boss → flange edge (`pitch/2 − 13` vs 6.14) | ✓ 18.48 | ✓ 18.73 | ✓ 10.75 | ✓ 10.92 | ✓ 10.75 | ✓ **8.15** | ✓ **8.15** |
| T1-14 `H_int ≥ deck + dev_h + 2` | ✓ 45 ≥ 36.15 | ✓ | ✓ 45 ≥ 36.2 | ✓ | ✓ 45 ≥ 36.2 | ✓ | ✓ |
| **T1-18(c) +X axial cable vs fan bay** | ✓ **0.00 slack** | ❌ **FAIL −14.60** | ✓ **0.00** | ❌ **FAIL −14.60** | ✓ **0.00** | ❌ **FAIL −14.60** | ❌ **FAIL −14.60** |
| T1-21 bbox ≤ 250 | ✓ 56.1 spare | ✓ 55.1 | ✓ 38.5 | ✓ 38.5 | ✓ 38.5 | ✓ 55.1 | ✓ 55.1 |
| T1-23 / T1-23b (vent keep-outs) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T1-24 pad on device flank (`18 ≤ dev_h − 2`) | ✓ 21.3 | ✓ 21.3 | ✓ 21.4 | ✓ 21.4 | ✓ 21.4 | ✓ 21.3 | ✓ 21.3 |
| T1-27 far-flank ribs ≥ 3, clear of `x_bolt` | ✓ **4** | ✓ 4 | ✓ 4 | ✓ 4 | ✓ 4 | ✓ 4 | ✓ 4 |
| T1-28 splitter bay vs −X cable envelope | ✓ 27 mm clear | ✓ | ✓ 27 | ✓ | ✓ 27 | ✓ | ✓ |
| T1-32 case 1/4"-20 stack `13.7 ≤ z_dev_lo` | ✓ **0.15** | ✓ 0.15 | ✓ **0.10** | ✓ 0.10 | ✓ **0.10** | ✓ 0.15 | ✓ 0.15 |
| VESA boss vs splitter bay (`mounts.scad:89`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T1-30 net intake area vs 1134 mm² *(test-only, see below)* | 1174 | **1153** | 1325 | 1325 | 1325 | **1153** | 1174 |
| `undef` in the layout struct | none | none | none | none | none | none | none |

No `undef` is produced on any SKU: `x_gap` is defined because `gap_clearance ≥ 6.14` everywhere, and
`x_far_mid` is defined because both `x_bolt ± 16.14` candidates are inside the fastener ring.

**Special handling, item by item:**

1. **Plus-family first use — `shell.scad` has never rendered a `plus` device.** Audited for
   compact-only assumptions and there are **none**. `_mcc_h_int()` is `MCC_PANEL_BAND + MCC_PLATE_H +
   MCC_PANEL_BAND` = 45.0 on every family; every family-varying quantity (`L`, `W`, `deck`,
   `y_dev_c`, `z_dev_lo`) comes from `mcc_case_layout()` / `mcc_cradle_deck(dev)`; a grep of
   `lib/mcc/**` outside `devices/` finds **no** literal `100.9`/`60.2`/`23.3`/`117.5`/`66.7` and no
   branch on `mcc_dev_family()` — family is pure data, exactly as §4 of `architecture.md` intends.
   Two plus-specific tight spots to know about, both passing:
   **(a) T1-32 has 0.10 mm of slack** (`13.7 ≤ z_dev_lo = 13.8`) because the plus device is 0.1 mm
   taller, so its deck is 0.05 mm shallower. Any upward revision of `MCC_INSERT_1_4_20.len` (12.7,
   `assumed`) breaks the three plus SKUs first. **(b)** the ⌀38 fan aperture at
   `fan_y = y_dev_c = −30.825` spans `y ∈ [−49.825, −11.825]`, clear of both walls.
2. **BNC-only ends (SDI TX #4, NDI to SDI #8, NDI to AIO #9's outer slot).** Slot assignment,
   `ez_pos = 41`, `d_bay_free = 69.60 ≥ 40.6` all correct. **The only problem is T1-18(c)** — §16.3.
3. **Two BNC on one end (SDI Plus #6, the loop-out).** Slots 3 and 4, pitch 47.83, both inside a
   69.60 mm-deep bay: the two 40.6 mm bend envelopes are 47.83 mm apart in X and cannot interfere.
   `ez_pos = 41` is `max(bnc, bnc)`, unchanged. **No library change** beyond §16.3.
4. **The 4K decoder's internal fan / top grille (R5, `architecture.md` §12 Q10 — "do not seal the
   device's top grille").** **Guaranteed by construction, and here is what guarantees it:** the
   plenum over the device is `MCC_FLOOR_T + H_int − z_dev_hi = 48 − 37.2 =` **10.8 mm** on the plus
   chassis (10.85 compact), and **nothing is drawn in it.** `mcc_cradle()`'s deck slab lives entirely
   below `z_dev_lo`; each far-flank rib's solid body tops out at `z_dev_lo + MCC_CRADLE_RIB_H =
   22.8`, i.e. 14.4 mm below the device's top face, and sits in `y ∈ [y_dev_lo − 16, y_dev_lo]`,
   *beside* the device, never over it; patch-flank ribs are gated on `|x| > plate_l/2 − 3` and are
   emitted on **no** current SKU; `mcc_shell_lid()` is a flat 3 mm slab whose only downward feature
   is the perimeter T&G groove. T1-14 is the standing guard (8.8 mm of slack on plus). The far-wall
   exhaust band `z ∈ [32, 44]` sits *above* `z_dev_hi = 37.2` for its upper half, i.e. it opens into
   the plenum — which is the right place for it. **No cradle or lid change is needed for #7.**
   *Open, and a user decision, not an architect one:* R5 says the fan is **not optional for the 10 W
   Plus models**, yet #5/#6/#7 will inherit `["fan", false]` if they are copied from
   `models/pro-convert-for-ndi-to-hdmi/case.scad`. Ask the user before those three PRs merge; it is
   one line of `cfg` plus a BOM row, never a library change.
5. **AIO with HDMI + BNC on the same end (#9).** `ez_pos = max(40, 41) = 41` (BNC governs `L`);
   `d_bay_free = 70.65` (**HDMI** governs `W`) — #9 is the only SKU where the two are governed by
   *different* parts, which is why its `W` is 159.85 while #8's is 158.80 at the same `L`. Watch it
   in review: a developer "simplifying" `W` to match #8 breaks the HDMI bay by 1.05 mm.
6. **TX with 3 slots, blank policy (#3, #4).** `n_slots = len(mcc_ports_external(dev)) = 3`, and
   `mcc_slot_assignment()` fills all three (block A → slots 1–2, block B → slot 3). **No `DBA-BL-B`
   is instantiated anywhere in this repo today**, which is the intended outcome — the blank exists
   for a caller that pads `n_slots`, and nothing does. The plate and aperture handle 3 slots
   **symmetrically**: `slot_x[i] = −span/2 + i·(span/2)` gives exactly `[−span/2, 0, +span/2]`, so
   the plate, the three windows and the three flange seats are symmetric about `x = 0`; the
   asymmetry that *does* appear is `x_gap = −31.475 / −31.725`, which is §6's deliberate −X
   tie-break for an even number of gaps, not a defect. `mcc_aperture_window()`'s `DBA-BL-B` branch
   stays dead code — leave it, do not delete it in a variant branch.

### 16.3 BLOCKING library change — T1-18(c) fails on every BNC-ended SKU

**The finding.** `lib/mcc/shell.scad:360-366` builds the +X end zone's *axial* term as

```
axial = (kind == "bnc") ? mcc_plug_len("NBB75DFGB")            // = 40.6
                        : mcc_dev_side_allow(kind) - mcc_bend_envelope(panel)
assert(x_dev_hi + max(axial) <= L/2 - MCC_WALL - fan_env_depth)      // fan_env_depth = 10 + 5 = 15
```

which reduces, since `L = 53 + dev_l + ez_pos` and `x_dev_hi = −L/2 + 50 + dev_l`, to the clean
condition **`ez_pos ≥ 15 + axial`**. Evaluated:

| SKU | `axial` | required `ez_pos` | actual `ez_pos` | result |
|---|---|---|---|---|
| #3 hdmi-tx, #5 hdmi-plus, #7 ndi-hdmi-4k (and the shipped NDI to HDMI) | 25.0 (`hdmi_a`: 40 − 15) | 40.0 | 40 | **pass, 0.00 mm slack** |
| #4 sdi-tx, #6 sdi-plus, #8 ndi-sdi, #9 ndi-aio | **40.6** (`bnc`) | **55.6** | 41 | ❌ **fail by 14.60 mm** |

Worked example, SDI TX: `x_dev_hi = 53.45`, `LHS = 53.45 + 40.6 = 94.05`,
`RHS = 97.45 − 3 − 15 = 79.45`. The same 14.60 mm shortfall appears on all four.

**Why the assert is wrong rather than the envelope.** `MCC_PANEL_PARTS`'s `plug_len` for
`NBB75DFGB` is **40.6, which is the Belden 4855R bend radius re-used** — `constants.scad:588-592`
says so in as many words ("for BNC the bend radius genuinely governs both axial and lateral
clearance"). T1-18 was re-scoped in rev 5 precisely because charging a lateral allowance against an
axial budget is double-counting ("the bend is spent in Y, turning toward the patch wall, not in X").
Clause (c) then reintroduced the double-count through the back door, with the doc's own hedge
("clause (c) cannot be evaluated honestly there; use `mcc_plug_len("NBB75DFGB")` as the interim
axial term"). That interim term is not honest — it is 40.6 mm of *bend radius* pretending to be a
plug body — and it is what fails.

**Options considered.**

| Option | Verdict |
|---|---|
| **(a) Give the axial term its own `assumed` table entry.** Add `MCC_DEV_AXIAL_PLUG` (or extend `MCC_DEV_SIDE_ALLOW` with an `axial` column) with `bnc → 25.0 assumed (M6)`, `hdmi_a → 25.0`, `rj45 → 17`, `usb_a`/`usb_b` → 9, and make T1-18(c) read it. BNC-ended SKUs then need `ez_pos ≥ 40` and have 41 → **1.0 mm slack**. HDMI-ended SKUs are unchanged (still exactly 0.00). | **ADOPTED.** It is the only option that fixes the double-count instead of paying for it; it moves **no geometry**, so `tests/golden/pro-convert-for-ndi-to-hdmi.*.json` do not change; and it puts the missing figure where M6 can replace it. The 25.0 is `assumed`, deliberately the same class of placeholder as HDMI's assumed straight-plug axial length, and it must be tagged as such. |
| (b) Compute the axial term uniformly as `allow − bend` for BNC too. | **Rejected.** It yields `41 − 40.6 = 0.4 mm` of axial plug body, which is not merely conservative, it is false — a BNC male plug body is certainly longer than 0.4 mm. An assert that passes on a figure everyone knows is wrong is worse than one that fires. |
| (c) Grow `ez_pos` on BNC ends to 55.6. | **Rejected.** `L` → 209.5 compact / 226.1 plus on four SKUs; plus bed margin falls from 44.5 to 29.9 mm; and it contradicts §4's own `ez` table, which sources 41 from a *bend radius*. Re-sizing four cases on a number that is admittedly not an axial figure is the wrong direction. |
| (d) Downgrade T1-18(c) to an `echo()` warning. | **Rejected.** It is the *only* guard against the fan bay and the +X cable bundle occupying the same volume, and the HDMI SKUs pass it with exactly zero slack — precisely the situation an assert exists for. |

**Ruling.** Option (a). **This is a library change, therefore it is BLOCKING for parallel work.** It
touches `lib/mcc/constants.scad` and `lib/mcc/shell.scad` — two files all seven branches depend on
and none of them may edit — so it must be done **once, first, on a single pre-flight branch**, merged
to `main`, and the seven branched from the result. Do **not** start #4/#6/#8/#9 before it lands, and
do not "work around" it in a `models/**` file: a variant that overrides a library assert is exactly
the abstraction leak §4's acceptance test exists to catch.

**Also record:** T1-18(c) passes with **0.00 mm** of slack on every HDMI-ended SKU. When `depth-mockup`
(M6) measures the straight HDMI plug and it comes back above 25 mm, T1-18(c) fails on #3, #5, #7 and
the shipped NDI to HDMI *simultaneously*, and the answer will then be `L`, not the assert. That is
the intended failure mode; nobody may pre-empt it by shaving `fan_env_depth`.

### 16.4 Non-blocking findings the seven developers must be told about

| # | Finding | Consequence for the seven |
|---|---|---|
| **D12** | **`cfg["external_ports"]` is inert.** `mcc_slot_assignment()` and `mcc_case_layout()` derive `n_slots` and every slot's part **solely** from `mcc_ports_external(dev)`; a grep of `lib/**` finds `external_ports` only in doc comments. The `new-case-variant` skill's promise that omitting an id "gets a DBA-BL-B blank instead of the live connector" is **not implemented**. | List every external port id in the variant config for documentation/BOM parity with the first case — but **do not try to blank or drop a port by omitting it**; it will silently do nothing. Any change here is a library change, out of scope for these seven. |
| **D13** | **The `new-case-variant` skill is stale and will actively mislead a Sonnet-tier developer.** It states that `shell.scad`/`cradle.scad`/`mounts.scad`/`vents.scad`/`panel.scad`/`ports.scad` "do not exist yet", and its template calls `mcc_shell(family=…, half="base")` and `mcc_panel(device=…, face=[1,0,0])` — **signatures that exist nowhere in the library.** The real API is `mcc_shell_base(dev, cfg)`, `mcc_shell_lid(dev, cfg)`, `mcc_panel_plate(size, slots)`, `mcc_panel_plate_dims(dev)`, `mcc_slot_assignment(dev)`, `mcc_case_layout(dev, cfg)`. | **Fix the skill on the same pre-flight branch as §16.3**, before any developer reads it. Until it is fixed, the normative template is `models/pro-convert-for-ndi-to-hdmi/case.scad` — copy that file, not the skill. |
| **D14** | `lib/mcc/layout.scad:388-391` evaluates T1-34d against the **mirrored** relief diagonal (ruling C1). Numerically invariant today. | Nothing. Do not "fix" it in a variant branch — it is a library change. |
| **D15** | **T1-30 (intake free area vs the fan aperture) is not an in-model assert.** It lives only in `tests/test_shell.scad:53`, hard-wired to NDI to HDMI, so the other seven SKUs ship with **no** intake-area check. Hand-evaluated from `_mcc_vent_slot_centers()` the seven land at **1174 / 1153 / 1325 / 1325 / 1325 / 1153 / 1174 mm²** against the 1134 mm² threshold — all pass, but **#4 and #8 have only ~19 mm² (1.6 %) of margin**, because their `W = 158.80` loses one whole slot off the −X end wall's run (27 slots instead of 28). | Nothing in a variant branch. Wiring T1-30 into `mcc_shell_base()` is recommended on the pre-flight branch **only after** a render confirms all eight devices pass; if a BNC compact SKU actually fails, that is a real thermal finding — escalate to the user, do not relax `MCC_VENT_AREA_RATIO`. |
| **D16** | `mcc_floor_keepout()` publishes the floor features, but **`mounts.scad` never asserts pairwise non-overlap**, although `layout.scad:240-243` and §7.1 both say it does. `MCC_FLOOR_FEATURE_MIN_SEP` is unused. | Nothing in a variant branch. Log for a later single-branch fix. |
| — | **Cable routing to the *inboard* +X slot.** On every 4-slot SKU, slot 3 sits at `+span/6`, ~32 mm inboard of `x_dev_hi`, so its lead makes the S-bend §3 warns about. That is fine for `usb_host` (#7, #8) but lands on a **stiff** cable on **#5** (`hdmi_out`), **#6** (`sdi_out`, the stiffest in the repo) and **#9** (`hdmi_out`). | Not a blocker and not a geometry change — it is a **measurement** gate. `depth-mockup` (M6) must be built and the S-bend tried with a real BNC and a real HDMI lead **before #5/#6/#9 are printed**. Say so in each PR. |

### 16.5 Parallel-work rules for the seven branches

**Pre-flight, once, on a single branch, merged before any of the seven is opened:**

1. §16.3's T1-18(c) fix (`constants.scad` + `shell.scad`). **Blocking.**
2. D13's `new-case-variant` skill rewrite. **Blocking in practice** — seven Sonnet developers reading
   a template with non-existent signatures is a guaranteed seven-way rework.
3. Optional on the same branch: D15's T1-30 assert, D14's shared relief-position function, D16's
   floor-overlap assert. All three are library-wide; none may be done inside a variant branch.
4. Render all eight devices and confirm §16.1/§16.2 against the actual OpenSCAD output. If any figure
   in §16.1 disagrees with the render, **the render wins** and §16 is corrected — this table was
   derived by hand.

**Files a variant branch MAY touch — and nothing else:**

- `models/<slug>/case.scad` *(new; a copy of `models/pro-convert-for-ndi-to-hdmi/case.scad` with the
  device include, `MCC_DEV_*` symbol, `external_ports` list and the echo strings changed — nothing
  structural)*
- `tests/golden/<slug>.base.json`, `<slug>.lid.json`, `<slug>.panel.json` *(new; generated by
  `python scripts/build.py golden --update`, numbers eyeballed against §16.1's `L × W × H` before
  committing)*
- **only its own `### <slug>` block** under `## Per-variant BOM` in `BOM.md` — every slug already has
  a section, so this is an edit inside one existing block, never a restructure
- **only its own status row** in `README.md`, if that row exists

**Files a variant branch MUST NOT touch:**

- **anything under `lib/mcc/`** — that is the whole point of §4's acceptance test. If a SKU appears to
  need a library edit, **stop and report to the teamlead**; do not edit and do not improvise geometry
  in `models/**` (`new-case-variant`'s stop-and-report gate).
- another SKU's `models/**` or `tests/golden/**`
- `BOM.md`'s common/coupon/purchase sections or another slug's block
- `README.md` structure or another SKU's row; `CLAUDE.md`; `.claude/knowledge/**`;
  `.claude/skills/**`; `scripts/**`; `.github/**`; `docs/plans/**`
- `tests/test_*.scad` — shared, and a seven-way conflict magnet

**Required render/preview set per PR** (both are gates, not nice-to-haves):

1. an **ISO** view of the assembled case (`part="assembly"`), and
2. a **straight-on `−Y → +Y` orthographic elevation of the patch wall** with the plate in place
   (`part="base"` + `part="panel_placed"`).

The elevation is mandatory because it is the *only* view in which the two defects this repo has
already shipped to the user — the `hull()`ed blob (D9) and the mirrored boss reliefs (ruling C1) —
are unambiguous. A PR without it is not reviewable. Both views go in the PR body, together with the
`build.py all` result and the golden `L × W × H` for comparison against §16.1.

**Merge order — compact first, then Plus:**

```
pre-flight (T1-18(c) + skill)  ->  #3 hdmi-tx  ->  #4 sdi-tx  ->  #8 ndi-sdi  ->  #9 ndi-aio
                              ->  #5 hdmi-plus ->  #6 sdi-plus ->  #7 ndi-hdmi-4k
```

Rationale: the compact family is the *proven* geometry (the shipped NDI to HDMI is compact), and #3
is the smallest delta of all seven — 3 slots, no BNC, HDMI-ended. Landing it first proves the
copy-the-thin-assembly path end to end. #4 then proves the BNC path with the §16.3 fix in place, and
#8/#9 add nothing new. **The plus family is genuinely new ground** (`shell.scad` has never rendered
one), so its three SKUs merge last, after the compact four have confirmed that no library change was
needed — and #5 (HDMI-ended, the closest plus analogue to a proven compact case) goes before #6 and
#7. Branches may all be *developed* in parallel; it is the **merge** that is ordered, so that if the
plus family does surface a library problem, it surfaces against a `main` that is already known good.

---

### 16.6 Per-SKU consequences of D-14 (rev 8, 2026-09-09)

All eight SKUs exist on `main`. This table is what actually changes per SKU. **Every `L × W × H`,
every `pitch`, every `x_dev_c`, every fastener position in §16.1 is unchanged** — `DBA-BL-B`'s
`depth`/`plug_len`/`bend` are untouched, so `d_bay_free`, `W` and the slot pitch cannot move, and
end zones are keyed by port `kind`, not by `panel`, so `L` cannot move either.

| SKU | family | `fan` | Fan 5 V source | Slot 3 | Slot order | Envelope | Goldens touched |
|---|---|---|---|---|---|---|---|
| `pro-convert-for-ndi-to-hdmi` | compact | `false` | — (host port simply unused) | `NAUSB-W-B` → **`DBA-BL-B`** | **unchanged** | **unchanged** 193.9 × 159.85 × 51.0 | `.panel`, `.base`, `.base_fan` |
| `pro-convert-for-ndi-to-sdi` | compact | `false` | — | `NAUSB-W-B` → **`DBA-BL-B`** | **unchanged** | **unchanged** 194.9 × 158.80 × 51.0 | `.panel`, `.base` |
| `pro-convert-for-ndi-to-hdmi-4k` | plus | `true` | **USB-A host** (R21, M9) | `NAUSB-W-B` → **`DBA-BL-B`** | **unchanged** | **unchanged** 210.5 × 166.35 × 51.0 | `.panel`, `.base` |
| `pro-convert-hdmi-plus` | plus | `true` | **Mini-DIN-8 pin 8** (R22, M10) | — | — | unchanged **unless M12 forces `fan_y`** | none from the blank; `.base` only if `fan_y` moves |
| `pro-convert-sdi-plus` | plus | `true` | **Mini-DIN-8 pin 8** | — | — | same | same |
| `pro-convert-hdmi-tx` | compact | `false` | (Mini-DIN-8, if a fan is ever fitted) | — | — | unchanged | none |
| `pro-convert-sdi-tx` | compact | `false` | (Mini-DIN-8, if ever) | — | — | unchanged | none |
| `pro-convert-for-ndi-to-aio` | compact | `false` | **none — stays passive** (no USB host, no Mini-DIN-8, `fan-power-sources.md:37-38,186`) | — | — | unchanged | none |

**The blanking is driven by user decision 1 ("the decoders' USB-A host port is never used"), not by
the fan.** That is why `-to-hdmi` and `-to-sdi` are blanked even though they carry no fan.

**Why the slot order does not move.** On all three decoders the blanked `usb_host` was *already* the
innermost port of block B — `-to-hdmi`/`-to-hdmi-4k`: `rank(hdmi_out) = [15, 35] > rank(usb_host) =
[8, 20]`; `-to-sdi`: `rank(sdi_out) = [40.6, 40.6] > [8, 20]`. Dropping its rank to `[0, 0]` keeps it
last. Slots 1 and 2 (`NE8FDP-B`, `NAUSB-W-B` `usb_b`) are block A and are untouched.

**Expected golden deltas — read this before running `--update`.** The change is real but **small
enough that `build.py golden` would pass without updating**, so "goldens still green" is *not*
evidence the edit landed:

- **`.panel`**: the slot-3 cutout grows ⌀23.8 → ⌀24.2 through the 2.0 mm field, i.e.
  `π/4·(24.2² − 23.8²)·2 ≈ **30 mm³** less material` — roughly **0.2 %** of a ~13,500 mm³ plate,
  under the 0.5 % tolerance but clearly visible in the JSON diff.
- **`.base`**: the window body circle grows `d_win` 24.4 → 24.8 through the 3.0 mm lip, plus 0.2 mm
  of extra cap rise — `≈ **46 mm³**`, i.e. **~0.01 %** of the base. **Expect it not to trip at all.**
- `.lid` is unaffected on every SKU (no slot-dependent geometry).

**Therefore the acceptance evidence for this change is visual, not numeric:** the mandatory
straight-on `−Y → +Y` patch-wall elevation (§16.5) must show **four exactly-round ⌀24-class
openings** on the three decoders, and `echo(mcc_slot_assignment(dev))` must print `DBA-BL-B` at
slot 3. Update the goldens anyway, and check the volume moved in the direction and magnitude above.

**Blocking item, encoders only, unchanged by rev 9.** `pro-convert-hdmi-plus` and
`pro-convert-sdi-plus` must not be touched **for D-14 slot work** until **M12** (Mini-DIN-8 plug
axial length) is measured — see `architecture.md` §11 **R23**. *None of the rev-9 plans (#24/#25/#29)
touches the patch wall, the slot map or any end zone, so M12 does not block them.*

---

## 17. Rulings, 2026-09-09 — architecture gate for #24 / #25 / #26 / #27 / #29 (rev 9)

Four researcher plans were gated together because three of them touch `mounts.scad`/`layout.scad`
and all three touch the same 8 `models/*/case.scad` cfg blocks. **No envelope figure moves.**

### 17.1 Verdicts

| Plan | Issues | Verdict | Blocking changes |
|---|---|---|---|
| `2026-09-09-mount-rail-and-brackets.md` | **#25** (rail), **#26** (TV bracket) | **APPROVE WITH CHANGES** | R1–R5 below |
| same plan, §4 | **#27** (truss bracket) | **REJECT for now — DEFER** | blocked on **M14** + a user safety sign-off (**R25/R26**) |
| `2026-09-09-cradle-deck.md` | **#29** | **APPROVE WITH CHANGES** | R6–R8 below |
| `2026-09-09-lid-vents.md` | **#24** | **APPROVE WITH CHANGES** | R9–R10 below |

### 17.2 Required changes — #25 / #26

- **R1 (blocking).** `MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + MCC_FLOOR_T = **7.0**`, not `+2.0 = 6.0`;
  assert **T1-38**. At 6.0 the 4 mm groove leaves 2.0 mm of ASA on the one surface that carries the
  whole case when bracket-mounted, against a 3.0 mm uniform-shell spec. The plan's derivation cites
  `MCC_APERTURE_LIP_WEB_MIN`, which is a *minimum-material-to-an-edge* rule for a lip, not the floor
  spec. Cost: the sill stands 4 mm (not 3) into the interior; at `MCC_RAIL_Y = −20` that is inside
  the cradle-deck volume and free.
- **R2 (blocking).** `MCC_RAIL_Y = **−20.0**`, not `+20.0` — see §7.1's mount-rail row and
  `architecture.md` §11 **R24**. Keep the plan's derivation *form*
  (`MCC_CASE_INSERT_KEEPOUT_D/2 + MCC_RAIL_ROOT_W/2 + margin`, negated), not a hand-typed number.
  Replace the plan's ad-hoc "2.0 mm because disc-vs-rect" with a **named** `MCC_FLOOR_FEATURE_EDGE_MIN
  = 2.0` — §7.1's separation rule already says `max(MCC_FLOOR_FEATURE_MIN_SEP, r1+r2+2.0)`, and 20 mm
  centre-to-centre satisfies the 15 mm term outright.
- **R3 (blocking).** The D16 pairwise floor assert **is** in scope for #25 (the plan is right: do not
  add a sixth unchecked feature to an unchecked set) — but it must carry the
  `case_tripod_insert`/`fishtail_reserve` exemption or it fails on the first render of all 8 SKUs
  (`architecture.md` §13 **D19**). It lives in `mounts.scad` (the §6 owner), not in `layout.scad`
  (functions only).
- **R4.** The L1 file is **`lib/mcc/rail.scad`**, not `bracket.scad`; `layout.scad` must **not**
  `use` it (`architecture.md` §3). Barrel entry after `use <fasteners.scad>`.
- **R5.** `mcc_floor_bore_cut()` is **retired**, not left as an empty module; `shell.scad:428`'s call
  site becomes `mcc_rail_features_cut(dev, cfg)`. `layout.scad`'s `vesa_pos` local is renamed
  **`floor_center`** — that name, not #29's proposed `mount_ref_pos`; **#25 owns the rename.**
- Also: `scripts/build.py` — add `discover_brackets()` **and** register it in *both* `discover_all()`
  and `cmd_doctor()`'s listing (which calls `discover_coupons() + discover_models()` directly, so it
  would silently under-report). Make `discover_models()` skip `"brackets"` the way it already skips
  `"coupons"`. `golden_path("brackets/tv-bracket", "tv-bracket")` already resolves to
  `tests/golden/brackets/tv-bracket.json` — no change needed there.
- The bracket plates' **cross ribs** are exactly the case `MCC_RIB_HEIGHT_RATIO_MAX` was introduced
  for (a stiffening fin standing off a plate face) — assert it there (`architecture.md` §13 **D22**).

### 17.3 Required changes — #29

- **R6 (blocking).** Deck ladder ribs use **`MCC_CRADLE_RIB_T = 3.0`**. Do **not** create
  `_mcc_cradle_deck_rib_t()` or `deck_h/3 ≈ 3.62`. Full reasoning: **D22**. In one line — the ≤3:1
  height rule governs cantilevered fins, and these are floor-standing, cross-braced webs, stiffer in
  every axis than the 3.0:1 far-flank ribs the repo already ships; the derived form would also make
  rib thickness a function of `dev_h` and put two extrusion widths in one printed part.
- **R7 (blocking).** Drop `_mcc_deck_rib_blocked()` for v1 (**D21**). If the teamlead wants it kept,
  it must be per-**segment** and driven by an allowlist published beside `mcc_floor_keepout()`.
- **R8 (blocking).** `cfg["tripod_insert"]` defaults **`true`** (**D-16**), set explicitly in all 8
  `case.scad` files; `mcc_tripod_insert_bore_cut()`'s internal guard defaults true too. Bring
  **T1-40** (solid island under the pad pocket) and **T1-41** (the boss must be braced into the
  lattice) — both are new failure modes the lattice creates and neither is caught by `check`.
- Not blocking, but required: **do not** edit `.claude/knowledge/**` from an implementation branch
  (the plan's steps 9/10). Both files are architect-owned; this section is the record. **Do not
  create `.claude/knowledge/decision-log.md`** — decisions live in `architecture.md` §11/§13 and this
  file's §10/§15/§17, and a fourth file fragments the record. Same ruling for #24's step 13.

### 17.4 Required changes — #24

- **R9 (blocking).** Add `use <ports.scad>` to `vents.scad` (**D20**) — `mcc_dev_slug()` is not
  reachable through `use <layout.scad>`; OpenSCAD's `use` is not transitive.
- **R10 (blocking).** No magic numbers in the new asserts: the inline `1.0` edge margin becomes
  `MCC_LID_VENT_EDGE_MIN`, and `assert(MCC_LID_VENT_WEB_W >= 1.6)` compares against a named minimum
  (or against `MCC_VENT_WEB_W`), per §3's parameter conventions.
- Gate the field in **one** place: read `cfg["lid_vents"]` in `mcc_shell_lid()` and call
  `mcc_lid_vents_cut()` conditionally; do not also re-read the flag inside the module (the plan's
  code and its doc comment disagree). Fix the doc comment.
- Assert numbering **T1-36 / T1-37 is ratified** (T1-35 was the highest); this gate also claims
  T1-38–T1-41 for #25/#29, so those are taken.
- Keep `mcc_shell_lid()`'s two existing "vent band never crosses into the lid" asserts — they guard
  the *wall* bands and stay true.
- Golden scope is right: only `*.lid.json` may change; if a `.base.json` or `.panel.json` moves,
  something leaked out of the lid — stop and investigate.

### 17.5 `PLAN-ASSUMPTION` verdicts

| Plan | # | Assumption | Verdict |
|---|---|---|---|
| rail | 1 | Truss safety framing: dovetail+latch is not the primary fall restraint; the printed eye is unrated; the certified safety cable is the rated element | **ESCALATED to the user — not ratifiable by the architect.** The framing is technically correct; signing it off is a safety decision. **R26.** Blocks #27 |
| rail | 2 | Single insertion direction, not bidirectional | **RATIFIED.** Two latches double the flex-fatigue parts for a benefit nobody asked for. Reversible later |
| rail | 3 | `MCC_RAIL_Y` offsets the rail rather than moving the 1/4"-20 insert | **RATIFIED in principle, REJECTED in value.** Keep the insert where it is; the rail moves — but to **−20**, derived from the load path, not to `+20`, derived from the obstacle. **R24 / R2** |
| rail | 4 | `MCC_TRUSS_MOUNT_PATTERN = [40,40]` placeholder, "same status as `MCC_SPLITTERS`" | **REJECTED.** Not the same status: a wrong *reservation* makes the case bigger, a wrong *bolt pattern* makes the part scrap. **M14.** Blocks #27 |
| rail | 5 | 30 N retention target is `assumed` | **RATIFIED** as a coupon target only. Becomes **M15**; no full-size bracket prints before that coupon is pulled |
| rail | 6 | Bracket plate thicknesses 6 mm (TV) / 8 mm (truss) `assumed` | **RATIFIED for #26** (sandwiched flat against a TV, the plate is a shim, not a beam). **Deferred with #27** — the truss plate is a cantilever and its outline must be re-sized to ≥ the case footprint once M14 lands |
| rail | 7 | VESA fully removed, not deprecated-but-optional | **RATIFIED — this is the user's decision (D-15).** If VESA is ever wanted back as a third option, that is new scope |
| deck | 1 | Derived deck-rib thickness `deck_h/3` distinct from `MCC_CRADLE_RIB_T` | **REJECTED. R6 / D22** |
| deck | 2 | `cfg.tripod_insert` defaults `false` | **OVERRULED → `true`. D-16 / R8** |
| deck | 3 | `_mcc_deck_rib_blocked()` AABB test is conservative and unverified | **REJECTED as written. R7 / D21** — it is not merely conservative, it deletes whole rib lines |
| deck | 4 | One global grid pitch, not per-family | **RATIFIED**, guarded by **T1-39**. Do not raise the bounds to silence a future failure |
| deck | 5 | §4's volume/print-time figures are estimates | **RATIFIED.** The golden diff is the authority; quote before/after `volume_mm3` per SKU in the PR |
| deck | 6 | "#25 has not landed yet" | **Resolved by the dispatch order below: #25 lands first, #29 branches off `main` after it merges.** The plan's §2 VESA-removal steps become *verification* steps, not edits |
| lid | A | Uniform lid-vent field on fan and non-fan SKUs alike | **RATIFIED.** Same logic as §6's unconditional fan-bay reservation and T1-30's uniform application; and R5 already warns that a fan whose thermoswitch never closes is indistinguishable from a failed one, so a passive path on the Plus family is redundancy, not competition |
| lid | B | No louvre / no dust mitigation in v1 | **RATIFIED**, recorded as **R27**. Revisit before print if the user's use ever includes rain/outdoor |
| lid | C | 2 rows of 2 × 20 mm slots, not a hex field | **RATIFIED.** Reuses `_mcc_vent_slot_centers()` with no new primitive and clears the area target with ~60 % margin |
| lid | — | All new `MCC_LID_VENT_*` are `assumed` | **RATIFIED.** They are design parameters, not device dimensions — the same category as `MCC_VENT_SLOT_W`. Not a "never invent a dimension" violation |
| lid | — | T1-36/T1-37 numbering | **RATIFIED** (see R10) |

### 17.6 Golden churn — justified?

**Yes, for all three, and the justification is different in each case; state it in each PR.**

- **#25**: every `*.base*.json` moves (4 VESA bosses + 4 bores out, rail sill + groove in).
  **`bbox` must be byte-identical on all 8.** Two new goldens under `tests/golden/brackets/`, one new
  `tests/golden/coupons/rail-latch.json`.
- **#29**: every `*.base*.json` `volume_mm3` drops ≈16 % (compact) / ≈21 % (plus) and `facets` drops.
  **`bbox` must be byte-identical.** Anything wildly outside that band is a bug, not a better lattice.
- **#24**: only `*.lid.json` moves (`volume` down, `area` up, `facets` up, **`bbox` unchanged**).
- In all three the ~0.5 % golden tolerance is far exceeded, so "goldens still green" would itself be
  the failure signal — unlike D-14, where the delta hid *under* the tolerance (§16.6).

### 17.7 Ordered developer dispatch

All three plans edit the same 8 `models/*/case.scad` cfg blocks and the same `constants.scad`, so
they are **serialised**, not fanned out — the seven-branch pattern of §16.5 does not apply here.

| # | Branch | Base | Scope | Gate to the next |
|---|---|---|---|---|
| 1 | `feature/issue-25-mount-rail` | `main` | `constants.scad` (rail block, VESA constants deleted), new `lib/mcc/rail.scad`, `layout.scad` (`floor_center` rename, VESA rows out, `"mount_rail"` row in), `mounts.scad` (VESA out, sill in, `mcc_rail_features_cut()`, **D16 assert with the D19 exemption**), `shell.scad` call site, 8 × `case.scad` (`"vesa"` out), `models/coupons/rail-latch.scad`, `build.py` discovery, `tests/test_bracket.scad`, `BOM.md` VESA rows out, base goldens ×8 | merged to `main`, CI green |
| 2a | `feature/issue-26-tv-bracket` | `main` (after 1) | `models/brackets/tv-bracket.scad` + README, `MCC_M8_CLR_D`, `BOM.md` `## Mounting brackets`, `tests/golden/brackets/tv-bracket.json` | — |
| 2b | `feature/issue-29-cradle-deck` | `main` (after 1) | `constants.scad` (grid constants), `cradle.scad` (lattice, pad island, tripod collar, `tripod_insert` flag), 8 × `case.scad` (`"tripod_insert"` in), `tests/test_shell.scad`, base goldens ×8 | merged to `main`, CI green |
| 3 | `feature/issue-24-lid-vents` | `main` (after 2b) | `constants.scad` (`MCC_LID_VENT_*`), `vents.scad` (+`use <ports.scad>`), `shell.scad` `mcc_shell_lid()`, 8 × `case.scad` (`"lid_vents"` in), `tests/test_shell.scad`, lid goldens ×8 | — |
| — | **#27 truss bracket** | — | **NOT DISPATCHED.** Blocked on **M14** (buy and measure a half coupler) and on the user's sign-off of the **R26** safety framing | — |

**2a and 2b may run concurrently** — disjoint file sets (`models/brackets/**` + `BOM.md` vs
`lib/mcc/cradle.scad` + `models/*/case.scad`), and they touch different `constants.scad` sections.
**Step 3 must not start before 2b merges**: both append to the same cfg block in the same 8 files.

**Every branch:** `python scripts/build.py all` green locally, CI-green `render` before the PR
merges, and a per-SKU before/after `volume_mm3` table in the PR body (§17.6).
for the worked geometry (30.0 mm to the fan frame, 25.0 mm to the reservation, plug length
`unknown`) and the four resolution options. Everything in the decoder column above is independent of
M12 and may proceed now.

---

## 18. Ruling, 2026-09-09c — architecture gate for #32, the external fan switch (rev 11)

Gates `docs/plans/2026-09-09-fan-switch.md`. **Verdict: APPROVED WITH CHANGES — 8 blocking (B1–B8)
plus one blocking user decision (U).** The plan's *software* shape is right and conforms to §3: a new
L1 provider, a constants record, a `layout.scad` position, one `shell.scad` call site, a `cfg` flag
that defaults from `cfg["fan"]`. What is wrong is the *mechanical* half — the pocket does not meet
the stated safety requirement, the placement formula does not check the constraint that actually
binds, and the call site does not intersect the wall.

### 18.1 Blocking changes

| # | Change | Why |
|---|---|---|
| **B1** | **Renumber T1-38/T1-39 → T1-43 (band), T1-44 (recess/panel), T1-45 (body depth).** | T1-38/T1-39 are rev 9's (rail groove, deck grid); rev 10 reached T1-42c. Third collision in a row — take the next ID from §9, not from memory |
| **B2** | **`translate([L/2 − MCC_WALL, switch_y, switch_z])`, not `switch_pos[0] = L/2`,** at the `shell.scad` call site; copy `vents.scad:146` exactly. Record the convention: `fan_pos`/`switch_pos` carry the wall's **outer-face** plane in X | As written the cut lands in `X ∈ [L/2, L/2+3]` — outside the shell. It removes **nothing**, stays watertight and single-shell, and shows a golden delta of exactly zero, which §4.7's "expect a small delta" invites a developer to `--update` past |
| **B3** | **`recess_t = actuator_proud_h + MCC_SWITCH_FLUSH_CLR`, with an internal wall pad** (`pad_t = recess_t + panel_t`, 45° blend, `pad_t ≥ MCC_WALL`). Not a flat 1.0 mm | A 1 mm dish under a ~10 mm toggle lever is cosmetic. The requirement is the same one T1-25 already enforces on the side-bolt head: the actuator finishes **below** the outer face. The pad goes **inward** — the D-13 pattern — so no envelope moves |
| **B4** | **Solve `switch_y` from both sides (§5), and assert both.** The binding obstruction is the `(+X, −Y)` corner lid fastener, at two depths: its 3 mm gusset strip near the wall and its ⌀8.28 boss deeper in | The plan's `switch_y = fan_y − 27` puts the fan gap at exactly `clr` by construction (its own T1-38 therefore cannot fail) and leaves the real constraint as prose. Its "clearance to gusset 6.65 mm" is also arithmetically unreproducible from its own definition — the gusset near edge is 9.85 mm from its keep-out edge, and the governing obstruction is the boss at 7.96 mm |
| **B5** | **`MCC_SWITCHES` table + `MCC_SWITCH_DEFAULT`, not a single `MCC_FAN_SWITCH` struct.** Fields: `hole_d`, `nut_d` (circumscribed), `keepout_d`, `pad_d`, `body_d`, `depth`, `actuator_proud_h`, `panel_t_min/max`, `clr`, `confidence` | Every other purchasable part here is a table (`MCC_FANS`, `MCC_SPLITTERS`, `MCC_PANEL_PARTS`), and `switches.md` records **three** candidates. Also: `keepout_d = 8.0` is under-sized — a 1/4-40 bushing nut is ~8 mm **across flats**, i.e. ~9.24 mm circumscribed, and the pocket is round |
| **B6** | **Compact family: `["fan_switch", false]` explicitly** in `models/pro-convert-for-ndi-to-hdmi/case.scad`'s `base_fan` branch and in `tests/test_shell.scad`'s `VARIANT_FAN`, with a comment citing §5 | Its feasible interval is empty (U, below). Without this the first compact render fails T1-43 and a developer's most likely "fix" is to shrink `clr` until it passes |
| **B7** | **Move `mcc_fan_spec()` to `constants.scad` (L0) and add `MCC_FAN_DEFAULT`;** `layout.scad` then calls it instead of open-coding `MCC_FANS[search([...])[0]][1]`, and `vents.scad:148`/`shell.scad:375` drop their `"NF-A4x10"` literals | §3 bans `layout.scad` from importing an L1 geometry provider — but not from calling an L0 pure function over an L0 table. Same rule that keeps the rail keep-out row on `MCC_RAIL_*`. No geometry change, no golden change |
| **B8** | **`mcc_switch_keepout()` (pure, in `switch.scad`) — mirroring `mcc_side_bolt_keepout()`** — and `vents.scad` consumes it. `layout.scad` must **not** call it | One owner for the keep-out shape. This is the half of PLAN-ASSUMPTION 5 that is overruled: no §6-style *bay reservation* (correct — a switch without a fan is meaningless), but yes a keep-out other features can test against |

### 18.2 The user decision (U) — blocking for the compact family only

**A flush switch does not fit the compact family beside the fan, at any clearance.** With
`pad_d = 14.0` and `body_d = 10.0`: `y_hi = −59.325` (fan side) against `y_lo = −59.285` (boss side)
— empty by 0.04 mm. The plus family has a 3.2 mm window and works. Three alternatives were evaluated
and **all three are rejected by the architect**, so the choice is the user's:

- **Flush rocker (KCD11-101, 14 × 8.5, 14 mm along Z) with a deeper recess — REJECTED.** Its snap-in
  bezel (~15.5 × 10) sets the pocket, not its cutout, so the pad needs ≈14.6 mm against a 17.60 mm
  pad band *and* a 12.5 mm body against a 14.96 mm body band — worse than the toggle on compact and
  knife-edge on plus. Its snap-fit panel range is also typically ~1–1.5 mm, incompatible with the
  2.0 mm minimum residual (T1-44b/c would fail as soon as the range is measured).
- **Shift `fan_y` per family for the IP65 R13-112A (⌀20.2, real 24 V DC rating) — REJECTED.** The
  `+Y` side is capped by the connector bay's inward reach (`fan_y ≤ −25.7` on compact), so the move
  buys ≤ 5.1 mm where ≈10 mm is needed. It also re-opens **R20**, which says the default moves on
  *measurement*, not on a switch's convenience, and it de-centres the fan from the device.
- **Printed guard ribs around a proud toggle — REJECTED.** Any guard for an outward-protruding
  actuator must itself protrude, which reverses **D-13** ("nothing protrudes from any wall on any
  variant"), grows `L` by ~10 mm on every fan SKU and therefore moves §1's envelope table — a
  user-facing figure, not an implementation detail.

**Recorded default: ship on the `plus` family (3 SKUs), compact explicitly off.** The compact SKUs
are `fan = false` by default anyway, so nothing a user builds today loses a feature. Revisit with
M17 in hand, or with a sourced low-profile actuator ≤ 10 mm wide.

### 18.3 PLAN-ASSUMPTION verdicts

| # | Subject | Verdict |
|---|---|---|
| 1 | MTS-101 (SPST) over the ticket's MTS-102 (SPDT) | **UPHELD** — SPST is the electrically correct part for a series on/off |
| 2 | `depth`/`panel_t_min`/`panel_t_max` are `assumed` | **UPHELD and escalated to M17**, extended to `actuator_proud_h` and `nut_d` — the two figures that actually decide the fit |
| 3 | R13-112A recorded but not placed; no silent `fan_y` move | **UPHELD, and strengthened** — a `fan_y` move cannot buy compact enough band either, so it is not a fallback (18.2) |
| 4 | Wiring (a) manual only as the BOM default | **UPHELD as provisional.** No geometry impact either way, so it must **not** gate the branch; the BOM row says "default pending user confirmation" and `architecture.md` §12 Q19 carries the question |
| 5 | No reservation module for the switch | **PARTLY OVERRULED** — no §6 bay reservation (agreed), but a `mcc_switch_keepout()` is required (B8) |
| 6 | `mcc_fan_envelope()` is dead code, out of scope | **UPHELD** — recorded as deviation **D23** with a separate ticket as fix owner. The bay's *depth* is in fact reserved unconditionally by T1-18(c); what is missing is a single definition of the 5 mm intake clearance and any Y/Z footprint check |

### 18.4 Golden and test impact (corrects the plan's §4.7)

- **Three goldens move**, not four: `pro-convert-for-ndi-to-hdmi-4k.base.json`,
  `pro-convert-hdmi-plus.base.json`, `pro-convert-sdi-plus.base.json`.
- **`pro-convert-for-ndi-to-hdmi.base_fan.json` must NOT move** (B6). If it does, the explicit
  `fan_switch = false` wiring is broken — that is a regression, not a refresh.
- **The delta is not necessarily negative.** With the internal pad the net is
  `pad − through-bore − recess`, which may be **positive**; the plan's "sanity-check the delta is
  material-removing" check is wrong and would mislead a developer. The invariant to check instead is
  **`bbox` unchanged on all four SKUs** and `parts == 1`.
- No `.lid.json` / `.panel.json` file is affected (correct in the plan).
- `tests/test_shell.scad` gains an explicit plus-family `fan_switch = true` branch — the compact
  `VARIANT_FAN` no longer exercises the cutout after B6, so without it the feature ships untested by
  `smoke`. This is D15's lesson again: a contract that lives only in a test that no longer runs the
  branch is not a contract.

### 18.5 Knowledge and BOM

`knowledge/components/switches.md` (new) and the `fans.md` KUOQIY note are **approved as scoped** —
both are sourced third-party product facts and belong in the `knowledge/**` tree, not here. Two
additions required: `switches.md` must record `actuator_proud_h` and `nut_d` per candidate (they are
what decides fit, and neither appears in the plan's table), and must state the compact-family
infeasibility so the next reader does not re-derive it. The BOM switch row is **plus-family only**,
`assumed`, pending M17 and the U decision.
