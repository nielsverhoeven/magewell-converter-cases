# Project status and next steps — updated 2026-10-04

Working memory for agents resuming this repo, on any machine. Keep it short and current; history
lives in `CHANGELOG.md` and the GitHub Releases, decisions in `architecture.md` (§13 deviations log,
records numbered per GitHub issue) and `layout-patch-wall.md`.

## Where things stand

| Area | State |
|---|---|
| OpenSCAD tree (`lib/mcc/**`, `models/**`, `tests/*.scad`, goldens) | All 8 cases, 6 coupons, `arch-tv-bracket` (now **straight**, #120/#122) and `vertical-tv-bracket`; every part print-ready, zero Bambu Studio warnings (CI slicer gate). **Frozen as the parity oracle** for the Fusion migration (R76.2/Q75.4); a change that cannot wait takes the exception path and lands in OpenSCAD and `cad/` together (D120.3). |
| Exact STEP export (`scripts/csg_to_step.py`) | #119: case base STEPs carried empty sheet shells and zero-area faces at the lid-boss bases; Fusion turned them into open/non-manifold edges (user's Bambu import: 77 / 30). #121 drops empty shells and #123 adds fuzzy 1e-4 booleans + a zero-area-face guard (both merged 2026-10-04). Verified in Fusion: fan base 0 open / 0 non-manifold, clean Bambu import. Records D119.1, D119.2, M119.1. |
| Fusion migration (#75) | Done: #76 data (`cad/params.py`, constants, devices), #77 layout solver, #81 case master C1–C9 (kit `cad/fusion/gen/core`, shared builders `gen/shared`, `gen/case`, OCP replay `cad/fusion/replay`, committed inventory, parity tooling, cad-gates CI job). Open: #78 design rules, #79 runtime (host + probes merged in #103; the live **probe sitting PR-79.3** with the user has not happened yet), #80 CI import path, #82 other seven cases, #83 coupons, #84 brackets (comparison baseline = #122's merge commit `5a885cc`; the plan's `V_ARCH_RISE`/`V_ARCH_ALPHA`/`tv_max` are void), #85 fillets/threads/review loop, #86 cutover. |
| Renders (#74) | PR1 merged (per-case showcase PNGs in releases). PR2/PR3 (GitHub Pages viewer, semi-transparent lid) wait for the user. |
| Fusion helper scripts and snapshots | `tools/fusion-scripts/` (MccShowAll, MccVerifyStep, MccFusionArchive) — manual, see its README. `archive/fusion/` holds committed `.f3d` snapshots, one per case variant and per TV-bracket assembly (#125, D125.1, R125.1: refresh after geometry changes). The hub project also holds the older single design "MCC case variants". |

## Open with the user

- **Duplicate Fusion hub project**: the user already had "Magewell **C**onverter cases"; `MccCaseProject`
  (before its name match ignored case) created "Magewell **c**onverter cases" and saved the design there.
  Ask: move the design into the user's own project? Never delete a hub project without the user's yes.
- **#120 follow-ups**: Q120.1 (orientation cue — teamlead default (a), only the UP arrow; option (b) an
  asymmetric chamfer would change the goldens again); Q120.2 (for sandwich mode: is the lift also free
  along and just above the top VESA row — centre to z 27.6 mm, arms to z 20 mm out to x ±200); Q120.3
  name kept.
- **Q79.1** MccFusionBridge add-in (default no — not merged until the user says yes).
- **Plans and verdicts of #78–#86 live outside git** in `C:\repos-github\mcc-fusion-ref\` on the old
  laptop (≈ 5 MB). They must be copied to a new machine, or committed to `docs/plans/fusion/` — ask the
  user first, and leave out the licence study (`F-fusion-migration.md`); never discuss the licence in
  public GitHub text.
- Material-saving options A–F (2026-09-28), the CLAUDE.md untrusted-text rule (default yes).

## Next steps

1. Refresh `exports/` (render or CI artefacts of the latest `main`) so local STEPs carry the #119 fix and the bracket exports the straight geometry.
2. Physical **Tier 4**: test-print the NDI-to-HDMI case (user, 2026-10-04 — print from the `.3mf`
   projects, not via Fusion), the six coupons, then measurements M1–M6, M15, M63.1, M100.1 (countersunk
   lid screws), M119.1, M120.1 into `lib/mcc/constants.scad` with `confidence: measured`.
3. Fusion: probe sitting PR-79.3 when the user says "start" (`scripts\fusion_run.py probe`, the user
   starts MccRun), then build the case master live; continue #82 → #83/#84 → #85 → #86 serially.

## Working rules agreed with the user (not elsewhere in the repo)

- **Token budget**: work serially; Sonnet/Haiku subagents by default, **Opus only for the
  solution-architect gate** (and verification of findings that will be implemented); short hand-backs.
- **Merge permission**: Fusion-migration PRs may be merged without asking when CI is green, the plan was
  architect-approved and the PR does not touch the OpenSCAD tree. Anything touching `lib/mcc`,
  `models/**/*.scad`, `tests/*.scad` or goldens needs the user's explicit yes.
- **Fusion on the user's PC**: run scripts there only after the user says go; the user grants
  computer-use access per session (Autodesk Fusion, `fusion360.exe`, Bambu Studio). Do not launch
  Fusion through its Start-menu entry while it runs (it prompts for a second instance); bring the window
  forward instead.
- **Agent git hygiene**: each git command plain (no `&&` chains, pipes or heredocs around git); add paths
  explicitly; never zero-byte files; CI runs Python 3.12 on Linux.

## New machine setup

Clone, then `git submodule update --init lib/BOSL2`; `.venv` from `requirements.txt` +
`requirements-step.txt` (cadquery-ocp 8.0.1 now installs on Python 3.14 — local STEP works);
OpenSCAD nightly 2026.09.23; Bambu Studio 02.08.02.61; `python scripts/build.py doctor`. Fusion:
Personal plan, copy `tools/fusion-scripts/*` into its Scripts folder (adjust the paths at their top).
Claude's per-machine memory does not travel — this file and `architecture.md` are the handover.
