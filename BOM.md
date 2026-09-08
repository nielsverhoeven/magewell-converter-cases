# Bill of Materials

**Generated from** `lib/mcc/devices/*.scad` (the 8 priority-device port maps) **+**
`lib/mcc/constants.scad` (`MCC_PANEL_PARTS`, `MCC_INSERT_M3`, `MCC_INSERT_1_4_20`, the
`MCC_SIDE_BOLT_*` captive-retention block, `MCC_FANS`, `MCC_SPLITTERS`), cross-checked against
`knowledge/**` and `.claude/knowledge/layout-patch-wall.md` (rev 3, 2026-09-08, the current
side-exit/patch-wall/side-bolt design — supersedes the floor-through-bolt + nylon-lock-nut
retention scheme implied by earlier drafts of this file).

**Generated 2026-09-07.** No `models/<slug>/case.scad` variant configs exist yet
(`lib/mcc/shell.scad`, `panel.scad`, `cradle.scad`, `mounts.scad`, `vents.scad`,
`fasteners.scad` are all not yet written — see `CLAUDE.md` "Current status"). Quantities below for
fan/splitter/cable rows are therefore **per the variant's default config** (fan bay and PoE-splitter
bay both *reserved* in every case per the architecture's reservation rule, but only *populated* with
a real part when a build explicitly enables `fan=true` / `splitter=true`) — not yet a real per-SKU
override table, since nothing has overridden the defaults yet.

Columns: **Item** (what it is) / **Part number** / **Qty** / **Notes** / **Source** (cited to
`knowledge/**:line`, `lib/mcc/constants.scad:line`, or `.claude/knowledge/layout-patch-wall.md`
§section — never a fabricated figure; `assumed` where the knowledge base has no sourced number).

Regenerating the per-variant sections below from a device's port map + variant config is the
`bom-update` skill's job (`.claude/knowledge/architecture.md` §10) — the skill also owns which
sections are hand-editable; see its `SKILL.md` before touching this file again.

---

## Common hardware (per case, every SKU)

Shared across all 8 priority variants — listed once here, not repeated per device section below.
Connector-count-dependent rows (D-connector rear bosses, patch cables) still vary by SKU and live in
the per-variant tables.

### Lid closure

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| M3 knurled thumb screw | generic (McMaster-Carr "Knurled Head Thumb Screws" family); length **assumed M3×10**, TBD after the lid/`tg-ladder` design lands | 6 | Every current SKU is over the `MCC_LID_SPAN_MAX = 180 mm` threshold post-D-12 (compact 193.9–194.9 mm, plus 210.5–211.5 mm) — both families get 6, not 4 | `.claude/knowledge/layout-patch-wall.md` §6 ("Family outcome after D-12 ... every current SKU gets 6 thumbscrews"); `knowledge/components/fasteners-and-hardware.md:97` (product family, exact stocked length not scrapeable) |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7 or equiv.) | RX-M3x5.7 | 6 | Lid boss, paired 1:1 with the thumbscrews above | `lib/mcc/constants.scad:96-100` (`MCC_INSERT_M3`); `knowledge/components/fasteners-and-hardware.md:17,22` |

### Panel plate retention (one long plate per case, independent of slot count)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7 or equiv.) | RX-M3x5.7 | 4 | Bosses standing rearward off the rabbet lip, at `mcc_panel_fixing_pos()` = `(±(plate_l/2-3), ±16.5)` — corrected 2026-09-08 (deviation D6) from the doc's original `z_conn_c ± 14`, which did not match the already-implemented `mcc_panel_plate()` | `.claude/knowledge/layout-patch-wall.md` §2.3 rev-5 correction; `lib/mcc/layout.scad:mcc_panel_fixing_pos()`; `lib/mcc/panel.scad:mcc_panel_plate()` |
| M3 machine screw, ~10–12 mm | generic pan/socket-head M3 | 4 | Screws along +Y through the plate's `MCC_PLATE_END_PAD` tabs into the bosses above | `knowledge/components/fasteners-and-hardware.md:96` (6–20 mm generic range); `:207` (a 3rd-party M3×12 mm kit specifically sold for Neutrik D-type panels, cited as a sourcing example, not this project's chosen length) |

### Device retention — captive side bolt (D-09, far wall)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| 1/4"-20 UNC slotted screw, ~19.05 mm under-head length (stock 3/4") | generic, cheese-head ⌀10.0 profile assumed (nearest metric standard ISO 1207/DIN 84 M6) | 1 | Threads `MCC_SIDE_BOLT_ENGAGE = 6.0 mm` into the device's own metal side thread — **no nut/insert on the device end** | `lib/mcc/constants.scad:143-150,240-242` (`MCC_SIDE_BOLT_HEAD_*`, `MCC_SIDE_BOLT_SCREW_LEN`); confidence **assumed** throughout, unverified against the real device thread (M2 in architecture's measurement list) |
| DIN 6799 E-clip, nominal size 5 | generic (groove ⌀5.0, groove width 0.8, clip OD ≈11.0, thickness 0.7) | 1 | Retains the screw in its pocket inside the boss — **replaces a nut**, no nut is used in the current design | `lib/mcc/constants.scad:157-167` (`MCC_SIDE_BOLT_CLIP`); flagged "NOT VERIFIED — DIN 6799 is not in `knowledge/**`" — confirm against the actual standard before ordering (M4) |
| EPDM anti-slip pad, side-bolt annulus, OD 18 / ID 8 mm | generic self-adhesive EPDM | 1 | On the boss face, compressed working thickness 2.0 mm | `lib/mcc/constants.scad:184-191` (`MCC_SIDE_BOLT_PAD_*`); `knowledge/components/fasteners-and-hardware.md:186` (⌀12×2.5 mm listed example, 2.0 mm compressed figure `assumed`) |
| EPDM anti-slip pad, floor, ≥40×40 mm footprint | generic self-adhesive EPDM | 1 | Under the device, compressed working thickness 2.0 mm — **a second, distinct pad from the side-bolt annulus above**, not the same item | `.claude/knowledge/layout-patch-wall.md` §7 Cradle table ("Compliant pad, floor 2.0 mm EPDM ... footprint ≥40×40"); `knowledge/components/fasteners-and-hardware.md:186` |

*(Connector-count-dependent rows — 2× M3 insert + 2× M3×8 screw per D-connector rear boss — are in
each per-variant table below, since the connector count varies 3–4 by SKU.)*

### Case floor mounting (own tripod/cheeseplate feature, distinct from the device-retention bolt above)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| 1/4"-20 brass heat-set insert | generic, ⌀8.8 mm hole / ⌀9.5 mm OD / 12.7 mm length (all `assumed`, typical brass-insert catalog range) | 1 | Case's own floor mount feature (tripod/cheeseplate) — **not** the device-retention side bolt, which threads directly into the device and needs no insert | `lib/mcc/constants.scad:102-113` (`MCC_INSERT_1_4_20`); no sourced figure exists in `knowledge/components/fasteners-and-hardware.md` for a 1/4"-20 insert specifically — flagged `confidence: assumed` in the constant's own comment |
| M4 machine screw + nut/washer | generic M4 | 4 (optional) | VESA MIS-D 75×75 mm pattern, or the Magewell-Fishtail-compatible M4 hole pattern — either use, not both simultaneously | `lib/mcc/constants.scad:274-276` (`MCC_VESA75_PITCH`, `assumed` — no VESA reference in `knowledge/**`); `CLAUDE.md` fixed decisions (floor features); Fishtail bracket geometry itself: `knowledge/magewell/assets/magewell-fishtail-bracket.stl` |
| Rubber/EPDM adhesive foot | generic, size TBD | 4 (typical) | Case underside | `knowledge/components/fasteners-and-hardware.md:180-187` (materials, common commodity size range 10–70 mm) |
| Cable zip tie / adhesive mount base | generic | as needed | Internal cable dressing | `knowledge/components/fasteners-and-hardware.md:215-222` |

### Fan bay (optional — only when a variant sets `fan=true`)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| Noctua NF-A4x10 5V (plain 3-pin or PWM) | NF-A4x10 5V | 1 | 40×40×10 mm, 32×32 mm mounting pitch, 0.044 A typ / 0.05 A max; ships with 4× NA-AV3 anti-vibration mounts in the box — no separate screws to buy | `knowledge/components/fans.md:13-24` (frame/current), `:89-95` (NA-AV3 bundled) |

### PoE-splitter bay (optional — only when a variant sets `splitter=true`)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| Dongle-class 802.3af/at → 5 V USB PoE splitter | UCTRONICS U6114 (5 V/4 A) or U6115 (5 V/2.4 A) class, or equivalent — **dimensions unmeasured**, `MCC_SPLITTER_DEFAULT = "DONGLE-75x40x20"` is a placeholder envelope | 1 | On-edge orientation, 20×75×40 mm (X×Y×Z) reserved bay at the −X end | `lib/mcc/constants.scad:309-338` (`MCC_SPLITTERS`, `assumed` throughout — "measure before the shell is finalised"); `knowledge/components/poe-splitters.md:54-55` (U6114/U6115 electrical specs), `:211-215` (dimensions explicitly unpublished) |
| RJ45 patch cable, short | generic Cat5e/6 | 2 | (a) etherCON feedthrough → splitter PoE-in; (b) splitter data-out → device RJ45 | `knowledge/components/poe-splitters.md:170-192` ("Required internal cabling" steps 1–2) |
| USB Type-B power cable (Y-spliced to fan if fitted) | generic, splitter-output-connector-to-USB-B | 1 | Splitter 5 V out → device USB-B power in, fan leads spliced onto the same VBUS/GND upstream of the device | `knowledge/components/poe-splitters.md:186-191` (step 3) |

---

## Coupon test kit — buy now to test the six Tier-4 coupons

Per `CLAUDE.md` ("Coupons before cases") — `neutrik-tile`, `depth-mockup`, `tg-ladder`,
`insert-boss`, `tolerance-ladder`, `side-bolt` (`models/coupons/*.scad`, all six already written)
must each be printed and measured before any full-size case is printed. Hardware needed to actually
test the printed coupons (not to print them):

| Item | Part number | Qty | Used by | Source |
|---|---|---|---|---|
| Neutrik HDMI feedthrough | **NAHDMI-W-B** | 1 | `neutrik-tile` and `depth-mockup` (both default `connector = "NAHDMI-W-B"`) | `models/coupons/neutrik-tile.scad:24`; `models/coupons/depth-mockup.scad:43` |
| Neutrik etherCON feedthrough | **NE8FDP-B** | 1 | `neutrik-tile` / `depth-mockup`, re-run with `-D connector="NE8FDP-B"` to test the 24.0 mm-class hole (vs. HDMI's 23.6 mm class) | `models/coupons/neutrik-tile.scad:22-23` |
| M3 heat-set insert (Ruthex RX-M3x5.7) | RX-M3x5.7 | ≥6 (enough to fill the `insert-boss` ladder's 6 bore sizes, plus spares for `tg-ladder`/`side-bolt` bosses) | `insert-boss` (calibrates `MCC_INSERT_M3.hole_d` for this printer/ASA combo across 6 bore diameters 3.8–4.3 mm) | `models/coupons/insert-boss.scad:3-6,19`; `knowledge/components/fasteners-and-hardware.md:22-28` |
| M3 machine screw, assorted 8–16 mm | generic | ≥6 | Test-seating each `insert-boss` bore after inserting | `knowledge/components/fasteners-and-hardware.md:96` |
| 1/4"-20 UNC slotted screw, ~19–25 mm | generic cheese-head | 1 | `side-bolt` coupon — real screw through the printed boss into a test surface | `models/coupons/side-bolt.scad:3-8,47-53` |
| DIN 6799 E-clip, nominal size 5 | generic | 1 | `side-bolt` coupon retention | `models/coupons/side-bolt.scad:6-8`; `lib/mcc/constants.scad:157-167` |
| EPDM pad, ⌀18 mm OD / ⌀8 mm ID (or nearest stock size, trim to fit) | generic self-adhesive | 1 | `side-bolt` coupon compliant pad — **the coupon needs this, not a nut**; a 1/4"-20 nut is not part of the current `side-bolt.scad` E-clip retention design and is optional only as a bench-testing fallback if the E-clip proves hard to source in time | `models/coupons/side-bolt.scad:6-8`; `lib/mcc/constants.scad:184-191` |
| HDMI patch cable, 0.3 m, straight plug | generic | 1 | `depth-mockup` — real cable tried against the printed ruler to measure the true `plug_len` for `NAHDMI-W-B` | `models/coupons/depth-mockup.scad:19-24`; `knowledge/components/cables.md:54` (0.15–0.3 m ultra-short HDMI widely available, no verified plug-length source yet — this measurement is what fixes that) |
| RJ45 (Cat6) patch cable, 0.3 m | generic slim-boot | 1 | `depth-mockup`, re-run with `-D connector="NE8FDP-B"` | `models/coupons/depth-mockup.scad:28`; `knowledge/components/cables.md:23` (0.15 m confirmed available; 0.3 m also common) |

`tg-ladder` and `tolerance-ladder` need no additional purchased hardware beyond calipers to measure
the printed clearances directly (they are self-contained peg/hole and tongue/groove ladders).

---

## Purchase hints (EU)

Per-category, not per-line-item (keeps this file from becoming a stale price list — **no prices are
tracked in this document**):

| Category | EU sourcing hint |
|---|---|
| Neutrik D-series connectors (`-B` black variants) | Thomann (stage/broadcast retailer, stocks Neutrik D-series incl. black); also Reichelt for some individual parts |
| M3 heat-set inserts, thumbscrews, generic machine screws | Ruthex direct (ruthex.de — the primary sourced brand in `knowledge/components/fasteners-and-hardware.md`), or Reichelt/Bossard for generic M3/M4 hardware |
| 1/4"-20 UNC hardware, DIN 6799 E-clips, EPDM pads | Generic industrial fastener suppliers (Bossard, RS Components, Conrad) — none of these specific items has a confirmed EU listing in `knowledge/**` yet; verify against the physical `side-bolt` coupon before bulk-ordering |
| Noctua fans (NF-A4x10 5V) | Reichelt, Mouser, or Amazon.de — `knowledge/components/fans.md` cites Amazon.de street pricing directly |
| PoE splitter (UCTRONICS U6114/U6115, dongle class) | US-based storefront (uctronics.com); `knowledge/components/poe-splitters.md`'s own "Open questions" section documents failed EU-availability searches (Amazon.de/Reichelt/Conrad/Mouser all 403/404/503'd in that research pass) — **re-check before committing to an EU build**, do not assume EU availability |
| PoE Texas GAT-USBC (named non-default alternative, does not fit this case topology per R11) | US-based (poetexas.com) — no EU distributor found; not recommended for this project's layout regardless of sourcing |
| ASA filament | Any EU filament retailer stocking ASA (Prusament, Fillamentum, etc.) — not independently researched in `knowledge/**`, treat brand choice as `unknown`/open unless the user names one |

---

## Per-variant BOM

Each table below is one row per external port (`panel` ≠ `"none"` in the device's `lib/mcc/devices/*.scad`
file) plus that SKU's connector-rear-boss hardware and internal patch cables. Common hardware
(lid, panel-plate retention, side-bolt retention, floor insert, VESA/Fishtail, fan/splitter bays) is
**not repeated per section** — see "Common hardware" above.

Internal patch cable lengths follow `knowledge/components/cables.md`'s shortest **confirmed
purchasable** length per connector type (0.15–0.3 m range per the design brief), not a bare
`mcc_bay_depth()` lower bound — see that file's per-row notes for the specific product citation.
**No right-angle adapter is used by default** on any port (D-08 veto,
`.claude/knowledge/layout-patch-wall.md` §4 — straight plugs only; a right-angle adapter is a legal
per-variant option but is not the default and is not listed here).

### pro-convert-hdmi-tx

**3 external D-connectors** (no 4th slot — see note below).

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NAHDMI-W-B | 1 | `hdmi_in` port | `lib/mcc/devices/pro-convert-hdmi-tx.scad:23-24`; `lib/mcc/constants.scad:424`; `knowledge/neutrik/README.md:35` |
| Neutrik NAUSB-W-B | 1 | `usb_b` port, power + USB-NET config | `lib/mcc/devices/pro-convert-hdmi-tx.scad:29-30`; `lib/mcc/constants.scad:425`; `knowledge/neutrik/README.md:33` |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-hdmi-tx.scad:31-32`; `lib/mcc/constants.scad:423`; `knowledge/neutrik/README.md:32` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 6 | 2 per connector rear boss × 3 connectors | `knowledge/components/fasteners-and-hardware.md:17,22`; `.claude/skills/neutrik-panel/SKILL.md` "Screw fixing" |
| M3×8 machine screw | 6 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (6–20 mm generic range; 8 mm is this project's chosen nominal, `assumed`, no stocked-length citation) |
| HDMI patch cable, straight plug, 0.3 m | 1 | `hdmi_in` | `knowledge/components/cables.md:54,121` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

**Note on slot count.** This SKU's port map has only 3 external ports (`ptz_tally` stays internal,
`rotary`/`side_bolt` are `panel:"none"`). Per `.claude/knowledge/layout-patch-wall.md` §3 ("`n_slots =
len(ext)`") and its §6 table row "compact, 3 slots (HDMI TX / SDI TX)", the panel plate is sized to
**3** slots by default, not padded to the 4-slot maximum — so **no `DBA-BL-B` blank is needed** unless
a future `case.scad` variant deliberately reserves a spare 4th slot. "Max 4 D-connectors per model"
(`CLAUDE.md`, `.claude/skills/neutrik-panel/SKILL.md` §"Multi-connector spacing") is a ceiling, not a
mandate to always populate 4.

### pro-convert-sdi-tx

**3 external D-connectors** (same slot-count note as HDMI TX above).

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NBB75DFGB | 1 | `sdi_in` port | `lib/mcc/devices/pro-convert-sdi-tx.scad:20-21`; `lib/mcc/constants.scad:426`; `knowledge/neutrik/README.md:36` |
| Neutrik NAUSB-W-B | 1 | `usb_b` port, power + USB-NET config | `lib/mcc/devices/pro-convert-sdi-tx.scad:26-27`; `lib/mcc/constants.scad:425`; `knowledge/neutrik/README.md:33` |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-sdi-tx.scad:28-29`; `lib/mcc/constants.scad:423`; `knowledge/neutrik/README.md:32` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 6 | 2 per connector rear boss × 3 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 6 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| 12G-SDI BNC↔BNC mini-coax lead (Belden 4855R), 0.15 m | 1 | `sdi_in`; bend radius 40.6 mm governs bay depth, not cable length | `knowledge/components/cables.md:63,65,123` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

### pro-convert-hdmi-plus

**4 external D-connectors** (uses the full slot count — no blank needed).

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NAUSB-W-B | 1 | `usb_b` port, power + USB-NET config | `lib/mcc/devices/pro-convert-hdmi-plus.scad:26-27`; `lib/mcc/constants.scad:425` |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-hdmi-plus.scad:28-29`; `lib/mcc/constants.scad:423` |
| Neutrik NAHDMI-W-B | 2 | `hdmi_in` + `hdmi_out` (loop-out externalized per the device file's own comment) | `lib/mcc/devices/pro-convert-hdmi-plus.scad:31-37`; `lib/mcc/constants.scad:424` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 8 | 2 per connector rear boss × 4 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 8 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| HDMI patch cable, straight plug, 0.3 m | 2 | `hdmi_in`, `hdmi_out` | `knowledge/components/cables.md:54,121` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |
| Noctua NF-A4x10 5V (plain 3-pin or PWM) | 1 | `models/pro-convert-hdmi-plus/case.scad`'s `fan` variant defaults **true** on this SKU (not the common-hardware table's "only when `fan=true`" case) — the Plus chassis' ~10 W thermal budget makes the fan not optional per `.claude/knowledge/layout-patch-wall.md` §16.2 item 4 / architecture.md §11 R5, user decision 2026-09-08 | `knowledge/components/fans.md:13-24` (frame/current); `models/pro-convert-hdmi-plus/case.scad` (`fan = true` default, comment cites the decision) |
| NA-AV3 anti-vibration mounts | 4 | Ships in the box with the fan above — **no separate screws to buy**, these both mount the fan and decouple it from the shell | `knowledge/components/fans.md:89-95` (bundled scope of delivery) |
| USB-A to 2/3-pin fan power lead (or third-party equivalent), Y-spliced onto the `usb_b` power feed inside the case | 1 | 5 V/GND tapped from the incoming `NAUSB-W-B` power line upstream of the device — this SKU has no PoE splitter (`splitter = false`, bay reserved but unpopulated), so the fan cannot be fed from a splitter's 5 V rail the way a `splitter=true` build would (see the Common Hardware "PoE-splitter bay" row) | `knowledge/components/fans.md:140-149` ("General 5V-from-USB power options" — generic USB-A-to-fan-connector adaptor leads) |

Note: the device file flags End B's own physical port pitch (HDMI IN / Mini-DIN-8 / HDMI OUT at
~22 mm) as tighter than `MCC_D_PITCH_H` (32 mm) — this does **not** affect the BOM above, since the
panel-plate connector slots are spread across the full case width by `mcc_slot_for_port()`
(`.claude/knowledge/layout-patch-wall.md` §3), not placed at the device's own port pitch.

### pro-convert-sdi-plus

**4 external D-connectors.** Plus-family case, ships with the fan fitted by default (`fan = true`,
`models/pro-convert-sdi-plus/case.scad`; user decision 2026-09-08, R5 — the Plus chassis' ~10 W
thermal budget makes the fan non-optional here, unlike the compact-family template it was copied
from) — the Noctua row below is therefore a **standard** row for this SKU, not the common-hardware
table's "only when `fan=true`" case.

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network (slot 1) | `lib/mcc/devices/pro-convert-sdi-plus.scad:22-23`; `lib/mcc/constants.scad:423` |
| Neutrik NAUSB-W-B | 1 | `usb_b` port, power + USB-NET config (slot 2) | `lib/mcc/devices/pro-convert-sdi-plus.scad:20-21`; `lib/mcc/constants.scad:425` |
| Neutrik NBB75DFGB | 2 | `sdi_out` (slot 3, loop-out) + `sdi_in` (slot 4) | `lib/mcc/devices/pro-convert-sdi-plus.scad:25-31`; `lib/mcc/constants.scad:426` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 8 | 2 per connector rear boss × 4 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 8 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| Noctua NF-A4x10 5V | 1 | Fan bay, fitted by default on this SKU (`fan = true`) — ships with 4× NA-AV3 anti-vibration mounts, no separate screws to buy | `knowledge/components/fans.md:13-24,89-95`; `.claude/knowledge/layout-patch-wall.md` §16.2 item 4 (R5) |
| 12G-SDI BNC↔BNC mini-coax lead (Belden 4855R), 0.15 m | 2 | `sdi_in`, `sdi_out` | `knowledge/components/cables.md:63,65,123` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

### pro-convert-for-ndi-to-hdmi

**4 external D-connectors.**

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NAHDMI-W-B | 1 | `hdmi_out` port | `lib/mcc/devices/pro-convert-for-ndi-to-hdmi.scad:19-20`; `lib/mcc/constants.scad:424` |
| Neutrik NAUSB-W-B | 2 | `usb_host` (USB-A host, wired through the reversible A/B feedthrough) + `usb_b` (power) | `lib/mcc/devices/pro-convert-for-ndi-to-hdmi.scad:21-25`; `lib/mcc/constants.scad:425`; `knowledge/neutrik/README.md:33` (reversible A/B) |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-for-ndi-to-hdmi.scad:26-27`; `lib/mcc/constants.scad:423` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 8 | 2 per connector rear boss × 4 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 8 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| HDMI patch cable, straight plug, 0.3 m | 1 | `hdmi_out` | `knowledge/components/cables.md:54,121` |
| USB 2.0 A-to-A cable, 0.15 m | 1 | `usb_host` | `knowledge/components/cables.md:78,125` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

### pro-convert-for-ndi-to-hdmi-4k

**4 external D-connectors** (Plus chassis, decoder electronics — see the device file's own comment).
**Fan fitted by default** (`fan = true` in `models/pro-convert-for-ndi-to-hdmi-4k/case.scad`, user
decision 2026-09-08 R5 / `.claude/knowledge/layout-patch-wall.md` §16.2 item 4 — the Plus-family
thermal budget makes active cooling the shipped default for this SKU, unlike the compact
`pro-convert-for-ndi-to-hdmi` template it was copied from), so unlike every other section in this
table the fan row below is **not** the common-hardware "optional, only when `fan=true`" case — it
ships with every unit of this SKU.

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NAUSB-W-B | 2 | `usb_host` (USB-A host) + `usb_b` (power) | `lib/mcc/devices/pro-convert-for-ndi-to-hdmi-4k.scad:23-31`; `lib/mcc/constants.scad:425` |
| Neutrik NAHDMI-W-B | 1 | `hdmi_out` port | `lib/mcc/devices/pro-convert-for-ndi-to-hdmi-4k.scad:27-28`; `lib/mcc/constants.scad:424` |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-for-ndi-to-hdmi-4k.scad:32-33`; `lib/mcc/constants.scad:423` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 8 | 2 per connector rear boss × 4 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 8 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| Noctua NF-A4x10 5V (plain 3-pin) | 1 | 40×40×10 mm case-cooling fan in the +X end wall's live cutout (`fan=true` default, `mcc_fan_cutout("NF-A4x10", grille=true)`) — additional to, and independent of, the device's own internal variable-speed fan | `knowledge/components/fans.md:13-24`; `lib/mcc/constants.scad:534-535` (`MCC_FANS`); `lib/mcc/fan.scad` |
| M3 machine screw, ~8–10 mm (or the bundled NA-AV3 silicone anti-vibration mounts, push-fit, no screw) | 4 | Through `mcc_fan_cutout()`'s 4 clearance holes at the fan's 32 mm pitch (⌀4.3) into the fan's own threaded corners | `knowledge/components/fans.md:89-95` (NA-AV3 bundled in the NF-A4x10 5V box); `lib/mcc/constants.scad:535` (`hole_d=4.3`) |
| USB-A-to-fan-connector power lead (generic, 2-/3-pin), or splice onto the device's own USB-B +5V feed | 1 | **The device's own external `usb_host` port (NAUSB-W-B, USB-A host) can power this fan**: NF-A4x10 5V draws 0.044 A typ / 0.05 A max, far under any USB host's current budget — a plain USB-A-to-fan-connector cable is the simplest wiring path (no separate internal 5V tap needed); wiring choice `assumed`, not verified against the device's actual USB-A host output rating | `knowledge/components/fans.md:20-24` (current draw), `:140-160` ("General 5V-from-USB power options") |
| USB 2.0 A-to-A cable, 0.15 m | 1 | `usb_host` | `knowledge/components/cables.md:78,125` |
| HDMI patch cable, straight plug, 0.3 m | 1 | `hdmi_out` | `knowledge/components/cables.md:54,121` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

Note: `vesa = true` (library default, set explicitly in `case.scad` for documentation parity) — the 4
VESA 75×75 M4 floor bosses are present, hardware already covered by the "Case floor mounting" common
section above (M4 machine screw + nut/washer, optional). `splitter = false` — the PoE-splitter bay is
reserved (architecture.md §6) but unpopulated on this SKU, same as every other current variant; no
splitter hardware row here.

### pro-convert-for-ndi-to-sdi

**4 external D-connectors.**

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NBB75DFGB | 1 | `sdi_out` port | `lib/mcc/devices/pro-convert-for-ndi-to-sdi.scad:21-23`; `lib/mcc/constants.scad:426` |
| Neutrik NAUSB-W-B | 2 | `usb_host` (USB-A host) + `usb_b` (power) | `lib/mcc/devices/pro-convert-for-ndi-to-sdi.scad:24-28`; `lib/mcc/constants.scad:425` |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-for-ndi-to-sdi.scad:29-30`; `lib/mcc/constants.scad:423` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 8 | 2 per connector rear boss × 4 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 8 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| 12G-SDI BNC↔BNC mini-coax lead (Belden 4855R), 0.15 m | 1 | `sdi_out` | `knowledge/components/cables.md:63,65,123` |
| USB 2.0 A-to-A cable, 0.15 m | 1 | `usb_host` | `knowledge/components/cables.md:78,125` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

Note: this model's top-face rotary/menu/select layout is carried over from the shared decoder
pattern at `confidence:"assumed"` (not independently photographed for this SKU per the device
file's own comment) — these controls are `panel:"none"` throughout and do not affect the BOM.

### pro-convert-for-ndi-to-aio

**4 external D-connectors.**

| Part | Qty | Notes | Source |
|---|---|---|---|
| Neutrik NAHDMI-W-B | 1 | `hdmi_out` port | `lib/mcc/devices/pro-convert-for-ndi-to-aio.scad:21-22`; `lib/mcc/constants.scad:424` |
| Neutrik NBB75DFGB | 1 | `sdi_out` port | `lib/mcc/devices/pro-convert-for-ndi-to-aio.scad:23-24`; `lib/mcc/constants.scad:426` |
| Neutrik NAUSB-W-B | 1 | `usb_b` port — power only, USB role beyond power is an open question per the device file's own comment | `lib/mcc/devices/pro-convert-for-ndi-to-aio.scad:26-27`; `lib/mcc/constants.scad:425` |
| Neutrik NE8FDP-B | 1 | `rj45` port, PoE/network | `lib/mcc/devices/pro-convert-for-ndi-to-aio.scad:28-29`; `lib/mcc/constants.scad:423` |
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | 8 | 2 per connector rear boss × 4 connectors | `knowledge/components/fasteners-and-hardware.md:17,22` |
| M3×8 machine screw | 8 | Paired 1:1 with the inserts above | `knowledge/components/fasteners-and-hardware.md:96` (`assumed` length) |
| HDMI patch cable, straight plug, 0.3 m | 1 | `hdmi_out` | `knowledge/components/cables.md:54,121` |
| 12G-SDI BNC↔BNC mini-coax lead (Belden 4855R), 0.15 m | 1 | `sdi_out` | `knowledge/components/cables.md:63,65,123` |
| USB 2.0 A-to-B cable, 0.15 m | 1 | `usb_b` | `knowledge/components/cables.md:79,125` |
| Cat6 slim RJ45 patch cable, 0.15 m | 1 | `rj45` | `knowledge/components/cables.md:23,119` |

Note: this model has no USB host port (two simultaneous video outputs instead of a USB-A pass-through)
per the device file's own comment — only one `NAUSB-W-B` is needed, not two.

---

## Per-variant BOM — not-yet-prioritized SKUs

No `lib/mcc/devices/*.scad` file exists yet for these — rows stay empty until that device data file
is written (see the `device-portmap` skill). Not part of this pass's scope.

### pro-convert-12g-sdi-4k-plus

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-aes67

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-audio-dx

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-hdmi-4k-plus

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-ip-to-aio-4k

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-ip-to-hdmi

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-ip-to-hdmi-4k

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-ip-to-usb

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-sdi-4k-plus

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |
