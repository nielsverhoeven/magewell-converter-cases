# Plan A — wide dovetail with lock (rev 2), post-D34/D35 baseline

> **Implemented as amended by the architect verdict appended at the end of this file (B1–B17 and Amendment 1). Where they conflict, the verdict wins. §6 (lock) is informational only.**

Status: draft, NOT yet architect-validated. Route through `solution-architect` before any developer
starts.

Repo state: `main` @ `047902e`. Rev 2 supersedes rev 1 entirely (same file, overwritten) per user
decisions of 2026-09-28, relayed by the teamlead. **Section 6 (the lock) is a deliberate placeholder**
— do not implement it; the teamlead will resume this plan once a parallel researcher's analysis of
Christopher's DP48 STEP files lands.

**User decisions this revision implements:**
1. Coupling stays the dovetail, with an added lock. No thumbscrews.
2. Width: intermediate, dovetail root width in the 60–70 mm range — value picked and justified below.
3. Drop `fishtail_reserve` AND `case_tripod_insert` (the D35 boss is already gone; this retires the
   reservation too) so the rail can cover the floor centre.
4. Clearance ≥ 0.5 mm on every non-bearing surface: flanks (0.57735 mm horizontal, unchanged from rev
   1) **and now also the groove roof** (taper top vs. groove ceiling) — rev 1's "0 mm roof gap is
   fine" call is overridden by explicit user instruction.
5. Place the rail near the device/case centre of mass in Y (R24 roll-moment resistance), re-checked
   against every floor/wall feature, both existing brackets, and the new vertical bracket.
6. Lock: placeholder only, pending DP48 analysis.

---

## 0. Numeric evidence and scope carried over from rev 1, still valid

- The **standoff fix** (§1 below) is unchanged from rev 1: remove `mcc_rail_male()`'s `MCC_FLOOR_T`
  pedestal, `male-local Z = female-local Z` identity, drop `+ MCC_FLOOR_T` from both brackets' mate
  transforms. All of rev 1 §1's reasoning and exact edits still apply and are repeated in §1 below
  with the roof-clearance interaction folded in.
- The **mated-intersection prototype** from rev 1 (a real CGAL/Manifold `intersection()` render
  returning "Current top level object is empty") is still valid evidence for the flank-clearance
  mechanism; re-run at the new width in §7 before treating this plan as verified — the numbers moved,
  the method didn't.
- **Hard-won lesson, repeat:** any manual epsilon-overlap cut in a prototype must grow the shape's
  height, not just translate it (`_mcc_rail_taper_eps()`'s own pattern) — a bare Z-shift produced a
  false non-empty intersection when this was checked in rev 1.

---

## 1. Standoff fix (unchanged from rev 1) + its interaction with the new roof clearance

### 1.1 Remove the pedestal

`mcc_rail_male()` (`lib/mcc/rail.scad:222-236`) unions a `MCC_FLOOR_T`-tall pedestal under the taper.
Delete it; the male becomes just the taper, standing directly on the bracket's flat top face at local
Z=0 (see §4 for why it is now shorter than `MCC_RAIL_DEPTH`, not equal to it).

**Exact edits to `lib/mcc/rail.scad`:**

1. In `mcc_rail_male()`'s `union()`: delete
   `cuboid([len, MCC_RAIL_MOUTH_W, MCC_FLOOR_T], anchor = BOTTOM);` entirely, and change
   `translate([0, 0, MCC_FLOOR_T]) _mcc_rail_taper(len);` to just calling the taper at Z=0 with the
   new, shorter male height (§4 gives the exact call).
2. `_mcc_rail_flank_extrude(z0, z1)`: change `zb = MCC_FLOOR_T;` to `zb = 0;`, with a comment that the
   "straight" branch now only ever fires for a leg reaching *down* into the consumer's plate
   (`z0 < 0`), since the pedestal segment it used to represent no longer exists.
3. `mcc_rail_female_cut()`'s notch: delete the `translate([0, 0, -MCC_FLOOR_T])` wrapper (was
   compensating for the old `male Z = female Z + MCC_FLOOR_T` relationship — now `male Z = female Z`,
   identity, no compensation needed). See §4 for the exact new Z-range (it is not simply
   `[-MCC_EPS, MCC_RAIL_DEPTH]` any more, because of the roof clearance).
4. The latch-height assert (was `MCC_RAIL_SILL_H + plate_t >= 5`): change to reference the male's
   *actual* new height, `MCC_RAIL_MALE_H` (§4) — `MCC_RAIL_SILL_H` (7.0) stays the *case-side* sill
   height (T1-38, unrelated to the bracket) and must not be reused here.
5. Rewrite the stale header block (lines 35-43): no more pedestal/standoff language; state the local
   Z=0 correspondence is direct on both halves, and that the flat case-floor and flat bracket-plate
   faces, everywhere outside the two footprints, sit flush by construction.

**`lib/mcc/mounts.scad` needs no change for the standoff fix** — confirmed again on rev 2: every
`MCC_RAIL_SILL_H` reference there (`mcc_floor_features_add()`'s sill block, the D34 passage's
`pass_h` cap) is already case-side and untouched by the male's own pedestal.

### 1.2 Both bracket mate transforms drop `+ MCC_FLOOR_T`

- **`models/brackets/tv-bracket.scad:236`**: `translate([0, MCC_RAIL_Y, MCC_FLOOR_T]) rotate(...)` →
  `translate([0, MCC_RAIL_Y, 0]) rotate(...)`. Rewrite the "Derivation of the rotate([0,0,180])"
  comment block (lines 39-57) to the simpler, offset-free composition.
- **`models/brackets/arch-tv-bracket.scad`**: see §5 — bound up with the sweep-condition re-derivation,
  not a standalone edit.
- **`models/coupons/rail-latch.scad`**: no edit — it only calls the two public rail functions, so both
  fixes are picked up automatically. Its golden moves (§7).

---

## 2. Retire `fishtail_reserve` and `case_tripod_insert`

### 2.1 What to delete

**`lib/mcc/layout.scad`, `mcc_floor_keepout()`:** delete both rows —
```
[floor_center[0], floor_center[1], "circle", MCC_CASE_INSERT_KEEPOUT_D, "case_tripod_insert"],
[floor_center[0], floor_center[1], "rect", MCC_FISHTAIL_BAND, "fishtail_reserve"],
```
and the now-unused `floor_center = [0, 0]` local (nothing else in this function reads it once both
rows are gone — confirm with a grep before deleting, but tracing the current code, this is its only
use).

**`lib/mcc/mounts.scad`, `mcc_assert_floor_keepout_no_overlap()`:** delete the now-dead exemption
clause for the `"case_tripod_insert"`/`"fishtail_reserve"` pair (D19) — both labels can never appear
in the list again, so the `if (!((rows[i][4] == "case_tripod_insert" && ...) || ...))` wrapper around
the assert becomes unreachable dead code. Simplify back to a plain, unconditional pairwise assert.

**`lib/mcc/constants.scad`:** delete `MCC_CASE_INSERT_KEEPOUT_D` and `MCC_FISHTAIL_BAND` — both become
fully unused once their only consumer (the two rows above) is gone. Verify with
`grep -rn "MCC_CASE_INSERT_KEEPOUT_D\|MCC_FISHTAIL_BAND" lib/ models/ tests/` before deleting; if
either has grown a second consumer since this research pass, stop and report rather than deleting
silently.

### 2.2 `cfg["tripod_insert"]` — recommend assert-incompatible, not full retirement

The D35 boss (`mcc_case_tripod_insert_boss()`/`mcc_tripod_insert_bore_cut()` in `lib/mcc/cradle.scad`,
opt-in via `cfg["tripod_insert"]`, default `false` since D35) is **not itself removed by this plan** —
only the always-on floor *reservation* for it is. Recommendation: **make `tripod_insert=true` and
`rail=true` mutually exclusive by assert**, not delete the boss capability outright.

Reasoning for recommending this over full retirement: nothing currently ships with
`tripod_insert=true` (D35's default is already `false`), so there is no live regression either way.
Deleting the boss/bore modules and their T1-32/T1-41 asserts is real, working, tested code with no
compensating benefit today — it forecloses a genuine future option (a non-bracket-mounted variant that
still wants a floor tripod thread) for zero present gain. An assert is cheap, reversible, and states
the real physical fact plainly: with the rail now covering the floor centre, the two features cannot
coexist. If the architect judges the future-optionality argument not worth carrying, full retirement
(deleting `mcc_case_tripod_insert_boss()`/`_bore_cut()`, their call sites in `cradle.scad`, the
`tripod_insert` cfg key from all 8 `case.scad` files, and `MCC_INSERT_1_4_20` if it becomes unused) is
the documented alternative — flagged for the architect to pick, not silently assumed.

**Exact edit, `lib/mcc/cradle.scad`, `mcc_cradle()`** (where `tripod_on` is read): add, right after the
existing `tripod_on = is_undef(tripod_flag) ? false : tripod_flag;` line —
```
assert(!(tripod_on && struct_val(cfg, "rail") != false),
    "mcc: cfg[\"tripod_insert\"]=true cannot combine with the mount rail (cfg[\"rail\"], default "
    + "true) -- the rail now covers the floor centre the tripod insert boss needs (2026-09-28 "
    + "wide-dovetail decision). Set [\"rail\", false] to use the tripod insert instead.");
```
(`struct_val(cfg, "rail") != false` mirrors the same `is_undef(...) ? true : ...` default the rail
flag itself uses elsewhere, so an *absent* `"rail"` key — which defaults to rail-on — correctly still
trips this assert.)

### 2.3 `CLAUDE.md`'s fixed-decision floor-features line

This file is project-owned prose, not something this plan edits — proposed replacement text for
whoever applies it (the current line is already stale, predating D-15's VESA removal):

> Floor features (one owner, `mounts.scad`): the tool-less dovetail mount rail (default; see §11 D-xx
> for width/placement), strap slots, splitter tie-down, stacking profile. The case's own 1/4"-20
> threaded insert is an **opt-in alternative to the rail**, mutually exclusive with it (assert-guarded,
> `cradle.scad`), not fitted by default. VESA 75×75 (D-15) and Magewell-Fishtail M4 compatibility
> (2026-09-28 wide-dovetail decision) have both been dropped — the rail now needs the floor centre they
> used to reserve.

### 2.4 What `architecture.md` §13 must record (architect's job — list only)

- A new deviation entry retiring `fishtail_reserve`/`case_tripod_insert` (user decision 2026-09-28,
  cite this plan), superseding the D19 exemption note (D19 itself becomes historical — the pair it
  exempted no longer exists).
- The `tripod_insert`/`rail` mutual-exclusion assert, its exact wording and location (§2.2), and which
  of the two options (assert-guard vs. full retirement) was chosen.
- `MCC_RAIL_ROOT_W`/`MOUTH_W`/`Y` new values and the centre-of-mass placement rationale (§3), recorded
  as R24's resolution/refinement, not a fresh risk.
- `MCC_RAIL_ROOF_CLR`/`MCC_RAIL_MALE_H`, the `_mcc_rail_taper()` height-parameter generalisation (§4).
- `ARCH_PLATE_T`, `CENTRE_W`, the corrected `centre_z_max` formula, and the T1-51 re-derivation (§5).
- The vertical-bracket centre-plate finding (§5.3): no growth needed, but its own B7/B8-equivalent
  asserts must be re-verified by that plan's own implementer against the new `MCC_RAIL_ROOT_W`.
- That `MCC_CASE_INSERT_KEEPOUT_D`/`MCC_FISHTAIL_BAND` were deleted, and confirmation no third
  consumer existed.
- That §6 (the lock) is intentionally unresolved in this plan revision.

---

## 3. Width and placement: 65 mm root, Y = −23.5

### 3.1 Why the device's Y-centroid is (almost) SKU-invariant

`y_dev_c = (MCC_GAP_FAR + MCC_WALL − MCC_T_PATCH − d_bay_free − MCC_GAP_DEV) / 2` — algebraically
independent of `dev_w`, `L`, and `W` (verified by simplifying `mcc_case_layout()`'s own formula, then
confirmed numerically: `pro-convert-hdmi-tx` (compact) and `pro-convert-hdmi-plus` (plus) both echo
**exactly `y_dev_c = −30.825`**, because both are HDMI-ended and `d_bay_free` is governed by whichever
port has the deepest bay — HDMI on both). BNC-ended SKUs (e.g. `pro-convert-sdi-plus`) shift by
`(75.65−74.6)/2 ≈ 0.5 mm` at most. **The device's own centre of mass sits at essentially one fixed Y
value across the whole family** — this is what makes "place the rail near it" a real, family-wide
placement, not a per-SKU compromise.

### 3.2 The exact-centroid placement doesn't fit 60–70 mm; the trade-off, quantified

Re-optimising against the *current* code's real numbers (re-echoed on rev 2; `fishtail_reserve` and
`case_tripod_insert` no longer bind, per §2 — the **only** remaining binding constraint is the
side-bolt support-web floor footprint, `−Y`):

```
c − h  >=  web_top + MCC_FLOOR_FEATURE_EDGE_MIN     (web_top = web_cy + 7)
```
(no `+Y`-side constraint survives §2's retirement — nothing else sits near the case's own plan
centre any more.)

At the exact device centroid `c = −30.825` (compact, the binding family): max sill half-width
`h = c − web_top − 2 = −30.825 − (−62.925) − 2 = 30.1` → max `ROOT_W = 2·(30.1−3) = 54.2 mm` — **below
the requested 60–70 mm range.** Getting to 65 mm requires shifting the centre toward `+Y` (away from
the far wall, toward the patch wall) by a small, quantified amount:

| Target `ROOT_W` | Required `c` (zero margin) | Shift off true centroid |
|---|---|---|
| 60 | −27.925 | 2.9 mm |
| 65 | −25.425 | 5.4 mm |
| 70 | −22.925 | 7.9 mm |

**Recommended: `MCC_RAIL_ROOT_W = 65.0` mm, `MCC_RAIL_Y = −23.5`** — the middle of the requested range,
at a centre giving **1.925 mm of margin beyond the bare 2 mm keep-out minimum** (i.e. ~3.9 mm of real
clearance from the side-bolt web), a **7.3 mm shift off the true device centroid** — modest relative
to the half-width (65/2 = 32.5 mm) being placed there. `plus`-family margins are larger still (web is
further from the case centre on that family) — confirmed by re-running the same check against
`pro-convert-hdmi-plus`/`pro-convert-sdi-plus`'s own echoed numbers; compact remains the governing
case.

**`MCC_RAIL_MOUTH_W` is now DERIVED from `MCC_RAIL_ROOT_W`, not the other way around** — flip the
existing formula (the width target is what the user specified, so it is the stored constant now):
```
MCC_RAIL_MOUTH_W = MCC_RAIL_ROOT_W - 2 * MCC_RAIL_DEPTH / tan(MCC_RAIL_FLANK_ANGLE);
                    // = 65.0 - 4.6188 = 60.3812. FLIPPED from the pre-2026-09-28 direction (mouth was
                    // the input, root derived) because the user's own requirement is stated as a root
                    // width target (60-70 mm range); deriving mouth from it keeps "formula, not
                    // magic number" while matching how the requirement was actually specified.
```

### 3.3 Everything else checked against the new (wider, re-centred) footprint

- **Strap slots**: compact `±67.925`, half-height 2.5 — nowhere near `[−58.5, 11.5]` (the new sill's Y
  range at `c=−23.5`, sill half `=35.5`). Unaffected, as before.
- **Splitter bay** (−X end, X-restricted): unaffected by a Y/width-only change (rail's X-span,
  `MCC_RAIL_LEN`, is untouched by this plan).
- **D34 +X-wall passage, now much wider**: its Y-width scales with the sill automatically (same
  `MCC_RAIL_ROOT_W + 2*MCC_RAIL_SILL_SIDE_W` term `mcc_floor_features_add()` already uses for both the
  main sill and the passage) — no separate edit. Its height cap, `pass_h = min(MCC_RAIL_SILL_H,
  fan_bay_z[0])`, is **purely Z-based and independent of Y/width** (confirmed again: `fan_bay_z[0]`
  depends only on `z_conn_c`/fan frame geometry, never on `MCC_RAIL_Y`/`ROOT_W`) — `pass_h` stays
  `5.5`, the `MCC_RAIL_PASSAGE_ROOF_MIN` margin stays the same `1.5 ≥ 1.2`, **numerically unchanged**
  from rev 1's finding.
- **Fan bay / fan cutout on the Plus family (ships with the fan by default) — checked explicitly, as
  asked.** `fan_y` defaults to `y_dev_c ≈ −30.825` — almost exactly where the rail now sits
  (`c=−23.5`, only 7.3 mm apart) — so the passage's Y-band now overlaps `fan_bay_y` far more than in
  rev 1 (`fan_bay_y = [−50.825, −10.825]` sits **entirely inside** the new passage Y-range
  `[−58.5, 11.5]`). This is safe for the same Z-capping reason above, but the fan's own **physical
  mounting screws** were also checked (`lib/mcc/fan.scad`: NF-A4x10 screw holes at `±pitch/2 = ±16 mm`
  in the fan's own local X/Y, mapping to world `Z = z_conn_c ± 16 = [9.5, 41.5]`) — the passage's `Z ≤
  5.5` stays **4 mm clear of the lowest fan mounting screw** regardless of how much Y-overlap exists.
  No collision with real fan hardware, by the same Z-separation argument, now with a concrete number
  behind it instead of an inference.
- **Cradle deck lattice**: unaffected in principle (Z-separated, as rev 1 established) — but the sill's
  Y-range now reaches slightly **positive** Y (`+11.5` at the recommended values), i.e. beyond the
  device's own `+Y` flank (`y_dev_hi = −0.725`, compact) into the open interior floor between the
  device and the patch wall. This is expected and harmless (no cradle feature exists out there to
  collide with) but means the sill is no longer entirely hidden under the device footprint — cosmetic
  only, note it in the PR so a reviewer isn't surprised by a visible floor step near mid-case.
- **`case_tripod_insert`/`fishtail_reserve` retirement (§2) is exactly what makes this centring
  possible** — under the old reservation, the same `c=−23.5` would have collided with the `+10`
  boundary those two rows used to enforce; confirmed this plan's width/placement choice depends on §2
  landing first (sequencing note carried into §7).

---

## 4. Groove-roof clearance ≥ 0.5 mm, and its effect on the D34 latch's Z-ranges

### 4.1 New constants

```openscad
MCC_RAIL_ROOF_CLR = 0.5; // mm. REQUIRED minimum clearance between the male taper's own top (root)
                          // and the female cut's own ceiling -- Christopher's "minimum 0.5 mm in
                          // this connection" applies to every non-bearing surface, not just the
                          // flanks (2026-09-28 user decision, overriding rev 1's "0 mm is fine"
                          // call). The ONLY bearing surface in this joint is the flat case-floor-on-
                          // bracket-plate seat (§1) -- the dovetail's own flanks and roof are both
                          // clearance surfaces now.
MCC_RAIL_MALE_H = MCC_RAIL_DEPTH - MCC_RAIL_ROOF_CLR; // = 3.5. The male taper's ACTUAL built
                          // height -- shorter than the female's own full MCC_RAIL_DEPTH cut by
                          // exactly the roof clearance, so the male's own top never reaches the
                          // female's ceiling. This is the male's real, total height off the
                          // bracket's flat top face now that the pedestal (§1) is also gone.
```

### 4.2 `_mcc_rail_taper()` must take an optional height, so the male can stop short without changing slope

Naively passing a shorter `h` to the existing `_mcc_rail_taper(len, clr, h=DEPTH)`-shaped call while
keeping `size2` pinned to `MCC_RAIL_ROOT_W` would **steepen** the taper (reach full root width over a
shorter rise) — wrong. Generalise the function to compute its own top width from the taper's real
slope at whatever height it is asked for, so every existing caller (the female cut, always at the full
`MCC_RAIL_DEPTH`) is numerically unaffected, and only the male's own call needs a new argument:

```openscad
// lib/mcc/rail.scad -- _mcc_rail_taper(), generalised (was: fixed h = MCC_RAIL_DEPTH, size2 pinned
// to MCC_RAIL_ROOT_W). _mcc_rail_flank_k() (already defined lower in this file for the latch) is the
// taper's own Y-growth-per-mm-of-Z; forward reference is fine in OpenSCAD (whole-file scope).
module _mcc_rail_taper(len, clr = 0, h = MCC_RAIL_DEPTH) {
    w_top = MCC_RAIL_MOUTH_W + 2 * h * _mcc_rail_flank_k(); // == MCC_RAIL_ROOT_W exactly when h ==
                                                              // MCC_RAIL_DEPTH -- every existing
                                                              // caller is bit-for-bit unchanged.
    prismoid(
        size1 = [len, MCC_RAIL_MOUTH_W + 2 * clr],
        size2 = [len, w_top + 2 * clr],
        h = h, anchor = BOTTOM
    );
}
```
(Consider moving `_mcc_rail_flank_k()`'s definition above `_mcc_rail_taper()` for readability while
this file is being edited anyway — not required, OpenSCAD resolves it either way.)

### 4.3 The male's own call: `_mcc_rail_taper(len, h = MCC_RAIL_MALE_H)` — everything else keeps `MCC_RAIL_DEPTH`

In `mcc_rail_male()`, the core taper call (§1.1's pedestal-removal edit) becomes:
```
_mcc_rail_taper(len, h = MCC_RAIL_MALE_H);
```
`mcc_rail_female_cut()`'s own cut call is **unchanged** — it still cuts to the full `MCC_RAIL_DEPTH`
(the extra `MCC_RAIL_ROOF_CLR` of void above the male's shortened top is exactly the roof gap being
asked for).

### 4.4 The nub must be capped at `MCC_RAIL_MALE_H`, or it becomes a disconnected sliver

The nub is a separate additive feature swept along the flank (`_mcc_rail_flank_extrude`), independent
of the core taper's own extent — if it is still told to run to `MCC_RAIL_DEPTH` after the core stops at
`MCC_RAIL_MALE_H`, its top `MCC_RAIL_ROOF_CLR`-tall slice has no core material left to attach to (a
disconnected sliver — a manifold defect, not merely a clearance question). Fix:

- `mcc_rail_male()`'s nub extrude call: `_mcc_rail_flank_extrude(MCC_FLOOR_T, MCC_RAIL_SILL_H)` (the
  pre-rev-1 original) becomes **`_mcc_rail_flank_extrude(0, MCC_RAIL_MALE_H)`** (not `MCC_RAIL_DEPTH`
  — must match the core's own real top).
- `mcc_rail_male()`'s arm-freeing cut extrude: may safely stay generous
  (`_mcc_rail_flank_extrude(-plate_t - 1, MCC_RAIL_DEPTH + 1)`) — over-cutting into air above
  `MCC_RAIL_MALE_H` where there is no material anyway is harmless, unlike under-cutting.
- `mcc_rail_female_cut()`'s notch: recommend capping it to match, `_mcc_rail_flank_extrude(-MCC_EPS,
  MCC_RAIL_MALE_H)` (not `MCC_RAIL_DEPTH`) — not strictly required (an over-sized pocket is harmless,
  the ramps that do the actual catching are unaffected by extra headroom above the nub), but keeps the
  pocket's own extent honestly matching what it receives.
- The latch-height assert (§1.1 point 4): use `MCC_RAIL_MALE_H`, not `MCC_RAIL_DEPTH`:
  `assert(MCC_RAIL_MALE_H + plate_t >= 5, ...)`. Sanity-checked: `tv-bracket` (`plate_t=6`) → 9.5≥5 ✓;
  `arch-tv-bracket` centre (`plate_t=11`, §5) → 14.5≥5 ✓; `rail-latch` coupon (`plate_t≈3`) → 6.5≥5 ✓.

### 4.5 Nothing else about the D34 latch changes

Arm length/thickness, engagement, ramp angles, `MCC_SNAP_STRAIN_MAX`, the slot/fillet asserts — none
reference `MCC_RAIL_DEPTH`/`MALE_H` except the one height assert just fixed. Re-verify by rendering
after the edit (five-second check, not an assumption): the same conclusion as rev 1's §5, now also
covering the roof-clearance edit, not just the pedestal removal.

---

## 5. Cross-cutting: both existing brackets, and the new vertical bracket

### 5.1 `models/brackets/arch-tv-bracket.scad`

Two independent breaks, both must be fixed (both already identified in rev 1; renumbered here with the
`MALE_H` correction folded in):

1. **Sweep condition loses the 3 mm standoff.** `T1-51`'s formula (`z_rail + MCC_FLOOR_T − arm_top_z
   ≥ ARCH_SWEEP_CLR`) must drop `MCC_FLOOR_T` (the case floor now rides at `z_rail`, not `z_rail +
   MCC_FLOOR_T`, during the slide). Re-solved: `ARCH_PLATE_T ≥ RIB_H + ARCH_SWEEP_CLR = 11`. Edit
   `ARCH_PLATE_T = 8.0` → `11.0`; edit the assert formula (drop `+ MCC_FLOOR_T`); edit the mate
   transform (line 665, drop `+ MCC_FLOOR_T`); update the header Z-stack table (`Z_RAIL=22,
   ARM_TOP_Z=20, case floor Z=22 [not "+MCC_FLOOR_T"], lid top=73`).
2. **`CENTRE_W=40` no longer contains the wider rail keep-out.** `RAIL_KEEPOUT_Y[1] =
   MCC_RAIL_ROOT_W/2 + MCC_RAIL_LATCH_ARM_T + MCC_RAIL_LATCH_ENGAGE = 32.5+1.6+2.0 = 36.1`, against
   `CENTRE_W/2 = 20` — **fails by 16.1 mm** (worse than rev 1's 3.4 mm, because the width grew from
   39.62 to 65). Required minimum: `CENTRE_W ≥ 2×36.1 = 72.2`. Recommend **`CENTRE_W = 78.0`**
   (~2.9 mm margin over the minimum). Re-run the file's own numeric sweep (`T1-47` bbox, `T1-54`,
   `T1-55`, `T1-59`) across the full `TV_TOP_CLEAR` range after the edit — do not hand-derive these
   further, they are already coded as loud asserts.
3. **`centre_z_max`'s formula was already slightly wrong after rev 1 and must be fixed now regardless:**
   it reads `ARCH_PLATE_T + MCC_RAIL_SILL_H + MCC_RAIL_END_STOP_H` — `MCC_RAIL_SILL_H` (7.0) was never
   the male's own height (that was established in rev 1 §1, missed in rev 1's own arch-bracket edit).
   Correct formula: `ARCH_PLATE_T + MCC_RAIL_MALE_H + MCC_RAIL_END_STOP_H` = `11 + 3.5 + 0 = 14.5`.
   Delete the stale "plus the end-stop's own extra rise" comment clause (`MCC_RAIL_END_STOP_H` is `0`
   since D34 — there is no end-stop flange any more).

### 5.2 `models/brackets/tv-bracket.scad`

Mate-transform fix per §1.2. Its own VESA-hole-vs-rail assert (`abs(h[1]) - h[2]/2 >
MCC_RAIL_ROOT_W/2 + MCC_EPS`, holes at `Y=±50/±100`) still passes trivially at the new
`ROOT_W/2 = 32.5` (was checked against 7.31 pre-rev-1). `PLATE_SIZE = 230` needs no change — the new
71 mm-wide sill band is nowhere close to that budget. Render and confirm as part of §7, do not skip it
on the assumption it's fine.

### 5.3 The new vertical bracket (`…\scratchpad\plans\D-vesa-400x300-bracket.md`)

Read in full. Its centre plate is `2*C_HALF × CENTRE_H = 180 × 90`, where `CENTRE_H=90` was sized for
its own **arm-tab geometry** (`2*(YJ_V+ARM_W/2) = 2*(25+20) = 90`), not for the rail — unlike the arch
bracket, the rail was never the binding dimension here even at the old width. Checking the same
keep-out formula that plan's own B7 uses (`RAIL_KEEPOUT_Y` inside `±CENTRE_H/2`): at the new
`ROOT_W=65`, `RAIL_KEEPOUT_Y[1] = 32.5+1.6+2.0 = 36.1`, against `CENTRE_H/2 = 45` — **fits with 8.9 mm
to spare. `CENTRE_H` does not need to grow for this width.** Flag for that plan's own implementer/
architect: its **B8** (M3 counterbore vs. rail keep-out gap, computed as "11.0 mm clear" at the old
14.6 mm width) **will shrink** at the new 65 mm width and must be re-verified against that file's own
joint-position constants (`YJ_V`, `JOINT_S`/`JOINT_P`) — this plan does not have that file's exact tab
coordinates memorised well enough to re-derive B8 by hand and does not attempt to; it is that plan's
own numeric sweep to re-run once `MCC_RAIL_ROOT_W` changes underneath it. Note also (informational,
not this plan's problem to fix): that plan's own file records the topology as "user-confirmed" but
separately describes a single-column 2-screw direct mount, whereas the teamlead's relay describes a
4-screw sandwiched mount with longer M8 bolts — these read as different mounting concepts; flag the
discrepancy for that plan's own owner rather than silently reconciling it here.

---

## 6. LOCK — pending DP48 analysis (placeholder, do not design)

**Do not implement a lock mechanism in this pass.** This section states only the space available and
the constraints any lock design must meet; the teamlead will resume this plan with the DP48 STEP-file
analysis to complete it.

**Space available on the male rail (bracket side):**
- Y: the **+Y flank is entirely free** (the D34 latch occupies only the −Y flank). The −Y flank is
  free everywhere **except** roughly the last `MCC_RAIL_LATCH_ARM_L` (18 mm) of X near the open (+X)
  end, where the latch's arm/nub/window already live.
- X: the full working length (`MCC_RAIL_LEN = 150 mm`) minus whatever the latch claims near +X (see
  above) and minus a few mm of lead-in/lead-out at each end for the taper's own asserts. The closed
  (−X) end and its adjacent ~130 mm of flank are entirely unclaimed by D34.
- Z: on the rail's own surface, `0` to `MCC_RAIL_MALE_H` (3.5 mm) if the lock is a rail-surface
  feature; if it is instead a case-floor feature (like the latch's own window/pocket), the fuller
  case-side sill depth (`0` to `MCC_RAIL_SILL_H = 7 mm`) is available, with the same `≥ MCC_FLOOR_T`
  residual-floor rule (T1-38) applying above it.

**What D34 already occupies, precisely** (so a lock design doesn't have to re-derive it): the −Y flank
near +X, `_mcc_rail_latch_geom()`'s `[x0, x1]` window (nub centred at `len/2 − MCC_RAIL_LATCH_LEAD_IN
= 55` from the open end, spanning `MCC_RAIL_LATCH_ARM_L=18` mm back toward −X), `MCC_RAIL_LATCH_ARM_T
=1.6` mm of flank-parallel thickness, plus `mcc_rail_male_window()`'s own matching cut through
whichever consumer plate the rail sits on.

**Constraints any lock must meet, gathered from this ticket's own decisions so far:**
- Tool-less per point 1 of this revision (no thumbscrews) — but a lock, unlike the D34 latch, may
  reasonably require a **deliberate** user action to release (that is the point of a lock vs. a snap
  latch) — confirm with the user whether "no thumbscrews" also rules out a key/lever/pin actuator, or
  only rules out a *screwed* fastener.
- Must not intrude on either clearance requirement in §4/rev-1-§2 (≥0.5 mm normal-to-flank, ≥0.5 mm at
  the roof) — a lock feature that bears directly (zero clearance) against the mating half by design
  would need its own explicit justification as the joint's *second* bearing surface, since §4.1
  states there is exactly one (the flat floor/plate seat) today.
- Must coexist with `mcc_rail_male_window()`'s own plate cut wherever the two are near each other in
  X — do not let a lock's own case-floor feature open into the same plate window the latch's arm leg
  already uses, or the two will interfere structurally.
- Must satisfy this repo's printability rules (no unsupported span > 3 mm cantilever / floating
  region per `.claude/knowledge/bambu-slicer.md`) in whichever print pose the case floor / bracket
  plate already print in — do not assume a new pose may be introduced for the lock alone.
- Must be reachable/operable once the case is fully mounted on the bracket (same "installer expects to
  operate it without removing the lid" constraint the D34 latch already satisfies) unless the DP48
  reference design itself implies otherwise (to be confirmed once that analysis lands).

---

## 7. Mated-intersection smoke test, tests/goldens, ordered steps, verification commands

### 7.1 Smoke test (unchanged approach from rev 1, values updated)

Extend `tests/test_rail.scad` (do not create a new file) with the same
`_mcc_rail_mate_check(len)` pattern rev 1 specified: a solid case-floor stock with the groove cut
(using `mcc_rail_female_cut()`), intersected with a bare `mcc_rail_male()` at flush (identity, Z=0)
placement — must render empty. Add a second numeric assert for the roof clearance, alongside the
existing flank-clearance assert:
```openscad
assert(MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE) >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("mcc: rail normal flank clearance=", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
        " below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_ROOF_CLR >= 0.5 - MCC_EPS,
    str("mcc: rail roof clearance=", MCC_RAIL_ROOF_CLR, " below the required 0.5 mm"));
```
Wire the zero-facet/zero-volume check into `scripts/build.py`'s `cmd_smoke` exactly as rev 1 specified
(§6 there): render the mate-check group to its own throwaway STL with `--summary all`, assert
`facets == 0` in the Python driver.

**`MCC_RAIL_MATE_CLR`/`MCC_RAIL_CLR_HORIZ`** (flank clearance constants) are unchanged from rev 1 —
`0.5` mm normal, `0.5/sin(60°) = 0.57735` mm horizontal, used in `mcc_rail_female_cut()`'s `clr =
MCC_RAIL_CLR_HORIZ;` line in place of `MCC_CLR_SLIDE`. Not repeated in full here; see rev 1's own §2 if
a from-scratch reading is needed — the derivation and the "which 0.5 mm" caveat are unchanged.

### 7.2 Goldens

All 8 SKUs' `base` golden move (sill/passage footprint, now centred differently and much wider); both
existing bracket goldens move (`tv-bracket.json`: pedestal-free, wider rail; `arch-tv-bracket.{arm,
centre}.json`: taller plate, wider centre); `coupons/rail-latch.json` moves. **The vertical bracket's
own goldens are that plan's responsibility, not this one's** — this plan only states the keep-out
finding in §5.3 for that plan's implementer to act on.

### 7.3 Ordered implementation steps

1. `lib/mcc/constants.scad`: delete `MCC_CASE_INSERT_KEEPOUT_D`, `MCC_FISHTAIL_BAND` (§2.1, after the
   grep check); add `MCC_RAIL_MATE_CLR`, `MCC_RAIL_CLR_HORIZ`, `MCC_RAIL_ROOF_CLR`, `MCC_RAIL_MALE_H`;
   flip the mouth/root relationship — `MCC_RAIL_ROOT_W = 65.0` (was derived, now primary),
   `MCC_RAIL_MOUTH_W` becomes the derived line (§3.2); `MCC_RAIL_Y = -23.5` (was −20.0).
2. `lib/mcc/layout.scad`: delete the two rows + the `floor_center` local (§2.1).
3. `lib/mcc/mounts.scad`: simplify `mcc_assert_floor_keepout_no_overlap()`'s now-dead exemption clause
   away (§2.1).
4. `lib/mcc/cradle.scad`: add the `tripod_insert`/`rail` mutual-exclusion assert (§2.2).
5. `lib/mcc/rail.scad`: generalise `_mcc_rail_taper()` (§4.2); pedestal removal + `MCC_RAIL_MALE_H`
   core-taper call + nub-extrude cap + latch-height assert fix (§1.1, §4.3, §4.4); female notch
   translate removal (§1.1 point 3); header rewrite.
6. Render `tests/test_rail.scad` — confirm the pre-existing D16/T1-38 checks still pass at the new
   constants (with the two retired rows gone from the list they iterate).
7. `models/brackets/tv-bracket.scad`: mate-transform fix (§1.2/§5.2).
8. `models/brackets/arch-tv-bracket.scad`: `ARCH_PLATE_T→11`, `CENTRE_W→78`, T1-51 formula, mate
   transform, `centre_z_max` formula, header Z-stack table (§5.1).
9. Add §7.1's mate-check block + roof-clearance assert to `tests/test_rail.scad`; wire `cmd_smoke`'s
   facets-== 0 check in `scripts/build.py`.
10. `python scripts/build.py smoke` — must pass.
11. `python scripts/build.py render --all` — exercises every affected assert, including the arch
    bracket's own `TV_TOP_CLEAR` sweep and `tv-bracket.scad`'s VESA-vs-rail check.
12. `python scripts/build.py check --all`.
13. `python scripts/build.py golden --update` (targeted: all 8 `<slug>.base.json`,
    `brackets/tv-bracket.json`, `brackets/arch-tv-bracket.{arm,centre}.json`,
    `coupons/rail-latch.json`) — review each diff against §7.2 before committing.
14. `python scripts/build.py slicer-check` — zero-warning gate; pay particular attention to the wider
    sill/passage and the taller, wider arch-bracket centre plate for any new bridging/cantilever
    finding (`.claude/knowledge/bambu-slicer.md`'s `scripts/slicer_probe.py zbisect|box|critical` is
    the fast path if one shows up).
15. `python scripts/build.py all` (full gate) before opening the PR.
16. Update `BOM.md` if any row cites the old `MCC_RAIL_ROOT_W`/`MOUTH_W` values by number.
17. Hand the CLAUDE.md text (§2.3) and the architecture.md recording list (§2.4) to the teamlead/
    architect — this plan does not edit either file itself.
18. **Do not open a PR that includes a lock mechanism** — §6 is explicitly incomplete pending the
    DP48 analysis; this plan's own scope ends at item 15's gate.

### 7.4 Verification commands (repo root, `OPENSCADPATH=lib`)

```
python scripts/build.py smoke
python scripts/build.py render --all
python scripts/build.py check --all
python scripts/build.py golden --update
python scripts/build.py slicer-check
python scripts/build.py all
```

---

## 8. Open questions for the user (carried over / updated from rev 1)

1. **Roof-clearance interpretation confirmed by this revision** (≥0.5 mm, not 0) — no longer open.
2. **"No thumbscrews" and the lock's actuator.** §6 flags this: does "tool-less, no thumbscrews" also
   rule out a key/lever/captive-pin lock actuator, or only a screwed fastener? Affects what DP48's
   mechanism can be adapted into.
3. **`ARCH_PLATE_T=11`/`CENTRE_W=78` and the vertical bracket's own re-verification (§5.3, B8)** — both
   are physical consequences of the requested width/placement, not independent choices; flagged for
   awareness, not a decision needed to proceed.
4. **The vertical-bracket plan's mounting-concept discrepancy** (§5.3, single-column 2-screw vs.
   sandwiched 4-screw) — not this plan's to resolve; flag to that plan's owner.
5. **Full retirement vs. assert-guard for `cfg["tripod_insert"]`** (§2.2) — this plan recommends the
   assert-guard; confirm or override before the architect records the decision.

## Architect verdict

# Architect verdict — Plan A (rev 2): wide, flush dovetail

> **Amended 2026-09-28 — read Amendments 1 and 2 at the end first.** Amendment 1 retires `tv-bracket` inside this PR, voids B8 and D.2, and replaces several Appendix E/G texts. Amendment 2 corrects R41's flank; its AM2-1 (coupon strips) is **withdrawn** — see the note at its end. A ships inside plan F's PR.

Gate: `solution-architect`, 2026-09-28. Plan: `scratchpad/plans/A-wide-dovetail.md`.
Checked against:
- `main` @ 047902e, **plus plan C as amended by its verdict** (A is implemented stacked on C);
- `.claude/knowledge/architecture.md` (source of truth) and `CLAUDE.md`.

IDs assigned here come after C's (D40–D43, R39, M19, Q20, T1-61):
- **rev 16**;
- **D44–D47**;
- **T1-62, T1-63**;
- **R40, R41**, plus **R42, R43** for the plan-D gate, recorded here because D has no branch yet;
- **Q21**, plus **Q22** for plan D;
- **M20** for plan D. M7 is retired and M15 is rewritten.

## Verdict: **APPROVED WITH BINDING CHANGES** (B1–B17; B1, B2 and B7 are blocking as written)

The direction is sound and matches every user decision of 2026-09-28:
- dovetail kept, root 65 mm, `MCC_RAIL_Y` = −23.5;
- pedestal removed, so the case floor sits flush;
- ≥ 0.5 mm clearance on the flanks and roof;
- Fishtail and case-insert reservations retired;
- D34 latch kept as the lock.

I re-derived the placement independently. 65 / −23.5 is valid:
- The binding neighbour is the side-bolt support web.
- The tightest SKU is **W = 158.80** (the BNC compact cases), not 159.85 as the plan says.
- There, the sill edge clears the web top (−62.4) by **3.4 mm**, and the keep-out row passes D16 with **4.4 mm** to spare.
- The maximum root at this Y is about 68.9 mm.

The plan's §6 lock section is treated as informational, as instructed.

As written, though, the plan breaks the latch, violates the user's own roof clearance in two places, fails four arch-bracket asserts, and proposes an unimplementable mate test.

### What I found, beyond what the plan checked

1. **The latch fuses to the plate (blocking).**
   - With the pedestal gone, the nub starts at the plate top (z = 0).
   - `mcc_rail_male_window()` only opens `MCC_RAIL_LATCH_WINDOW_CLR` (0.6 mm) around the arm band, but the nub protrudes `MCC_RAIL_LATCH_ENGAGE` (2.0 mm).
   - The nub's outer 1.4 mm would therefore union straight onto the solid plate: the arm cannot flex and the case cannot be slid on.
   - In D34 the nub floated 3 mm above the plate, so plan A's "§4.5 nothing else about the D34 latch changes" is wrong.
2. **Two roof-clearance violations.**
   - Capping the female notch at `MCC_RAIL_MALE_H` (plan §4.4) puts the nub's top face in 0 mm contact with the notch roof.
   - `mcc_rail_female_cut()` shifts its taper down by `MCC_EPS` on top of `_mcc_rail_taper_eps()`'s own pierce slab, so the real groove roof sits at `DEPTH − 0.01` and the roof gap is **0.49 mm**.
3. **The arch cascade fails its own asserts (blocking).**
   - **T1-60 (UP arrow) fails at `CENTRE_W` = 78.** The band between the rail keep-out top (36.1) and the body edge (39) is 2.9 mm; the 6 mm arrow plus 2 × 1 mm needs 8. The minimum is 88.2.
   - **T1-57 fails at `ARCH_PLATE_T` = 11 with M3×10.** Engagement is 2.3 mm against 4.5 required.
   - **T1-55 passes at `TV_TOP_CLEAR` = 184.9 only on the assert's 0.01 mm tolerance** (gap 0.994 against 1.0). The widened body puts the rib end's outer corner (y ≈ −25.3) inside its Y band, so the X gap alone governs.
   - The preview variant sets `tripod_insert = true`, which the new T1-63 rejects.
   - The plan's "do not hand-derive, they are loud asserts" would leave a developer stuck at render time.
4. **The mate "smoke test" cannot work as described.**
   - `build.py smoke` exports CSG, which never evaluates whether an `intersection()` is empty.
   - The wiring is "exactly as rev 1 specified", and rev 1 no longer exists.
   - A synthetic block also tests only the cross-section, not the case's real frames.
   - D34 already ships the right tool: `scripts/rail_fit.py`, a virtual insertion sweep against a real rendered base. It hardcodes `RAIL_Y = −20`, a −`MCC_FLOOR_T` pedestal shift and a roof clip that assumed male-to-roof contact.
5. **The rail-latch coupon cannot be tested (D46).**
   - Its groove plinth is fused on the shared base plate with the groove mouth facing that plate, so the groove is a sealed tunnel.
   - After D44 this coupon is the physical gate for the roof bridge, so it must work.
6. **The ~66 mm groove-roof bridge** (the base prints open-side-up) breaks §5's 10 mm span rule, forced by the width decision. It is recorded as a sanctioned exception with a physical gate (R40).
7. **Missed consumers:**
   - `tests/test_layout.scad:94` asserts the `case_tripod_insert` row exists;
   - `arch-tv-bracket.scad:661` sets the preview's `tripod_insert` to true;
   - `scripts/rail_fit.py`;
   - the BOM Fishtail note (`BOM.md:66`);
   - the BOM adhesive-feet row (`BOM.md:67`): feet would stand the floor off the plate;
   - the base_fan golden;
   - the coupons-README rail-latch rows;
   - stale comments in `shell.scad`, `cradle.scad`, `mounts.scad` and `layout.scad`.
8. **Pre-existing, recorded, not fixed here:**
   - **D45**: the sill's closed end sits 0.55–1.05 mm inside the compact splitter bay; R24's "9.6 mm" claim is wrong.
   - **D47**: the tv-bracket's case sits on the same face as the VESA mount it is sandwiched to.

## Rulings on the plan's open points

- **`cfg["tripod_insert"]`: assert-guard, not full retirement.** D35 explicitly kept the option. The new assert is **T1-63** in `mcc_cradle()`.
- **CLAUDE.md**: the plan's §2.3 text is superseded. The line is already current up to D35. Use Appendix E4.
- **§6 LOCK**: not implemented. **Q21** records the DP48 question.
- **The axial end stop stays a contact face.** The groove's closed −X end is the D34 end stop, so at full mate the rail's −X face touches it; `rail_fit.py` asserts exactly that. My reading is that the user's "≥ 0.5 mm on every non-bearing surface — flanks and roof" rule is about the cross-section. The end stop constrains X, which the floor seat does not, so it is a stop, not a seat. If the user wants clearance there too, only the latch would locate X (with 0.58 mm of play). I did not assume that; it is listed under Q21 because the DP48 lock may define X differently anyway.

## Binding changes

**B1 — BLOCKING. The latch window must clear the nub.** Use Appendix B.4 verbatim:
- `mcc_rail_male_window()` adds `_mcc_rail_nub_2d(g)` to the union it offsets.
- It clips the window in Y to the nub, arm and slot band (`y0 − e − c … y0 + t + s + c`). The old ±50 clip let the tip-gap strip, which reaches 2·DEPTH past the flank, cut 40.8 mm out from the rail axis — through the edge of a narrow consumer plate.

**B2 — BLOCKING. Keep ≥ 0.5 mm over the nub and at the roof.**
- The female notch spans the **full** groove depth: `_mcc_rail_flank_extrude(-MCC_EPS, MCC_RAIL_DEPTH)`, not `MCC_RAIL_MALE_H`.
- Remove the extra `-MCC_EPS` Z-shift in `mcc_rail_female_cut()`.
- Appendix B.6.

**B3 — Latch internals (Appendix B.5):**
- The arm's leg overlaps into the arm by `20 * MCC_EPS`, not `MCC_FLOOR_T / 2` (a case constant, meaningless without a pedestal; 1.5 mm into the sheared arm also eats slot clearance).
- The slot-deflection assert uses `MCC_RAIL_CLR_HORIZ`, the female clearance, instead of `MCC_CLR_SLIDE`.
- The latch-height assert uses `MCC_RAIL_MALE_H`, as the plan says, but only when a plate is present (`plate_t == 0 || …`). As the plan wrote it, 3.5 + 0 < 5 fails the bare-rail probe calls: `tests/test_rail.scad` (`mcc_rail_male()`, `mcc_rail_male(len = 60)`) and `scripts/rail_fit.py`.

**B4 — Constants: Appendix A verbatim.** It supersedes plan §3.2/§4.1/§7.3 step 1:
- `MCC_RAIL_ROOT_W = 65.0` becomes primary, with the mouth derived;
- `MCC_RAIL_Y = -23.5` with a corrected derivation comment;
- `MCC_RAIL_MATE_CLR`, `MCC_RAIL_CLR_HORIZ`, `MCC_RAIL_ROOF_CLR` and `MCC_RAIL_MALE_H` are added;
- the "reuse `MCC_CLR_SLIDE`" rule is rewritten, since 0.3 mm horizontal is only 0.26 mm normal;
- `MCC_CASE_INSERT_KEEPOUT_D` and `MCC_FISHTAIL_BAND` are deleted.

**B5 — rail.scad: Appendix B verbatim.** It covers:
- the header;
- `_mcc_rail_taper(h=)` as the plan specifies;
- `_mcc_rail_flank_extrude` with `zb = 0`;
- the window (B1);
- `mcc_rail_male()` (B3);
- `mcc_rail_female_cut()` (B2, plus the T1-62 asserts).

**B6 — Keep-out retirement (Appendix C):**
- `layout.scad`: rows, `floor_center` and the doc.
- `mounts.scad`: the exemption removed, plus the header and doc.
- `cradle.scad`: the **T1-63** assert, plus stale comments; `tests/test_shell.scad`: two stale D-16 comments (C.3b).
- `shell.scad`: comment.
- `tests/test_layout.scad:94`: invert it.
- `tests/test_rail.scad`: header, T1-62 checks, manual checks.

**B7 — BLOCKING. Arch cascade corrected: Appendix D.1.**
- `ARCH_PLATE_T = 11.0` (plan, ✓).
- `CENTRE_W = 92.0`, not 78 (T1-60).
- `LAP_RIB_GAP = 3.0` (T1-55 margin becomes 2.3 mm).
- New `M3_COUNTERBORE_DEPTH = M3_HEAD_K + 1.3` and `M3_JOINT_SCREW_L = 12` (T1-57: tip 5.7, engagement 5.3, bore-floor margin 0.9).
- T1-51 and the mate transform drop `MCC_FLOOR_T`.
- `centre_z_max` uses `MCC_RAIL_MALE_H`.
- The preview uses `["tripod_insert", false]`.
- Header Z-stack and prose updated.
- `tests/test_arch_tv_bracket.scad`: the first value is 69.7, and the manual-check bound is 69.675.

**B8 — tv-bracket (Appendix D.2):**
- mate transform `translate([0, MCC_RAIL_Y, 0])`;
- the bbox assert uses `MCC_RAIL_MALE_H`;
- header, derivation and inline comments rewritten.

**B9 — rail-latch coupon fix (D46): Appendix D.3 verbatim.** The groove half stands on the bed, groove open. Two snap-off strips beside the groove join the halves. The echo and header are updated.

**B10 — The mate check is `scripts/rail_fit.py`, updated per Appendix D.4.**
- It reads `MCC_RAIL_Y` from constants, applies no Z-shift (male frame = female frame) and no roof clip (the roof is now a clearance).
- Run it for `pro-convert-for-ndi-to-hdmi`, `pro-convert-sdi-tx` (W = 158.80) and `pro-convert-hdmi-plus`. Each must print `rail fit OK`.
- Do **not** implement plan §7.1's synthetic intersection in `test_rail.scad` or its `cmd_smoke` facets==0 wiring. The numeric T1-62 checks do go into `test_rail.scad`.

**B11 — Goldens.**
- Update exactly: `coupons/rail-latch`, `brackets/tv-bracket`, `brackets/arch-tv-bracket`, and the 8 SKUs (their base and lid goldens, plus the one base_fan golden).
- Run them as one targeted command (Appendix F step 11). **Never an untargeted `golden --update`** (plan §7.4 has one).
- `git diff --stat -- tests/golden/` may then show content changes **only** in:
  - the 8 `*.base.json`;
  - `pro-convert-for-ndi-to-hdmi.base_fan.json` (the plan forgot it);
  - `brackets/tv-bracket.json` and `brackets/arch-tv-bracket.{arm,centre}.json`;
  - `coupons/rail-latch.json`.
- Any `*.lid.json` or other change: **STOP**.
- Regenerate on top of C's goldens; never hand-merge golden JSON.

**B12 — Docs: Appendix E verbatim:**
- BOM:
  - the floor-mounting heading and its insert, rail and feet rows (feet: free-standing only);
  - arch M8 `pad_clamp_t` 10.0;
  - arch M3×12.
- `models/brackets/README.md`: the TV-back distance 22–73 mm, M3×12.
- `models/coupons/README.md`: rail-latch rows and form.
- CLAUDE.md: floor line and Current status.
- CHANGELOG.

**B13 — architecture.md and layout-patch-wall.md: Appendix G/H verbatim** on the feature branch; nothing else in those files. This replaces plan §2.4 and §7.3 step 17.

**B14 — Permanent record.**
- Create `docs/plans/2026-09-28-wide-dovetail.md` = plan A rev 2 verbatim.
- Directly under its title, add: `> **Implemented as amended by the architect verdict appended at the end of this file (B1–B17). Where they conflict, the verdict wins. §6 (lock) is informational only.**`
- Then append this file's full content under `## Architect verdict`.

**B15 — Stop conditions.** Stop and report, without improvising, if:
- `slicer-check` or `check` flags the groove roof, the passage or the +X wall notch on any base (R40);
- `rail_fit.py` fails;
- T1-63 fires anywhere except a deliberate manual check;
- any assert in the arch sweep fails after Appendix D.1;
- a golden moves outside B11's list.

**B16 — The lock stays D34.** Plan §6 is not implemented; it waits on the DP48 bodies (Q21).

**B17 — Sequencing.** Appendix F:
- A is stacked on C and merges after C.
- If C changes, rebase A and regenerate A's goldens.
- D is re-planned on top of A, never in parallel with a rail change.

## DO NOT

- Do not change the latch arm/nub dimensions (`MCC_RAIL_LATCH_ARM_L/_T/_ENGAGE/_SLOT/_RAMP_*`). Only the window, leg overlap, notch depth and asserts change.
- Do not move `MCC_RAIL_Y`, or set `MCC_RAIL_ROOT_W` outside 60–70 (user range), to answer a print or slicer finding. Stop and report.
- Do not "fix" a sagging roof by narrowing the rail. The lever is `MCC_RAIL_ROOF_CLR`, and only after M15.
- Do not change `MCC_CLR_SLIDE`: other fits still use it.
- Do not delete the tripod-insert boss/bore modules, their tests, T1-32/T1-41 or `MCC_INSERT_1_4_20` (assert-guard chosen).
- Do not implement plan §6 (lock), plan §7.1's `test_rail.scad` intersection, or the `cmd_smoke` facets wiring.
- Do not fix D45 (splitter overlap) or D47 (tv-bracket vs VESA mount) in this PR. Do not touch any vertical-bracket file.
- Do not run `golden --update` without explicit targets. Do not hand-edit golden JSON.
- Do not start before C's branch exists: A anchors on C's rev-15 text, D40–D43 rows, R39, M19, Q20, T1-61 and C's goldens.

---

## Appendix A — `lib/mcc/constants.scad`

**A.1** Two separate deletions; `MCC_STRAP_SLOT` sits between them and stays.
- Delete this one line:
```
MCC_CASE_INSERT_KEEPOUT_D = 20.0; // plan-view keep-out disc for the case's own 1/4"-20 insert, mm.
```
- Delete these two lines:
```
MCC_FISHTAIL_BAND = [60, 20];     // Magewell Fishtail M4 reservation band [x,y], mm — reserve-only,
                                    // hole pitch unknown (knowledge/magewell/accessories.md:26, M7).
```
Before deleting, check the consumers with a grep over `lib/`, `models/` and `tests/`:
- The only consumers may be `layout.scad`'s two rows (Appendix C.1) and the `MCC_RAIL_Y` comment replaced in A.3.
- If any other consumer shows up, stop.

**A.2** Replace the two definitions from `MCC_RAIL_MOUTH_W = 10.0;` through the end of the `MCC_RAIL_ROOT_W` comment (`// "formulas not magic numbers") = 10.0 + 2*4.0/tan(60) ~= 14.6188.`) with:
```openscad
MCC_RAIL_ROOT_W = 65.0;    // dovetail root width (wide end: deepest into the case floor / top of the
                            // bracket's male rail), mm. USER DECISION 2026-09-28 (architecture.md
                            // §13 D44): "much wider, intermediate, root 60-70 mm"; 65 validated at the
                            // gate (max ~68.9 at MCC_RAIL_Y below before the sill meets the side-bolt
                            // web). PRIMARY since D44 -- MOUTH_W is derived from it (was the reverse).
MCC_RAIL_MOUTH_W = MCC_RAIL_ROOT_W - 2 * MCC_RAIL_DEPTH / tan(MCC_RAIL_FLANK_ANGLE);
                            // dovetail mouth width (narrow end: the case's exterior floor face / the
                            // bracket plate top), mm. DERIVED = 65.0 - 4.6188 = 60.3812.
```

**A.3** Replace the block from `// R2 (blocking, layout-patch-wall.md §17.2/§11 R24): NEGATIVE, not +20.0 — the plan's own derivation` through `MCC_RAIL_Y = -20.0;` with:
```openscad
// Rail Y (D44, 2026-09-28 -- supersedes rev 9's R2 value -20.0). As close to the device's own centre
// of mass (y_dev_c = -30.825 on every HDMI-ended SKU, ~0.5 mm less negative on the BNC-ended ones) as
// the 65 mm root allows. Binding neighbour: the side-bolt support web's floor footprint. On the
// tightest SKU (W = 158.80) the sill's -Y edge (MCC_RAIL_Y - MCC_RAIL_ROOT_W/2 - MCC_RAIL_SILL_SIDE_W =
// -59.0) stays 3.4 mm clear of the web top (-62.4), and the groove's "mount_rail" keep-out row clears
// it by 4.4 mm beyond MCC_FLOOR_FEATURE_EDGE_MIN (D16). Negative as before (R24): the rail sits under
// the device, so the case's mass stays on the rail band when the patch wall hangs down. The case-insert
// and Fishtail reservations that pinned the rail to |y| >= 19.31 are gone (D44).
MCC_RAIL_Y = -23.5;
```

**A.4** Replace the comment block that starts `// MCC_RAIL_CLR: deliberately NOT a new constant. Reuse MCC_CLR_SLIDE (0.3, above) for the` and ends `// only drift from the first (docs/plans/2026-09-09-mount-rail-and-brackets.md §1.1).` with:
```openscad
// Rail clearances (D44, user decision 2026-09-28, from the external specialist's review): at least
// 0.5 mm on EVERY non-bearing surface of the joint. The only designed bearing face is the case's flat
// exterior floor on the bracket plate (the male has no MCC_FLOOR_T pedestal any more); on a vertical,
// TV-mounted bracket the gravity-side flank also bears (architecture.md R41). These replace the
// rev-9 rule "reuse MCC_CLR_SLIDE for the rail": 0.3 mm horizontal at a 60 deg flank is only 0.26 mm
// normal to it -- below the requirement. MCC_CLR_SLIDE stays for every other sliding fit.
MCC_RAIL_MATE_CLR = 0.5;    // minimum clearance on every non-bearing rail face, mm. User decision (D44).
MCC_RAIL_CLR_HORIZ = MCC_RAIL_MATE_CLR / sin(MCC_RAIL_FLANK_ANGLE); // = 0.5774. Per-side horizontal
                            // offset of the female groove and latch notch from the male profile that
                            // gives MCC_RAIL_MATE_CLR normal to a MCC_RAIL_FLANK_ANGLE flank (T1-62).
MCC_RAIL_ROOF_CLR = MCC_RAIL_MATE_CLR; // = 0.5. Gap between the male's flat top (and the nub's) and
                            // the groove roof, mm. Its own constant on purpose: the roof is a ~66 mm
                            // bridge in the base's print pose (architecture.md R40) -- if the rail-latch
                            // coupon (M15) shows it sags into this gap, raise THIS; never narrow the rail.
MCC_RAIL_MALE_H = MCC_RAIL_DEPTH - MCC_RAIL_ROOF_CLR; // = 3.5. The male taper's built height above the
                            // bracket plate (no pedestal since D44).
```

**A.5** In the `MCC_RAIL_LATCH_WINDOW_CLR` comment:
- Old: `// clearance of the bracket-plate window around the arm leg and`
- New: `// clearance of the bracket-plate window around the arm leg, nub and`

## Appendix B — `lib/mcc/rail.scad`

**B.1 Header.** Replace the comment lines from `// Cross-section: a standard dovetail, narrow (MCC_RAIL_MOUTH_W) at the mating surface — Z=0 for` through `// pedestal's top and the taper exactly fills the case's own groove.` with:
```
// Cross-section: a standard dovetail, narrow (MCC_RAIL_MOUTH_W) at the mating surface -- local Z=0
// on BOTH halves (D44, 2026-09-28: the male has no pedestal any more; male-local = female-local,
// Z included) -- widening to MCC_RAIL_ROOT_W at Z=MCC_RAIL_DEPTH, the groove roof. WIDE material sits
// DEEPER inside the groove, so the case cannot be lifted straight off the bracket; only sliding along
// X clears the interlock. At full mate the case's flat exterior floor rests FLUSH on the bracket
// plate everywhere outside the two footprints -- the joint's only designed bearing face. The male
// stands MCC_RAIL_MALE_H tall (MCC_RAIL_ROOF_CLR short of the roof) and the groove is offset
// MCC_RAIL_CLR_HORIZ per side, so every other face has >= MCC_RAIL_MATE_CLR (T1-62).
```

**B.2 `_mcc_rail_taper()`.** Replace the whole module (doc + body, from `// Module: _mcc_rail_taper()` through its closing `}`) with:
```openscad
// Module: _mcc_rail_taper()
// Description:
//   Private. The dovetail taper alone (no latch): a prismoid from MCC_RAIL_MOUTH_W at local Z=0,
//   widening along the flank's own slope for `h` mm, length `len` along X, centred on Y=0, anchored
//   BOTTOM. The female groove uses the full MCC_RAIL_DEPTH (top width == MCC_RAIL_ROOT_W exactly);
//   the male stops at MCC_RAIL_MALE_H with the SAME slope (D44), so the two profiles can never drift.
// Arguments:
//   len = rail/groove length along the slide axis, mm.
//   clr = per-side horizontal clearance added to both widths, mm. Default 0 (the male). The female
//         groove passes MCC_RAIL_CLR_HORIZ (D44).
//   h   = height, mm. Default MCC_RAIL_DEPTH.
module _mcc_rail_taper(len, clr = 0, h = MCC_RAIL_DEPTH) {
    w_top = MCC_RAIL_MOUTH_W + 2 * h * _mcc_rail_flank_k();
    prismoid(
        size1 = [len, MCC_RAIL_MOUTH_W + 2 * clr],
        size2 = [len, w_top + 2 * clr],
        h = h, anchor = BOTTOM
    );
}
```

**B.3 `_mcc_rail_flank_extrude()`.**
- In `_mcc_rail_nub_2d()`'s doc, change `at the pedestal flank line` to `at the mouth flank line (plate top)`, and `MCC_CLR_SLIDE = the female notch` to `MCC_RAIL_CLR_HORIZ = the female notch`.
- In `_mcc_rail_flank_extrude()`, replace:
```
//   Private. Extrudes a plan-view 2-D child (drawn at the pedestal's flank line) over z0..z1 of the
//   MALE frame so it follows the -Y flank: straight up to MCC_FLOOR_T (pedestal), then sheared
//   outward with the dovetail taper above it. The same helper cuts the female notch (female z = male
//   z - MCC_FLOOR_T, handled by the caller's translate), so arm, slot, nub and notch stay parallel
//   to the flank by construction.
module _mcc_rail_flank_extrude(z0, z1) {
    zb = MCC_FLOOR_T;
```
with:
```
//   Private. Extrudes a plan-view 2-D child (drawn at the mouth flank line) over z0..z1 of the shared
//   frame so it follows the -Y flank: sheared outward with the dovetail taper above Z=0, straight
//   below it (only a leg or cut reaching DOWN into the consumer's plate is ever below Z=0 -- D44
//   removed the pedestal). The same helper cuts the female notch (male Z = female Z since D44), so
//   arm, slot, nub and notch stay parallel to the flank by construction.
module _mcc_rail_flank_extrude(z0, z1) {
    zb = 0;
```

**B.4 `mcc_rail_male_window()`.** Replace the whole module body (from `module mcc_rail_male_window(len = MCC_RAIL_LEN, plate_t) {` through its closing `}`) with:
```openscad
module mcc_rail_male_window(len = MCC_RAIL_LEN, plate_t) {
    if (MCC_RAIL_LATCH_ENABLED && plate_t > 0) {
        g = _mcc_rail_latch_geom(len);
        y0 = -MCC_RAIL_MOUTH_W / 2;
        c = MCC_RAIL_LATCH_WINDOW_CLR;
        e = MCC_RAIL_LATCH_ENGAGE;
        translate([0, 0, -plate_t - MCC_EPS])
            linear_extrude(height = plate_t + 2 * MCC_EPS)
                intersection() {
                    offset(delta = c) union() {
                        translate([g[2], y0]) square([g[3] - g[2], MCC_RAIL_LATCH_ARM_T]);
                        _mcc_rail_latch_cut_2d(g);
                        // D44: with no pedestal the nub starts AT the plate top -- the plate must be
                        // open under it too, or the nub fuses to the plate and the arm cannot flex.
                        _mcc_rail_nub_2d(g);
                    }
                    // Never past the root (the arm's leg must stay joined to the plate there), and
                    // never further out than the nub + clearance: the tip-gap cut reaches far past
                    // the flank for the SHEARED arm above the plate; at plate level only the leg and
                    // the nub need room.
                    translate([g[2] - 50, y0 - e - c])
                        square([g[3] - g[2] + 50, e + 2 * c + MCC_RAIL_LATCH_ARM_T + MCC_RAIL_LATCH_SLOT]);
                }
    }
}
```
Also change the module's doc line `//   coupon base): the window under the latch arm and its slot, through the plate's whole` to `//   coupon base): the window under the latch arm, its slot and its nub (D44), through the plate's whole`.

**B.5 `mcc_rail_male()`.** Replace the module's doc paragraph line `//   ADDITIVE. The male dovetail rail (bracket side): a MCC_FLOOR_T-tall pedestal (MCC_RAIL_MOUTH_W` and the next line `//   wide — the standoff under the case's exterior floor face) carrying the shared taper, over the` with:
```
//   ADDITIVE. The male dovetail rail (bracket side): the shared taper, MCC_RAIL_MALE_H tall, standing
//   directly on the consumer's plate (no pedestal since D44 -- the case floor rests flush on it), over the
```
Then replace everything from `    if (MCC_RAIL_LATCH_ENABLED) {` (the first line after `strain = …;`) through the module's closing `}` with:
```openscad
    if (MCC_RAIL_LATCH_ENABLED) {
        assert(L / t >= 8, str("mcc: rail latch L/t=", L / t, " below 8:1 (fasteners-and-hardware.md:133)"));
        assert(MCC_RAIL_LATCH_SLOT / 2 >= MCC_RAIL_LATCH_ROOT_FILLET - MCC_EPS,
            str("mcc: rail latch root radius ", MCC_RAIL_LATCH_SLOT / 2, " below the root fillet minimum"));
        assert(MCC_RAIL_LATCH_SLOT > e + MCC_EPS - MCC_RAIL_CLR_HORIZ,
            str("mcc: rail latch slot ", MCC_RAIL_LATCH_SLOT, " cannot absorb the nub's deflection"));
        assert(strain <= MCC_SNAP_STRAIN_MAX,
            str("mcc: rail latch tip strain ", strain, " exceeds MCC_SNAP_STRAIN_MAX ", MCC_SNAP_STRAIN_MAX));
        // The arm's printed height (bed to rail top) only exists with a consumer plate. plate_t = 0 is
        // the bare-rail probe call (tests/test_rail.scad, scripts/rail_fit.py): 3.5 mm there is not a
        // printed arm. (Before D44 the 3 mm pedestal made this pass vacuously at plate_t = 0.)
        assert(plate_t == 0 || MCC_RAIL_MALE_H + plate_t >= 5,
            str("mcc: rail latch arm height ", MCC_RAIL_MALE_H + plate_t, " below the 5 mm minimum clip width"));
        assert(g[2] - MCC_RAIL_LATCH_SLOT > -len / 2 + 5 && g[3] < len / 2 - 2,
            str("mcc: rail latch (", g, ") does not fit inside len=", len));
    }

    difference() {
        union() {
            // D44: no pedestal -- the taper stands directly on the consumer's plate (local Z=0),
            // MCC_RAIL_ROOF_CLR short of the groove roof.
            _mcc_rail_taper(len, h = MCC_RAIL_MALE_H);
            if (MCC_RAIL_LATCH_ENABLED)
                // Nub over the taper -- rides inside the groove. It starts at the plate top as a
                // 2 mm ledge off the arm, over mcc_rail_male_window()'s opening (which covers the nub
                // since D44), so it never fuses to the plate; it stops at the core's own top.
                _mcc_rail_flank_extrude(0, MCC_RAIL_MALE_H) _mcc_rail_nub_2d(g);
        }
        if (MCC_RAIL_LATCH_ENABLED)
            _mcc_rail_flank_extrude(-plate_t - 1, MCC_RAIL_DEPTH + 1) _mcc_rail_latch_cut_2d(g);
    }
    // The arm's leg through the consumer's plate window, down to the bed, drawn in its final plan
    // shape (arm band minus slot and tip gap). It runs MCC_RAIL_LATCH_WINDOW_CLR past the root into
    // the plate (the window stops at the root) and 20*MCC_EPS up into the arm's own lowest band -- a
    // shared volume for the union that leaves the slot's deflection room intact (D44; it used to run
    // MCC_FLOOR_T/2 up into the pedestal).
    if (MCC_RAIL_LATCH_ENABLED && plate_t > 0)
        translate([0, 0, -plate_t])
            linear_extrude(height = plate_t + 20 * MCC_EPS)
                difference() {
                    translate([g[2], -MCC_RAIL_MOUTH_W / 2])
                        square([g[3] - g[2] + MCC_RAIL_LATCH_WINDOW_CLR, t + MCC_RAIL_LATCH_SLOT]);
                    _mcc_rail_latch_cut_2d(g);
                }
}
```

**B.6 `mcc_rail_female_cut()`.**
1. In its doc comment:
   - replace `MCC_CLR_SLIDE per side for a sliding fit` with `MCC_RAIL_CLR_HORIZ per side (>= MCC_RAIL_MATE_CLR normal to the flanks, D44)`;
   - replace these two lines:
```
//   out through its +X wall. Plus the latch notch in the -Y flank (the nub's outline grown by
//   MCC_CLR_SLIDE, following the flank). Local frame: mouth at Z=0 = the case's exterior floor
```
   with:
```
//   out through its +X wall. Plus the latch notch in the -Y flank (the nub's outline grown by
//   MCC_RAIL_CLR_HORIZ, following the flank, over the groove's full depth). Local frame: mouth at
//   Z=0 = the case's exterior floor
```
2. Replace the module body from its first `assert(` through its closing `}` with:
```openscad
    assert(MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));
    // T1-62 (D44): >= MCC_RAIL_MATE_CLR on every non-bearing face -- normal to the flanks, and at the
    // roof over the male's (and the nub's) shortened top.
    assert(MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE) >= MCC_RAIL_MATE_CLR - MCC_EPS,
        str("mcc: T1-62 rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
            " mm normal, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    assert(MCC_RAIL_DEPTH - MCC_RAIL_MALE_H >= MCC_RAIL_MATE_CLR - MCC_EPS,
        str("mcc: T1-62 rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
            " mm, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    clr = MCC_RAIL_CLR_HORIZ;
    g = _mcc_rail_latch_geom(len);

    union() {
        // No Z shift: _mcc_rail_taper_eps() already pierces Z=0 with its own slab, so the groove roof
        // sits at exactly MCC_RAIL_DEPTH (the old extra -MCC_EPS shift lowered it by 0.01 mm).
        translate([open_ext / 2, 0, 0])
            _mcc_rail_taper_eps(len + open_ext, clr, MCC_EPS);
        if (MCC_RAIL_LATCH_ENABLED)
            // Male Z = female Z since D44. The notch spans the groove's FULL depth, so the nub (which
            // stops at MCC_RAIL_MALE_H) keeps MCC_RAIL_ROOF_CLR above its top as well.
            _mcc_rail_flank_extrude(-MCC_EPS, MCC_RAIL_DEPTH)
                _mcc_rail_nub_2d(g, grow = clr);
    }
}
```
3. In `_mcc_rail_taper_eps()`, replace the four doc lines:
```
//   Private. Like _mcc_rail_taper(), but with the whole shape shifted down by `eps` and grown by
//   `eps` so it overlaps the caller's own Z=0 boundary cleanly (manifold-avoidance — see
//   mcc_rail_female_cut()'s own doc comment). The extra `eps` (0.01 mm) is applied only to the
//   bottom face; the two nominal widths (at the true Z=0 mouth and Z=depth root) are unaffected.
```
with:
```
//   Private. _mcc_rail_taper() at its true [0, MCC_RAIL_DEPTH], plus a thin slab at the mouth width
//   spanning [-eps, 0], so the cut pierces the caller's own Z=0 face cleanly (manifold-avoidance).
//   Nothing is shifted: D44 removed the caller's extra -eps shift, which lowered the groove roof.
```

## Appendix C — layout / mounts / cradle / shell / tests

**C.1 `lib/mcc/layout.scad`, `mcc_floor_keepout()`.**
1. Doc comment. Replace these eleven lines:
```
//   Pure function: every floor-plan feature `mounts.scad` places (case 1/4"-20 insert, the mount
//   rail (D-15, rev 9 — replaces VESA), the Fishtail reserve band, strap slots, splitter tie-down
//   anchor, the side-bolt support-web footprint), each `[cx, cy, "circle"|"rect", size_or_d,
//   "label"]`. NOT nullary (rev-5 correction 2, layout-patch-wall.md §7.1) — strap slots, the
//   splitter bay and the side-bolt web all depend on `L`, `W`, and `x_bolt`. `mounts.scad` draws the
//   real geometry from this list and asserts pairwise non-overlap (MCC_FLOOR_FEATURE_MIN_SEP, or
//   r1+r2+2.0 where larger — D16, rev 9, exempting the "case_tripod_insert"/"fishtail_reserve" pair,
//   which is deliberately concentric — D19) — this function only computes positions, per this file's
//   "functions only" contract (ruling 1); it does not itself assert (the assert belongs to the L2
//   caller that owns the floor, architecture.md §6). Rev 9: `layout.scad` must NOT `use <rail.scad>`
//   (architecture.md §3) — the "mount_rail" row below is built from the MCC_RAIL_* L0 constants only.
```
   with:
```
//   Pure function: every floor-plan feature `mounts.scad` places (the mount rail -- D-15, rev 9,
//   replaces VESA; widened by D44 -- strap slots, splitter tie-down anchor, the side-bolt support-web
//   footprint), each `[cx, cy, "circle"|"rect", size_or_d, "label"]`. NOT nullary (rev-5 correction 2,
//   layout-patch-wall.md §7.1) — strap slots, the splitter bay and the side-bolt web all depend on `L`,
//   `W`, and `x_bolt`. `mounts.scad` draws the real geometry from this list and asserts pairwise
//   non-overlap (MCC_FLOOR_FEATURE_MIN_SEP, or r1+r2+2.0 where larger — D16, rev 9) — this function
//   only computes positions, per this file's "functions only" contract (ruling 1); it does not itself
//   assert (the assert belongs to the L2 caller that owns the floor, architecture.md §6). The case
//   1/4"-20 insert and the Magewell-Fishtail M4 band are no longer reserved (D44: the wide rail covers
//   the floor centre; the opt-in insert is guarded by T1-63 in cradle.scad). Rev 9: `layout.scad` must
//   NOT `use <rail.scad>` (architecture.md §3) — the "mount_rail" row below is built from the MCC_RAIL_*
//   L0 constants only.
```
2. Delete these three lines of the `let(...)`:
```
        floor_center = [0, 0], // shell parameter default — case plan centre, layout-patch-wall.md §7.1.
                                // Renamed from "vesa_pos" (D-15, rev 9, issue #25 owns the rename) —
                                // still anchors the case 1/4"-20 insert and the Fishtail reserve band.
```
3. Delete these two rows of the returned list:
```
        [floor_center[0], floor_center[1], "circle", MCC_CASE_INSERT_KEEPOUT_D, "case_tripod_insert"],
        [floor_center[0], floor_center[1], "rect", MCC_FISHTAIL_BAND, "fishtail_reserve"],
```

**C.2 `lib/mcc/mounts.scad`.**
1. Replace the header lines 3–11 (from `//   L2. Every case-floor feature except the case's own 1/4"-20 insert boss and the compliant-pad` through `//   §13 D16 — exempting the concentric "case_tripod_insert"/"fishtail_reserve" pair, D19).`) with:
```
//   L2. Every case-floor feature except the case's own opt-in 1/4"-20 insert boss (cradle.scad, T1-32 —
//   installed from the underside into the deck hollow; since D44 only with ["rail", false], T1-63).
//   Owns: the tool-less dovetail mount rail (D-15, rev 9, issue #25 — replaces VESA; widened, flush and
//   >= 0.5 mm-clearance since D44), strap slots (displaced off the reserved splitter bay per §7.1
//   correction 1), the splitter tie-down (mcc_splitter_tiedown(orient="edge")), and a minimal
//   stacking-profile recess.
//   Positions come from mcc_floor_keepout() (layout.scad) so this file never re-derives them; this
//   file also owns the D16 pairwise non-overlap assert over that same list (architecture.md §6,
//   §13 D16 — no exemptions since D44).
```
2. Replace the whole `mcc_assert_floor_keepout_no_overlap()` doc and module (from `// Module: mcc_assert_floor_keepout_no_overlap()` through its closing `}`) with:
```openscad
// Module: mcc_assert_floor_keepout_no_overlap()
// Usage:
//   mcc_assert_floor_keepout_no_overlap(dev, cfg);
// Description:
//   D16 (architecture.md §13, fixed by issue #25): asserts every pairwise combination of
//   mcc_floor_keepout(dev, cfg)'s own rows does not overlap (per _mcc_floor_feature_overlap()
//   above). No exemptions since D44 (2026-09-28): the concentric "case_tripod_insert"/
//   "fishtail_reserve" pair D19 exempted no longer exists. Called once from mcc_shell_base()
//   alongside the rest of this file's floor-feature calls.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_assert_floor_keepout_no_overlap(dev, cfg) {
    rows = mcc_floor_keepout(dev, cfg);
    n = len(rows);
    for (i = [0:1:n - 2])
        for (j = [i + 1:1:n - 1])
            assert(!_mcc_floor_feature_overlap(rows[i], rows[j]),
                str("mcc: floor features \"", rows[i][4], "\" and \"", rows[j][4],
                    "\" overlap on \"", mcc_dev_slug(dev), "\" (D16)"));
}
```
3. In `mcc_floor_features_cut()`'s doc, replace:
```
//   have somewhere to seat). The Fishtail M4 pattern is RESERVE-ONLY per §15 correction 4 (pitch
//   unknown, M7) — no holes are cut for it here, only the keep-out registered in
//   mcc_floor_keepout().
```
with:
```
//   have somewhere to seat). (The Magewell-Fishtail M4 reservation was dropped by D44.)
```

**C.3 `lib/mcc/cradle.scad`.**
1. Insert directly after `    tripod_on = is_undef(tripod_flag) ? false : tripod_flag; // D35: default false.` (in `mcc_cradle()`):
```openscad
    // T1-63 (D44, 2026-09-28): the wide mount rail covers the floor centre this boss needs, and the
    // floor keep-out no longer reserves it -- the two are mutually exclusive. "rail" defaults to
    // true (mounts.scad), so an absent key still trips this.
    rail_flag = struct_val(cfg, "rail");
    rail_on = is_undef(rail_flag) ? true : rail_flag;
    assert(!(tripod_on && rail_on),
        str("mcc: T1-63 cfg[\"tripod_insert\"]=true needs [\"rail\", false] on \"", mcc_dev_slug(dev),
            "\" -- the wide rail covers the floor centre (architecture.md §13 D44)"));
```
2. Replace `for why that would leave it a few mm short). Guarded by cfg["tripod_insert"] (default true,` with `for why that would leave it a few mm short). Guarded by cfg["tripod_insert"] (default false since D35;`. Replace the next line `//   D-16, rev 9 issue #29) so shell.scad's unconditional call site needs no change — mirrors` with `//   rail must be off, T1-63) so shell.scad's unconditional call site needs no change — mirrors`.
3. Replace `                     // floor_center-default (0,0) case tripod insert boss below lands inside the` with `                     // (0,0) case tripod insert boss below (opt-in, T1-63) lands inside the`.
4. Replace `        // cfg["tripod_insert"] (default true, D-16) — omitted entirely when false, leaving that` with `        // cfg["tripod_insert"] (default false, D35; needs ["rail", false], T1-63) — omitted when false, leaving that`.

**C.3b `tests/test_shell.scad`** (stale since D35; comments only).
1. Replace `// tripod_insert defaults to true (D-16) when the key is absent, as VARIANT/VARIANT_FAN above both` with `// tripod_insert defaults to false (D35) when the key is absent, as VARIANT/VARIANT_FAN above both`.
2. Replace `// --- cradle.scad standalone (default tripod_insert=true, D-16) ---` with `// --- cradle.scad standalone (default tripod_insert=false, D35; true needs ["rail", false], T1-63) ---`.

**C.4 `lib/mcc/shell.scad`.** Replace:
```
    // D16 (architecture.md §13, fixed by issue #25): no two mcc_floor_keepout() rows overlap,
    // except the concentric "case_tripod_insert"/"fishtail_reserve" pair (D19).
```
with:
```
    // D16 (architecture.md §13, fixed by issue #25): no two mcc_floor_keepout() rows overlap (no
    // exemptions since D44).
```

**C.5 `tests/test_layout.scad`.** Replace:
```
assert(len([for (f = fk) if (f[4] == "case_tripod_insert") f]) == 1, "case_tripod_insert missing");
```
with:
```
// D44: the case-insert and Fishtail reservations are retired -- neither row may come back silently.
assert(len([for (f = fk) if (f[4] == "case_tripod_insert" || f[4] == "fishtail_reserve") f]) == 0,
    "D44: case_tripod_insert/fishtail_reserve keep-out rows must not exist");
```

**C.6 `tests/test_rail.scad`.**
1. Replace header lines 8–11:
```
//     - D16 (lib/mcc/mounts.scad mcc_assert_floor_keepout_no_overlap()): no two
//       mcc_floor_keepout() rows overlap, except the concentric "case_tripod_insert"/
//       "fishtail_reserve" pair (D19) -- run against a real device record so the exemption is
//       actually proven, not merely asserted to exist.
```
with:
```
//     - D16 (lib/mcc/mounts.scad mcc_assert_floor_keepout_no_overlap()): no two
//       mcc_floor_keepout() rows overlap (no exemptions since D44), run against a real device record.
//     - T1-62 (D44): >= MCC_RAIL_MATE_CLR normal to the flanks and at the roof.
```
2. Insert directly after `assert(MCC_RAIL_END_STOP_L == 0 && MCC_RAIL_END_STOP_H == 0, "D34: the male end-stop flange is retired");`:
```openscad

// --- T1-62 / D44: >= MCC_RAIL_MATE_CLR on every non-bearing face, and the user's width range ------
assert(MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE) >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("T1-62: rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE), " below ", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_DEPTH - MCC_RAIL_MALE_H >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("T1-62: rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H, " below ", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_MATE_CLR >= 0.5 - MCC_EPS, "D44: the user's minimum rail clearance is 0.5 mm");
assert(MCC_RAIL_ROOT_W >= 60 && MCC_RAIL_ROOT_W <= 70,
    str("D44: MCC_RAIL_ROOT_W=", MCC_RAIL_ROOT_W, " outside the user's 60-70 mm range"));
```
3. Replace the manual check 2 block:
```
// 2. D16, violated by moving the rail on top of the case's own 1/4"-20 insert keep-out (scratch
//    edit constants.scad MCC_RAIL_Y = 0):
//    -> "mcc: floor features \"case_tripod_insert\" and \"mount_rail\" overlap ... (D16)"
```
with:
```
// 2. D16, violated by moving the rail onto the side-bolt support web (scratch edit constants.scad
//    MCC_RAIL_Y = -40):
//    -> "mcc: floor features \"mount_rail\" and \"side_bolt_web\" overlap ... (D16)"
//
// 3. T1-63 (D44), the opt-in case insert together with the (default-on) rail:
//    mcc_cradle(DEV, [["fan", false], ["splitter", false], ["tripod_insert", true]]);
//    -> "mcc: T1-63 cfg[\"tripod_insert\"]=true needs [\"rail\", false] ..."
```

## Appendix D — brackets, coupon, `rail_fit.py`

**D.1 `models/brackets/arch-tv-bracket.scad`.**
1. Replace the header Z-stack block, from `//   Z stack (TV back = 0; plan §1.3, re-derived independently by the architect, §12.1 -- all checks` through `//   §1.3 -- so it must pass over it in Z instead).`, with:
```
//   Z stack (TV back = 0; plan §1.3, re-derived for D44 -- the case floor now sits FLUSH on the
//   centre's top face, the rail has no pedestal any more):
//     Arm TV face / centre gap floor ............ Z = 0
//     Arm top face = centre bottom face (stacked lap) ... Z = ARCH_PLATE_T       (= 11)
//     Rail mounting face (centre top) Z_RAIL ..... Z = 2 * ARCH_PLATE_T          (= 22)
//     Arm feature top ARM_TOP_Z (ribs, M8 pad boss) Z = ARCH_PLATE_T + RIB_H     (= 20)
//     Case floor (exterior), at full mate and while sliding .. Z = Z_RAIL          (= 22, flush)
//     Case lid top ................................ Z = 22 + 51 = 73            (H=51, CLAUDE.md)
//   Sweep condition (T1-51 / A5): Z_RAIL - ARM_TOP_Z >= ARCH_SWEEP_CLR, i.e.
//   2T - (T + 9) >= 2 => T >= 11 -- ARCH_PLATE_T=11 is the smallest plate that clears the pad
//   during the +X slide-on approach (the case can never clear the pad by going above it -- plan
//   §1.3 -- so it must pass over it in Z instead). T was 8 while the rail carried a 3 mm pedestal.
```
2. Replace `//       (assembly (0, rise, ARCH_PLATE_T)); bottom face (TV-facing, but 8 mm standing off the TV --` with `//       (assembly (0, rise, ARCH_PLATE_T)); bottom face (TV-facing, but 11 mm standing off the TV --`.
3. Replace the five lines from `ARCH_PLATE_T = 8.0; // mm. derived minimum (§1.3 Z-stack derivation above; T>=8 for the slide-on` through `                     // cantilevered BEAM, a different structural class.` with:
```openscad
ARCH_PLATE_T = 11.0; // mm. derived minimum (Z-stack derivation above: T>=11 for the slide-on sweep to
                      // clear the pad once D44 removed the rail's 3 mm pedestal -- was 8) and
                      // independently justified for torsion stiffness (plan §2). NOT
                      // MCC_BRACKET_PLATE_T (6.0, constants.scad) -- that constant is a SHIM thickness
                      // for a TV-sandwiched plate (tv-bracket.scad); this plate is a cantilevered BEAM,
                      // a different structural class.
```
4. Replace `CENTRE_W = 40.0; // mm. assumed (= ARM_W) -- centre-body height in local Y.` with:
```openscad
CENTRE_W = 92.0; // mm. D44: must hold the 65 mm rail's keep-out Y span [-32.5, +36.1] (T1-53, needs
                  // >= 72.2) AND the UP arrow above it (T1-60: 36.1 + 1 + 6 + 1 = 44.1 <= CENTRE_W/2,
                  // minimum 88.2) -- 92 leaves 0.95 mm on both T1-60 bounds. Was 40 (= ARM_W) for the
                  // 14.6 mm rail.
```
5. Replace `LAP_RIB_GAP = 1.0; // mm. assumed -- arm ribs stop this far short of the lap.` with:
```openscad
LAP_RIB_GAP = 3.0; // mm. arm ribs stop this far short of the lap. D44: 3.0 (was 1.0) -- with the
                    // 92 mm centre body the rib end's outer corner lies inside the body's Y band at large
                    // TV_TOP_CLEAR, so T1-55's X clearance alone governs: 1.0 left 0.994 mm at
                    // TV_TOP_CLEAR=184.9 (limit 1.0, passing only on the assert's EPS); 3.0 leaves 2.34.
```
6. Replace `M3_JOINT_SCREW_L = 10; // mm. derived stock length (§3.3 screw-stack derivation, T1-57).` with:
```openscad
M3_COUNTERBORE_DEPTH = M3_HEAD_K + 1.3; // mm. D44 (T1-57): the head sits 4.3 mm deep in the 11 mm
                  // centre, leaving 6.7 mm of centre under it, so an M3x12 reaches 5.3 mm into the arm
                  // (tip 1.4 mm above the insert-bore floor, 0.9 more than T1-57's 0.5) -- the same
                  // engagement the 8 mm stack had.
M3_JOINT_SCREW_L = 12; // mm. derived stock length (§3.3 screw-stack derivation, T1-57). Was 10 (8 mm plates).
```
7. `replace_all` in this file:
   - `m3_counterbore_depth = M3_HEAD_K + 0.3;` → `m3_counterbore_depth = M3_COUNTERBORE_DEPTH;` (2 occurrences: the T1-57 block and `mcc_arch_tv_centre()`).
8. Replace:
```
        centre_z_max = ARCH_PLATE_T + MCC_RAIL_SILL_H + MCC_RAIL_END_STOP_H, // = 17 (rail rises
            // MCC_RAIL_SILL_H=7 above its own foot at Z_RAIL, plus the end-stop's own extra rise)
```
with:
```
        centre_z_max = ARCH_PLATE_T + MCC_RAIL_MALE_H + MCC_RAIL_END_STOP_H, // = 14.5 (the male rises
            // MCC_RAIL_MALE_H above its own foot at Z_RAIL -- D44; MCC_RAIL_END_STOP_H is 0 since D34)
```
9. Replace the T1-51 block:
```
    // T1-51 (A5): the +X slide-on sweep clears the right arm's pad (§1.3).
    assert(z_rail + MCC_FLOOR_T - arm_top_z >= ARCH_SWEEP_CLR - MCC_EPS,
        str("mcc: arch-tv-bracket T1-51 slide-on sweep clearance=", z_rail + MCC_FLOOR_T - arm_top_z,
            " below ARCH_SWEEP_CLR=", ARCH_SWEEP_CLR));
```
with:
```
    // T1-51 (A5): the +X slide-on sweep clears the right arm's pad (§1.3). D44: the case floor rides
    // flush at z_rail (no pedestal), so there is no MCC_FLOOR_T term any more.
    assert(z_rail - arm_top_z >= ARCH_SWEEP_CLR - MCC_EPS,
        str("mcc: arch-tv-bracket T1-51 slide-on sweep clearance=", z_rail - arm_top_z,
            " below ARCH_SWEEP_CLR=", ARCH_SWEEP_CLR));
```
10. Replace `//   facing, but standing 8 mm off the TV -- PLAN-ASSUMPTION-3) face on the bed (local Z=0).` with `//   facing, but standing 11 mm off the TV -- PLAN-ASSUMPTION-3) face on the bed (local Z=0).`
11. Replace `    variant = [["fan", true], ["splitter", false], ["fan_switch", true], ["tripod_insert", true], ["lid_vents", true]];` with:
```
    variant = [["fan", true], ["splitter", false], ["fan_switch", true], ["tripod_insert", false], ["lid_vents", true]]; // tripod off: T1-63 (D44)
```
12. Replace `    translate([RAIL_X + x_shift, rise + MCC_RAIL_Y, z_rail + MCC_FLOOR_T]) rotate([0, 0, 180]) {` with `    translate([RAIL_X + x_shift, rise + MCC_RAIL_Y, z_rail]) rotate([0, 0, 180]) { // D44: flush`.
13. In the reused-constants comment, remove `MCC_FLOOR_T, ` from the list. After C it reads `MCC_CLR_SLIDE, MCC_RAIL_*, MCC_FLOOR_T, MCC_WALL, ...`, and nothing in the file uses it any more. Grep first: if any `MCC_FLOOR_T` use remains, leave the list alone.

**D.1b `tests/test_arch_tv_bracket.scad`.** Replace:
```
// Three TV_TOP_CLEAR values (mm): the arch floor (73.2, just above the rise>=0 bound of ~73.175 --
// T1-49), the file's own placeholder default (150), and just under the user bound (184.9,
// TV_TOP_CLEAR_MAX=185 -- T1-50).
_TV_TOP_CLEAR_VALUES = [73.2, 150, 184.9];
```
with:
```
// Three TV_TOP_CLEAR values (mm): the arch floor (69.7, just above the rise>=0 bound of ~69.675 at
// MCC_RAIL_Y=-23.5 -- T1-49, D44), the file's own placeholder default (150), and just under the user
// bound (184.9, TV_TOP_CLEAR_MAX=185 -- T1-50; the T1-55 extreme after D44).
_TV_TOP_CLEAR_VALUES = [69.7, 150, 184.9];
```
Then, in manual check 1:
- `mcc_arch_tv_assert(mcc_arch_tv_geom(tv_top_clear = 72));` → `mcc_arch_tv_assert(mcc_arch_tv_geom(tv_top_clear = 69));`
- `needs TV_TOP_CLEAR >= 73.175...` → `needs TV_TOP_CLEAR >= 69.675...`

**D.2 `models/brackets/tv-bracket.scad`.**
1. Replace:
```
//       local Z=0, rising into +Z. Since mcc_rail_male()'s own local Z=0 is documented
//       (lib/mcc/rail.scad) as "the pedestal foot, meets the bracket plate", the plate's own top
//       face at Z=0 IS that mating face by construction -- no extra transform needed to align it.
```
with:
```
//       local Z=0, rising into +Z. mcc_rail_male()'s own local Z=0 is the plate's top face, and
//       since D44 (no pedestal) it is ALSO the plane the case's exterior floor rests on, flush.
```
2. Replace the "Derivation of the rotate([0,0,180])" bullet: from `//     - Derivation of the rotate([0,0,180]): lib/mcc/mounts.scad places the case's female groove` through `//       uses; render it and check the PNG before trusting this comment over the picture.`. The new text:
```
//     - Derivation of the rotate([0,0,180]): lib/mcc/mounts.scad places the case's female groove
//       at `translate([0, MCC_RAIL_Y, 0]) mcc_rail_female_cut(...)` in the case's OWN world frame
//       (floor at world Z=0, case centred at X=Y=0) -- a pure translate, no rotation, so
//       female-local (X,Y,Z) = case-world (X, Y-MCC_RAIL_Y, Z). Since D44 (no pedestal) the male's
//       local frame IS the female's, Z included: the case's exterior floor rests on the plate's top
//       face. Mating a case onto a RAW mcc_rail_male() call therefore needs
//       `translate([0, -MCC_RAIL_Y, 0])` applied to the case's native-frame geometry -- and since
//       MCC_RAIL_Y is negative, that puts the case's own +Y (patch wall) at a large POSITIVE local Y,
//       i.e. UP under the "+Y is up" convention -- the WRONG way. Rotating the rail by 180 deg about
//       its own local Z (a proper rotation, not a mirror, so the dovetail's chirality and the mate
//       stay valid) and the mated case by the same 180 deg composes to
//       `translate([0, MCC_RAIL_Y, 0]) rotate([0,0,180])` applied to the case's native-frame
//       geometry -- the patch wall lands at a large NEGATIVE local Y, i.e. DOWN. That is the
//       transform the "assembly" branch below uses; render it and check the PNG before trusting
//       this comment over the picture.
```
3. `replace_all`: `MCC_BRACKET_PLATE_T + MCC_RAIL_SILL_H + (RIBS ? RIB_H : 0)` → `MCC_BRACKET_PLATE_T + MCC_RAIL_MALE_H + (RIBS ? RIB_H : 0)` (2 occurrences).
4. Replace `    // why; mcc_rail_male()'s own local Z=0 (pedestal foot) sits on this plate's top face (Z=0).` with `    // why; mcc_rail_male()'s own local Z=0 sits on this plate's top face (Z=0), flush with the case floor (D44).`.
5. Replace `    translate([0, MCC_RAIL_Y, MCC_FLOOR_T]) rotate([0, 0, 180]) {` with `    translate([0, MCC_RAIL_Y, 0]) rotate([0, 0, 180]) { // D44: flush, no pedestal`.

**D.3 `models/coupons/rail-latch.scad` (fixes D46).**
1. Replace header lines:
```
//   thumb-release disengages it cleanly; calibrates MCC_CLR_SLIDE for this printer/material
//   combination the same way tolerance-ladder.scad calibrates it for the other fit classes, plus
//   MCC_RAIL_LATCH_ENGAGE and the 30 N retention target (assumed, layout-patch-wall.md §1.1) with a
//   simple pull-test (luggage scale through a temporary loop).
//
//   Both halves share ONE base plate so the whole coupon renders/checks as a single connected
//   shell (architecture.md §9 Tier-3 "one connected shell" — same requirement every other coupon in
//   this directory already satisfies via its own shared base). Snap or saw the thin bridging plate
//   between the two halves apart after printing, before the pull test.
```
with:
```
//   pull-off works; checks the D44 clearances (>= 0.5 mm normal to the flanks and at the roof --
//   MCC_RAIL_MATE_CLR is a user decision, confirmed here, not calibrated), the groove-roof bridge
//   (architecture.md R40: the groove half prints exactly like the case floor), MCC_RAIL_LATCH_ENGAGE
//   and the 30 N retention target (assumed) with a simple pull-test (luggage scale, temporary loop).
//
//   The groove half stands directly on the bed, groove mouth down and OPEN, like the case floor; the
//   rail half stands on its own plate. Two thin snap-off strips beside the groove join them so the
//   coupon renders/checks as one connected shell (architecture.md §9 Tier 3). Snap the strips off
//   before testing. (Until D46 the groove half sat on a shared plate that sealed its groove mouth.)
```
2. Replace:
```
x_base0   = -MCC_WALL;     // the base starts under the female's stop wall.
```
with:
```
x_base0   = -MCC_WALL;     // the coupon's -X extent: the female's stop wall.
STRIP_W   = 2.0;           // snap-off joining strip width, mm. assumed -- thin enough to break by hand.
```
3. Replace in the `echo(...)`:
   - `" clr_slide=", MCC_CLR_SLIDE,` → `" clr_horiz=", MCC_RAIL_CLR_HORIZ, " roof_clr=", MCC_RAIL_ROOF_CLR,`
   - `" print_bbox=", [base_w, base_d, PLATE_T + MCC_RAIL_SILL_H]` → `" print_bbox=", [base_w, base_d, max(MCC_RAIL_SILL_H, PLATE_T + MCC_RAIL_MALE_H)]`
4. Replace everything from `// The base doubles as the male's bracket plate, so it carries the latch window (issue #46, D34):` through the end of `module _rail_latch_female() { … }` (that is, the base module, the Z0 comment block and `Z0 = …;`, and the female module). The new text:
```openscad
// The male half's own plate (the bracket-plate stand-in) carries the latch window (issue #46, D34;
// nub included since D44): the arm's leg stands on the bed through it, joined only at its root. Two
// snap-off strips join it to the groove half; they run along the groove half's outer edges, clear of
// the groove's open +X end.
module _rail_latch_base() {
    difference() {
        union() {
            translate([x_male0 - MARGIN, -base_d / 2, 0])
                cube([LEN + 2 * MARGIN, base_d, PLATE_T]);
            for (y0 = [-footprint_d / 2, footprint_d / 2 - STRIP_W])
                translate([LEN - MCC_EPS, y0, 0])
                    cube([x_male0 - MARGIN - LEN + 2 * MCC_EPS, STRIP_W, PLATE_T]);
        }
        translate([x_male0 + LEN / 2, 0, PLATE_T])
            mcc_rail_male_window(len = LEN, plate_t = PLATE_T);
    }
}

// The male lands MCC_EPS INTO its plate (a genuine shared volume, not a coincident face -- trimesh's
// split(), the Tier-3 "one connected shell" check, would otherwise see two parts).
Z0 = PLATE_T - MCC_EPS;

// Female half: a plinth standing DIRECTLY on the bed with its groove mouth face down -- the case
// floor's own print pose, so the groove roof prints as the same ~66 mm bridge as on a real base (R40).
// mcc_rail_female_cut()'s local Z=0 (the case's exterior floor face) is the bed; the groove is closed
// at -X by a MCC_WALL stop wall and runs out open through the plinth's +X end, like the case (D34).
module _rail_latch_female() {
    translate([x_female0, 0, 0])
        difference() {
            translate([-MCC_WALL, -footprint_d / 2, 0])
                cube([LEN + MCC_WALL, footprint_d, MCC_RAIL_SILL_H]);
            translate([LEN / 2, 0, 0])
                mcc_rail_female_cut(len = LEN, open_ext = 1);
        }
}
```
5. Replace `// Male half: mcc_rail_male()'s own local Z=0 (pedestal base) lands MCC_EPS into the shared base` with `// Male half: mcc_rail_male()'s own local Z=0 (the plate top) lands MCC_EPS into its base`. Replace the following line `// plate's own top face (world Z=Z0) -- the base plate itself stands in for the bracket's own plate,` with `// plate's own top face (world Z=Z0) -- that plate stands in for the bracket's own plate,`.

**D.4 `scripts/rail_fit.py`.**
1. Replace the docstring lines:
```
Renders mcc_rail_male() (no plate) with the pinned OpenSCAD, loads
exports/<slug>/base.model.stl (run `build.py render <slug> --part base` first) and, for a set of
insertion offsets dx (male shifted +X, i.e. not yet fully in), intersects the two below the groove
roof (the roof is a designed face-to-face contact). Expected, and asserted:
```
with:
```
Renders mcc_rail_male() (no plate) with the pinned OpenSCAD, loads
exports/<slug>/base.model.stl (run `build.py render <slug> --part base` first) and, for a set of
insertion offsets dx (male shifted +X, i.e. not yet fully in), intersects the two over the WHOLE
base: since D44 the male's frame is the groove's (no pedestal) and the roof, like the flanks, keeps
>= MCC_RAIL_MATE_CLR -- any contact at full mate is a failure. Expected, and asserted:
```
2. Delete these three lines:
```
RAIL_Y = -20.0      # lib/mcc/constants.scad MCC_RAIL_Y
FLOOR_T = 3.0       # MCC_FLOOR_T: male z = FLOOR_T is the case's exterior floor face
ROOF_Z = 3.9        # just under the groove roof (MCC_RAIL_DEPTH = 4)
```
3. In `main()`, replace:
```
    base = trimesh.boolean.intersection(
        [trimesh.load(str(base_path), force="mesh"), box(bounds=[[-400, -200, -10], [400, 200, ROOF_Z]])],
        engine="manifold")
```
with:
```
    base = trimesh.load(str(base_path), force="mesh")
    rail_y = _const("MCC_RAIL_Y")
```
4. Replace `        m.apply_translation([dx, RAIL_Y, -FLOOR_T])` with `        m.apply_translation([dx, rail_y, 0.0])`.
5. Delete the now-unused import line `from trimesh.creation import box`.

## Appendix E — docs (developer-owned, same PR)

Paste rule: copy only the text inside the fences.

**E1 `BOM.md`.** Rows are identified by their opening text; line numbers shift with C.
0. Replace the heading `### Case floor mounting (own tripod/cheeseplate feature, distinct from the device-retention bolt above)` with `### Case floor mounting (the mount-rail groove — no floor insert or reservations since D35/D44)`.
1. In the row that begins `| ~~1/4"-20 brass heat-set insert~~ |`, replace:
```
`cfg["tripod_insert"]` can bring it back per variant.
```
with:
```
`cfg["tripod_insert"]` can bring it back per variant, but only together with `["rail", false]` (D44, assert T1-63).
```
2. Replace the whole row that begins `| — | — | — | Tool-less dovetail mount rail (D-15, rev 9, issue #25 — **replaces VESA 75×75**)` with:
```
| — | — | — | Tool-less dovetail mount rail (D-15, rev 9, issue #25 — **replaces VESA 75×75**; widened and made flush by D44: 65 mm root, the case floor sits flush on the bracket plate, ≥ 0.5 mm clearance on every non-bearing face) needs no BOM hardware of its own: the female groove (case floor) and the male rail + snap latch are printed features. See `## Mounting brackets` for bracket hardware. The Magewell-Fishtail M4 reservation is **dropped** (D44) — no Fishtail hardware | `.claude/knowledge/architecture.md` §6 floor rule (rev 16), §13 D44; `lib/mcc/rail.scad` |
```
3. Replace the whole row that begins `| Rubber/EPDM adhesive foot |` with:
```
| Rubber/EPDM adhesive foot | generic, size TBD | 4 (typical) | Case underside — **free-standing use only**: never on a case that mounts on a bracket, where feet would hold the floor off the plate that D44 requires it to sit flush on | `knowledge/components/fasteners-and-hardware.md:180-187` (materials, common commodity size range 10–70 mm) |
```
4. In the arch M8 row (the one that begins `| M8 socket head cap screw (ISO 4762) |`), replace `7.0 mm at the current parameters` with `10.0 mm at the current parameters (11 mm plates since D44)`.
5. Replace the whole row that begins `| M3 socket head cap screw M3×10 (ISO 4762) | generic | 8 | Lap joints` with:
```
| M3 socket head cap screw M3×12 (ISO 4762) | generic | 8 | Lap joints, 4 per side, driven from the top face (M3×12 since D44: 11 mm centre plate, counterbore `M3_HEAD_K + 1.3` — T1-57) | `models/brackets/arch-tv-bracket.scad` T1-57; `docs/plans/2026-09-27-arch-tv-bracket.md` §3.3 derivation |
```

**E2 `models/brackets/README.md`.**
1. Replace `  of free space to the right of its final position, from 19 to 70 mm off the TV back.` with `  of free space to the right of its final position, from 22 to 73 mm off the TV back (D44: 11 mm plates, the case floor flush on the centre).`
2. Replace `bolt both arms to the centre (M3×10, from the` with `bolt both arms to the centre (M3×12, from the`.

**E3 `models/coupons/README.md`.**
1. Replace the whole table row whose first cell is rail-latch.scad (in code font, the coupon table near the top) with:
```
| `rail-latch.scad` | The tool-less dovetail mount rail (D-15; widened, flush and ≥ 0.5 mm-clearance since D44): the dovetail slides freely along its full engagement length with acceptable play, the groove roof (a ~66 mm bridge printed exactly like the case floor) does not sag into the 0.5 mm roof gap, the snap latch flexes freely, clicks at full insertion and holds at least the assumed retention target (pull-test with a luggage scale through a temporary loop, **≥ 30 N / ≈3 kgf**) | `lib/mcc/constants.scad` : `MCC_RAIL_ROOF_CLR` (raise it if the roof sags — never narrow the rail), `MCC_RAIL_LATCH_ENGAGE` / `MCC_RAIL_LATCH_RAMP_OUT`, the 30 N retention target (`assumed`); confirms (does not calibrate) `MCC_RAIL_MATE_CLR`, a user decision |
```
2. Replace the whole table row whose first cell is rail-latch (in code font) in the "Orientation (Bambu Studio)" table with:
```
| `rail-latch` | **Print as modelled, no rotation:** the groove half stands directly on the bed, groove mouth down (like the case floor); the rail half stands on its own plate, rail up (like a bracket). Two thin snap-off strips join them — break them off before testing. | Both halves in their production print pose: the groove roof prints as the same ~66 mm bridge as on a real base (architecture.md R40), and the latch arm's leg stands on the bed through its plate window. |
```
3. Replace the `### rail-latch` section body, from the line `> **Latch redesigned** (2026-09-28, architecture.md D34): an in-plane snap arm cut from the male` through `  retuning it.` (just before `## print-log.md`). The new text:
```
- Hardware needed: a luggage/fish scale (or similar), a temporary loop (string/cable tie) round the
  rail half's plate for the pull test, and calipers.
- Snap the two joining strips off first.
- **Roof sag (R40):** before inserting anything, measure the groove roof's height above the groove
  half's bottom face at mid-width, at both ends and in the middle (nominal 4.0 mm). The rail's own top
  is 3.5 mm tall: the roof must stay clear of it.
- **Latch freedom:** with a small screwdriver, press the latch nub inward — the arm must flex freely
  (nothing fused to the plate under the nub) and spring back.
- Slide the rail half into the groove from the open (+X) end. Does it engage smoothly along the full
  60 mm, self-aligning on the dovetail before the latch has to do any work (the 20 mm
  `MCC_RAIL_LATCH_LEAD_IN`)? Does it click at full insertion, and does the groove's closed end stop
  over-travel?
- **Play (R41):** at full insertion, measure the lateral and lift play (expected ≈ ±0.6 mm and ≈ 1 mm
  from the 0.5 mm clearance, D44).
- Pull-test: with the latch engaged, pull the two halves apart along the slide axis (via the loop)
  and read the scale at disengagement. **Target ≥ 30 N (≈3 kgf)**, `assumed`.
- **Good** = no roof contact, free latch arm, smooth slide, clean click, end stop works, pull-off at
  or above 30 N, play within the expected figures.
- Record: roof heights, slide feel, play, click quality, pull-off force (N), any cracking at the
  latch arm's root.
- Update: `lib/mcc/constants.scad` → `MCC_RAIL_ROOF_CLR` if the roof sags into the gap (raise it;
  never narrow the rail — user decision D44), and `MCC_RAIL_LATCH_ENGAGE` / `MCC_RAIL_LATCH_RAMP_OUT`
  if the pull-off misses the target. If the play is objectionable, report it — `MCC_RAIL_MATE_CLR`
  is a user decision, not a coupon result.
```

**E4 `CLAUDE.md`.**
1. Fixed decision "Closure" — replace these lines:
```
  16, no external lug — D-13); the device lies flat in a ribbed cradle. No floor through-bolt. Floor
  features (one owner, `mounts.scad`): the dovetail mount-rail groove (D-15/D34), strap slots,
  stacking profile. **No floor insert** (user decision 2026-09-28, D35): the case's own 1/4"-20
  floor insert is off in every variant — the side bolt is the only screw (`cfg["tripod_insert"]`
  stays available, default false). Hole position per SKU is
```
with:
```
  16, no external lug — D-13); the device lies flat in a ribbed cradle. No floor through-bolt. Floor
  features (one owner, `mounts.scad`): the dovetail mount-rail groove (D-15/D34), strap slots,
  stacking profile. **Wide, flush dovetail** (user decision 2026-09-28, D44): 65 mm root at
  `MCC_RAIL_Y` = −23.5; the case's exterior floor sits flush on the bracket plate (no pedestal) and
  every non-bearing face of the joint keeps ≥ 0.5 mm clearance (flanks and roof); the D34 latch is
  the lock. **No floor insert and no floor reservations** (D35, D44): the side bolt is the only
  screw; the Magewell-Fishtail M4 and 1/4"-20 insert reservations are dropped because the rail covers
  the floor centre — `cfg["tripod_insert"]` stays available only with `["rail", false]` (assert
  T1-63). Hole position per SKU is
```
2. Current status (after C's edit). Replace:
```
a plain Ø2.5 tap-drill bore instead of a printed thread (D41) — are in architecture.md §13.
```
with:
```
a plain Ø2.5 tap-drill bore instead of a printed thread (D41), the wide flush mount rail (D44) — are in architecture.md §13.
```

**E5 `CHANGELOG.md`.** Insert directly after C's line:
```
- CI: a case part whose STEP falls back to the faceted converter now fails `build.py ci`.
```
the following bullets:
```
- **Wide, flush mount rail** (architecture.md D44, user decision 2026-09-28): the dovetail's root is
  65 mm (was ≈14.6 mm) at `MCC_RAIL_Y` = −23.5, the case's exterior floor sits flush on the bracket
  plate (the rail's 3 mm pedestal is gone), and every non-bearing face of the joint keeps ≥ 0.5 mm
  clearance. Brackets and cases printed before this change do not mate with ones printed after it.
  The arch bracket's plates are 11 mm (was 8), its centre 92 mm wide (was 40), and its lap screws
  M3×12 (was M3×10).
- **Floor reservations dropped** (D44): the Magewell-Fishtail M4 band and the 1/4"-20 insert keep-out
  are gone — the rail covers the floor centre. `tripod_insert` now requires `["rail", false]`.
- `rail-latch` coupon: the groove half now prints standing on the bed with its groove open, like the
  case floor (it used to be sealed by the shared base plate, D46).
```

## Appendix F — amended implementation order (stacked on C)

1. Branch `feature/wide-dovetail` from C's branch head, or from `main` after C merges. Confirm that `.claude/knowledge/architecture.md` contains the line `**Revision 15, 2026-09-28` and a `| **D43** |` row.
2. Appendix A (constants).
3. Appendix B (rail.scad).
4. Appendix C (layout, mounts, cradle, shell, tests).
5. Appendix D.1, D.1b and D.2 (brackets and their test).
6. Appendix D.3 (coupon) and D.4 (`rail_fit.py`).
7. `python scripts/build.py doctor`, then `smoke`. Everything must pass, including `test_rail`, `test_layout` and `test_arch_tv_bracket` at 69.7/150/184.9.
8. `python scripts/build.py render --all`, then `check --all` (B15 applies).
9. `python scripts/rail_fit.py <slug>` for each of `pro-convert-for-ndi-to-hdmi`, `pro-convert-sdi-tx` and `pro-convert-hdmi-plus`. It reads `exports/<slug>/base.model.stl` from step 8; if that file is missing, run `python scripts/build.py render <slug> --part base`. Each run must print `rail fit OK`.
10. `python scripts/build.py golden` (no `--update`). Expect FAILs only on B11's list; anything else, STOP.
11. Run this one targeted command:
    `python scripts/build.py golden coupons/rail-latch brackets/tv-bracket brackets/arch-tv-bracket pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio --update`
    Then run `golden` again (all must PASS), then check `git diff --stat -- tests/golden/` against B11.
12. `python scripts/build.py slicer-check`: zero warnings (B15).
13. `python scripts/build.py review`.
14. `python scripts/build.py ci --group k/6 --jobs 3` for k = 1…6 (or the PR's CI run). This also runs C's exact-STEP gate on the new bases.
15. Appendix E (docs), then Appendix G and H (architecture docs), then B14 (record).
16. `python scripts/build.py all`, then open the PR into `main`, CI green. The PR body cites D44–D47 and lists Q21 and M15 as open for the user.

**Ordering rules (A vs. C, and D):**
- A never merges before C.
- If C gets review fixes after A branched, rebase A onto C. Then redo steps 7–14; above all, regenerate A's goldens rather than merging JSON.
- `constants.scad`, `BOM.md`, `CLAUDE.md` and `CHANGELOG` edits are in disjoint places in C and A. A's anchors deliberately use C's new text:
  - `CLAUDE.md` Current status;
  - the `CHANGELOG` bullet;
  - architecture.md: the rev-15 header, the D43/R39/M19/Q20 rows and the numbering note;
  - layout-patch-wall.md: rev 15 and T1-61.
- Plan D is re-planned against A's merged constants (see its verdict). No change to `rail.scad` may run in parallel with A. That includes the future DP48 lock (Q21), which stacks after A.

---

## Appendix G — `.claude/knowledge/architecture.md` (paste verbatim on the feature branch)

Paste rule: copy only the text inside the fences. Rows are identified by their first cell. Anchors quoted inline contain no backticks.

**G1 Header.** Insert immediately before the paragraph beginning `**Revision 15, 2026-09-28`, followed by one blank line:
```
**Revision 16, 2026-09-28 (wide, flush mount rail — D44; plan `docs/plans/2026-09-28-wide-dovetail.md`).**
User decisions after the external specialist's CAD review: the dovetail stays and becomes **much wider**
(65 mm root, `MCC_RAIL_Y` = −23.5, near the device's centre of mass); the case's exterior floor sits
**flush** on the bracket (the male's 3 mm pedestal is gone — the floor-on-plate seat is the joint's only
designed bearing face); **≥ 0.5 mm clearance on every non-bearing face** (flanks and roof); and the
Magewell-Fishtail M4 and 1/4"-20 insert floor reservations are **dropped** (the rail covers the floor
centre; the opt-in insert now needs `["rail", false]`, **T1-63**). The D34 latch stays the lock, adapted
— its plate window now also clears the nub, which would otherwise fuse to the plate once the pedestal is
gone. New: **T1-62** (rail clearances), **R40** (the ~66 mm groove-roof bridge and the +X-wall notch),
**R41** (joint play; bearing faces on a TV-mounted bracket), **Q21** (the DP48 lock); M15 rewritten, M7
retired; §13 **D44–D47**. Cascade: arch-bracket plates 8 → 11 mm, centre 40 → 92 mm, lap screws
M3×12. **No case envelope figure moves.** Also recorded here, because it has no branch yet: the gate of
plan D, the vertical VESA-400 × 300 column bracket — **rejected for re-plan** (hub topology and a fresh
sibling file approved as the direction); its open items are **R42**, **R43**, **M20** and **Q22**.
```

**G2 §6 floor rule.**
1. Replace:
```
  **mount-rail dovetail groove and its sill** (D-15, rev 9 — replaces VESA), the
  Magewell-Fishtail M4 reservation, the strap slots, the stacking profile and the splitter
  tie-downs. It exposes `mcc_floor_keepout()` and asserts non-overlap between all of them.
```
with:
```
  **mount-rail dovetail groove and its sill** (D-15, rev 9 — replaces VESA; widened by D44), the
  strap slots, the stacking profile and the splitter tie-downs (the Magewell-Fishtail M4 reservation
  was dropped by D44). It exposes `mcc_floor_keepout()` and asserts non-overlap between all of them.
```
2. Replace:
```
  the underside *into the deck hollow*: the case's own 1/4"-20 insert boss (T1-32) and the
  compliant-pad pocket.
```
with:
```
  the underside *into the deck hollow*: the case's own 1/4"-20 insert boss (T1-32; opt-in, and since
  D44 only with `["rail", false]` — T1-63) and the compliant-pad pocket (removed by D37).
```
3. Replace:
```
  **`floor_center`** (it still anchors `case_tripod_insert` and `fishtail_reserve`). It is removed,
```
with:
```
  **`floor_center`** (it anchored `case_tripod_insert` and `fishtail_reserve`; all three are gone since
  D44). It is removed,
```
4. Insert directly after the line `  when it is bracket-mounted (T1-38).`:
```
  **Wide, flush, clearance everywhere (D44, rev 16 — user decisions 2026-09-28).** Root width
  **65 mm** (`MCC_RAIL_ROOT_W`, now the primary constant; the mouth is derived) at
  `MCC_RAIL_Y = −23.5` — as close to the device's centre of mass (`y_dev_c ≈ −30.8`) as the side-bolt
  web allows (sill edge 3.4 mm clear on the tightest SKU, W = 158.80). The male carries **no
  pedestal**: male-local = female-local, and the case's exterior floor rests **flush** on the bracket
  plate — the joint's only designed bearing face (on a TV-mounted bracket the gravity-side flank also
  bears, R41). Every other face keeps **≥ `MCC_RAIL_MATE_CLR` = 0.5 mm**: normal to the flanks
  (`MCC_RAIL_CLR_HORIZ` = 0.577 horizontal) and at the roof (the male is `MCC_RAIL_MALE_H` = 3.5 tall
  under the 4.0 groove, and the latch notch runs the full depth over the nub) — **T1-62**. The D34
  latch is the lock; its plate window also clears the nub. The Fishtail and case-insert reservations
  are retired, and D19's exemption with them; the opt-in insert and the rail are mutually exclusive
  (**T1-63**). Printing: the groove roof is a ~66 mm bridge in the base's print pose — a sanctioned
  exception to §5's 10 mm span rule, forced by the width, judged by the slicer gate and the
  `rail-latch` coupon (R40, M15).
```

**G3 §9 prose.** Insert immediately before the line beginning `Full table with sources: `:
```
**Rev 16 adds T1-62** (rail clearances: `MCC_RAIL_CLR_HORIZ·sin(flank) ≥ MCC_RAIL_MATE_CLR` and
`MCC_RAIL_DEPTH − MCC_RAIL_MALE_H ≥ MCC_RAIL_MATE_CLR`, D44) and **T1-63** (`tripod_insert` and the rail
are mutually exclusive, D44). **The next free id is T1-64.**
```

**G4 §11 R24.** Insert directly after `  from assumed into measured. **Do not print a full-size bracket before that coupon is pulled.**`:
```
**Refined by D44 (rev 16, 2026-09-28).** The rail now sits at `−23.5` with a 65 mm root, so its band
(`y ∈ [−56, 9]`) spans most of the device's own width: the roll moment this risk describes is carried by
a much wider base, and the case's mass sits over the rail band rather than beside it. The
`case_tripod_insert`/`fishtail_reserve` arithmetic above is retired with those rows, and the "clears the
splitter bay by 9.6 mm (compact)" figure was wrong — see D45. What remains is the clearance-induced play
(R41) and the physical check (M15).
```

**G5 §11 new risks.** Insert directly after C's line `  reverses D40 and goes back to the user.` (the last line of R39), with a blank line before:
```

**R40 — the wide groove's roof is a ~66 mm bridge, and the +X wall gets a 66 mm notch. NEW 2026-09-28
(rev 16, D44).** The base prints open-side-up, so the groove (cut up into the exterior floor) prints
mouth-down and its roof is a flat bridge across the root width plus clearance
(`MCC_RAIL_ROOT_W + 2·MCC_RAIL_CLR_HORIZ` ≈ 66.2 mm, was ≈ 15 mm) — far past §5's 10 mm span rule, and
forced by the user's width decision (no roof shape fits 3 mm of residual floor).
- **Sag eats the roof clearance.** A sagging bridge drops toward the male's flat top, and the 0.5 mm roof
  gap is the only margin. The `rail-latch` coupon's groove half prints in the same pose (D46 fix) and is
  the gate (M15). If the roof sags into the gap, **raise `MCC_RAIL_ROOF_CLR`** (the male gets shorter)
  — never narrow the rail (user decision). The CI slicer gate reports floating regions and
  cantilevers, not sag.
- **The +X end wall is notched ≈ 66 × 4 mm at its foot**, where the groove runs out (D34 passage; was
  ≈ 15 mm). On the Plus family the ⌀38 fan aperture above it (z ≥ 6.5) leaves ~2.5 mm of wall between
  the two over ~38 mm. The 1 m drop requirement (CLAUDE.md) has no test yet for this edge; flagged, not
  blocking.

**R41 — clearance means play, and on a TV-mounted bracket a flank carries the weight. NEW 2026-09-28
(rev 16, D44).** With 0.5 mm normal clearance at 60° flanks the case has ≈ ±0.58 mm lateral and ≈ 1.0 mm
lift play before the dovetail engages. Lying flat, the floor-on-plate seat bears and the flanks float.
**Hung on a TV** (arch bracket, tv-bracket, the future vertical bracket) gravity acts along the case's
own Y. The lower flank bears — its 60° slope then pulls the case onto the plate with ~0.58 × its weight
— and all clearance collects on the other side. The out-of-plane moment tilts the case until the upper
lip engages: about 1° for 1 mm over a ~60 mm band. Acceptable (user decision), but the case can rattle
within those limits, and the D34 latch holds X only. Measure it on the coupon (M15) and on the first
bracket print. If it is objectionable the lever is `MCC_RAIL_MATE_CLR` — a **user** decision (D44), not
a developer tweak.

**R42 — a sandwiched printed bracket puts ASA in the TV wall-mount's clamp path. NEW 2026-09-28 (rev 16,
plan-D gate).** The user's vertical VESA-column bracket (Samsung 400 × 300, one 300 mm column) is clamped
between the TV and the TV's own wall mount by that mount's M8 screws (longer bolts). The screws'
preload then passes through the printed pads, and printed ASA creeps under sustained load
(`knowledge/components/fasteners-and-hardware.md:140`, stated for snap arms; the creep is the
material's). The wall mount's joint on that column would relax while the other column's does not — on
the joint that carries the TV. `tv-bracket.scad` already accepted a 6 mm ASA shim in the same kind of
position (`MCC_BRACKET_PLATE_T`, PLAN-ASSUMPTION 6 ratified in `layout-patch-wall.md` §17.5), but for VESA
100/200 TVs, not a VESA-400-class TV. **This is a user safety
decision, not an architect's** (the R26 pattern). The options are steel compression sleeves through the
pads plus steel spacers of the same length on the other column (recommended), or an explicit written
acceptance of ASA in the clamp path. The other column needs equal spacers either way, or the wall
mount's rails end up skewed. No vertical bracket is printed for use before this is decided (Q22).

**R43 — the case must fit between the TV and the wall, beside a wall mount nobody has measured, and it
can only slide on from one side. NEW 2026-09-28 (rev 16, plan-D gate).**
- **Space.** On the vertical bracket the case's lid top is `2·T + H` ≈ 73 mm off the TV back (T = 11
  after D44). All of it must fit inside the TV-to-wall gap, which the TV's wall mount (a rail on each
  column, a wall plate, possibly arms) also occupies.
- **Slide direction.** The case's groove is open at one end only (D34), and its patch wall must hang
  down. So the case always slides on from the bracket frame's +X side (right, seen from behind the TV),
  and it sweeps `L + slide_clear` ≈ 392 mm (Plus family) measured from its final −X edge.
- **Consequence.** Assume the mount's rails sit on both 400 mm-pitch columns and the case floor cannot
  pass over them. Then only one layout crosses no column: the +X column (seen from behind), with the
  case outboard and slid on from beyond it.
  - Plan D's default (−X column, case inboard) sweeps to ≈ 412 mm from its own column, which is past the
    other column at 400 mm.
  - Plan D's `COLUMN_SIDE` X-mirror would need a mirrored case, which does not exist.
  - A low, flat pad (height T, so the case floor at 2T clears a thin mount rail) could reopen the
    inboard layout.

Nothing in the repo describes the mount; **M20** decides.
```

**G6 §12 questions.** Insert directly after C's line `    thread-hold test.` (the last line of Q20):
```
21. **The rail lock — replace the D34 latch with Christopher's "DP48" lock? NEW 2026-09-28 (rev 16, D44)
    — needs the user.** The two DP48 STEP bodies received so far are identical base plates, with neither
    a dovetail nor a lock; the lock bodies are missing. Until they arrive and are analysed, the adapted
    D34 latch is the shipped lock (plan A §6 is informational only). Also open:
    - Does "tool-less, no thumbscrews" rule out a key/lever/pin actuator, or only screwed fasteners?
    - Should the groove's closed −X end (the D34 axial end stop, a contact face at full mate) also keep
      0.5 mm, leaving X to the lock alone? Rev 16 keeps it as a stop.
22. **Plan D (vertical VESA-column bracket) — sandwich decisions. NEW 2026-09-28 (rev 16) — needs the
    user.**
    (a) R42: steel compression sleeves plus steel spacers on the other column (recommended), or accept
    ASA in the wall mount's clamp path?
    (b) R43/M20: with the mount's rails on both columns, only one layout works — unless a low, flat pad
    lets the case floor pass over those rails. That layout is the +X column (seen from behind the TV:
    the right-hand one, i.e. the TV's left seen from the front), with the case outboard, slid on from
    the TV's edge side. Is that acceptable? And what are the column-to-TV-edge distance and the
    TV-to-wall gap?
    (c) The arch bracket is a **direct** mount by user decision (#47: its top VESA holes must not also
    carry another mount). If the Samsung's wall mount uses all four holes, the arch cannot be used while
    that mount is on the TV — keep the arch direct-only, or give it a sandwich mode too?
    (d) Open a GitHub issue for plan D (`ticket-source.md`).
```

**G7 §12 measurement list.**
1. Replace the whole row beginning `| M7 | Magewell Fishtail M4 hole pitch |` with:
```
| ~~M7~~ | ~~Magewell Fishtail M4 hole pitch~~ | **Retired rev 16 (D44):** the Fishtail reservation is dropped | — |
```
2. Replace the whole row beginning `| **M15** |` with:
```
| **M15** | **Print `models/coupons/rail-latch` (D46 fix: groove half standing on the bed, groove open) and test it:** (a) slide feel and play at `MCC_RAIL_MATE_CLR` = 0.5 (expect ≈ ±0.6 mm lateral, ≈ 1 mm lift — R41); (b) **groove-roof sag** on the groove half — roof height at mid-width vs. 4.0 mm, and the rail's 3.5 mm top must not touch it (R40); (c) the latch arm flexes freely (nub not fused to the plate), clicks at full insertion, and the axial pull-off at disengage meets **≥ 30 N** (`assumed`) | R24/R40/R41 — every `MCC_RAIL_*` figure is `assumed` except the user-decided width and clearance. (b) decides `MCC_RAIL_ROOF_CLR`; (c) tunes `MCC_RAIL_LATCH_ENGAGE`/`_RAMP_OUT`. **"Coupons before cases" applies to brackets too — no full-size bracket prints before this** | User, with a luggage scale and calipers |
```
3. Insert directly after the row beginning `| **M19** |`:
```
| **M20** | **The user's TV and its wall mount, for the vertical VESA-column bracket (plan D):** the TV model, its VESA pattern (400 × 300?) and M8 thread depth; the wall mount's model, its TV-side rail/plate width and thickness at the column, the TV-back-to-wall standoff, and the footprint and depth of its wall plate and any arms within 250 mm of the column on both sides | R42/R43 — decides inboard vs. outboard reach, whether the ≈ 73 mm case stack fits, the spacer/sleeve length and the M8 bolt length. Blocks plan D's re-plan, not A | User, with the TV and mount in hand |
```
4. Insert directly after the numbering-note line ending `and are not repeated here. **Rev 15** adds M19.`:
```
> **Rev 16** retires M7 (D44) and adds M20 (plan-D gate).
```

**G8 §13 deviations log.** Insert directly after the row beginning `| **D43** |`. Each row is one line:
```
| **D44** | 2026-09-28 | §6 floor rule / D-15 rail (rev 9, D34): a 14.6 mm-root dovetail at `MCC_RAIL_Y = −20`, a 3 mm pedestal under the male (the case hovered 3 mm above the plate, carried by the flanks), `MCC_CLR_SLIDE` (0.26 mm normal) on the flanks, a 0 mm roof, and Fishtail + case-insert floor reservations | Not a code defect — **user decisions** after the external specialist's CAD review: much wider (root 60–70 mm), the case floor flush on the bracket, ≥ 0.5 mm on every non-bearing face, drop the Fishtail reservation (and with it the insert reservation the wide rail now covers) | The joint's seat, stiffness and clearances are what the specialist reviews; the reservations blocked the width | **Done in rev 16 (plan A, `docs/plans/2026-09-28-wide-dovetail.md`, as amended by its architect verdict).** `MCC_RAIL_ROOT_W = 65` (primary; mouth derived), `MCC_RAIL_Y = −23.5`; male pedestal removed, `MCC_RAIL_MALE_H = 3.5`, `_mcc_rail_taper(h=)`; `MCC_RAIL_MATE_CLR = 0.5`, `MCC_RAIL_CLR_HORIZ`, `MCC_RAIL_ROOF_CLR`; latch notch at full depth; the female groove is no longer shifted −`MCC_EPS` (its roof sat 0.01 mm low); the latch window now clears the nub (without it the nub fuses to the plate); rows `case_tripod_insert`/`fishtail_reserve`, `floor_center`, `MCC_CASE_INSERT_KEEPOUT_D`, `MCC_FISHTAIL_BAND` and D19's exemption deleted; the opt-in insert is assert-guarded against the rail (T1-63 — chosen over full retirement because D35 kept the option); T1-62; arch bracket `ARCH_PLATE_T` 11, `CENTRE_W` 92, `LAP_RIB_GAP` 3, M3×12 (T1-51/55/57/60 re-derived — the plan's 78 mm centre failed T1-60 and its M3×10 failed T1-57); the mate check is `scripts/rail_fit.py`, updated. R40, R41, Q21; M15 rewritten; M7 retired |
| **D45** | 2026-09-28 | §6 reservation rule: a reserved bay clears every other feature; §11 R24 claimed the rail "clears the splitter bay by 9.6 mm (compact)" | `lib/mcc/mounts.scad:63-66` draws the rail sill over `x ∈ [−75, +75]`, while the compact family's reserved splitter bay spans `x ≤ −L/2 + MCC_WALL + 20` = −73.95 (L = 193.9) / −74.45 (L = 194.9) — the sill's closed end sits **0.55–1.05 mm inside the bay** for `z ∈ [3, 7]` over the bay's Y overlap. T1-17 (splitter vs. floor keep-outs) was never implemented | A splitter fitted to the reservation would be ~1 mm short of room at its foot. Pre-existing since rev 9; D44 widens the overlapping face but does not cause it | **Open — low severity, separate small ticket.** Either pull the sill's closed end back by the overlap on the compact family, or record the bay as 1 mm shorter; implement T1-17 as a floor-keep-out-vs-splitter-bay assert. Not in plan A |
| **D46** | 2026-09-28 | §9 Tier 4: a coupon tests the real geometry in the real print pose | `models/coupons/rail-latch.scad` fused the groove plinth ON the shared base plate with its groove mouth facing down into that plate: the groove was a sealed tunnel, so the rail could not be inserted without sawing the plinth off. The file's own comment ("sunk into its own top face") contradicted its code | M15 could not be performed, and after D44 this coupon is also the gate for the ~66 mm roof bridge (R40) | **Fixed in rev 16 (plan A):** the groove half stands directly on the bed, groove open, like the case floor; two snap-off strips beside the groove join the halves into one shell |
| **D47** | 2026-09-28 | #26 `tv-bracket.scad`: "sandwiched between a TV's own back panel and its existing wall/stand mount", with the case mated on the rail | The rail — and so the mated case, ≈ 211 × 166 mm, centred on the plate — is on the plate's mount-side face, the same face the wall/stand mount's TV-side plate or rails bolt onto at the VESA 100/200 holes (±50/±100), most of which lie under the case's footprint. D44 makes it strictly tighter (the case floor now rests on the plate) | The tv-bracket cannot carry a case while a VESA mount is attached at those holes | **Open — escalated to the user.** Pre-existing since #26. Options for a later ticket: offset the rail off the VESA pattern, restrict the tv-bracket to mounts whose interface clears the case footprint, or retire it in favour of the arch/vertical brackets. Not in plan A |
```

**G9 §14.**
1. Replace:
```
wall's inner face to the pad face plus a 3 mm central support web down to the floor. The floor keeps
only the case's own 1/4"-20 insert, VESA 75 + Fishtail M4, strap slots and the stacking profile — and
the stacking profile no longer has to dodge a lug.
```
with:
```
wall's inner face to the pad face plus a 3 mm central support web down to the floor. The floor keeps
only the wide mount-rail groove (D44), strap slots and the stacking profile — no insert, no VESA, no
Fishtail reservation — and the stacking profile no longer has to dodge a lug.
```
2. Replace:
```
**Floor.** VESA 75×75 and the case's own 1/4"-20 insert default to the case plan centre; `vesa_pos`
is a shell parameter so a colliding SKU can shift it; `mcc_floor_keepout()` asserts non-overlap. The
device-retention through-bolt is **no longer a floor feature** (D-09).
```
with:
```
**Floor.** The mount rail (D-15; 65 mm root at `y = −23.5`, flush seat, ≥ 0.5 mm clearance — D44),
strap slots, the splitter tie-down and the stacking profile; `mcc_floor_keepout()` asserts non-overlap.
VESA 75 × 75 (D-15), the Fishtail M4 band and the case-insert reservation (D44) are gone. The
device-retention through-bolt is **no longer a floor feature** (D-09).
```

## Appendix H — `.claude/knowledge/layout-patch-wall.md` (paste verbatim on the feature branch)

**H1 Header.** Insert immediately before C's line beginning `Status: **revision 15, 2026-09-28**`, followed by one blank line:
```
Status: **revision 16, 2026-09-28** (aligned with `architecture.md` rev 16 — D44, the wide, flush rail).
What changes here: **§7.1's floor keep-out table** — the case-insert and Fishtail rows are struck, and
the mount-rail row carries the new width, position and clearances; **§9** gains **T1-62** and **T1-63**;
**§10**'s D-15/D-16 rows carry D44's status. **No envelope figure moves on any SKU.** Rev-15 status
follows.
```

**H2 §7.1 floor keep-out table.** Replace these three rows, each in place:
- Row beginning `| Case 1/4"-20 **insert** (case → tripod/cheeseplate) |`:
```
| ~~Case 1/4"-20 **insert** (case → tripod/cheeseplate)~~ | ~~⌀20 disc at `floor_center`~~ | **STRUCK, rev 16 (D44, 2026-09-28).** The wide rail covers the floor centre; the reservation is dropped, and `floor_center` with it. The opt-in insert (`cfg["tripod_insert"]`, default false since D35) is allowed only with `["rail", false]` — T1-63 — and then has no keep-out row (nothing else is near the floor centre without the rail) |
```
- Row beginning `| **Mount rail (dovetail groove + sill)** |`:
```
| **Mount rail (dovetail groove + sill)** | **`[L/2 + MCC_RAIL_LEN/2] × MCC_RAIL_ROOT_W` rect — the groove from its closed −X end at −75 out through the +X wall (D34), 65 wide — at `y = MCC_RAIL_Y = −23.5`, label `"mount_rail"`** | **Rev 9 (D-15), widened rev 16 (D44).** Root 65 mm (user range 60–70), mouth derived (60.38); sill `ROOT_W + 2·MCC_RAIL_SILL_SIDE_W` = 71 wide, `y ∈ [−59.0, 12.0]`. Binding neighbour: the side-bolt web — the sill edge is 3.4 mm clear of the web top (−62.4) on the tightest SKU (W = 158.80), and the keep-out row is 4.4 mm beyond `MCC_FLOOR_FEATURE_EDGE_MIN` (D16); max root at this `y` ≈ 68.9. Z: groove `[0, 4]`, sill `[0, 7]` (T1-38 unchanged: 3.0 mm over the groove); the male is `MCC_RAIL_MALE_H` = 3.5 tall and flush on the plate, with ≥ 0.5 mm normal clearance on the flanks and at the roof (T1-62). The sill's closed end reaches 0.55–1.05 mm into the compact splitter bay (D45, open) |
```
- Row beginning `| Fishtail M4 pair |`:
```
| ~~Fishtail M4 pair~~ | ~~60 × 20 band at `floor_center`~~ | **STRUCK, rev 16 (D44, user decision 2026-09-28: "not needed").** M7 retired; D19's exemption retired with the pair |
```

**H3 §9.** Insert directly after C's row beginning `| **T1-61** |`:
```
| **T1-62** | *the rail joint keeps its clearance* — `MCC_RAIL_CLR_HORIZ·sin(MCC_RAIL_FLANK_ANGLE) ≥ MCC_RAIL_MATE_CLR` (0.5, normal to the flanks) **and** `MCC_RAIL_DEPTH − MCC_RAIL_MALE_H ≥ MCC_RAIL_MATE_CLR` (roof) | **new rev 16** (D44, user decision: ≥ 0.5 mm on every non-bearing face). Evaluated in `mcc_rail_female_cut()` and in `tests/test_rail.scad`. The geometry-level mate (no interference at full insertion, the end stop works, only the nub overlaps while sliding) is checked by `scripts/rail_fit.py` against a real base |
| **T1-63** | *the opt-in case insert and the rail are mutually exclusive* — `!(cfg["tripod_insert"] && rail_on)`, with `"rail"` defaulting to true | **new rev 16** (D44). The wide rail covers the floor centre the insert boss needs, and its keep-out row is gone. Evaluated in `mcc_cradle()`. **The next free id is T1-64** |
```

**H4 §10.**
1. In the D-15 row, replace its last cell:
```
| **fixed** in intent; every `MCC_RAIL_*` figure is `assumed` until coupon **M15** |
```
   with:
```
| **fixed** in intent; **widened, flush and ≥ 0.5 mm-clearance since D44 (rev 16)**; every `MCC_RAIL_*` figure except the user-decided width/clearance is `assumed` until coupon **M15** |
```
2. In the D-16 row, replace `| **fixed**; brings **T1-41** with it |` with:
```
| **SUPERSEDED**: default `false` since D35 (2026-09-28); since D44 the insert needs `["rail", false]` (T1-63) and has no floor reservation. T1-41 still applies when it is fitted |
```

---

## Amendment 1 (2026-09-28, user decisions)

The coordinator relayed the user's answers to D47, Q21 and Q22. **Where this amendment and anything above disagree, the amendment wins.** Nothing above is rewritten.

### AM-1 The decisions

1. **D47: retire `tv-bracket`** (the VESA 100/200 sandwich plate, #26) — "phase the bracket out".
   - Only the arch bracket and the planned vertical bracket remain.
   - The retirement is folded into plan A (AM-3): `tv-bracket.scad` is deleted, never edited first.
2. **Q21, end stop.** The groove's closed −X end stays a contact face (the D34 end stop), as rev 16 has it.
   - Q21 stays open **for the lock only**.
   - The user points out that the DP48 bodies do carry a dovetail and a detent: two 0.8 mm bumps into recesses.
   - A new analysis is running. It stacks after A, as sequenced.
3. **Q22** (plan-D scope):
   - (a) **ASA is accepted** in the wall mount's clamp path; no steel sleeves. Recorded as "user decision 2026-09-28, in chat: accept ASA".
   - (b) Layout: the **+X column** (seen from behind the TV), **case outboard**, slid on from the TV's edge side.
   - (c) The **arch bracket gets a sandwich mode**. This belongs to plan D's re-plan, not to A.
   - (d) GitHub issue: the user has been asked.
   - M20 is still open.

### AM-2 Changes to the binding changes above

- **B8 and Appendix D.2 are void.** Do not edit `tv-bracket.scad`; delete it (AM-3).
- **B11.**
  - Drop `brackets/tv-bracket` from the update list.
  - `tests/golden/brackets/tv-bracket.json` is **deleted** (AM-3), not updated. Deletion is the only allowed change to that file.
- **DO NOT.** "Do not fix … D47 … in this PR" is reversed: this PR closes D47. D45 stays out of scope.
- **Appendix D.1 item 3** uses this text instead, because `MCC_BRACKET_PLATE_T` no longer exists:
```openscad
ARCH_PLATE_T = 11.0; // mm. derived minimum (Z-stack derivation above: T>=11 for the slide-on sweep to
                      // clear the pad once D44 removed the rail's 3 mm pedestal -- was 8) and
                      // independently justified for torsion stiffness (plan §2). A cantilevered BEAM,
                      // not a sandwiched shim.
```
- **Appendix F.**
  - Step 5 becomes "D.1 and D.1b, then AM-3 items 1–7".
  - Step 11's command becomes:
```
python scripts/build.py golden coupons/rail-latch brackets/arch-tv-bracket pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio --update
```
  - Step 15 also covers AM-3 items 9–16.
- **B14.** The banner reads "(B1–B17 and Amendment 1)".

### AM-3 Retiring `tv-bracket` — the complete list

**Code, tests and build** (Appendix F step 5):

1. `git rm models/brackets/tv-bracket.scad`.
2. `git rm tests/golden/brackets/tv-bracket.json`. `build.py golden` has no orphan check, so a golden left behind would never be noticed.
3. `lib/mcc/constants.scad`:
   - **Delete** `MCC_BRACKET_PLATE_T`: the four lines below and the blank line after them. After item 1 and D.1 item 3 nothing uses it. Its only consumers in `lib/`, `models/` and `tests/` were `tv-bracket.scad` and the arch `ARCH_PLATE_T` comment.
```
MCC_BRACKET_PLATE_T = 6.0; // TV-bracket sandwich-plate thickness, mm. assumed (PLAN-ASSUMPTION 6,
                           // layout-patch-wall.md §17.5 — RATIFIED for #26: sandwiched flat
                           // against a TV, the plate is a shim, not a beam, so 6 mm is not
                           // re-derived from the rib rule below).
```
   - **Replace** the six text lines of the section header, between its two separator lines:
```
// Section: Mounting brackets (issue #26 — VESA sandwich plate carrying the mount rail; §17.2's
// R4/R5/D22 apply here too: the rib rule is stated once, generic, not duplicated per bracket)
// docs/plans/2026-09-09-mount-rail-and-brackets.md §3. `MCC_M8_CLR_D` (above, in the fastener
// section — a generic clearance size, not bracket-specific) is the only other new constant #26
// needs; VESA hole *positions* (±50/±100) are plan-fixed geometry, not calibrated constants, so
// they stay as literals inside tv-bracket.scad per the plan's own §3.1 table.
```
     with:
```
// Section: Mounting brackets (models/brackets/*.scad). Bracket-own geometry stays inside each bracket
// file; only cross-cutting rules live here (§17.2's R4/R5/D22: the rib rule is stated once, generic,
// not duplicated per bracket). The VESA 100/200 sandwich plate that opened this section
// (tv-bracket.scad, #26) was retired in rev 16, with MCC_BRACKET_PLATE_T (architecture.md D47).
```
   - In the `MCC_RIB_HEIGHT_RATIO_MAX` comment, replace:
```
                                 // (D22, architecture.md §13/§17.2) — the bracket's own cross ribs
                                 // are exactly the floor-standing stiffening fin this rule targets;
```
     with:
```
                                 // (D22, architecture.md §13/§17.2) — bracket ribs (the arch arm's
                                 // edge ribs) are exactly the standing stiffening fin this rule targets;
```
   - Keep `MCC_M8_CLR_D` (arch pads), `MCC_M4_CLR_D` (`fasteners.scad`) and `MCC_RIB_HEIGHT_RATIO_MAX` (arch).
4. `lib/mcc/rail.scad`, `mcc_rail_male_window()` doc: `(tv-bracket, arch-tv-bracket centre, rail-latch` → `(arch-tv-bracket centre, rail-latch`.
5. `models/brackets/arch-tv-bracket.scad` — comments only, so nothing points at a deleted file.
   - Single-line substitutions:
     - `//   models/brackets/tv-bracket.scad (#26); consumes` → `//   the retired tv-bracket.scad (#26, D47); consumes`
     - `unlike tv-bracket.scad's` → `unlike the retired tv-bracket.scad's`
     - `the tv-bracket.scad convention; nothing here is` → `the models/brackets convention; nothing here is`
     - `(+X, per tv-bracket's rotate([0,0,180]) convention)` → `(+X, per this file's rotate([0,0,180]) rail placement)`
     - `-- identical call to tv-bracket.scad's, just lifted` → `-- the standard rotate([0,0,180]) rail call, lifted`
   - Replace these two lines:
```
                       // pattern (https://en.wikipedia.org/wiki/VESA_mount, same citation as
                       // tv-bracket.scad:98-100).
```
     with:
```
                       // pattern (https://en.wikipedia.org/wiki/VESA_mount).
```
   - Replace these two lines:
```
RIB_T = MCC_WALL; // = 3.0. <= 0.6 x ARCH_PLATE_T (fdm-rugged-enclosure-guidelines.md:67), same
                   // choice as tv-bracket.scad:117.
```
     with:
```
RIB_T = MCC_WALL; // = 3.0. <= 0.6 x ARCH_PLATE_T (fdm-rugged-enclosure-guidelines.md:67).
```
   - Replace these two lines:
```
            mcc_ghost(dev, show = true); // force-shown regardless of MCC_SHOW_GHOST, same
                                          // precedent as tv-bracket.scad's own "assembly" branch.
```
     with:
```
            mcc_ghost(dev, show = true); // force-shown regardless of MCC_SHOW_GHOST (preview only).
```
   - Afterwards a grep of the file for `tv-bracket.scad` must show only the two "retired" mentions.
6. `scripts/build.py`, `discover_brackets()` docstring: `(VESA sandwich bracket, arch TV bracket, truss` → `(arch TV bracket, VESA-column bracket, truss`.
7. `scripts/package_release.py` (comments only):
   - `"brackets/tv-bracket" -> "tv-bracket"` → `"brackets/arch-tv-bracket" -> "arch-tv-bracket"`.
   - Replace:
```
        # coupons; the bracket's own PLAN-ASSUMPTION 5/6 retention-force and plate-thickness
        # figures, layout-patch-wall.md §17.5, are likewise un-coupon-verified) — always flag.
```
     with:
```
        # coupons; the brackets' rail retention force (M15) and TV measurements (M18) are likewise
        # unmeasured) — always flag.
```
8. **Checked; no change needed:**
   - `.github/workflows/*`, and the logic in `build.py` and `package_release.py`: bracket discovery is generic, and CI's six part groups rebalance themselves.
   - `tests/golden/README.md`: it never listed the tv-bracket.
   - **Nothing has to replace the tv-bracket as the male-rail consumer under test.** No test or script used it: `tests/test_rail.scad` and `scripts/rail_fit.py` call a bare `mcc_rail_male()`. The plate-window + rail pattern stays covered by `tests/test_arch_tv_bracket.scad` (the arch centre, 3 `TV_TOP_CLEAR` values), by the `rail-latch` coupon (render/check/golden/slicer, and physically M15) and by `test_rail.scad`'s `plate_t = 6` call.
   - The tv-bracket's patch-wall-down `assembly` preview is superseded by the arch's `assembly` / `assembly_sweep` previews.

**Docs** (Appendix F step 15):

9. `BOM.md`, section "Mounting brackets":
   - Delete from the paragraph that begins "tv-bracket.scad (issue #26) is a VESA 100×100/200×200 sandwich plate" through the paragraph that ends "form for the retention target this depends on)." That removes the intro, the 4-row table and the paragraph after it. Put this in their place:
```
The VESA 100×100/200×200 sandwich plate `tv-bracket.scad` (issue #26) was **retired** on 2026-09-28
(user decision, `.claude/knowledge/architecture.md` §13 D47): a mated case covered the VESA mount
interface it was sandwiched to. The case side of every bracket needs no hardware: the rail/latch
interface is tool-less (see `models/coupons/rail-latch.scad` for the retention target it depends on).
```
   - In the arch "Deviations from the issue's own text" paragraph, fix two figures A missed:
     - `blind in the 8 mm arm` → `blind in the 11 mm arm`
     - `**centre plate stands 8 mm off the TV**` → `**centre plate stands 11 mm off the TV** (D44)`
10. `models/brackets/README.md`:
   - `Flat, single-part plates that carry` → `Flat printed plates that carry`.
   - Delete the "What each bracket carries" table row whose first cell is tv-bracket.scad. Directly after that table, insert:
```
The VESA 100/200 sandwich plate `tv-bracket.scad` (#26) was retired on 2026-09-28 (architecture.md
§13 D47). A vertical VESA-column bracket (Samsung 400 × 300, one column) is planned, and the arch
bracket gains a sandwich mode with it.
```
   - Replace:
```
Unlike `tv-bracket.scad`, this bracket carries **no VESA plate** — it mounts directly on a TV's
```
     with:
```
This bracket carries **no VESA plate** — it mounts directly on a TV's
```
   - Replace:
```
- **Orientation**: same convention as `tv-bracket` (patch wall down); the **arch points up** (see
```
     with:
```
- **Orientation**: patch wall down (see "Orientation" below); the **arch points up** (see
```
   - Replace:
```
  `centre` — **flat (TV-side) face on the bed**, rail up (same convention as `tv-bracket`/
  `rail-latch`), no supports.
```
     with:
```
  `centre` — **flat (TV-side) face on the bed**, rail up (same convention as the `rail-latch`
  coupon), no supports.
```
   - Replace the whole "## Orientation (issue #26's own acceptance criterion)" section, heading through its "Open point, not blocking" paragraph, with:
```
## Orientation (issue #26's acceptance criterion, kept for every bracket)

Every bracket places the rail with `rotate([0,0,180])`, so a case slid onto it hangs with its patch
(cable) wall facing **down** when the bracket is mounted as its own section above documents (the arch:
arch up, UP arrow). Verify it with the bracket file's `part == "assembly"` preview (a ghost case mated
onto the rail) rather than trusting the transform algebra alone; `.claude/skills/print-check/SKILL.md`
carries the one-line go/no-go version.
```
   - Render block: `render brackets/tv-bracket --format both` → `render brackets/arch-tv-bracket --format both`.
   - "Orientation (Bambu Studio)" table: delete the row whose first cell is tv-bracket, and replace the arch `centre` row with:
```
| `arch-tv-bracket` `centre` | **Flat (TV-side, standoff) face down on the bed, rail up** — the same rail orientation as the `rail-latch` coupon. | The dovetail taper and the latch nub's 2 mm ledge are the only overhangs (D34, D44); the latch arm's leg stands on the bed through the plate window; the tabs print flat with the body. |
```
11. `scripts/README.md`: in the command table, the cell reading render brackets/tv-bracket (in code font) becomes render brackets/arch-tv-bracket (in code font).
12. `.claude/skills/print-check/SKILL.md` §3:
   - Delete the table row for models/brackets/tv-bracket.scad.
   - Replace the first line of the span rule (it also records R40's sanctioned exception, which A should have carried):
```
No unsupported span over **10 mm** anywhere (the general shell rule, architecture.md §5) — check any
```
     with:
```
No unsupported span over **10 mm** anywhere (the general shell rule, architecture.md §5), with one
sanctioned exception: the mount-rail groove roof in every base, a ≈ 66 mm bridge (architecture.md R40,
D44), which the `rail-latch` coupon (M15) judges. Check any
```
13. `.claude/knowledge/session-resume.md` is the teamlead's file; the developer may apply this in the same PR. In the "Print-ready exports" row:
   - `**all 36 parts slice with zero Bambu Studio warnings**` → `**every part slices with zero Bambu Studio warnings**` (C and A both change the count);
   - `tv-bracket ribs off (D31)` → `tv-bracket retired (D47)`.
14. `CHANGELOG.md`: AM-6.
15. `CLAUDE.md`: AM-5.
16. `.claude/knowledge/architecture.md`: AM-4. Historical text stays as it is: `layout-patch-wall.md` §17, `docs/plans/**`, the old CHANGELOG entries, and architecture.md's D31/D28 rows and rev notes.

### AM-4 `architecture.md` — use these instead of the matching Appendix G blocks

Everything else in Appendix G stands.

**G1, whole header paragraph:**
```
**Revision 16, 2026-09-28 (wide, flush mount rail — D44; `tv-bracket` retired — D47; plan
`docs/plans/2026-09-28-wide-dovetail.md`).** User decisions after the external specialist's CAD review:
the dovetail stays and becomes **much wider** (65 mm root, `MCC_RAIL_Y` = −23.5, near the device's
centre of mass); the case's exterior floor sits **flush** on the bracket (the male's 3 mm pedestal is
gone — the floor-on-plate seat is the joint's only designed bearing face; the groove's closed −X end
stays the axial end stop); **≥ 0.5 mm clearance on every non-bearing face** (flanks and roof); and the
Magewell-Fishtail M4 and 1/4"-20 insert floor reservations are **dropped** (the rail covers the floor
centre; the opt-in insert now needs `["rail", false]`, **T1-63**). The D34 latch stays the lock, adapted
— its plate window now also clears the nub, which would otherwise fuse to the plate once the pedestal is
gone. The VESA 100/200 **`tv-bracket` is retired** (user decision: phase it out — **D47** closed); the
arch bracket (horizontal) and the planned vertical VESA-column bracket remain. New: **T1-62** (rail
clearances), **R40** (the ~66 mm groove-roof bridge and the +X-wall notch), **R41** (joint play; bearing
faces on a TV-mounted bracket), **Q21** (the DP48 lock); M15 rewritten, M7 retired; §13 **D44–D47**.
Cascade: arch-bracket plates 8 → 11 mm, centre 40 → 92 mm, lap screws M3×12. **No case envelope figure
moves.** Also recorded here, because it has no branch yet: the gate of plan D, the vertical VESA-400 ×
300 column bracket — **rejected for re-plan** (hub topology and a fresh sibling file approved as the
direction) — with the user's answers: printed ASA accepted in the wall mount's clamp path (**R42**),
the case outboard of the +X column (**R43**), and a sandwich mode for the arch bracket in the
re-plan's scope (**Q22**); **M20** (the TV and wall-mount measurements) is open.
```

**G5, R41:** replace `**Hung on a TV** (arch bracket, tv-bracket, the future vertical bracket)` with `**Hung on a TV** (the arch bracket, the planned vertical bracket)`.

**G5, R42, whole paragraph:**
```
**R42 — a sandwiched printed bracket puts ASA in the TV wall-mount's clamp path. NEW 2026-09-28 (rev 16,
plan-D gate) — ACCEPTED by the user.** In sandwich mode (the vertical VESA-column bracket, and the arch
bracket's planned sandwich mode) the bracket's pads are clamped between the TV and the TV's own wall
mount by that mount's M8 screws, so the screws' preload passes through printed ASA, which creeps under
sustained load (`knowledge/components/fasteners-and-hardware.md:140`, stated for snap arms; the creep is
the material's). **User decision 2026-09-28, in chat: accept ASA** — no steel compression sleeves.
What follows from it:
- **Equal-height spacers go under every VESA hole the bracket does not occupy**, so the mount's rails
  stay coplanar — the other column's two holes (vertical bracket), the bottom row's two holes (arch
  sandwich mode). They should be **printed ASA too**, with the same height and bearing area as the
  bracket's pads, so both sides creep alike and the rails stay parallel as the joints relax; a steel
  spacer on one side and ASA on the other would relax unevenly.
- Pads and spacers are flat clamp faces with an M8 clearance hole — no counterbore, no washer seat —
  printed solid (100 % infill; the re-plan confirms the export can carry it), hole axis vertical.
- **Recommended practice, not a gate:** re-check the M8 preload 24–48 h after installation and at every
  rig-in; ASA relaxation shows up as lost preload, not as visible damage.
- M8 length, the same on all four holes = the mount's thickness at the hole + the pad/spacer height +
  the usable TV thread depth − ≥ 1 mm, rounded **down** (M20). Too long can crack the TV's back panel.
```

**G5, R43, whole block:**
```
**R43 — the vertical bracket's case must fit between the TV and the wall, and it slides on from one
side only. NEW 2026-09-28 (rev 16, plan-D gate); layout decided by the user.** The case's groove is open
at one end only (D34) and its patch wall hangs down, so a case always slides on from the bracket frame's
+X side (right, seen from behind the TV), sweeping `L + slide_clear` ≈ 392 mm (Plus family) from its
final −X edge. With the TV's wall mount on both 400 mm-pitch columns, a sweep that crosses a column
hits that column's mount rail — and the bolt head on it — unless the case floor clears both in Z.
**User decision 2026-09-28: the vertical bracket goes on the +X column (seen from behind the TV), case
outboard, slid on from the TV's edge side** — the one layout whose sweep crosses no column. Open (M20):
- the case stack (lid at `2·T + H` ≈ 73 mm off the TV back, T = 11, plus any pad height the sandwich
  adds) must fit the TV-to-wall gap beside the column, clear of the mount's wall plate and arms;
- the sweep's start position reaches ≈ 412 mm outboard of the column: the TV must be that wide there, or
  the space beside the TV free, for the case to be offered up;
- `REACH_KEEPOUT` must clear the mount's rail band at the column.
**The arch bracket's sandwich mode** has exactly the problem the vertical layout avoids: its +X sweep
(≈ 181 mm past its final position, to ≈ 287 mm from the arch centre) crosses the right-hand column at
200 mm. It is feasible only if the case floor clears that column's mount rail and bolt head in Z (with
flat pads at the arm top: `2T ≥ T + t_rail + k_head + ARCH_SWEEP_CLR`, where `t_rail` is the mount
rail's thickness and `k_head` the bolt-head height, both from M20), and its ≈ 73 mm stack sits between
the columns, where a wall plate usually is. Plan D's re-plan owns both.
```

**G6, items 21 and 22:**
```
21. **The rail lock — DP48. NEW 2026-09-28 (rev 16, D44) — open, analysis running.** The user pointed
    out that the two DP48 bodies do carry a dovetail and a detent (two 0.8 mm bumps into recesses, per
    the user); a new analysis is running and, once gated, stacks after plan A. Until then the adapted D34
    latch is the shipped lock (plan A §6 is informational only). Still open with it: does "tool-less, no
    thumbscrews" rule out a key/lever/pin actuator, or only screwed fasteners? *(Answered 2026-09-28:
    the groove's closed −X end stays the axial end stop, a contact face, as rev 16 has it.)*
22. **Plan D (vertical VESA-column bracket) — sandwich decisions. NEW 2026-09-28 (rev 16).** Answers
    (user, 2026-09-28):
    (a) R42: **accept ASA** in the wall mount's clamp path, no steel sleeves (in chat: "accept ASA");
    printed-ASA spacers of equal height under the unoccupied holes.
    (b) R43: **the +X column (seen from behind the TV), case outboard, slid on from the TV's edge side.**
    (c) **The arch bracket gets a sandwich mode too** — in the plan-D re-plan's scope, not plan A; R43
    records its slide-path and stack constraints.
    (d) GitHub issue for plan D: **open — the user has been asked.**
```

**G7, M20 row:**
```
| **M20** | **The user's TV and its wall mount, for the sandwiched brackets (plan D: the vertical bracket and the arch's sandwich mode):** the TV model, its VESA pattern (400 × 300?) and usable M8 thread depth; the wall mount's model, its TV-side rail width and thickness at each hole, the bolt-head height, the TV-back-to-wall standoff, and the footprint and depth of its wall plate and any arms within 450 mm outboard of the +X column and between the columns | R42/R43 — decides whether the ≈ 73 mm case stack fits beside the +X column, `REACH_KEEPOUT` against the mount's rail, the arch sandwich mode's Z clearance over the right-hand column, and the pad/spacer height and M8 bolt length. Blocks plan D's re-plan, not A | User, with the TV and mount in hand — **open, the user has been asked** |
```

**G8, D47 row:**
```
| **D47** | 2026-09-28 | #26 `tv-bracket.scad`: "sandwiched between a TV's own back panel and its existing wall/stand mount", with the case mated on the rail | The rail — and so the mated case, ≈ 211 × 166 mm, centred on the plate — is on the plate's mount-side face, the same face the wall/stand mount's TV-side plate or rails bolt onto at the VESA 100/200 holes (±50/±100), most of which lie under the case's footprint. D44 makes it strictly tighter (the case floor now rests on the plate) | The tv-bracket cannot carry a case while a VESA mount is attached at those holes | **Closed — retired (user decision 2026-09-28: phase the bracket out).** Removed in rev 16 with plan A (its verdict's Amendment 1): `models/brackets/tv-bracket.scad`, its golden, `MCC_BRACKET_PLATE_T` and every doc/skill reference. The arch bracket (horizontal) and the planned vertical VESA-column bracket remain; the arch sandwich mode's sweep past a mount rail is R43 |
```

### AM-5 `CLAUDE.md` — replaces E4.2 and adds a Fixed-decisions bullet

E4.1 stands. In "Current status", replace:
```
Studio project; every part (8 cases as base + lid, coupons, `tv-bracket`, `arch-tv-bracket` arm ×2
```
with:
```
Studio project; every part (8 cases as base + lid, coupons, `arch-tv-bracket` arm ×2
```
Replace:
```
floor-pad island (D37), boss-wide lid-boss webs (D38), `tv-bracket` has no ribs (D31), the rail
```
with:
```
floor-pad island (D37), boss-wide lid-boss webs (D38), the rail
```
Instead of E4.2, replace:
```
a plain Ø2.5 tap-drill bore instead of a printed thread (D41) — are in architecture.md §13.
```
with:
```
a plain Ø2.5 tap-drill bore instead of a printed thread (D41), the wide flush mount rail (D44), the retired `tv-bracket` (D47) — are in architecture.md §13.
```
In "Fixed decisions", insert directly after the line:
```
  the default BOM** — end zones are sized for straight plugs, measured with the `depth-mockup` coupon.
```
this bullet:
```
- **Mount brackets** (user decisions 2026-09-28): the **arch bracket** is the horizontal option (top
  VESA row; it mounts directly today and gains a sandwich mode), and a **vertical VESA-column
  bracket** is planned (Samsung 400 × 300, one column; the case sits outboard of the right-hand column
  seen from behind the TV). In sandwich mode a bracket is clamped between the TV and the TV's own
  wall mount on longer M8 bolts, and **printed ASA in that clamp path is accepted** (architecture.md
  §11 R42). The VESA 100/200 `tv-bracket` is **retired** (D47) — do not reintroduce it.
```

### AM-6 `CHANGELOG.md`

Insert directly after E5's last line:
```
  case floor (it used to be sealed by the shared base plate, D46).
```
this block (starting with a blank line):
```

### Removed (2026-09-28)

- **`tv-bracket`** — the VESA 100/200 sandwich plate (issue #26) — is retired (architecture.md D47,
  user decision 2026-09-28): a mated case covered the VESA mount interface it was sandwiched to. The
  arch bracket stays as the horizontal option; a vertical VESA-column bracket is planned.
  `MCC_BRACKET_PLATE_T` goes with it.
```

### AM-7 Sequencing

- Unchanged: C → A (now including AM-3) → D.
- The DP48 lock analysis stacks after A (Q21).
- Plan D's rev 2 now also covers the arch sandwich mode. The D verdict carries a matching Amendment 1.

---

## Amendment 2 (2026-09-28): two fixes found while prototyping plan F

Binding on A's branch (`feature/wide-dovetail`). **This amendment wins over anything above.** A must be CI-green on its own. The anchors below are the text as it now stands on A's branch.

### AM2-1 — The rail-latch coupon fails `build.py check` (8 parts)

**Cause.** D.3's two snap-off strips are flush with the long outer faces of the groove plinth and of the rail plate, at y = ±`footprint_d`/2. The union leaves zero-volume slivers on the bed plane, and `check` splits the coupon into separate parts.

**Fix.** Move the strips 1 mm in from those faces. These are exactly the lines plan F uses, so F's coupon rewrite keeps them unchanged. In `models/coupons/rail-latch.scad`, `_rail_latch_base()`:

1. Replace:
```
// snap-off strips join it to the groove half; they run along the groove half's outer edges, clear of
// the groove's open +X end.
```
   with:
```
// snap-off strips join it to the groove half, 1 mm in from the coupon's outer long edges and clear of
// the groove's open +X end. (Flush with those edges they left zero-volume slivers on the bed plane:
// `check` split the coupon into 8 parts.)
```
2. Replace:
```
            for (y0 = [-footprint_d / 2, footprint_d / 2 - STRIP_W])
```
   with:
```
            for (y0 = [-footprint_d / 2 + 1, footprint_d / 2 - 1 - STRIP_W])
```

**Nothing else in the coupon changes.** After the fix:
- run `build.py render coupons/rail-latch` and `check`: the coupon must be **1 part and watertight**;
- update its golden, which is already in B11's list;
- run `slicer-check coupons/rail-latch`: zero warnings.

**Stop condition.** If `check` still reports more than one part after this fix, stop and report the part count and where the extra parts are. Do not improvise further geometry. The latch window and leg are then the next suspects, and that is the architect's call.

### AM2-2 — R41 names the wrong flank

**Physics.** Hung patch-wall down, the case hangs on the rail's **upper** flank. That is rail-local −Y, which the brackets' `rotate([0,0,180])` turns to the top. The case's upper groove wall hooks over it like a French cleat (F2 §6.1). The lower flank could only push the case down.

So the "lower flank bears … tilts until the upper lip engages" sentences in R41 describe the wrong mechanism. The tipping moment is taken by the upper-flank hook together with the floor pressing on the plate below the rail.

**1. `.claude/knowledge/architecture.md`, §11 R41.** Replace these five lines:
```
**Hung on a TV** (the arch bracket, the planned vertical bracket) gravity acts along the case's
own Y. The lower flank bears — its 60° slope then pulls the case onto the plate with ~0.58 × its weight
— and all clearance collects on the other side. The out-of-plane moment tilts the case until the upper
lip engages: about 1° for 1 mm over a ~60 mm band. Acceptable (user decision), but the case can rattle
within those limits, and the D34 latch holds X only. Measure it on the coupon (M15) and on the first
```
with:
```
**Hung on a TV** (the arch bracket, the planned vertical bracket) gravity acts along the case's
own Y and the **upper flank bears** (rail-local −Y — the brackets' `rotate([0,0,180])` puts it on top):
the case's upper groove wall hooks over the rail's upper flank like a French cleat, loading it with
≈ 1.15 × the case's weight normal to the flank, and the flank's 60° slope pulls the case onto the plate
with ≈ 0.58 × its weight. The tipping moment of the case's offset centre of mass is taken by that hook
and by the floor pressing on the plate below the rail. All clearance collects at the lower flank
(≈ 1.15 mm horizontal), so gravity keeps the case seated; only a push against its weight lifts it off
the upper flank. Acceptable (user decision), and the D34 latch holds X only. Measure it on the coupon (M15) and on the first
```
   The phrase "and the D34 latch holds X only" is kept on purpose: plan F's R41 edit replaces exactly that phrase.

**2.** Same error, same fix, comments and prose only.
   - Replace `the gravity-side flank also` with `the upper flank (rail-local −Y) also`, once each, in:
     - `.claude/knowledge/architecture.md`, the §6 D44 paragraph;
     - `lib/mcc/constants.scad`, the "Rail clearances (D44 …)" comment.
   - No geometry changes and no golden moves.

### AM2-3 — Record

- Append this amendment to `docs/plans/2026-09-28-wide-dovetail.md` (B14), under the verdict.
- Its history text stays as written.

### Note (2026-09-28, later the same day): AM2-1 is WITHDRAWN; A ships inside plan F's PR

**Why AM2-1 is withdrawn.** A's developer showed the diagnosis was wrong.
- The 8-part `check` failure also appears on `arch-tv-bracket:centre`, which has no strips, and it reproduces on a bare `mcc_rail_male(len=60, plate_t=6)`.
- The cause is a zero-volume sliver at the D34 nub's tangent vertices on the flank line (`_mcc_rail_nub_2d()`, at the rail's z ≈ 0).
- A's pedestal removal (D44) puts the nub there; on `main` the pedestal kept it clear and every part passes. The flush snap-off strips did not cause it.
- AM2-1 was relayed from plan F's prototype report without being reproduced at this gate — the gate's miss.

**Teamlead's process decision.**
- A's PR stays a **draft** and does not merge on its own.
- Plan F stacks on `feature/wide-dovetail` and deletes the D34 nub together with the rest of the latch. F's PR into `main` carries A and F together and must be CI-green; A's draft PR is then closed as superseded.
- So nobody applies AM2-1. A's `check` failure on the arch centre and the coupon is a known interim state of the draft branch; B15's stop on it is satisfied by this routing.
- The strip question moves to F's coupon rewrite: F keeps the 1 mm inset, because F's own prototype justifies it independently of the nub (F's verdict, FB3).

**AM2-2 still stands.** Plan F's R41 edit carries the full corrected paragraph itself, so R41 comes out right whether or not A's developer applied AM2-2 (F's verdict, FB4).
