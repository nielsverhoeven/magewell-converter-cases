# Project status and next milestone — updated 2026-09-08 (evening)

Working memory for agents resuming this repo. Keep it short and current; history lives in
`CHANGELOG.md` and the GitHub Releases, decisions in `architecture.md` / `layout-patch-wall.md`.

## State on `main`

| Area | State | Notes |
|---|---|---|
| `knowledge/**` | done | Magewell (22 files + Fishtail STL), Neutrik (drawings/STEP), components (fans, fasteners, cables, PoE splitters, Mini-DIN8), design (FDM + thermal). Sources cited; `unknown` where unverifiable. |
| Software | done | OpenSCAD nightly 2025.09.07, Bambu Studio 02.08.02, BOSL2 submodule (pinned), `.venv` with trimesh, pyyaml, cadquery-ocp (STEP). |
| `.claude/skills/*` (9) | done | knowledge-lookup, openscad-authoring, openscad-render, neutrik-panel, device-portmap, new-case-variant, print-check, bom-update, git-flow. |
| Library `lib/mcc/**` | done, verified | L0 constants/util/ports/layout, L1 neutrik/fasteners/fan/poe_splitter/ghost, L2 shell/panel/cradle/mounts/vents; 8 device data files (positions `photo`/`assumed`). |
| Cases `models/<slug>/case.scad` (8) | done, verified | HDMI TX, SDI TX (compact, 3 slots); NDI to HDMI, NDI to SDI, NDI to AIO (compact, 4 slots); HDMI Plus, SDI Plus, NDI to HDMI 4K (Plus, fan fitted). Goldens for base/lid/panel (+ `base_fan` on NDI to HDMI). |
| Coupons `models/coupons/*.scad` (6) | done, verified | neutrik-tile, depth-mockup, tg-ladder, insert-boss, tolerance-ladder, side-bolt — **not yet printed**. |
| Tooling / CI / releases | done, verified | `build.py all --with-step` green; `render.yml` = PR gate (required check on protected `main`); `release.yml` = automatic pre-release per merge with per-device zips (STL + 3MF + STEP + manifest), slug-prefixed STEPs, SHA256SUMS. Releases v0.1.0 … v0.8.x. |
| Architecture records | rev 7 | `architecture.md` + `layout-patch-wall.md` (§16 fit-check of all 8 SKUs). Open non-blocking: R20 intake vent margin (~1.6 % on BNC compact SKUs), T1-30 not in-model, `mounts.scad` floor non-overlap assert missing, `mcc_warn_unmeasured()` not wired (build.py `confidence` parses device files instead). |

## Next milestone: Tier 4 — measure, then print

1. **Print the six coupons** on the X1 Carbon (ASA; forms in `models/coupons/README.md`, log in
   `print-log.md`; 3MF/STEP in every release zip `coupons-<version>.zip`).
2. **Write measured values into `lib/mcc/constants.scad`** and raise `confidence` to `measured`:
   `MCC_CLR_TG`, `MCC_INSERT_M3.hole_d`, `MCC_HOLE_COMP`, `MCC_PANEL_PARTS[*].plug_len`,
   `MCC_PLUG_AXIAL` (HDMI/BNC straight-plug lengths — the weakest assumption, sets `ez_pos`),
   `MCC_CLR_SLIDE/PRESS`, side-bolt stack + E-clip figures.
3. **User measurements** (architecture §12 M1–M6): side 1/4"-20 hole X/Z/side per SKU (R17: |v| ≤ 1.7 mm
   for the ⌀18 pad), thread depth, dongle splitter dimensions, E-clip, screw head, BNC plug body.
4. Update the device files (`side_bolt` `pos`, `confidence`), re-render, `golden --update` with
   justification, then `print-check` and the **first full-size print** (NDI to HDMI first).
5. A release with every exported port at `measured` becomes a normal (non-pre) release automatically.

## Later

- IP-decoder family (120 × 79.3 × 24.5, USB-C power, 3.5 mm audio) — new shell family variables.
- R20: taller intake band when measured plug lengths change the end zones; T1-30 as an in-model assert.
- Optional per-variant PoE-splitter fit-out once a measured dongle exists.
