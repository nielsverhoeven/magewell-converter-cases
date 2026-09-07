# Cable & Connector Clearance Reference

Research notes for sizing the internal depth between a Magewell Pro Convert device's port
face and the case wall (where a short internal cable runs to a panel-mounted Neutrik
D-series connector). Figures below are pulled from manufacturer datasheets and retailer
product pages where fetchable; anything that could not be confirmed from an actually
fetched source is marked `unknown` rather than guessed.

**Research date: 2026-09-07.** Web search budget was exhausted partway through this
research session, and several manufacturer PDF datasheets could not be parsed by the
fetch tool (binary/compressed PDF content) — those gaps are called out explicitly below
and in the Sources list rather than papered over.

---

## 1. Ultra-short RJ45 Cat6A patch cables (slim/flat boot)

| Item | Value | Source |
|---|---|---|
| Standard RJ45 plug body length (IEC 60603-7 / TIA-568.2-D, no boot) | 18.5–21.5 mm (568.2-D caps plug length at ≤21.5 mm for patch-panel clearance) | [accio.com RJ45 plug dimensions](https://www.accio.com/plp/rj45-plug-dimensions) |
| Boot length added beyond the bare plug (slim/short/flush boot types) | `unknown` — no manufacturer figure found in mm | — |
| Cables Plus USA "Ultra Short" molded boot | Described as "flush boot design" giving "minimum boot projection at the plug/cable interface"; cable OD 0.115 in (2.9 mm), stranded 32 AWG, lengths from 1–7 ft (shortest listed is 1 ft / 0.3 m, not down to 0.15 m) | [store.cablesplususa.com](https://store.cablesplususa.com/ultra-slim-cat6-ethernet-patch-cable-stranded-32awg-utp-bare-copper-black-jacket-ultra-short-molded-boot/) |
| Product example: 0.15 m Cat6 slim patch cable, snagless, unshielded | Length 6 in / 0.15 m / 0.5 ft | [FS.com](https://www.fs.com/eu-en/products/66742.html) |
| Product example: SlimRun Cat6, 28 AWG, snagless RJ45, 6 in | Component-level slim patch cable | [Monoprice #13510](https://www.monoprice.com/product?p_id=13510) (page returned 403 on fetch; found via search) |

**Note:** IEC 60603-7 also specifies housing width 14.0 mm ±0.1 mm — not the relevant dimension for depth clearance, included only for completeness.

---

## 2. EtherCON-to-RJ45 short leads (Neutrik etherCON)

| Item | Value | Source |
|---|---|---|
| Neutrik NE8MC-B (RJ45 cable connector carrier / etherCON boot) mechanical specs | Cable O.D. max 8 mm; insertion/withdrawal force ≤20 N; >1000 mating cycles; -30°C to +80°C | [neutrik.com NE8MC-B](https://www.neutrik.com/en/product/ne8mc-b) |
| Overall assembled length of etherCON connector (shell + boot) | `unknown` — not listed on the HTML product page; the official dimensioned datasheet PDF ([neutrik.com PDF](https://www.neutrik.com/media/8070/download/ethercon-cable-connector-ne8mc.pdf?v=1)) could not be parsed by the fetch tool (binary PDF stream) | — |
| Product family example: Van Damme Tourcat etherCON leads (Cat5e/Cat6/Cat6a) | Multiple lengths, screened, Neutrik NE8MC terminated | [designacable.com](https://www.designacable.com/screened-cat5e-ethercon-lead-flexible-van-damme-cable-neutrik-rj45-cabling.html) |
| Product family example: Cat5e etherCON shielded patch leads | Category listing | [comms-express.com](https://www.comms-express.com/categories/cat5e-rj45-neutrik-ethercon-shielded-patch-leads-cables/) |
| Product example: Sommer Cable Cat6a RJ45 lead | Shortest confirmed listing found was 1 m, not ultra-short | [thomann.co.uk](https://www.thomann.co.uk/sommer_cable_cat_6a_cable_1m_rj45_rj45.htm) |

**Important caveat:** one search-engine summary (not an independently fetched/read source) suggested a Neutrik NE8MX6 assembly length of ~76.5 mm. Because this was not confirmed by directly fetching and reading a primary source, it is **not** used as a verified figure here — treat etherCON overall length as `unknown` until physically measured or confirmed against a readable Neutrik CAD/PDF drawing. EtherCON's ruggedized locking shell is visibly and substantially larger than a bare RJ45 plug (see product photos at the links above), so budget meaningfully more depth than for plain RJ45.

---

## 3. Ultra-short HDMI cables and right-angle adapters

| Item | Value | Source |
|---|---|---|
| HDMI Type A connector cross-section | Plug 13.9 mm × 4.45 mm; receptacle 14 mm × 4.55 mm (width × height only — axial plug **length/depth** not given) | [Wikipedia: HDMI](https://en.wikipedia.org/wiki/HDMI) |
| Straight HDMI plug overall length beyond port face | `unknown` — no fetched source gave an axial length figure | — |
| Right-angle HDMI adapter added depth (90°/270° combo, any rotation) | "Each right angle HDMI adapter extends less than 1 inch [25.4 mm] from the HDMI port" | [Cable Matters combo pack](https://www.cablematters.com/pc-484-141-combo-pack-270-degree-and-90-degree-right-angle-hdmi-adapter.aspx) |
| Per-direction (up/down/left/right) breakdown | `unknown` — Cable Matters gives one figure for the adapter regardless of which way it's rotated; a single 90° adapter body is rotated to point whichever direction is needed, so the added-depth figure above applies to all four orientations of that product | Same as above |
| Product example: ultra-short mini-HDMI cable, right angle, 15 cm | Mini-HDMI (not full-size), 90° downward angle, 4K@60Hz | [Amazon (YOUCHENG)](https://www.amazon.com/Degree-Adapter-Support-YOUCHENG-Raspberry/dp/B08QCPPF8P) — noted as mini-HDMI, included only as an illustrative short-cable example |
| Product example: right-angle HDMI adapter (right-exit) | C2G / Legrand AV | [cablestogo.com](https://www.cablestogo.com/audio-video/adapters-and-couplers/right-angle-hdmi-adapter-right-exit/p/cg-43290) (redirects to legrandav.com; no dimension figure retrievable from that page) |
| Ultra-short full-size straight HDMI (0.15–0.3 m) | Widely available (Amazon/Walmart/Target/Adorama listings), but no specific product page with a verified plug-length figure was fetched | General search only — see Sources |

---

## 4. Ultra-short 12G-SDI BNC-to-BNC leads

| Item | Value | Source |
|---|---|---|
| Belden 4694R (12G-SDI, "RG-6 style", 18 AWG solid, 6.96 mm / 0.274 in OD) — min bend radius | 2.750 in ≈ **69.9 mm** | [avlgear.com Belden 4694R](https://avlgear.com/products/belden-4694r-12g-sdi-75-ohm-4k-uhd-rg-6-coax-video-cable-18-awg-black-1000-feet) |
| Belden 4855R (12G-SDI, "Mini RG-59", 23 AWG, 4.04 mm / 0.159 in OD) — min bend radius | 1.600 in ≈ **40.6 mm** | [avlgear.com Belden 4855R](https://avlgear.com/products/belden-4855r-12g-sdi-75-ohm-4k-uhd-mini-rg-59-coax-video-cable-black-1000-feet) |
| BNC male plug overall/mated length | `unknown` — only outer diameter (0.570 in / 14.5 mm) was found, not axial length; Amphenol RF and Farnell/TTI BNC catalog PDFs either 403'd or were unreadable binary PDFs | [Wikipedia: BNC connector](https://en.wikipedia.org/wiki/BNC_connector) |
| Product example: 6 in (0.15 m) 12G-SDI BNC extension lead, Belden 4855R | SKU 103030-12G-6INCH — this is the shortest pre-made length found for this cable type | [customcableconnection.com](https://customcableconnection.com/products/hd-sdi-mini-rg59-bnc-extension-cables-12g-rated) |
| Product example: thin/short SDI cable, 12 in | Marketed for compact camera/monitor rigs | [SmallHD 12" Thin SDI Cable](https://smallhd.com/products/12-inch-thin-sdi-cable) |

**Practical note:** for a case with tight internal depth, prefer Belden 4855R (mini coax) over 4694R — its bend radius is roughly 60% smaller (40.6 mm vs. 69.9 mm), which is normally the dominant space constraint for a coax lead, not the BNC plug body itself.

---

## 5. USB-A to USB-A and USB-A to USB-B short cables

| Item | Value | Source |
|---|---|---|
| USB Type-A plug body length (insertion depth) | ≈ 12 mm | [accesscomms.com.au](https://www.accesscomms.com.au/usb-connector-dimensions/) |
| USB Type-B plug body length | `unknown` — not separately researched/verified | — |
| Product example: USB 2.0 A-to-A, 6 in (0.15 m) | 480 Mbps, OD 4.5 mm | [Amazon (MyCableMart)](https://www.amazon.com/MyCableMart-Certified-480Mbps-Beige-Cable/dp/B010RH9AL0) |
| Product example: USB 2.0 A-to-B, 0.5 ft (0.15 m) | 28 AWG, 480 Mbps | [ShowMeCables](https://www.showmecables.com/usb-2-0-a-male-to-b-male-0-5-ft) |

---

## 6. DC barrel extension leads and XLR4-to-DC-barrel adapters

| Item | Value | Source |
|---|---|---|
| 5.5×2.1 mm DC barrel plug (in-line, unscrewable shell, solder/crimp type) — overall length | 33.7 mm; shell diameter 9.7 mm | [Adafruit #3310](https://www.adafruit.com/product/3310) |
| 5.5×2.5 mm DC barrel plug — overall length | `unknown` — not separately verified | — |
| XLR4 (4-pin) connector body — overall length | `unknown` — Neutrik NC4MXX HTML product page lists only electrical/mechanical ratings (cable OD 3.5–8.0 mm, insertion force ≤20 N, IP40, -30 to +80°C), no length figure; the dimensioned PDF datasheet could not be parsed | [neutrik.com NC4MXX](https://www.neutrik.com/en/product/nc4mxx) |
| Product example: DC barrel extension, 5.5×2.1 mm, male–female, 30 cm, panel-mount | | [Adafruit #5607](https://www.adafruit.com/product/5607) / [The Pi Hut](https://thepihut.com/products/round-panel-mount-5-5mm-2-1mm-dc-barrel-jack-extension-cable-30cm-long) |
| Product example: XLR4-female to 2.1 mm DC barrel adapter, 17 in | | [Amazon (Fotodiox)](https://www.amazon.com/Fotodiox-Adapter-Female-Barrel-inches/dp/B075G32DVQ) |
| Product example: XLR4-male to 2.1 mm DC barrel power cable, 10 ft | | [B&H (Bescor)](https://www.bhphotovideo.com/c/product/1457759-REG/bescor_xlrmpp_10_4_pin_xlr_male.html) |
| Product example: XLR4-female DC power adapter cable | | [B&H (LanParte DC-4PXLR)](https://www.bhphotovideo.com/c/product/1100264-REG/lanparte_dc_4pxlr_4_pin_xlr_female_dc.html) |

**Note:** the 33.7 mm figure is for one specific in-line solder-type barrel plug with an unscrewing outer shell; a factory-molded cable-mount barrel plug on a pre-made lead may be shorter, but no such figure was independently verified.

---

## 7. 3.5mm TRS short leads (audio)

| Item | Value | Source |
|---|---|---|
| 3.5 mm TRS plug overall length | `unknown` — Switchcraft's 3.5mm jacks-and-plugs category page returned no dimensional content on fetch, and B&H's Switchcraft 35HDBAU product page returned 403 | — |
| Product example: 15 cm 3.5mm TRS extension lead, male–female, 90° angle | 2-pack | [Amazon (Kework)](https://www.amazon.com/3-5mm-Kework-2-pack-Stereo-Headphone/dp/B07D1Z6XXZ) |
| Product example: 3.5mm TRS cable, manufacturer reference | Cable Matters 3.5mm TRS product line (shortest confirmed listing was a 3 ft breakout cable, not an ultra-short lead) | [Amazon (Cable Matters)](https://www.amazon.com/Cable-Matters-3-5mm-Adapter-Breakout/dp/B0CBHPZYZ7) |

---

## Space needed between device port face and case wall

Recommended clearance = verified plug length + a margin, per row's reasoning. Where the
plug length itself is `unknown`, the recommendation either falls back to the dominant
verified constraint (e.g. coax bend radius) or is left `unknown` rather than fabricated —
**every such case is flagged for physical measurement/mockup before finalizing case
geometry.**

| Cable/Adapter type | Plug overall length beyond port (mm) | Min bend radius (mm) | Recommended minimum internal clearance (mm) | Notes |
|---|---|---|---|---|
| RJ45 Cat6A slim/short-boot patch lead | 18.5–21.5 (bare plug, verified); boot adds `unknown` extra | n/a | **~27 mm** (21.5 mm max plug + 5 mm generic margin) | Treat as a lower bound — boot projection wasn't independently verified in mm; "ultra short/flush" boots are marketed as adding minimal length, but confirm against the actual chosen product. |
| EtherCON-to-RJ45 lead (Neutrik NE8MC/NE8MX shell) | `unknown` | n/a | `unknown` — physically measure the specific connector | EtherCON's locking shell is visibly larger than bare RJ45; budget noticeably more depth than the RJ45 row until measured. Do not use the unverified 76.5 mm figure mentioned in Section 2. |
| Ultra-short HDMI, straight plug | `unknown` | n/a | `unknown` — physically measure | No axial plug-length source found; only cross-section (13.9×4.45 mm) verified. |
| Right-angle HDMI adapter (any of up/down/left/right) | 25.4 (verified, "<1 inch") | n/a | **~30 mm** (25.4 mm + 5 mm margin for the adapter body/cable exit) | Same physical adapter rotated to whichever direction is needed; figure is from one manufacturer (Cable Matters) and may vary slightly by brand. |
| Ultra-short 12G-SDI BNC-to-BNC lead (Belden 4855R mini coax, recommended for tight spaces) | `unknown` (BNC plug body not verified) | 40.6 (verified) | **≥ 41 mm**, driven by cable bend radius rather than plug length | Bend radius is the binding constraint for coax — the cable must be allowed to curve at least this radius as it turns from the BNC plug toward the case wall exit; add more if the connector's own body length turns out to exceed this once measured. |
| Ultra-short 12G-SDI BNC-to-BNC lead (Belden 4694R standard coax, if used instead) | `unknown` | 69.9 (verified) | **≥ 70 mm** | Same reasoning as above; use only if 4855R's smaller OD/bend radius isn't suitable. |
| USB-A to USB-A / USB-A to USB-B short cable (USB-A end) | 12 (verified) | n/a | **~17 mm** (12 mm + 5 mm margin) | USB-B plug length not verified; if the device's port is USB-B, treat that end as `unknown` and measure. |
| DC barrel extension lead, 5.5×2.1 mm | 33.7 (verified, one representative in-line product) | n/a | **~39 mm** (33.7 mm + 5 mm margin) | Figure is for an in-line solder-shell plug; a molded cable-mount plug may be shorter — confirm against the actual product chosen. |
| DC barrel extension lead, 5.5×2.5 mm | `unknown` | n/a | `unknown` — physically measure | Not separately researched; likely similar order of magnitude to 5.5×2.1 mm given the shared barrel format, but not confirmed. |
| XLR4-to-DC-barrel adapter (XLR4 end) | `unknown` | n/a | `unknown` — physically measure | Neutrik's HTML spec pages omit length; PDF datasheets were not machine-readable in this research pass. Expect this to be one of the largest connectors in the list based on general XLR form factor, but do not use that as a numeric planning figure without direct measurement. |
| 3.5mm TRS short lead | `unknown` | n/a | `unknown` — physically measure | No dimensioned source was retrievable (403s / empty fetch) in this pass. |

**General margin logic used above:** for connectors with a verified plug length but no
governing cable bend-radius spec (RJ45, HDMI right-angle, USB-A, DC barrel), a flat +5 mm
was added as generic service margin (connector housing tolerance, slight cable stiffness
at the exit, room to seat the connector without forcing it). For the coax (SDI) leads,
the manufacturer's published minimum bend radius is used directly as the clearance
driver instead, since that is normally larger than the BNC plug body and is the figure
that actually determines whether the cable can turn cleanly inside the case without
kinking or degrading signal integrity.

---

## Sources

- [Belden 4694R — avlgear.com product page](https://avlgear.com/products/belden-4694r-12g-sdi-75-ohm-4k-uhd-rg-6-coax-video-cable-18-awg-black-1000-feet) — min bend radius (2.750 in) and OD (0.274 in) for 4694R. Fetched 2026-09-07.
- [Belden 4855R — avlgear.com product page](https://avlgear.com/products/belden-4855r-12g-sdi-75-ohm-4k-uhd-mini-rg-59-coax-video-cable-black-1000-feet) — min bend radius (1.600 in) and OD (0.159 in) for 4855R. Fetched 2026-09-07.
- [Belden 4694R technical data sheet (PDF)](https://catalog.belden.com/techdata/EN/4694R_techdata.pdf) — attempted fetch; binary PDF, unreadable by fetch tool. 2026-09-07.
- [Belden 4855R technical data sheet (PDF)](https://catalog.belden.com/techdata/EN/4855R_techdata.pdf) — attempted fetch; binary PDF, unreadable. 2026-09-07.
- [Belden 4694R — Belden.com product page](https://www.belden.com/products/cable/video-cable/coaxial-video-cable/4694r) — 403 Forbidden on fetch. 2026-09-07.
- [Belden 4855R — Belden.com product page](https://www.belden.com/products/cable/broadcast-cable/sdi-video-coax-cable/4855r) — 403 Forbidden on fetch. 2026-09-07.
- [accio.com — RJ45 plug dimensions](https://www.accio.com/plp/rj45-plug-dimensions) — IEC 60603-7 / TIA-568.2-D plug length (18.5–21.5 mm) and housing width figures. Fetched 2026-09-07.
- [Cables Plus USA — Ultra-Slim Cat6 patch cable](https://store.cablesplususa.com/ultra-slim-cat6-ethernet-patch-cable-stranded-32awg-utp-bare-copper-black-jacket-ultra-short-molded-boot/) — boot design description, cable OD, available lengths. Fetched 2026-09-07.
- [FS.com — 0.15 m Cat6 slim patch cable](https://www.fs.com/eu-en/products/66742.html) — product example, found via search (direct fetch returned no content). 2026-09-07.
- [Monoprice #13510 — SlimRun Cat6 patch cable](https://www.monoprice.com/product?p_id=13510) — product example; fetch returned 403. 2026-09-07.
- [Zion Communication — Patch Cord Boot Types Explained](https://www.zion-communication.com/Patch-Cord-Boot-Types-Explained-Snagless-Slim-Short-and-Molded-Boots-id05104255.html) — qualitative description of snagless/slim/short/molded boots; no mm figures found. Fetched 2026-09-07.
- [Neutrik NE8MC-B product page](https://www.neutrik.com/en/product/ne8mc-b) — mechanical/environmental specs for etherCON cable connector carrier; no overall length given. Fetched 2026-09-07.
- [Neutrik etherCON NE8MC datasheet (PDF)](https://www.neutrik.com/media/8070/download/ethercon-cable-connector-ne8mc.pdf?v=1) — attempted fetch; binary PDF, unreadable. 2026-09-07.
- [designacable.com — Van Damme Tourcat etherCON lead](https://www.designacable.com/screened-cat5e-ethercon-lead-flexible-van-damme-cable-neutrik-rj45-cabling.html) — product example. Fetched via search 2026-09-07.
- [comms-express.com — Cat5e etherCON shielded patch leads category](https://www.comms-express.com/categories/cat5e-rj45-neutrik-ethercon-shielded-patch-leads-cables/) — product category example. Found via search 2026-09-07.
- [Thomann UK — Sommer Cable Cat6a RJ45/RJ45 1m](https://www.thomann.co.uk/sommer_cable_cat_6a_cable_1m_rj45_rj45.htm) — product example. Found via search 2026-09-07.
- [Wikipedia — HDMI](https://en.wikipedia.org/wiki/HDMI) — Type A connector cross-section (13.9×4.45 mm plug / 14×4.55 mm receptacle); no axial length. Fetched 2026-09-07.
- [Cable Matters — 270°/90° right-angle HDMI adapter combo pack](https://www.cablematters.com/pc-484-141-combo-pack-270-degree-and-90-degree-right-angle-hdmi-adapter.aspx) — "extends less than 1 inch from the HDMI port" figure. Fetched 2026-09-07.
- [cablestogo.com / legrandav.com — right-angle HDMI adapter (right exit)](https://www.cablestogo.com/audio-video/adapters-and-couplers/right-angle-hdmi-adapter-right-exit/p/cg-43290) — product example; redirected page had no dimension content. Fetched 2026-09-07.
- [Amazon — YOUCHENG 15cm mini-HDMI right-angle cable](https://www.amazon.com/Degree-Adapter-Support-YOUCHENG-Raspberry/dp/B08QCPPF8P) — illustrative short-cable product example (mini-HDMI, not full-size). Found via search 2026-09-07.
- [Wikipedia — BNC connector](https://en.wikipedia.org/wiki/BNC_connector) — male BNC outer diameter (14.5 mm); no axial length figure. Fetched 2026-09-07.
- [Amphenol RF — BNC connectors](https://www.amphenolrf.com/rf-connectors/bnc-connectors.html) — attempted fetch for dimensions; 403 Forbidden. 2026-09-07.
- [L-com — 12G SDI connectors category](https://www.l-com.com/coaxial-12g-sdi-connectors) — attempted fetch for dimensioned products; listing page had no per-product dimension data. 2026-09-07.
- [customcableconnection.com — 12G-SDI BNC extension cables (Belden 4855R)](https://customcableconnection.com/products/hd-sdi-mini-rg59-bnc-extension-cables-12g-rated) — confirmed shortest available length is 6 in (0.15 m), SKU 103030-12G-6INCH. Fetched 2026-09-07.
- [SmallHD — 12" Thin SDI Cable](https://smallhd.com/products/12-inch-thin-sdi-cable) — product example. Found via search 2026-09-07.
- [accesscomms.com.au — USB connector dimensions](https://www.accesscomms.com.au/usb-connector-dimensions/) — USB Type-A plug body length (~12 mm). Fetched 2026-09-07.
- [Amazon — MyCableMart 6in USB 2.0 A-to-A cable](https://www.amazon.com/MyCableMart-Certified-480Mbps-Beige-Cable/dp/B010RH9AL0) — product example, cable OD 4.5 mm. Found via search 2026-09-07.
- [ShowMeCables — USB 2.0 A-to-B, 0.5 ft](https://www.showmecables.com/usb-2-0-a-male-to-b-male-0-5-ft) — product example. Found via search 2026-09-07.
- [Adafruit #3310 — 5.5/2.1mm DC barrel plug](https://www.adafruit.com/product/3310) — overall length 33.7 mm, diameter 9.7 mm. Fetched 2026-09-07.
- [Adafruit #5607 — 30cm DC barrel jack extension cable](https://www.adafruit.com/product/5607) / [The Pi Hut mirror](https://thepihut.com/products/round-panel-mount-5-5mm-2-1mm-dc-barrel-jack-extension-cable-30cm-long) — product example. Found via search 2026-09-07.
- [Amazon — Fotodiox 4-pin XLR female to 2.1mm DC barrel, 17in](https://www.amazon.com/Fotodiox-Adapter-Female-Barrel-inches/dp/B075G32DVQ) — product example; fetch returned only page title, no body spec content. 2026-09-07.
- [B&H — Bescor 4-pin XLR male to 2.1mm DC barrel, 10ft](https://www.bhphotovideo.com/c/product/1457759-REG/bescor_xlrmpp_10_4_pin_xlr_male.html) — product example. Found via search 2026-09-07.
- [B&H — LanParte DC-4PXLR](https://www.bhphotovideo.com/c/product/1100264-REG/lanparte_dc_4pxlr_4_pin_xlr_female_dc.html) — product example. Found via search 2026-09-07.
- [Neutrik NC4MXX product page](https://www.neutrik.com/en/product/nc4mxx) — mechanical/electrical specs for 4-pin XLR male connector; no overall length given. Fetched 2026-09-07.
- [Neutrik XLR product guide (PDF, via Mouser)](https://www.mouser.com/datasheet/2/289/Product_Guide_-_Section_XLR-938291.pdf) — referenced in search results but not fetched (PDF). 2026-09-07.
- [Switchcraft — 3.5mm jacks and plugs category](https://www.switchcraft.com/catalog/jacks-and-plugs/audio-jacks-and-plugs/3-5-mm-jacks-and-plugs/) — attempted fetch; page returned no content. 2026-09-07.
- [B&H — Switchcraft 35HDBAU 3.5mm TRS plug](https://www.bhphotovideo.com/c/product/929574-REG/switchcraft_35hdbau_3_5mm_stereo_plug_0_290.html) — attempted fetch; 403 Forbidden. 2026-09-07.
- [Amazon — Kework 15cm 3.5mm TRS extension lead](https://www.amazon.com/3-5mm-Kework-2-pack-Stereo-Headphone/dp/B07D1Z6XXZ) — product example. Found via search 2026-09-07.
- [Amazon — Cable Matters 3.5mm TRS breakout cable](https://www.amazon.com/Cable-Matters-3-5mm-Adapter-Breakout/dp/B0CBHPZYZ7) — manufacturer reference example (3ft, not ultra-short). Found via search 2026-09-07.
