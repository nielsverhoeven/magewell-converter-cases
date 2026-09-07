# Neutrik D-series cutout cheat-sheet

One page, print-friendly. Full reasoning and sourcing lives in `SKILL.md` and
`knowledge/neutrik/**`; this file is just the numbers.

## Geometry (all D-series parts share this)

```
Origin = cutout center = center of the mounting-hole rectangle

                    19.0 mm (X)
        ┌───────────────────────┐
     ●──┼───┐                   │        ● mounting hole, ⌀3.4 mm (MCC_M3_CLR_D)
        │   │      ○○○○○        │        ○ main cutout, ⌀mcc_cutout_d(part)
  24.0  │   │    ○       ○      │  24.0 mm (Y)
  mm    │   │   ○    +    ○     │
        │   │    ○       ○      │
        │   │      ○○○○○        │
        │   │                ┌──┼──●
        └───────────────────────┘
Mounting hole A: (-9.5, +12.0)      Mounting hole B: (+9.5, -12.0)
Flange: 26.0 x 31.0 mm, corner radius R3.5 mm
```

## Part table (always the black `-B` variant)

| Part | hole_d (min) | +MCC_HOLE_COMP | depth | max_panel_t | plug_len | bend | bay_depth |
|---|---|---|---|---|---|---|---|
| NE8FDP-B (etherCON) | 24.0 mm | 24.2 mm | 34.55 mm | 4.0 mm | 25 mm | 10 mm | 59.55 mm |
| NAHDMI-W-B (HDMI) | 23.6 mm | 23.8 mm | 40.65 mm | **2.0 mm** | 35 mm | 15 mm | 75.65 mm |
| NAUSB-W-B (USB A/B) | 23.6 mm | 23.8 mm | 40.55 mm | 2.0 mm | 20 mm | 8 mm | 60.55 mm |
| NBB75DFGB (BNC/SDI) | 23.6 mm | 23.8 mm | 34.0 mm | 2.0 mm | 40.6 mm | 40.6 mm | 74.6 mm |
| DBA-BL-B (blank) | — (solid) | — | 3.2 mm | 4.0 mm | 0 | 0 | 3.2 mm |

Mini-DIN-8 is **not** in this table and **not** supported by `mcc_panel_cutout()` — the PTZ/Tally
port stays internal (`panel:"none"`) on every current SKU. Future-variant research only, in
`knowledge/components/mini-din8-feedthrough.md`.

All rows sourced in `lib/mcc/constants.scad`'s `MCC_PANEL_PARTS` comment block; ultimate sources are
`knowledge/neutrik/d-series-cutout.md` and `knowledge/neutrik/placement-and-depth.md`.

## Fixed rules

- Panel seat thickness: **2.0 mm** everywhere (the safe common denominator, even for etherCON which
  officially tolerates up to 4 mm).
- Fixing: rear bosses + M3 heat-set insert (5.7 mm). Never self-tapping into 2 mm ASA.
- Max 4 D-connectors per model.
- Spacing: ≥32 mm horizontal / ≥36 mm vertical center-to-center (`MCC_D_PITCH_H`/`MCC_D_PITCH_V`).
- Entry point: `mcc_panel_cutout(kind, ...)` only — never `mcc_neutrik_*` from `models/**`.
