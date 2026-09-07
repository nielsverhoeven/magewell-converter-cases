---
name: knowledge-lookup
description: Resolve any dimension, part number, or spec question about Magewell devices, Neutrik connectors, or case-building components from knowledge/**, citing file:line; use whenever a number is needed for a .scad file, a BOM, or a design decision, and never invent a figure — return unknown instead.
---

# knowledge-lookup

`knowledge/**` is sourced, cited product research. It is read-only reference data — never edit it as
a side effect of a design task; if you find an error, flag it to the user instead of "fixing" a
source you didn't author. This skill is about **finding** a fact fast and citing it correctly.

## The one rule that matters

**Every dimension used anywhere in this repo (a `.scad` constant, a BOM row, a design argument)
traces to `knowledge/<file>.md:<line>`, or is explicitly `unknown`/`assumed`.** If you cannot find a
sourced figure after checking the files below, say so — return `unknown` in the answer and, if it
feeds a constant, mark it `confidence:"assumed"` with a `TODO` comment. Never fill a gap with a
plausible-sounding number. A wrong dimension here becomes a part that doesn't fit a connector that
costs real money.

## Directory map

```
knowledge/
  README.md                        index of everything below (create/maintain this)
  magewell/
    README.md                      device table (SKU, family, size, power, op-temp, fan)
    housing-families.md             chassis dims, face-by-face port layout, case-design implications
    power-and-thermal.md            full power/thermal table, fan contradiction detail
    accessories.md                  L-bracket, Fishtail bracket, rack kits
    models/<slug>.md                one file per device SKU — identity/physical/ports/power/mounting
    sources.md                      every source URL
  neutrik/
    README.md                      part-per-function summary table (read this first)
    d-series-cutout.md              THE shared cutout spec: geometry, hole pattern, flange, panel-t
    placement-and-depth.md          depth-behind-panel table, multi-gang spacing, grounding
    connectors/{ethercon,usb,hdmi,bnc-sdi,dc-power,audio,blanking-and-caps}.md   per-family detail
    sources.md
  components/
    README.md
    fans.md                        Noctua fan lineup, mounting patterns, power draw
    fasteners-and-hardware.md      heat-set inserts, screws, latches, magnets, feet
    cables.md                      port-to-wall depth clearance by connector type
    poe-splitters.md               PoE splitter candidates, dimensions, wiring architecture
    mini-din8-feedthrough.md       PTZ/Tally port panel options (future variant only — see CLAUDE.md)
    sources.md
  design/
    README.md                       flags the known cross-file numeric inconsistencies — read first
    fdm-rugged-enclosure-guidelines.md   material, wall/rib/fillet rules, tolerances, ventilation
    thermal-guidelines.md          convection/fan-sizing math, vent placement
```

## Lookup procedure

1. Guess the topic → jump straight to the file from the map above. When unsure, start at the
   relevant `README.md` (each subdirectory has one) — it one-line-summarizes every file in it.
2. Read the actual line, not just the table caption — the `Read` tool's line numbers are exact and
   are what you cite.
3. Cite as `knowledge/<path>.md:<line>` or `:<start>-<end>` for a range. Cite the *narrowest* range
   that supports the number, not the whole file.
4. If two files disagree, check `knowledge/design/README.md` — "Known inconsistencies to resolve"
   lists every currently-known cross-file conflict (fan current draw, fan max power, insert hole
   diameter) with a recommended resolution. If your conflict isn't listed there, surface it rather
   than silently picking a side.

## Confidence / flag vocabulary

| Flag | Meaning | What to do with it |
|---|---|---|
| `unknown` | Not published anywhere found | Do not use for a real cutout/assert. Escalate or measure. |
| `(estimated from image)` | Read off a product photo, not a spec sheet | Usable for layout planning, not for a load-bearing dimension without a coupon check. |
| `(retailer, unverified)` | Fallback only, never a substitute for an official figure | Do not use if any official figure exists, even an approximate one. |
| `assumed` | Engineering estimate, no source at all | Must carry a `TODO` + the reasoning; replace via the relevant coupon (`neutrik-panel` skill, Tier 4). |
| A `*` on a knowledge-base table value | Flags a contradiction between sources | Read the note under the table before using the value. |

These flags map directly onto the port-map `confidence` field (`measured|drawing|manual|photo|assumed`,
architecture.md §7) and the panel-part table's own `confidence` column in
`lib/mcc/constants.scad` — don't invent a different scale.

## The black `-B` rule

Every Neutrik part used in this project is the **black `-B` variant**, with no exception: NE8FDP-B,
NAUSB-W-B, NAHDMI-W-B, NBB75DFGB, DBA-BL-B. Most of the underlying dimensioned drawings in
`knowledge/neutrik/**` were pulled from the nickel/undyed part number (color-only difference,
mechanically assumed identical, flagged per-part as "not independently re-verified" — e.g.
`knowledge/neutrik/connectors/hdmi.md:62` "Confirm NAHDMI-W-B mechanical dimensions match NAHDMI-W
exactly (assumed, color-only difference)"). Treat that assumption as safe for CAD; if a coupon print
ever contradicts it, escalate immediately, not silently.

## 20 most-used facts (verified file:line)

| # | Fact | Value | Source |
|---|---|---|---|
| 1 | Pro Convert Plus chassis size | 117.5 × 66.7 × 23.4 mm | `knowledge/magewell/housing-families.md:14` |
| 2 | Pro Convert Compact/TX chassis size | 100.9 × 60.2 × 23.3 mm | `knowledge/magewell/housing-families.md:99` |
| 3 | D-series cutout diameter | ≥24.0 mm (etherCON/XLR) or ≥23.6 mm (HDMI/USB/BNC); 24.2–24.4 mm recommended nominal | `knowledge/neutrik/d-series-cutout.md:36-43` |
| 4 | D-series mounting-screw pitch | ±9.5 mm horiz (19.0 mm hole-to-hole), ±12.0 mm vert (24.0 mm hole-to-hole), diagonal orientation | `knowledge/neutrik/d-series-cutout.md:47-56` |
| 5 | D-series flange footprint | 26.0 × 31.0 mm, corner radius R3.5 mm | `knowledge/neutrik/d-series-cutout.md:74-76` |
| 6 | Depth behind panel, NE8FDP (etherCON) | 34.55 mm front-mount / 36.3 mm rear-fixed | `knowledge/neutrik/placement-and-depth.md:12-13` |
| 7 | Depth behind panel, NAHDMI-W (HDMI) | 40.65 mm front-mount / 40.2 mm rear-fixed | `knowledge/neutrik/placement-and-depth.md:14-15` |
| 8 | Depth behind panel, NAUSB-W (USB) | 40.55 mm, front-mount only | `knowledge/neutrik/placement-and-depth.md:16` |
| 9 | Depth behind panel, NBB75DFG (BNC) | 34.0 mm, front-mount only | `knowledge/neutrik/placement-and-depth.md:17` |
| 10 | HDMI panel-thickness cap | max. 2 mm — the tightest of the whole family | `knowledge/neutrik/d-series-cutout.md:90` |
| 11 | Multi-gang D-connector spacing (engineering recommendation, not an official Neutrik spec) | ≥30–32 mm horizontal, ≥35–38 mm vertical center-to-center | `knowledge/neutrik/placement-and-depth.md:42-43` |
| 12 | M3 heat-set insert print/drill hole | ~4.0 mm nominal (community consensus); ASA/ABS CAD-pocket cross-check 4.29 mm | `knowledge/components/fasteners-and-hardware.md:22` and `:60` |
| 13 | M3 heat-set insert length (Ruthex RX-M3x5.7) | 5.7 mm | `knowledge/components/fasteners-and-hardware.md:17` |
| 14 | Fan default, Noctua NF-A4x10 5V | 40×40×10 mm, 32×32 mm mounting spacing, 0.044 A typ / 0.05 A max | `knowledge/components/fans.md:13-22` |
| 15 | PoE-splitter placeholder, PoE Texas GAT-USBC | 114 × 51 × 25 mm, 85 g | `knowledge/components/poe-splitters.md:58` |
| 16 | Device power path | 5 V via USB-B (bundled 5 V/2.1 A adapter) or PoE 802.3af via RJ45 | `knowledge/magewell/housing-families.md:29-33` |
| 17 | Device operating temperature | 0–45 °C (Plus family), 0–40 °C (Compact/TX family) | `knowledge/magewell/README.md:20` (Plus row), `:22` (TX row) |
| 18 | Mini-DIN-8 PTZ/Tally port | No Neutrik D-size panel-mount equivalent exists | `knowledge/magewell/housing-families.md:84-86` |
| 19 | BNC/SDI cable bend radius (Belden 4855R, governs BNC bay depth) | 40.6 mm | `knowledge/components/cables.md:63` |
| 20 | Rib design rule | thickness ≤ ~60% of adjoining wall; height ≤ ~3× rib thickness | `knowledge/design/fdm-rugged-enclosure-guidelines.md:67-68` |

Spot-checked by direct grep at the time this skill was written — line numbers are exact matches, not
approximations. If a knowledge file is later edited, these line numbers can drift; re-grep before
trusting an old citation blindly, and update this table if you notice drift.

## Common mistakes

- Citing a table's caption line instead of the row that actually has the number.
- Using a `(retailer, unverified)` figure when an official (if approximate, `~`) figure exists a few
  rows away — always prefer the official figure even if it's vaguer.
- Treating the nickel/undyed Neutrik drawing numbers as automatically true for the `-B` part without
  noting the "not independently re-verified" caveat that almost every `connectors/*.md` file carries.
- Forgetting that `mini-din8-feedthrough.md` is research for a **future** variant — the current fixed
  decision is `panel:"none"` for this port; don't wire it into a device file's cutout without an
  explicit user request to build that variant.

## Worked examples

**"What panel thickness does the BNC connector need?"**
1. Topic is a Neutrik connector spec → `knowledge/neutrik/README.md`'s summary table points at
   `connectors/bnc-sdi.md` for BNC-specific detail and `d-series-cutout.md` for the shared spec.
2. `d-series-cutout.md`'s §3 panel-thickness table (line 92) says NBB75DFG's rating is "not stated on
   datasheet; front-mount only — treat as ≤ 3 mm pending drawing confirmation (**open question**)".
3. Answer: **`unknown` officially; this project's design constant (`MCC_PANEL_SEAT_T = 2.0 mm`,
   `lib/mcc/constants.scad:71-73`) treats every connector uniformly at 2.0 mm regardless**, cited to
   `knowledge/neutrik/d-series-cutout.md:92` for the open question and `constants.scad:71-73` for the
   project's actual resolution. Don't answer "3 mm" — that's the fallback ceiling from the table, not
   what the project actually builds to.

**"How deep does the internal cavity need to be behind an HDMI connector?"**
1. → `knowledge/neutrik/placement-and-depth.md` (depth-behind-panel is its whole subject).
2. Line 14: NAHDMI-W front-mount depth is 40.65 mm — that's the *connector body alone*.
3. §3's table (lines 66-69) adds the mating-plug/cable-bend allowance: "~65-75 mm" suggested total,
   explicitly flagged as "engineering estimate, not sourced."
4. `lib/mcc/constants.scad`'s `MCC_PANEL_PARTS` already encodes this as `mcc_bay_depth("NAHDMI-W-B")
   = 40.65 + 35 = 75.65 mm` — cite both the knowledge-base range (for the reasoning) and the actual
   constant (for the number a render will use), and flag that the `plug_len` figure is
   `confidence:"assumed"` pending the `depth-mockup` coupon (see `neutrik-panel`).
