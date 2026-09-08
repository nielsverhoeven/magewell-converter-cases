---
name: bom-update
description: Regenerate BOM.md from device records and variant configs — per-variant Neutrik parts, inserts, thumbscrews, retention hardware, and cables, with source citations and EU purchase hints; use after adding or changing a case variant, or whenever BOM.md looks stale against models/**.
---

# bom-update

`BOM.md` (repo root) is owned by another workstream in this repo for its overall structure — this
skill covers what a per-variant section should contain and how to derive it mechanically from the
device record + variant config, so it doesn't drift into hand-maintained guesswork. If `BOM.md`
itself needs restructuring, that's outside this skill's scope; only regenerate/append the variant
sections.

## Per-variant table shape

One section per `models/<slug>/`, driven by that model's device data file
(`lib/mcc/devices/<slug>.scad`) and its `case.scad` variant config (`new-case-variant` skill):

```markdown
## <Device Name> (`models/<slug>/`)

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NE8FDP-B | 1 | rj45 port, PoE/network | knowledge/neutrik/connectors/ethercon.md |
| Neutrik NAUSB-W-B | 1 | usb_b port, power + config | knowledge/neutrik/connectors/usb.md |
| Neutrik NAHDMI-W-B | 1 | hdmi_in port | knowledge/neutrik/connectors/hdmi.md |
| Neutrik DBA-BL-B | 1 | blanks the unused <port id> position | knowledge/neutrik/connectors/blanking-and-caps.md |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7 or equiv.) | <n> | panel screw bosses + lid thumbscrew bosses | knowledge/components/fasteners-and-hardware.md:17 |
| M3 knurled thumbscrew | <n> (4, or 6 on lids >~180 mm per architecture §11 R7) | captive lid fastening | knowledge/components/fasteners-and-hardware.md §2 |
| 1/4"-20 bolt, ~<length> mm | 1 | device retention through the floor | architecture.md §Decision 5/7 |
| 1/4"-20 nylon-insert (nyloc) nut | 1 | vibration-resistant retention, per architecture §11 R8 | — |
| M4×12 screw + M4 nut | 2 each, if VESA/Fishtail mount used | floor mounting pattern | knowledge/magewell/housing-families.md (Fishtail bracket hardware, e.g. MECO0067/68) |
| Noctua NF-A4x10 5V | 1, if `fan = true` | fan bay | knowledge/components/fans.md:13-25 |
| PoE Texas GAT-USBC (placeholder) | 1, if `splitter = true` | PoE splitter bay | knowledge/components/poe-splitters.md:58 |
| <patch cable, per port> | 1 each | internal cable, length per bay depth | knowledge/components/cables.md |
```

Fill `<n>` and quantities from the device file's external ports (every port whose `panel` is not `"none"`) and the case options — don't
hand-guess a round number. Every row's connector count is `1:1` with those external ports (`cfg.external_ports` was dropped on 2026-09-08)
whose `panel` value is a real Neutrik part (not `"none"`); every omitted-but-physically-present port
with a real `panel` value gets a DBA-BL-B blank row instead, not a silently dropped line.

## Common-hardware section

Hardware shared across every variant regardless of device — list once at the top of `BOM.md`, not
repeated per section:

- M3 heat-set inserts (bulk pack) — `knowledge/components/fasteners-and-hardware.md` §1
- M3 knurled thumbscrews — same file, §2
- 1/4"-20 bolt + nylon-insert nut stock
- ASA filament — `knowledge/design/fdm-rugged-enclosure-guidelines.md` §1 (material table)

## The always-black rule, restated for the BOM

Every Neutrik line item is the **`-B` (black)** part number. If you're tempted to write `NE8FDP`
instead of `NE8FDP-B` because that's the part the sourced dimensions came from, don't — the BOM is
what someone orders from, and ordering the wrong color variant means a mismatched case for a live
tour. Cross-check every Neutrik row against the table in `neutrik-panel`'s SKILL.md before
publishing.

## Source citation column

Every row cites either a `knowledge/**` file (dimension/part justification) or, for something not in
the knowledge base at all (a generic M4 screw, a nylon nut), a plain `—` rather than a fabricated
citation. Never leave a Neutrik/fastener/fan/splitter row uncited if a `knowledge/**` file exists for
it — that defeats the "never invent a dimension" rule from CLAUDE.md, since a BOM entry with the
wrong dimension is exactly as costly as a CAD constant with the wrong dimension.

## EU purchase hints

Add a short purchase-source note per category, not per line item (keeps the BOM from becoming a
retailer price list that goes stale):

| Category | EU sourcing hint |
|---|---|
| Neutrik connectors | Thomann (stage/broadcast retailer, stocks Neutrik D-series incl. black variants) |
| Fasteners (inserts, thumbscrews) | Reichelt, or a specialist 3D-printing-insert seller (e.g. Ruthex direct, ruthex.de — see `fasteners-and-hardware.md`) |
| Noctua fans | Reichelt, Mouser |
| PoE splitter (GAT-USBC placeholder) | US-based (poetexas.com) — no EU distributor found in this pass per `knowledge/components/poe-splitters.md`'s own open questions; re-check before committing to it for an EU build |
| ASA filament | Any EU filament retailer stocking ASA (Prusament, Fillamentum, etc.) — not itself researched in `knowledge/**`, treat as `unknown` sourcing unless the user names a brand |

Do not upgrade a hint to a firm recommendation without checking whether `knowledge/components/*.md`'s
own "Open questions" section already flags that exact sourcing gap (the PoE splitter row above is a
live example — `poe-splitters.md`'s own sources list documents EU-availability search failures in
detail; don't silently resolve that gap by picking a distributor that was never verified).

## Worked example — Pro Convert HDMI TX

Using the `device-portmap` example device record (`hdmi_in`, `usb_b`, `rj45` external; `ptz_tally`
kept internal per the fixed decision; `rotary`/`tripod` not panel-mounted):

```markdown
## Pro Convert HDMI TX (`models/pro-convert-hdmi-tx/`)

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NAHDMI-W-B | 1 | hdmi_in port | knowledge/neutrik/connectors/hdmi.md:10 |
| Neutrik NAUSB-W-B | 1 | usb_b port, power + USB-NET config | knowledge/neutrik/connectors/usb.md:10 |
| Neutrik NE8FDP-B | 1 | rj45 port, PoE/network | knowledge/neutrik/connectors/ethercon.md:11 |
| M3×5.7 heat-set insert | 6 | 2 per connector rear boss (3 connectors) | knowledge/components/fasteners-and-hardware.md:17 |
| M3 knurled thumbscrew + M3×5.7 insert | 4 | captive lid fastening | knowledge/components/fasteners-and-hardware.md §2 |
| 1/4"-20 bolt + nylon-insert nut | 1 each | device retention (housing-families.md:132, hole position `assumed`) | knowledge/magewell/housing-families.md:132 |
| HDMI patch cable, short | 1 | length per `mcc_bay_depth("NAHDMI-W-B")` = 75.65 mm bay | knowledge/components/cables.md §3 |
| USB 2.0 A-to-B cable, short | 1 | length per `mcc_bay_depth("NAUSB-W-B")` = 60.55 mm bay | knowledge/components/cables.md §5 |
| RJ45 patch lead, short | 1 | length per `mcc_bay_depth("NE8FDP-B")` = 59.55 mm bay | knowledge/components/cables.md §1-2 |
```

No fan/splitter row: HDMI TX is fanless (`knowledge/magewell/housing-families.md:118-119`) and this
variant doesn't reserve a splitter bay unless the user asked for a PoE-powered build. Note the
`ptz_tally` port does **not** appear as a Neutrik row at all — it stays internal per the fixed
decision, so it contributes nothing to the BOM (not even a DBA-BL-B blank, since a blank is only for
a port position the panel physically has and isn't using — `ptz_tally` never gets a panel position in
the first place while `panel:"none"`).

## Cable length derivation

Don't invent a patch-cable length. `mcc_bay_depth(part)` (already defined in
`lib/mcc/constants.scad`, see `neutrik-panel`'s part table) is `depth + plug_len` — the minimum
clear internal depth the bay needs, and therefore a lower bound on how short the internal patch cable
plausibly needs to be. Round up to the nearest commodity length actually sold (`cables.md`'s tables
list what's actually available, e.g. "shortest confirmed listing found was 1 m" for some etherCON
leads) rather than assuming an arbitrary short length exists — several cable types in `cables.md` are
explicitly `unknown` below a certain length and flagged for physical measurement; carry that
`unknown` into the BOM row rather than silently rounding to a number that was never verified to be
purchasable.

## Regeneration workflow

1. For each `models/<slug>/case.scad` that exists, read its variant config and the corresponding
   `lib/mcc/devices/<slug>.scad`.
2. Build the per-variant table per the shape above.
3. Diff against the existing `BOM.md` section for that slug (if any) — flag anything that changed
   (a port added/removed, a fastener count changed) rather than silently overwriting a
   human-edited note.
4. Leave the common-hardware section and file structure as-is; only touch per-variant sections and
   append new ones.
