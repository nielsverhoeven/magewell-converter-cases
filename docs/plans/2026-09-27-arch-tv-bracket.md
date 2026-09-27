# Plan: arch TV bracket — mount rail on the top two VESA 400 screws only, 3-part print (issue #47)

Status: **researcher plan, not yet architect-validated.** Route through `solution-architect` before
any developer starts (Team Charter step 2 — this is structural: the first multi-part bracket, a
`scripts/build.py` discovery change, a test that `use`s a `models/**` file, and new BOM hardware).

Source ticket: [#47](https://github.com/nielsverhoeven/magewell-converter-cases/issues/47). Sibling of
#26 (`models/brackets/tv-bracket.scad`); consumes #25's rail (`lib/mcc/rail.scad`) unchanged.

Required reading before implementing: `docs/plans/2026-09-09-mount-rail-and-brackets.md` §0–§3 (the
rail interface and the existing TV bracket); `models/brackets/tv-bracket.scad` in full, especially
its header "Derivation of the rotate([0,0,180])" and its `part == "assembly"` branch;
`lib/mcc/rail.scad`; `lib/mcc/fasteners.scad` (`mcc_heat_set_bore()`); `lib/mcc/constants.scad`
sections "Heat-set inserts", "Mount rail", "Mounting brackets"; `scripts/build.py`
`discover_brackets()`, `_extra_parts()`, `golden_path()`, `MAX_AXIS_MM`;
`.claude/knowledge/architecture.md` §3 ("`models/brackets/*.scad` are assemblies, not cases"), §9;
`knowledge/design/fdm-rugged-enclosure-guidelines.md` §4 (ribs) and §8 (insert bosses).

### User decisions (2026-09-27 — fixed, not re-opened here)

Arch/boomerang shape, lower ends on the TV's **top two** VESA screws only; raised flat centre with
the latch. Screws **400 mm** apart, **M8**. Latch = the existing `mcc_rail_male()` in the
`tv-bracket` orientation (patch wall hangs DOWN). Mounted **directly** on the TV (new M8 screws in
the BOM, length **`unknown`**, never stated). The case stays **fully behind the TV**; the
screw-to-top-edge distance is **< 185 mm**, otherwise `unknown` → a named parameter plus a Tier-1
assert. The case hangs **between** the screws horizontally and may overlap the screw line
vertically. Wider than the X1C bed → **3 parts** joined by overlapping laps with screws into
heat-set inserts; every part prints flat without supports.

---

## 0. Concept in one paragraph (read this first)

Two identical **arms** (one printable part, printed twice) lie flat on the TV back, each with an M8
pad on a top VESA screw at one end and a **lap** at the other. The **centre piece** carrying the
rail is a flat plate that sits **on top of** the two arm laps (a *stacked* lap, not a half-lap) and
is screwed down into heat-set inserts in the arms. Stacking is not a style choice — it falls out
of two constraints worked in §1.3: (a) the case **slides on along X from the +X end**, so its floor
sweeps over the right arm and its M8 pad, and (b) the case floor rides only `MCC_FLOOR_T` (3 mm)
above the rail's mounting face. Anything proud of the arms (ribs, M8 head) must therefore sit
below the case floor, which needs the rail raised by one plate thickness above the arms — exactly
what a centre plate stacked on the arms provides, with no support-requiring joggle in any part.

---

## 1. Frame and geometry

### 1.1 Frame (assembly frame of `arch-tv-bracket.scad`)

Viewed from **behind the TV** (the installer's view of the TV back):

- Origin: midpoint between the two top VESA screw centres, on the TV back surface.
- +X to the right, **+Y up**, +Z away from the TV (the TV back is the plane `Z = 0`).
- Screw centres at `P_L = (−HALF_PITCH, 0)`, `P_R = (+HALF_PITCH, 0)`.
- Each printable part is **authored in its own print frame** (bed face at its own `Z = 0`) and
  placed into this assembly frame only by the `assembly*` preview branches (§6).

### 1.2 Parameters (all local to `models/brackets/arch-tv-bracket.scad` — bracket-own geometry
stays out of `constants.scad`, the `tv-bracket.scad` convention; nothing here is cross-cutting)

| Name | Value | Basis |
|---|---|---|
| `VESA_TOP_PITCH` | `400` | user decision 2026-09-27 (#47); VESA MIS-F 400×400 is a standard pattern ([Wikipedia](https://en.wikipedia.org/wiki/VESA_mount), same citation as `tv-bracket.scad:98-100`) |
| `HALF_PITCH` | `VESA_TOP_PITCH / 2` = 200 | derived |
| `TV_TOP_CLEAR` | `150` | **`unknown` → placeholder, `assumed`.** Distance from the top-screw **centreline** up to the TV's **top outer edge**. User: `< 185` (#47). Measurement **M18** (§9). Override per TV with `-D TV_TOP_CLEAR=<mm>` or, once measured, edit and re-golden. |
| `TV_TOP_CLEAR_MAX` | `185` | user decision 2026-09-27 ("less than 185 mm") — an assert bound only |
| `TV_TOP_MARGIN` | `10.0` | `assumed` — case top stays this far below the TV top edge (bezel, measurement error, sight line over the edge) |
| `ARCH_PLATE_T` | `8.0` | derived minimum, §1.3 (and justified structurally, §2). **Not** `MCC_BRACKET_PLATE_T` (6.0): that constant was ratified as a *shim* thickness for a sandwiched plate (`constants.scad:733-736`); this is a beam. |
| `RIB_T` | `MCC_WALL` = 3.0 | `≤ 0.6 × ARCH_PLATE_T` = 4.8 (`fdm-rugged-enclosure-guidelines.md:67`) — same choice as `tv-bracket.scad:117` |
| `RIB_H` | `MCC_RIB_HEIGHT_RATIO_MAX * RIB_T` = 9.0 | `fdm-rugged-enclosure-guidelines.md:68`, D22 |
| `ARCH_SWEEP_CLR` | `2.0` | `assumed` — vertical clearance between the sliding case floor and the tallest arm feature; same magnitude as `MCC_GAP_DEV` (`constants.scad:443`) |
| `ARM_W` | `40.0` | `assumed` — arm width; carries the 2×2 joint pattern, two edge ribs and the M8 pad |
| `PAD_BOSS_D` | `30.0` | `assumed` — ≥ counterbore ⌀16.6 + 2 × 2·`MCC_WALL`; asserted |
| `CENTRE_W` | `40.0` | `assumed` (= `ARM_W`) — centre-body height in Y |
| `C_HALF` | `90.0` | `assumed` — centre-body half-length; rail footprint half-length is `MCC_RAIL_LEN/2 + MCC_RAIL_END_STOP_L` = 81, leaving a 9 mm end web (asserted ≥ `MCC_WALL`) |
| `XJ` | `95.0` | `assumed` — `|x|` of each lap centre in the assembly frame (tuned in §3.2) |
| `LAP_L` | `30.0` | `assumed` — lap length along the arm axis |
| `JOINT_S`, `JOINT_P` | `14.0`, `20.0` | `assumed` — joint hole pitch along / across the arm axis (2×2 pattern) |
| `LAP_RIB_GAP` | `1.0` | `assumed` — arm ribs stop this far short of the lap |
| `ARCH_KEEPOUT_CLR` | `1.0` | `assumed` — clearance used by the hole-vs-rail and rib-vs-centre asserts |
| `M8_HEAD_K`, `M8_WASHER_D`, `M8_WASHER_H` | `8.0`, `16.0`, `1.6` | ISO 4762 socket-head height / ISO 7089 washer OD, thickness — **nominal standard values, not in `knowledge/**` → `assumed`** (follow-up: add to `knowledge/components/fasteners-and-hardware.md`) |
| `M3_HEAD_D`, `M3_HEAD_K` | `5.5`, `3.0` | ISO 4762 M3 head ⌀ / height — same status, `assumed` |
| `M3_JOINT_SCREW_L` | `10` | derived stock length, §3.3 |
| `ARROW_DEPTH` | `0.6` | `assumed`, cosmetic "UP" deboss (§3.5) |
| reused | `MCC_M8_CLR_D` (9.0), `MCC_M3_CLR_D` (3.4), `MCC_INSERT_M3`, `MCC_CLR_SLIDE`, `MCC_RAIL_*`, `MCC_FLOOR_T`, `MCC_WALL`, `MCC_BUILD`, `MCC_BED_MARGIN`, `MCC_EPS` | `constants.scad` — no new library constant |

### 1.3 Z stack (derivation of the stacked lap and of `ARCH_PLATE_T = 8`)

The rail's open end is at local −X; `tv-bracket` places it `rotate([0,0,180])`, so in this frame
the case enters from **+X** and slides −X by `MCC_RAIL_LEN` (engagement starts with the case
centre at `x = +MCC_RAIL_LEN = +150`, right case edge at `150 + L_max/2 = 255.75`). Its floor
therefore sweeps across the whole right arm, including the right M8 pad at `x = 200`, over the
band `y ∈ [rise − 103.175, rise + 63.175]`. Clearing the pad (boss radius 15) *above* it would need
`rise − 103.175 > 15`, i.e. `rise > 118`, but the TV allows at most `rise < 111.8` (§1.4). So **the
case can never clear the pad by going above it** — it must pass over it in Z.

| Plane (TV back = 0) | Z | Derivation |
|---|---|---|
| Arm TV face / centre gap floor | 0 | TV back |
| Arm top face = centre bottom face | `ARCH_PLATE_T` = 8 | stacked lap |
| Rail mounting face (centre top) `Z_RAIL` | `2 * ARCH_PLATE_T` = 16 | stacked lap |
| Arm feature top `ARM_TOP_Z` (rib tops, M8 pad boss top) | `ARCH_PLATE_T + RIB_H` = 17 | rib rule |
| Case floor (exterior) at full mate and while sliding | `Z_RAIL + MCC_FLOOR_T` = 19 | `rail.scad` header: male pedestal is `MCC_FLOOR_T` tall |
| Case lid top | `19 + H` = 70 | `H = 51` (CLAUDE.md fixed decision) |

Sweep condition: `Z_RAIL + MCC_FLOOR_T − ARM_TOP_Z ≥ ARCH_SWEEP_CLR`, i.e.
`2T + 3 − (T + 9) ≥ 2` ⇒ **`T ≥ 8`**. `ARCH_PLATE_T = 8` is the smallest plate that works with the
ruled rib height; it is also the thickness §2 wants for torsion. (With `T = 6` the case would hit
the arm ribs/M8 head during slide-on.) The M8 head is counterbored into the pad boss so it sits
below `ARM_TOP_Z` (§3.4); the M3 joint heads are counterbored into the centre so nothing on the
centre exceeds `Z_RAIL` except the rail itself.

Consequence recorded as `PLAN-ASSUMPTION-3`: the arms lie flat on the TV back; the **centre stands
off the TV by 8 mm** (it never touches the panel between the screws).

### 1.4 Case envelope and the arch rise (derived from `TV_TOP_CLEAR`)

Case envelope: computed in-file, not hand-typed — loop `mcc_case_dims(dev, cfg)` over all 8 device
records with `cfg = [["fan", false], ["splitter", false], ["fan_switch", false]]`. Researcher check
(local OpenSCAD 2021.01 + the repo's BOSL2, `echo` only): `fan` true/false does not change L/W on any
SKU; maxima are **`L_max = 211.5`** (`pro-convert-sdi-plus`) and **`W_max = 166.35`**
(`pro-convert-hdmi-plus`, `…-for-ndi-to-hdmi-4k`), `H = 51` — matching CLAUDE.md's family
envelopes (211.5 × 166.4, rounded).

Mated case in the assembly frame (same algebra as `tv-bracket.scad:39-57`, with the rail foot
moved from `(0, 0, 0)` to `(0, rise, Z_RAIL)`):

```
translate([0, rise + MCC_RAIL_Y, Z_RAIL + MCC_FLOOR_T]) rotate([0, 0, 180])  <case native geometry>
```

so the case spans `x ∈ ±L/2` and `y ∈ [rise + MCC_RAIL_Y − W/2, rise + MCC_RAIL_Y + W/2]`; its far
wall is the **top** edge, its patch wall the **bottom** edge (patch wall down — the #26 convention).

- `CASE_TOP_ABOVE_RAIL = W_max/2 + MCC_RAIL_Y = 83.175 − 20 = 63.175`
- **`rise = TV_TOP_CLEAR − TV_TOP_MARGIN − CASE_TOP_ABOVE_RAIL`** (the rail sits as high as the TV
  allows; at the placeholder: `150 − 10 − 63.175 = 76.825`)
- Valid range: `rise ≥ 0` (an arch, not a V) ⇒ **`TV_TOP_CLEAR ≥ 73.175`**; the user bound
  `TV_TOP_CLEAR < 185` ⇒ `rise < 111.825`. Both asserted (§5).
- Case bottom at the placeholder: `76.825 − 20 − 83.175 = −26.35` (26 mm below the screw line —
  the accepted overlap). Case x-edge `105.75` vs the pad boss edge `200 − 15 = 185`: the case hangs
  between the screws with 79 mm to spare (asserted).

### 1.5 Arm and centre geometry

- Arm angle `alpha = atan2(rise, HALF_PITCH − XJ)`; arm length (pad centre → lap centre)
  `A = sqrt((HALF_PITCH − XJ)^2 + rise^2)`. Placeholder: `alpha = 36.19°`, `A = 130.10`.
- **Arm, print frame:** pad centre at origin, arm axis = +X, TV face on the bed.
  - Plate `z ∈ [0, ARCH_PLATE_T]`: a `ARM_W`-wide bar from `x = 0` to `x = A + LAP_L/2`, unioned
    with a `⌀ARM_W` disc at the origin (rounded pad end).
  - Pad boss `⌀PAD_BOSS_D`, `z ∈ [0, ARM_TOP_Z]` at the origin; M8 through-hole `⌀MCC_M8_CLR_D`;
    counterbore from the top (§3.4).
  - Two edge ribs `RIB_T × RIB_H` on the top face at `y = ±(ARM_W/2 − RIB_T/2)`, from `x = 0` to
    `x = A − LAP_L/2 − LAP_RIB_GAP`.
  - Lap `x ∈ [A − LAP_L/2, A + LAP_L/2]`: flat top, 4 insert bores (§3).
  - **Symmetric about its own X axis by construction** (pad, ribs, lap, holes). Hence the left arm
    is the *same* part under a proper in-plane rotation, not a mirror — see §3.1.
- **Placement** (assembly frame): right arm `translate([+HALF_PITCH, 0, 0]) rotate([0, 0, 180 − alpha])`,
  left arm `translate([−HALF_PITCH, 0, 0]) rotate([0, 0, alpha])`. Check: local +X of the right arm
  maps to `(−cos α, sin α)`, so the lap centre lands at `(200 − A cos α, A sin α) = (XJ, rise)` ✓.
- **Centre, print frame:** origin = the rail centre projected onto the centre's bottom face (=
  assembly `(0, rise, ARCH_PLATE_T)`), bottom face on the bed, `z ∈ [0, ARCH_PLATE_T]`.
  - Body: `2·C_HALF × CENTRE_W` rectangle, centred.
  - Two **tabs** = the arm laps' own footprint, placed with the *same* transform as the arms,
    re-expressed in centre-local coordinates: `translate([side*HALF_PITCH, −rise, 0])
    rotate([0, 0, side > 0 ? 180 − alpha : alpha]) translate([A, 0, 0]) cuboid([LAP_L, ARM_W,
    ARCH_PLATE_T], anchor = BOTTOM)`. The angled tabs are what gives the "boomerang" outline.
  - Rail: `translate([0, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male();` — the identical
    call to `tv-bracket.scad:182`, just lifted onto this plate's top face.
  - 4 M3 counterbored clearance holes per tab (§3.3), same transform as the arm's insert bores.
- **Print bboxes** (placeholder / worst case over `TV_TOP_CLEAR ∈ [73.2, 185)`, researcher's
  numeric sweep): arm `165.1 × 40 × 17` / ≤ `188.4 × 40 × 17`; centre `237.8 × 50.0 × 17` / ≤
  `239.7 × 50 × 17` (Z = `8 + MCC_RAIL_SILL_H 7 + MCC_RAIL_END_STOP_H 2`). All ≤ `MAX_AXIS_MM = 244`
  (`scripts/build.py:55`), the centre with ≥ 4.3 mm to spare — asserted, because it is the tight one.

---

## 2. Structural sanity check (rough, not FEA — every material figure `assumed`)

**Load.** No case or device mass is sourced: `pro-convert-hdmi-plus.md:18` gives only a
low-confidence retailer "1.2 lb" (≈ 0.54 kg); `pro-convert-hdmi-tx.md:17` ~230 g (unverified). The
printed case's solid-model volume for the widest SKU is ≈ 360 cm³ (`tests/golden/pro-convert-hdmi-plus.
{base,lid,panel}.json`: 249 413 + 94 763 + 15 586 mm³) — ≈ 385 g at an `assumed` ASA density of
1.07 g/cm³ (an upper bound; infill makes it lighter). Plus connectors/cables/fan (`unknown`, allow
0.3 kg): ≈ 1.2 kg. **Design mass 1.5 kg, `assumed`; design load `F_D = 3 × 1.5 × 9.81 ≈ 45 N`**
(×3 for clicking the case on, cable tugs and knocks — `assumed`).

**Material.** `knowledge/**` has no ASA modulus (the CNC Kitchen stiffness figure cited at
`fdm-rugged-enclosure-guidelines.md:227` was not recorded). Use `E_eff = 1500 MPa`, `ν = 0.35`,
`G ≈ 555 MPa` — **`assumed`**, a derated FDM value.

**Load path.** In-plane (the arch): `F_D` down at `x = 0`, two M8 pins. Out-of-plane: the case
centre of mass sits `e = 19 + 51/2 = 44.5 mm` off the TV, so a moment `M = F_D·e ≈ 2000 N·mm` about X
tries to peel the rail's top edge off the TV; it reaches the pads as **torsion in the centre and
the arms** (each side ≈ 1000 N·mm).

| Check | Estimate (placeholder geometry) | Verdict |
|---|---|---|
| In-plane bending at the lap, arm `8 × 40` | `M ≈ 22.5 N × 105 mm = 2363 N·mm`, `I = 42 667 mm⁴` → `σ ≈ 1.1 MPa` | negligible |
| Arm torsion, `J ≈ ⅓·40·8³ + 2·⅓·9·3³ ≈ 6990 mm⁴`, `L = A = 130` | `θ ≈ T·L/(G·J) ≈ 0.034 rad (1.9°)` at `F_D`; `τ ≈ T·t/J ≈ 1.2 MPa` | stiffness governs, not strength |
| Centre torsion, half-length 90, `J ≈ 6830 + rail ≈ 8500 mm⁴` | `θ ≈ 0.019 rad (1.1°)` at `F_D` | — |
| **Total rail tilt** | **≈ 3° at `F_D`, ≈ 1° under static weight** | acceptable for a hidden mount; creep is the open risk (R-C) |
| Same with `T = 6` | `J` drops ∝ `t³` → ≈ 2.3× the tilt (≈ 2.3° static) | rejected — and fails §1.3 anyway |

Why **thickness, not ribs**, carries this: an open rib adds almost nothing to torsional stiffness
(`⅓·b·t³` per strip, 81 mm⁴ per rib vs 6827 for the plate). The edge ribs are still worth having:
they stiffen the arm's out-of-plane bending (the `sin α` share of the moment) and resist warp of a
165 mm ASA bar (`fdm-rugged-enclosure-guidelines.md:17` "significant warping"). They go on the
**top face** of the arms because the TV face is the bed face and touches the TV; the centre gets
**no ribs** (its top is under the case floor with 3 mm to spare, its bottom is the bed face) — its
stiffness is the plate plus the 156 mm rail, which is itself a 7 mm-deep beam. If the Tier-4 check
(M18d) shows too much tilt, raise `ARCH_PLATE_T` to 10: every Z plane re-derives, the sweep slack
grows to 4 mm, `J` roughly doubles.

**M8 pads.** Tilting a `⌀40` pad under `T ≈ 1000 N·mm` needs ≈ 50 N of clamp to hold — any snug M8
far exceeds it. The real concern is **ASA creep under the head relaxing the preload** — hence the
washer (§3.4) and risk R-C.

---

## 3. Joints, fasteners, one-part arms

### 3.1 Why both arms are one printable part

A flat part with features on one face only cannot be turned into its mirror image by flipping it
(that moves the ribs onto the TV face). It *can* be if it has a mirror line of its own in-plane:
then `mirror(part) = rotate_z(part)`. The arm is built symmetric about its own axis (§1.5), so the
left arm is the right arm rotated by `alpha` instead of `180 − alpha` — a proper rotation, ribs
still on top. **One `arm` part, quantity 2.** The issue's wording ("left arm, centre piece, right
arm") is still three printed parts; only the STL count drops to two. `PLAN-ASSUMPTION-4`.

The centre is **keyed** by construction: its two tabs are mirror images of each other, so it
mates the arms in exactly one in-plane orientation, and it cannot be flipped over (the rail would
face the TV and the 9 mm rail/end-stop would hit it inside the 8 mm gap).

### 3.2 Joint layout and the tuning of `XJ`

Per lap: 4 holes at arm-local `(A ± JOINT_S/2, ±JOINT_P/2)`. One private function
`_mcc_arch_tv_joint_holes(g)` returns that list; the arm (insert bores) and the centre (counterbored
clearance holes) both consume it through the same placement transform, so the two halves cannot
drift — the D6 one-source rule (`architecture.md` §3/§5 rev 5), applied inside one file.

Three constraints compete for the ~41 mm between the rail footprint end (81) and the bed half-width
(122): the M3 counterbores must clear the rail keep-out (below), the centre part must fit the bed,
and the arm rib ends must clear the centre body. The researcher swept `rise ∈ [0, 111.8]` for
several candidates; `XJ = 95, LAP_L = 30, ARM_W = 40, JOINT_S = 14, JOINT_P = 20` gives, worst case
over the whole range:

| Margin | Worst case | Asserted by |
|---|---|---|
| M3 counterbore (r = 3.05) to rail keep-out rectangle | ≥ 4.7 mm | T1-A8 |
| Centre part width below 244 mm | ≥ 4.3 mm | T1-A1 |
| Arm rib-end corners outside the centre body | ≥ 3.5 mm | T1-A9 |

Rail keep-out rectangle (rail-centre-relative, after the 180° rotation): `x ∈ [−(MCC_RAIL_LEN/2 +
MCC_RAIL_END_STOP_L), +MCC_RAIL_LEN/2] = [−81, 75]`, `y ∈ [−MCC_RAIL_ROOT_W/2, MCC_RAIL_ROOT_W/2 +
MCC_RAIL_LATCH_ARM_T + MCC_RAIL_LATCH_ENGAGE] = [−7.31, +10.91]` (the latch arm and nub stand on the
rail-local −Y flank, i.e. +Y here — `rail.scad:151-175`). Built from `MCC_RAIL_*` constants, never
hand-typed.

Edge distances (`fdm-rugged-enclosure-guidelines.md:127`, ≥ 2 mm hole wall to any part edge):
across `ARM_W/2 − JOINT_P/2 − hole_d/2 = 20 − 10 − 2 = 8`; along `LAP_L/2 − JOINT_S/2 − 2 = 6`;
hole-to-hole `14 − 4 = 10`. All asserted.

### 3.3 M3, not M4 (deviation from the issue text — `PLAN-ASSUMPTION-1`)

The issue says "M4 screws into heat-set inserts". The plan uses **M3**:

- `MCC_INSERT_M3` is the only **sourced** insert (`len 5.7` — `fasteners-and-hardware.md:17`;
  `hole_d 4.0` — `:22`) and is the one the `insert-boss` coupon calibrates. `MCC_INSERT_M4`
  (`constants.scad:115-127`) is explicitly unsourced/`assumed` and unused.
- Geometry: `mcc_heat_set_bore()` cuts `len + 1` deep (`fasteners.scad:25,33`). M3: 6.7 mm into
  the 8 mm arm → blind, 1.3 mm skin on the TV face. M4 (`len 8.1`): 9.1 mm → **punches through an
  8 mm arm**; it would need a 10 mm plate, which re-derives the whole Z stack (`Z_RAIL = 20`).
- Load: worst M3 shear ≈ 54 N (in-plane joint moment 2363 N·mm over a polar radius
  `√(7² + 10²) = 12.2` mm, 4 screws, + 5.6 N direct); tension ≈ 25 N per screw from the
  out-of-plane moment. Peak insert pull-out measured ≈ 1400 N (PLA, `fasteners-and-hardware.md:56`;
  ASA `unknown`, `:58`) — well over an order of magnitude of margin even if ASA is much weaker.
- The M3 hardware (inserts, screws) is already stocked for every case.

Screw stack (derives `M3_JOINT_SCREW_L`): counterbore in the centre `⌀(M3_HEAD_D + 2·MCC_CLR_SLIDE)
= 6.1`, depth `M3_HEAD_K + 0.3 = 3.3` → head seat at `z = 16 − 3.3 = 12.7`. Insert spans
`z ∈ [8 − 5.7, 8] = [2.3, 8]`, bore floor at `8 − 6.7 = 1.3`. **M3×10** → tip at `2.7`: 1.4 mm above
the bore floor, 5.3 mm of insert engagement (≥ 1.5·d = 4.5, `assumed` rule of thumb). Asserted.

### 3.4 M8 pad

Through `⌀MCC_M8_CLR_D` (9.0, `constants.scad:144`). Counterbore from the top
`⌀(M8_WASHER_D + 2·MCC_CLR_SLIDE) = 16.6`, depth `M8_WASHER_H + M8_HEAD_K + 0.4 = 10.0`, so the
socket head sits 0.4 mm below the boss top (`ARM_TOP_Z = 17`) and the case slides over it.
**Clamped pad thickness `PAD_CLAMP_T = ARM_TOP_Z − 10.0 = 7.0`** — the number the installer needs
for the screw length (§8.1). Asserts: `PAD_CLAMP_T ≥ 2·MCC_WALL`; boss wall
`(PAD_BOSS_D − 16.6)/2 = 6.7 ≥ 2·MCC_WALL`.

### 3.5 Upside-down install (the #26 open point)

The whole assembled bracket *can* be mounted rotated 180° in-plane (it becomes a V, and the case
hangs patch wall up). The arch shape is itself the main cue; add a cheap explicit one: a debossed
triangle "UP" arrow, `ARROW_DEPTH = 0.6`, pointing +Y on the centre's top face at centre-local
`(−30, +14)` — outside the rail keep-out (`y ≤ 10.91`) and below the body edge (`y = 20`), never
in contact with the case (it is below `Z_RAIL`). `PLAN-ASSUMPTION-6`.

---

## 4. File layout and `scripts/build.py`

### 4.1 One file, two exported parts

**`models/brackets/arch-tv-bracket.scad`**, parts **`arm`** and **`centre`**, plus non-exported
`assembly` / `assembly_sweep` previews. Rejected alternative: one `.scad` per printable part — the
two files must share every lap/rise parameter, and `architecture.md` §3 lets a bracket import only
the barrel, so the shared values would have to move into `constants.scad` (bracket-own geometry in
L0, against the `tv-bracket.scad:85-92` convention), and no single file could draw the assembly.

Default `part = "centre";` (overridden by `-D part=...`; never `"assembly"` as default, so a bare
`openscad -o x.stl` never exports ghosts).

### 4.2 `discover_brackets()` change (required — today it hard-codes `parts=[stem]`)

In `scripts/build.py`:

1. Next to `_EXTRA_PARTS_MARKER_RE` add
   `_PARTS_MARKER_RE = re.compile(r"//\s*build\.py:\s*parts\s*=\s*(.+)")`. It cannot match the
   `extra_parts` marker (after `build.py:` it requires `p`), and vice versa.
2. Factor `_extra_parts()`'s body into `_marker_list(text: str, regex) -> list[str]`; keep
   `_extra_parts(text)` as a one-line wrapper (no behaviour change for models); add
   `_bracket_parts(text) = _marker_list(text, _PARTS_MARKER_RE)`.
3. `discover_brackets()`: read the file (`OSError` → `""`, same as `discover_models()`), then
   `parts = _bracket_parts(text) or [stem]`. The marker **replaces** the default (a multi-part
   bracket has no part named after its stem); `tv-bracket.scad` has no marker → unchanged.
4. Update the docstring ("single-part flat plates" → "flat plates; single part named after the
   file stem unless a `// build.py: parts = a, b` marker lists them") and the
   `scripts/README.md:57` row.

The file carries `// build.py: parts = arm, centre` in its header. Everything downstream already
handles multi-part targets: `golden_path()` → `tests/golden/brackets/arch-tv-bracket.arm.json` /
`.centre.json`; exports → `exports/brackets/arch-tv-bracket/{arm,centre}.{stl,3mf,summary.json}`;
`package_release._package_flat_parts()` loops `target.parts` (→ `arch-tv-bracket/arm.stl` in the
brackets zip); `_step_asset_name()` handles `part != stem`. `check` applies the 244 mm cap per STL.

---

## 5. Tier-1 asserts — `module mcc_arch_tv_assert(g)`

All geometry derives from one pure function `mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR)`
returning a BOSL2 struct (`rise`, `alpha`, `arm_len`, `z_rail`, `arm_top_z`, `case_top_above_rail`,
`l_max`, `w_max`, `pad_clamp_t`, bbox vectors). Asserts live in a **module** (not bare top-level
statements) so the smoke test can run them for other `TV_TOP_CLEAR` values (§7.1); the file calls
`mcc_arch_tv_assert(G)` at top level so every render fires them. Proposed ids `T1-A1…A13` —
the architect assigns final T1 numbers (current highest is T1-46).

| Id | Assert | Source of the rule |
|---|---|---|
| A1 | arm and centre bbox ≤ `MCC_BUILD − 2·MCC_BED_MARGIN` (244) per axis **and** `mcc_bbox_ok()` | `build.py:55`; see note ¹ |
| A2 | `rise + case_top_above_rail + TV_TOP_MARGIN ≤ tv_top_clear + MCC_EPS` and the centre's top edge (`rise + bbox_y/2`) ≤ `tv_top_clear − TV_TOP_MARGIN` | user decision "fully behind the TV" |
| A3 | `rise ≥ 0` (message: "TV too short above the screws: needs TV_TOP_CLEAR ≥ 73.175; a V variant is a new user decision") | user sketch (arch) |
| A4 | `tv_top_clear < TV_TOP_CLEAR_MAX` | user decision (< 185) — catches typos |
| A5 | `z_rail + MCC_FLOOR_T − arm_top_z ≥ ARCH_SWEEP_CLR` | §1.3 slide-on sweep |
| A6 | `RIB_T ≤ 0.6·ARCH_PLATE_T`; `RIB_H ≤ MCC_RIB_HEIGHT_RATIO_MAX·RIB_T` | `fdm-…-guidelines.md:67-68`, D22 |
| A7 | `MCC_RAIL_LEN/2 + MCC_RAIL_END_STOP_L + MCC_WALL ≤ C_HALF`; rail keep-out `y` span inside `±CENTRE_W/2` | rail must sit on the body |
| A8 | every M3 counterbore circle (r + `ARCH_KEEPOUT_CLR`) is disjoint from the rail keep-out rectangle (circle–rectangle distance, not an x-only check) | §3.2 |
| A9 | every arm rib-end corner is outside the centre body rectangle by ≥ `ARCH_KEEPOUT_CLR` | §3.2 |
| A10 | insert bore depth (`len + 1`) + 1.0 skin ≤ `ARCH_PLATE_T`; hole edge distances ≥ 2 | §3.3; `fdm-…-guidelines.md:127` |
| A11 | M3 tip ≥ bore floor + 0.5; engagement ≥ 1.5·3 | §3.3 |
| A12 | `pad_clamp_t ≥ 2·MCC_WALL`; pad boss wall ≥ `2·MCC_WALL` | §3.4 |
| A13 | `l_max/2 + 10 ≤ HALF_PITCH − PAD_BOSS_D/2` (case hangs between the screws) | user decision |

¹ Observed while researching, **not fixed here**: `mcc_bbox_ok()` (`lib/mcc/util.scad:42-44`) allows
`MCC_BUILD − MCC_BED_MARGIN` = 250 per axis, while `build.py`'s `MAX_AXIS_MM` is `256 − 2·6` = 244.
A1 therefore asserts the stricter 244 explicitly. Architect: record as a deviation or fix in a
follow-up.

Also `echo()` one summary line per render (`rise`, `alpha`, `arm_len`, both bboxes,
`pad_clamp_t`, `TV_TOP_CLEAR` with the word `assumed`). **Do not** echo the string
`WARNING: unmeasured` — that is the device-port release gate (`build.py:63,448`) and would fail
`all --release` on a tag.

---

## 6. Previews (non-exported, invisible to `build.py`)

- `part == "assembly"`: both arms, the centre, the rail, placed in the assembly frame (§1.5);
  a ghost Plus case (`MCC_DEV_PRO_CONVERT_HDMI_PLUS`, variant `fan = true, splitter = false,
  fan_switch = true` — the SKU's own `case.scad:75-80`) mated with the §1.4 transform, ghost device
  force-shown as in `tv-bracket.scad:223-226`; a translucent ghost TV-back slab (`z ∈ [−3, 0]`,
  top edge at `y = TV_TOP_CLEAR`) and a thin red cuboid along the top edge; two grey ghost M8
  heads in the counterbores.
- `part == "assembly_sweep"`: the same, with the case shifted `+MCC_RAIL_LEN` in X (engagement
  start), to show the floor passing over the right arm and pad.
- Verify by picture, not algebra (the #26 rule): render both to PNG (the container's
  `/usr/bin/openscad` is 2021.01 — fine for a preview PNG and for `echo`, **not** for goldens) and
  confirm: patch wall down, case top below the red line, case floor above the right arm in the
  sweep view, arms on `z = 0`, centre on the arm laps.

---

## 7. Tests and goldens

### 7.1 Smoke test — new `tests/test_arch_tv_bracket.scad`

`use <../models/brackets/arch-tv-bracket.scad>` (a `use` imports modules/functions only; the
file's top-level `part` dispatch and top-level assert call do **not** run). Then, for
`tv_top_clear ∈ [73.2, 150, 184.9]` (arch floor, placeholder, just under the user bound):
`g = mcc_arch_tv_geom(tv_top_clear = v); mcc_arch_tv_assert(g);` and instantiate
`mcc_arch_tv_arm(g)` / `mcc_arch_tv_centre(g)` translated apart. Header comment documents the two
negative cases that must fail (`72`, `185`) but are not run (an assert failure is a non-zero exit).
A test `use`-ing a `models/**` file is new — `PLAN-ASSUMPTION-5`.

### 7.2 Goldens — `tests/golden/brackets/arch-tv-bracket.arm.json`, `…centre.json`

Only the pinned nightly may produce them (tessellation/Manifold); the developer's container cannot
download it. Route:

1. Add `if: always()` to the "Upload exports" step of `.github/workflows/render.yml` (today it is
   skipped when `build.py all` fails, so a missing golden also hides the summaries needed to create
   it). One-line CI change, include it in this PR.
2. Push the branch without the two goldens → CI fails at `golden` ("missing golden") → download the
   `exports` artifact, unpack it into `exports/` so that
   `exports/brackets/arch-tv-bracket/{arm,centre}.summary.json` exist.
3. `python scripts/build.py golden --update brackets/arch-tv-bracket` (reads summaries only, no
   OpenSCAD) → commit the two JSONs → push → CI green. Sanity-check the bboxes against §1.5
   (`≈ 165.1 × 40 × 17`, `≈ 237.8 × 50 × 17`).

Fallback: the user runs `golden --update` on Windows with the pinned nightly.
`tests/golden/brackets/tv-bracket.json` must **not** change (proves the `discover_brackets()`
change is inert for single-part brackets). Add a row to `tests/golden/README.md`'s naming table:
`brackets/arch-tv-bracket` | `arm` | `tests/golden/brackets/arch-tv-bracket.arm.json`.

---

## 8. BOM, README, print-check

### 8.1 `BOM.md` → "Mounting brackets" (hand-authored; add under the `tv-bracket` table)

Intro sentence: `arch-tv-bracket.scad` (issue #47) screws **directly** onto a TV's top two VESA 400
screw positions (M8); printed once per mounting point.

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| `arch-tv-bracket` arm | `models/brackets/arch-tv-bracket.scad` part `arm`, ASA | **2** | same STL printed twice; the left arm is the right one rotated | this plan §3.1 |
| `arch-tv-bracket` centre | same file, part `centre`, ASA | 1 | carries the rail; sits on the arm laps | §1.5 |
| M8 socket head cap screw (ISO 4762) | generic | 2 | **Length: MEASURE, do not guess.** Under-head length = `PAD_CLAMP_T` (echoed by the render; 7.0 mm at current parameters) + the usable thread depth of *your* TV's VESA inserts − ≥ 1 mm, rounded **down** to a stock length. Too long can damage the panel. | M18 (§9); user decision #47 |
| M8 flat washer (ISO 7089, ⌀16) | generic | 2 | under the head, in the pad counterbore — spreads the clamp on ASA | §3.4 (`assumed` ISO nominal) |
| M8 washers as spacers | generic | 0–4 (situational) | only if the TV back is not flat along an arm; adding them lengthens the screw by their thickness | R-F |
| M3 socket head cap screw M3×10 (ISO 4762) | generic | 8 | lap joints, 4 per side, from the top | §3.3 derivation |
| M3 heat-set insert Ruthex RX-M3x5.7 | RX-M3x5.7 | 8 | in the arm laps, installed from the top face | `fasteners-and-hardware.md:17,22` |

### 8.2 `models/brackets/README.md`

- "What each bracket carries" row: `arch-tv-bracket.scad` | two identical arms (M8 pad + counter-
  bored head, edge ribs, M3-insert lap) + a centre piece with the male rail, 4 M3 per lap | screwed
  directly onto the TV's top two VESA 400 screws; nothing else touches the TV.
- Orientation: same convention as `tv-bracket` (patch wall down); the **arch points up** (UP arrow
  on the centre); the case slides on **from the right** (viewed from behind the TV) and needs
  ≈ `MCC_RAIL_LEN` (150 mm) of free space right of its final position.
- Print table rows: `arm` — **TV face on the bed**, ribs/pad boss/insert bores up, no supports;
  `centre` — **flat face on the bed**, rail up (same rail orientation as `tv-bracket` /
  `rail-latch`), no supports.
- Render: `build.py render brackets/arch-tv-bracket --format both`.
- Assembly order: inserts into both arms → bolt both arms to the centre (M3, from the top) on a
  table → offer the bracket to the TV → two M8 through the pads → click the case on.

### 8.3 `.claude/skills/print-check/SKILL.md` §3 table — one row

`models/brackets/arch-tv-bracket.scad` | `arm`: TV face down; `centre`: flat face down, rail up.
Mount with the **arch up** (UP arrow); patch wall then hangs down. **Do not print for use before
M15 (rail-latch) and M18 (TV measurements).**

---

## 9. Risks and Tier-4 measurements (proposed ids — architect assigns; current highest R29, M17)

- **R-A — M8 screw length / panel damage.** Length is `unknown` by design; BOM says measure. A
  screw bottoming in the TV insert can crack or dent the panel. Measure the insert depth (M18b).
- **R-B — upside-down (V) install**, patch wall up. Mitigated by the arch shape, the UP arrow and
  the keyed centre (§3.1, §3.5); not prevented.
- **R-C — two-screw load path and ASA creep.** Estimated tilt ≈ 1° static / 3° at `F_D` on
  `assumed` material data (§2); creep under the M8 washers and in torsion is unquantified. The
  case hangs over nothing but the TV's own back — failure drops it onto the TV's stand/floor.
- **R-D — `TV_TOP_CLEAR` unknown.** The A2 assert is only as good as the value; the placeholder
  (150) is not a measurement. Do not print for use until M18a is written back
  (`confidence → measured` in the comment) and goldens refreshed.
- **R-E — slide-on path.** The case enters from +X and passes 19–70 mm off the TV back over the
  right arm; TV rear bulges, connector panels or cables right of the screw may block it (M18c).
- **R-F — TV back not flat along the arms**, or not coplanar with the two screw faces. Arms then
  rock or bend when clamped; use spacer washers (BOM). The centre never touches (8 mm gap).
- **R-G — insert bore floor is 1.3 mm** (thin TV-face skin under each insert). Structural load is
  on the insert's walls, not the floor; the screw tip stays 1.4 mm above it (A11).
- **R-H — tight bed margins** (centre ≥ 4.3 mm under 244). Asserted; any change to the rail
  constants or `XJ`/`LAP_L` re-runs A1.
- **Inherited:** R24 (single rail line, roll moment) and the **M15 rail-latch gate** — no full-size
  bracket print before `rail-latch` is pull-tested; the latch thumb-release reach is still the
  coupon's open question.

**M18 (proposed) — on the user's actual TV, before printing the arch bracket for use:** (a)
`TV_TOP_CLEAR`: top-screw **centre** to the TV's top outer edge; (b) usable M8 thread depth of the
two top VESA inserts (probe with a long screw, count turns ×1.25 mm); (c) obstacles/bulges on the TV
back within the sweep band right of the right screw, and free space behind the TV (≥ 70 mm + cable
bend if the TV is near a wall); (d) after the first print: rail tilt under the real case (checks §2).

---

## 10. Ordered implementation steps

Branch `feature/issue-47-arch-tv-bracket` off `main` (confirm with the `git-flow` skill).

1. `scripts/build.py`: §4.2 steps 1–4 (`_PARTS_MARKER_RE`, `_marker_list()`, `_bracket_parts()`,
   `discover_brackets()`); `scripts/README.md:57` row. Run `python scripts/build.py doctor` —
   `brackets/tv-bracket` still lists `parts=[tv-bracket]`.
2. Create `models/brackets/arch-tv-bracket.scad` (style: `tv-bracket.scad` — header with frame,
   Z-stack table, orientation derivation; `$fa = 1; $fs = 0.4;` only; `include <mcc/mcc.scad>` +
   all 8 `include <mcc/devices/*.scad>`; `// build.py: parts = arm, centre`; `part = "centre";`):
   1. §1.2 parameters with their basis comments.
   2. `_mcc_arch_tv_envelope_max()` (loop `mcc_case_dims()` over the 8 records, §1.4).
   3. `mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR)` (§1.4, §1.5, §3.4 values as a struct).
   4. `_mcc_arch_tv_joint_holes(g)`; `_mcc_arch_tv_place(g, side)` (children placed with the arm
      transform, centre-local frame) and the assembly-frame variant; `_mcc_arch_tv_circle_rect_gap()`.
   5. `mcc_arch_tv_assert(g)` — A1–A13 (§5); call it at top level.
   6. `mcc_arch_tv_arm(g)` (§1.5, §3.2–3.4): `difference(){ union(){plate, pad boss, ribs};
      M8 hole + counterbore; for holes: translate([x, y, ARCH_PLATE_T]) mcc_heat_set_bore(MCC_INSERT_M3); }`
      — every functional hole `$fn = 64, circum = true`, `MCC_EPS` overlaps on both faces (the
      `tv-bracket.scad:184-194` pattern).
   7. `mcc_arch_tv_centre(g)`: `difference(){ union(){body, two tabs, rail}; M3 clearance holes +
      counterbores; UP arrow deboss; }` — the rail is **not** inside the `difference()` path of any
      cut (A8 guarantees it, but keep the union/difference order explicit).
   8. `assembly` / `assembly_sweep` branches (§6); `else assert(false, …)` for unknown parts.
   9. `echo()` summary (§5).
3. Render locally for `echo` + preview PNGs (2021.01): `-D part="assembly"` and
   `"assembly_sweep"`; inspect per §6. Fix the transform if the picture disagrees with §1.4.
4. `tests/test_arch_tv_bracket.scad` (§7.1).
5. `.github/workflows/render.yml`: `if: always()` on "Upload exports" (§7.2).
6. `models/brackets/README.md`, `BOM.md`, `.claude/skills/print-check/SKILL.md`,
   `tests/golden/README.md` (§7.2, §8).
7. Push; obtain goldens via §7.2; commit them with a PR note ("new target, no existing golden
   moves; `tv-bracket.json` unchanged").
8. PR to `main`, CI-green (`render` check) before merge. PR body cites this plan and lists M18.
9. Architect records (not the developer): `architecture.md` §3 bracket wording (multi-part via
   marker), the R/M/T1 ids, the `mcc_bbox_ok()` 250-vs-244 note, the test-uses-model precedent.

---

## 11. `PLAN-ASSUMPTION` list for the architect

1. **M3, not M4, for the lap joints** — contradicts the issue text. Sourced insert, blind in an
   8 mm plate, ample margin (§3.3). M4 would force 10 mm plates and `Z_RAIL = 20`. User/architect
   to confirm.
2. **`TV_TOP_CLEAR = 150` placeholder** and **`TV_TOP_MARGIN = 10`**, both `assumed`; the rise is
   derived to put the case top exactly `TV_TOP_MARGIN` below the TV edge (highest allowed). The
   bracket is buildable and asserted today, but must not be printed for use before M18.
3. **Stacked lap ⇒ the centre stands 8 mm off the TV** and the rail face is 16 mm off it (case
   floor at 19, lid at 70). Forced by the +X slide-on sweep over the right arm and pad (§1.3).
   The user said "the bracket's back face touches the TV" — true for the arms, not the centre.
4. **One `arm` part printed twice** instead of distinct left/right parts (§3.1).
5. **A smoke test `use`s a `models/**` file** (`tests/test_arch_tv_bracket.scad`) — new precedent;
   the alternative (moving arch geometry into `lib/`) would put per-bracket geometry into a library.
6. **Cosmetic UP-arrow deboss** as the upside-down mitigation (the #26 open point) — cheap, not a
   physical key for the whole assembly.
7. **`scripts/build.py` gains a `// build.py: parts = …` marker for brackets** (replaces
   `[stem]`), plus `if: always()` on the CI export upload so goldens can be produced from CI.
8. **Structural numbers are `assumed`** (1.5 kg design mass, ×3 factor, `E_eff = 1500 MPa`); `T = 8`
   is also the geometric minimum. No sourced ASA modulus exists in `knowledge/**`; the M18d tilt
   check after the first print is the real verification.
9. **ISO 4762 / ISO 7089 head and washer dimensions** are used as nominal standards, marked
   `assumed`, because `knowledge/components/fasteners-and-hardware.md` does not carry them yet —
   suggest a researcher follow-up to source and add them.

---

## 12. Architect verdict (2026-09-27)

(Numbered §12: §9 is this plan's risk list and §10–§11 exist.)

**Verdict: APPROVE WITH CHANGES — 11 binding changes (B1–B11).** The concept, the Z stack, the
one-file/two-part split and the `build.py` marker are sound, and most numbers reproduce. But one of
the plan's own Tier-1 asserts **fails at the placeholder**, so the first render would go red (B1).
Separately, the review found a **defect in the rail interface that #47 inherits from #25** (F1). It
does not block this PR, but it blocks printing *any* bracket for use.

### 12.1 What was re-derived (independently, numeric sweep over `TV_TOP_CLEAR ∈ [73.2, 184.99]`)

| Claim | Plan | Architect | Status |
|---|---|---|---|
| `CASE_TOP_ABOVE_RAIL`, `rise` @150, range | 63.175 / 76.825 / `TV_TOP_CLEAR ≥ 73.175`, `rise < 111.825` | same | ✓ |
| `L_max`, `W_max` | 211.5 (`sdi-plus`), 166.35 (`hdmi-plus`, `…-4k`) | same, cross-checked against the committed `tests/golden/*.base*.json` / `.lid.json` bboxes (shipped cfgs) | ✓ |
| Pad cannot be cleared from above | needs `rise > 118.175`, max 111.825 | same | ✓ |
| Sweep condition ⇒ `T ≥ 8` | `2T + 3 − (T + 9) ≥ 2` | same; case base bbox `min z = 0` on all 8 SKUs, so nothing protrudes below the case floor | ✓ |
| `alpha`, `A` @150 | 36.19°, 130.10 | same | ✓ |
| Arm bbox | 165.1 / ≤ 188.4 × 40 × 17 | same | ✓ |
| Centre bbox | 237.8 / ≤ 239.7 × 50 × 17 | 239.70 max X (worst at the top of the range), 50.0 Y, Z `8 + MCC_RAIL_SILL_H + MCC_RAIL_END_STOP_H` = 17 (matches `tv-bracket.json`'s rail height 9) | ✓ |
| Rail keep-out | x `[−81, 75]`, y `[−7.31, +10.91]` | same | ✓ |
| **A8, M3 counterbore to rail keep-out** | **worst ≥ 4.7 mm** | **open-end (+X) lap: ≥ 4.87 ✓. End-stop (−X) lap: −0.60 mm at 150, −1.13 mm at 184.9 → the counterbore overlaps the end-stop flange/pedestal footprint.** Positive only below `TV_TOP_CLEAR ≈ 135` | **✗ → B1** |
| A9, rib vs centre body | ≥ 3.5 | ≥ 4.85 (segment check, not just corners) | ✓ (B2 hardens the assert) |
| M3 stack | seat 12.7, tip 2.7, 5.3 engaged, 1.3 skin | same | ✓ |
| M8 pad | clamp 7.0, head 0.4 below 17, boss wall 6.7 | same; ISO nominals (k 8, washer 16 × 1.6; M3 dk 5.5, k 3) are correct standard values | ✓ |
| Structure | ≈ 1° static / 3° at `F_D` | reproduced. See N1: `⅓bt³` overstates `J` by ≈ 13 % for b/t = 5. Separately, bearing on the TV back makes the real arm torsion much stiffer. Conclusion unchanged | ✓ |
| Citations | `fasteners-and-hardware.md:17, :22, :58` | **stale.** `:17`/`:22` now hold unrelated text; the figures are at `:35` (RX-M3x5.7, 5.7 mm), `:40` (4.0 mm hole) and `:59` (ASA pull-out `unknown`). `:56`, `fdm-…:17/:67/:68/:127/:227`, `pro-convert-hdmi-plus.md:18`, `pro-convert-hdmi-tx.md:17` and every code `file:line` check out | **✗ → B5** |
| `mcc_bbox_ok()` 250 vs `MAX_AXIS_MM` 244 | flagged | `build.py` is right: `MCC_BED_MARGIN` is a per-side margin. `util.scad:43` and the `architecture.md` §9 Tier-1 row are wrong | → D26, B9 |

### 12.2 Binding changes

- **B1 — centre the rail's physical footprint on the centre plate (fixes the A8 failure).** In
  `models/brackets/arch-tv-bracket.scad` add
  `RAIL_X = MCC_RAIL_END_STOP_L / 2; // = 3.0, derived: moves the rotated footprint [−81, 75] to [−78, 78]`.
  Use it consistently in four places:
  1. the rail call `translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male();`
  2. the keep-out rectangle, x `[RAIL_X − MCC_RAIL_LEN/2 − MCC_RAIL_END_STOP_L, RAIL_X + MCC_RAIL_LEN/2]`, still built from `MCC_RAIL_*`
  3. the case mate transform `translate([RAIL_X, rise + MCC_RAIL_Y, Z_RAIL + MCC_FLOOR_T]) rotate([0, 0, 180])`
  4. A13, which becomes `l_max/2 + abs(RAIL_X) + 10 ≤ HALF_PITCH − PAD_BOSS_D/2`.

  A8 must evaluate **each lap separately** against the asymmetric rectangle. Re-derived worst case
  with B1: **1.87 mm on both laps** (≥ `ARCH_KEEPOUT_CLR` = 1.0). Correct §3.2's table to 1.87.
  If F1's fix ever drops the end-stop flange, `RAIL_X` becomes 0 automatically. Do **not** fix this
  by moving `XJ`: the centre bbox has only 4.3 mm left.
- **B2 — A9 checks the rib edges, not only their end corners.** For each of the 4 rib edge lines
  (arm-local `y = ±ARM_W/2`, `±(ARM_W/2 − RIB_T)`), sample from the rib end to `x = 0` in ≤ 1 mm
  steps. Assert every sample is ≥ `ARCH_KEEPOUT_CLR` outside the centre body rectangle, reusing
  `_mcc_arch_tv_circle_rect_gap()` with `r = 0`. A corner can lie outside the rectangle via `y`
  while the edge re-enters it further along. Today the margin is 4.85 either way, but the assert
  must be correct for every future `CENTRE_W` or `XJ`.
- **B3 — the UP arrow gets a size and an assert.** Add `ARROW_L = 8.0`, `ARROW_W = 6.0` (`assumed`,
  cosmetic). Put the arrow centre at centre-local
  `(−30, (KEEPOUT_Y_MAX + CENTRE_W/2) / 2)`, i.e. `y ≈ 15.45`, not the hand-typed `+14`. Add
  **T1-60**: the arrow's bbox stays ≥ `ARCH_KEEPOUT_CLR` inside the body edge and ≥ `ARCH_KEEPOUT_CLR`
  outside the rail keep-out rectangle. At `+14` with an unspecified size, a 6 mm arrow would sit
  0.09 mm off the latch nub's keep-out.
- **B4 — assert ids.** A1–A13 become **T1-47 … T1-59** in order, plus B3's **T1-60**. Every assert
  message carries its id (the highest in the repo today is T1-46).
- **B5 — use the correct citations** in code comments, assert messages and the BOM rows:
  `knowledge/components/fasteners-and-hardware.md:35` (RX-M3x5.7, 5.7 mm), `:40` (4.0 mm hole),
  `:56` (≈ 1400 N, PLA), `:59` (ASA/PETG/PC pull-out `unknown`). Do **not** copy
  `constants.scad`'s own stale `:17`/`:22` (follow-up, N4).
- **B6 — correct the slide-on travel.** The case can only engage once its leading end wall passes
  the rail's open end (see F1), so engagement starts at case centre
  `x = RAIL_X + MCC_RAIL_LEN/2 + L/2`, not `+MCC_RAIL_LEN`.
  - Add `slide_clear = MCC_RAIL_LEN/2 + l_max/2` (= 180.75) to the geom struct and the `echo()`
    summary.
  - `assembly_sweep` shifts the ghost case by `MCC_RAIL_LEN/2 + L_ghost/2`.
  - `models/brackets/README.md` and M18c state: "free space to the right of the mounted case's right
    edge ≥ `slide_clear` (≈ 181 mm), plus hand room, from 19 to 70 mm off the TV back" (replaces
    "≈ 150 mm").
  - Fix §1.3's first paragraph to match. The Z-stack conclusion is unchanged: the case still passes
    over the right pad.
- **B7 — one list of devices, and a hook for the next SKU.** Collect the 8 device records into one
  named list, `_ARCH_TV_DEVS = [MCC_DEV_…, …]`, consumed by `_mcc_arch_tv_envelope_max()`. Its
  header comment says "a new SKU must be added here". Also add one line to
  `.claude/skills/new-case-variant/SKILL.md`'s checklist: "if the new case can hang on
  `models/brackets/arch-tv-bracket.scad`, add its device include and record to `_ARCH_TV_DEVS`, then
  re-golden `brackets/arch-tv-bracket`." Reason: the IP-decoder family (120 × 79.3) is wider than
  the Plus family. If it were missed, A2 would silently pass while the case stuck up past the TV's
  top edge, breaking a user decision.
- **B8 — the CI change, narrowed.** On "Upload exports" in `.github/workflows/render.yml` use
  `if: ${{ !cancelled() }}`, not `if: always()`. The workflow has `cancel-in-progress: true`, and
  `always()` also uploads partial exports from superseded runs. Put it in its **own commit**
  (`ci: upload exports even when build.py all fails`) so it can be reviewed and reverted on its own.
  No security objection: the step runs no code, needs no secrets, and uploads only generated
  STL/3MF/summary/manifest files (fork PRs run with a read-only token).
- **B9 — A1 (T1-47) asserts the stricter cap, written as an expression.** Assert every bbox axis
  `≤ MCC_BUILD − 2 * MCC_BED_MARGIN`, never a literal `244`, and cite **D26** in the message.
  `mcc_bbox_ok()` may be called as well but is not the gate. Do **not** change `util.scad` in this PR
  (D26 has its own follow-up).
- **B10 — print gate wording.** The `models/brackets/README.md` and `print-check` `SKILL.md` rows
  read: "Do not print for use before **M15** (rail-latch), **M18** (TV measurements) and **R38**
  (rail entry/interference, F1) are closed." The README also says that the released STL is rendered
  for the **placeholder** `TV_TOP_CLEAR = 150`, and that a measured TV needs
  `render brackets/arch-tv-bracket -D TV_TOP_CLEAR=<mm>`.
- **B11 — the PR body names the two deviations from the issue text** so the user can veto them at
  review:
  - M3 instead of M4 lap screws (PLAN-ASSUMPTION-1).
  - The centre stands 8 mm off the TV; only the arms touch it (PLAN-ASSUMPTION-3).

  It also lists M18 and R38, and states "no existing golden moves; `tv-bracket.json` unchanged".

### 12.3 F1 — inherited from #25, escalated, not fixed here (proposed **R38**)

Evidence: an intersection render (OpenSCAD 2021.01, CGAL) of the case floor, the sill and
`mcc_rail_female_cut()` under `tv-bracket.scad`'s own mate transform, against the rotated
`mcc_rail_male()`. Four problems:

- **(a) No entry path.** The female groove is **blind at both ends**: 150 mm long in a 194.9 or
  211.5 mm floor, and nothing in `mounts.scad` or `shell.scad` runs it out through an end wall. The
  male taper stands 4 mm above the case's exterior floor plane, so no case can slide on, and the
  dovetail stops it being lowered on.
- **(b) The end stop sits in the floor.** At full mate the end-stop flange occupies
  `x ∈ [75, 81]`, case-local `z ∈ [0, 6]`, which **intersects the solid case floor (263 mm³)**. The
  stop concept (the flange hits un-grooved floor at `len/2`) contradicts any run-out on the entry
  side.
- **(c) The latch arm hits the groove flank.** The arm stands on the nominal root-width line, but
  the groove is tapered and the latch pocket covers only the nub. The arm intersects the groove
  flank/floor over `x ∈ [60, 69]` (42 mm³).
- **(d) The nub pocket is too shallow.** It does not account for `MCC_RAIL_LATCH_ARM_T`: the nub
  pokes 0.3 mm past it.

The `rail-latch` coupon cannot reveal (a) or (b): its female plinth is exactly `LEN` long, so the
groove is open at both ends and the plinth's end face acts as the stop. It is also not modelled
mated.

**Ruling:** open a separate ticket against `lib/mcc/rail.scad` / `mounts.scad` (an interface
redesign). It blocks use of *both* brackets and of the M15 pull test's meaning; it does **not**
block this PR. The arch bracket derives every rail-dependent value (keep-out, Z bbox, `RAIL_X`,
`slide_clear`) from `MCC_RAIL_*`, so it absorbs the fix with a re-golden and no code edit.

### 12.4 Non-binding notes

- **N1.** For torsion use `J ≈ β·b·t³` with `β ≈ 0.29` at b/t = 5 (≈ 6130 mm⁴, not 6990). Tilt
  rises ≈ 13 %, still ≈ 1° static.
- **N2.** Sink the rail foot and the arm ribs `MCC_EPS` into their plates (the `rail-latch.scad`
  lesson). `tv-bracket` passes `parts == 1` with coincident faces today, so this is optional.
- **N3.** Keep `_mcc_arch_tv_envelope_max()` cheap. A `use`d file re-evaluates its top-level
  assignments per call, and each call runs 8 × `mcc_case_layout()`. That is fine for 3 smoke values;
  do not add a large sweep to the smoke test.
- **N4.** Follow-up: `constants.scad:85-95` cites `fasteners-and-hardware.md:17/:22`, which are now
  `:35/:40`.
- **N5.** M18d acceptance (proposed, `assumed`): static rail tilt ≤ 2° after 24 h with the heaviest
  Plus SKU. If it fails, set `ARCH_PLATE_T = 10` and re-derive.
- **N6.** The README should say that the TV's top VESA holes must not also carry another mount
  (direct mount by user decision).

### 12.5 PLAN-ASSUMPTION rulings

| # | Ruling |
|---|---|
| 1 | **RATIFIED.** M3: sourced insert, blind in 8 mm, > 10× pull-out margin. M4 would re-derive the whole Z stack. The fastener size is not among the user's fixed decisions, but the PR body flags it for veto (B11) |
| 2 | **RATIFIED as `assumed`.** Both values stay named parameters with `-D` override. No print for use before M18a (B10) |
| 3 | **RATIFIED.** Re-derived (§12.1). The centre's 8 mm stand-off is forced by the +X sweep, not chosen. This does not re-open the direct-mount decision: the arms carry and bear on the TV. Stated in the PR (B11) |
| 4 | **RATIFIED.** The arm is symmetric about its own axis; the left arm is `rotate(alpha)`, a proper rotation; the laps land at `(±XJ, rise)` ✓. One STL, qty 2 in the BOM |
| 5 | **RATIFIED as a precedent, with conditions.** The architect records these in `architecture.md` §9: a test may `use` (never `include`) a `models/**` file; `lib/**` never references `models/**`; the model keeps all Tier-1 asserts in a public assert module, which it also calls at top level (`use` skips bare top-level asserts); the test never assigns `part`; public symbols carry the file's `mcc_arch_tv_` prefix |
| 6 | **RATIFIED** with B3 (defined size, T1-60). A cue, not a key (R-B stands) |
| 7 | **RATIFIED.** The `parts` marker is the right mechanism: it mirrors `extra_parts`, keeps every shared lap/rise parameter in one file, and is inert for `tv-bracket`. One file per part would need either L0 pollution or a shared `.scad` that `discover_brackets()` would glob as a target. The CI change is accepted with B8 |
| 8 | **RATIFIED.** Every material and mass figure is `assumed` and labelled so. `T = 8` is set by geometry; stiffness is only corroborative. M18d with N5's threshold is the real check |
| 9 | **RATIFIED.** ISO 4762/7089 nominals are correct standard values and properly labelled `assumed`, which is not an invented dimension. Researcher follow-up: source them into `knowledge/components/fasteners-and-hardware.md` |
| ¹ bbox | **Deviation D26.** Intended rule `MCC_BUILD − 2·MCC_BED_MARGIN` (244, per-side margin); violations at `lib/mcc/util.scad:43` and the `architecture.md` §9 Tier-1 row (250). Fix owner: a separate small ticket (change `util.scad`, prove it golden-neutral: every current caller is ≤ 230, and update §9). This PR asserts 244 explicitly (B9) |

**Ids the architect will record after merge (not the developer):**

- **T1-47 … T1-60**, assert ids (B4).
- **R30 … R37**, the plan's R-A … R-H in order.
- **R38**, F1.
- **M18a–d**, the TV measurements.
- **D26**, the bbox cap.
- **`architecture.md` rev 13, §3 rule update.** A bracket may `include` device data files, read-only,
  for previews or envelope derivation, and may list multiple parts via `// build.py: parts = …`.
  This legitimises `tv-bracket.scad:77` and B7.
- **§9**, the PLAN-ASSUMPTION-5 test precedent.
