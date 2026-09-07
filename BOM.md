# Bill of Materials

One table per case variant (Magewell Pro Convert SKU, 1:1 with `knowledge/magewell/models/*.md`
and the future `models/<slug>/case.scad`). Rows are empty until the corresponding device data file
(`lib/mcc/devices/<slug>.scad`) and case model exist — a BOM row depends on the device's port map
(which connectors it actually needs), so it cannot be filled in ahead of that. Regenerating this
table from a device's port map + variant config is the `bom-update` skill's job
(`.claude/knowledge/architecture.md` §10); do not hand-fill rows once that skill exists.

Columns: **Item** (what it is) / **Part number** / **Qty** / **Notes** / **Source** (where the
figure or part choice is cited, `file:line` into `knowledge/**`).

## Common hardware

Shared across every variant. Cited from `knowledge/**` where sourced research exists; where it
doesn't (marked below), the figure is a standard mechanical constant recorded directly in
`lib/mcc/constants.scad` rather than invented here.

| Item | Part number | Qty (per case) | Notes | Source |
|---|---|---|---|---|
| M3 heat-set insert | Ruthex RX-M3x5.7 | varies (per boss: connector fixing ×2/panel, lid fasteners) | 5.7 mm length; hole_d 4.0 mm nominal print/drill diameter | `knowledge/components/fasteners-and-hardware.md:17,22` (length, hole size); OD (4.6 mm) is **assumed**, not sourced — see `lib/mcc/constants.scad` `MCC_INSERT_M3` comment |
| M3 knurled thumb screw | generic (McMaster-Carr "Knurled Head Thumb Screws" family; exact stocked length TBD) | 4–6 (lid fasteners; architecture.md §11 R7 recommends 6 on any shell over ~180 mm) | Tool-less lid access | `knowledge/components/fasteners-and-hardware.md:97,103` |
| 1/4"-20 bolt | standard UNC 1/4"-20, length TBD per stack height | 1 | Device retention through-bolt (architecture.md §11 R8) | Not sourced in `knowledge/**` — standard mechanical-fastener constant; see `lib/mcc/constants.scad` `MCC_TRIPOD_MAJOR_D`/`MCC_TRIPOD_CLR_D` |
| 1/4"-20 nylon-insert lock nut | standard UNC 1/4"-20 nyloc | 1 | Vibration-resistant retention for the device bolt, per architecture.md §11 R8 ("specify a thread-locking or nylon-insert solution") | Not sourced in `knowledge/**` — standard mechanical-fastener constant |
| M4 machine screw + washer | standard M4, length TBD | 4 (VESA 75×75) or per Fishtail bracket pattern | Floor-mount hardware (`mounts.scad` VESA/Fishtail pattern, architecture.md §6) | `MCC_VESA75_PITCH` in `lib/mcc/constants.scad` is **assumed** — no VESA reference exists in `knowledge/**`; Fishtail bracket geometry itself is `knowledge/magewell/assets/magewell-fishtail-bracket.stl` |
| Fan | Noctua NF-A4x10 5V | 0 or 1 (Plus-family thermal variants only, architecture.md §11 R5) | 40×40×10 mm, 32 mm hole pitch, 5 V 3-pin, 0.22 W typ | `knowledge/components/fans.md:22` |
| PoE splitter | PoE Texas GAT-USBC | 0 or 1 (placeholder pending `knowledge/components/poe-splitters.md` final selection, architecture.md §12 Q6) | 114×51×25 mm, 85 g, USB-C PD out; **not yet the final chosen part** | `knowledge/components/poe-splitters.md:58` |
| etherCON / RJ45 feedthrough | Neutrik **NE8FDP-B** | per device port map | Black finish, per repo rule "always black `-B` Neutrik parts" | `lib/mcc/constants.scad` `MCC_PANEL_PARTS["NE8FDP-B"]`; ultimately `knowledge/neutrik/d-series-cutout.md` / `knowledge/neutrik/placement-and-depth.md` |
| HDMI feedthrough | Neutrik **NAHDMI-W-B** | per device port map | Max 2 mm panel thickness | `lib/mcc/constants.scad` `MCC_PANEL_PARTS["NAHDMI-W-B"]` |
| USB A/B feedthrough | Neutrik **NAUSB-W-B** | per device port map | Max panel thickness treated as 2.0 mm pending confirmation (architecture.md §11 R4) | `lib/mcc/constants.scad` `MCC_PANEL_PARTS["NAUSB-W-B"]` |
| BNC feedthrough | Neutrik **NBB75DFGB** | per device port map | 75 Ω; Belden 4855R bend radius (40.6 mm) governs bay depth | `lib/mcc/constants.scad` `MCC_PANEL_PARTS["NBB75DFGB"]` |
| Blanking plate | Neutrik **DBA-BL-B** | per unused D-cutout | Fills an unused panel cutout | `lib/mcc/constants.scad` `MCC_PANEL_PARTS["DBA-BL-B"]` |

## Per-variant BOM

Each table below is a skeleton — filled once that device's data file and case model exist. Rows
beyond the common hardware above (Neutrik connectors, PTZ/Tally Mini-DIN-8 solution, etc.) are
per-device, driven by that device's port map (`lib/mcc/devices/<slug>.scad`).

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

### pro-convert-for-ndi-to-aio

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-for-ndi-to-hdmi

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-for-ndi-to-hdmi-4k

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-for-ndi-to-sdi

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-hdmi-4k-plus

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-hdmi-plus

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-hdmi-tx

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

### pro-convert-sdi-plus

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |

### pro-convert-sdi-tx

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| | | | | |
