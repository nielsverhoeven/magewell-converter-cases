# Knowledge base — index

Sourced, cited product and domain research for designing 3D-printable cases for Magewell Pro Convert
NDI converters. This tree (`knowledge/**`) is stable reference data, distinct from
`.claude/knowledge/**` (agent working memory — architecture, testing, ticket-source; see the split
explained in `CLAUDE.md`). Do not merge the two, and do not put sourced research in `.claude/`.

Read `.claude/skills/knowledge-lookup/SKILL.md` for how to use this index efficiently and how to cite
what you find — this file is the map, that skill is the procedure.

## Citation rule

Every fact pulled from this tree is cited as `knowledge/<path>.md:<line>` (or `:<start>-<end>`),
pointing at the exact line, not just the containing file. A number without a citation, used anywhere
in this repo's code/BOM/design decisions, is a rule violation — see CLAUDE.md's non-negotiables.

## Flags legend

| Flag | Meaning |
|---|---|
| `unknown` | Not published anywhere found — do not use for a real dimension |
| `(estimated from image)` | Read off a product photo, not a spec sheet |
| `(retailer, unverified)` | Fallback only, never a substitute for an official figure |
| `assumed` | Engineering estimate with no source — must carry a `TODO` and a plan to replace it (usually a coupon) |
| `*` on a table value | Flags a contradiction between sources — read the note under the table |

## Assets policy

Third-party reference material (product photos, datasheet excerpts, drawings) lives under
`knowledge/**/assets/` with attribution to the original source, and nowhere else in the repo. Never
commit a binary asset outside this pattern.

## Directory map

### `knowledge/magewell/` — the devices

- **[README.md](magewell/README.md)** — full device table (SKU, family, size, power, op-temp, fan)
  and the priority-model list for this project.
- **[housing-families.md](magewell/housing-families.md)** — the four shared chassis, face-by-face
  port layout for each, and case-design implications. Read this before `models/*.md` for any device
  — it has the port *ordering* detail the per-model files are often terser about.
- **[power-and-thermal.md](magewell/power-and-thermal.md)** — full power/thermal table and the fan
  contradiction detail in full.
- **[accessories.md](magewell/accessories.md)** — L-bracket, Fishtail bracket, rack kits, shelves,
  Modator 2U.
- **[models/](magewell/models/)** — one file per device SKU: identity, physical dims, port layout,
  power, mounting, open questions.
- **[sources.md](magewell/sources.md)** — every source URL for this subtree.

### `knowledge/neutrik/` — the panel connectors

- **[README.md](neutrik/README.md)** — carries the project's black `-B` rule banner; part-per-
  function summary table. Read this first.
- **[d-series-cutout.md](neutrik/d-series-cutout.md)** — the shared mechanical spec: cutout geometry,
  mounting-hole pattern, flange footprint, panel thickness per connector, mounting hardware.
- **[placement-and-depth.md](neutrik/placement-and-depth.md)** — depth-behind-panel table, multi-gang
  spacing guidance, total-depth-needed (connector + patch cable) table, grounding quick reference.
- **[connectors/](neutrik/connectors/)** — per-family detail: `ethercon.md`, `usb.md`, `hdmi.md`,
  `bnc-sdi.md`, `dc-power.md`, `audio.md`, `blanking-and-caps.md`.
- **[sources.md](neutrik/sources.md)** — every source URL, with fetch date.

### `knowledge/components/` — off-the-shelf hardware

- **[README.md](components/README.md)** — one-line summary of each file below.
- **[fans.md](components/fans.md)** — Noctua fan lineup, mounting patterns, power draw.
- **[fasteners-and-hardware.md](components/fasteners-and-hardware.md)** — heat-set inserts, screws,
  latches, hinges, magnets, feet/bumpers.
- **[cables.md](components/cables.md)** — port-to-wall depth clearance by connector type.
- **[poe-splitters.md](components/poe-splitters.md)** — PoE splitter candidates, dimensions, the
  required internal cabling architecture.
- **[mini-din8-feedthrough.md](components/mini-din8-feedthrough.md)** — PTZ/Tally panel-mount
  options. Research for a **possible future variant only** — the current fixed decision keeps this
  port internal (`panel:"none"`); see CLAUDE.md.
- **[sources.md](components/sources.md)** — every source URL for this subtree.

### `knowledge/design/` — enclosure and thermal guidelines

- **[README.md](design/README.md)** — summaries plus the **known cross-file numeric
  inconsistencies** list (fan current draw, fan max power, insert hole diameter) — read this before
  trusting a single figure that could plausibly come from more than one file.
- **[fdm-rugged-enclosure-guidelines.md](design/fdm-rugged-enclosure-guidelines.md)** — material
  choice, wall/rib/fillet rules, tolerances, inserts, hinges, bumpers, ventilation, EMI grounding.
- **[thermal-guidelines.md](design/thermal-guidelines.md)** — convection/fan-sizing math, vent
  placement, fan noise vs. venue ambient.

## Known inconsistencies

See **[design/README.md](design/README.md) → "Known inconsistencies to resolve"** for the full,
current list of figures that disagree across files (as of this writing: NF-A4x10 5V current draw,
NF-A6x25 max input power, NF-A4x20 ULNA noise rating, and the M3 heat-set insert hole diameter). Do
not silently pick a side when you hit one of these — either follow that section's stated resolution,
or escalate if you hit a new one it doesn't already cover.
