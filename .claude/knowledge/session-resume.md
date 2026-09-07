# Session resume — paused 2026-09-07 (~16:10)

The kickoff session was paused mid-flight (laptop shutdown). This file says exactly where things
stand and what to do next, in order. Delete it (or move its content to CHANGELOG/issues) once the
`feature/repo-setup` PR is merged.

## State on disk (all on branch `feature/repo-setup`, WIP commit)

| Area | State | Notes |
|---|---|---|
| `knowledge/**` | **done** | Magewell (22 files), Neutrik (10 + assets), components (fans, fasteners, cables, PoE splitters, Mini-DIN8), design (FDM + thermal). Sources cited; `unknown` where unverifiable. |
| Software | **done** | OpenSCAD nightly 2025.09.07 (`C:\Program Files\OpenSCAD (Nightly)`), Bambu Studio 02.08.02, BOSL2 submodule at `lib/BOSL2` (SHA 804028c), `.venv` with trimesh. |
| `.claude/skills/*` (9) | **done** | knowledge-lookup, openscad-authoring, openscad-render, neutrik-panel, device-portmap, new-case-variant, print-check, bom-update, git-flow. |
| `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `BOM.md`, PR template | **done** | `CLAUDE.md` "Current status" and the `neutrik-panel` row ("or Mini-DIN-8") are stale — see step 5. |
| `scripts/build.py`, `render.ps1`, CI `render.yml` | **done, verified** | Pipeline proven on the coupons; CI pinned AppImage + sha256 + runtime libs + stray-file guard; triggers: `main`, `v*` tags, PRs to `main`. |
| `lib/mcc/*.scad` (L0/L1), `lib/mcc/devices/*.scad` (8), `models/coupons/*.scad` (5), `tests/test_*.scad` (4) | **written, NOT verified** | The developer agent was stopped during its final read-through of `constants.scad`, before running the render/smoke verification. Expect small errors. |
| `.claude/knowledge/architecture.md`, `layout-patch-wall.md` | **partially current** | Records: patch-wall topology, Mini-DIN8 internal, D-cutout facts. Does NOT yet record the last three user decisions (see step 4). |

## User decisions taken today (all fixed; also in the teamlead's memory)

Printer Bambu Lab X1 Carbon; OpenSCAD nightly + BOSL2; ASA only, no TPU; priority devices HDMI/SDI
Plus, HDMI/SDI TX, NDI decoders; panel = black `-B` Neutrik only (NE8FDP-B, NAUSB-W-B ×1–2,
NAHDMI-W-B, NBB75DFGB, DBA-BL-B); Mini-DIN-8 PTZ/Tally stays internal; loop-out goes outside;
side-exit layout with ONE patch wall (all connectors in one long side wall, max 4); passive-first +
parametric fan bay (NF-A4x10 5V) + reserved PoE-splitter bay with **dongle-class default envelope
75×40×20 mm (assumed; buy one UCTRONICS U6114/U6115 and measure)**; closure = tongue-and-groove +
captive M3 knurled thumbscrews in heat-set inserts, **6 for lids >180 mm (Plus), 4 for compact**;
**retention = captive 1/4"-20 SLOTTED bolt through the far (non-patch) long wall into the device's
side thread — the device's 1/4"-20 hole is on a long side face (user verified); the bolt must stay in
the case when unscrewed; device lies flat on the floor in a ribbed cradle** (the floor through-bolt
is withdrawn); floor = case 1/4"-20 insert + VESA 75×75 + Fishtail M4 + strap slots + stacking
profile; **case height stays 51 mm (4 mm Z web; the 49 mm proposal was vetoed)**; **no right-angle
HDMI adapter in the default BOM (vetoed) — end zones are sized for straight plugs and measured with
the depth-mockup coupon**; 1 m drop target, 3 mm walls / 5 perimeters; English docs; exports via CI
only; **simplified Git Flow: `feature/*` → `main` via PR, releases via annotated `v*` tags on `main`**
(the user dropped `develop` on 2026-09-08; no `release/*`/`hotfix/*` branches; no git-flow tooling).

## Next steps, in order

1. ~~Verify the library~~ **DONE 2026-09-08**: `build.py all` green (smoke 4/4, render 5/5,
   check 5/5, goldens 5/5 in `tests/golden/coupons/`). The coupon connector selector is now
   `-D connector="NE8FDP-B"` (`part` is reserved for build.py's export name). CI got the missing
   OpenGL/X/Qt runtime libraries for the AppImage.
2. ~~Mini-DIN-8 fix-up~~ **DONE**: `panel:"none"` on every `minidin8` port; `MINIDIN8` removed from
   `MCC_PANEL_PARTS` and the dispatcher; `test_ports.scad` asserts it.
3. ~~Constants fix-up~~ **DONE 2026-09-08**: splitter default `DONGLE-75x40x20`; captive side bolt
   implemented (`mcc_captive_side_bolt_boss/_cut`, keep-out, `side-bolt` coupon, `side_bolt` port
   record in all 8 devices, floor `mcc_case_tripod_insert_*` replaces the through-bolt boss). The
   D-13 flush reconciliation (`MCC_GAP_FAR` 16 derived, `proud` 0, support web, strip keep-out,
   T1-29/T1-31) is the last code step of this branch.
3c. **Architecture is current** (rev 4 / layout rev 3): D-09…D-13 recorded; envelopes compact
   194.9 × 159.9 × 51, plus 211.5 × 166.4 × 51, 6 thumbscrews both; new non-blocking risk R20
   (intake vent area below the thermal heuristic → taller intake band when `vents.scad` is written).
3b. ~~Branching docs~~ **DONE 2026-09-08**: CONTRIBUTING, `git-flow` skill, PR template, CHANGELOG,
   README, ticket-source, CI triggers and CLAUDE.md all describe `feature/* → main`, releases via
   tags; the `gitflow.*` git config was removed.
4. **Re-run the architect** (Opus, single instance) with the brief "record R11/R12/D-04/D-06/D-08
   decisions" — the previous run was stopped before it edited anything. Decisions to record are the
   bold items above; deliverables: update `architecture.md` (§1 envelope H=51 and straight-plug end
   zones, §6 floor rule simplified, §7 `side_bolt` port convention `face [0,-1,0]`, §11 R11/R12
   resolved + new risks, §12, §14) and `layout-patch-wall.md` (device yaw: hole side faces −Y;
   side-bolt boss spec; end-zone formula for straight plugs; splitter 75×40×20; envelopes; asserts;
   D-09 side bolt, D-10 dongle splitter).
5. **CLAUDE.md**: rewrite "Current status" (library + coupons exist, unverified → verified), remove
   "(or Mini-DIN-8)" from the `neutrik-panel` row, update Closure/Retention and Cooling bullets with
   the bold decisions above, envelope ≈ 175–192 × 150–156 × 51 mm.
6. ~~`build.py all` green → open the PR~~ **DONE**: PR #1 `feature/repo-setup` → `main` is open and
   CI-green; merge once the items above land.
7. **Next milestone** (new feature branch): `lib/mcc/shell.scad`, `cradle.scad`, `mounts.scad`,
   `vents.scad`, `models/<slug>/case.scad` for the 8 priority devices — but only after the six
   coupons (`neutrik-tile`, `depth-mockup`, `tg-ladder`, `insert-boss`, `tolerance-ladder`,
   `side-bolt`) are printed on the X1C and measured (forms in `models/coupons/README.md`), and after
   the user measures: the side 1/4"-20 hole position (X from the short end, Z from the bottom —
   R17: |v| ≤ 1.7 mm for the ⌀18 pad — and which side) per SKU, the thread depth, the chosen dongle
   splitter's dimensions, and confirms the DIN 6799 size-5 E-clip figures.

## Known gaps / open questions carried over

- All mating-plug lengths are `assumed` (etherCON 25, HDMI 35, USB-B 20, BNC 40.6 bend) → depth-mockup.
- NAUSB-W / NBB75DFG panel-thickness rating unknown (designing to 2.0 mm seat anyway).
- Magewell Fishtail hole pitch unknown → derive from `knowledge/magewell/assets/magewell-fishtail-bracket.stl`.
- Device weights unpublished; fan presence in HDMI Plus / SDI Plus contradictory in Magewell docs.
- WebSearch budget of the session was exhausted; PoE-splitter and Mini-DIN8 research used WebFetch only.
