---
name: neutrik-panel
description: Place a Neutrik D-series (or Mini-DIN-8) panel cutout with pocket, rear screw bosses, and spacing/depth asserts; use whenever a model needs a connector cutout — always through mcc_panel_cutout(), never by calling the Neutrik provider module directly.
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
| MINIDIN8 (future variant only) | 12.5 mm (flagged — likely undersized, see the `TODO(teamlead): MINIDIN8's hole_d` comment in `constants.scad`) | 20 mm (assumed) | 3.0 mm (assumed) | 15 mm (assumed) | 10 mm (assumed) | 35 mm |

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
- **Screw fixing**: the Neutrik screw holes (±9.5, ±12.0 mm) sit *inside* the 26×31 flange footprint,
  so they cannot land on shell material outside the flange. Use **local rear bosses** at the two
  screw positions, protruding rearward from the 2.0 mm seat to ~7 mm total, each with an M3 heat-set
  insert (5.7 mm, `MCC_INSERT_M3`). **Self-tapping directly into 2 mm of ASA is not an approved
  option** — the plate is too thin to hold a self-tap reliably. The Neutrik **MFD** M3 fixing plate is
  the documented alternative if a boss ever proves impractical for a specific connector, but it adds
  an SKU per connector — don't reach for it as a default.
- **Print orientation**: the panel plate prints flat, face-down, so its holes are true circles with
  no bridging — see `print-check` for the full orientation rule.
- **Aperture roof in the shell**: the rabbet's roof is a ≤45° self-supporting chamfer, never a flat
  bridge — this is the general shell rule "no unsupported horizontal span over 10 mm anywhere in the
  shell," not specific to the panel.

## Dispatcher contract — `mcc_panel_cutout()` is the only entry point

`panel.scad` owns `mcc_panel_cutout(kind, ...)`. `neutrik.scad` is one *provider* behind it, not the
top-level abstraction, because the Mini-DIN-8 PTZ/Tally port has no D-size equivalent and (for the
future variant) needs a bespoke round cutout with its own flange/fixing pattern reusing only the same
M3 screw grid.

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
| Heat-set boss OD | ≥ `MCC_BOSS_MIN_RATIO` (1.8) × insert OD |

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

**Writing a measured result back**: edit the relevant row in `lib/mcc/constants.scad`'s
`MCC_PANEL_PARTS` (or the constant it feeds), replace the value, and update the comment to name the
coupon and the date, e.g. `// measured via neutrik-tile coupon, 2026-09-14, calipers`. Don't change
the `confidence` semantics elsewhere when you do this — a measured value simply replaces an assumed
one at the same key.

See `.claude/skills/neutrik-panel/cutout-cheatsheet.md` for the printable one-page version of the
geometry table above.
