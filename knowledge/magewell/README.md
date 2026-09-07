# Magewell Pro Convert — Knowledge Base

Reference data for designing 3D-printable protective cases for Magewell Pro Convert devices.
Sourced from magewell.com product pages, tech-spec pages, datasheet PDFs and user manuals,
fetched 2026-09-07. See `sources.md` for the full URL list.

Conventions: dimensions in mm (L × W × H as printed on the datasheet), power in W, temperature in
°C. `unknown` = not published anywhere found. `(estimated from image)` = read off a product photo,
not a spec sheet. Retailer-sourced figures are marked "(retailer, unverified)" and are a fallback
only — never a substitute for an official figure. A `*` on a Fan value flags a contradiction between
sources; see the note under the table and `housing-families.md` / `power-and-thermal.md`.

## All models

| Model | SKU | Type | Housing family | L × W × H (mm) | Weight | PoE | DC input | Max power | Op. temp | Fan | Detail |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pro Convert HDMI 4K Plus | 640100000 (KR 640100006) | Encoder | [Plus](housing-families.md#a-plus-1175--667--234-mm) | 117.5 × 66.7 × 23.4 | unknown | 802.3af | 5 V USB-B ~2 A (adapter 5 V/2.1 A) | ~10 W | 0–45 °C | yes* | [file](models/pro-convert-hdmi-4k-plus.md) |
| Pro Convert SDI 4K Plus | 640300000 (KR 640300006) | Encoder | [Plus](housing-families.md#a-plus-1175--667--234-mm) | 117.5 × 66.7 × 23.4 | unknown (retailer "2.2 lb", unverified) | 802.3af | 5 V ~1.5 A (adapter 5 V/2.1 A) | ~7 W | 0–45 °C | yes* | [file](models/pro-convert-sdi-4k-plus.md) |
| Pro Convert 12G SDI 4K Plus | 640900000 (KR 640900002) | Encoder | [Plus](housing-families.md#a-plus-1175--667--234-mm) | 117.5 × 66.7 × 23.4 | unknown (retailer "0.300 kg", unverified) | 802.3af | 5 V ~1.65 A (adapter 5 V/2.1 A) | ~8.5 W | 0–45 °C | yes* | [file](models/pro-convert-12g-sdi-4k-plus.md) |
| **Pro Convert HDMI Plus** | 640200000 (KR 640200006) | Encoder | [Plus](housing-families.md#a-plus-1175--667--234-mm) | 117.5 × 66.7 × 23.4 | unknown (retailer "1.2 lb", low confidence) | 802.3af | 5 V ~1.5 A (adapter 5 V/2.1 A) | ~8 W | 0–45 °C | uncertain* | [file](models/pro-convert-hdmi-plus.md) |
| **Pro Convert SDI Plus** | 640400000 (KR 640400006) | Encoder | [Plus](housing-families.md#a-plus-1175--667--234-mm) | 117.5 × 66.7 × 23.4 | unknown | 802.3af | 5 V ~1.5 A (adapter 5 V/2.1 A) | ~7 W | 0–45 °C | uncertain* | [file](models/pro-convert-sdi-plus.md) |
| **Pro Convert HDMI TX** | 640500000 (KR 640500006) | Encoder | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | ~230 g (retailer, unverified) | 802.3af | 5 V ~1.5 A (adapter 5 V/2.1 A) | ~6 W | 0–40 °C | no | [file](models/pro-convert-hdmi-tx.md) |
| **Pro Convert SDI TX** | 640600000 (KR 640600006) | Encoder | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | unknown | 802.3af | 5 V ~1.5 A (adapter 5 V/2.1 A) | ~7 W | 0–40 °C | no | [file](models/pro-convert-sdi-tx.md) |
| **Pro Convert for NDI to HDMI** | 641000000 (64100) | Decoder | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | unknown | 802.3af | 5 V ~1.1 A (adapter 5 V/2.1 A) | ~5 W | 0–40 °C | no | [file](models/pro-convert-for-ndi-to-hdmi.md) |
| **Pro Convert for NDI to HDMI 4K** | 641100000 | Decoder | [Plus](housing-families.md#a-plus-1175--667--234-mm) (unusual — see note) | 117.5 × 66.7 × 23.4 | unknown | 802.3af | 5 V ~1.6 A (adapter 5 V/2.1 A) | ~7.2 W | 0–45 °C | yes | [file](models/pro-convert-for-ndi-to-hdmi-4k.md) |
| **Pro Convert for NDI to SDI** | 641500000 (64150) | Decoder | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | unknown | 802.3af | 5 V ~1.05 A (adapter 5 V/2.1 A) | ~5.5 W | 0–40 °C | no | [file](models/pro-convert-for-ndi-to-sdi.md) |
| **Pro Convert for NDI to AIO** | 642100000 | Decoder | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | unknown | 802.3af | 5 V ~1.05 A (adapter 5 V/2.1 A) | ~5.5 W | 0–40 °C | no | [file](models/pro-convert-for-ndi-to-aio.md) |
| Pro Convert IP to HDMI | 644300000 (64430) | Decoder | [IP decoder](housing-families.md#c-ip-decoder-120--793--245-mm) | 120 × 79.3 × 24.5 | unknown | 802.3af/at | USB-C 5 V/12 V, 10 W | ~6.62 W | 0–40 °C | no | [file](models/pro-convert-ip-to-hdmi.md) |
| Pro Convert IP to HDMI 4K | 644100000 (64410) | Decoder | [IP decoder](housing-families.md#c-ip-decoder-120--793--245-mm) | 120 × 79.3 × 24.5 | unknown | 802.3at | USB-C 12 V, 20 W | ~12.12 W | 0–40 °C | no | [file](models/pro-convert-ip-to-hdmi-4k.md) |
| Pro Convert IP to AIO 4K | 644000000 (64400) | Decoder | [IP decoder](housing-families.md#c-ip-decoder-120--793--245-mm) | 120 × 79.3 × 24.5 | unknown (retailer ~200 g, conflicts with official specs) | 802.3at | USB-C 12 V, 20 W | ~15.1 W | 0–40 °C | no | [file](models/pro-convert-ip-to-aio-4k.md) |
| Pro Convert IP to USB | 623000000 (62300, model ED0230A) | Decoder | [IP to USB](housing-families.md#d-ip-to-usb-981--5678--18-mm) | 98.1 × 56.78 × 18 | unknown | none | USB-C 5 V/1 A from host | ~3.8 W | 0–50 °C | no | [file](models/pro-convert-ip-to-usb.md) |
| Pro Convert AES67 | 642400000 (KR 642400001, part 64240) | Audio | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | unknown | 802.3af | 5 V USB-B, ~1 A (adapter 5 V/2.1 A) | ~5 W | –10–50 °C | no | [file](models/pro-convert-aes67.md) |
| Pro Convert Audio DX | 642600000 (KR 642600001) | Audio | [Compact/TX](housing-families.md#b-compacttx-1009--602--233-mm) | 100.9 × 60.2 × 23.3 | unknown (retailer "1.76 lb" is boxed weight, unreliable) | 802.3af | 5 V USB-B (adapter 5 V/2.1 A) | ~5 W | –10–50 °C | no | [file](models/pro-convert-audio-dx.md) |

`*` Fan contradiction: for the 4K-capable Plus models (HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus)
the Web-UI shows a "Fan Speed" field that reports say is "not available for TX products" (implying
it applies to these) — but the shared Pro Convert decoder manual states variable-speed fan is "ONLY
available for 4K products" (p.18), which for HDMI Plus/SDI Plus (not 4K-capable) argues against a
fan being present. Their own official datasheets list no fan at all. Treated here as: **yes** for
the three 4K-capable Plus-family encoders and NDI to HDMI 4K; **uncertain** for HDMI Plus/SDI Plus.
See `housing-families.md` and `power-and-thermal.md` for the full discussion.

## Housing families

Four distinct chassis are used across the whole Pro Convert line. Full dimensioned face-by-face
breakdown, port order, and case-design implications are in **[housing-families.md](housing-families.md)**.

| Family | Dimensions (mm) | Members | Cooling |
|---|---|---|---|
| (a) Plus | 117.5 × 66.7 × 23.4 | HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus, HDMI Plus, SDI Plus, NDI to HDMI 4K | Internal fan on 4K-capable models (see contradiction note); top circular grille |
| (b) Compact/TX | 100.9 × 60.2 × 23.3 | HDMI TX, SDI TX, NDI to HDMI, NDI to SDI, NDI to AIO, AES67, Audio DX | Fanless |
| (c) IP decoder | 120 × 79.3 × 24.5 | IP to HDMI, IP to HDMI 4K, IP to AIO 4K | Fanless, louvered top vents |
| (d) IP to USB | 98.1 × 56.78 × 18 | IP to USB | Fanless, no vents |

## Priority models for this project

These are the models this project's case designs are being built for first:

- **Pro Convert HDMI Plus** — `models/pro-convert-hdmi-plus.md`
- **Pro Convert SDI Plus** — `models/pro-convert-sdi-plus.md`
- **Pro Convert HDMI TX** — `models/pro-convert-hdmi-tx.md`
- **Pro Convert SDI TX** — `models/pro-convert-sdi-tx.md`
- **Pro Convert for NDI to HDMI** — `models/pro-convert-for-ndi-to-hdmi.md`
- **Pro Convert for NDI to HDMI 4K** — `models/pro-convert-for-ndi-to-hdmi-4k.md`
- **Pro Convert for NDI to SDI** — `models/pro-convert-for-ndi-to-sdi.md`
- **Pro Convert for NDI to AIO** — `models/pro-convert-for-ndi-to-aio.md`

Note: HDMI Plus/SDI Plus use the (a) Plus chassis (117.5 × 66.7 × 23.4 mm); HDMI TX/SDI TX and the
NDI to HDMI/SDI/AIO decoders use the (b) Compact/TX chassis (100.9 × 60.2 × 23.3 mm); NDI to HDMI 4K
is the odd one out — same electronics family as the other NDI decoders but housed in the larger (a)
Plus chassis.

## Other reference files

- **[housing-families.md](housing-families.md)** — chassis dimensions, face-by-face port layout, case-design implications.
- **[power-and-thermal.md](power-and-thermal.md)** — full power/thermal table and heat-budget notes.
- **[accessories.md](accessories.md)** — L-bracket, Fishtail bracket, rack kits, shelves, Modator 2U.
- **[sources.md](sources.md)** — every source URL, grouped by model/topic.
- **[models/](models/)** — one file per model with full identity/physical/port/power/mounting detail.
