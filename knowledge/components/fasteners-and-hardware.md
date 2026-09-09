# Fasteners and Hardware

Component knowledge base entry for fasteners, inserts, latches, and small hardware relevant to
FDM-printed rugged cases for Magewell Pro Convert NDI converters. All figures below are sourced
from vendor pages, datasheets, or published test articles fetched on **2026-09-07**. Anything that
could not be verified from an actual source is explicitly marked `unknown` rather than guessed.

---

## 1. M3 Heat-Set Inserts

**Which figure this project uses (added 2026-09-08):** this file carries two disagreeing hole-
diameter figures for M3 inserts — the ~4.0 mm nominal figure in §1.1 (Ruthex/community consensus)
and the 4.24–4.30 mm per-material CAD-pocket chart in §1.3 (tools.creative3dp.com) — and does not
pick a winner between them; neither is dropped, since they come from different, non-comparable
source families (a single nominal community figure vs. a third-party per-material shrink-compensated
pocket chart). For this project specifically:

- The **library default** is `MCC_INSERT_M3.hole_d = 4.0` (mm), defined in `lib/mcc/constants.scad`
  — i.e. the code currently follows the §1.1 nominal figure, not the §1.3 chart.
- The **`insert-boss` coupon** (`models/coupons/insert-boss.scad`) is the mechanism that actually
  decides the calibrated value for this printer/material combination: it prints a ladder of bosses
  at bore diameters 3.8/3.9/4.0/4.1/4.2/4.3 mm (bracketing both the §1.1 nominal figure and the
  §1.3 ASA/ABS column) so the real hole-shrinkage-compensated diameter for ASA can be measured
  directly, per the "print a hole-diameter test coupon" guidance already given below, rather than
  trusting either sourced number blindly. Update `MCC_INSERT_M3.hole_d` from the coupon's measured
  result once printed — do not silently switch to the §1.3 chart's 4.29 mm ASA/ABS figure without a
  physical measurement backing it.

### 1.1 Ruthex product line (primary reference brand)

| Item | Value | Source |
|---|---|---|
| Insert material | Lead-free brass, spiral/opposite-knurl geometry (Ruthex claims to have introduced this knurl geometry to the 3D-printing market in 2018) | [ruthex.de M3 product page](https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen) |
| Standard M3 insert | RX-M3x5.7 — length **5.7 mm** | [ruthex.de M3 product page](https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen) |
| Short M3 insert | RX-M3S / RX-M3x4.0 — length **4.0 mm** | product listing: [ruthex M3S short insert](https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck) |
| "Made for Voron" M3 variant | RX-M3x5x4 (5 mm OD stepped / 4 mm) | product listing: [ruthex Voron M3 insert](https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-made-for-voron-rx-m3x5x4-messing-gewindebuchsen-fur-3d-druck) |
| Long M3 insert | Not confirmed on ruthex.de as a distinct catalog SKU beyond the above | `unknown` |
| Stated compatible materials | PLA, PETG, ABS, PP (installable with soldering iron or ultrasonic inserter, blind or through holes) | [ruthex.de M3 product page](https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen) |
| Recommended print/drill hole diameter, M3 | **4.0 mm nominal** (community and forum consensus around Ruthex parts converges on 4.0 mm as the printed/drilled hole target, with users noting 4.0 mm can be tight to insert and ~4.1 mm is a more forgiving practical size at 4.4 mm inserts begin to sit loose) | search-indexed content from ruthex retailer/community pages, e.g. [3ddruckboss.de Ruthex collection](https://3ddruckboss.de/collections/ruthex-gewindeeinsatze), [drucktipps3d.de forum thread on insert hole sizing](https://forum.drucktipps3d.de/forum/thread/26986-kernloch-einschmelzmuttern/) — **not a formal Ruthex datasheet table**, treat as corroborated community figure rather than a hard spec |
| Ruthex per-material (PLA vs PETG vs ASA vs PC) hole diameter table | Ruthex does **not** publish a separate hole-diameter figure per material on its product pages; the single 4.0 mm nominal is used across materials | `unknown` — no Ruthex-published per-material table found |

**Important caveat on the 4.0 mm figure:** CNC Kitchen's insert testing (see 1.2) explicitly found that printed
holes come out **undersized relative to CAD** by a printer/process-dependent amount (~0.2–0.3 mm in their
2026 test), which is why "4.0 mm hole" in a datasheet and "4.0 mm in your CAD model" do not give the same
physical result. Always print a hole-diameter test coupon for your specific printer/material combo rather than
trusting a single nominal number blindly.

### 1.2 CNC Kitchen testing / cross-check

| Finding | Detail | Source |
|---|---|---|
| Article | "Are Our Heat-Set Insert Datasheets Wrong?" (2026) | [cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong) |
| Hole diameters tested | 3.6 mm – 4.6 mm (M3 inserts) | same |
| Test material | Polymaker PolySonic PLA, printed on a Bambu/Creality-class "CORE One" printer — **this test was run on PLA, not PETG/ASA/PC**, so the absolute pull-out force numbers below should not be assumed to transfer directly to those materials | same |
| Peak pull-out force (tightest holes) | ≈ 1,400 N (≈ 150 kgf / 325 lbf) | same |
| Pull-out force at 4.2 mm CAD hole (typical as-printed result) | ≈ 90% of maximum measured strength | same |
| Conclusion on datasheets | Author kept the 4.0 mm nominal recommendation but advises adding ~0.2–0.3 mm to the CAD hole diameter to compensate for hole shrinkage, since "every printer and material shrinks holes differently" | same |
| Numeric pull-out force specifically for PETG, ASA, or PC | `unknown` — CNC Kitchen's published *written* test article covers PLA only; no written (non-video) CNC Kitchen article with PETG/ASA/PC pull-out numbers was found | — |

| Installation guidance (CNC Kitchen "Tips & Tricks" article) | Detail | Source |
|---|---|---|
| Soldering iron temperature rule of thumb | ~10–20 °C above the material's normal print/nozzle temperature | [cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts) |
| PLA | ~225 °C | same |
| PETG | ~245 °C | same |
| ABS | ~265 °C | same |
| ASA / PC | `unknown` from this specific CNC Kitchen article (not stated) — see secondary cross-check table below | — |
| Two-stage installation method | (1) Melt the insert ~90% of the way in with the iron tip; (2) seat the final stretch with a screwdriver/tweezers and hold a few seconds until the plastic re-solidifies, to stop the insert creeping back out | same |

### 1.3 Secondary cross-check: per-material hole size & temperature chart

Because neither Ruthex nor CNC Kitchen publish a single table covering PLA/PETG/ABS/ASA/PC side by side, the
table below (a secondary, non-Ruthex/non-CNC-Kitchen source) is included for cross-reference only. Treat it as
indicative, not authoritative for this project's hardware BOM.

| Insert size | PLA (CAD pocket) | PETG | ABS/ASA | Nylon (PA) | PC |
|---|---|---|---|---|---|
| M3 | 4.24 mm | 4.26 mm | 4.29 mm | 4.30 mm | 4.29 mm |
| M4 | 5.83 mm | 5.86 mm | 5.91 mm | 5.93 mm | 5.91 mm |
| M5 | 6.63 mm | 6.67 mm | 6.74 mm | 6.77 mm | 6.74 mm |
| M6 | 8.23 mm | 8.28 mm | 8.36 mm | 8.40 mm | 8.36 mm |

Source: [tools.creative3dp.com heat-set insert hole size chart](https://tools.creative3dp.com/blog/heat-set-insert-hole-size-chart/)
— note the chart's own commentary that "the variation between materials at the same insert size is small
(0.05–0.10 mm)" because print-process shrinkage dominates over material-specific shrinkage.

| Material | Soldering iron install temperature |
|---|---|
| PLA | 220–240 °C |
| PETG | 230–250 °C |
| ABS / ASA | 250–270 °C |
| Nylon (PA) | 280 °C |
| Polycarbonate | 290–310 °C |

Source: same [creative3dp hole-size chart article](https://tools.creative3dp.com/blog/heat-set-insert-hole-size-chart/).
These ASA/PC numbers are **not corroborated by Ruthex or CNC Kitchen** directly — use as a starting point and
verify against your own iron/insert combination.

### 1.4 Installation method summary (for this project)

1. Print the hole ~0.2–0.3 mm undersized versus the insert's nominal OD to allow for hole shrinkage (verify with
   a printed test coupon per material/printer).
2. Set soldering iron temperature 10–20 °C above the filament's normal print temperature (see tables above).
3. Melt the insert in roughly 90% of the way, then seat the last stretch with light hand pressure (screwdriver
   shaft, tweezers) and hold until the plastic re-solidifies, per CNC Kitchen's two-stage method.
4. Let the part cool undisturbed before threading a screw in.

---

## 2. Screws and Captive Fasteners

| Fastener type | Typical use case in case work | Common lengths | Notes / sourcing |
|---|---|---|---|
| M3 pan/socket-head machine screw | Lid-to-body fastening into heat-set inserts | 6–20 mm (varies with wall + insert length) | Generic hardware; widely stocked (McMaster-Carr, Bossard, AliExpress-class generic listings) |
| M3 knurled thumb screw | Tool-less panel access (battery covers, cable panels) where a screwdriver shouldn't be required | Panel-dependent; typically 6–16 mm usable grip length | McMaster-Carr stocks "Knurled Head Thumb Screws" and "Knurled Head Thumb Bolts" as named product lines — see [mcmaster.com Knurled Head Thumb Screws](https://www.mcmaster.com/products/knurled-head-thumb-screws) (specific catalog lengths/prices could not be scraped from the JS-rendered catalog page — `unknown` numeric list; consult catalog directly) |
| M3 captive panel screw | Removable panels where the screw must stay attached to the panel (no drop risk when opening a case in the field) | Panel-dependent | McMaster-Carr carries a dedicated "Captive Panel Screws" family (slotted, hex-socket, and other drive styles) — see [mcmaster.com Captive Panel Screws](https://www.mcmaster.com/products/captive-panel-screws/); exact stocked lengths `unknown` (catalog not scrapeable via automated fetch) |
| M2.5 machine screw | Lighter-duty alternative to M3 for small brackets, PCB/connector retention, or weight-sensitive sub-assemblies | 4–12 mm | Generically described in electronics-hardware guides as suited to "laptop chassis and small consumer electronics" work where M3 is unnecessarily heavy; source is general secondary guidance, not a single authoritative datasheet — treat as directional only |
| Generic AliExpress-class listings | Both M3 thumbscrews and captive screws are sold in bulk by generic Chinese hardware sellers | Varies | Confirmed to exist as a sourcing channel via search (e.g. AliExpress wiki/spec-comparison content), but per-listing pricing/exact dimensions were not fetched — treat AliExpress as a real but unverified-per-listing source |

**Sourcing channels identified (existence confirmed, not all dimensions/prices verified):**
- McMaster-Carr (US) — [mcmaster.com/products/captive-panel-screws](https://www.mcmaster.com/products/captive-panel-screws/), [mcmaster.com/products/knurled-head-thumb-screws](https://www.mcmaster.com/products/knurled-head-thumb-screws)
- Bossard (EU industrial fastener distributor) — known supplier of captive/panel fasteners; no specific product page was fetched for this document, so treat as a sourcing lead only (`unknown` specifics)
- Generic AliExpress-class marketplace listings — exist for both M3 thumbscrews and captive panel screws, exact specs/pricing per listing not verified here

---

## 3. Quick-Open Mechanisms

### 3.1 Printed snap-fit latches (design guidance, not hardware)

| Design parameter | Guidance | Source |
|---|---|---|
| Cantilever length-to-thickness ratio | Start around L/t ≥ 8:1 for a flexible cantilever snap arm | [Hubs/Protolabs Network — how to design snap-fit joints for 3D printing](https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/) |
| Root fillet | Radius ≥ 0.5× the cantilever's base thickness, to spread stress and avoid a stress-riser crack point | same |
| Minimum clip width | ~5 mm | same |
| Engagement/protrusion depth | ≥ ~2 mm for a secure catch (increase for a "tighter" retention feel) | same |
| Print orientation | Orient the flexing arm so bending occurs **parallel to layer lines**, not across them (avoid printing the cantilever so it flexes in the Z/layer direction, which is the weak axis for FDM parts) | same; also see [Formlabs — designing 3D-printed snap-fit enclosures](https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/) |
| Hook shape | Taper the hook / use a trapezoidal profile rather than a rectangular one; use curved (not sharply filleted) transitions at the hook edge | [Formlabs snap-fit enclosure guide](https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/) |
| Example case-study dimensions | Formlabs' own worked example used a 20 mm cantilever length with 1.2 mm engagement depth — presented as one example, not a universal number | same |
| Assembly-only vs. permanently-loaded arms | Cantilever should flex during assembly/disassembly only, not remain under sustained deflection load in service (creep risk in FDM plastics, worse in PETG/ASA than PLA) | Hubs/Protolabs guide (general engineering consensus) |

These are general design rules, not code — apply them per-latch during CAD design rather than treating any one
number as fixed.

### 3.2 Small cam/toggle draw latches

| Item | Detail | Source |
|---|---|---|
| Southco TL series (Toggle Style Draw Latch) | "TL-20" = small size, "TL-40" = medium size — the "20"/"40" is a Southco size code, **not** a millimeter dimension | [southco.com TL-40-113-07 product page](https://southco.com/en_any_int/tl-40-113-07), [TL-20-201-07](https://southco.com/en_us_int/tl-20-201-07) |
| Southco TL series mount options | Exposed mount and concealed mount variants; stainless steel (passivated) or zinc-plated steel finishes | same product family pages |
| Southco TL datasheet | Exists at [media.southco.com/media/static/Literature/tl.en.pdf](https://media.southco.com/media/static/Literature/tl.en.pdf) but is a binary/compressed PDF that could not be parsed by the fetch tool used for this research; numeric pull/holding-force and panel-gap figures from it are `unknown` for this document — consult the PDF directly | attempted fetch, unreadable |
| Generic "40mm" toggle draw latches (flight-case/toolbox market) | A distinct product category from Southco's "TL-40" size code — generic catch/latch hardware advertised around **40mm × 27mm** overall footprint is sold for toolboxes, flight cases, and trunks | e.g. [Amazon: CASE Catch Clip Over Latch Toggle Type Square 40MM x 27MM](https://www.amazon.com/CASE-CATCH-LATCH-TOGGLE-SQUARE/dp/B0848P2JWG), [Fayshing flight-case latch category](https://fayshing.com/product-category/latches/) |
| Pull force for generic 40mm toggle latches | `unknown` — no fetched listing included a load-tested pull-force spec | — |
| Elesa toggle latches | Elesa/Elesa+Ganter sell a "Latches" and "Toggle latches" product family, but a specific model (e.g. "C220") datasheet with pull-force spec was not locatable via search | [elesa.com Latches category](https://www.elesa.com/en/elesab2bstoreus/latches-us--1) — figures `unknown` |

### 3.3 Quarter-turn fasteners (Dzus / Camloc style)

| Item | Detail | Source |
|---|---|---|
| Southco D2 — Dzus Rapier quarter-turn fastener | Accommodates total material (panel stack) thickness from **0.5 mm to 30.4 mm** | [southco.com D2 Dzus Rapier product family page](https://southco.com/en_any_int/D2) |
| Stud sizes available | 3.5 mm, 5 mm, 7 mm, 9 mm | same |
| Mechanism | Spring-loaded stud (diamond-shaped base plate, riveted to the outer panel) engages a spring receptacle riveted to the inner panel/bracket; a quarter turn locks the stud into the receptacle | same; general description corroborated by [Wikipedia — Dzus fastener](https://en.wikipedia.org/wiki/Dzus_fastener) |
| Camloc | Camloc's quarter-turn range (e.g. its 2600 series) is described as functionally very similar to Dzus/Panex fasteners and is commonly used interchangeably in the same applications | secondary sourcing (search-indexed comparison content); no Camloc datasheet was fetched directly — treat panel-thickness figures for Camloc specifically as `unknown` |
| Turn mechanism | Quarter-turn (90°) slotted, Phillips, or hex-drive stud head, depending on variant | Southco D2 family pages, e.g. [D2-517-1108-190](https://southco.com/en_us_int/d2-517-1108-190) |

### 3.4 Magnets (neodymium disc, N35 vs N52)

| Size | Grade | Pull force | Source |
|---|---|---|---|
| 6 mm dia × 3 mm thick | N35 | **0.89 kg** | [first4magnets.com — 6mm dia x 3mm thick N35, 0.89kg Pull](https://www.first4magnets.com/product/6mm-dia-x-3mm-thick-n35-neodymium-magnet-089kg-pull-19521) |
| 6 mm dia × 3 mm thick | N42 | **0.9 kg** | [first4magnets.com — 6mm dia x 3mm thick N42, 0.9kg Pull](https://www.first4magnets.com/product/6mm-dia-x-3mm-thick-n42-neodymium-magnet-09kg-pull-19218) |
| 6 mm dia × 3 mm thick | N52 | `unknown` — no first4magnets/K&J/supermagnete listing for this exact size+grade combination was found via search | — |
| 8 mm dia × 3 mm thick | N35 | `unknown` — product exists (e.g. Radial Magnets catalog entry) but a pull-force figure was not retrieved from a fetched source | product existence: [radialmagnet.com Neodymium Magnet Disk N35 8mm x 3mm](https://radialmagnet.com/our-magnets/neodymium-magnet-disk-n35-8mm-x-3mma/) |
| 8 mm dia × 3 mm thick | N52 | **≈1.76 kg** (≈3.89 lb) | [suprememagnets.com — N52 Neodymium magnet disc 8mm OD x 3mm](https://suprememagnets.com/products/neodymium-magnet-8x3mm-disc) |

Note: figures are the vendor's own quoted "pull force" (to a flush mild-steel plate), which is a standard but
somewhat idealized test condition — real-world holding force through a printed PETG/ASA wall plus paint/finish
will be lower. N52 is the strongest common commercial neodymium grade and will out-pull N35 by roughly 40–50%
at the same physical size, consistent with the 6×3 mm N35→N42 step above (~0.89→0.9 kg) and the general
industry-known N35→N52 strength gap; however, no single vendor supplied a matched N35-vs-N52 pair at exactly
the same size to quote a precise same-size ratio, so treat "40–50% stronger" as a general rule of thumb, not a
sourced figure for this specific size.

### 3.5 Printed hinges with a steel/filament pin

| Item | Detail | Source |
|---|---|---|
| 1.75 mm filament as hinge pin | Common maker technique: print interlocking knuckle halves, then push a length of raw 1.75 mm filament through as the pin — no screws or glue needed | [Thingiverse — "Redesigned panel hinge uses 1.75mm filament as hinge pin"](https://www.thingiverse.com/thing:1215238) |
| 3 mm steel rod as hinge pin | Alternative for higher load-bearing hinges (heavier lid, repeated open/close cycles); steel rod offers higher shear strength than a printed or filament pin but requires the knuckle bore to be sized for a metal rod rather than filament | general design pattern noted across multiple maker hinge guides; no single fetched source gives a steel-rod-specific tolerance table — cross-reference general FDM clearance guidance below |
| Knuckle/pin clearance tolerance | **0.2–0.3 mm** gap between pin and barrel is described as the "sweet spot" for FDM-printed hinges | [Snapmaker — 3D Printed Hinges: Design Rules, Tolerances & Inspiration](https://www.snapmaker.com/blog/3d-printed-hinges/) |
| Print orientation | Print the hinge flat on the bed (pin axis in X/Y) rather than vertically, so the pin/barrel walls are made of continuous, long filament strands along their length rather than being built up in short Z layers — this maximizes shear strength at the pin | same |
| Common failure modes | "Elephant's foot" at the base (nozzle too close to bed) can fuse the hinge shut — fix via Z-offset calibration; over-extrusion can fill the clearance gap solid — fix by reducing flow 2–5% | same |

---

## 4. Feet, Bumpers, and Cable Management

### 4.1 Rubber feet / anti-slip pads

| Item | Detail | Source |
|---|---|---|
| Common materials | Silicone, EPDM, SBR, NBR, PU, PVC, EVA rubber — silicone and EPDM are the two most commonly marketed for self-adhesive stick-on feet | [Vital Parts — Self Adhesive Rubber Pads, Foam Pads, Anti-Slip EPDM](https://www.vital-parts.co.uk/self-adhesive-rubber-pads-10640-p.asp) |
| Common size range | Round/square pads from roughly **10 mm to 70 mm** diameter/side are the common commodity range; one supplier lists a 25-size range spanning **4.5 mm to 179 mm** diameter, 1.5–4.2 mm thickness | [Homediyer — self-adhesive rubber feet pads, 25 sizes](https://homediyer.com/products/black-rubber-feet-small-large-silicone-selfadhesicve-stick-on-pads-various-sizes) |
| Example specific product | 12 mm round EPDM cellular-rubber anti-slip pad, 2.5 mm thick, adhesive-backed | [adsamm.com — EPDM anti-slip pads Ø12mm x 2.5mm](https://www.adsamm.com/84-x-anti-slip-pads-made-of-epdm-cellular-rubber-0-47-inch-12-mm-black-round-adhedsive-non-slip-rubber-pad-0-1-inch-2-5-mm-thickness.html) |
| Mounting method | Self-adhesive (pressure-sensitive backing), no fasteners required | same sources |

### 4.2 TPU bumper hardware / mounting

| Mounting approach | Detail | Source |
|---|---|---|
| Screw + adhesive combo | A published CNC Kitchen printable design ("Corner Bumper (TPU Optimized)") is explicitly built for a combined screw-and-glue mounting approach | [Printables — CNC Kitchen Corner Bumper (TPU Optimized)](https://www.printables.com/model/369017-corner-bumper-tpu-optimized) |
| Screw-through mounting | Generic TPU edge-protector designs accommodate screw holes sized for screws up to ~4 mm diameter with head diameters up to ~8 mm, screwed with standard self-tapping/chipboard-style screws | secondary maker-guide sourcing (search-indexed content); no single vendor datasheet fetched — treat as directional |
| Adhesive-only mounting | UHU adhesive putty for repositionable/simple mounting, or E6000-type adhesive for a permanent bond | secondary maker-guide sourcing (search-indexed content) |
| Interference fit | TPU compresses under load; if a bumper relies on a friction/interference fit rather than screws or glue, the mating feature should be designed **0.2–0.4 mm oversized** so the TPU compresses into the correct final position | secondary maker-guide sourcing (search-indexed content) |

### 4.3 Neutrik D-series panel connector mounting screws

| Item | Detail | Source |
|---|---|---|
| Standard D-series panel cutout | Countersunk mounting holes sized to accept **M3 bolts or rivets** | [neutrik.com D-series product family page](https://www.neutrik.com/en/neutrik/products/xlr-connectors/xlr-chassis-connectors/d-series) |
| M3-threaded D-series variant | Some D-series housings include integral M3 tapped threads, allowing direct screw-in from the front without a separate nut/rivet | same |
| Supported panel thickness | **1–3 mm** | same |
| PCB-mount D-series hardware | Self-tapping screw, 2.2 mm diameter, max. 5 mm length (example part: KA22x5) — this is for PCB-mounted D-shape connectors, not panel screws | same |
| MFD fixing plate accessory | Neutrik's "MFD" fixing plate for D-size chassis connectors is described as an M3-threaded mounting plate for efficient mounting of D-sized connectors by M3 screws; the underlying datasheet PDF exists at neutrik.com but could not be parsed as text by the fetch tool used here | [neutrik.com/en/product/mfd](https://www.neutrik.com/en/product/mfd) (PDF at [neutrik.com/en/product/mfd.pdf](https://www.neutrik.com/en/product/mfd.pdf), fetched but unreadable as text) |
| NAC3MPX (powerCON TRUE1 chassis connector) mounting screws | Installation guidance found via secondary sourcing recommends M3 stainless steel countersunk screws for panel fastening; a separately sold kit offers **M3 x 12 mm countersunk Pozi screws with Loctite-secured nuts** for Neutrik D-type chassis panels | [designacable.com — Black M3x12mm Long Screw & Nut, Neutrik D-Type Chassis Panel Mount](https://www.designacable.com/black-m3x12mm-long-screw-nut-neutrik-d-type-chassis-panel-mount.html) (third-party accessory listing, not the Neutrik datasheet itself) |
| Exact Neutrik-specified screw part number/torque spec from the official NAC3MPX/NE8FDX datasheet PDF | `unknown` — the primary Neutrik datasheet PDFs were located but not successfully parsed as text by the available fetch tooling in this session | — |

**Conclusion for this project:** Design D-series connector cutouts to Neutrik's general D-shape panel spec
(countersunk M3 clearance holes, panel thickness 1–3 mm), and use M3 machine screws (stainless steel,
countersunk head, ~10–12 mm length depending on panel + nut-plate stack) unless/until the exact Neutrik
datasheet PDF is manually reviewed for a connector-specific screw callout.

### 4.4 Cable strain relief, cable ties, and adhesive mount bases

| Item | Detail | Source |
|---|---|---|
| Cable tie width classes | Miniature: 2.5 mm wide (lengths 60–200 mm); Intermediate: 3.6 mm wide (lengths 100–370 mm); Standard: 4.8 mm wide (lengths 100–700 mm+) | [HellermannTyton — Cable Ties](https://www.hellermanntyton.us/cable-ties/), [FibreStrap — Zip Tie Sizes](https://www.fibrestrap.com/zip-tie-sizes) |
| Overall cable tie size range across the market | Widths 2.5 mm–12.7 mm; lengths 100 mm–1030 mm | same sources |
| Adhesive-backed cable tie mount bases | Common commodity sizes: **1" × 1" (25.4 x 25.4mm), 19.5 mm × 19.5 mm, 0.75" × 0.75" (19 x 19mm)**, in 2-way and 4-way (routing-direction) styles; 3M sells both adhesive-only and screw-mount variants | [3M Cable Tie Mounting Bases product family](https://www.3m.com/3M/en_US/p/d/b00034736/), [Amazon — 10Gtek self-adhesive cable tie mounts, 19.5x19.5mm](https://www.amazon.com/Adhesive-Cable-Mounts-Holders-19-5mm/dp/B07F7Y9KGX) |
| Strain relief approach | `unknown` specific product spec — no dedicated strain-relief-boot datasheet was fetched in this research pass; general cable tie + adhesive mount base + printed cable clip combination is the common DIY approach implied by the sourcing above, not a single sourced product |

---

## 5. Captive side bolt — orderable options (issue #28)

> **Which screw to order:** slotted **fillister-head** 1/4"-20 UNC × 3/4" (19.05 mm) machine screw,
> A2 stainless steel, to ASME B18.6.3. It is the only head style checked in this research pass that
> reliably clears the case's ⌀12×6 mm head recess (`MCC_SIDE_BOLT_HEAD_REC_D/H`,
> `lib/mcc/constants.scad:155-163`) — see §5.1–5.2. Round-head and pan-head equivalents do not fit,
> and no captive/thumb-screw candidate found fits the recess without enlarging it (§5.2).

Research pass run 2026-09-09 for issue #28 ("Device retention screw: which 1/4"-20 slotted screw to
order"). Scope is documentation only — this section and the corresponding `BOM.md` rows.
`lib/mcc/constants.scad` is **not** changed by this section — see the follow-up flagged in §5.3.

### 5.1 Recommended: slotted fillister-head screw (ASME B18.6.3)

| Item | Value | Source |
|---|---|---|
| Standard | ASME B18.6.3 — Slotted Fillister Head Machine Screws | search result; standard number and head-dimension table as reported in the research pass — no direct standard-document URL was captured in the research handoff, see the Sources note below |
| Thread / length | 1/4"-20 UNC × 3/4" (19.05 mm) | same |
| Material | A2 stainless steel | same |
| Head diameter | ⌀9.88–10.52 mm | same — compare `MCC_SIDE_BOLT_HEAD_D = 10.0` mm, `assumed` (`lib/mcc/constants.scad:155-158`) |
| Head height | 5.26–6.02 mm | same — compare `MCC_SIDE_BOLT_HEAD_H = 4.5` mm, `assumed` (same constant block) |
| Fit vs. the printed recess | Closest imperial match to the assumed head dimensions, and the only head style checked here that reliably clears the case's ⌀12×6 mm head recess (`MCC_SIDE_BOLT_HEAD_REC_D/H = 12.0/6.0`, `lib/mcc/constants.scad:159-163`) | analysis in the research pass, based on the standard's own head-dimension table |
| Confirmed stock | zollschraubendirekt.de (Germany) | fetched — the one EU imperial-fastener specialist that fetched successfully in this research pass, confirming a slotted 1/4-20 × 3/4" screw in stock |

The fillister head's own height range (5.26–6.02 mm) runs above the repo's current `assumed`
`MCC_SIDE_BOLT_HEAD_H` (4.5 mm) by up to ~1.5 mm. This does not block ordering the screw — the
recess depth `MCC_SIDE_BOLT_HEAD_REC_H = 6.0 mm` already has margin over the assumed head height —
but is worth re-checking once the physical `side-bolt` coupon is measured (architecture's
measurement list M4/M5). Not resolved in this ticket; `constants.scad` is unchanged.

### 5.2 Alternative head styles considered (and rejected)

| Head style | Head diameter (max) | Fits the ⌀12 mm recess? | Verdict |
|---|---|---|---|
| Slotted fillister head (ASME B18.6.3) | ⌀10.52 mm | Yes — reliable clearance | **Recommended, §5.1** |
| Plain round head | up to ⌀11.99 mm | Marginal — near-zero clearance in the ⌀12 mm recess | Not recommended |
| Pan head | up to ⌀12.50 mm | No — larger than the recess itself | Rejected |
| Captive/thumb screw (e.g. Accu's socket-head captive screw) | not the limiting factor — drive style is | Drive is hex/socket, not slotted | Rejected — no captive/thumb-screw candidate found in this research pass fits the recess without enlarging it, and the one hex-drive candidate located would also deviate from the fixed D-09 "slotted screw" decision (`CLAUDE.md` "Fixed decisions" — Closure) |

### 5.3 Retention E-clip — DIN 6799

| Item | Value | Source |
|---|---|---|
| Part | RS PRO DIN 6799 external circlip | search result; RS Components UK/NL storefront listings — not independently fetched in this research pass, see §5.6 |
| Stock number, steel | 0289203 | same |
| Stock number, A2 stainless | 2096592 | same |
| Spec as listed | "5 mm shaft, 4.8 mm groove diameter" | same |

**Flag for a follow-up ticket:** every real DIN 6799 clip found in this research pass is spec'd for
a **4.8 mm** groove diameter, not the 5.0 mm currently assumed in `MCC_SIDE_BOLT_CLIP.groove_d`
(`lib/mcc/constants.scad:171-176`, `["groove_d", 5.0]`). Recommend correcting that constant once
confirmed against the physical `side-bolt` coupon (M4). **Not applied in this ticket** —
`lib/mcc/constants.scad` is out of scope for issue #28.

### 5.4 EPDM preload washer

No exact-match stock SKU for the case's OD18/ID8×2mm EPDM annulus (`MCC_SIDE_BOLT_PAD_*`,
`lib/mcc/constants.scad:184-191`) was confirmed at Reichelt, Conrad, RS, or Farnell in this research
pass. Recommend a generic self-adhesive rubber-washer assortment kit (Amazon.de/Amazon.nl), trimmed
to size, or a custom die-cut from a UK rubber specialist, until a closer match is found — the same
open item already noted in §4.1 above (`:186`, no exact stock SKU for the OD12×2.5 mm listed
example either).

### 5.5 Thread-locker

Removable/medium-strength thread-locker (e.g. Loctite 243), **not** a nylon patch or a
permanent/high-strength thread-locker. There is no nut on this joint — the screw threads directly
into the device's own metal thread — and the fixed D-09 decision requires the device to stay
removable (`CLAUDE.md` "Fixed decisions" — Closure), so a single-use nylon patch or a permanent
locker would be the wrong tool for a joint meant to be undone repeatedly.

### 5.6 What could not be verified

- **Reichelt and Conrad** — confirmed, via a successful fetch, to **not stock imperial UNC hardware
  at all**. A genuine absence, not a fetch failure.
- **Accu.co.uk / accu-components.com, all RS Components regional domains, Bossard, McMaster-Carr,
  and boltdepot.com** — blocked automated fetch (HTTP 403) in this research pass. Every figure
  attributed to these sources above (including the RS PRO E-clip stock numbers in §5.3) comes from
  search-index titles/snippets, not a page fetch — a human should confirm price and stock before
  ordering.
- **zollschraubendirekt.de** — the one EU imperial-fastener specialist that fetched successfully,
  confirming the §5.1 screw in stock.
- **Hornbach** — returned no relevant results for this class of hardware and was not pursued
  further (general DIY store, not an imperial-fastener specialist).

---

## Sources

All URLs below were fetched or searched on **2026-09-07**.

- https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen — fetched; standard M3 (RX-M3x5.7) insert spec, material, compatible plastics
- https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck — search result; short M3 insert (RX-M3S, 4.0mm length)
- https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-made-for-voron-rx-m3x5x4-messing-gewindebuchsen-fur-3d-druck — search result; Voron-variant M3 insert
- https://www.ruthex.de/en/pages/faq — fetched (attempted); did not contain the hole-size/temperature table sought
- https://3ddruckboss.de/collections/ruthex-gewindeeinsatze — search result; community/retailer corroboration of 4.0mm hole sizing
- https://forum.drucktipps3d.de/forum/thread/26986-kernloch-einschmelzmuttern/ — search result; forum discussion of practical M3 insert hole sizing (4.0–4.4mm range)
- https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong — fetched; 2026 pull-out force test article (PLA), hole diameter range tested, peak force, datasheet-accuracy conclusion
- https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts — fetched; soldering iron temperatures (PLA/PETG/ABS) and two-stage installation method
- https://tools.creative3dp.com/blog/heat-set-insert-hole-size-chart/ — fetched; secondary cross-check table of hole diameters and install temperatures per material (PLA/PETG/ABS-ASA/Nylon/PC)
- https://facfox.com/docs/kb/mastering-heat-set-inserts-a-professionals-guide-to-durable-3d-printed-threads — fetched; checked for a per-material table (none found), general wall-thickness/hole-depth rules
- https://www.mcmaster.com/products/captive-panel-screws/ — search result; confirms McMaster-Carr stocks captive panel screws (catalog page not scrapeable for exact dimensions)
- https://www.mcmaster.com/products/knurled-head-thumb-screws — search result; confirms McMaster-Carr stocks knurled thumb screws
- https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/ — search result; cantilever snap-fit design rules (L/t ratio, fillet radius, clip width)
- https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/ — fetched; snap-fit hook geometry, print-orientation, worked example dimensions
- https://southco.com/en_any_int/tl-40-113-07 — search result; Southco TL-40 (medium) toggle draw latch product line
- https://southco.com/en_us_int/tl-20-201-07 — search result; Southco TL-20 (small) toggle draw latch product line
- https://media.southco.com/media/static/Literature/tl.en.pdf — fetched (binary, unreadable as text); Southco TL draw latch datasheet, numeric specs not extractable
- https://www.amazon.com/CASE-CATCH-LATCH-TOGGLE-SQUARE/dp/B0848P2JWG — search result; generic 40mm x 27mm toggle case latch (flight-case market)
- https://fayshing.com/product-category/latches/ — search result; generic flight-case latch/lock hardware category
- https://www.elesa.com/en/elesab2bstoreus/latches-us--1 — search result; Elesa latches product family (no specific model datasheet located)
- https://southco.com/en_any_int/D2 — search result; Dzus Rapier (D2) quarter-turn fastener panel thickness range (0.5–30.4mm) and stud sizes
- https://southco.com/en_us_int/d2-517-1108-190 — search result; Dzus quarter-turn stud example product
- https://en.wikipedia.org/wiki/Dzus_fastener — search result; general Dzus fastener mechanism description
- https://www.first4magnets.com/product/6mm-dia-x-3mm-thick-n35-neodymium-magnet-089kg-pull-19521 — search result (fetch blocked 403, title/spec confirmed via search index); N35 6x3mm disc, 0.89kg pull
- https://www.first4magnets.com/product/6mm-dia-x-3mm-thick-n42-neodymium-magnet-09kg-pull-19218 — search result (fetch blocked 403); N42 6x3mm disc, 0.9kg pull
- https://suprememagnets.com/products/neodymium-magnet-8x3mm-disc — fetched; N52 8x3mm disc, ~1.76kg pull
- https://radialmagnet.com/our-magnets/neodymium-magnet-disk-n35-8mm-x-3mma/ — search result; confirms N35 8x3mm disc exists as a catalog item (no pull force retrieved)
- https://www.thingiverse.com/thing:1215238 — search result; 1.75mm filament used as a printed-hinge pin, design concept
- https://www.snapmaker.com/blog/3d-printed-hinges/ — fetched; hinge pin/barrel clearance tolerance (0.2–0.3mm), print orientation, failure modes
- https://homediyer.com/products/black-rubber-feet-small-large-silicone-selfadhesicve-stick-on-pads-various-sizes — search result; self-adhesive rubber feet size range (4.5–179mm, 25 sizes)
- https://www.vital-parts.co.uk/self-adhesive-rubber-pads-10640-p.asp — search result; rubber/EPDM pad material options
- https://www.adsamm.com/84-x-anti-slip-pads-made-of-epdm-cellular-rubber-0-47-inch-12-mm-black-round-adhedsive-non-slip-rubber-pad-0-1-inch-2-5-mm-thickness.html — search result; specific EPDM anti-slip pad example (12mm x 2.5mm)
- https://www.printables.com/model/369017-corner-bumper-tpu-optimized — search result; CNC Kitchen's TPU corner bumper design (screw + glue mounting)
- https://blog.uavmodel.com/3d-printing-tpu-parts-for-fpv-drones-bumpers-mounts-and-antenna-holders/ — search result; general TPU bumper mounting practices (screw sizing, adhesives, oversizing for interference fit)
- https://www.neutrik.com/en/neutrik/products/xlr-connectors/xlr-chassis-connectors/d-series — fetched; D-series panel cutout spec (M3 countersunk holes, 1-3mm panel thickness), PCB mount screw spec
- https://www.neutrik.com/en/product/mfd — search result; MFD M3 fixing plate accessory for D-series connectors
- https://www.neutrik.com/en/product/mfd.pdf — fetched (binary, unreadable as text); MFD datasheet PDF, could not extract numeric detail
- https://www.designacable.com/black-m3x12mm-long-screw-nut-neutrik-d-type-chassis-panel-mount.html — search result; third-party M3x12mm screw/nut kit sold specifically for Neutrik D-type panel mounting
- https://www.hellermanntyton.us/cable-ties/ — search result; cable tie width/length class overview
- https://www.fibrestrap.com/zip-tie-sizes — search result; cable tie size ranges cross-check
- https://www.3m.com/3M/en_US/p/d/b00034736/ — search result; 3M adhesive cable tie mounting base product family
- https://www.amazon.com/Adhesive-Cable-Mounts-Holders-19-5mm/dp/B07F7Y9KGX — search result; example adhesive cable tie mount base (19.5x19.5mm)

### Sources added 2026-09-09 for issue #28

Domain-level URLs below — the research pass for issue #28 named these retailers/domains but its
handoff did not include specific product-page URLs for most of them; where only a domain is cited,
that domain's own storefront should be searched directly rather than treating the homepage as a
citation for a specific figure. ASME B18.6.3 itself (the fillister-head dimensional standard cited
in §5.1) is one such case: no source URL for the standard document was captured in the handoff, so
those head-diameter/height figures are cited by standard number only, pending a formal citation.

- https://www.zollschraubendirekt.de/ — fetched; confirmed slotted 1/4-20 × 3/4" UNC machine screw in stock (§5.1) — homepage cited, specific product-page URL not captured in the research handoff
- https://www.reichelt.de/ — fetched; confirmed no imperial UNC hardware stocked (§5.6)
- https://www.conrad.de/ — fetched; confirmed no imperial UNC hardware stocked (§5.6)
- https://uk.rs-online.com/ — search result (fetch blocked, HTTP 403); DIN 6799 E-clip stock numbers 0289203 (steel) / 2096592 (A2 stainless) via search-index snippet only (§5.3, §5.6)
- https://nl.rs-online.com/ — search result (fetch blocked, HTTP 403); same E-clip listing, NL storefront (§5.3, §5.6)
- https://www.accu.co.uk/ — blocked (HTTP 403); captive/thumb socket-head screw candidate found via search-index only, rejected in §5.2 (hex drive, not slotted)
- https://www.accu-components.com/ — blocked (HTTP 403); same candidate, alternate storefront
- https://www.bossard.com/ — blocked (HTTP 403); general 1/4"-20 UNC sourcing lead, no specific figures retrieved
- https://www.mcmaster.com/ — blocked (HTTP 403); general 1/4"-20 UNC sourcing lead, no specific figures retrieved
- https://www.boltdepot.com/ — blocked (HTTP 403); general 1/4"-20 UNC sourcing lead, no specific figures retrieved
- https://www.amazon.de/ — search result; generic self-adhesive EPDM/rubber washer assortment kits (§5.4)
- https://www.amazon.nl/ — search result; same, NL storefront (§5.4)
- https://www.hornbach.de/ — fetched; no relevant results for this hardware class, not pursued further (§5.6)
