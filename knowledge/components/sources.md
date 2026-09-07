# Sources — components/ and design/ knowledge files

Consolidated source list for the five researcher-written knowledge files:

- `components/fans.md`
- `components/fasteners-and-hardware.md`
- `components/cables.md`
- `design/fdm-rugged-enclosure-guidelines.md`
- `design/thermal-guidelines.md`

Fetch date shown for every entry is **2026-09-07** (the reference date given to the researchers),
even where a source document's own internal notes mention a slightly different research-session
date range. Status flags:

- **BLOCKED (403)** — server refused automated fetch (HTTP 403 Forbidden)
- **BLOCKED (429)** — server rate-limited automated fetch (HTTP 429 Too Many Requests)
- **UNPARSEABLE** — fetched but binary/compressed content (usually a PDF) the fetch tool could not
  render as text
- **search result** — URL surfaced by a web search; page itself not independently fetched/read
- **fetched** — page was successfully retrieved and read

Where no status is shown, treat the row as **fetched**.

---

## From `components/fans.md` — Noctua fans and accessories

| URL | Used for | Status |
|---|---|---|
| https://www.noctua.at/en/products/nf-a4x10-5v/specifications | NF-A4x10 5V full spec table (speed/airflow/pressure/noise/current/power) | fetched *(see note below — contradicted by thermal-guidelines.md)* |
| https://www.noctua.at/en/products/nf-a4x10-5v-pwm/specifications | NF-A4x10 5V PWM full spec table | fetched |
| https://www.noctua.at/en/products/nf-a4x10-flx/specifications | NF-A4x10 FLX (12V, 3-pin) full spec table | fetched |
| https://www.noctua.at/en/products/nf-a4x10-pwm/specifications | NF-A4x10 PWM (12V, 4-pin) full spec table | fetched |
| https://www.noctua.at/en/products/nf-a4x20-5v/specifications | NF-A4x20 5V full spec table | fetched |
| https://www.noctua.at/en/products/nf-a4x20-5v-pwm/specifications | NF-A4x20 5V PWM full spec table | fetched |
| https://www.noctua.at/en/products/nf-a4x20-pwm/specifications | NF-A4x20 PWM (12V) full spec table | fetched |
| https://www.noctua.at/en/products/nf-a6x25-5v/specifications | NF-A6x25 5V full spec table | fetched |
| https://www.noctua.at/en/products/nf-a6x25-5v-pwm/specifications | NF-A6x25 5V PWM full spec table | fetched |
| https://www.noctua.at/en/products/nf-a6x25-pwm/specifications | NF-A6x25 PWM (12V) full spec table | fetched |
| https://www.noctua.at/en/products/nf-a8-5v/specifications | NF-A8 5V full spec table, incl. bundled USB power cable | fetched |
| https://www.noctua.at/en/products/nf-a8-flx/specifications | NF-A8 FLX (12V, 3-pin) full spec table | fetched |
| https://www.noctua.at/en/products/na-sav3/specifications | NA-SAV3 (16-pack NA-AV3 anti-vibration mount) spec | fetched |
| https://www.noctua.at/en/support/faqs/how-to-install-the-fan-using-the-anti-vibration-mounts | NA-AV3 double-sided mount / pawl-numbering install mechanism | fetched |
| https://www.noctua.at/en/products/na-fc1/specifications | NA-FC1 fan controller spec (PWM, 3-fan, 5–12V, 3A) | fetched |
| https://www.noctua.at/en/products/na-sec1/specifications | NA-SEC1 (3-pack 30cm extension cable) spec | fetched |
| https://www.noctua.at/en/expertise/tech/omnijoin-adaptor-set | OmniJoin adaptor set purpose/usage | fetched |
| https://www.noctua.at/en/support/faqs/can-i-power-fans-via-a-wall-socket | NA-AC7 USB cable bundling rules; NV-PS1/NA-AC10 wall power for 12V fans | fetched |
| https://www.amazon.de/s?k=Noctua+NF-A4x10+5V+PWM | Street prices, NF-A4x10/A4x20 5V-family variants | fetched |
| https://www.amazon.de/s?k=Noctua+NF-A6x25+5V | Street prices, NF-A6x25 variants | fetched |
| https://www.amazon.de/s?k=Noctua+NF-A8+FLX+NA-FC1+NA-SAV3 | Street price, NF-A8 FLX/PWM | fetched |
| https://www.amazon.de/s?k=Noctua+NF-A8+5V+3-pin | Street price, NF-A8 5V/5V PWM | fetched |
| https://www.amazon.de/s?k=Noctua+NA-FC1+fan+controller | Street prices, NA-FC1 (€24.90) / NA-SEC1 (€9.90) | fetched |
| https://www.amazon.de/s?k=Noctua+NA-SAV3+anti-vibration | Street price, NA-SAV3 (€9.90) | fetched |

**Note on the NF-A4x10 5V URL:** `fans.md` records this page as successfully fetched, with a real
0.044 A (typ) / 0.05 A (max) current figure. `design/thermal-guidelines.md` (§8, same fetch date)
cites the *identical* URL as returning **HTTP 429** on every attempt, and falls back to an estimated
~120 mA instead. Same URL, contradictory fetch outcomes recorded in two different documents — see
`design/README.md` → "Known inconsistencies to resolve".

---

## From `components/fasteners-and-hardware.md`

| URL | Used for | Status |
|---|---|---|
| https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen | RX-M3x5.7 standard M3 insert: material, length, compatible plastics | fetched |
| https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck | RX-M3S short M3 insert (4.0mm length) | search result |
| https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-made-for-voron-rx-m3x5x4-messing-gewindebuchsen-fur-3d-druck | RX-M3x5x4 "Made for Voron" M3 insert variant | search result |
| https://www.ruthex.de/en/pages/faq | Checked for hole-size/temperature table | fetched (attempted) — did not contain the sought table |
| https://3ddruckboss.de/collections/ruthex-gewindeeinsatze | Community/retailer corroboration of 4.0mm hole sizing | search result |
| https://forum.drucktipps3d.de/forum/thread/26986-kernloch-einschmelzmuttern/ | Forum discussion of practical M3 insert hole sizing (4.0–4.4mm) | search result |
| https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong | 2026 pull-out force test (PLA), hole-diameter range, datasheet-accuracy conclusion | fetched |
| https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts | Soldering-iron temps (PLA/PETG/ABS), two-stage install method | fetched |
| https://tools.creative3dp.com/blog/heat-set-insert-hole-size-chart/ | Secondary per-material hole-diameter & install-temp cross-check table | fetched |
| https://facfox.com/docs/kb/mastering-heat-set-inserts-a-professionals-guide-to-durable-3d-printed-threads | Checked for a per-material table (none found); general wall/hole-depth rules | fetched |
| https://www.mcmaster.com/products/captive-panel-screws/ | Confirms McMaster-Carr stocks captive panel screws | search result — catalog not scrapeable for exact dims |
| https://www.mcmaster.com/products/knurled-head-thumb-screws | Confirms McMaster-Carr stocks knurled thumb screws | search result |
| https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/ | Cantilever snap-fit design rules (L/t ratio, fillet radius, clip width) | search result |
| https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/ | Snap-fit hook geometry, print orientation, worked example dims | fetched |
| https://southco.com/en_any_int/tl-40-113-07 | Southco TL-40 (medium) toggle draw latch product line | search result |
| https://southco.com/en_us_int/tl-20-201-07 | Southco TL-20 (small) toggle draw latch product line | search result |
| https://media.southco.com/media/static/Literature/tl.en.pdf | Southco TL draw latch datasheet (pull/holding-force, panel gap) | **UNPARSEABLE** (binary PDF) |
| https://www.amazon.com/CASE-CATCH-LATCH-TOGGLE-SQUARE/dp/B0848P2JWG | Generic 40mm×27mm toggle case latch (flight-case market) | search result |
| https://fayshing.com/product-category/latches/ | Generic flight-case latch/lock hardware category | search result |
| https://www.elesa.com/en/elesab2bstoreus/latches-us--1 | Elesa latches product family (no specific model datasheet found) | search result |
| https://southco.com/en_any_int/D2 | Dzus Rapier (D2) quarter-turn panel-thickness range, stud sizes | search result |
| https://southco.com/en_us_int/d2-517-1108-190 | Dzus quarter-turn stud example product | search result |
| https://en.wikipedia.org/wiki/Dzus_fastener | General Dzus fastener mechanism description | search result |
| https://www.first4magnets.com/product/6mm-dia-x-3mm-thick-n35-neodymium-magnet-089kg-pull-19521 | N35 6×3mm disc magnet, 0.89kg pull | **BLOCKED (403)** — spec confirmed via search index only |
| https://www.first4magnets.com/product/6mm-dia-x-3mm-thick-n42-neodymium-magnet-09kg-pull-19218 | N42 6×3mm disc magnet, 0.9kg pull | **BLOCKED (403)** |
| https://suprememagnets.com/products/neodymium-magnet-8x3mm-disc | N52 8×3mm disc magnet, ~1.76kg pull | fetched |
| https://radialmagnet.com/our-magnets/neodymium-magnet-disk-n35-8mm-x-3mma/ | Confirms N35 8×3mm disc exists (no pull force retrieved) | search result |
| https://www.thingiverse.com/thing:1215238 | 1.75mm filament as printed-hinge pin, design concept | search result |
| https://www.snapmaker.com/blog/3d-printed-hinges/ | Hinge pin/barrel clearance tolerance (0.2–0.3mm), orientation, failure modes | fetched |
| https://homediyer.com/products/black-rubber-feet-small-large-silicone-selfadhesicve-stick-on-pads-various-sizes | Self-adhesive rubber feet size range (4.5–179mm, 25 sizes) | search result |
| https://www.vital-parts.co.uk/self-adhesive-rubber-pads-10640-p.asp | Rubber/EPDM pad material options | search result |
| https://www.adsamm.com/84-x-anti-slip-pads-made-of-epdm-cellular-rubber-0-47-inch-12-mm-black-round-adhedsive-non-slip-rubber-pad-0-1-inch-2-5-mm-thickness.html | Specific EPDM anti-slip pad example (12mm × 2.5mm) | search result |
| https://www.printables.com/model/369017-corner-bumper-tpu-optimized | CNC Kitchen TPU corner bumper design (screw + glue mounting) | search result |
| https://blog.uavmodel.com/3d-printing-tpu-parts-for-fpv-drones-bumpers-mounts-and-antenna-holders/ | General TPU bumper mounting practices (screw sizing, adhesives, interference fit) | search result |
| https://www.neutrik.com/en/neutrik/products/xlr-connectors/xlr-chassis-connectors/d-series | D-series panel cutout spec (M3 countersunk, 1–3mm panel thickness), PCB-mount screw spec | fetched |
| https://www.neutrik.com/en/product/mfd | MFD M3 fixing plate accessory for D-series connectors | search result |
| https://www.neutrik.com/en/product/mfd.pdf | MFD datasheet PDF | **UNPARSEABLE** (binary PDF) |
| https://www.designacable.com/black-m3x12mm-long-screw-nut-neutrik-d-type-chassis-panel-mount.html | Third-party M3×12mm screw/nut kit for Neutrik D-type panel mounting | search result |
| https://www.hellermanntyton.us/cable-ties/ | Cable tie width/length class overview | search result |
| https://www.fibrestrap.com/zip-tie-sizes | Cable tie size range cross-check | search result |
| https://www.3m.com/3M/en_US/p/d/b00034736/ | 3M adhesive cable-tie mounting base product family | search result |
| https://www.amazon.com/Adhesive-Cable-Mounts-Holders-19-5mm/dp/B07F7Y9KGX | Example adhesive cable-tie mount base (19.5×19.5mm) | search result |

---

## From `components/cables.md`

| URL | Used for | Status |
|---|---|---|
| https://avlgear.com/products/belden-4694r-12g-sdi-75-ohm-4k-uhd-rg-6-coax-video-cable-18-awg-black-1000-feet | Belden 4694R min bend radius (69.9mm), OD | fetched |
| https://avlgear.com/products/belden-4855r-12g-sdi-75-ohm-4k-uhd-mini-rg-59-coax-video-cable-black-1000-feet | Belden 4855R min bend radius (40.6mm), OD | fetched |
| https://catalog.belden.com/techdata/EN/4694R_techdata.pdf | Belden 4694R full technical datasheet | **UNPARSEABLE** (binary PDF) |
| https://catalog.belden.com/techdata/EN/4855R_techdata.pdf | Belden 4855R full technical datasheet | **UNPARSEABLE** (binary PDF) |
| https://www.belden.com/products/cable/video-cable/coaxial-video-cable/4694r | Belden 4694R product page | **BLOCKED (403)** |
| https://www.belden.com/products/cable/broadcast-cable/sdi-video-coax-cable/4855r | Belden 4855R product page | **BLOCKED (403)** |
| https://www.accio.com/plp/rj45-plug-dimensions | IEC 60603-7 / TIA-568.2-D RJ45 plug length (18.5–21.5mm), housing width | fetched |
| https://store.cablesplususa.com/ultra-slim-cat6-ethernet-patch-cable-stranded-32awg-utp-bare-copper-black-jacket-ultra-short-molded-boot/ | "Ultra Short" flush-boot Cat6 patch cable, OD, lengths | fetched |
| https://www.fs.com/eu-en/products/66742.html | 0.15m Cat6 slim patch cable product example | search result — direct fetch returned no content |
| https://www.monoprice.com/product?p_id=13510 | SlimRun Cat6, 28 AWG, 6in patch cable | **BLOCKED (403)** |
| https://www.zion-communication.com/Patch-Cord-Boot-Types-Explained-Snagless-Slim-Short-and-Molded-Boots-id05104255.html | Qualitative boot-type description (snagless/slim/short/molded) — no mm figures | fetched |
| https://www.neutrik.com/en/product/ne8mc-b | NE8MC-B etherCON mechanical specs (cable OD, insertion force, cycles, temp) | fetched |
| https://www.neutrik.com/media/8070/download/ethercon-cable-connector-ne8mc.pdf?v=1 | etherCON NE8MC dimensioned datasheet | **UNPARSEABLE** (binary PDF) |
| https://www.designacable.com/screened-cat5e-ethercon-lead-flexible-van-damme-cable-neutrik-rj45-cabling.html | Van Damme Tourcat etherCON lead product example | search result |
| https://www.comms-express.com/categories/cat5e-rj45-neutrik-ethercon-shielded-patch-leads-cables/ | Cat5e etherCON shielded patch leads category | search result |
| https://www.thomann.co.uk/sommer_cable_cat_6a_cable_1m_rj45_rj45.htm | Sommer Cable Cat6a RJ45 lead (shortest found: 1m) | search result |
| https://en.wikipedia.org/wiki/HDMI | HDMI Type A connector cross-section (13.9×4.45mm plug) | fetched |
| https://www.cablematters.com/pc-484-141-combo-pack-270-degree-and-90-degree-right-angle-hdmi-adapter.aspx | Right-angle HDMI adapter added-depth figure ("<1 inch") | fetched |
| https://www.cablestogo.com/audio-video/adapters-and-couplers/right-angle-hdmi-adapter-right-exit/p/cg-43290 | Right-angle HDMI adapter (right-exit) example | fetched — redirected page had no dimension content |
| https://www.amazon.com/Degree-Adapter-Support-YOUCHENG-Raspberry/dp/B08QCPPF8P | Illustrative short mini-HDMI right-angle cable (not full-size) | search result |
| https://en.wikipedia.org/wiki/BNC_connector | BNC male plug OD (14.5mm); no axial length figure | fetched |
| https://www.amphenolrf.com/rf-connectors/bnc-connectors.html | BNC connector dimensions | **BLOCKED (403)** |
| https://www.l-com.com/coaxial-12g-sdi-connectors | 12G SDI connectors category | fetched (attempted) — no per-product dimension data |
| https://customcableconnection.com/products/hd-sdi-mini-rg59-bnc-extension-cables-12g-rated | Shortest available 12G-SDI BNC lead (6in, Belden 4855R) | fetched |
| https://smallhd.com/products/12-inch-thin-sdi-cable | Thin/short SDI cable product example | search result |
| https://www.accesscomms.com.au/usb-connector-dimensions/ | USB Type-A plug body length (~12mm) | fetched |
| https://www.amazon.com/MyCableMart-Certified-480Mbps-Beige-Cable/dp/B010RH9AL0 | USB 2.0 A-to-A, 6in cable example | search result |
| https://www.showmecables.com/usb-2-0-a-male-to-b-male-0-5-ft | USB 2.0 A-to-B, 0.5ft cable example | search result |
| https://www.adafruit.com/product/3310 | 5.5×2.1mm DC barrel plug overall length (33.7mm), shell dia. | fetched |
| https://www.adafruit.com/product/5607 | 30cm DC barrel jack extension cable, panel-mount, example | search result |
| https://thepihut.com/products/round-panel-mount-5-5mm-2-1mm-dc-barrel-jack-extension-cable-30cm-long | Mirror of the Adafruit #5607 listing | search result |
| https://www.amazon.com/Fotodiox-Adapter-Female-Barrel-inches/dp/B075G32DVQ | XLR4-female to 2.1mm DC barrel adapter example | fetched — only page title returned, no body spec content |
| https://www.bhphotovideo.com/c/product/1457759-REG/bescor_xlrmpp_10_4_pin_xlr_male.html | XLR4-male to DC barrel power cable example | search result |
| https://www.bhphotovideo.com/c/product/1100264-REG/lanparte_dc_4pxlr_4_pin_xlr_female_dc.html | XLR4-female DC power adapter cable example | search result |
| https://www.neutrik.com/en/product/nc4mxx | NC4MXX (4-pin XLR) mechanical/electrical specs; no length figure | fetched |
| https://www.mouser.com/datasheet/2/289/Product_Guide_-_Section_XLR-938291.pdf | Neutrik XLR product guide PDF | referenced only, not fetched |
| https://www.switchcraft.com/catalog/jacks-and-plugs/audio-jacks-and-plugs/3-5-mm-jacks-and-plugs/ | 3.5mm jacks/plugs category | fetched (attempted) — page returned no content |
| https://www.bhphotovideo.com/c/product/929574-REG/switchcraft_35hdbau_3_5mm_stereo_plug_0_290.html | Switchcraft 35HDBAU 3.5mm TRS plug | **BLOCKED (403)** |
| https://www.amazon.com/3-5mm-Kework-2-pack-Stereo-Headphone/dp/B07D1Z6XXZ | 15cm 3.5mm TRS extension lead example | search result |
| https://www.amazon.com/Cable-Matters-3-5mm-Adapter-Breakout/dp/B0CBHPZYZ7 | Cable Matters 3.5mm TRS breakout cable (3ft, not ultra-short) | search result |

---

## From `design/fdm-rugged-enclosure-guidelines.md`

| URL | Used for | Status |
|---|---|---|
| https://www.cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament | PLA/PETG/ASA impact strength, stiffness, temperature-failure figures | fetched |
| https://help.prusa3d.com/article/petg_2059 | PETG nozzle/bed temps, warping, mechanical notes | fetched |
| https://help.prusa3d.com/article/asa_1809 | ASA nozzle/bed temps, enclosure requirement, warping, UV resistance | fetched |
| https://help.prusa3d.com/article/enclosure-guidepost_366332 | Which materials need a printer enclosure | search result |
| https://www.rapiddirect.com/blog/3d-printing-wall-thickness/ | Wall thickness and perimeter guidance for rugged parts | search result |
| https://xometry.pro/en/topic/recommended-wall-thickness-for-fdm/ | Structural wall-thickness minimums | search result |
| https://www.printedsolid.com/blogs/news/37036739-3d-printing-design-tips-part-1-stress-concentrations | Why sharp corners are stress concentrators | search result |
| https://www.fictiv.com/articles/fillets-when-to-use-em-when-to-lose-em | Fillet radius sizing rules, fillet vs. chamfer | search result |
| https://www.luisllamas.es/en/3d-printing-ribs-stiffness/ | Rib thickness/height ratios | search result |
| https://www.fictiv.com/articles/best-practices-for-adding-ribs-and-gussets-to-3d-printed-parts-for-structural-integrity | Rib/gusset sizing, warping mitigation | search result |
| https://link.springer.com/article/10.1007/s12206-017-0415-7 | Print-orientation effect on adhesively bonded lap-joint strength | search result |
| https://insertguide.com/why-do-bosses-crack-around-heat-set-inserts/ | Heat-set insert boss wall thickness / OD guidelines, crack causes | **BLOCKED (403)** — cited via search-result summary only |
| https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/ | Living-hinge material choice (PP for injection molding, Nylon12/TPU for FDM), thickness | fetched |
| https://designmycase.co.uk/bumper-cases | Bumper/crumple-zone drop-protection design principle | search result |
| https://learn.adafruit.com/iphone-x-ninjaflex-pla-bumper-case/3d-printing | TPU+PLA bumper case worked example | search result |
| https://www.neutrik.com/en/neutrik/products/xlr-connectors/xlr-chassis-connectors/emc-series | Neutrik EMC-series shielded connector purpose | search result |
| https://www.neutrik.com/en/product/nc3fdx-emc-spec | EMC shield-continuity mechanism (capacitor/ferrite) | search result |
| https://benchmarkmedia.com/blogs/application_notes/grounding-xlr-connectors-neutrik-usa | Chassis/shell/shield common-ground best practice | search result |
| https://resources.system-analysis.cadence.com/blog/all-things-connectors-part-5-shielded-connectors | Floating-ground-in-plastic-enclosure note, shield-bonding recommendation | search result |
| https://business.pelican.com/us/en/capabilities/certifications-testing-cases | Pelican-style 26-drop/3-temperature test protocol | **BLOCKED (403)** — cited via search-result summary only |

**Search-aggregation-only citations** (no single fetchable URL — WebSearch results across multiple
domains, listed in the source document's own Sources section but not individually fetched):
material property/pricing comparisons (PC-CF, PA-CF, PETG-CF, ABS, TPU pricing and UV-resistance
figures — domains include bambulab.com, numakers.com, 3dxtech.com, wevolver.com, spoolhound.com,
and others), FDM tolerance/overhang/bridging rules (zbotic.in, snapmaker.com, layerx3d.in, and
others), TPU corner-bumper/AMS tradeoffs (thangs.com, forum.bambulab.com, 3dprintdecoded.com), lid
design (zbotic.in, formlabs.com, facfox.com), PETG living-hinge failure data (fastpreci.com,
community.ultimaker.com), and ventilation chimney-effect guidance (mpvent.com, fanacdc.com,
acdcecfan.com). See the source document's own Sources section for the full domain list per topic.

---

## From `design/thermal-guidelines.md`

| URL | Used for | Status |
|---|---|---|
| https://en.wikipedia.org/wiki/Acrylonitrile_butadiene_styrene | ABS thermal conductivity (0.1 W/m·K) | fetched |
| https://engineerexcel.com/thermal-conductivity-plastic/ | ABS conductivity range (0.15–0.21 W/m·K); aluminum conductivity (~204 W/m·K) | fetched |
| https://devel.lulzbot.com/filament/Rigid_Ink/PETG%20DATA%20SHEET.pdf | PETG thermal conductivity, 0.21 W/m·K (ASTM C177) | fetched |
| https://www.wevolver.com/article/petg-temperature-resistance-heat-limits-and-practical-insights-for-engineers | PETG conductivity range ~0.1–0.2 W/m·K | fetched |
| https://www.makeitfrom.com/material-properties/Acrylonitrile-Styrene-Acrylate-ASA | ASA thermal conductivity, 0.18 W/m·K | fetched |
| https://cdn.shopify.com/s/files/1/0919/6571/8867/files/purefil_ASA_Material_data_sheet.pdf | Confirms ASA TDS format has a conductivity field — value blank on this sheet | fetched |
| https://designerdata.nl/materials/plastics/thermo-plastics/polycarbonate | PC thermal conductivity, 0.2025 W/m·K | fetched |
| https://leipole.com.sg/technical-articles/how-to-calculate-enclosure-heat-transfer-load-accurately/ | Natural-convection h values (still air 1.6, light air 2.5, forced 6.0+ W/m²K) | fetched |
| https://www.electronics-cooling.com/2001/08/simplified-formula-for-estimating-natural-convection-heat-transfer-coefficient-on-a-flat-plate/ | Flat-plate h = C(ΔT/L)^0.25 formula and orientation constants | fetched |
| https://www.eng-tips.com/threads/rule-of-thumb-equations-for-convective-cooling-of-metal-surfaces.362994/ | "5–10 W/m²K" electronics-box convection rule of thumb | **BLOCKED (403)** — indexed snippet only, archive.org mirror also unreachable |
| https://fanacdc.com/enclosure-ventilation/ | CFM sizing formula (3.16×P/ΔT), chimney-effect placement, filter overview | fetched |
| https://blog.airlinehyd.com/ventilation-when-its-required | Corroborating CFM formula, 20–30% safety margin guidance | fetched |
| https://www.acdcecfan.com/enclosure-ventilation-for-electronics/ | Corroborating CFM formula (3.17×P/ΔT), "Bottom-In, Top-Out" rule, filter-on-inlet guidance | fetched |
| https://orionfans.com/pq-curve/ | Static-pressure/backpressure derating (PQ curve) concept | fetched |
| https://industrialmonitordirect.com/blogs/knowledgebase/calculating-resistor-wattage-for-dc-fan-speed-control-circuits | Why a fixed resistor is unsuitable for fan speed control | fetched |
| https://ipxchange.tech/industry-insights/low-power/ldo-vs-buck/ | LDO vs. buck-converter efficiency crossover point (~100µA); buck up to 95% efficient | fetched |
| https://www.hearingconservation.org/assets/Decibel.pdf | Reference ambient noise levels (library 30dB, conversation 60–70dB, concert 115dB) | fetched |
| https://thrillzing.com/music-venues/concert-decibel-levels/ | Venue-specific concert SPL ranges (clubs/theaters/arenas/stadiums) | fetched |
| https://www.quietpc.com/nf-a4x10 | NF-A4x10 FLX specs (4500 RPM, 4.8 CFM, 17.9 dB(A)) | fetched |
| https://www.quietpc.com/nf-a4x20-flx | NF-A4x20 FLX specs (5000 RPM, 5.5 CFM, 14.9 dB(A)) | fetched |
| https://www.quietpc.com/nf-a6x25 | NF-A6x25 FLX specs (3000 RPM, 17.2 CFM, 19.3 dB(A)) | fetched |
| https://www.quietpcusa.com/Noctua-NF-A8-ULN-Quiet-Computer-Fan-80mm | NF-A8 ULN specs (1400 RPM, 34.8 m³/h, 10.4 dB(A)) | fetched |
| https://www.coolerguys.com/products/noctua-nf-a8-pwm-fan-80x25mm-12v-4-pin | NF-A8 PWM specs (2200 RPM, 55.5 m³/h, 17.7 dB(A)) | fetched |
| https://en.wikipedia.org/wiki/USB_3.0 | USB 2.0 (500mA) / USB 3.0 (900mA) current budgets per USB-IF spec | fetched |
| https://www.noctua.at/en/products/nf-a4x10-5v/specifications | Confirms NF-A4x10 5V SKU exists; specific 5V current NOT retrieved | **BLOCKED (429)** *(contradicts fans.md, which records this same URL as successfully fetched — see note above)* |
| https://tripplite.eaton.com/poe-to-usb-micro-b-rj45-active-splitter-802af-48v-to-5v-1a-raspberry-pi-up-to-328ft-100m~NPOESPLG5VMU | Confirmed real PoE-to-5V/1A-USB splitter product (NPOE-SPL-G-5VMU) | fetched |

---

## Blocked / unparseable sources — quick index

| URL | Document | Failure |
|---|---|---|
| media.southco.com/media/static/Literature/tl.en.pdf | fasteners-and-hardware.md | UNPARSEABLE (binary PDF) |
| neutrik.com/en/product/mfd.pdf | fasteners-and-hardware.md | UNPARSEABLE (binary PDF) |
| first4magnets.com (N35 6×3mm) | fasteners-and-hardware.md | BLOCKED (403) |
| first4magnets.com (N42 6×3mm) | fasteners-and-hardware.md | BLOCKED (403) |
| catalog.belden.com (4694R techdata PDF) | cables.md | UNPARSEABLE (binary PDF) |
| catalog.belden.com (4855R techdata PDF) | cables.md | UNPARSEABLE (binary PDF) |
| belden.com (4694R product page) | cables.md | BLOCKED (403) |
| belden.com (4855R product page) | cables.md | BLOCKED (403) |
| monoprice.com (#13510) | cables.md | BLOCKED (403) |
| neutrik.com (etherCON NE8MC PDF) | cables.md | UNPARSEABLE (binary PDF) |
| amphenolrf.com (BNC connectors) | cables.md | BLOCKED (403) |
| bhphotovideo.com (Switchcraft 35HDBAU) | cables.md | BLOCKED (403) |
| insertguide.com (heat-set insert boss article) | fdm-rugged-enclosure-guidelines.md | BLOCKED (403) |
| business.pelican.com (certifications-testing-cases) | fdm-rugged-enclosure-guidelines.md | BLOCKED (403) |
| eng-tips.com (convective-cooling rule-of-thumb thread) | thermal-guidelines.md | BLOCKED (403) |
| noctua.at/en/products/nf-a4x10-5v/specifications | thermal-guidelines.md | BLOCKED (429) — *see contradiction note above* |
