# Plan F — gravity rail lock (rev 1): replace the D34 snap latch, always patch-wall down, DP48 lead-in

**Implemented as amended by the architect verdict appended at the end of this file. Where they conflict, the verdict wins.**

Status: **implementation plan, for the architect gate (rev 17) and then a Sonnet developer.** Every
decision is made below; where the developer meets something this plan does not describe, the answer
is **stop and report**, never improvise.

Baseline: **plan A as amended by its verdict, including Amendment 1** (`A-wide-dovetail.md` rev 2,
`A-wide-dovetail.VERDICT.md`: ROOT_W 65, `MCC_RAIL_Y` −23.5, no pedestal, flank/roof clearance 0.5,
`tv-bracket` retired, arch `ARCH_PLATE_T` 11 / `CENTRE_W` 92, `scripts/rail_fit.py` as the mate check).
Order: **C → A → F → D** (plan-D verdict rev 2). F is **architecture rev 17**; its reserved ids are
T1-64…T1-69, D48–D50, R44–R46, M21, Q23. This plan uses T1-64…66, D48–D50, R44–R45, M21 (Q23 unused).

User decisions this plan implements (2026-09-28):
1. **Gravity lock only.** A rigid bump on the rail's upper (−Y) flank drops into a pocket in the groove
   flank. **The D34 snap latch is removed completely**: arm, slot, nub, notch, `mcc_rail_male_window()`,
   `mcc_rail_male(plate_t)`, every `MCC_RAIL_LATCH_*` constant, `MCC_SNAP_STRAIN_MAX`, their asserts and
   every doc reference that exists only for them.
2. **A mounted case ALWAYS hangs patch-wall down** — every bracket, the truss use (#27) included, no
   portrait TV. A fixed decision; the lock depends on it.
3. **The DP48 1 × 45° lead-in** at the groove entrance (the case's +X wall passage).

Binding requirements from the plan-D verdict (rev 2):
- **F-R1**: a pure function `mcc_rail_male_keepout(len = MCC_RAIL_LEN)` in `lib/mcc/rail.scad`, returning
  `[[x_min, x_max], [y_min, y_max]]` rail-local — the plate-side keep-out, bump included.
- **F-R2**: a consumer puts the rail on its plate with one call, `union() { plate(); mcc_rail_male(len) }`
  — no plate cut. The arch migrates; after F no bracket calls `mcc_rail_male_window()` or reads
  `MCC_RAIL_LATCH_*`.
- **F-R3**: rev 17; `architecture.md` §3 gains the consumer rule (proposed text in Appendix X; the
  architect's verdict owns the final text).

Source analysis: `scratchpad/plans/F2-dp48-lock-analysis.md` (the DP48 reverse-engineering).

**Prototype evidence.** Every code change below was applied to a scratch copy of the plan-A
worktree (`feature/wide-dovetail` as of 2026-09-28 18:40, A's code appendices applied) and run:
`build.py smoke` 10/10 PASS; `render` + `check` PASS for three bases (NDI-to-HDMI, SDI TX W = 158.80,
HDMI Plus), the arch arm and centre, and the coupon (after the §6 strip fix); `rail_fit.py` **rail fit
OK** on all three SKUs (play 1.154 mm, max lift over the bump 0.703 mm, locked when hanging);
**Bambu Studio slicer-check: zero warnings** on the coupon, arch arm, arch centre and all three
bases; **exact STEP** (C's gate) OK on the coupon, a base and the arch centre. The arch arm's render
summary is identical to A's (its golden does not move). Scripts: `scratchpad/dp48v2/planF/`.

---

## 0. The design in numbers

Rail-local frame (the one `rail.scad` documents): X = slide axis, the case groove open at +X and
closed at −X; Y across the dovetail; Z = 0 at the plate / the case's exterior floor. Every bracket
places the rail with `rotate([0,0,180])` and the case hangs patch-wall down (D49), so the rail-local
**−Y flank is the upper, weight-bearing flank** (the far-wall side of the case rests on it).

| Item | Value | Tag |
|---|---|---|
| Lock bump location | male rail, **−Y flank**, on the solid rail core (no arm), full male height Z 0 → `MCC_RAIL_MALE_H` (3.5), swept parallel to the flank | decided (F2) |
| Bump protrusion `MCC_RAIL_LOCK_ENGAGE` | **0.70** horizontal (Y) = 0.61 normal to the 60° flank | assumed; DP48 uses 82 % of its lift play, this is 61 % of ours |
| Bump profile along X | entry ramp **30°** on −X (1.212 long), flat **1.0**, exit face **90°** (square) on +X | assumed; DP48 exit = 0.3 vertical + R0.5 (measured) |
| Bump position | exit face at `len/2 − 3.0` → **x 69.79 … 72.00** at len 150; **24.79 … 27.00** at len 60 | 3.0 = DP48's strip-to-trailing-end distance (measured) |
| Pocket (female, −Y flank) | the bump's outline grown by `MCC_RAIL_CLR_HORIZ` (0.577) in plan, **full groove depth** Z −ε → 4.0: axial play 0.577 each side, 0.577 horizontal (0.5 normal) over the bump's top, 0.5 over it at the roof | follows T1-62 |
| Flank play (A) | 2 × 0.577 = **1.155** horizontal; a hanging case can move 1.155 toward the far wall | from A |
| Ride-over lift | **0.70**; the lower flank keeps **0.455** horizontal (0.39 normal) meanwhile; T1-64 demands ≥ 0.2 | derived; prototype measured 0.703 |
| What flexes | **nothing** — the case shifts/yaws rigidly inside the dovetail's own play | derived |
| Lock preload | the case's weight on the upper flank: 1.155 W normal (pure shift) down to ≈ 0.59 W (yaw about the −X end) | derived; W ≈ 6–8 N assumed |
| Axial retention while hanging | **self-locking** (square exit face): no cam, limited by the face's bearing (≈ 100 N at an assumed 40–45 MPa) | derived/assumed |
| Release | lift the case until it stops on the lower flank (≤ 1.15 mm), then slide it back off | derived |
| Lead-in `MCC_RAIL_LEADIN` | **1.0**: at the case's +X outer face (X = L/2) the flanks and the mouth flare 1.0 per side over the last 1.0 mm (45° in plan); the roof stays at 4.0 | DP48 1.0 × 45° entry chamfer (measured) |
| Sill wall behind the pocket, at the roof | 3.0 − 0.577 − 0.70 = **1.72** (T1-66 demands ≥ `MCC_WALL/2` = 1.5) | derived |
| Plate-side keep-out `mcc_rail_male_keepout()` | `[[−len/2, len/2], [−(ROOT_W/2 + 0.70), ROOT_W/2]]` = `[[−75, 75], [−33.2, 32.5]]` | conservative (ROOT_W/2 ≥ the male's 32.21 top) |
| Arch keep-out (rotated) | `RAIL_KEEPOUT_Y` **[−32.5, 33.2]** (was [−32.5, 36.1]); `RAIL_KEEPOUT_X` [−75, 75] unchanged | derived |

Release direction, in words for users: the case slides **back off the way it went on**. The groove
opens at the case's +X end wall (the fan end), so a case is hung with that end toward the rail's free
end and pushed along until it clicks.

---

## 1. Preconditions and anchors to re-verify after A lands

1. A is merged on `main` (after C). Branch **`feature/gravity-lock`** from `main`. If the teamlead
   explicitly allows starting earlier, branch from `feature/wide-dovetail`'s approved, CI-green head
   and rebase onto `main` after A merges — then redo steps 9–15 of §12 and regenerate the goldens;
   never hand-merge golden JSON.
2. `.claude/knowledge/architecture.md` contains `**Revision 16, 2026-09-28` and rows `| **D44** |` …
   `| **D47** |`.
3. Every anchor below must be found **exactly once, verbatim**. They are quoted from A's verdict
   appendices and the in-progress A worktree (2026-09-28 18:40). **If any anchor is missing or differs,
   stop and report** — A's review may have reworded it; the architect then re-anchors.

| File | Anchor (exact text) |
|---|---|
| `lib/mcc/constants.scad` | `// Section: Mount rail (dovetail + spring-lip latch) — issue #25, replaces VESA (D-15, rev 9)` |
| | a line starting `// Rail latch — REDESIGNED 2026-09-28 (issue #46, architecture.md §13 D34; replaces the D28` |
| | a line starting `MCC_RAIL_PASSAGE_ROOF_MIN = 1.2;` (below the previous one) |
| | `                            // offset of the female groove and latch notch from the male profile that` |
| | `MCC_RAIL_ROOF_CLR = MCC_RAIL_MATE_CLR; // = 0.5. Gap between the male's flat top (and the nub's) and` |
| | `                            // bridge in the base's print pose (architecture.md R40) -- if the rail-latch` |
| `lib/mcc/rail.scad` | `//   it), plus the pure mcc_rail_sill_size() accessor. NOT named bracket.scad (architecture.md §3` |
| | `// runs into. The male slides in -X relative to the case; the latch sits on the -Y flank near the` |
| | `//   Private. The dovetail taper alone (no latch): a prismoid from MCC_RAIL_MOUTH_W at local Z=0,` |
| | `// Latch geometry (issue #46, architecture.md §13 D34). Everything below is derived from the` |
| | `// Module: _mcc_rail_taper_eps()` |
| `lib/mcc/mounts.scad` | `        // Open at +X through the case wall (D34): the groove's closed -X end is the end stop.` |
| | `            mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = L / 2 - MCC_RAIL_LEN / 2 + 1);` |
| `models/brackets/arch-tv-bracket.scad` | a comment line starting `// Rail keep-out rectangle, centre-local frame, B1-shifted` and, 4 lines below, a line starting `RAIL_KEEPOUT_Y = [` |
| | a line starting `CENTRE_W = 92.0; // mm.` and, 3 lines below, `                  // 14.6 mm rail.` |
| | `    // The rail is unioned AFTER the plate's own cuts: its latch arm's leg fills the window` |
| | `        translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male_window(plate_t = ARCH_PLATE_T);` |
| | `    // onto this plate's own top face; plate_t lets the latch arm's leg reach the bed.` |
| | `    translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male(plate_t = ARCH_PLATE_T);` |
| | `M15 (rail-latch pull test)` |
| | `//   Z stack, RAIL_X, slide_clear) derives from MCC_RAIL_* so a future rail fix is absorbed by a` |
| `models/coupons/rail-latch.scad` | the file exists (A's D.3 version, calling `mcc_rail_male_window(len = LEN, plate_t = PLATE_T)` and `mcc_rail_male(len = LEN, plate_t = Z0)`) |
| `tests/test_rail.scad` | a line starting `// --- Latch (issue #46, D34): snap-fit rules`; a line starting `assert(MCC_RAIL_END_STOP_L == 0 && MCC_RAIL_END_STOP_H == 0` |
| | `translate([0, -60, 0]) mcc_rail_male(plate_t = 6); // with the arm's leg through a 6 mm plate` |
| | `        mcc_rail_female_cut(open_ext = 20);` and `        mcc_rail_female_cut(len = 60);` |
| | `//     - T1-62 (D44): ` (header) |
| `scripts/rail_fit.py` | the file exists (A's D.4 version; F replaces it whole) |

4. Confirm the whole region of `rail.scad` from the `// Latch geometry` anchor to
   `// Module: _mcc_rail_taper_eps()` contains exactly these definitions and nothing else:
   `_mcc_rail_flank_k`, `_mcc_rail_latch_geom`, `_mcc_rail_nub_2d`, `_mcc_rail_flank_extrude`,
   `_mcc_rail_latch_cut_2d`, `mcc_rail_male_window`, `mcc_rail_male`, `mcc_rail_female_cut`. Anything
   else there: stop and report.
5. `grep -rln --include=*.scad --include=*.py "mcc_rail_male_window\|MCC_RAIL_LATCH\|MCC_SNAP_STRAIN_MAX\|\bplate_t\b" lib models tests scripts`
   must list only `lib/mcc/rail.scad`, `lib/mcc/constants.scad`, `models/brackets/arch-tv-bracket.scad`,
   `models/coupons/rail-latch.scad`, `tests/test_rail.scad` and `scripts/rail_fit.py` (the last may
   not appear: A's version reads `MCC_RAIL_Y` only). Any other file — for example a vertical-bracket
   file — stop and report.

---

## 2. `lib/mcc/constants.scad`

**F2.1** Replace the section header
```
// Section: Mount rail (dovetail + spring-lip latch) — issue #25, replaces VESA (D-15, rev 9)
```
with
```
// Section: Mount rail (dovetail + gravity lock) — issue #25, replaces VESA (D-15, rev 9; lock D48)
```

**F2.2** Delete every line from the one starting `// Rail latch — REDESIGNED 2026-09-28 (issue #46,`
down to, **not including**, the line starting `MCC_RAIL_PASSAGE_ROOF_MIN = 1.2;`. That removes the latch
comment block, `MCC_RAIL_LATCH_ENABLED`, `_ARM_L`, `_ARM_T`, `_ROOT_FILLET`, `_ENGAGE`, `_SLOT`,
`_RAMP_IN`, `_RAMP_OUT`, `_FLAT`, `_WINDOW_CLR`, `MCC_SNAP_STRAIN_MAX`, `_LEAD_IN` and `MCC_RAIL_LATCH_X`
(with its continuation comment). Put this block in their place, followed by nothing else (the
`MCC_RAIL_PASSAGE_ROOF_MIN` line follows directly):
```openscad
// Rail lock -- a GRAVITY lock (user decision 2026-09-28, architecture.md §13 D48; it replaces the D34
// snap latch, which is removed). A rigid bump on the male rail's -Y flank, near its +X end, drops into
// a pocket in the case groove's -Y flank at full insertion. Every bracket places the rail with
// rotate([0,0,180]) and a mounted case always hangs patch-wall down (fixed decision, D49), so the -Y
// flank is the upper one: the case's weight rests on it (about 1.15 x the weight, normal to the 60 deg
// flank) and holds the bump in its pocket. Nothing flexes: sliding on, the case rides over the bump
// inside the dovetail's own flank play (2 x MCC_RAIL_CLR_HORIZ = 1.155 mm horizontal, T1-64); the exit
// face is square to the slide axis, so an axial pull cannot cam a hanging case out. Release: lift the
// case about 1 mm (it stops on the lower flank) and slide it back off. Reference: the external
// specialist's DP48 plate -- 0.8 mm strips riding inside 0.97 mm of dovetail play (analysis F2).
MCC_RAIL_LOCK_ENGAGE = 0.70;      // bump protrusion beyond the flank, horizontal (Y), mm (0.61 normal to
                                   // the flank). assumed: the DP48 uses 82 % of its lift play, this is
                                   // 61 % of ours, leaving 0.45 mm for FDM tolerance. Tuned on the
                                   // rail-lock coupon's e-ladder (M15).
MCC_RAIL_LOCK_PLAY_MARGIN = 0.2;  // horizontal flank play that must remain while the bump rides the
                                   // groove flank, mm (T1-64). assumed.
MCC_RAIL_LOCK_RAMP_IN = 30;       // entry ramp (the bump's -X side) to the slide axis, deg. assumed (the
                                   // D34 nub's entry angle).
MCC_RAIL_LOCK_RAMP_OUT = 90;      // exit face (the bump's +X side) to the slide axis, deg. 90 = square:
                                   // self-locking against an axial pull at any friction (T1-65). assumed.
MCC_RAIL_LOCK_FLAT = 1.0;         // bump flat top length along X, mm. assumed.
MCC_RAIL_LOCK_END_OFFSET = 3.0;   // male's +X (trailing) end to the bump's exit face, mm. assumed -- the
                                   // DP48 strips sit 3.0-5.0 mm from their trailing end (F2). rail.scad
                                   // derives the position from its own `len`, so the 60 mm coupon works.
MCC_RAIL_LEADIN = 1.0;            // 45-deg lead-in where the groove leaves the case's +X wall: flanks and
                                   // mouth flare by this much per side (horizontal) over the last this-many
                                   // mm; the roof stays. The DP48's 1.0 x 45 deg entry chamfer (F2). assumed.
```
Every new value is a plain numeric literal on purpose: `scripts/rail_fit.py` reads them with a
literal-only regex.

**F2.3** In the `MCC_RAIL_CLR_HORIZ` comment replace `offset of the female groove and latch notch from the male profile that`
with `offset of the female groove and lock pocket from the male profile that`.

**F2.4** In the `MCC_RAIL_ROOF_CLR` line replace `(and the nub's)` with `(and the lock bump's)`, and in its
continuation replace `-- if the rail-latch` with `-- if the rail-lock`.

Nothing else in this file changes. Keep `MCC_RAIL_PASSAGE_ROOF_MIN`, `MCC_RAIL_END_STOP_L/H` (still read
by the arch; out of scope) and every D44 constant exactly as A left them.

---

## 3. `lib/mcc/rail.scad`

**F3.1** Header. Replace the two lines
```
//   it), plus the pure mcc_rail_sill_size() accessor. NOT named bracket.scad (architecture.md §3
//   rev 9, R4/layout-patch-wall.md §17.2): the name describes the INTERFACE, not one of its two
```
with
```
//   it), plus the pure accessors mcc_rail_sill_size() and mcc_rail_male_keepout() (the plate-side
//   keep-out every bracket reads -- D50). NOT named bracket.scad (architecture.md §3 rev 9,
//   R4/layout-patch-wall.md §17.2): the name describes the INTERFACE, not one of its two
```

**F3.2** Replace the three lines
```
// runs into. The male slides in -X relative to the case; the latch sits on the -Y flank near the
// open end (+len/2 - MCC_RAIL_LATCH_LEAD_IN). Before D34 the groove was closed at BOTH ends, so no
// case could ever be slid onto a bracket.
```
with
```
// runs into. The male slides in -X relative to the case; the gravity-lock bump sits on the -Y flank
// near the male's +X end (len/2 - MCC_RAIL_LOCK_END_OFFSET, D48), and the groove's exit through the
// case's +X wall has a 45-degree lead-in (D48). Before D34 the groove was closed at BOTH ends, so no
// case could ever be slid onto a bracket.
```

**F3.3** In `_mcc_rail_taper()`'s doc replace `The dovetail taper alone (no latch):` with
`The dovetail taper alone (no lock):`.

**F3.4** Replace the whole region that starts with the separator line `// ------…` directly **above**
`// Latch geometry (issue #46, architecture.md §13 D34). Everything below is derived from the` and ends
directly **before** the line `// Module: _mcc_rail_taper_eps()` with the block below. The block ends with
one empty line, so exactly one empty line separates its last `}` from `// Module: _mcc_rail_taper_eps()`.
It deletes `_mcc_rail_latch_geom()`, `_mcc_rail_nub_2d()`, `_mcc_rail_latch_cut_2d()` and
`mcc_rail_male_window()`, keeps `_mcc_rail_flank_k()` and `_mcc_rail_flank_extrude()` (re-documented;
the taper uses the first), adds `_mcc_rail_lock_geom()`, `_mcc_rail_lock_2d()` and
`mcc_rail_male_keepout()`, and rewrites `mcc_rail_male()` (no `plate_t`) and `mcc_rail_female_cut()`
(new `entry_x`, `lock_e`). The T1-38 and T1-62 asserts keep A's messages; their comparisons are
merely written the other way round.
```openscad
// -----------------------------------------------------------------------------------------
// Flank helpers. The lock bump (male) and its pocket (female) are drawn in plan view at the mouth
// flank line (y = -MOUTH_W/2, the plate top) and swept up the -Y flank by _mcc_rail_flank_extrude(),
// so both stay parallel to the flank by construction.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_flank_k()
// Description: Private. Outward (-Y) run of the -Y flank per mm of height over the taper.
function _mcc_rail_flank_k() = (MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH);

// Module: _mcc_rail_flank_extrude()
// Description:
//   Private. Extrudes a plan-view 2-D child (drawn at the mouth flank line) over z0..z1 of the shared
//   frame so it follows the -Y flank: sheared outward with the dovetail taper above Z=0, straight
//   below it. Male Z = female Z since D44, so the same helper places the lock bump and cuts its
//   pocket.
module _mcc_rail_flank_extrude(z0, z1) {
    zb = 0;
    k = _mcc_rail_flank_k();
    if (z0 < zb)
        translate([0, 0, z0]) linear_extrude(height = min(z1, zb) - z0 + MCC_EPS) children();
    if (zb < z1)
        multmatrix([[1, 0, 0, 0], [0, 1, -k, k * zb], [0, 0, 1, 0], [0, 0, 0, 1]])
            translate([0, 0, max(z0, zb)]) linear_extrude(height = z1 - max(z0, zb)) children();
}

// -----------------------------------------------------------------------------------------
// Gravity lock (user decision 2026-09-28, architecture.md §13 D48 -- replaces the D34 snap latch). A
// RIGID bump on the male's -Y flank, near its +X end, drops into a pocket in the groove's -Y flank at
// full insertion. Every bracket places the rail with rotate([0,0,180]) and a mounted case always hangs
// patch-wall down (D49), so the -Y flank is the upper one: the case's weight rests on it and holds the
// bump in its pocket. Nothing flexes -- sliding on, the case rides over the bump inside the
// dovetail's own flank play (T1-64). The exit face is square to the slide axis, so an axial pull
// cannot cam a hanging case out; lifting the case about 1 mm (onto the lower flank) releases it.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_lock_geom()
// Description:
//   Private, pure. [x0, x1, ramp_in_l, ramp_out_l] of the lock bump for a rail of working length
//   `len` and protrusion `e`: exit face (its +X side) at len/2 - MCC_RAIL_LOCK_END_OFFSET, then the
//   flat top and the entry ramp toward -X. The male slides in -X relative to the case, so the
//   groove's open end meets the entry ramp first; withdrawing, the pocket's +X wall meets the exit
//   face.
function _mcc_rail_lock_geom(len, e = MCC_RAIL_LOCK_ENGAGE) =
    let(
        r_in = e / tan(MCC_RAIL_LOCK_RAMP_IN),
        r_out = MCC_RAIL_LOCK_RAMP_OUT == 90 ? 0 : e / tan(MCC_RAIL_LOCK_RAMP_OUT),
        x1 = len / 2 - MCC_RAIL_LOCK_END_OFFSET,
        x0 = x1 - r_out - MCC_RAIL_LOCK_FLAT - r_in
    )
    [x0, x1, r_in, r_out];

// Module: _mcc_rail_lock_2d()
// Description:
//   Private. The lock bump's plan outline at the mouth flank line, grown by `grow` (0 = the male
//   bump; MCC_RAIL_CLR_HORIZ = the female pocket). It reaches 0.2 mm into the rail core so the union
//   with the taper shares real volume.
module _mcc_rail_lock_2d(len, e = MCC_RAIL_LOCK_ENGAGE, grow = 0) {
    g = _mcc_rail_lock_geom(len, e);
    y0 = -MCC_RAIL_MOUTH_W / 2;
    offset(delta = grow)
        polygon([
            [g[0], y0 + 0.2],
            [g[0], y0],
            [g[0] + g[2], y0 - e],
            [g[1] - g[3], y0 - e],
            [g[1], y0],
            [g[1], y0 + 0.2],
        ]);
}

// Function: mcc_rail_male_keepout()
// Usage:
//   ko = mcc_rail_male_keepout([len]);   // [[x_min, x_max], [y_min, y_max]]
// Description:
//   Pure. The conservative plan-view extent, in the shared rail-local frame, of everything
//   mcc_rail_male() puts on or into a consumer's plate: the taper (bounded by MCC_RAIL_ROOT_W, wider
//   than the male's own MCC_RAIL_MALE_H top) plus the lock bump on the -Y flank. The rail needs no
//   cut in the plate (D50): a consumer unions mcc_rail_male() onto its plate and keeps its other plate
//   features out of this rectangle, adding its own clearance. A rotate([0,0,180]) placement negates
//   and swaps both ranges. Brackets read this, never the MCC_RAIL_LOCK_* constants (architecture.md
//   §3, D50).
// Arguments:
//   len = working length, mm. Default: MCC_RAIL_LEN.
function mcc_rail_male_keepout(len = MCC_RAIL_LEN) =
    [[-len / 2, len / 2], [-MCC_RAIL_ROOT_W / 2 - MCC_RAIL_LOCK_ENGAGE, MCC_RAIL_ROOT_W / 2]];

// Module: mcc_rail_male()
// Usage:
//   union() { plate(); mcc_rail_male([len=]); }
// Description:
//   ADDITIVE. The male dovetail rail (bracket side): the shared taper, MCC_RAIL_MALE_H tall, standing
//   directly on the consumer's plate (no pedestal since D44 -- the case floor rests flush on it), over
//   the working length [-len/2, +len/2], with the rigid gravity-lock bump on its -Y flank (D48). No
//   separate end stop (D34): the case groove's closed -X end stops the rail's -X end face. The rail
//   needs no cut in the consumer's plate (D50): the consumer unions it on and keeps its other plate
//   features out of mcc_rail_male_keepout().
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   lock_e = lock bump protrusion, mm. Default: MCC_RAIL_LOCK_ENGAGE. Only the rail-lock coupon's
//            e-ladder passes another value, and always the same one to mcc_rail_female_cut().
module mcc_rail_male(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    g = _mcc_rail_lock_geom(len, lock_e);
    // T1-64 (D48): the bump rides over the groove flank inside the dovetail's own flank play
    // (2 x MCC_RAIL_CLR_HORIZ), with MCC_RAIL_LOCK_PLAY_MARGIN to spare -- nothing is designed to flex.
    assert(0 < lock_e && lock_e + MCC_RAIL_LOCK_PLAY_MARGIN <= 2 * MCC_RAIL_CLR_HORIZ + MCC_EPS,
        str("mcc: T1-64 rail lock bump ", lock_e, " + margin ", MCC_RAIL_LOCK_PLAY_MARGIN,
            " does not fit the flank play ", 2 * MCC_RAIL_CLR_HORIZ));
    // T1-65 (D48): exit face 75..90 deg to the slide axis (90 = square, self-locking at any friction),
    // entry ramp 15..60 deg, and the whole bump inside the working length.
    assert(75 <= MCC_RAIL_LOCK_RAMP_OUT && MCC_RAIL_LOCK_RAMP_OUT <= 90,
        str("mcc: T1-65 rail lock exit face ", MCC_RAIL_LOCK_RAMP_OUT, " deg outside 75..90"));
    assert(15 <= MCC_RAIL_LOCK_RAMP_IN && MCC_RAIL_LOCK_RAMP_IN <= 60,
        str("mcc: T1-65 rail lock entry ramp ", MCC_RAIL_LOCK_RAMP_IN, " deg outside 15..60"));
    assert(-len / 2 + 5 < g[0] && g[1] < len / 2 - 1,
        str("mcc: T1-65 rail lock bump x=", [g[0], g[1]], " does not fit inside len=", len));

    union() {
        // D44: no pedestal -- the taper stands directly on the consumer's plate (local Z=0),
        // MCC_RAIL_ROOF_CLR short of the groove roof.
        _mcc_rail_taper(len, h = MCC_RAIL_MALE_H);
        // D48: the lock bump, swept up the -Y flank from the plate top to the core's own top. It
        // stands on the plate at Z=0 and fuses to it: it is rigid by design.
        _mcc_rail_flank_extrude(0, MCC_RAIL_MALE_H) _mcc_rail_lock_2d(len, lock_e);
    }
}

// Module: mcc_rail_female_cut()
// Usage:
//   mcc_rail_female_cut([len=], [open_ext=], [entry_x=], [lock_e=]);
// Description:
//   SUBTRACTIVE. The matching dovetail groove (case-floor side): the shared taper widened by
//   MCC_RAIL_CLR_HORIZ per side (at least MCC_RAIL_MATE_CLR normal to the flanks, D44), from its
//   CLOSED -X end (the end stop, D34) at -len/2 through +len/2 and on by `open_ext` -- the passage
//   the male enters through, which the case runs out through its +X wall. Plus the gravity-lock
//   pocket in the -Y flank (the bump's outline grown by MCC_RAIL_CLR_HORIZ, following the flank, over
//   the groove's full depth -- D48) and, when `entry_x` is given, a 45-degree lead-in where the
//   groove leaves the part: flanks and mouth flare by MCC_RAIL_LEADIN per side over the last
//   MCC_RAIL_LEADIN mm before the face at X = entry_x; the roof stays at MCC_RAIL_DEPTH (D48). Local
//   frame: mouth at Z=0 = the case's exterior floor face, +Z into the case; a MCC_EPS overlap below
//   Z=0 pierces that face cleanly.
//   T1-38 (rev 9 R1): at least MCC_FLOOR_T of floor remains above the groove over the working length.
// Arguments:
//   len      = working length, mm. Default: MCC_RAIL_LEN. Must match the mating mcc_rail_male().
//   open_ext = how far the groove continues past +len/2 (the insertion passage), mm. Default 0.
//   entry_x  = X of the outer face the groove leaves through (a case: its +X wall, L/2), mm. Default
//              undef = no lead-in. Must lie in [len/2, len/2 + open_ext].
//   lock_e   = lock bump protrusion, mm. Default MCC_RAIL_LOCK_ENGAGE -- always the male's value.
module mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = 0, entry_x = undef, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    assert(MCC_FLOOR_T - MCC_EPS <= MCC_RAIL_SILL_H - MCC_RAIL_DEPTH,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));
    // T1-62 (D44): at least MCC_RAIL_MATE_CLR on every non-bearing face -- normal to the flanks, and
    // at the roof over the male's (and the lock bump's) shortened top.
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
        str("mcc: T1-62 rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
            " mm normal, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
        str("mcc: T1-62 rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
            " mm, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    // T1-66 (D48): the sill side wall behind the lock pocket keeps at least MCC_WALL/2 at the roof,
    // and the lead-in stays inside the wall it is cut into.
    assert(MCC_WALL / 2 - MCC_EPS <= MCC_RAIL_SILL_SIDE_W - MCC_RAIL_CLR_HORIZ - lock_e,
        str("mcc: T1-66 sill wall behind the rail lock pocket = ",
            MCC_RAIL_SILL_SIDE_W - MCC_RAIL_CLR_HORIZ - lock_e, " mm, below MCC_WALL/2"));
    assert(MCC_RAIL_LEADIN <= MCC_WALL + MCC_EPS,
        str("mcc: T1-66 rail lead-in ", MCC_RAIL_LEADIN, " mm deeper than MCC_WALL=", MCC_WALL));
    assert(is_undef(entry_x) || (len / 2 - MCC_EPS <= entry_x && entry_x <= len / 2 + open_ext + MCC_EPS),
        str("mcc: rail_female_cut entry_x=", entry_x, " outside [len/2, len/2 + open_ext]"));
    clr = MCC_RAIL_CLR_HORIZ;

    union() {
        // No Z shift: _mcc_rail_taper_eps() already pierces Z=0 with its own slab, so the groove roof
        // sits at exactly MCC_RAIL_DEPTH.
        translate([open_ext / 2, 0, 0])
            _mcc_rail_taper_eps(len + open_ext, clr, MCC_EPS);
        // D48: the lock pocket, over the groove's FULL depth, so the bump (which stops at
        // MCC_RAIL_MALE_H) keeps MCC_RAIL_ROOF_CLR above its top and MCC_RAIL_CLR_HORIZ around it.
        _mcc_rail_flank_extrude(-MCC_EPS, MCC_RAIL_DEPTH)
            _mcc_rail_lock_2d(len, lock_e, grow = clr);
        // D48: the DP48-style 45-degree lead-in at the outer face the male enters through.
        if (!is_undef(entry_x))
            hull() {
                translate([entry_x - MCC_RAIL_LEADIN, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr, MCC_EPS);
                translate([entry_x + MCC_EPS, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr + MCC_RAIL_LEADIN, MCC_EPS);
            }
    }
}

```
`_mcc_rail_taper_eps()` and everything above `_mcc_rail_taper()`'s end stay as A left them.

---

## 4. `lib/mcc/mounts.scad` (the case floor)

**F4.1** In `mcc_rail_features_cut()` replace
```
        // Open at +X through the case wall (D34): the groove's closed -X end is the end stop.
```
with
```
        // Open at +X through the case wall (D34): the groove's closed -X end is the end stop. The
        // +X outer face (x = L/2) gets the 45-degree lead-in (D48).
```
and replace
```
            mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = L / 2 - MCC_RAIL_LEN / 2 + 1);
```
with
```
            mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = L / 2 - MCC_RAIL_LEN / 2 + 1, entry_x = L / 2);
```
Nothing else in `mounts.scad` changes: the sill (`ROOT_W + 2·SILL_SIDE_W`) contains the pocket (its
outer wall at the roof stays 1.72 mm thick, T1-66), and the `"mount_rail"` floor keep-out row stays as
it is — the pocket lies inside the sill, and the D34 notch it replaces reached 1.3 mm further out.

---

## 5. `models/brackets/arch-tv-bracket.scad` (F-R2 migration, no geometry of its own)

**F5.1** Replace the comment block that starts with the line `// Rail keep-out rectangle, centre-local frame, B1-shifted`
through the line starting `RAIL_KEEPOUT_Y = [` (inclusive; 5 lines: 3 comment lines, `RAIL_KEEPOUT_X`,
`RAIL_KEEPOUT_Y`) with:
```openscad
// Rail keep-out rectangle, centre-local frame, B1-shifted: the rail's own plate-side keep-out
// (mcc_rail_male_keepout(), rail-local) mapped through this file's rotate([0,0,180]) rail
// placement, which negates and swaps both ranges -- the lock bump on the rail-local -Y flank
// lands at +Y here. D50 / F-R1: never built from MCC_RAIL_* internals.
_RAIL_KO = mcc_rail_male_keepout(MCC_RAIL_LEN);
RAIL_KEEPOUT_X = [RAIL_X - _RAIL_KO[0][1], RAIL_X - _RAIL_KO[0][0]];
RAIL_KEEPOUT_Y = [-_RAIL_KO[1][1], -_RAIL_KO[1][0]];
```
Result: `RAIL_KEEPOUT_X` = [−75, 75] (unchanged), `RAIL_KEEPOUT_Y` = [−32.5, 33.2] (was [−32.5, 36.1]).

**F5.2** Replace the line starting `CENTRE_W = 92.0; // mm.` and its three continuation comment lines
(the last one is `                  // 14.6 mm rail.`) with:
```openscad
CENTRE_W = 92.0; // mm. D44: holds the rail keep-out Y span (T1-53) and the UP arrow above it
                  // (T1-60). Sized for the D34 latch's [-32.5, +36.1]; since D48 the keep-out
                  // (mcc_rail_male_keepout()) is [-32.5, +33.2], so T1-60 needs only
                  // 2 x (33.2 + 1 + 6 + 1) = 82.4 and 92 leaves 2.4 mm on both of its bounds.
                  // Kept at 92 so D48 moves no bracket outline. Was 40 for the 14.6 mm rail.
```
Do **not** change the value 92.0.

**F5.3** In `mcc_arch_tv_centre()`:
- replace the two comment lines
  `    // The rail is unioned AFTER the plate's own cuts: its latch arm's leg fills the window` and
  `    // mcc_rail_male_window() cuts through this plate (issue #46, D34) down to the bed.` with the one line
  `    // The rail is unioned after the plate's own cuts; it needs no cut of its own in the plate (D50).`
- **delete** the line
  `        translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male_window(plate_t = ARCH_PLATE_T);`
- replace `    // onto this plate's own top face; plate_t lets the latch arm's leg reach the bed.` with
  `    // onto this plate's own top face (D50: one union, no plate cut).`
- replace `    translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male(plate_t = ARCH_PLATE_T);`
  with `    translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male();`

**F5.4** Comments: replace `M15 (rail-latch pull test)` with `M15 (rail-lock coupon)`, and in the header
replace `//   Z stack, RAIL_X, slide_clear) derives from MCC_RAIL_* so a future rail fix is absorbed by a`
with `//   Z stack, RAIL_X, slide_clear) derives from MCC_RAIL_* or mcc_rail_male_keepout(), so a future rail fix is absorbed by a`.

Effects (all from existing formulas, no other edit): the rail loses the latch arm and window and gains
the bump; the UP arrow's `arrow_y` moves from 41.05 to 39.6 (T1-60 margins 2.4 / 2.4 mm); T1-53 and
T1-54 gain margin. `RAIL_X`, `MCC_RAIL_END_STOP_L/H` and every other line stay.

---

## 6. The coupon: `rail-latch` becomes `rail-lock`

**F6.1** `git mv models/coupons/rail-latch.scad models/coupons/rail-lock.scad`, then replace the whole
file content with:
```openscad
//////////////////////////////////////////////////////////////////////
// models/coupons/rail-lock.scad
//   Tier-4 physical coupon (architecture.md §9). A short groove tile (case-floor stand-in,
//   mcc_rail_female_cut()) plus a matching short rail (bracket-plate stand-in, mcc_rail_male()), at
//   MCC_RAIL_LEN's real cross-section but a shorter LEN=60 mm working length -- a fit/lock test, not a
//   full-length print (docs/plans/2026-09-09-mount-rail-and-brackets.md §2). It checks the D44
//   clearances (0.5 mm normal to the flanks and at the roof -- MCC_RAIL_MATE_CLR is a user decision,
//   confirmed here, not calibrated), the groove-roof bridge (architecture.md R40: the groove half
//   prints exactly like the case floor), the 45-degree lead-in, and the gravity lock (D48): the rigid
//   bump on the rail's -Y flank rides over the groove flank inside the dovetail's own play, clicks into
//   its pocket, and -- with the rail plate vertical and the groove half hanging on the upper flank --
//   cannot be pulled out along the rail until the groove half is lifted about 1 mm (M15).
//
//   The groove half stands directly on the bed, groove mouth down and OPEN, like the case floor; the
//   rail half stands on its own plate. Two thin snap-off strips beside the groove join them so the
//   coupon renders/checks as one connected shell (architecture.md §9 Tier 3). Snap the strips off
//   before testing.
//
//   e-ladder (M15): LOCK_E below is passed to BOTH halves. The exported part uses the production
//   MCC_RAIL_LOCK_ENGAGE; for the ladder, render extra copies with -D LOCK_E=0.5 / 0.6 / 0.8 (see
//   models/coupons/README.md "rail-lock").
//
// Render:
//   openscad --backend=Manifold -o out/rail-lock.stl models/coupons/rail-lock.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="(file-stem)" (the export part name -- see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter -- side-bolt.scad:26-29's documented convention.
part = "rail-lock";

LEN = 60; // working (dovetail) length under test, mm. Well under MCC_RAIL_LEN=150 -- brief's own
           // "short groove tile" instruction (docs/plans/2026-09-09-mount-rail-and-brackets.md §2).
LOCK_E = MCC_RAIL_LOCK_ENGAGE; // lock bump protrusion for THIS print, mm -- the e-ladder overrides it
                               // with -D; both halves always get the same value.
MARGIN = 6; // plinth/plate footprint margin beyond MCC_RAIL_ROOT_W, mm. assumed -- wall support
             // around the groove/rail cross-section, generous enough to print cleanly.
GAP = 20; // gap between the female half's own footprint and the male half's, mm. assumed --
           // handling/labelling clearance; the snap-off strips still connect them into one printed
           // shell for the CI mesh check (see the file header comment).
PLATE_T = MCC_FLOOR_T; // the rail half's own plate thickness, mm -- its "bracket plate" stand-in
                         // (mcc_rail_male()'s own local Z=0 sits at its TOP face).

footprint_d = MCC_RAIL_ROOT_W + 2 * MARGIN; // Y footprint shared by both halves' own solid stock.

x_female0 = 0;             // female groove's own [0, LEN] working length, local X; the plinth adds
                           // a MCC_WALL end-stop wall at -X (the groove's CLOSED end, D34) and the
                           // groove runs out open through the plinth's +X end, like the case.
x_male0   = LEN + GAP;     // male rail's own working-length footprint starts here, local X.
x_base0   = -MCC_WALL;     // the coupon's -X extent: the female's stop wall.
STRIP_W   = 2.0;           // snap-off joining strip width, mm. assumed -- thin enough to break by hand.
base_w    = x_male0 + LEN + MARGIN - x_base0;
base_d    = footprint_d;

// This coupon's own lock position, re-derived from ITS OWN (short) LEN, exactly as lib/mcc/rail.scad
// does: the bump's exit face sits MCC_RAIL_LOCK_END_OFFSET inside the rail's +X end.
_lock_exit_x_here = LEN / 2 - MCC_RAIL_LOCK_END_OFFSET;

echo(str(
    "rail-lock: len=", LEN, " sill_h=", MCC_RAIL_SILL_H, " depth=", MCC_RAIL_DEPTH,
    " mouth_w=", MCC_RAIL_MOUTH_W, " root_w=", MCC_RAIL_ROOT_W, " flank_angle=", MCC_RAIL_FLANK_ANGLE,
    " clr_horiz=", MCC_RAIL_CLR_HORIZ, " roof_clr=", MCC_RAIL_ROOF_CLR,
    " lock_e=", LOCK_E, " lock_exit_x=", _lock_exit_x_here,
    " lock_ramps_in_out_deg=", [MCC_RAIL_LOCK_RAMP_IN, MCC_RAIL_LOCK_RAMP_OUT],
    " flank_play=", 2 * MCC_RAIL_CLR_HORIZ, " leadin=", MCC_RAIL_LEADIN,
    " print_bbox=", [base_w, base_d, max(MCC_RAIL_SILL_H, PLATE_T + MCC_RAIL_MALE_H)]
));

// The rail half's own plate (the bracket-plate stand-in). The rail needs no cut in it (D50). Two
// snap-off strips join it to the groove half, 1 mm in from the coupon's outer long edges and clear of
// the groove's open +X end. (Flush with those edges they left a zero-volume sliver on the bed plane:
// `check` saw 2 parts and no watertight mesh.)
module _rail_lock_base() {
    union() {
        translate([x_male0 - MARGIN, -base_d / 2, 0])
            cube([LEN + 2 * MARGIN, base_d, PLATE_T]);
        for (y0 = [-footprint_d / 2 + 1, footprint_d / 2 - 1 - STRIP_W])
            translate([LEN - MCC_EPS, y0, 0])
                cube([x_male0 - MARGIN - LEN + 2 * MCC_EPS, STRIP_W, PLATE_T]);
    }
}

// The male lands MCC_EPS INTO its plate (a genuine shared volume, not a coincident face -- trimesh's
// split(), the Tier-3 "one connected shell" check, would otherwise see two parts).
Z0 = PLATE_T - MCC_EPS;

// Female half: a plinth standing DIRECTLY on the bed with its groove mouth face down -- the case
// floor's own print pose, so the groove roof prints as the same ~66 mm bridge as on a real base (R40).
// mcc_rail_female_cut()'s local Z=0 (the case's exterior floor face) is the bed; the groove is closed
// at -X by a MCC_WALL stop wall and runs out open through the plinth's +X end, like the case (D34),
// with the case's 45-degree lead-in at that face (entry_x, D48).
module _rail_lock_female() {
    translate([x_female0, 0, 0])
        difference() {
            translate([-MCC_WALL, -footprint_d / 2, 0])
                cube([LEN + MCC_WALL, footprint_d, MCC_RAIL_SILL_H]);
            translate([LEN / 2, 0, 0])
                mcc_rail_female_cut(len = LEN, open_ext = 1, entry_x = LEN / 2, lock_e = LOCK_E);
        }
}

// Male half: mcc_rail_male()'s own local Z=0 (the plate top) lands MCC_EPS into its base
// plate's own top face (world Z=Z0) -- that plate stands in for the bracket's own plate,
// so no extra plate geometry is added here.
module _rail_lock_male() {
    translate([x_male0 + LEN / 2, 0, Z0])
        mcc_rail_male(len = LEN, lock_e = LOCK_E);
}

union() {
    _rail_lock_base();
    _rail_lock_female();
    _rail_lock_male();
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
```
Why the strips move 1 mm in: flush with the plinth's and plate's long faces, the union left a
zero-volume two-triangle sliver on the bed plane (`check`: parts = 2, not watertight). A's own D.3
coupon shows the same failure (parts = 8 in the prototype). **If A's merged coupon already fixed the
strips differently and its `check` passes, keep A's strip lines instead and change nothing else in
them.** The rest of the file is fixed as written.

**F6.2** `git rm tests/golden/coupons/rail-latch.json` (the golden of a file that no longer exists;
`build.py golden` has no orphan check). The new golden `tests/golden/coupons/rail-lock.json` is created
by §9. Build discovery is by file stem, so nothing in `scripts/` or CI needs the new name.

---

## 7. `tests/test_rail.scad`

**F7.1** Replace every line from the one starting `// --- Latch (issue #46, D34): snap-fit rules` through the
line starting `assert(MCC_RAIL_END_STOP_L == 0 && MCC_RAIL_END_STOP_H == 0` (inclusive) with:
```openscad
// --- Gravity lock (D48): lift budget, profile and walls, checked from the constants so a regression
// fails here before any render (T1-64 .. T1-66). ---------------------------------------------------
assert(MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_LOCK_PLAY_MARGIN <= 2 * MCC_RAIL_CLR_HORIZ + MCC_EPS,
    str("T1-64: lock bump ", MCC_RAIL_LOCK_ENGAGE, " + margin ", MCC_RAIL_LOCK_PLAY_MARGIN,
        " does not fit the flank play ", 2 * MCC_RAIL_CLR_HORIZ));
assert(75 <= MCC_RAIL_LOCK_RAMP_OUT && MCC_RAIL_LOCK_RAMP_OUT <= 90, "T1-65: lock exit face outside 75..90 deg");
assert(15 <= MCC_RAIL_LOCK_RAMP_IN && MCC_RAIL_LOCK_RAMP_IN <= 60, "T1-65: lock entry ramp outside 15..60 deg");
assert(MCC_WALL / 2 - MCC_EPS <= MCC_RAIL_SILL_SIDE_W - MCC_RAIL_CLR_HORIZ - MCC_RAIL_LOCK_ENGAGE,
    "T1-66: sill wall behind the lock pocket below MCC_WALL/2");
assert(MCC_RAIL_LEADIN <= MCC_WALL, "T1-66: rail lead-in deeper than MCC_WALL");
assert(MCC_RAIL_END_STOP_L == 0 && MCC_RAIL_END_STOP_H == 0, "D34: the male end-stop flange is retired");

// --- D50: the plate-side keep-out every bracket reads (never the MCC_RAIL_LOCK_* constants) --------
_rail_ko = mcc_rail_male_keepout();
assert(_rail_ko == [[-MCC_RAIL_LEN / 2, MCC_RAIL_LEN / 2],
                    [-MCC_RAIL_ROOT_W / 2 - MCC_RAIL_LOCK_ENGAGE, MCC_RAIL_ROOT_W / 2]],
    str("D50: mcc_rail_male_keepout()=", _rail_ko));
assert(mcc_rail_male_keepout(60)[0] == [-30, 30],
    str("D50: mcc_rail_male_keepout(60)=", mcc_rail_male_keepout(60)));
```
(The variable is `_rail_ko`, not `_ko`: `_ko` is assigned further down for the floor keep-out, and
OpenSCAD would let the later assignment win.)

**F7.2** Replace
`translate([0, -60, 0]) mcc_rail_male(plate_t = 6); // with the arm's leg through a 6 mm plate`
with
```openscad
// D50: a consumer unions the rail onto its plate -- the rail needs no cut in the plate.
translate([0, -60, 0])
    union() {
        translate([0, 0, -6]) cuboid([MCC_RAIL_LEN + 10, MCC_RAIL_ROOT_W + 10, 6], anchor = BOTTOM);
        mcc_rail_male();
    }
```

**F7.3** Replace `        mcc_rail_female_cut(open_ext = 20);` with
`        mcc_rail_female_cut(open_ext = 20, entry_x = MCC_RAIL_LEN / 2);`

**F7.4** Replace the three comment lines that start `// rail-latch.scad's own length) -- the latch must be re-derived from THIS len, not the fixed`
with
```
// rail-lock.scad's own length) -- the lock bump must be re-derived from THIS len
// (len/2 - MCC_RAIL_LOCK_END_OFFSET); this is exactly the regression the len=60 case here guards
// against. The e-ladder's largest bump (lock_e = 0.8, M15) must render too. ----------------------
```
(the line above them, ending `(models/coupons/`, stays).

**F7.5** Directly after the len = 60 female block (the lines `        mcc_rail_female_cut(len = 60);` and
`    }`), insert:
```openscad
translate([300, 0, 0]) mcc_rail_male(len = 60, lock_e = 0.8);
translate([300, 60, 0])
    difference() {
        cuboid([60, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
        mcc_rail_female_cut(len = 60, open_ext = 1, entry_x = 30, lock_e = 0.8);
    }
```

**F7.6** Header: replace `//     - T1-62 (D44): ` with
```
//     - T1-64 .. T1-66 (D48): the gravity lock's lift budget, profile and walls; D50: the
//       rail's plate-side keep-out, mcc_rail_male_keepout().
//     - T1-62 (D44): 
```
(the rest of that header line stays).

**F7.7** In the manual-checks block, after check 3, append:
```
// 4. T1-64 (D48), a lock bump too tall for the flank play (scratch edit constants.scad
//    MCC_RAIL_LOCK_ENGAGE = 1.0), then render a case base or the coupon; the render fails with:
//    "mcc: T1-64 rail lock bump 1 + margin 0.2 does not fit the flank play ..."
```

---

## 8. `scripts/rail_fit.py` — replace the whole file

It now proves the four things the lock depends on: zero overlap at full mate (hanging, centred and
pushed up), the end stop, a hanging case locked, and — over the whole insertion — a lift over the bump
that fits the dovetail's play with `MCC_RAIL_LOCK_PLAY_MARGIN` to spare. Prototype: 49 s per SKU.
```python
#!/usr/bin/env python3
"""Virtual insertion sweep: slide the male mount rail into a rendered case base and check that it
mates, stops, locks, and rides over its gravity-lock bump inside the dovetail's own play
(architecture.md §13 D34, D44, D48).

    python scripts/rail_fit.py [case-slug]          # default: pro-convert-for-ndi-to-hdmi

Renders mcc_rail_male() (no plate) with the pinned OpenSCAD and loads exports/(slug)/base.model.stl
(run `build.py render (slug) --part base` first). Frame: the case as rendered (floor at Z=0); the male
sits at (dx, MCC_RAIL_Y + dy, 0). dx is the insertion offset along X: 0 = fully mated, negative =
over-travel, positive = not yet fully in (also the direction a hanging case is pulled to remove it).
dy is the male's Y offset from the groove's centre line. A case hanging patch-wall down (D49) rests
on the male's -Y flank, i.e. at dy_lo, the most negative collision-free dy; the lock bump pushes the
case toward the far wall, i.e. the male toward larger dy.

Checked, exit code 0 when all hold:
  1. full mate (dx = 0): zero overlap at dy_lo, 0 and dy_hi -- the bump sits in its pocket with
     clearance, and the play band dy_hi - dy_lo is the dovetail's own (about 2 x 0.577 mm);
  2. over-travel (dx = -0.5): overlap -- the groove's closed -X end stops the rail;
  3. locked (dx = pocket clearance + 0.1, hanging at dy_lo): overlap, only within the bump's X span
     -- a hanging case cannot be pulled off without lifting it;
  4. insertion sweep, every dx: the least lift that clears everything, lift = dy_req - dy_lo, fits
     the play band with MCC_RAIL_LOCK_PLAY_MARGIN to spare, and at dy_lo nothing but the bump
     touches -- the case rides over the bump inside the flank play, nothing has to flex.
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
from pathlib import Path

import trimesh
from trimesh.creation import box

import build

EPS_V = 1e-3    # mm^3: overlap volumes up to this count as zero (mesh noise on touching faces)
DY_TOL = 0.005  # mm: bisection tolerance of the Y searches


def _const(name):
    text = (build.LIB_DIR / "mcc" / "constants.scad").read_text(encoding="utf-8")
    return float(re.search(rf"^{name}\s*=\s*([-\d.]+)", text, re.M).group(1))


def _overlap(male, base, dx, y):
    """(volume, male-frame X span or None) of the male at (dx, y, 0) intersected with the base."""
    m = male.copy()
    m.apply_translation([dx, y, 0.0])
    inter = trimesh.boolean.intersection([m, base], engine="manifold")
    v = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
    if v <= EPS_V:
        return 0.0, None
    return v, (float(inter.bounds[0][0]) - dx, float(inter.bounds[1][0]) - dx)


def _free(male, base, dx, y):
    return _overlap(male, base, dx, y)[0] == 0.0


def _extreme_free_y(male, base, dx, y0, direction, span=3.0):
    """From the collision-free y0, the farthest collision-free y in `direction` (+1 or -1)."""
    lo, hi = 0.0, span
    if _free(male, base, dx, y0 + direction * hi):
        return y0 + direction * hi
    while DY_TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if _free(male, base, dx, y0 + direction * mid):
            lo = mid
        else:
            hi = mid
    return y0 + direction * lo


def _least_free_y(male, base, dx, y_lo, y_hi):
    """The smallest collision-free y in [y_lo, y_hi] at dx, or None if even y_hi collides."""
    if _free(male, base, dx, y_lo):
        return y_lo
    if not _free(male, base, dx, y_hi):
        return None
    lo, hi = y_lo, y_hi
    while DY_TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if _free(male, base, dx, mid):
            hi = mid
        else:
            lo = mid
    return hi


def main(argv):
    slug = argv[0] if argv else "pro-convert-for-ndi-to-hdmi"
    base_path = build.EXPORTS_DIR / slug / "base.model.stl"
    if not base_path.is_file():
        print(f"error: {base_path} missing - run `build.py render {slug} --part base` first")
        return 1
    with tempfile.TemporaryDirectory(prefix="mcc_railfit_") as t:
        scad = Path(t) / "male.scad"
        scad.write_text("include <mcc/mcc.scad>\nmcc_rail_male();\n", encoding="utf-8")
        stl = Path(t) / "male.stl"
        ok, _ = build.run_openscad(build.find_openscad(), scad, {}, [stl], None)
        if not ok:
            return 1
        male = trimesh.load(str(stl), force="mesh")

    rail_y = _const("MCC_RAIL_Y")
    margin = _const("MCC_RAIL_LOCK_PLAY_MARGIN")
    e = _const("MCC_RAIL_LOCK_ENGAGE")
    pocket_clr = _const("MCC_RAIL_MATE_CLR") / math.sin(math.radians(_const("MCC_RAIL_FLANK_ANGLE")))
    half = _const("MCC_RAIL_LEN") / 2
    x1 = half - _const("MCC_RAIL_LOCK_END_OFFSET")  # bump exit face, male frame (rail.scad geometry)
    x0 = x1 - _const("MCC_RAIL_LOCK_FLAT") - e / math.tan(math.radians(_const("MCC_RAIL_LOCK_RAMP_IN")))

    # Everything the male can touch lies within this band (the male is 3.5 mm tall and about 66 mm
    # wide); cropping the base to it once keeps every boolean below fast, and loses no contact.
    whole = trimesh.load(str(base_path), force="mesh")
    base = trimesh.boolean.intersection(
        [whole, box(bounds=[[-400, rail_y - 45, -10], [400, rail_y + 45, 12]])], engine="manifold")
    case_len = float(whole.bounds[1][0] - whole.bounds[0][0])
    bad = []

    # 1. Full mate.
    if not _free(male, base, 0.0, rail_y):
        print("FAIL: fully mated and centred, but overlapping")
        print("rail fit FAILED")
        return 1
    dy_lo = _extreme_free_y(male, base, 0.0, rail_y, -1) - rail_y
    dy_hi = _extreme_free_y(male, base, 0.0, rail_y, +1) - rail_y
    play = dy_hi - dy_lo
    print(f"full mate: play band dy {dy_lo:+.3f} .. {dy_hi:+.3f} (play {play:.3f} mm)")
    for dy in (dy_lo, 0.0, dy_hi):
        if not _free(male, base, 0.0, rail_y + dy):
            bad.append(f"fully mated but overlapping at dy={dy:+.3f}")

    # 2. Over-travel.
    if _free(male, base, -0.5, rail_y):
        bad.append("no end stop: over-travel at dx=-0.5 does not collide")

    # 3. Locked while hanging.
    dx_lock = pocket_clr + 0.1
    v, span = _overlap(male, base, dx_lock, rail_y + dy_lo)
    print(f"locked:    dx={dx_lock:.3f} hanging  overlap={v:.3f} mm3" + (f"  male x {span[0]:.2f}..{span[1]:.2f}" if span else ""))
    if span is None:
        bad.append(f"not locked: a hanging case slides {dx_lock:.3f} mm toward removal without collision")
    elif span[0] + 0.5 < x0 or x1 + 0.5 < span[1]:
        bad.append(f"lock collision outside the bump {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")

    # 4. Insertion sweep.
    dxs = [0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0]
    dxs += [12.5 + 2.5 * i for i in range(int((case_len / 2 - x0 + 5.0 - 12.5) / 2.5) + 1)]
    dxs += [60.0, 90.0, 120.0, case_len / 2 + half - 1.0]
    worst = 0.0
    for dx in dxs:
        y_req = _least_free_y(male, base, dx, rail_y + dy_lo, rail_y + dy_hi)
        v, span = _overlap(male, base, dx, rail_y + dy_lo)
        if y_req is None:
            bad.append(f"dx={dx:.2f}: no collision-free position inside the play band")
            print(f"dx={dx:7.2f}  BLOCKED")
            continue
        lift = y_req - (rail_y + dy_lo)
        worst = max(worst, lift)
        print(f"dx={dx:7.2f}  lift={lift:.3f} mm" + (f"  hanging overlap male x {span[0]:.2f}..{span[1]:.2f}" if span else ""))
        if play + DY_TOL < lift + margin:
            bad.append(f"dx={dx:.2f}: lift {lift:.3f} + margin {margin} exceeds the play {play:.3f}")
        if span and (span[0] + 0.5 < x0 or x1 + 0.5 < span[1]):
            bad.append(f"dx={dx:.2f}: collision outside the bump {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")
    print(f"max lift over the bump {worst:.3f} mm of {play:.3f} mm play (margin {margin} mm, bump {e} mm)")

    for b in bad:
        print("FAIL:", b)
    print("rail fit OK" if not bad else "rail fit FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```
Expected output (prototype, all three SKUs): `full mate: play band dy -0.577 .. +0.577 (play 1.154 mm)`;
`locked: dx=0.677 hanging overlap=0.245 mm3 male x 71.90..72.00`; lift 0.000 up to dx 0.5, ≈ 0.70 while
the bump rides the flank, lower in the last millimetre (the lead-in), 0.000 once the bump has left
the case; `max lift over the bump 0.703 mm of 1.154 mm play`; `rail fit OK`.

---

## 9. Goldens

After §2–§8 on top of A's goldens, run `python scripts/build.py golden` (no `--update`). **Only these
may fail**: the 8 `tests/golden/(slug).base.json`, `tests/golden/pro-convert-for-ndi-to-hdmi.base_fan.json`,
`tests/golden/brackets/arch-tv-bracket.centre.json`, and `coupons/rail-lock` (missing golden). Anything
else — any `*.lid.json`, `brackets/arch-tv-bracket.arm.json` (the prototype shows it identical), another
coupon — **stop**.

Then, having done F6.2's `git rm`, run this one targeted command:
```
python scripts/build.py golden coupons/rail-lock brackets/arch-tv-bracket pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio --update
```
then `golden` again (all PASS), then `git diff --stat -- tests/golden/`: content changes only in the 8
`*.base.json`, the one `base_fan` json and `arch-tv-bracket.centre.json`; one deletion
(`coupons/rail-latch.json`); one addition (`coupons/rail-lock.json`). Anything else: stop. Never an
untargeted `golden --update`, never hand-edited JSON.

---

## 10. Docs (developer, same PR)

Paste rule: copy only the text inside the fences. Anchors are A's post-merge text.

**F10.1 `CLAUDE.md`, "Fixed decisions", Closure bullet.** Replace this fragment (it spans a line
break; the text after `**No floor insert` on the second line stays as it is):
```
  every non-bearing face of the joint keeps ≥ 0.5 mm clearance (flanks and roof); the D34 latch is
  the lock. **No floor insert
```
with
```
  every non-bearing face of the joint keeps ≥ 0.5 mm clearance (flanks and roof). **The lock is a
  gravity lock** (user decision 2026-09-28, D48): a rigid 0.7 mm bump on the rail's upper flank drops
  into a pocket in the groove flank and is held there by the case's own weight; nothing flexes, there
  is no latch and no actuator — remove a case by lifting it about 1 mm and sliding it back off. The
  groove's entrance through the +X wall has a 1 × 45° lead-in. **No floor insert
```

**F10.2 `CLAUDE.md`, "Fixed decisions", Mount brackets bullet** (added by A's AM-5). After its last
sentence `The VESA 100/200 `tv-bracket` is **retired** (D47) — do not reintroduce it.` append (same
bullet, new sentence on the next line, two-space indent):
```
  **A mounted case always hangs patch-wall down** (user decision 2026-09-28, D49) — on every bracket,
  the truss mount (#27) included, and never on a TV turned to portrait: the gravity lock only engages
  when the case's weight rests on the rail's upper flank.
```

**F10.3 `CLAUDE.md`, "Current status".** Replace `latch redesign (D34)` with
`gravity lock that replaced the D34 latch (D48)` (the text before it, `the rail`, ends the previous line
and stays).

**F10.4 `BOM.md`.**
1. In the row that begins `| — | — | — | Tool-less dovetail mount rail (D-15, rev 9, issue #25`, replace
   `the female groove (case floor) and the male rail + snap latch are printed features` with
   `the female groove (case floor, with the lock pocket) and the male rail (with the rigid gravity-lock bump, D48) are printed features`.
2. In the "Mounting brackets" paragraph A wrote (AM-3 item 9), replace this two-line fragment
```
needs no hardware: the rail/latch
interface is tool-less (see `models/coupons/rail-latch.scad` for the retention target it depends on).
```
   with
```
needs no hardware: the rail/lock
interface is tool-less — a rigid gravity lock, released by lifting the case about 1 mm (D48; its
tests: `models/coupons/rail-lock.scad`, M15).
```
3. In the arch paragraph replace `(rail-latch), M18` with `(rail-lock), M18`.

**F10.5 `models/coupons/README.md`.**
1. Replace the whole coupon-table row whose first cell is `rail-latch.scad` (in code font) with:
```
| `rail-lock.scad` | The tool-less dovetail mount rail (D-15; wide, flush, ≥ 0.5 mm clearance since D44) and its **gravity lock** (D48): the dovetail slides freely with the expected play, the groove roof (a ~66 mm bridge printed exactly like the case floor) does not sag into the 0.5 mm roof gap, the case-side lead-in guides the rail in, and — with the rail plate vertical and the groove half loaded and hanging — the lock clicks, cannot be pulled off along the rail, and releases when the groove half is lifted about 1 mm | `lib/mcc/constants.scad` : `MCC_RAIL_ROOF_CLR` (raise it if the roof sags — never narrow the rail), `MCC_RAIL_LOCK_ENGAGE` (the e-ladder); confirms (does not calibrate) `MCC_RAIL_MATE_CLR`, a user decision |
```
2. Replace the whole "Orientation (Bambu Studio)" row whose first cell is `rail-latch` (in code font) with:
```
| `rail-lock` | **Print as modelled, no rotation:** the groove half stands directly on the bed, groove mouth down (like the case floor); the rail half stands on its own plate, rail up (like a bracket). Two thin snap-off strips join them — break them off before testing. | Both halves in their production print pose: the groove roof prints as the same ~66 mm bridge as on a real base (architecture.md R40), the lock pocket and lead-in print like the case's, and the rail's lock bump stands on its plate like on a bracket. |
```
3. Rename the heading `### rail-latch` to `### rail-lock` and replace its whole body (up to, not
   including, `## print-log.md`) with:
```
- Hardware needed: a luggage/fish scale, a dummy mass of the heaviest case (weigh one assembled case
  with its device; ≈ 0.8 kg `assumed` until weighed) that can be strapped to the groove half, a
  temporary loop (string/cable tie), a board to screw or clamp the rail half to vertically, calipers.
- Snap the two joining strips off first.
- **Roof sag (R40):** before inserting anything, measure the groove roof's height above the groove
  half's bottom face at mid-width, at both ends and in the middle (nominal 4.0 mm). The rail's own top
  is 3.5 mm tall: the roof must stay clear of it.
- **Play (R41, R45):** lying flat, slide the rail half in from the open (+X) end until it stops;
  with the lock *not yet* engaged (rail only partly in), measure the lateral play (expect ≈ 1.15 mm
  total; the lock needs at least `MCC_RAIL_LOCK_ENGAGE` + 0.2 = 0.9 mm of it).
- **Lock, hanging:** clamp the rail half's plate vertical, slide axis horizontal, the rail's lock bump
  on its upper flank (the bump side up). Strap the dummy mass to the groove half. Hang the groove half
  on the rail's free end and push it along: it must ride over the bump without binding and click in.
  Then (a) pull the groove half along the rail, away from the stop, via the loop at the rail line:
  it must not release up to ≥ 50 N (record where and how it fails if it does); (b) tug the groove
  half's lower edge outward, away from the plate: no release; (c) lift the groove half until it stops
  (≤ 1.2 mm) and slide it off: it must release one-handed.
- **e-ladder:** print extra copies with `python scripts/build.py render coupons/rail-lock -D LOCK_E=0.5`
  (then 0.6, then 0.8), copying `exports/coupons/rail-lock/rail-lock.3mf` aside after each run; re-run
  `render coupons/rail-lock` without `-D` afterwards to restore the release export. Repeat "Play" and
  "Lock, hanging" on each and pick the largest bump that never binds.
- **Cycling:** 100 insert/remove cycles on the production copy, then repeat "Play" and "Lock,
  hanging"; inspect the bump and the pocket's +X wall for crushing or wear.
- **Good** = no roof contact, smooth slide-in with a clean click, locked against the pulls in (a) and
  (b), one-handed lift-and-slide release, play within the expected figure, no wear after 100 cycles.
- Record: roof heights, play, click quality, the pull forces reached in (a), the e-ladder results,
  wear after cycling.
- Update: `lib/mcc/constants.scad` → `MCC_RAIL_ROOF_CLR` if the roof sags into the gap (raise it;
  never narrow the rail — user decision D44), `MCC_RAIL_LOCK_ENGAGE` from the e-ladder. If the play is
  objectionable, report it — `MCC_RAIL_MATE_CLR` is a user decision, not a coupon result.
```

**F10.6 `models/brackets/README.md`.**
1. Replace `rail up (same convention as the `rail-latch`` (end of a line) with
   `rail up (same convention as the `rail-lock`` (the next line, `  coupon), no supports.`, stays).
2. Replace `MEASURE, see `BOM.md`) → click the case on.` with
   `MEASURE, see `BOM.md`) → hang the case on and slide it until the lock clicks (see "Installing and removing a case").`
3. Replace `before M15 (rail-latch pull test), M18` with `before M15 (rail-lock coupon tests), M18`.
4. Directly after the "## Orientation (issue #26's acceptance criterion, kept for every bracket)"
   section (A's text, ending `carries the one-line go/no-go version.`), insert, with a blank line before:
```
**A mounted case always hangs patch-wall down** (user decision 2026-09-28, architecture.md D49) — on
every bracket, the planned truss bracket (#27) included, and never on a TV turned to portrait. The
rail's gravity lock (D48) only engages in that pose: the case's weight must rest on the rail's upper
flank, where the lock bump is.

## Installing and removing a case

- **Install:** hold the case patch-wall down, with its +X end wall (the fan end, where the floor
  groove opens) toward the rail's free end; set the groove onto the rail's end — the 45° lead-in at
  the groove entrance guides it — and slide the case along until it stops and the lock clicks (the
  case rises about 0.7 mm over the lock bump on the way and drops into place).
- **Remove:** lift the case until it stops (about 1 mm — the dovetail itself limits it), then slide it
  back off the way it went on. A plain pull along the rail does not release a hanging case.
```
5. Replace the whole "Orientation (Bambu Studio)" row whose first cell is `arch-tv-bracket` `centre` with:
```
| `arch-tv-bracket` `centre` | **Flat (TV-side, standoff) face down on the bed, rail up** — the same rail orientation as the `rail-lock` coupon. | The dovetail taper and the lock bump that follows its upper flank are the only overhangs (D44, D48), both self-supporting at 30° from vertical; the rail needs no plate window (D50); the tabs print flat with the body. |
```

**F10.7 `scripts/README.md`.** In the command-table row for `rail_fit.py`, keep the first cell and
replace the second cell with:
```
(separate script, run from `scripts/`) Virtual insertion sweep of the male mount rail into a rendered `base.model.stl`: asserts zero overlap at full mate (hanging, centred and pushed up), that the end stop blocks over-travel, that a hanging case is locked (the gravity-lock bump catches its pocket), and that over the whole insertion the case lifts over the bump inside the dovetail's own play with `MCC_RAIL_LOCK_PLAY_MARGIN` to spare — nothing flexes (architecture.md D34, D44, D48). Run after any change to `rail.scad`, `mounts.scad` or a case's floor.
```

**F10.8 `.claude/skills/print-check/SKILL.md` §3,** arch row: replace `M15 (rail-latch)` with
`M15 (rail-lock)`, and replace `patch wall then hangs down.` with
`patch wall then hangs down — always (D49). Install: slide the case on until the lock clicks; remove: lift it about 1 mm, then slide it back off.`

**F10.9 `CHANGELOG.md`.** Insert directly after A's AM-6 block (its last line is
`  `MCC_BRACKET_PLATE_T` goes with it.`), with a blank line before:
```
### Changed (2026-09-28, gravity lock)

- **The rail lock is a gravity lock** (architecture.md D48, user decision 2026-09-28): a rigid 0.7 mm
  bump on the rail's upper flank drops into a pocket in the case groove's flank and is held there by
  the case's own weight. It replaces the D34 snap latch (arm, plate window, nub and notch are gone):
  nothing flexes; remove a case by lifting it about 1 mm and sliding it back off. Brackets and cases
  printed before this change do not mate with ones printed after it.
- **The groove entrance has a 1 × 45° lead-in** where it leaves the case's +X wall (D48).
- **A mounted case always hangs patch-wall down** (D49) — the lock depends on it.
- Brackets read the rail's plate-side keep-out from `mcc_rail_male_keepout()` and union the rail on
  with no plate cut (D50). The arch bracket's rail no longer cuts its centre plate.
- Coupon `rail-latch` is now `rail-lock` (tests the lock hanging, plus an e-ladder).
```

**F10.10 Permanent record.** Create `docs/plans/2026-09-28-gravity-lock.md` = this plan verbatim;
directly under its title add the line
`**Implemented as amended by the architect verdict appended at the end of this file. Where they conflict, the verdict wins.**`
and append the verdict's full text under `## Architect verdict`.

**Not to edit:** `knowledge/**`; `docs/plans/**` other than F10.10; old CHANGELOG entries;
`.claude/skills/openscad-authoring/SKILL.md` (its "D34: the rail latch leg" is a lesson, not a
reference to live code); the two `rail-latch` comments in `scripts/csg_to_step.py` (they record where
an OCCT issue was found); `.claude/knowledge/session-resume.md` (the teamlead's; suggested edit: its
stale "rail latch off pending #46 (D28)" and "Rail latch redesign — issue #46" lines).

---

## 11. Printability and slicer gate

- **Bump (bracket, printed plate-down).** It stands on the plate at Z = 0 (fused, rigid — no window),
  and each layer steps out with the flank, i.e. the same 30°-from-vertical overhang as the flank
  itself; its exit and entry faces are vertical walls. No floating region, no cantilever.
- **Pocket (case base, printed floor-down).** A 0.70 mm-deeper notch in the groove's −Y flank, full
  groove depth, 3.35 mm long: its ceiling is the groove roof bridge, locally anchored 0.70 mm further
  out; the sill wall behind it stays 1.72 mm (T1-66). The D34 notch it replaces was 1.3 mm deeper;
  the prototype bases with the pocket slice with zero warnings.
- **Lead-in (case base, +X wall).** A 1 mm plan-view flare of the flanks and mouth inside the 3 mm
  wall; the roof is not raised, so the passage roof (`MCC_RAIL_PASSAGE_ROOF_MIN`) and the Plus family's
  fan aperture above it are untouched. Flared flank faces overhang less than the flank itself.
- **Exact STEP** (C's gate): the new constructs are `offset`, the flank shear (both already used by
  D34) and one 3-D `hull` of two prismoid slices — all supported by `scripts/csg_to_step.py`.
- **Prototype:** `slicer-check` zero warnings on `coupons/rail-lock`, `brackets/arch-tv-bracket`
  (arm, centre) and the bases of `pro-convert-for-ndi-to-hdmi`, `pro-convert-sdi-tx`,
  `pro-convert-hdmi-plus`; exact STEP OK on the coupon, the NDI-to-HDMI base and the arch centre.

---

## 12. Ordered steps and verification

1. §1 checks (anchors, region contents, grep). Stop on any miss.
2. §2 `constants.scad`.
3. §3 `rail.scad`.
4. §4 `mounts.scad`.
5. §5 `arch-tv-bracket.scad`.
6. §6 coupon (`git mv`, content, `git rm` of the old golden).
7. §7 `tests/test_rail.scad`.
8. §8 `scripts/rail_fit.py`.
8a. `grep -rn --include=*.scad --include=*.py "mcc_rail_male_window\|MCC_RAIL_LATCH\|MCC_SNAP_STRAIN_MAX\|\bplate_t\b\|_mcc_rail_nub_2d\|_mcc_rail_latch" lib models tests scripts`
    must print nothing (verified on the prototype). The word `latch` may still appear in comments
    that describe D34 as history — the constants block, the rail.scad lock header, the arch's
    `CENTRE_W` comment; those are intended. The docs (§10) are updated later, in step 16.
9. `python scripts/build.py doctor`, then `python scripts/build.py smoke` — all PASS (`test_rail`,
   `test_arch_tv_bracket` at 69.7 / 150 / 184.9, every other test).
10. `python scripts/build.py render --all`, then `python scripts/build.py check --all` — all PASS.
11. From `scripts/`: `python rail_fit.py pro-convert-for-ndi-to-hdmi`, `python rail_fit.py pro-convert-sdi-tx`,
    `python rail_fit.py pro-convert-hdmi-plus` — each ends `rail fit OK`; the max lift is
    0.70 ± 0.02 mm and the play 1.154 ± 0.02 mm. Paste the three summaries into the PR.
12. §9 goldens.
13. `python scripts/build.py slicer-check` — zero warnings on every part.
14. `python scripts/build.py review`.
15. `python scripts/build.py ci --group k/6 --jobs 3` for k = 1…6 (or the PR's CI run) — includes the
    exact-STEP gate on every base.
16. §10 docs.
17. Architecture records: paste the architect verdict's rev-17 text (Appendix X below is the proposal
    it starts from) into `.claude/knowledge/architecture.md` and `.claude/knowledge/layout-patch-wall.md`.
18. F10.10 permanent record.
19. `python scripts/build.py all`, then the PR into `main`, CI green. The PR body cites D48–D50,
    T1-64…66, R44/R45, M15 and M21, and pastes the three `rail_fit.py` summaries.

**Stop and report, without improvising, if:** an anchor is missing (§1); any smoke/render/check fails;
`rail_fit.py` fails on any SKU, or its max lift is not 0.70 ± 0.02; a golden moves outside §9's list;
the slicer gate warns on any part; a base's STEP falls back to the faceted converter; T1-53/T1-54/T1-60
fail in the arch sweep.

**DO NOT:**
- change `MCC_RAIL_ROOT_W`, `MCC_RAIL_Y`, `MCC_RAIL_DEPTH`, `MCC_RAIL_FLANK_ANGLE`, `MCC_RAIL_LEN`,
  `MCC_RAIL_MATE_CLR`, `MCC_RAIL_CLR_HORIZ`, `MCC_RAIL_ROOF_CLR` or `MCC_RAIL_MALE_H` (user decisions / A);
- change any new `MCC_RAIL_LOCK_*` or `MCC_RAIL_LEADIN` value to make a gate pass — stop and report;
- change `CENTRE_W`, `ARCH_PLATE_T`, `RAIL_X` or any other arch geometry beyond §5;
- remove `MCC_RAIL_END_STOP_L/H` or `MCC_RAIL_PASSAGE_ROOF_MIN` (out of scope);
- put a lock bump on the +Y flank, add a flexing element, a thumb release, or any plate cut to the rail;
- add a keep-out row for the pocket in `layout.scad`;
- run an untargeted `golden --update` or hand-edit golden JSON;
- touch any vertical-bracket (plan D) file — D lands after F and consumes only `mcc_rail_male()` and
  `mcc_rail_male_keepout()`.

---

## 13. Open points

1. **The coupon's snap-off strips** (§6): A's own D.3 coupon fails `check` (parts = 8) in the
   prototype. If A lands a different fix, F keeps it; this is flagged to the teamlead for A now.
2. **Dummy mass for M15**: weigh one assembled case per family; ≈ 0.8 kg is `assumed`. The lock's
   self-locking does not depend on it; the ride-over feel and the release effort do.

---

## Appendix X — proposed rev-17 records (the architect's verdict owns the final text)

**X1 Revision header** (insert before `**Revision 16, 2026-09-28`):
```
**Revision 17, 2026-09-28 (gravity rail lock — D48–D50; plan `docs/plans/2026-09-28-gravity-lock.md`).**
User decisions after the analysis of the external specialist's DP48 plate: the rail lock is a
**gravity lock only** — a rigid 0.7 mm bump on the rail's upper (−Y) flank drops into a pocket in the
groove flank and is held by the case's own weight; the **D34 snap latch is removed** (arm, window, nub,
notch, `MCC_RAIL_LATCH_*`, `MCC_SNAP_STRAIN_MAX`). **A mounted case always hangs patch-wall down** (D49).
The groove entrance gets the DP48's 1 × 45° lead-in. Brackets consume the rail only through
`mcc_rail_male()` (no plate cut) and `mcc_rail_male_keepout()` (D50). New: **T1-64 … T1-66**, **R44**,
**R45**, **M21**; M15 rewritten; Q21 closed; R41 updated. No case envelope figure moves.
```

**X2 §3, the `rail.scad` bullet.** Add `mcc_rail_male_keepout()` (pure, rev 17) to the listed API, and
add a fourth rule:
```
  - **Brackets consume the rail through two public symbols only** (rev 17, D50): `mcc_rail_male(len)`,
    unioned onto the bracket's plate — the rail needs no cut in any plate — and
    `mcc_rail_male_keepout(len)`, the rail-local plate-side keep-out (bump included) that the bracket
    maps through its own placement and pads with its own clearance. A bracket never reads
    `MCC_RAIL_LOCK_*` or other rail internals and never rebuilds the rail's footprint.
```
In the L1 table, `rail.scad`'s description loses "spring-lip latch" in favour of "gravity-lock bump
and pocket".

**X3 §6 floor rule** (A's D44 paragraph): replace `The D34 latch is the lock; its plate window also
clears the nub.` with `The lock is the gravity lock (D48): a rigid bump on the rail's upper flank in a
pocket of the groove flank, held by the case's weight — no plate cut, no flexure.`; replace
`and the latch notch runs the full depth over the nub` with `and the lock pocket runs the full depth
over the bump`.

**X4 §9** — T1-64 (lift budget: `lock_e + MCC_RAIL_LOCK_PLAY_MARGIN ≤ 2·MCC_RAIL_CLR_HORIZ`), T1-65
(exit face 75–90°, entry 15–60°, bump inside the working length), T1-66 (sill wall behind the pocket
≥ `MCC_WALL/2`; lead-in ≤ `MCC_WALL`) — evaluated in `mcc_rail_male()` / `mcc_rail_female_cut()` and in
`tests/test_rail.scad`. The next free id is T1-67. `layout-patch-wall.md` §9 gets the same three rows,
and its T1-62 row's `only the nub overlaps while sliding` becomes `only the lock bump overlaps while
sliding, and the lift it needs stays inside the flank play (T1-64)`.

**X5 §11.** R41: replace `and the D34 latch holds X only` with `and the gravity lock (D48) holds X while
the case hangs`, and correct `The lower flank bears` to `The upper flank (rail-local −Y) bears` — the
case's upper groove wall hooks over the rail's upper flank like a French cleat; a lower flank could
only push the case down (F2 statics, and the lock is placed on that upper flank). New:
```
**R44 — the rail lock is gravity-engaged. NEW 2026-09-28 (rev 17, D48/D49).** While the case hangs
patch-wall down its weight holds the bump in its pocket (≈ 0.6–1.15 × the weight, normal to the flank,
depending on whether the case yaws about its −X end), and the square exit face stops any axial pull at
or below the rail line — including every cable load at the patch wall. It does not hold when that
flank is unloaded: while the case is being hung, when the TV is laid flat or carried, or when the case
is pushed upward; then only friction resists sliding. A −X pull on the case's top (far-wall) edge can
yaw its +X end up and release it at ≈ 3 × the weight — also the natural hand release. Mitigation:
D49, the install/removal text (brackets README), M21. Accepted by the user.

**R45 — the ride-over needs the printed flank play. NEW 2026-09-28 (rev 17, D48).** The case rides over
the 0.70 mm bump inside the dovetail's own 1.155 mm horizontal play (0.45 mm margin; T1-64 asserts
≥ 0.2). A print that comes out more than ≈ 0.1 mm oversize on each of the four flank faces binds —
nothing is designed to flex. M15 measures the printed play and runs the e-ladder; if it binds, lower
`MCC_RAIL_LOCK_ENGAGE` (0.5 is still self-locking). Never widen the rail or change `MCC_RAIL_MATE_CLR`
(user decisions).
```

**X6 §12.** Q21 closed:
```
21. **The rail lock — DP48. Answered 2026-09-28 (rev 17).** The DP48 plate was analysed (scratch F2): a
    15° dovetail whose two 0.8 mm strips ride inside the dovetail's own play into recesses — a rigid,
    gravity-seated detent. User decision: **gravity lock only**, the D34 latch removed (D48); a mounted
    case always hangs patch-wall down (D49). The "tool-less, no thumbscrews" question is moot — the lock
    has no actuator. *(Also answered: the groove's closed −X end stays the axial end stop.)*
```
M15 rewritten:
```
| **M15** | **Print `models/coupons/rail-lock` and test it:** (a) roof sag on the groove half — roof height at mid-width vs 4.0 mm; the rail's 3.5 mm top must not touch it (R40); (b) play with the lock not engaged — expect ≈ 1.15 mm lateral (R41, R45); (c) **the lock, hanging**: rail plate vertical, groove half loaded to the heaviest case (≈ 0.8 kg, `assumed` — weigh one) — it rides over the bump without binding and clicks; an axial pull at the rail line does not release it up to ≥ 50 N; an outward tug at the lower edge does not release it; lifting ≤ 1.2 mm and sliding releases it one-handed; (d) e-ladder `LOCK_E` 0.5 / 0.6 / 0.8; (e) 100 cycles, then (b)–(c) again and inspect the bump and the pocket's +X wall | R40, R41, R44, R45 — every `MCC_RAIL_*` figure is `assumed` except the user-decided width and clearance. (a) decides `MCC_RAIL_ROOF_CLR`; (c)/(d) decide `MCC_RAIL_LOCK_ENGAGE`. **"Coupons before cases" applies to brackets too — no full-size bracket prints before this** | User, with a luggage scale, a dummy mass and calipers |
```
New M21 (after M20):
```
| **M21** | **First bracket print (arch, direct mode), with a real case and device:** the lock's yaw release force for a −X pull on the case's top (far-wall) edge (≈ 3 × the weight expected), no release for pulls on the patch-wall edge and on the cables, and the one-hand lift-and-slide removal behind a mounted TV | R44 — the 60 mm coupon cannot reproduce the full case's yaw lever | User |
```

**X7 §13** rows, after D47:
```
| **D48** | 2026-09-28 | D34 (in-plane snap latch: arm, slot, plate window, nub, notch) and D44 ("the D34 latch stays the lock"); Q21 | **User decision 2026-09-28**, after analysing the specialist's DP48 plate (scratch F2): **gravity lock only**, the D34 latch removed; adopt the DP48's 1 × 45° entry lead-in | D34 released by pulling (≥ 30 N target, never measured; a beam estimate gave ≈ 10–19 N) and needed a window through every consumer plate | **Done in rev 17 (plan F, `docs/plans/2026-09-28-gravity-lock.md`).** A rigid bump on the rail's −Y flank (`MCC_RAIL_LOCK_ENGAGE` 0.70 horizontal, 30° entry, 90° exit, exit face `len/2 − 3.0`) drops into a pocket in the groove's −Y flank (the bump grown by `MCC_RAIL_CLR_HORIZ`, full groove depth); nothing flexes — the case rides over it inside the dovetail's own 1.155 mm play (T1-64); square exit face (T1-65); sill wall behind the pocket ≥ 1.5 mm (T1-66); release = lift ≈ 1 mm + slide. Lead-in `MCC_RAIL_LEADIN` = 1.0 at the case's +X face (`mcc_rail_female_cut(entry_x)`). Removed: `_mcc_rail_latch_geom()`, `_mcc_rail_nub_2d()`, `_mcc_rail_latch_cut_2d()`, `mcc_rail_male_window()`, `mcc_rail_male(plate_t)`, every `MCC_RAIL_LATCH_*`, `MCC_SNAP_STRAIN_MAX`. `rail_fit.py` proves the lift, the lock and the full-mate clearance; coupon `rail-latch` → `rail-lock` (snap-off strips 1 mm in from the edges). M15 rewritten, M21, R44, R45; Q21 closed |
| **D49** | 2026-09-28 | Issue #26's orientation *convention* ("mount with +Y up so the patch wall hangs down"); the arch README: nothing keys the assembly against a 180° install | **User decision 2026-09-28: a mounted case ALWAYS hangs patch-wall down** — every bracket, the truss use (#27) included, no portrait TV | The gravity lock (D48) only engages when the case's weight rests on the rail's −Y flank | **Fixed decision, rev 17** (CLAUDE.md, brackets README). Every bracket keeps the `rotate([0,0,180])` rail placement. Still no physical key against a 180° install — the arch's UP arrow and shape remain cues (R44) |
| **D50** | 2026-09-28 | §3 rail rules: brackets called `mcc_rail_male(plate_t)` + `mcc_rail_male_window()` and built keep-outs from `MCC_RAIL_LATCH_*` | Plan-D gate (F-R1/F-R2): a bracket must not know rail internals | Every rail change would ripple into every bracket file | **Done in rev 17 (plan F).** `mcc_rail_male_keepout(len)` (pure, `rail.scad`) returns the rail-local plate-side keep-out `[[x_min, x_max], [y_min, y_max]]`, bump included; a bracket unions `mcc_rail_male(len)` onto its plate (no cut) and reads only that accessor. The arch migrated (`RAIL_KEEPOUT_X/Y`); plan D (rev 18) uses only these two |
```

## Architect verdict

# Architect verdict — Plan F (rev 1): gravity rail lock

Gate: `solution-architect`, 2026-09-28. Plan: `scratchpad/plans/F-gravity-lock.md`; source analysis `F2-dp48-lock-analysis.md`.

Checked against:
- A's branch as it stands (`feature/wide-dovetail`, worktree `agent-ad9b0d387faf107ca`), and A's verdict with Amendments 1–2, including the AM2-1 withdrawal note;
- the plan-D rev-2 verdict (F-R1…F-R3);
- the user decisions of 2026-09-28: gravity lock only, the D34 latch removed, a mounted case always hangs patch-wall down, the DP48 1 × 45° lead-in.

**Revision and ids:** rev 17.
- Used: T1-64…T1-66, D48–D50, R44, R45, M21, **Q23** (new here, FB5).
- T1-67…T1-69 and R46 were reserved for F and stay **unused**. Do not reassign them, so plan D's pre-assigned ids (T1-70…T1-90, D51, R47, M22) stay valid.

## Verdict: **APPROVED WITH BINDING CHANGES** (FB1–FB12)

This is a good plan. The design follows the user's decisions exactly:
- rigid bump on the rail's upper (rail-local −Y) flank;
- square exit face, so it is self-locking while the case hangs;
- nothing flexes;
- the bump rides over inside the dovetail's own 1.155 mm play, 0.9 ≤ 1.155 (T1-64);
- sill wall behind the pocket 1.72 ≥ 1.5 (T1-66);
- the DP48 lead-in without raising the roof.

It implements F-R1 and F-R2 cleanly:
- `mcc_rail_male_keepout()` is conservative: rail-local y ∈ [−33.2, 32.5] covers the bump's worst point at −32.91.
- `mcc_rail_male(len, lock_e)` needs no plate cut.
- The arch is migrated, with `RAIL_KEEPOUT_Y` [−32.5, 33.2] and T1-60 keeping 2.4 mm on both sides.

The anchors, stop conditions, grep checks, the new `rail_fit.py` (mate, stop, lock and lift budget) and the prototype evidence are the right level of rigour. I re-derived the figures and they check out:
- bump x 69.79…72.00 at len 150 and 24.79…27.00 at len 60;
- r_in 1.212;
- keep-out bounds;
- `arrow_y` 39.6;
- the directions of lock and release in the assembly frame.

**What changes:**
1. **The teamlead's routing.** A ships inside F's PR (FB1). A's `check` failure (the D34 nub's sliver at the rail's z ≈ 0 after D44) is fixed by F deleting the nub, and F must prove it (FB2).
2. **AM2-1 is withdrawn** (A's verdict note). F's coupon keeps the strip inset on its own evidence (FB3).
3. **R41 must be replaced whole.** F's two-phrase edit would leave "tilts until the upper lip engages" standing next to "the upper flank bears" (FB4).
4. **A missed safety point.** A gravity lock does not hold when the TV is laid down, carried or tilted, or when a TV lift tilts or flips it. The user-facing texts must say so, and Q23 asks about the user's lift (FB5).
5. **Missed normative mentions.** Five records still name the latch or the `rail-latch` coupon, and the §9 "next free id" is wrong (FB6, FB7).
6. **Smaller items:** the §3 rule must forbid brackets passing `lock_e` (FB8); CLAUDE.md additions (FB9); records (FB10); golden rules for the combined PR (FB11); the e-ladder (FB12).

## Binding changes

**FB1 — Routing (teamlead decision, confirmed).**
- F branches `feature/gravity-lock` from the head of `feature/wide-dovetail` (A's **draft** branch) now. It does not wait for A to be green.
- A's PR stays a draft and never merges on its own. **F's PR into `main` carries A and F together** and merges only CI-green. A's draft PR is then closed as superseded.
- When C (#57) merges, rebase the A+F stack onto `main`. After every rebase, regenerate goldens with the targeted command (FB11) and re-run §12 steps 9–15. Never hand-merge golden JSON.
- F §1 precondition 1 becomes: "Branch from the head of `feature/wide-dovetail`". Precondition 2 (rev 16 present) and 3–5 (anchors, region, grep) stay.
- If an A anchor is missing because A's developer stopped early, stop and report.

**FB2 — `check` gate: one part and watertight, everywhere.**
- After §12 step 10, `check` must report **1 part, watertight** for every part, and explicitly for:
  - `brackets/arch-tv-bracket` `centre` and `arm`;
  - `coupons/rail-lock`;
  - all 8 bases, plus `base_fan`.
- **Pre-approved fallback.** If any part carrying the lock bump or pocket shows more than one part, the cause is the D34 nub's failure mode: a polygon vertex exactly on the flank line (y = −MOUTH_W/2) at the rail's z = 0.
  - In that case, and only then, replace `_mcc_rail_lock_2d()`'s `polygon([...])` with the trapezoid below.
  - The trapezoid continues the ramps 0.2 mm into the core, so no vertex lies on the flank line. The bump outside the flank, the pocket and every assert are unchanged.
  - Then re-run steps 9–13. If it still fails, stop and report.
```openscad
    x_in  = g[0] - 0.2 * g[2] / e;   // entry ramp continued 0.2 mm into the core
    x_out = g[1] + 0.2 * g[3] / e;   // exit face/ramp continued likewise (== g[1] for a 90 deg exit)
    offset(delta = grow)
        polygon([[x_in, y0 + 0.2], [g[0] + g[2], y0 - e], [g[1] - g[3], y0 - e], [x_out, y0 + 0.2]]);
```

**FB3 — The coupon keeps the 1 mm strip inset.**
- F6.1's lines `for (y0 = [-footprint_d / 2 + 1, footprint_d / 2 - 1 - STRIP_W])` stay.
- They are justified independently of the nub: F's own prototype coupon has no nub, and with the strips flush it failed `check` with 2 parts (a zero-volume sliver on the bed plane); moved 1 mm in, it passed.
- Keep F6.1's comment, with its last two lines replaced:
```
// the groove's open +X end. (Flush with those edges they left a zero-volume sliver on the bed plane:
// `check` saw 2 parts and no watertight mesh.)
```
  become:
```
// the groove's open +X end. (Flush with those edges they left a zero-volume sliver on the bed plane:
// in plan F's prototype, which has no latch nub, `check` saw 2 parts and no watertight mesh.)
```
- F §6's note "If A's merged coupon already fixed the strips differently…" is obsolete: A does not fix them.

**FB4 — R41 is replaced whole.**
- F's X5 phrase edits are void. Replace the **whole** R41 paragraph, from its line beginning `**R41 — clearance means play` through the line that ends `a developer tweak.`, with Appendix G5's R41. This works whether or not A's developer applied AM2-2.
- Also replace `the gravity-side flank also` with `the upper flank (rail-local −Y) also` where it still appears: once in `architecture.md` §6 (the D44 paragraph) and once in `lib/mcc/constants.scad` (the "Rail clearances (D44 …)" comment). Comment and prose only.

**FB5 — The gravity lock does not hold off-pose.** Say so, and ask about the lift.
- R44 gains the rule (Appendix G5): **take the case off before the TV is laid down, carried or tilted, including by a TV lift that tilts or flips it.**
- **Q23** asks whether the user's lift ever takes the TV out of upright (G6). This matters for a live-performance product on a lift.
- The same rule goes into:
  - the brackets README's "Installing and removing a case" (an extra bullet, below);
  - CLAUDE.md's D49 sentence (FB9);
  - print-check's arch row: append `Take the case off before the TV is laid down, carried or tilted (R44).`

  README bullet, appended to F10.6 item 4's fenced block:
```
- **Before the TV moves:** take the case off before the TV is laid down, carried or tilted — including by
  a TV lift that tilts or flips it. The lock only holds while the case hangs patch-wall down (R44).
```

**FB6 — Normative mentions F missed** (the verbatim texts are in Appendix G):
- §3's L1 table row for `rail.scad`;
- §6 D44 paragraph: `rail-latch` coupon → `rail-lock`;
- R24: `rail-latch` coupon → `rail-lock`;
- R26: "dovetail+latch" → "dovetail + gravity lock";
- R40: `rail-latch` coupon → `rail-lock`;
- in `layout-patch-wall.md`: the rev-17 header and the T1-62 row edit.

History stays as written: rev headers, D-rows, old gate tables, CHANGELOG entries and `docs/plans/**`.

**FB7 — Ids.**
- The §9 "next free id" statement is Appendix G4's: T1-67…T1-69 unused, T1-70…T1-90 belong to plan D, and the next free id is **T1-91**. It is not F's proposed "T1-67".
- R46 is unused.
- Q23 is used (FB5).
- The numbering note gains `> **Rev 17** adds M21.`

**FB8 — Brackets never pass `lock_e`.** The §3 consumer rule (Appendix G2) says so:
- only the rail-lock coupon's e-ladder passes it, and always to both halves;
- a bracket calls `mcc_rail_male()` or `mcc_rail_male(len)` only.

**FB9 — CLAUDE.md.**
- F10.1 and F10.3 as written.
- F10.2 as written, plus one sentence at the end: `Take the case off before the TV is laid down, carried or tilted (R44).`
- In "Non-negotiables", "Coupons before cases", replace `` `tolerance-ladder` are printed `` with `` `tolerance-ladder` and `rail-lock` are printed ``. The rail-lock coupon is the physical gate for the case's groove roof (R40), pocket and lead-in (M15).
- Plan D's rev-2 verdict, Appendix E1, is amended in this run to carry these D49 sentences when D rewrites that bullet.

**FB10 — Records.**
- F10.10 as written.
- **Re-sync `docs/plans/2026-09-28-wide-dovetail.md`** (A's record, B14) so its appended verdict equals A's final verdict file: Amendments 1–2 plus the AM2-1 withdrawal note.
- `architecture.md` and `layout-patch-wall.md` take this verdict's Appendix G/H text, which replaces the plan's Appendix X. Appendix X stays in the plan record as the proposal.

**FB11 — Golden rules for the combined PR.**
- F §9's list is relative to A's branch head.
- **Relative to `main`**, the combined PR may change goldens only as follows:
  - content changes in the 8 `(slug).base.json`, `pro-convert-for-ndi-to-hdmi.base_fan.json`, and `brackets/arch-tv-bracket.arm.json` + `.centre.json`;
  - deletions of `brackets/tv-bracket.json` (A, AM-3) and `coupons/rail-latch.json` (F6.2);
  - one addition, `coupons/rail-lock.json`.
- No `*.lid.json` and no other coupon may move. Check with `git diff --stat main -- tests/golden/` before the PR.
- After the final rebase, regenerate with one targeted command:
```
python scripts/build.py golden coupons/rail-lock brackets/arch-tv-bracket pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio --update
```

**FB12 — e-ladder.**
- Rendering it with `-D LOCK_E=…` is accepted for this coupon. The release export stays the production 0.70.
- The README says the **teamlead or tester** produces the ladder 3MFs for the user; the user does not run `build.py`.
- Non-binding: if the ladder is printed more than once, a follow-up can add an exported `rail-lock-ladder` coupon (four rail halves, 0.5–0.8, one groove half).
  - One groove half cut for 0.8 serves every rung. Cut it for 0.8, not 0.7: a groove cut for 0.7 would give the 0.8 rung less than the design clearance (≈ 0.48 mm laterally instead of 0.577).
  - That coupon needs its own gate.

## Rulings

- **Order and branching:** C → A+F (one PR) → D. Plan D's rev-2 verdict is unaffected, except FB9's note in its Appendix E1.
- **The strip inset:** kept (FB3). **AM2-1:** withdrawn. **AM2-2:** carried by F (FB4).
- **Coupon rename `rail-latch` → `rail-lock`:** approved. It now tests a lock, and every reference is updated (F10.x).
- **`plate_t` removed from `mcc_rail_male()`:** approved. D will copy the post-F arch call (D verdict, DB1).
- **`MCC_RAIL_END_STOP_L/H` kept:** approved, out of scope.

## DO NOT

- Do not merge A on its own, and do not apply AM2-1 anywhere except through F6.1's rewrite.
- Do not touch the bump polygon unless FB2's fallback condition occurs, and then apply exactly FB2's replacement.
- Do not put a lock bump on the +Y flank, or add a flexing element, a thumb release or any plate cut to the rail.
- Do not change `MCC_RAIL_ROOT_W`, `_Y`, `_DEPTH`, `_FLANK_ANGLE`, `_LEN`, `_MATE_CLR`, `_CLR_HORIZ`, `_ROOF_CLR` or `_MALE_H`.
- Do not change any `MCC_RAIL_LOCK_*` or `MCC_RAIL_LEADIN` value to make a gate pass.
- Do not change the arch's `CENTRE_W`, `ARCH_PLATE_T`, `RAIL_X` or any geometry beyond F §5.
- Do not add a floor keep-out row for the pocket.
- Do not touch plan D's files.
- Do not run an untargeted `golden --update`, and do not hand-edit JSON.
- Do not reassign T1-67…T1-69 or R46.

## Implementation order

1. From the head of `feature/wide-dovetail`: F §1 checks. Note in the PR whether A's developer applied AM2-2; FB4 replaces R41 whole either way.
2. Branch `feature/gravity-lock`, then F §2–§8, with FB3's comment tweak.
3. Gates:
   - `doctor` and `smoke`;
   - `render --all` and `check --all` (**FB2**);
   - `rail_fit.py` on the 3 SKUs: `rail fit OK`, max lift 0.70 ± 0.02, play 1.154 ± 0.02;
   - goldens (§9 against A's head, then FB11 against `main`);
   - `slicer-check` with zero warnings;
   - `review`;
   - `ci --group k/6` for k = 1…6.
4. Docs:
   - F §10;
   - FB5's README bullet and print-check addition;
   - FB9's CLAUDE.md changes;
   - Appendix G into `architecture.md`, Appendix H into `layout-patch-wall.md`;
   - F10.10;
   - FB10's re-sync.
5. After C (#57) merges: rebase A+F onto `main`, regenerate goldens (FB11), redo step 3, and confirm `git diff --stat main -- tests/golden/`.
6. Open **one PR, A+F, into `main`**.
   - The body cites D44–D50, T1-62…T1-66, R40–R45, M15, M21 and Q21/Q23, and pastes the three `rail_fit.py` summaries.
   - It must be CI-green before it merges. Then close A's draft PR as superseded.
7. Physical gate: M15 (the rail-lock coupon, including hanging and the e-ladder), then M21 on the first bracket.

---

## Appendix G — `.claude/knowledge/architecture.md` (rev 17; replaces the plan's Appendix X)

Paste rule: copy only the text inside the fences.

**G1 — Header.** Insert immediately before the paragraph beginning `**Revision 16, 2026-09-28`, followed by one blank line:
```
**Revision 17, 2026-09-28 (gravity rail lock — D48–D50; plan `docs/plans/2026-09-28-gravity-lock.md`;
shipped in one PR with rev 16).** User decisions after the analysis of the external specialist's DP48
plate: the rail lock is a **gravity lock only** — a rigid 0.7 mm bump on the rail's upper (rail-local
−Y) flank drops into a pocket in the groove flank and is held there by the case's own weight; the **D34
snap latch is removed** (arm, window, nub, notch, `MCC_RAIL_LATCH_*`, `MCC_SNAP_STRAIN_MAX`). **A mounted
case always hangs patch-wall down** (D49). The groove entrance gets the DP48's 1 × 45° lead-in. Brackets
consume the rail only through `mcc_rail_male()` (no plate cut) and `mcc_rail_male_keepout()` (D50). New:
**T1-64 … T1-66**, **R44**, **R45**, **M21**, **Q23**; M15 rewritten; Q21 closed; R41 corrected (the upper
flank bears). T1-67 … T1-69 and R46, reserved for this revision, stay unused. No case envelope figure
moves.
```

**G2 — §3.**
1. In the L1 table, replace:
```
    lib/mcc/rail.scad                     mount-rail dovetail profile: male rail, female cut,
                                          spring-lip latch. ONE source of truth shared by
```
   with:
```
    lib/mcc/rail.scad                     mount-rail dovetail profile: male rail, female cut,
                                          gravity-lock bump and pocket, plate-side keep-out
                                          (rev 17). ONE source of truth shared by
```
2. In the `rail.scad` bullet, replace `` `mcc_rail_male()` (additive), `mcc_rail_female_cut()` (subtractive), `mcc_rail_sill_size()` (pure). `` with `` `mcc_rail_male()` (additive), `mcc_rail_female_cut()` (subtractive), `mcc_rail_sill_size()` and `mcc_rail_male_keepout()` (pure, rev 17). ``
3. Insert directly after the line `    rule (§6) has one owner.`:
```
  - **Brackets consume the rail through two public symbols only** (rev 17, D50): `mcc_rail_male(len)`,
    unioned onto the bracket's plate — the rail needs no cut in any plate — and
    `mcc_rail_male_keepout(len)`, the rail-local plate-side keep-out (bump included) that the bracket
    maps through its own placement and pads with its own clearance. A bracket never passes `lock_e`
    (only the rail-lock coupon's e-ladder does, always to both halves), never reads `MCC_RAIL_LOCK_*`
    or other rail internals, and never rebuilds the rail's footprint.
```

**G3 — §6 D44 paragraph.**
1. Replace:
```
  under the 4.0 groove, and the latch notch runs the full depth over the nub) — **T1-62**. The D34
  latch is the lock; its plate window also clears the nub. The Fishtail and case-insert reservations
```
   with:
```
  under the 4.0 groove, and the lock pocket runs the full depth over the bump) — **T1-62**. The lock
  is the gravity lock (D48): a rigid bump on the rail's upper flank in a pocket of the groove flank,
  held by the case's weight — no plate cut, no flexure. The Fishtail and case-insert reservations
```
2. Replace `` `rail-latch` coupon (R40, M15). `` with `` `rail-lock` coupon (R40, M15). ``
3. FB4's `the gravity-side flank also` → `the upper flank (rail-local −Y) also`, if still present.

**G4 — §9 prose.** Insert immediately before the line beginning `Full table with sources: `:
```
**Rev 17 adds T1-64 … T1-66** (D48, the gravity lock: T1-64 the lift budget `MCC_RAIL_LOCK_ENGAGE +
MCC_RAIL_LOCK_PLAY_MARGIN ≤ 2·MCC_RAIL_CLR_HORIZ`; T1-65 the exit face 75–90°, the entry ramp 15–60° and
the bump inside the working length; T1-66 the sill wall behind the pocket ≥ `MCC_WALL/2` and the
lead-in ≤ `MCC_WALL`). T1-67 … T1-69, reserved for rev 17, stay unused; T1-70 … T1-90 are assigned to
plan D (rev 18). **The next free id is T1-91.**
```

**G5 — §11.**
1. R24: replace `` The `rail-latch` coupon (M15) is what turns it `` with `` The `rail-lock` coupon (M15) is what turns it ``.
2. R26: replace `and the dovetail+latch is not claimed as the primary fall restraint` with `and the dovetail + gravity lock is not claimed as the primary fall restraint`.
3. R40: replace `` The `rail-latch` coupon's groove half prints in the same pose (D46 fix) and is `` with `` The `rail-lock` coupon's groove half prints in the same pose (D46 fix) and is ``.
4. R41: replace the whole paragraph (FB4) with:
```
**R41 — clearance means play, and on a TV-mounted bracket a flank carries the weight. NEW 2026-09-28
(rev 16, D44; flank corrected rev 17).** With 0.5 mm normal clearance at 60° flanks the case has
≈ ±0.58 mm lateral and ≈ 1.0 mm lift play before the dovetail engages. Lying flat, the floor-on-plate
seat bears and the flanks float. **Hung on a TV** (the arch bracket, the planned vertical bracket)
gravity acts along the case's own Y and the **upper flank bears** (rail-local −Y — the brackets'
`rotate([0,0,180])` puts it on top): the case's upper groove wall hooks over the rail's upper flank like
a French cleat, loading it with ≈ 1.15 × the case's weight normal to the flank, and the flank's 60°
slope pulls the case onto the plate with ≈ 0.58 × its weight. The tipping moment of the case's offset
centre of mass is taken by that hook and by the floor pressing on the plate below the rail. All
clearance collects at the lower flank (≈ 1.15 mm horizontal), so gravity keeps the case seated; only a
push against its weight lifts it off the upper flank. Acceptable (user decision), and the gravity lock
(D48) holds X while the case hangs. Measure it on the coupon (M15) and on the first bracket print. If
it is objectionable the lever is `MCC_RAIL_MATE_CLR` — a **user** decision (D44), not a developer
tweak.
```
5. Insert directly after R43's block, with a blank line before:
```
**R44 — the rail lock is gravity-engaged. NEW 2026-09-28 (rev 17, D48/D49).** While the case hangs
patch-wall down its weight holds the bump in its pocket (≈ 0.6–1.15 × the weight, normal to the flank,
depending on whether the case yaws about its −X end), and the square exit face stops any axial pull at
or below the rail line — including every cable load at the patch wall. It does not hold when that
flank is unloaded: while the case is being hung, when the TV is laid flat, carried or tilted, or when
the case is pushed upward; then only friction resists sliding. **Take the case off before the TV is
laid down, carried or tilted — including by a TV lift that tilts or flips it (Q23).** A −X pull on the
case's top (far-wall) edge can yaw its +X end up and release it at ≈ 3 × the weight — also the natural
hand release. Mitigation: D49, the install/removal text (brackets README), M21. Accepted by the user.

**R45 — the ride-over needs the printed flank play. NEW 2026-09-28 (rev 17, D48).** The case rides over
the 0.70 mm bump inside the dovetail's own 1.155 mm horizontal play (0.45 mm margin; T1-64 asserts
≥ 0.2). A print that comes out more than ≈ 0.1 mm oversize on each of the four flank faces binds —
nothing is designed to flex. M15 measures the printed play and runs the e-ladder; if it binds, lower
`MCC_RAIL_LOCK_ENGAGE` (0.5 is still self-locking). Never widen the rail or change `MCC_RAIL_MATE_CLR`
(user decisions).
```

**G6 — §12.**
1. Replace item 21 (from its line beginning `21. **The rail lock` through the end of that item) with:
```
21. **The rail lock — DP48. Answered 2026-09-28 (rev 17).** The DP48 plate was analysed (scratch F2): a
    15° dovetail whose two 0.8 mm strips ride inside the dovetail's own play into recesses — a rigid,
    gravity-seated detent. User decision: **gravity lock only**, the D34 latch removed (D48); a mounted
    case always hangs patch-wall down (D49). The "tool-less, no thumbscrews" question is moot — the lock
    has no actuator. *(Also answered: the groove's closed −X end stays the axial end stop.)*
```
2. Insert directly after item 22:
```
23. **Does the user's TV lift ever take the TV out of upright? NEW 2026-09-28 (rev 17, R44) — needs the
    user.** The gravity lock only holds while the case hangs patch-wall down. A lift that only raises
    and lowers an upright TV is fine; a ceiling flip-down, tilting or swivelling lift leaves the case
    unlocked in some poses — then the case must come off before the lift moves, or the lock decision
    (D48) goes back to the user.
```
3. Replace the whole row beginning `| **M15** |` with:
```
| **M15** | **Print `models/coupons/rail-lock` and test it:** (a) roof sag on the groove half — roof height at mid-width vs 4.0 mm; the rail's 3.5 mm top must not touch it (R40); (b) play with the lock not engaged — expect ≈ 1.15 mm lateral (R41, R45); (c) **the lock, hanging**: rail plate vertical, groove half loaded to the heaviest case (≈ 0.8 kg, `assumed` — weigh one) — it rides over the bump without binding and clicks; an axial pull at the rail line does not release it up to ≥ 50 N; an outward tug at the lower edge does not release it; lifting ≤ 1.2 mm and sliding releases it one-handed; (d) e-ladder `LOCK_E` 0.5 / 0.6 / 0.8; (e) 100 cycles, then (b)–(c) again and inspect the bump and the pocket's +X wall | R40, R41, R44, R45 — every `MCC_RAIL_*` figure is `assumed` except the user-decided width and clearance. (a) decides `MCC_RAIL_ROOF_CLR`; (c)/(d) decide `MCC_RAIL_LOCK_ENGAGE`. **"Coupons before cases" applies to brackets too — no full-size bracket prints before this** | User, with a luggage scale, a dummy mass and calipers |
```
4. Insert directly after the row beginning `| **M20** |`:
```
| **M21** | **First bracket print (arch, direct mode), with a real case and device:** the lock's yaw release force for a −X pull on the case's top (far-wall) edge (≈ 3 × the weight expected), no release for pulls on the patch-wall edge and on the cables, and the one-hand lift-and-slide removal behind a mounted TV | R44 — the 60 mm coupon cannot reproduce the full case's yaw lever | User |
```
5. Insert after the last numbering-note line:
```
> **Rev 17** adds M21.
```

**G7 — §13.** Insert directly after the row beginning `| **D47** |` (one row per line):
```
| **D48** | 2026-09-28 | D34 (in-plane snap latch: arm, slot, plate window, nub, notch) and D44 ("the D34 latch stays the lock"); Q21 | **User decision 2026-09-28**, after analysing the specialist's DP48 plate (scratch F2): **gravity lock only**, the D34 latch removed; adopt the DP48's 1 × 45° entry lead-in | D34 released by pulling (≥ 30 N target, never measured; a beam estimate gave ≈ 10–19 N) and needed a window through every consumer plate; with D44's flush seat its nub also sat on the plate plane and left a zero-volume sliver that failed `check` on the arch centre and the coupon | **Done in rev 17 (plan F, `docs/plans/2026-09-28-gravity-lock.md`; shipped in one PR with rev 16).** A rigid bump on the rail's −Y flank (`MCC_RAIL_LOCK_ENGAGE` 0.70 horizontal, 30° entry, 90° exit, exit face `len/2 − 3.0`) drops into a pocket in the groove's −Y flank (the bump grown by `MCC_RAIL_CLR_HORIZ`, full groove depth); nothing flexes — the case rides over it inside the dovetail's own 1.155 mm play (T1-64); square exit face (T1-65); sill wall behind the pocket ≥ 1.5 mm (T1-66); release = lift ≈ 1 mm + slide. Lead-in `MCC_RAIL_LEADIN` = 1.0 at the case's +X face (`mcc_rail_female_cut(entry_x)`). Removed: `_mcc_rail_latch_geom()`, `_mcc_rail_nub_2d()`, `_mcc_rail_latch_cut_2d()`, `mcc_rail_male_window()`, `mcc_rail_male(plate_t)`, every `MCC_RAIL_LATCH_*`, `MCC_SNAP_STRAIN_MAX`. `rail_fit.py` proves the lift, the lock and the full-mate clearance; coupon `rail-latch` → `rail-lock` (snap-off strips 1 mm in from the edges, justified by the lock-only prototype). M15 rewritten, M21, R44, R45, Q23; Q21 closed |
| **D49** | 2026-09-28 | Issue #26's orientation *convention* ("mount with +Y up so the patch wall hangs down"); the arch README: nothing keys the assembly against a 180° install | **User decision 2026-09-28: a mounted case ALWAYS hangs patch-wall down** — every bracket, the truss use (#27) included, no portrait TV | The gravity lock (D48) only engages when the case's weight rests on the rail's −Y flank | **Fixed decision, rev 17** (CLAUDE.md, brackets README, print-check). Every bracket keeps the `rotate([0,0,180])` rail placement. Take the case off before the TV is laid down, carried or tilted (R44, Q23). Still no physical key against a 180° install — the arch's UP arrow and shape remain cues |
| **D50** | 2026-09-28 | §3 rail rules: brackets called `mcc_rail_male(plate_t)` + `mcc_rail_male_window()` and built keep-outs from `MCC_RAIL_LATCH_*` | Plan-D gate (F-R1/F-R2): a bracket must not know rail internals | Every rail change would ripple into every bracket file | **Done in rev 17 (plan F).** `mcc_rail_male_keepout(len)` (pure, `rail.scad`) returns the rail-local plate-side keep-out `[[x_min, x_max], [y_min, y_max]]`, bump included; a bracket unions `mcc_rail_male(len)` onto its plate (no cut), never passes `lock_e`, and reads only that accessor. The arch migrated (`RAIL_KEEPOUT_X/Y`); plan D (rev 18) uses only these two |
```

## Appendix H — `.claude/knowledge/layout-patch-wall.md` (rev 17)

**H1.** Insert immediately before the line beginning `Status: **revision 16, 2026-09-28**`, followed by one blank line:
```
Status: **revision 17, 2026-09-28** (aligned with `architecture.md` rev 17 — D48, the gravity lock). **§9**
gains **T1-64 … T1-66**, and the T1-62 row's mate check now covers the lock bump. No envelope figure
moves on any SKU.
```

**H2 — §9, T1-62 row.** Replace `only the nub overlaps while sliding` with `only the lock bump overlaps while sliding, and the lift it needs stays inside the flank play (T1-64)`.

**H3 — §9.** Insert directly after the row beginning `| **T1-63** |`:
```
| **T1-64** | *the case rides over the lock bump inside the flank play* — `MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_LOCK_PLAY_MARGIN ≤ 2·MCC_RAIL_CLR_HORIZ` (0.70 + 0.2 ≤ 1.155) | **new rev 17** (D48). Evaluated in `mcc_rail_male()` and `tests/test_rail.scad`; `scripts/rail_fit.py` measures the real lift (0.70 ± 0.02) against a rendered base |
| **T1-65** | *the lock is self-locking and fits the rail* — exit face 75–90° to the slide axis, entry ramp 15–60°, the bump inside `(−len/2 + 5, len/2 − 1)` | **new rev 17** (D48). Evaluated in `mcc_rail_male()` and `tests/test_rail.scad` |
| **T1-66** | *the case keeps wall around the lock* — sill wall behind the pocket `MCC_RAIL_SILL_SIDE_W − MCC_RAIL_CLR_HORIZ − lock_e ≥ MCC_WALL/2` (1.72 ≥ 1.5); lead-in `MCC_RAIL_LEADIN ≤ MCC_WALL` | **new rev 17** (D48). Evaluated in `mcc_rail_female_cut()` and `tests/test_rail.scad`. T1-67 … T1-69 stay unused; T1-70 … T1-90 belong to plan D; **the next free id is T1-91** |
```
