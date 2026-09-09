# Implementation plan — slimmer cradle deck (ribs/ladder, VESA removed)

> ## Architect verdict — 2026-09-09 (`architecture.md` rev 9 / `layout-patch-wall.md` §17)
>
> **APPROVED WITH CHANGES.** Branch `feature/issue-29-cradle-deck` off `main` **after #25 merges**
> (may run concurrently with `feature/issue-26-tv-bracket`). §2's VESA-removal steps become
> *verification* steps — **#25 owns the VESA removal and the `floor_center` rename** (not
> `mount_ref_pos`).
>
> Blocking changes:
> 1. **Ladder ribs use `MCC_CRADLE_RIB_T = 3.0`.** Do not create `_mcc_cradle_deck_rib_t()` or
>    `MCC_RIB_HEIGHT_RATIO_MAX`-derived `deck_h/3`. Reasoning: `architecture.md` §13 **D22** — the
>    ≤3:1 rule governs cantilevered fins, not floor-standing cross-braced webs.
> 2. **`cfg.tripod_insert` defaults `true`** (teamlead decision **D-16**), set explicitly in all 8
>    `case.scad`. PLAN-ASSUMPTION 2 is overruled.
> 3. **`_mcc_deck_rib_blocked()` is dropped for v1** (**D21**) — as written it tests a rib's whole
>    AABB, so any keep-out band crossing the deck deletes every perpendicular rib line.
>
> Two new failure modes the lattice creates, neither caught by `check`: **T1-40** the pad pocket must
> land on a solid island (otherwise the EPDM pad bears on ~15 % of its area and dishes); **T1-41** the
> tripod boss must be braced into the lattice instead of standing as a lone ⌀17.1 post.
>
> Rejected process steps: do **not** edit `.claude/knowledge/**` from the branch (step 9 — both files
> are architect-owned and this gate has already recorded the rulings), and do **not** create
> `decision-log.md` (step 10).

Status: **PLAN — not yet architect-validated, not yet implemented.**

GitHub issue: **#29** (`gh issue view 29`), depends on **#25** (dovetail-rail floor mount, replaces
VESA). Per `.claude/knowledge/ticket-source.md`, findings are also posted as a comment on #29;
this file is the durable, fully-explicit version for the implementing developer. Target branch:
`feature/issue-29-cradle-deck` off `main` (`git-flow` skill).

Read before implementing: `.claude/knowledge/architecture.md` §6 (floor rule), §9 (test policy);
`.claude/knowledge/layout-patch-wall.md` §1 (frame), §2.2 (`z_conn_c`/plate height), §7 + §7.1
(cradle/floor), §16 (per-SKU fit-check pattern — not directly about this ticket, but the format to
follow when checking all 8 SKUs); `lib/mcc/cradle.scad`, `lib/mcc/mounts.scad`, `lib/mcc/layout.scad`,
`lib/mcc/constants.scad`, `lib/mcc/fasteners.scad`;
`knowledge/design/fdm-rugged-enclosure-guidelines.md` §4 (ribs vs. solid).

**This plan is coupled to #25**, which is not yet implemented (`gh issue view 25` shows it OPEN,
no commits found referencing it). §2 and §3 below specify edits to `mounts.scad`/`layout.scad` that
are arguably #25's territory (VESA removal, floor-keepout coordination). They are included here
because issue #29 explicitly asks for them and because the cradle-deck redesign cannot be finished
without knowing VESA is gone. **Before starting, the developer must check whether #25 has landed
first** (`git log main --oneline --grep="25"`, `git branch -a | grep issue-25`) — if it has, treat
§2's edits as already done and diff against them rather than reapplying blindly; if a `#25` PR is
in flight concurrently, coordinate file ownership with whoever is on it (both touch
`mounts.scad`/`layout.scad`).

---

## 1. What the deck does today, and what survives

### 1.1 The deck height is not a free variable

The device's Z position is derived from the **connector centreline**, not the other way around.
`lib/mcc/layout.scad:339` sets `z_conn_c = MCC_SIDE_BOLT_AXIS_Z` (`constants.scad:205`), which is
itself derived as:

```
z_conn_c = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H/2 = 3 + 3 + 19.5 = 25.5
```

`MCC_PLATE_H = 39.0` is fixed by the **4 mm flange-to-plate-edge web in Z** (`architecture.md` §5,
**D-06 vetoed** 2026-09-08 — a 37 mm plate was explicitly rejected). `MCC_FLOOR_T`/`MCC_PANEL_BAND`
are the uniform 3 mm shell spec. The device sits centred on that same axis
(`layout.scad:337`, `mcc_case_layout()`):

```
z_dev_lo = MCC_FLOOR_T + mcc_cradle_deck(dev)
mcc_cradle_deck(dev) = MCC_SIDE_BOLT_AXIS_Z - mcc_dev_size(dev)[2]/2 - MCC_FLOOR_T   // layout.scad:208-209
```

So **deck height (interior floor to device underside) = `z_conn_c − dev_h/2 − MCC_FLOOR_T`**, a
pure consequence of three already-fixed numbers (`z_conn_c`, `dev_h`, `MCC_FLOOR_T`). For the
compact family (`dev_h = 23.3`): `25.5 − 11.65 − 3 = 10.85 mm`. For plus (`dev_h = 23.4`):
`25.5 − 11.7 − 3 = 10.80 mm`. These match the issue's "~10.85 mm" figure and
`layout-patch-wall.md` §7's `z = 13.8/13.85` row (deck top = `z_dev_lo`, not the deck height itself
— that table row is mis-labelled "Deck top" when it should also state the *height*; fix while
editing, see §6 step 9).

**Conclusion: the deck cannot be made shorter.** Lowering it means lowering `z_conn_c`, which means
either shrinking `MCC_PLATE_H` (reopens the vetoed D-06) or shrinking `MCC_PANEL_BAND`/`MCC_FLOOR_T`
below the uniform 3 mm shell spec (a material-thickness decision, also not open). None of that is
in scope for #29 or #25, and CLAUDE.md's "Fixed decisions" list both D-06 and the 51 mm case height
as **do not re-open**. **This plan changes only what fills the deck's fixed height/footprint, not
the height itself.** If a future ticket wants to reopen `z_conn_c`, it needs a new user decision —
escalate, don't improvise it here.

### 1.2 What the deck actually is today, vs. what the doc says

`lib/mcc/cradle.scad:96-106` (`mcc_cradle()`) currently builds the deck as a **solid cube**
(`deck_x × deck_y × deck_h`, where `deck_x`/`deck_y` are the device's own XY footprint plus a
`LIP = MCC_WALL = 3.0 mm` margin on every side) with exactly one subtraction: the
40×40×2 mm compliant floor-pad pocket (`MCC_CRADLE_FLOOR_PAD_MIN`/`MCC_CRADLE_FLOOR_PAD_T`) near the
device centre. The case's own 1/4"-20 tripod-insert boss (T1-32) is unioned in as a separate plain
cylinder. The far-flank ribs (`_mcc_far_flank_rib()`) and patch-flank ribs are **already** discrete
fin geometry standing *above* the deck top or bridging the far duct — they are not part of the solid
block and are **unaffected by this ticket**.

`layout-patch-wall.md` §7's cradle table already says "Deck slab | 8.8 mm, ribbed/hollow, 3 mm top
plate on 3 mm webs" — **that description was never implemented** (the height figure, 8.8, is also
stale — it predates the D-13 `MCC_GAP_FAR` change and doesn't match either family's actual
`z_dev_lo`). This ticket is what finally builds a ribbed deck; §6 step 9 replaces that row with the
real, implemented design instead of the old aspirational one.

### 1.3 What survives, what changes

| Element | Today | After this ticket |
|---|---|---|
| Deck top height (`z_dev_lo`) | `mcc_cradle_deck(dev)` (layout.scad) | **unchanged** — same function, same values |
| Deck footprint (X/Y) | device footprint + `MCC_WALL` margin | **unchanged** |
| Deck fill | solid cube | **perimeter frame (`MCC_WALL` wide) + interior ladder ribs on a ~22 mm grid** (§5) |
| Pad pocket | 40×40×2 mm cut near device centre | **unchanged**, cut from the new lattice instead of the cube |
| Far-flank ribs | discrete fins, deterministic placement | **unchanged** (`_mcc_far_flank_rib_x()` untouched) |
| Patch-flank ribs | only where `\|x\| > plate_l/2 − 3` | **unchanged** |
| Case tripod-insert boss (T1-32) | always drawn | **optional**, `cfg.tripod_insert` (default `false`) — §2 |
| VESA blind-insert bosses | always drawn (`cfg.vesa`, default `true`) | **removed entirely** — §2 |

---

## 2. VESA removal and the case's own tripod insert

### 2.1 Remove the VESA blind-insert bosses (owned by `mounts.scad`/`layout.scad`, not `cradle.scad`)

Issue #25 drops the VESA 75×75 pattern outright, replaced by the dovetail rail. The VESA bosses are
not in `cradle.scad` — they are `mounts.scad`'s (`architecture.md` §6 floor rule: `mounts.scad` is
the *single owner* of every floor feature except the case's own tripod insert and the compliant pad,
which stay in `cradle.scad`). Remove:

- `lib/mcc/mounts.scad`: delete `_mcc_vesa_positions()` (lines 57-62), the `if (vesa_on) { ... }`
  block in `mcc_floor_features_add()` (lines 78-97, keep the module shell but it becomes a no-op
  unless something else is added to it later — do not leave a dangling empty `module`, just remove
  the VESA-specific body and its now-unused `vesa_flag`/`vesa_on`/`h`/`boss_r` locals), and the
  mirrored `if (vesa_on) { ... }` block in `mcc_floor_bore_cut()` (lines 111-118, same treatment).
  Update both modules' doc comments (they currently describe the VESA behaviour) to say "no VESA
  feature any more; floor mount is the dovetail rail (see #25 / `bracket.scad`)" — do not leave a
  stale doc comment describing deleted code.
- `lib/mcc/layout.scad`, `mcc_floor_keepout()` (`layout.scad:247-282`): delete the 4
  `vesa_ne`/`vesa_se`/`vesa_nw`/`vesa_sw` rows (lines 272-275) and the now-unused `MCC_VESA_HOLE_D`
  reference. **Do not delete the `vesa_pos` local itself** — it is also the anchor for the
  `fishtail_reserve` row and (per §2.2 below) the case's own tripod-insert keep-out, neither of
  which #25/#29 touch. Rename it from `vesa_pos` to `mount_ref_pos` (it is no longer VESA-specific)
  and update every reference in that function (`fishtail_reserve` row, `case_tripod_insert` row).
- `lib/mcc/constants.scad`: `MCC_VESA_HOLE_D` (line 505) and `MCC_VESA75_PITCH` (line 520) become
  dead once the two call sites above are gone — delete them (grep to confirm no other reference
  first: `grep -rn "MCC_VESA" lib/ tests/ models/`). `MCC_INSERT_M4` (lines 121-125) stays: it is
  a generic M4 heat-set-insert record with no VESA-specific naming, and nothing here says it isn't
  needed elsewhere later — leave it unless a grep after the above deletions shows it is now
  genuinely unused, in which case delete it too and say so in the commit message.
- **Every `models/<slug>/case.scad`'s `"vesa"` cfg-key doc comment** (the block starting `//
  "vesa"      (bool, optional, default true) -- draws the 4 VESA 75x75 M4 heat-set bosses...`,
  present in all 8 files per the `pro-convert-for-ndi-to-hdmi/case.scad` pattern) must be deleted.
  This is mechanical and identical across all 8 `models/*/case.scad` files — grep for `"vesa"` to
  find every occurrence (`grep -rln '"vesa"' models/`). None of the 8 files sets `["vesa", ...]` in
  their `variant`/cfg struct today (checked — the flag only ever used its default), so this is a
  comment-only deletion, no behavioural change in the case files themselves.
- **Tier-1 test coverage**: `tests/test_shell.scad` and `tests/test_layout.scad` (if it references
  `mcc_floor_keepout()`'s VESA rows or `"vesa"` cfg) need the same grep-and-remove treatment. Check
  both before assuming no test references VESA.

### 2.2 The case's own 1/4"-20 tripod insert: make it optional, default off

**Argument for making it `cfg.tripod_insert`, default `false`, rather than keeping it always-on:**

- The two new bracket types (#26 TV bracket, #27 truss bracket) mount via #25's dovetail rail — that
  is now the primary, tool-less mounting path for both stage use cases this repo actually targets
  (live performance rigging). The case's own insert is a *third*, lower-priority option (bare
  tripod stud / cheeseplate, no bracket) that nothing in the fixed decisions calls out as required
  once the rail exists.
- **The existing margin is already fragile and this ticket makes it more so.** T1-32
  (`cradle.scad:119-121`) asserts `MCC_INSERT_1_4_20.len + 1 <= z_dev_lo`, i.e. `13.7 <= z_dev_lo`.
  That is `13.85` (compact) / `13.8` (plus) — **0.15 mm / 0.10 mm of slack**, already flagged as
  tight in `layout-patch-wall.md` §7.1 rev-5 correction 3. Keeping this feature mandatory means
  every future device (including the not-yet-built `ip_decoder` family, 24.5 mm tall — even less
  deck height) inherits a near-zero-margin assert it may not be able to satisfy at all, on a feature
  most SKUs won't use. Making it opt-in removes that constraint from the default build.
  Additionally §5's ladder-grid design (below) means the boss can no longer rely on "the deck is a
  solid cube around it anyway" for redundant support — with `cfg.tripod_insert = false` (the new
  default) this problem simply doesn't arise on any of the 8 current SKUs.
- **Precedent already in this codebase for a free-standing boss when it doesn't land on solid
  material**: `mounts.scad`'s own doc comment for the (now-removed) VESA bosses states "where it
  doesn't [land under the cradle deck], the boss stands as a small free-standing post rising from
  the floor" — i.e. a floor-standing insert boss not embedded in a solid block is already an
  accepted pattern here. When `cfg.tripod_insert = true`, the boss (unchanged geometry, still a
  plain cylinder `z ∈ [0, z_dev_lo]`) simply stands as a free-standing post inside the ladder grid's
  open area; it does not need a rib to pass through it for structural validity, though the grid
  function (§5) happens to usually place one nearby anyway since the boss sits at the deck centre
  `(0,0)`, close to the plan-view middle of the interior grid.
- **Decision, subject to solution-architect and user confirmation (this is exactly the kind of call
  the architecture gate exists for — do not treat this plan's recommendation as final without that
  sign-off):** add `cfg.tripod_insert` (bool, default `false`, same `is_undef()`-defaults-to
  pattern as the removed `"vesa"` key) to `mcc_cradle()`. When `true`, draw the boss (T1-32,
  unchanged geometry/assert) and cut its bore; when `false`, draw neither, and the deck's plan-view
  centre point is simply open lattice like everywhere else. Document the new key in every
  `models/<slug>/case.scad`'s cfg-key comment block (mechanical, same 8 files as §2.1, and can be
  done in the same pass) but **do not set it `true` in any of the 8 shipping variants** — it stays
  an opt-in a future SKU/user can enable, not a default-on feature to re-derive per device today.

---

## 3. Interaction with the floor rail (#25)

**Different Z bands, so no direct geometric collision by construction.** The rail (#25) is a floor
*exterior*-or-embedded feature; the cradle deck occupies interior floor space **above** the 3 mm
floor slab (`z ∈ [MCC_FLOOR_T, z_dev_lo]`). `cradle.scad` still "never cuts the floor"
(`architecture.md` §6) — that invariant is untouched by this ticket.

**The real interaction is indirect, and it is new because of this ticket specifically**: today the
deck is solid, so *any* floor feature that happens to sit under the device footprint gets "free"
vertical backing/reinforcement from the solid block above it (this is explicitly how the VESA bosses
used to work — `mounts.scad`'s own comment: "where the deck already fills the same volume, the boss
simply embeds in it (redundant, harmless material)"). Once the deck is mostly air, that free
reinforcement disappears. Two concrete requirements follow:

1. **The ladder grid must not blindly cross a registered floor feature it doesn't know about.**
   `mcc_cradle()` must call `mcc_floor_keepout(dev, cfg)` (already exported by `layout.scad`,
   `cradle.scad` already `use`s `layout.scad` — no new import needed) and skip any candidate rib
   position whose footprint overlaps a registered keep-out **other than** `"case_tripod_insert"` and
   `"fishtail_reserve"` (both of those are established "additive/reserve, safe to coexist" entries —
   see §2.2's boss-coexistence precedent and the Fishtail band's own "reserve-only, no geometry cut"
   status). This is written generically (§5's `_mcc_deck_rib_blocked()`) precisely so that whatever
   XY keep-out entry #25 eventually registers for the rail (unknown today — #25 is not implemented)
   is automatically respected without a second `cradle.scad` change once #25 lands. **On today's 8
   SKUs this filter is a no-op** (checked: `strap_*` and `side_bolt_web` keep-out entries do not
   fall inside any current SKU's tight deck footprint — the strap slots sit near the outer walls,
   `y = ±(W/2−12)`, and the side-bolt web's Y range `[−W/2+3, −W/2+17]` sits entirely below
   `y_dev_lo` on every priority device) — this step is forward-looking, not a fix for an existing
   collision.
2. **"Keep the far duct free" (from the ticket) is already satisfied by construction and needs no
   new code.** The deck's Y span is `[y_dev_lo − MCC_WALL, y_dev_hi + MCC_WALL]`; the far duct
   (`MCC_GAP_FAR = 16 mm` between the far wall and `y_dev_lo`) is entirely outside that span. The
   deck has never reached into the far duct — only the separately-owned far-flank ribs bridge it,
   and their own "must not dam the duct" notch rule (`layout-patch-wall.md` §7) is unchanged by this
   ticket. Confirm this with a render/visual check (§6 step 12) rather than adding a redundant
   assert for a geometric fact that already follows from `deck_y`'s own definition.

**This plan does not implement anything from #25 itself** (no `bracket.scad`, no rail cut, no new
`mcc_floor_keepout()` row for it) — that is #25's scope. When #25 is implemented, its developer
should re-read this ticket's §3 to confirm the rail's floor-keepout label is *not* added to the
`{"case_tripod_insert","fishtail_reserve"}` coexistence allowlist in `_mcc_deck_rib_blocked()`
(§5) unless it is genuinely safe for a rib to run through it.

---

## 4. Mass / print-time saving estimate, stiffness, thermal side-benefit

**Method and caveat:** these are hand-calculated estimates from the current solid-deck geometry and
the proposed rib pattern, to size the change before implementing it — **not** a substitute for the
real number, which is whatever `scripts/build.py golden` reports after §5 is implemented. Use this
section to sanity-check that number, not to pre-fill the golden files.

| | Compact (NDI to HDMI, `dev` 100.9×60.2×23.3) | Plus (HDMI Plus, `dev` 117.5×66.7×23.4) |
|---|---|---|
| Deck footprint (incl. `MCC_WALL` margin) | 106.9 × 66.2 mm | 123.5 × 72.7 mm |
| Deck height | 10.85 mm | 10.80 mm |
| **Solid deck volume today** (cube − 40×40×2 pad pocket) | 76,785 − 3,200 ≈ **73,585 mm³** | 96,967 − 3,200 ≈ **93,767 mm³** |
| Current whole-base golden volume | 278,682 mm³ (`tests/golden/pro-convert-for-ndi-to-hdmi.base.json`) | 314,250 mm³ (`...hdmi-plus.base_fan.json`) |
| Deck's share of the base today | **≈ 26 %** | **≈ 30 %** |
| Estimated ladder-deck volume (perimeter frame `MCC_WALL` wide + interior ribs at `MCC_CRADLE_DECK_GRID_PITCH`, both at deck height) | frame ≈ 1,003 mm² + interior ribs ≈ 1,523 mm² ≈ 2,526 mm² × 10.85 ≈ **≈ 27,400 mm³** | frame ≈ 1,141 mm² + interior ribs ≈ 1,433 mm² ≈ 2,574 mm² × 10.80 ≈ **≈ 27,800 mm³** |
| **Estimated saving** | **≈ 46,000 mm³ ≈ 63 % of the deck's own material, ≈ 16–17 % of the whole base part** | **≈ 66,000 mm³ ≈ 70 % of the deck's own material, ≈ 21 % of the whole base part** |

Print-time savings track volume roughly linearly for infill-dominated regions like this (the deck is
currently 100 % infill-equivalent solid); expect a comparable double-digit percentage cut in the
deck's own print time, smaller as a fraction of the whole part (walls/lid/vents dominate total time).

**Stiffness argument.** `fdm-rugged-enclosure-guidelines.md` §4: "ribs and gussets deliver most of
the stiffness gain [of a solid block] for a fraction of the material" and recommends *against*
thickening solid sections (uneven cooling → sink marks/warping) in favour of ribs. The device rests
on the rib top edges rather than a continuous slab — mechanically the same principle already
validated in this repo's own far-flank ribs, whose doc comment states "anti-rotation is carried
entirely by the ribs... structural, not cosmetic" (`layout-patch-wall.md` §7). A cross-braced grid
(ribs running both X and Y, intersecting at every grid point) is stiffer per unit mass than either a
single free-standing fin or a solid block of the same footprint, and ASA's higher stiffness (vs. PLA)
means the thinner rib section is not a durability compromise for this load case (static device
weight + drop shock transmitted through the far-wall bolt and the ribs, not through the floor).

**Thermal side-benefit.** Today the solid deck blocks all airflow under the device across its
entire footprint except the side ducts (`MCC_GAP_FAR` on the far flank, `MCC_GAP_DEV` on the patch
flank). A ladder deck opens real cross-sections between floor and device underside across most of
the footprint, letting the existing intake/exhaust vent flow (`vents.scad`, `architecture.md` §11 R5
thermal discussion) reach more of the device's underside rather than only its flanks. This is a
secondary, unquantified benefit (R5's numbers are governed by external surface area and vent
aperture size, not the cradle) — record it as a qualitative plus, not a new thermal budget line.

---

## 5. `lib/mcc/cradle.scad` module changes

### 5.1 New constants (`lib/mcc/constants.scad`, add after `MCC_CRADLE_FLOOR_PAD_MIN`, i.e. after
line 468)

```
MCC_RIB_HEIGHT_RATIO_MAX = 3.0;   // rib height <= this * rib thickness.
                                   // knowledge/design/fdm-rugged-enclosure-guidelines.md §4
                                   // "keep to about 3x rib thickness as a practical limit".

MCC_CRADLE_DECK_GRID_PITCH = 22.0; // target interior ladder-rib pitch, mm -- GitHub issue #29
                                    // ("3 mm ribs on a 20-25 mm grid"), mid-point of that range.
                                    // Actual achieved pitch varies per SKU (rounds to a whole
                                    // number of bays) -- bounded by the two constants below.

MCC_CRADLE_DECK_GRID_PITCH_MIN = 16.0; // T1-assert lower bound on achieved grid pitch, mm.
MCC_CRADLE_DECK_GRID_PITCH_MAX = 32.0; // T1-assert upper bound on achieved grid pitch, mm.
```

`MCC_CRADLE_RIB_T` (existing, 3.0) stays exactly as-is and keeps governing the far-flank/patch-flank
ribs, which this ticket does not touch. The new ladder-deck ribs get their **own**, slightly larger,
derived thickness (§5.2) rather than reusing `MCC_CRADLE_RIB_T` directly — flag this divergence for
the architect (PLAN-ASSUMPTION #1, §7): it keeps `MCC_RIB_HEIGHT_RATIO_MAX` satisfied by
construction for every SKU (deck ribs run floor-to-deck-top with no cantilever, so their `deck_h`
governs the ratio, not `MCC_CRADLE_RIB_H`), at the cost of two different rib thicknesses appearing in
the same printed part.

### 5.2 New functions and module in `lib/mcc/cradle.scad`

Add after `_mcc_far_flank_rib_x()` (after line 61), before `mcc_cradle()`:

```
// Function: _mcc_cradle_deck_rib_t()
// Description:
//   Private. Ladder-deck rib thickness for a deck of height `deck_h`: the larger of
//   MCC_CRADLE_RIB_T and deck_h / MCC_RIB_HEIGHT_RATIO_MAX, so the printed height:thickness ratio
//   never exceeds the fdm-rugged-enclosure-guidelines.md §4 3:1 rule regardless of family.
function _mcc_cradle_deck_rib_t(deck_h) =
    max(MCC_CRADLE_RIB_T, deck_h / MCC_RIB_HEIGHT_RATIO_MAX);

// Function: _mcc_cradle_deck_grid()
// Description:
//   Private. Interior ladder-rib centre positions along one axis, given the deck's OUTER bound
//   `[lo, hi]` on that axis (i.e. deck_x or deck_y, frame included). Divides the interior span
//   (outer span less the MCC_WALL-wide perimeter frame on each side) into the smallest number of
//   equal bays whose width is close to MCC_CRADLE_DECK_GRID_PITCH, then returns the (n_bays - 1)
//   interior divider positions. Never returns a position inside the MCC_WALL frame band itself.
// Arguments:
//   lo, hi = deck's outer bound on this axis, mm.
function _mcc_cradle_deck_grid(lo, hi) =
    let(
        span    = (hi - lo) - 2 * MCC_WALL,
        n_bays  = max(1, round(span / MCC_CRADLE_DECK_GRID_PITCH)),
        n_ribs  = n_bays - 1,
        step    = span / n_bays
    )
    [for (i = [1:1:n_ribs]) lo + MCC_WALL + i * step];

// Function: _mcc_deck_rib_blocked()
// Description:
//   Private. True if a candidate rib segment centred at (cx, cy) with plan-view half-extents
//   (hw, hh) overlaps any `keepout` entry (mcc_floor_keepout() row shape) EXCEPT the two labels
//   known to coexist safely with the deck lattice: "case_tripod_insert" (the boss stands as a
//   free-standing post when cfg.tripod_insert=true, or is simply absent -- either way a rib
//   crossing that XY position is harmless) and "fishtail_reserve" (reserve-only, no geometry is
//   ever cut for it). Every other label -- strap slots, the side-bolt support web, and whatever
//   .claude/knowledge/layout-patch-wall.md-registered keep-out issue #25's floor rail adds once
//   implemented -- blocks a rib. Uses a conservative axis-aligned-bounding-box test (a circle
//   keep-out is treated as its bounding square), which only ever over-skips a rib, never
//   under-skips one.
// Arguments:
//   cx, cy   = candidate rib segment centre, mm.
//   hw, hh   = candidate rib segment plan-view half-extents, mm.
//   keepout  = mcc_floor_keepout(dev, cfg) result.
function _mcc_deck_rib_blocked(cx, cy, hw, hh, keepout) =
    let(
        hits = [for (f = keepout)
            if (f[4] != "case_tripod_insert" && f[4] != "fishtail_reserve")
                let(
                    is_circle = f[2] == "circle",
                    fw = is_circle ? f[3] / 2 : f[3][0] / 2,
                    fh = is_circle ? f[3] / 2 : f[3][1] / 2,
                    clear = (abs(cx - f[0]) > hw + fw) || (abs(cy - f[1]) > hh + fh)
                )
                if (!clear) true
        ]
    )
    len(hits) > 0;

// Module: _mcc_cradle_deck_lattice()
// Usage:
//   _mcc_cradle_deck_lattice(deck_x, deck_y, deck_h, keepout);
// Description:
//   ADDITIVE. The deck's fill: a MCC_WALL-wide perimeter frame around [deck_x, deck_y] plus an
//   interior ladder of X- and Y-running ribs on ~MCC_CRADLE_DECK_GRID_PITCH centres (rib thickness
//   from _mcc_cradle_deck_rib_t()), all MCC_FLOOR_T..MCC_FLOOR_T+deck_h tall. Any interior rib
//   segment that overlaps a registered floor keep-out (per _mcc_deck_rib_blocked(), other than the
//   two labels that coexist safely) is skipped rather than drawn. Replaces the old solid cube in
//   mcc_cradle() (this file). The pad-pocket subtraction is NOT done here -- the caller
//   difference()s it against this module's result, same as it did against the old cube.
// Arguments:
//   deck_x, deck_y = [lo, hi] deck outer bounds on each axis, mm.
//   deck_h         = deck height, mm.
//   keepout        = mcc_floor_keepout(dev, cfg) result.
module _mcc_cradle_deck_lattice(deck_x, deck_y, deck_h, keepout) {
    rib_t = _mcc_cradle_deck_rib_t(deck_h);
    assert(deck_h / rib_t <= MCC_RIB_HEIGHT_RATIO_MAX + MCC_EPS,
        str("mcc: deck ladder rib height:thickness ratio ", deck_h / rib_t, " exceeds MCC_RIB_HEIGHT_RATIO_MAX=",
            MCC_RIB_HEIGHT_RATIO_MAX));

    interior_x = [deck_x[0] + MCC_WALL, deck_x[1] - MCC_WALL];
    interior_y = [deck_y[0] + MCC_WALL, deck_y[1] - MCC_WALL];
    grid_x = _mcc_cradle_deck_grid(deck_x[0], deck_x[1]);
    grid_y = _mcc_cradle_deck_grid(deck_y[0], deck_y[1]);
    assert(len(grid_x) >= 1 && len(grid_y) >= 1,
        str("mcc: deck ladder produced zero interior ribs on a ", deck_x, "x", deck_y, " deck"));

    union() {
        // Perimeter frame: outer box minus inner box, deck-height tall.
        difference() {
            translate([deck_x[0], deck_y[0], MCC_FLOOR_T])
                cube([deck_x[1] - deck_x[0], deck_y[1] - deck_y[0], deck_h]);
            translate([interior_x[0], interior_y[0], MCC_FLOOR_T - MCC_EPS])
                cube([interior_x[1] - interior_x[0], interior_y[1] - interior_y[0], deck_h + 2 * MCC_EPS]);
        }
        // Interior ribs running in Y (one per grid_x position), each spanning the interior Y range.
        for (gx = grid_x)
            if (!_mcc_deck_rib_blocked(gx, (interior_y[0] + interior_y[1]) / 2, rib_t / 2,
                                        (interior_y[1] - interior_y[0]) / 2, keepout))
                translate([gx - rib_t / 2, interior_y[0], MCC_FLOOR_T])
                    cube([rib_t, interior_y[1] - interior_y[0], deck_h]);
        // Interior ribs running in X (one per grid_y position), each spanning the interior X range.
        for (gy = grid_y)
            if (!_mcc_deck_rib_blocked((interior_x[0] + interior_x[1]) / 2, gy,
                                        (interior_x[1] - interior_x[0]) / 2, rib_t / 2, keepout))
                translate([interior_x[0], gy - rib_t / 2, MCC_FLOOR_T])
                    cube([interior_x[1] - interior_x[0], rib_t, deck_h]);
    }
}
```

### 5.3 `mcc_cradle()` changes (lines 78-144)

- Keep every existing local (`x_dev_lo`, `x_dev_hi`, ..., `LIP`, `deck_x`, `deck_y`, `deck_h`) and
  the `assert(deck_h > 0, ...)` exactly as-is.
- Add `keepout = mcc_floor_keepout(dev, cfg);` after the existing `l = mcc_case_layout(dev, cfg);`
  line.
- Add `tripod_flag = struct_val(cfg, "tripod_insert"); tripod_on = is_undef(tripod_flag) ? false : tripod_flag;`
  (mirrors the removed `mounts.scad` `vesa_on` pattern exactly, default flipped to `false`).
- Replace the `// --- Deck slab ---` `difference() { cube(...); <pad pocket> }` block (lines 97-106)
  with:
  ```
  // --- Deck lattice (perimeter frame + interior ladder ribs) ---
  difference() {
      _mcc_cradle_deck_lattice(deck_x, deck_y, deck_h, keepout);
      translate([x_dev_c, y_dev_c, MCC_FLOOR_T + deck_h - MCC_CRADLE_FLOOR_PAD_T])
          cube([MCC_CRADLE_FLOOR_PAD_MIN, MCC_CRADLE_FLOOR_PAD_MIN, MCC_CRADLE_FLOOR_PAD_T + MCC_EPS]);
  }
  ```
- Wrap the existing "Case tripod-mount insert boss" block (lines 108-124, the `assert(...)` and the
  `cyl(...)` call) in `if (tripod_on) { ... }`. Do not otherwise change its geometry — same
  `boss_od_tripod`, same `cyl()` call.
- Leave the far-flank rib loop and patch-flank rib loop (lines 126-142) untouched.

### 5.4 `mcc_tripod_insert_bore_cut()` changes (lines 20-37)

Add the same default-`false` guard **inside** the module (matching `mounts.scad`'s own
`mcc_floor_bore_cut()` pattern for its VESA bore, so `shell.scad`'s existing unconditional call site
at line 427 needs no change):

```
module mcc_tripod_insert_bore_cut(dev, cfg) {
    tripod_flag = struct_val(cfg, "tripod_insert");
    tripod_on = is_undef(tripod_flag) ? false : tripod_flag;
    if (tripod_on) {
        translate([0, 0, MCC_EPS])
            rotate([180, 0, 0])
                mcc_case_tripod_insert_bore();
    }
}
```

### 5.5 New Tier-1 asserts introduced

Both already appear inline above (in `_mcc_cradle_deck_lattice()`): the height:thickness ratio
assert and the "at least one interior rib per axis" assert. Add one more, in `mcc_cradle()` itself,
guarding the grid-pitch bounds (defence against a hypothetical future device far outside today's
size range silently producing a degenerate 1-bay or 50-rib grid):

```
grid_pitch_x = (deck_x[1] - deck_x[0] - 2 * MCC_WALL) / (len(_mcc_cradle_deck_grid(deck_x[0], deck_x[1])) + 1);
grid_pitch_y = (deck_y[1] - deck_y[0] - 2 * MCC_WALL) / (len(_mcc_cradle_deck_grid(deck_y[0], deck_y[1])) + 1);
assert(grid_pitch_x >= MCC_CRADLE_DECK_GRID_PITCH_MIN && grid_pitch_x <= MCC_CRADLE_DECK_GRID_PITCH_MAX,
    str("mcc: deck ladder X pitch ", grid_pitch_x, " outside [", MCC_CRADLE_DECK_GRID_PITCH_MIN, ",",
        MCC_CRADLE_DECK_GRID_PITCH_MAX, "] on \"", mcc_dev_slug(dev), "\""));
assert(grid_pitch_y >= MCC_CRADLE_DECK_GRID_PITCH_MIN && grid_pitch_y <= MCC_CRADLE_DECK_GRID_PITCH_MAX,
    str("mcc: deck ladder Y pitch ", grid_pitch_y, " outside [", MCC_CRADLE_DECK_GRID_PITCH_MIN, ",",
        MCC_CRADLE_DECK_GRID_PITCH_MAX, "] on \"", mcc_dev_slug(dev), "\""));
```

Place these right after the existing `assert(deck_h > 0, ...)` line, before the deck-lattice
`difference()`.

### 5.6 Goldens change on all 8 SKUs, justified

Every `models/<slug>/case.scad`'s `"base"` (and `"base_fan"` where it exists) golden's `volume_mm3`
drops by roughly the §4 estimate; `facets` also drops (fewer/simpler solids than one big cube);
`bbox` is **unchanged** (the deck never touched the printed envelope). This is the intended,
justified change this ticket exists to make — update with
`python scripts/build.py golden --update` (see §6) and note the before/after volumes in the PR
description, not as a code comment.

---

## 6. Ordered implementation steps

1. Confirm #25's status (`git log main --oneline | grep -i "25\|rail\|bracket"`, `git branch -a`).
   If #25 has landed, diff its actual `mounts.scad`/`layout.scad` changes against §2.1 above before
   touching those files — apply only what's still needed.
2. Create branch `feature/issue-29-cradle-deck` off `main`.
3. `lib/mcc/constants.scad`: add the four new constants (§5.1); delete `MCC_VESA_HOLE_D` and
   `MCC_VESA75_PITCH` once §2.1's call sites are gone (do this deletion *after* step 4, not before,
   so nothing references them mid-edit).
4. `lib/mcc/mounts.scad`: apply §2.1's VESA removal (both modules), update doc comments.
5. `lib/mcc/layout.scad`: apply §2.1's `mcc_floor_keepout()` edit (delete 4 VESA rows, rename
   `vesa_pos` → `mount_ref_pos`, update its other two references).
6. Re-grep for `MCC_VESA` / `"vesa"` across `lib/`, `tests/`, `models/` — confirm zero remaining
   references before proceeding (catches anything this plan's file list missed).
7. `lib/mcc/cradle.scad`: add §5.2's three functions + one module, apply §5.3's `mcc_cradle()`
   edits, apply §5.4's `mcc_tripod_insert_bore_cut()` edit, add §5.5's two pitch-bound asserts.
8. Delete the 8 `"vesa"` cfg-key doc-comment blocks from `models/*/case.scad` (§2.1); add the new
   `"tripod_insert"` cfg-key doc-comment block to the same 8 files (§2.2) — do not set it `true` in
   any of them.
9. Documentation: in `.claude/knowledge/layout-patch-wall.md` §7's cradle table, replace the
   "Deck slab | 8.8 mm, ribbed/hollow, 3 mm top plate on 3 mm webs" row with the real design:
   height formula (§1.1), perimeter frame `MCC_WALL` wide, interior ladder ribs on
   `MCC_CRADLE_DECK_GRID_PITCH` (~22 mm) centres, rib thickness `_mcc_cradle_deck_rib_t(deck_h)`, no
   separate top plate (device rests on rib top edges, same as the existing far-flank/patch-flank
   ribs). In the same section's "Floor keep-out zones" table (§7.1), delete the VESA row and add a
   one-line note that VESA is superseded by #25's rail (do not delete the historical rev-5
   correction 4 text about VESA — annotate it "superseded by #25/#29, 2026-09-09" rather than
   rewriting history, matching this repo's existing convention for superseded rulings). **Do not
   edit `architecture.md` directly** — that file is solution-architect-owned; hand this plan to the
   architecture gate and let it record the ruling there.
10. Create `.claude/knowledge/decision-log.md` if it does not exist yet (it doesn't, checked), and
    add one dated entry (2026-09-09) recording: the VESA-removal rationale (§2.1, superseded by
    #25), the tripod-insert-default-off rationale (§2.2), and the derived-rib-thickness-vs-shared-
    constant divergence (§5.1/§7 PLAN-ASSUMPTION #1) — this is exactly the "rationale, not a code
    comment" content CLAUDE.md's "Plans must not prescribe explanatory comments" rule asks for.
11. Run `python scripts/build.py doctor` (environment sanity), then `python scripts/build.py smoke`
    — fix any assert failures before proceeding (do not skip to golden with a failing smoke tier).
12. Add a `cfg.tripod_insert = true` instance to `tests/test_shell.scad`'s `mcc_cradle()` exercise
    (Tier-2 policy: instantiate every public module at default, min, and max parameters) — e.g.
    `VARIANT_TRIPOD = concat(VARIANT, [["tripod_insert", true]]);` placed near the existing
    `VARIANT`/`VARIANT_FAN` definitions, then
    `translate([250, 500, 0]) mcc_cradle(dev = DEV, cfg = VARIANT_TRIPOD);` alongside the existing
    standalone `mcc_cradle()` call. Re-run smoke.
13. Render all 8 SKUs' `base` (+ `base_fan` where present) parts and visually inspect: perimeter
    frame present, interior ladder ribs present and not colliding with the pad pocket or (on the
    default `tripod_insert=false` SKUs) any stray boss geometry. Confirm the deck's Y span still
    stops short of the far duct (§3 item 2) by eye on at least one Plus and one compact SKU.
14. `python scripts/build.py check` — mesh checks must stay green: watertight, winding-consistent,
    `len(split()) == 1` (single connected shell) on every base. This is the check most likely to
    catch a rib that failed to union with the frame (a gap between `interior_x`/`interior_y` and a
    grid position due to an off-by-one in `_mcc_cradle_deck_grid()`), or a `tripod_insert=true` boss
    that floats disconnected because no nearby rib actually touches it in a corner case.
15. `python scripts/build.py golden --update` — review the diff: `bbox` must be byte-identical to
    before on every SKU; `volume_mm3` must drop, in the ballpark of §4's estimates (compact ≈
    16–17 %, plus ≈ 21 % of the whole base); flag anything wildly outside that range for a second
    look before committing the updated goldens.
16. Regenerate `BOM.md` (`bom-update` skill) if the VESA M4 insert hardware or the tripod insert
    appeared as BOM line items on any SKU — confirm with a grep of `BOM.md` for "VESA"/"M4" before
    assuming no change is needed.
17. `python scripts/build.py all` end-to-end, green.
18. Commit, push, open the PR against `main` referencing #29 (and #25 if it landed first). Do not
    merge — CI-green `render` check gate per `CLAUDE.md`'s branching non-negotiables, and this
    ticket's own architecture-gate step (Team Charter §2) must run before any developer starts,
    let alone merges.

---

## 7. PLAN-ASSUMPTIONs (escalate/confirm before or during implementation)

1. **Ladder-deck ribs get a derived thickness (`deck_h / 3`, ≈ 3.6 mm) distinct from the existing
   `MCC_CRADLE_RIB_T` (3.0 mm) used by far-flank/patch-flank ribs**, to keep the 3:1 height:thickness
   guideline satisfied without a per-SKU hand-tuned exception. The alternative — reuse
   `MCC_CRADLE_RIB_T` = 3.0 mm everywhere and accept a ≈3.6:1 ratio on the new grid ribs (justified
   by their being cross-braced at every grid intersection, unlike a free-standing fin) — is cheaper
   (one constant, ~0.6 mm less rib material) but knowingly exceeds a stated guideline. **Needs an
   architect/user call**, not a developer judgment call.
2. **`cfg.tripod_insert` defaults to `false` on all 8 shipping SKUs** (§2.2) — this removes a
   feature that was previously always-on. If any user or SKU actually wants the bare-tripod-stud
   mounting option preserved by default, that is a product decision, not something this plan should
   guess at. **Needs user confirmation** — this plan's argument is that #25's brackets make it
   redundant, but the user has not been asked directly.
3. **`_mcc_deck_rib_blocked()`'s AABB-based keep-out test is conservative (over-skips), not exact.**
   On today's 8 SKUs this never actually skips anything (§3), so it's unverified against a real
   collision case. When #25 lands and registers a real rail keep-out, re-render every SKU and
   visually confirm the skip logic behaves sensibly (doesn't remove more rib than necessary) rather
   than trusting the assert-level smoke tests alone.
4. **The exact interior grid pitch (~22 mm) is a single global constant, not per-family-tuned.**
   §5.2 shows it lands at 20.07–23.5 mm across the two priority families — inside the ticket's
   20–25 mm ask — but this was checked by hand for exactly two device sizes, not proven in general.
   If a future SKU (e.g. `ip_decoder`, 120 × 79.3) produces a pitch near the `MCC_CRADLE_DECK_GRID_PITCH_MIN/MAX`
   bounds, that is the assert's job to catch (§5.5) — do not raise the bounds to silence it without
   checking why first.
5. **§4's volume/print-time savings are hand-calculated pre-implementation estimates**, not a golden
   diff. Treat the percentages as directional (double-digit reduction expected) rather than exact;
   the real numbers come from step 15's actual golden diff.
6. **This plan assumes #25 has not yet landed** (verified via `git log`/`git branch` at research
   time, 2026-09-09). If #25 lands between this plan being written and implementation starting, step
   1 requires re-checking before any of §2's edits are applied, to avoid duplicate/conflicting work.
