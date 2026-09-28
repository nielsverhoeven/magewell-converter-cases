---
name: neutrik-panel
description: Place a Neutrik D-series connector — straight in the case's patch wall (teardropped seat hole + window, printed M3 threads in the wall, no screw pillars) or in a flat coupon panel — with spacing/depth/web asserts; use whenever a model needs a connector cutout — always through mcc_panel_wall_cut()/mcc_panel_cutout(), never by calling the Neutrik provider module directly.
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

## Seat, fixing and printability — connectors straight in the patch wall (architecture.md §5 rev 14, D36)

There is **no separate connector panel** (user decision 2026-09-28). The connectors mount straight
into the base's 8 mm patch wall: a 3 mm bezel recess (`_mcc_patch_wall_recess()`), then 5 mm of
wall that `mcc_panel_wall_cut()` → `mcc_neutrik_d_wall_cut()` cuts per slot. The base prints
**standing** (open side up), so everything in the wall is designed for a vertical wall:

- **Seat thickness**: `MCC_PANEL_SEAT_T = 2.0 mm` — the safe common denominator across the family
  (HDMI caps at 2 mm, `knowledge/neutrik/d-series-cutout.md:90`). Behind it a slightly larger body
  window runs through the remaining 3 mm.
- **Holes are truncated teardrops** pointing up, both capped at the window's `cap_h` so the roof
  over the opening is ONE flat bridge through the whole wall (≤ `MCC_APERTURE_BRIDGE_MAX`). A seat
  hole capped lower than the window leaves a 2 mm strip open on both faces — Bambu reads it as a
  floating cantilever. Everything the teardrop adds lies inside the 26 × 31 flange.
- **Screw fixing**: the connector's two screws thread into a **printed M3×0.5 thread in the wall
  itself**, through all 5 mm (9 turns). **No pads/pillars behind the wall** — the old plate's rear
  pads (⌀8.28 at 15.3 mm from the centre) reached ~1 mm into the ⌀24.3 hole, which the modeller
  rejected, and standing proud of a vertical wall they would be overhangs. T1-48 asserts ≥
  `MCC_WALL_THREAD_WEB_MIN` (1.2 mm) of wall between each thread and either opening — the
  tightest web in the wall. The thread axis is now **horizontal** in the print: verify on the
  `neutrik-tile` coupon (a standing wall section) before the first case. Never call BOSL2
  `screw_hole()` directly from `models/**`.
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
- **Never add material to the connector's side of the seat plane or inside the hole cylinder** —
  cut the openings *after* anything added nearby (the plate-era bug was pads unioned after the
  hole was cut).
- **Bezel recess roof**: chamfered steeper than 45° (rise 1.2 per mm) so the standing wall never
  overhangs it; at exactly 45° the chamfer ran through the wall's top outer edge and left
  zero-area slivers (parts > 1 in `build.py check`).

## Dispatcher contract — `panel.scad` is the only entry point

`panel.scad` owns `mcc_panel_wall_cut(part, ...)` (the case's patch wall, D36) and
`mcc_panel_cutout(part, ...)` (a flat panel — the `depth-mockup` coupon). `neutrik.scad` is one *provider* behind it, not the
top-level abstraction — today every dispatchable part is a Neutrik D-series part (plus the
`DBA-BL-B` blank), so the dispatcher is single-provider in practice. It stays behind `panel.scad`
rather than being called directly so a second provider (e.g. a future Mini-DIN-8 round-cutout
module, see the note above) can be added later without touching `models/**`.

**If `models/**` ever calls `mcc_neutrik_*` directly instead of the `panel.scad` dispatchers, that is a
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
| Wall web around each connector thread (T1-48, D36) | distance from the thread axis to the seat hole / window outline − (major_d + 4·$slop)/2 ≥ `MCC_WALL_THREAD_WEB_MIN` (1.2) |
| Teardrop cap bridges (T1-34a) | flat width of both teardrops ≤ `MCC_APERTURE_BRIDGE_MAX` (10) |
| Connector-fixing thread engagement (T1-42b) | `(wall_t − MCC_THREAD_M3_CHAMFER)/MCC_THREAD_M3_PITCH` ≥ `MCC_THREAD_ENGAGE_MIN_TURNS` (3); 9 turns in the 5 mm wall |
| Thread pad wall (T1-42a — `mcc_thread_pad()`, the `m3-thread-ladder` coupon only) | `(pad_d − (major_d + 4·$slop))/2` ≥ `MCC_THREAD_WALL_MIN` (2.0) |
| Connector-fixing residual radial thread engagement vs `$slop` (T1-42c, rev 10 — the one that would have caught a too-large `$slop`) | `0.5·(major_d − minor_d) − 2·$slop` ≥ `MCC_THREAD_ENGAGE_MIN_RADIAL` (0.135) |

## Coupons — how the placeholder numbers get replaced

Two of the five Tier-4 physical coupons (architecture.md §9) exist specifically for this skill's
numbers, and neither has been printed yet — do not treat any `assumed`-confidence figure in
`MCC_PANEL_PARTS` as final until its coupon reports back:

- **`neutrik-tile`** (`models/coupons/neutrik-tile.scad`) — a 40×45 mm section of the patch wall
  (5 mm, printed standing on a foot) with one connector cut exactly as in the case (D36). Verifies
  a real connector fits, seats flush and screws into the horizontal printed threads; this is what
  calibrates `MCC_HOLE_COMP` for real.
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
