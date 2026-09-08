# magewell-converter-cases

3D-printable, rugged, single-device cases for Magewell Pro Convert NDI converters used in live
performance. Every external connection leaves the case through a Neutrik D-series panel connector
(always the black `-B` variant) with a short internal patch cable to the device. Modelled in
OpenSCAD nightly + BOSL2, printed in ASA on a **Bambu Lab X1 Carbon** (256 × 256 × 256 mm, enclosed,
AMS; confirmed by the user — every part must print on this machine).

## Language rule

Docs, skills, code comments, commit messages: **English**. Converse with the user in **Dutch** —
they work in Dutch day to day; this file and the knowledge base stay English because they are
shared engineering artefacts.

## Source of truth

**`.claude/knowledge/architecture.md` is the source of truth for intended design** — layering,
naming, `$fn` policy, the port-map record shape, export/test policy. Code or a plan that disagrees
with it is either a deviation to fix or an intended evolution to record there — never silently
absorbed. Consult `solution-architect` before structural changes; see Team routing below.

Two knowledge trees, do not merge them:

| Tree | Contents |
|---|---|
| `knowledge/**` | Sourced product/domain research (Magewell devices, Neutrik connectors, components, design guidelines). Stable, cited, third-party. Index: `knowledge/README.md`. |
| `.claude/knowledge/**` | Agent working memory for *this* repo: `architecture.md`, `testing.md`, `ticket-source.md`. Not sourced research — don't put product facts here. |

## Fixed decisions (do not re-open without a user decision)

- **Priority devices**: Pro Convert HDMI Plus / SDI Plus (Plus chassis 117.5×66.7×23.4 mm), HDMI TX
  / SDI TX (compact 100.9×60.2×23.3), NDI decoders (NDI to HDMI/SDI/AIO compact; NDI to HDMI 4K on
  the Plus chassis).
- **Panel connectors, always black `-B`**: etherCON NE8FDP-B (network/PoE), NAUSB-W-B (5 V power +
  USB-NET config; a second one on decoders for the USB-A host port), NAHDMI-W-B (HDMI in/out incl.
  loop-out), NBB75DFGB (SDI BNC), DBA-BL-B (blank). The Mini-DIN-8 PTZ/Tally port stays **internal**
  (`panel:"none"`) in every current variant — see `knowledge/components/mini-din8-feedthrough.md`
  for a possible future variant only, do not wire it up by default.
- **Layout**: side-exit with **one patch wall** — all external connectors sit in a single long side
  wall; the other long wall and both end walls carry none. Not in line with the device (an in-line
  layout exceeds the 256 mm bed for the Plus family, see architecture.md §11 R1). Family envelopes
  (layout-patch-wall.md rev 3): compact 194.9 × 159.9 × 51 mm, Plus 211.5 × 166.4 × 51 mm — base
  and lid print on separate plates; max 4 D-connectors per model; 6 lid thumbscrews on both.
- **Cooling**: passive-first on the compact family (`fan = false`, bay reserved); **Plus-family cases
  ship with the Noctua NF-A4x10 5V fitted by default** (`fan = true`, user decision 2026-09-08 per
  risk R5); parametric fan bay (Noctua NF-A4x10 5V default); reserved PoE-splitter
  bay (802.3af→5 V USB, gigabit) with a **dongle-class default envelope 75×40×20 mm** (`assumed`,
  e.g. UCTRONICS U6114/U6115 — buy one and measure; the GAT-USBC 114×51×25 does not fit, see
  architecture.md §11 R11). Both bays are reserved in every variant even when unused (§6 rule);
  the splitter reservation adds 20 mm to the −X end zone on every variant (D-12).
- **Closure**: tongue-and-groove lid, 6 captive M3 knurled thumbscrews into M3 heat-set inserts
  (rule: 6 above 180 mm lid span; both families are above it). **Retention: captive 1/4"-20
  SLOTTED bolt + DIN 6799 E-clip through the far (non-patch) long wall into the device's side
  thread** — the user verified the device's 1/4"-20 hole is on a long side face; the bolt must stay
  in the case when unscrewed; the boss is **flush** (far wall moved 10 mm outward, `MCC_GAP_FAR`
  16, no external lug — D-13); the device lies flat in a ribbed cradle. No floor through-bolt. Floor
  features (one owner, `mounts.scad`): 1/4"-20 threaded insert for the case itself, VESA 75×75 +
  Magewell-Fishtail-compatible M4 holes, strap slots, stacking profile. Hole position per SKU is
  `assumed` until measured (X from the short end, Z from the bottom, which side).
  Case height stays **51 mm** (4 mm Z web; 49 mm proposal vetoed); **no right-angle HDMI adapter in
  the default BOM** — end zones are sized for straight plugs, measured with the `depth-mockup` coupon.
- **Ruggedness**: 1 m drop onto concrete, ASA only, 3 mm walls / 5 perimeters, connectors recessed
  behind a shell bezel. The connector panel is a separate 2 mm flat-printed plate in a rabbet
  (architecture.md §5) — never call the Neutrik provider directly from `models/**`.

## Non-negotiables

- **Never invent a dimension.** Cite `knowledge/<file>.md:<line>`, or write `unknown` / `assumed`.
- Every port position carries a `confidence` field (`measured|drawing|manual|photo|assumed`).
- Always the black `-B` Neutrik variant — no exceptions, no "just for the prototype."
- No `$fn` set globally — see `openscad-authoring`. Functional holes get local `$fn≥64` + `circum=true`.
- STL/3MF are **never** committed — `exports/` is gitignored; CI renders on tag. Small text goldens
  (`tests/golden/*.json`) *are* committed.
- Third-party reference assets live in `knowledge/**/assets/` with attribution, nowhere else.
- **Coupons before cases** — `neutrik-tile`, `depth-mockup`, `tg-ladder`, `insert-boss`,
  `tolerance-ladder` are printed and measured before any full-size case is printed.

## Standard commands

```
python scripts/build.py doctor        # environment sanity (OpenSCAD, BOSL2 submodule pinned)
python scripts/build.py render        # render all models, --backend=Manifold
python scripts/build.py smoke         # tests/*.scad -> .csg, asserts fire, non-zero exit = fail
python scripts/build.py check         # mesh checks (watertight, winding, single shell)
python scripts/build.py golden        # diff tests/golden/*.json, --update to refresh
python scripts/build.py all           # doctor + smoke + render + check + golden
```

## Which skill for what

| Task | Skill |
|---|---|
| Look up a dimension/part/spec | `knowledge-lookup` |
| Write or review `.scad` in `lib/mcc/**` or `models/**` | `openscad-authoring` |
| Run OpenSCAD headlessly, read render output | `openscad-render` |
| Place a Neutrik D-series cutout | `neutrik-panel` |
| Create/verify a device data file from `knowledge/magewell/models/*.md` | `device-portmap` |
| Scaffold a new `models/<slug>/` case assembly | `new-case-variant` |
| Pre-slice go/no-go before printing | `print-check` |
| Regenerate `BOM.md` | `bom-update` |
| Pick a branch, sequence a commit/PR/release | `git-flow` |

## Team routing

Research a ticket into a plan → `researcher`. Validate a design decision before implementation →
`solution-architect` (single instance per repo, mandatory gate — see the Team Charter). Implement an
architect-validated plan → a general-purpose Sonnet-tier developer, fed a fully explicit plan (file
paths, module names, ordered steps). Tests → `tester`.

## Current status

**All eight priority cases exist and are on `main`** (`models/<slug>/case.scad` for HDMI/SDI TX,
HDMI/SDI Plus, NDI to HDMI / HDMI 4K / SDI / AIO), built on the full library: L0 (`constants`,
`util`, `ports`, `layout`), L1 (`neutrik`, `fasteners`, `fan`, `poe_splitter`, `ghost`), L2
(`shell`, `panel`, `cradle`, `mounts`, `vents`), 8 device data files (all positions `photo`/
`assumed`), 6 calibration coupons, 7 smoke tests, goldens for every part. `build.py all --with-step`
is green locally and in CI; every merge to `main` publishes a pre-release with per-device zips
(STL + 3MF + STEP + manifest). Plus-family cases ship with the fan. **Next milestone is physical
(Tier 4)**: print and measure the six coupons on the X1C, measure the side 1/4"-20 hole per SKU, the
dongle splitter and the E-clip, write the measured values into `constants.scad` (confidence →
`measured`), then the first full-size print. Later: the IP-decoder family (120 × 79.3 × 24.5). See
`.claude/knowledge/session-resume.md` for the ordered plan; `new-case-variant` explains the
thin-assembly workflow and when to stop and report instead of improvising geometry.

## Branching (Git Flow)

This repo uses a simplified Git Flow **without a `develop` branch** (user decision 2026-09-08):
`main` is the integration *and* release branch; all work happens on `feature/*` branches (a hotfix
is simply a feature branch off `main`) that reach `main` via PR; releases are annotated `vX.Y.Z`
tags on `main`. Recipes in `CONTRIBUTING.md` and the `git-flow` skill (see the table above). Three
non-negotiables:

- **Never commit directly on `main`.** All work happens on `feature/*` and reaches `main` via PR.
- **Releases only via annotated `vX.Y.Z` tags on `main`.** No other path produces a GitHub Release.
- **A PR into `main` must be CI-green** (`render` check) before it merges — no exceptions for
  "small" changes.
