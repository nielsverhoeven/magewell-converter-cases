# Neutrik D-series knowledge base

> **Project rule: always the black `-B` variant.** Every Neutrik part used in this project is the
> black-housing SKU, no exception: **NE8FDP-B** (etherCON), **NAUSB-W-B** (USB A/B), **NAHDMI-W-B**
> (HDMI), **NBB75DFGB** (BNC/SDI), **DBA-BL-B** (blank). Most dimensioned drawings below were pulled
> from the nickel/undyed part number (color-only difference, assumed mechanically identical, flagged
> per-part as "not independently re-verified" in each `connectors/*.md` file) — that assumption is
> safe for CAD; treat it as unconfirmed only if a physical coupon ever contradicts it. See
> `.claude/skills/neutrik-panel/SKILL.md` for the full part table and cutout spec.

Research reference for designing OpenSCAD panel cutouts for Neutrik D-series ("D-shape"/"D-size")
feedthrough connectors used on the 3D-printed Magewell Pro Convert NDI converter cases. Built
2026-09-07 by fetching Neutrik's own product pages and dimensioned CAD drawings (cross-checked
against multiple independent parts) plus a handful of distributor/community sources for
corroboration only. See `sources.md` for the full URL list and fetch dates.

## How to use this knowledge base

1. **Start with `d-series-cutout.md`** — the cutout geometry, mounting-hole pattern, and flange
   footprint are shared by every connector below. This is what an OpenSCAD `d_series_cutout()`
   module should implement.
2. **Check `placement-and-depth.md`** — for how much internal depth to reserve behind each cutout,
   and how far apart to place multiple cutouts.
3. **Look up the specific connector family** under `connectors/` for part numbers, mating cable
   connectors, electrical ratings, and per-connector quirks (panel thickness limits, grounding,
   IP rating).

## Summary table — recommended part per function

| Function | Recommended chassis part | Mating cable connector | Depth behind panel | Notes |
|---|---|---|---|---|
| **Ethernet (etherCON)** | **NE8FDP** (CAT5e feedthrough) or **NE8FDX-P6** (CAT6A feedthrough, if 10G is needed) | NE8MX (CAT5e) / NE8MX6 (CAT6A) | 34.55–36.3 mm (NE8FDP, sourced) | Front or rear mount, panel ≤4 mm. See `connectors/ethercon.md`. |
| **USB (A/B)** | **NAUSB-W** (USB 2.0) or **NAUSB3** (USB 3.0, less verified) | NKUSB-* | 40.55 mm (NAUSB-W, sourced) | Front mount only. No true D-size USB-C — see below. `connectors/usb.md`. |
| **USB-C** | **Not available in D-size.** Neutrik's USB-C is the separate mediaCON® system (different footprint) | n/a | n/a | Open question if USB-C is required — plan a non-D-series cutout or an external adapter. `connectors/usb.md`. |
| **HDMI** | **NAHDMI-W** (HDMI 2.0 feedthrough) | any standard HDMI cable (no dedicated Neutrik plug found) | 40.2–40.65 mm (sourced) | Front or rear mount, panel ≤2 mm — the tightest panel-thickness limit of this whole family. `connectors/hdmi.md`. |
| **SDI / BNC (75 Ω)** | **NBB75DFG** (grounded, default) or **NBB75DFI** (isolated, if multiple BNCs on one conductive panel) | NBNC75BLP9X | 34 mm (NBB75DFG, sourced) | Front mount only. True 75 Ω, VSWR data to 3 GHz — 12G-SDI rating not confirmed. `connectors/bnc-sdi.md`. |
| **DC power (~12 V)** | **NC4FD-L-1** (female chassis receptacle, 4-pole XLR) | (not looked up in this pass) | ~21.7 mm (estimated, not independently drawn) | No D-size barrel jack exists at Neutrik. Pin 1(−)/pin 4(+) is an *industry* convention, not Neutrik-enforced — document it explicitly in this project. `connectors/dc-power.md`. |
| **Audio (1/4"/6.35 mm)** | **NJ3FP6C** (locking phone jack) | standard EIA RS-453 plugs | not independently drawn | 3.5 mm D-size equivalent not confirmed to exist. `connectors/audio.md`. |
| **Unused cutout** | **DBA-BL** blanking plate | n/a | 3.2 mm (flat cover) | Same mounting pattern as every live connector — cleanest source for the hole-spacing dimensions. `connectors/blanking-and-caps.md`. |

## Files in this knowledge base

- `README.md` — this file
- `d-series-cutout.md` — the shared cutout specification (geometry, hole pattern, flange, panel
  thickness, mounting hardware) — read this first
- `connectors/ethercon.md` — NE8FDP, NE8FDX-P6, NE8FDY-C6 and mating NE8MX/NE8MX6 family
- `connectors/usb.md` — NAUSB-W, NAUSB3, and the USB-C/mediaCON situation
- `connectors/hdmi.md` — NAHDMI-W
- `connectors/bnc-sdi.md` — NBB75DFG/NBB75DFI and mating NBNC75BLP9X
- `connectors/dc-power.md` — NC4FD-L-1/NC4MD-L-1 (XLR4) and the "no D-size barrel jack" finding
- `connectors/audio.md` — NJ3FP6C and the 3.5 mm open question
- `connectors/blanking-and-caps.md` — DBA-BL and SCDX dust covers
- `placement-and-depth.md` — depth-behind-panel table, multi-gang spacing guidance, cable-clearance
  estimates, grounding quick reference
- `sources.md` — every URL used, with fetch date and what it provided; includes failed fetch
  attempts for transparency

## Headline findings (confidence noted)

- **Cutout is a single circular hole**, not a stadium/rounded-rect shape as some hobbyist sources
  describe — confirmed on five independent official Neutrik drawings. **High confidence.**
- **Cutout diameter**: ≥24.0 mm (etherCON/XLR) or ≥23.6 mm (HDMI/USB/BNC), minimum-tolerance
  ("≥Ø…") in all official drawings — safe to cut slightly larger. **High confidence.**
- **Mounting-hole pattern**: two holes, diagonally opposite, forming a 19.0 × 24.0 mm rectangle
  between hole centers (±9.5 mm / ±12.0 mm from the cutout center), hole diameter 3.1–3.5 mm
  depending on connector. Confirmed on six independent drawings including the blanking plate (the
  cleanest reference, since it has no other features). **High confidence.**
- **Flange footprint**: 26 × 31 mm, R3.5 mm corners, confirmed on every drawing examined. **High
  confidence.**
- **Depth behind panel** ranges from ~21.7 mm (solder-cup XLR) to ~40.65 mm (HDMI/USB
  feedthroughs) — see the table above. **High confidence for the specific parts drawn (NE8FDP,
  NAHDMI-W, NAUSB-W, NBB75DFG, XLR3); estimated by analogy for DC-power XLR4 and NBB75DFI.**
- **No D-size DC barrel jack** and **no true D-size USB-C** exist in Neutrik's catalog as browsed in
  this pass. **Medium-high confidence** (based on category browsing, not exhaustive).
- **Multi-gang spacing** has no confirmed official Neutrik figure — current guidance (30–32 mm
  horizontal / 35–38 mm vertical center spacing) is derived from the flange size plus a weak
  third-party corroboration (Penn-Elcom rack panels). **Low-medium confidence — flagged as an open
  question.**

## Open questions (full list)

See the "Open questions" section at the end of each file. The most design-relevant ones:

1. Real Neutrik multi-gang D-series spacing drawing (not found — see `placement-and-depth.md`).
2. Panel thickness rating for NBB75DFG, NAUSB-W, NC4FD-L-1/NC4MD-L-1, NJ3FP6C (not stated on the
   datasheets fetched — etherCON and HDMI are the only families with an explicit number).
3. Exact mating-cable plug/boot lengths for internal patch-cable clearance planning (only cable OD
   ranges were found, not overall plug lengths).
4. Whether "A-series" (mentioned in the original brief) is a distinct real Neutrik standard relevant
   to this project, or a mix-up with the round (non-D) XLR chassis series.
5. Whether a dedicated 12G-SDI-rated D-series BNC part exists.
6. Exact depth-behind-panel for NC4FD-L-1/NC4MD-L-1 and NBB75DFI (estimated by analogy only).
