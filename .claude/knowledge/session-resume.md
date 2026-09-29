# Project status and next milestone — updated 2026-09-28

Working memory for agents resuming this repo. Keep it short and current; history lives in
`CHANGELOG.md` and the GitHub Releases, decisions in `architecture.md` / `layout-patch-wall.md`.

## State on `main`

| Area | State | Notes |
|---|---|---|
| `knowledge/**` | done | Magewell (22 files + Fishtail STL), Neutrik (drawings/STEP), components (fans, fasteners, cables, PoE splitters, Mini-DIN8), design (FDM + thermal). Sources cited; `unknown` where unverifiable. |
| Software | done | OpenSCAD nightly 2026.09.23 (local + CI), Bambu Studio 02.08.02.61 (local + CI AppImage), BOSL2 submodule (pinned), `.venv` from requirements.txt (trimesh, shapely, rtree, manifold3d, mapbox-earcut). cadquery-ocp (STEP) has no wheel for local Python 3.14 — STEP runs in CI only. |
| `.claude/skills/*` (10) | done | knowledge-lookup, openscad-authoring, openscad-render, neutrik-panel, device-portmap, new-case-variant, print-check, bom-update, git-flow, **bambu-studio** (CLI slicer gate, warning probes, opening projects for review). |
| Library `lib/mcc/**` | done, verified | L0 constants/util/ports/layout, L1 neutrik/fasteners/fan/poe_splitter/ghost, L2 shell/panel/cradle/mounts/vents; 8 device data files (positions `photo`/`assumed`). |
| Cases `models/<slug>/case.scad` (8) | done, verified | HDMI TX, SDI TX (compact, 3 slots); NDI to HDMI, NDI to SDI, NDI to AIO (compact, 4 slots); HDMI Plus, SDI Plus, NDI to HDMI 4K (Plus, fan fitted). Goldens for base/lid/panel (+ `base_fan` on NDI to HDMI). |
| Coupons `models/coupons/*.scad` (6) | done, verified | neutrik-tile, depth-mockup, tg-ladder, insert-boss, tolerance-ladder, side-bolt — **not yet printed**. |
| Print-ready exports | done, verified (2026-09-28) | Print pose + Bambu Studio projects per part and per case, `review.3mf`; **every part slices with zero Bambu Studio warnings** (architecture §8 rev 13, §13 D26–D33). Top of the panel frame is now a lid lip (D32); tv-bracket retired (D47); rail latch off pending #46 (D28). Empirical slicer rules: `bambu-slicer.md`. |
| Tooling / CI / releases | done, verified | `render.yml` = PR gate: smoke + six parallel "Validate parts — group k of 6" jobs (`build.py ci`: render → check → golden → Bambu slicer → STEP per part) + `render` aggregator (required check), ≈ 3 min; `release.yml` = automatic pre-release per merge with per-device zips (STL + 3MF + STEP + manifest), slug-prefixed STEPs, SHA256SUMS. Releases v0.1.0 … v0.8.x. |
| Architecture records | rev 7 | `architecture.md` + `layout-patch-wall.md` (§16 fit-check of all 8 SKUs). Open non-blocking: R20 intake vent margin (~1.6 % on BNC compact SKUs), T1-30 not in-model, `mounts.scad` floor non-overlap assert missing, `mcc_warn_unmeasured()` not wired (build.py `confidence` parses device files instead). |

## Open decisions for the user (2026-09-28)

- **Material saving** (measured: compact case ≈ 272 g, Plus ≈ 296 g; process settings move < 2 %,
  so savings are geometric). Within fixed decisions: A) lid-fastener bosses wall-hung instead of
  floor-to-top pillars (~6 g/case), C) deck rib pitch 22 → 30 mm (~5 g). Touching fixed decisions:
  B) deck ribs 3 → 2 mm (~8 g, D22), D) 4 walls (~6 g), E) floor 3 → 2 mm (~24 g), F) lid 3 → 2 mm +
  ribs (~20 g) — E/F need a drop-test coupon first. Awaiting the user's pick.
- **Rail latch redesign** — issue #46 (D28).

## Next milestone: Tier 4 — measure, then print

1. **Print the six coupons** on the X1 Carbon (ASA; forms in `models/coupons/README.md`, log in
   `print-log.md`; 3MF/STEP in every release zip `coupons-<version>.zip`).
2. **Write measured values into `lib/mcc/constants.scad`** and raise `confidence` to `measured`:
   `MCC_CLR_TG`, `MCC_INSERT_M3.hole_d`, `MCC_HOLE_COMP`, `MCC_PANEL_PARTS[*].plug_len`,
   `MCC_PLUG_AXIAL` (HDMI/BNC straight-plug lengths — the weakest assumption, sets `ez_pos`),
   `MCC_CLR_SLIDE/PRESS`, side-bolt stack + E-clip figures.
3. **User measurements** (architecture §12 M1–M6): side 1/4"-20 hole X/Z/side per SKU (R17: |v| ≤ 1.7 mm
   for the ⌀18 pad), thread depth, dongle splitter dimensions, E-clip, screw head, BNC plug body.
   Also **M62.1** (issue #62, R62.1): buy the lid thumbscrew (small knurled M3, head Ø7–8 mm, ≤ 8 mm
   under the head, M3×6 recommended) and measure head ⌀ across the knurl, head height and length; try it
   in a printed ⌀8 × 1.5 counterbore. A head over ≈ 7.8 mm means a bigger counterbore — an architect
   re-gate (T1-62.1 fires above ⌀8.09), not a constant tweak. Feeds `MCC_LID_CB_D`.
   Also **M63.1** (issue #63, R44/R63.1): weigh one assembled case per family with its device (and the
   fan where fitted; about 0.8 kg `assumed`) — every release force of the top lock scales with it, and it
   is the dummy mass for M15. Then **M15** (rewritten by #63): print `models/coupons/rail-lock` and test
   the roof sag, the play and the lock hanging under that mass, incl. the e-ladder (`LOCK_E` 0.4 / 0.5 /
   0.7); no full-size bracket prints before it passes. Feeds `MCC_RAIL_ROOF_CLR` and
   `MCC_RAIL_LOCK_ENGAGE`. Then **M21** on the first arch bracket print with a real case and device:
   release forces and the one-hand pull-and-slide removal (R63.1).
4. Update the device files (`side_bolt` `pos`, `confidence`), re-render, `golden --update` with
   justification, then `print-check` and the **first full-size print** (NDI to HDMI first).
5. A release with every exported port at `measured` becomes a normal (non-pre) release automatically.

## Later

- IP-decoder family (120 × 79.3 × 24.5, USB-C power, 3.5 mm audio) — new shell family variables.
- R20: taller intake band when measured plug lengths change the end zones; T1-30 as an in-model assert.
- Optional per-variant PoE-splitter fit-out once a measured dongle exists.
