# Project status and next milestone — updated 2026-09-08

Working memory for agents resuming this repo. Keep it short and current; move history to
`CHANGELOG.md` and decisions to `architecture.md` / `layout-patch-wall.md`.

## State on disk (branch `feature/repo-setup`, PR #1 → `main`, CI green)

| Area | State | Notes |
|---|---|---|
| `knowledge/**` | done | Magewell (22 files + Fishtail STL), Neutrik (10 + official drawings/STEP), components (fans, fasteners, cables, PoE splitters, Mini-DIN8), design (FDM + thermal). Sources cited; `unknown` where unverifiable; inconsistencies resolved 2026-09-08. |
| Software | done | OpenSCAD nightly 2025.09.07 (`C:\Program Files\OpenSCAD (Nightly)`), Bambu Studio 02.08.02, BOSL2 submodule `lib/BOSL2` (SHA 804028c), `.venv` with trimesh + pyyaml. |
| `.claude/skills/*` (9) | done | knowledge-lookup, openscad-authoring, openscad-render, neutrik-panel, device-portmap, new-case-variant, print-check, bom-update, git-flow. |
| `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `BOM.md`, PR template | done, current | Branching = simplified Git Flow (`feature/*` → `main`, tags). BOM filled for the 8 priority SKUs + coupon test kit. |
| `scripts/build.py`, `render.ps1`, CI `render.yml` | done, verified | Pinned AppImage + sha256 + runtime libs + stray-file guard; triggers `main`, `v*`, PRs to `main`, manual. |
| `lib/mcc/*.scad` (L0/L1), `lib/mcc/devices/*.scad` (8), `models/coupons/*.scad` (6), `tests/test_*.scad` (5), `tests/golden/coupons/*.json` (6) | done, verified | `build.py all`: smoke 5/5, render 6/6, check 8/8, goldens 6/6. Captive side bolt (flush, D-13), `side_bolt` port records, floor tripod insert, splitter default `DONGLE-75x40x20`. |
| `.claude/knowledge/architecture.md` (rev 4), `layout-patch-wall.md` (rev 3) | current | D-01…D-13 recorded; deviations D1–D3 resolved; open risks R16, R17, R20. |
| **Not written yet** | — | L2 geometry `shell.scad`, `cradle.scad`, `mounts.scad`, `vents.scad`; `models/<slug>/case.scad` assemblies. |

## Fixed decisions (summary — full list in CLAUDE.md, rationale in architecture.md)

Bambu Lab X1 Carbon, ASA, no TPU; OpenSCAD nightly + BOSL2; priority devices HDMI/SDI Plus,
HDMI/SDI TX, NDI decoders; black `-B` Neutrik only; Mini-DIN-8 stays internal; loop-out outside;
side-exit with ONE patch wall (≤4 D slots); passive-first + parametric fan bay + reserved dongle
splitter bay (D-12: +20 mm end zone in every variant); tongue-and-groove lid with 6 captive M3
thumbscrews; captive slotted 1/4"-20 side bolt + DIN 6799 E-clip, flush boss (D-13, `MCC_GAP_FAR`
16); case height 51 mm; straight HDMI plugs; VESA 75 + Fishtail M4 + strap slots + stacking
profile; envelopes compact 194.9 × 159.9 × 51, plus 211.5 × 166.4 × 51 (base and lid on separate
plates); simplified Git Flow.

## Next milestone: L2 geometry + case assemblies (new `feature/*` branch off `main`)

Gate before starting (Tier 4, `architecture.md` §9):
1. Print the six coupons on the X1C (3MF files delivered to the user; forms in
   `models/coupons/README.md`) and write the measured values into `lib/mcc/constants.scad`:
   `MCC_CLR_TG` (tg-ladder), `MCC_INSERT_M3.hole_d` (insert-boss), `MCC_HOLE_COMP` (neutrik-tile),
   `MCC_PANEL_PARTS[*].plug_len` (depth-mockup — replaces the weakest assumption, `ez(hdmi_a)`),
   `MCC_CLR_SLIDE/PRESS` (tolerance-ladder), side-bolt stack + E-clip size (side-bolt coupon).
2. User measurements (M1–M5 in `architecture.md` §12): side 1/4"-20 hole X (from the short end),
   Z (from the bottom; R17: |v| ≤ 1.7 mm for the ⌀18 pad) and which long side per SKU; thread
   depth; the dongle splitter's real dimensions; DIN 6799 clip figures; screw head ⌀/height.
3. Then: researcher plan → architect fit-check → developer implements `shell.scad` (patch-wall
   aperture + rabbet, reservation rule, side-bolt keep-out ∪ strip, R20 taller intake band),
   `cradle.scad`, `mounts.scad` (floor rule), `vents.scad`, then `models/<slug>/case.scad` via the
   `new-case-variant` skill, goldens, BOM per variant, `print-check` before the first full print.

## Known gaps carried over

- Mating-plug lengths `assumed` (etherCON 25, HDMI 35, USB-B 20, BNC 40.6 bend) → depth-mockup.
- NAUSB-W / NBB75DFG panel-thickness rating unknown (designing to a 2.0 mm seat).
- Magewell Fishtail hole pitch unknown → derive from `knowledge/magewell/assets/magewell-fishtail-bracket.stl`.
- Device weights unpublished; fan presence in HDMI Plus / SDI Plus contradictory in Magewell docs.
- Intake vent area (R20) must be re-derived when `vents.scad` is written.
