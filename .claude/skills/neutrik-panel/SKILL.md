---
name: neutrik-panel
description: Place a Neutrik D-series panel cutout with pocket, rear screw bosses, and spacing/depth asserts; use whenever a model needs a connector cutout — always through mcc_panel_cutout(), never by calling the Neutrik provider module directly.
---

# neutrik-panel

Every external connector on every case in this repo mounts through the same 26×31 mm D-series
cutout, in the **black `-B`** variant, with no exception. This skill is the mechanical spec plus the
repo's dispatcher contract for using it correctly.

## The always-black rule

| Function | Part (always `-B`) | Notes |
|---|---|---|
| Ethernet / PoE | **NE8FDP-B** | CAT5e feedthrough, max. 4 mm panel |
| Power + USB-NET config (and, on decoders, a second one for the USB-A host port) | **NAUSB-W-B** | USB 2.0 A/B reversible feedthrough, front-mount only, max. panel `unknown` → treat as ≤2 mm in this project (see table below) |
| HDMI in/out incl. loop-out | **NAHDMI-W-B** | max. **2 mm** panel — the tightest of the family |
| SDI (BNC) | **NBB75DFGB** | grounded 75 Ω feedthrough, front-mount only, max. panel `unknown` → treat as ≤2 mm |
| Unused port | **DBA-BL-B** | blanking plate, 3.2 mm flat cover, same M3 pattern |

Never substitute the nickel/undyed part number in a BOM or a model comment — even though the
dimensioned drawings this spec is built from are mostly the nickel part (mechanically assumed
identical per-connector, see `knowledge-lookup`'s black `-B` rule section).

## Part table — cutout ⌀, depth, max panel t, plug allowance, bay depth

All from `lib/mcc/constants.scad`'s `MCC_PANEL_PARTS` table (already-cited, already in the repo —
read that file for the full sourcing comment block above each row) and cross-checked against
`knowledge/neutrik/**`:

| Part | `hole_d` (before `MCC_HOLE_COMP`) | `depth` (connector body) | `max_panel_t` | `plug_len` | `bend` (lateral) | `mcc_bay_depth()` |
|---|---|---|---|---|---|---|
| NE8FDP-B | 24.0 mm | 34.55 mm | 4.0 mm | 25 mm | 10 mm | 59.55 mm |
| NAHDMI-W-B | 23.6 mm | 40.65 mm | 2.0 mm | 35 mm | 15 mm | 75.65 mm |
| NAUSB-W-B | 23.6 mm | 40.55 mm | 2.0 mm | 20 mm | 8 mm | 60.55 mm |
| NBB75DFGB | 23.6 mm | 34.0 mm | 2.0 mm | 40.6 mm | 40.6 mm | 74.6 mm |
| DBA-BL-B | 0 (solid) | 3.2 mm | 4.0 mm | 0 | 0 | 3.2 mm |

**Mini-DIN-8 is not supported by `mcc_panel_cutout()`.** The PTZ/Tally Mini-DIN-8 port stays
internal (`panel:"none"`) on every current SKU (user decision 2026-09-07, architecture.md §5) — it
is not a row in `MCC_PANEL_PARTS` and `panel.scad` has no Mini-DIN-8 branch. A port referencing
`"MINIDIN8"` is a deviation (guarded by an assert in `tests/test_ports.scad`). Research for a
*possible future variant* lives in `knowledge/components/mini-din8-feedthrough.md` only — do not
wire it into the dispatcher without a new user decision.

`mcc_cutout_d(part) = mcc_panel_hole_d(part) + MCC_HOLE_COMP` (`MCC_HOLE_COMP = 0.2`) is the nominal
CAD hole diameter — always call this function, never hand-add the compensation yourself; if
`MCC_HOLE_COMP` is later recalibrated by the `tolerance-ladder` coupon, every call site should move
with it automatically.

`lib/mcc/constants.scad` is actively maintained by a separate workstream and its exact line numbers
move — grep for the constant/comment text (`MCC_PANEL_PARTS`, `MCC_PANEL_SEAT_T`, the `TODO(teamlead)`
markers) rather than trusting a remembered line number from this skill or an old conversation.

## Geometry — what to actually cut

Origin at the cutout center (= geometric center of the mounting-hole rectangle):

| Feature | X | Y | Diameter |
|---|---|---|---|
| Main cutout | 0 | 0 | `mcc_cutout_d(part)`, ≥24.0 mm (etherCON/XLR) or ≥23.6 mm (HDMI/USB/BNC) minimum per drawing |
| Mounting hole A | −9.5 mm | +12.0 mm | `MCC_M3_CLR_D` (3.4 mm) — genuine M3 clearance, looser than the connector's own 3.1–3.5 mm min |
| Mounting hole B | +9.5 mm | −12.0 mm | same |

**Orientation**: the two mounting holes sit diagonally opposite each other (top-left/bottom-right or
top-right/bottom-left), never top/bottom or left/right pairs — this is fixed by the standard, not a
free choice per connector. See the ASCII diagram in `knowledge/neutrik/d-series-cutout.md:18-34` if
you need to double check by eye. `MCC_D_SCREW_PITCH = [19.0, 24.0]` in `constants.scad` is this exact
±9.5/±12.0 pattern already expressed as a pitch pair.

Flange keep-out: reserve the full **26 × 31 mm** flange (`MCC_D_FLANGE`), corner radius **R3.5 mm**
(`MCC_D_FLANGE_R`), as flat unobstructed panel around every cutout — this is what the ≥4 mm web
assert (below) is protecting.

## Panel seat, bosses, and fixing (architecture.md §5)

The connector panel is a **separate 2 mm flat-printed plate in a rabbet** — never a pocket cut
directly into the shell end wall. Rationale in full in architecture.md §5; the two load-bearing
consequences for this skill:

- **Seat thickness**: `MCC_PANEL_SEAT_T = 2.0 mm` — the safe common denominator across the whole
  family (HDMI caps at 2 mm; everything else in this project's part list is treated as ≤2 mm too,
  since NAUSB-W-B and NBB75DFGB's true panel-thickness rating is an open question in
  `knowledge/neutrik/d-series-cutout.md:92-93`). Do not thin below 2.0 mm even for etherCON, which
  officially tolerates up to 4 mm — a uniform seat keeps the panel-plate module parameter-free per
  connector kind.
- **Screw fixing (rev 10, 2026-09-09, GitHub issue #30 — supersedes the pre-#30 heat-set-insert
  boss)**: the Neutrik screw holes (±9.5, ±12.0 mm) sit *inside* the 26×31 flange footprint, so they
  cannot land on shell material outside the flange. The connector's own two screws thread directly
  into a **printed M3×0.5 internal thread** in the same local rear pad, via BOSL2
  `screw_hole(thread=true)` — not into a heat-set insert. Geometry lives in one public module,
  `mcc_thread_pad()` (`lib/mcc/neutrik.scad`), called both by `mcc_neutrik_d_bosses()` (production)
  and by `models/coupons/m3-thread-ladder.scad` (the calibration ladder) — never call BOSL2
  `screw_hole()` directly from `models/**`. Pad OD (`MCC_THREAD_M3_PAD_D = 8.28`) and height
  (`MCC_THREAD_M3_PAD_H = 7.0`) are pinned equal to the pre-#30 boss's own OD/height, so no shell
  wall-window geometry moved when this landed. **Self-tapping directly into 2 mm of ASA is still not
  an approved option** — that remains the reason this is a *pad*, not a thread in the 2 mm plate
  field itself (~4 turns, rejected). The Neutrik **MFD** M3 fixing plate is the documented
  alternative if a pad ever proves impractical for a specific connector, but it adds an SKU per
  connector — don't reach for it as a default.
  - **Print orientation is the reason this is printable at all**: the panel plate prints flange-face
    down, so the pad's bore axis is **vertical**, growing straight up off the bed — the single best
    orientation for a printed internal thread (no bridging, no thread-flank overhang).
  - **`$fn` policy exception, scoped to the thread bore only** (`architecture.md` §3, rev 10): the
    thread bore is `$fn=32`, not the repo's usual `$fn≥64` minimum — BOSL2 `screw_hole()` accepts no
    `circum` argument, so the usual circumscribe mechanism is unavailable, and the measured cost of
    `$fn=64` on a real thread is ~26× the render time and ~38× the STL size of a plain bore (~13×/
    ~19× at `$fn=32`) — see `architecture.md` §3 for the full citation. **The pad's own outer
    cylinder keeps `$fn=64` + `circum=true`** — this exception never extends past the thread bore.
  - **`MCC_THREAD_M3_SLOP` (default 0.05) is the load-bearing tuning constant, not `MCC_HOLE_COMP`.**
    BOSL2 grows an internal thread by `4·$slop` in *diameter* (`lib/BOSL2/screws.scad:753`) — a
    plausible-looking but too-large `$slop` silently erases the entire M3×0.5 thread (only 0.2705 mm
    of nominal radial engagement). Calibrate with `models/coupons/m3-thread-ladder.scad`
    (rungs `[0.02, 0.035, 0.05, 0.065, 0.08]`) before trusting this default — acceptance is **≥5
    insert/remove cycles per pad**, not one successful seat (R28), because a connector gets
    unscrewed for cable service and repeat-cycle stripping is exactly the failure mode a heat-set
    insert existed to prevent.
  - **`MCC_THREAD_FAST` (default `false`, override with `-D MCC_THREAD_FAST=true`)** substitutes a
    plain `MCC_M3_CLR_D` clearance bore for the real thread — fast dev-iteration renders and the
    interactive case-viewer artifact only (same `MCC_SHOW_GHOST` precedent: default `false`/safe,
    opt in via `-D`). **Never** for a release, coupon, or print export — goldens and CI always use
    the real thread.
  - **Out of scope, and don't conflate the two**: the panel *plate's own* 4 retention bosses
    (`_mcc_patch_wall_fixing_bosses()` in `shell.scad`, screwing the plate into the shell's rabbet)
    are a completely different physical system and are **unchanged** — still M3 heat-set inserts.
    Issue #30 only converted the connector-to-plate fixing covered by this section.
- **Print orientation**: the panel plate prints flat, face-down, so its holes are true circles with
  no bridging — see `print-check` for the full orientation rule.
- **Aperture roof in the shell**: the rabbet's roof is a ≤45° self-supporting chamfer, never a flat
  bridge — this is the general shell rule "no unsupported horizontal span over 10 mm anywhere in the
  shell," not specific to the panel.

## Dispatcher contract — `mcc_panel_cutout()` is the only entry point

`panel.scad` owns `mcc_panel_cutout(part, ...)`. `neutrik.scad` is one *provider* behind it, not the
top-level abstraction — today every dispatchable part is a Neutrik D-series part (plus the
`DBA-BL-B` blank), so the dispatcher is single-provider in practice. It stays behind `panel.scad`
rather than being called directly so a second provider (e.g. a future Mini-DIN-8 round-cutout
module, see the note above) can be added later without touching `models/**`.

**If `models/**` ever calls `mcc_neutrik_*` directly instead of `mcc_panel_cutout()`, that is a
layering deviation** — flag it in review, don't just fix it silently; log it per architecture.md §13.

## Multi-connector spacing

No official Neutrik multi-gang drawing exists (open question, `placement-and-depth.md:52-55`) — the
numbers below are an engineering recommendation derived from the flange size, already captured as
`MCC_D_PITCH_H = 32` / `MCC_D_PITCH_V = 36` in `constants.scad`:

- Horizontal (side by side): ≥ 30–32 mm center-to-center (26 mm flange + 4–6 mm keep-out web).
- Vertical (stacked): ≥ 35–38 mm center-to-center (31 mm flange + 4–7 mm keep-out web).
- Widen the web further (6–10 mm) on a thin (≤2.5 mm) wall relying on the surrounding plastic alone
  for stiffness, with no rib/gusset behind it.
- **Max 4 D-connectors per model** (fixed decision, see CLAUDE.md) — if a device's port map wants a
  5th, that's a variant-config decision (drop a port, blank it with DBA-BL-B, or move it to another
  face), not a spacing problem to solve by shrinking the pitch below these numbers.

## Asserts that must hold (Tier 1, in-model)

| Assertion | Bound |
|---|---|
| `mcc_cutout_d(part)` | stays in the sane per-connector band, never blown past the ~0.9 mm/side flange overlap margin |
| D-connector pitch, whenever ≥2 cutouts on one face | ≥ `MCC_D_PITCH_H` horizontal / `MCC_D_PITCH_V` vertical |
| Each flange fits on the panel with ≥4 mm web to the frame | 26×31 mm + margin ≤ available panel area |
| Panel seat thickness | ≤ `mcc_panel_max_t(part)` |
| Clear depth behind the cutout | ≥ `mcc_bay_depth(part)` |
| Connector-fixing thread pad wall (T1-42a, rev 10) | `(pad_d − (major_d + 4·$slop))/2` ≥ `MCC_THREAD_WALL_MIN` (2.0) |
| Connector-fixing thread engagement (T1-42b, rev 10) | `(pad_h − MCC_THREAD_M3_CHAMFER)/MCC_THREAD_M3_PITCH` ≥ `MCC_THREAD_ENGAGE_MIN_TURNS` (3) |
| Connector-fixing residual radial thread engagement vs `$slop` (T1-42c, rev 10 — the one that would have caught a too-large `$slop`) | `0.5·(major_d − minor_d) − 2·$slop` ≥ `MCC_THREAD_ENGAGE_MIN_RADIAL` (0.135) |

The plate's own 4 retention bosses (out of scope for issue #30, see the note above) still follow the
pre-#30 rule: Heat-set boss OD ≥ `MCC_BOSS_MIN_RATIO` (1.8) × insert OD.

## Coupons — how the placeholder numbers get replaced

Two of the five Tier-4 physical coupons (architecture.md §9) exist specifically for this skill's
numbers, and neither has been printed yet — do not treat any `assumed`-confidence figure in
`MCC_PANEL_PARTS` as final until its coupon reports back:

- **`neutrik-tile`** (`models/coupons/neutrik-tile.scad`, not yet written) — one D cutout with the
  2 mm pocket and rear bosses in a 40×45 mm tile. Verifies a real connector actually fits and screws
  down; this is what calibrates `MCC_HOLE_COMP` for real.
- **`depth-mockup`** (`models/coupons/depth-mockup.scad`, not yet written) — holds one panel
  connector at a set distance from a mock device port face so the real patch cable can be tried. This
  is the *only* way to replace the `plug_len`/`bend` placeholders in `MCC_PANEL_PARTS` (currently
  `TODO(teamlead)`-flagged, `confidence:"assumed"`, per the comment block above the table in
  `constants.scad`).
- **`m3-thread-ladder`** (`models/coupons/m3-thread-ladder.scad`, new rev 10, GitHub issue #30) — 5
  printed M3 thread pads at production `pad_d`/`pad_h`/`$fn` (built from the same `mcc_thread_pad()`
  the connector-fixing boss module calls), sweeping `$slop` across `[0.02, 0.035, 0.05, 0.065, 0.08]`.
  Calibrates `MCC_THREAD_M3_SLOP` (default 0.05, `assumed`) — the only way to replace this placeholder
  is a real M3 machine screw threaded and unthreaded ≥5 times per pad (R28).

**Writing a measured result back**: edit the relevant row in `lib/mcc/constants.scad`'s
`MCC_PANEL_PARTS` (or the constant it feeds), replace the value, and update the comment to name the
coupon and the date, e.g. `// measured via neutrik-tile coupon, 2026-09-14, calipers`. Don't change
the `confidence` semantics elsewhere when you do this — a measured value simply replaces an assumed
one at the same key.

See `.claude/skills/neutrik-panel/cutout-cheatsheet.md` for the printable one-page version of the
geometry table above.
