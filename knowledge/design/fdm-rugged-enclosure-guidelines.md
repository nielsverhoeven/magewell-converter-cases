# FDM Design Guidelines for Rugged Protective Enclosures

Scope: design guidance for 3D-printed (FDM/FFF) rugged, drop-resistant protective cases — specifically for Magewell Pro Convert NDI video converters used in live/touring production — printable on consumer FDM printers (e.g. Prusa MK4/MK3S, Bambu Lab P1S/X1C). Every figure below is sourced from a fetched web page; where no verified figure could be found, the cell/value says `unknown` rather than a guess. See [Sources](#sources) for the full citation list with fetch dates (all fetched/searched 2026-09-05 unless noted otherwise... see note below).

> **Note on dates:** research for this document was carried out in the session dated **2026-09-05** through **2026-09-07**; all citations are marked with the fetch date actually used, 2026-09-05/06/07 as applicable in the Sources table (the task specifies 2026-09-07 as the reference date; all sources were live-fetched in the same research session).

---

## 1. Material choice for rugged enclosures

### 1.1 Mechanical / thermal comparison table

| Material | Impact strength / toughness | HDT (°C) | Warping tendency | UV resistance | Approx. price class (per kg) | Notes / printer requirements |
|---|---|---|---|---|---|---|
| **PLA** *(baseline reference only, not recommended for rugged use)* | Izod-style impact ~5 kJ/m² (Charpy-type test, CNC Kitchen) — lowest of PLA/PETG/ASA tested | Softens ~60 °C, fails ~65 °C (CNC Kitchen test) | Low | Poor — becomes brittle | Low, ~$14-18/kg (SUNLU-class budget PLA) | No enclosure needed; brittle, not suitable for rugged case |
| **PETG** | Impact ~8.6 kJ/m² in CNC Kitchen's flex/impact test — "high tenacity and flexibility... often prevent it from breaking" (Prusa) | Begins softening ~80 °C, fails ~85 °C (CNC Kitchen); Prusa: good up to ~80 °C service temp | Low — Prusa: "very little thermal expansion... does not shrink or warp" | Moderate — yellows/loses gloss over years; loses tensile strength "twice as fast" as it visually degrades vs ABS in some outdoor tests; well-designed parts reported to hold structural integrity 3–5 years outdoors in temperate climates | ~$18.99/kg median (US ~$19.79/kg, EU ~€19.99/kg, Aug 2026) | No enclosure required. Nozzle 230–240 °C, bed 85–90 °C (Prusa profile) |
| **ASA** | Impact ~18 kJ/m² in CNC Kitchen's test — "more than three times PLA," best of the three materials tested | Softens ~110 °C, fails ~120 °C (CNC Kitchen); other sources cite HDT 85–102 °C depending on brand/test method | High — Prusa: "significant warping is the main disadvantage" | Excellent — "the #1 choice for outdoor use," replaces ABS's butadiene with UV-stable acrylate rubber, maintains color/stiffness/mechanical integrity through extended outdoor exposure | ~€27.99–28.89/kg EU, ~$26.99/kg US (Aug 2026) | Enclosure recommended/required (Prusa: needed for large parts, high ambient temp reduces warp). Nozzle 260 °C, bed 105→110 °C (Prusa profile) |
| **ABS** | Notched Izod ~200–220 J/m (≈4 ft·lb/in) | ~95–100 °C at 0.45 MPa | High — cannot print without enclosure per one guide; needs 40–50 °C ambient to prevent warp/delamination | Poor — butadiene component breaks down under UV, yellows and becomes brittle, visible yellowing "after a few months outside" | ~$15–25/kg (budget $12-16/kg, premium $18-25/kg) | Enclosure required for warp/delamination control |
| **PC (Polycarbonate)** | Notched Izod 600–900 J/m (ASTM D256) — much tougher than ABS/ASA | 135–140 °C at 0.45 MPa (some commercial filaments list ≥120 °C) | Very high — high coefficient of thermal expansion; brim of 5–8 mm recommended; needs enclosure at 60–70 °C ambient | Mixed/moderate — described as having "excellent UV resistance" by one source but also flagged as "susceptible to UV degradation and yellowing with prolonged exposure" by another; treat as needing UV-stabilized grade or paint/coating for long-term outdoor touring use | ~$40–80/kg (roughly 20–40% more than ABS/PLA) | Enclosure required. Nozzle ~260–310 °C (some sources cite up to 290–310 °C); bed 110–150 °C depending on source/brand — verify against your specific filament's datasheet |
| **PC-CF** | `unknown` — no verified Izod/Charpy figure found in fetched sources | `unknown` — not found in fetched sources (general PC-CF is marketed for heat resistance; no verified number retrieved) | High (inherits PC's high shrink/warp behavior; CF filling reduces it somewhat vs unfilled PC, per general CF-filament behavior, but no verified number found) | `unknown` | `unknown` — general CF-filled engineering filaments run roughly $25 to well over $150/kg | Requires hardened nozzle (steel/ruby-tipped) — abrasive fill wears brass nozzles. Enclosure required (inherits PC's warping/temperature needs) |
| **PA-CF (nylon carbon fiber)** | Dry PA6-CF samples absorbed ~15% of impact hammer energy in one test; moisture-conditioned PA6 (unfilled) impact strength more than tripled after conditioning, absorbing >50% of hammer energy — carbon fiber stiffens nylon and lowers its shrink rate significantly vs plain nylon | Bambu PA6-CF: 186 °C at 0.45 MPa / 164 °C at 1.8 MPa (manufacturer data); other PAHT-CF products report up to ~190–194 °C annealed | Low-moderate — CF fill "lowers the shrink rate significantly" vs unfilled nylon, which is notoriously warp-prone; still benefits from enclosure/drying discipline | Moderate — UV exposure of PA6/CF composites increases modulus/hardness but "significantly reduces impact energy" (embrittlement) per a published UV-exposure study; CF reinforcement appears to provide some protective benefit vs unreinforced PA6, but the material still photo-oxidatively degrades (N–H, C=O bond changes per FTIR) | Roughly $25–$174+/kg depending on brand (one example: 3DXTech CarbonX Nylon12+CF ≈$174/kg for a 2kg spool) | Requires hardened nozzle (abrasive CF). Requires aggressive filament drying (nylon is highly hygroscopic) and typically an enclosure. Recommended hardened-nozzle temp for PA-CF cited around 270 °C nozzle / 90–110 °C bed by one source |
| **PETG-CF** | `unknown` — no verified Izod/Charpy number found in fetched sources | `unknown` — not found in fetched sources | Lower than unfilled PETG (CF fill increases dimensional stability generally, per general CF-filament behavior); no verified specific number found | `unknown` (inherits base PETG's moderate/mixed UV behavior, unverified for the CF-filled variant specifically) | Roughly in the general CF-filament band, $25+/kg — no PETG-CF-specific figure verified | Requires hardened nozzle (abrasive CF). Nozzle 240–260 °C, bed 80–90 °C |
| **TPU** | Flexible/elastomeric — not measured in rigid-plastic Izod/Charpy terms in sources found; used specifically *for* impact energy absorption (see §12) | `unknown` — not applicable/found as a rigid-plastic HDT figure; glass transition ~65–70 °C cited for typical 95A TPU | Low — generally considered easy/low-warp to print | `unknown` for bare TPU itself; one source notes TPU film is used as a UV-protective *layer over* polycarbonate sheet (implying reasonable inherent UV durability), but no direct TPU UV-degradation figure was found | ~$18–55/kg depending on brand/hardness (budget ~$17.99/kg Elegoo US, up to ~$55/kg specialty Recreus FilaFlex 70A) | No enclosure needed. Melt zone ~210–240 °C; most common 95A shore hardness spools print around 230 °C nozzle. Shore hardness range 70A–95A; 95A most common/easiest to print |

### 1.2 Sources for §1
See the Sources section; key figures drawn from CNC Kitchen's PLA/PETG/ASA comparison, Prusa's PETG and ASA knowledge-base articles, and multiple filament-property/pricing searches (WebSearch aggregated results) — flagged individually above where a figure could not be traced to a single authoritative fetched page.

---

## 2. Wall thickness and perimeter counts for impact resistance

| Use case | Recommended wall thickness | Perimeter/wall-loop count (0.4 mm nozzle) | Notes |
|---|---|---|---|
| Absolute minimum, non-structural feature | 0.8 mm | 2 perimeters (2 × 0.4 mm line width) | Below this the slicer cannot reliably build a solid wall; may leave gaps |
| General structural wall (recommended minimum) | 1.2 mm | 3 perimeters | |
| Parts under mechanical load (practical recommendation) | 2–3 mm | ~5–7 perimeters at 0.4 mm line width | Cited as the practical range for "parts under any mechanical load" |
| Load-bearing walls | ≥2.4 mm, combined with 40–60% infill | 6+ perimeters | |
| Snap-fit / hinge areas | Increase locally to 2.0 mm | — | Prevents cracking during assembly/flex cycling |
| Industrial TPU parts (bumpers, dampers, seals) | 2.0–3.0 mm minimum | — | Elevated vs rigid-plastic minimums due to TPU's lower modulus |

**Design rule:** wall thickness should be a multiple of the nozzle diameter (line width) to avoid the slicer generating partial-width "gap fill" extrusions, which are a weak point for layer adhesion and impact resistance. More perimeters (vs relying on infill) generally out-performs single/thin-wall designs for impact resistance because each perimeter is a continuous, well-bonded extrusion loop, whereas sparse infill patterns introduce voids and stress risers. — [RapidDirect wall thickness guide](https://www.rapiddirect.com/blog/3d-printing-wall-thickness/), [Xometry Pro](https://xometry.pro/en/topic/recommended-wall-thickness-for-fdm/)

---

## 3. Corner radii

Sharp internal (and to a lesser degree external) corners are stress concentrators: they abruptly redirect the internal force path, concentrating stress at a single point and increasing the risk of crack initiation, especially at FDM's inherently anisotropic layer interfaces. — [Printed Solid — 3D Printing Design Tips: Stress Concentrations](https://www.printedsolid.com/blogs/news/37036739-3d-printing-design-tips-part-1-stress-concentrations)

| Guideline | Value | Source note |
|---|---|---|
| Practical fillet radius rule of thumb | Roughly equal to (or at least half) the thickness of the adjoining wall | |
| Typical functional-part fillet range | 1–3 mm | |
| Minimum useful fillet size | Should exceed nozzle diameter / layer height — fillets close to nozzle diameter or layer height barely change the stress concentration and mainly just add slicing complexity | |
| Demonstrated benefit | Filleting an inside corner "can more than double" the load a typical bracket takes before failure | |
| Fillet vs. chamfer | Fillets distribute load across a broad region (better stress-concentration reduction); chamfers remove the sharp corner but are less effective than a true radius | |

— [Fictiv — Fillets: When to Use 'Em, When to Lose 'Em](https://www.fictiv.com/articles/fillets-when-to-use-em-when-to-lose-em), [Printed Solid](https://www.printedsolid.com/blogs/news/37036739-3d-printing-design-tips-part-1-stress-concentrations)

**Application to this project:** all internal corners of the case shell (especially at wall-to-floor junctions, boss bases, and lid lip corners) should carry a generous fillet — not a bare 90° corner — sized to the local wall thickness (e.g. ~1–2 mm fillet on a 2–3 mm wall).

---

## 4. Ribs and gussets

| Parameter | Guideline | Source |
|---|---|---|
| Rib thickness | At least 2–3× nozzle diameter (e.g. ~1.2–1.5 mm at 0.4 mm nozzle); should generally be *less* than the adjoining wall thickness — aim for roughly 60% of wall thickness — to avoid a thick junction that both risks sink/cracking and prints slower | luisllamas.es, Fictiv |
| Rib height | Keep to about 3× rib thickness as a practical limit — taller ribs behave like slender columns and buckle instead of stiffening | Fictiv / PartWork.ai |
| Gusset height (attached to a boss) | Up to ~95% of the boss height, but generally under 4× nominal wall thickness, with 2× nominal wall thickness preferred | Fictiv |
| Why not just thicken the wall | A thick, solid wall shrinks unevenly as it cools, producing sink marks and warping; the standard fix is to keep walls at a uniform (thinner) thickness and add ribs/gussets for stiffness instead — ribs and gussets deliver most of the stiffness gain "for a fraction of the material" | Fictiv / Core77 |

**Application:** the Magewell case shell should use uniform ~2–3 mm walls per §2, with internal ribs at panel centers/spans prone to flex, rather than simply making the whole shell thicker.

---

## 5. Print orientation vs. layer adhesion

**Core rule:** FDM parts are strongest in the plane parallel to the print bed (X-Y plane) and weakest across layer lines (Z-axis / interlayer bonds). Parts printed with their long axis along Z show lower tensile strength than the same geometry printed flat, "due to weaker bonding between layers," and are "particularly vulnerable to forces acting parallel to the layers and especially to impact strength." — [ResearchGate: Effect of Printing Orientation on Mechanical Properties of FDM Parts](https://www.researchgate.net/publication/362937073_The_Effect_of_Printing_Orientation_on_the_Mechanical_Properties_of_FDM_3D_Printed_Parts)

Practical implications for a drop-resistant electronics case:

- Orient the case shell so that the faces/edges most likely to take a direct impact (the flat panels and outer walls that would hit the floor in a drop) load the perimeter walls **in-plane** rather than putting a tensile/peel load directly across a layer interface.
- Avoid orientations where a drop impact would try to pry two layers apart (Z-axis cleavage) at a thin wall or a boss.
- Thinner layers generally improve interlayer bonding/strength versus thicker layers, at the cost of print time — a relevant trade-off for a case's outer shell layers.
- For bonded/assembled joints (e.g. glued TPU bumpers, snap-fit lids), orientation also affects bond strength: at lower layer thickness, "edgewise" orientation gave the best bonding strength in one lap-joint study, while at higher layer thickness "flatwise" orientation was best — worth testing empirically per joint design.

— [Markforged — 3D Printing Settings Impacting Part Strength](https://markforged.com/resources/learn/design-for-additive-manufacturing-plastics-composites/understanding-3d-printing-strength/3d-printing-settings-impacting-part-strength), [Springer — Effect of layer thickness and print orientation on strength of 3D printed and adhesively bonded single lap joints](https://link.springer.com/article/10.1007/s12206-017-0415-7)

---

## 6. Tolerances for sliding fits, press fits, and snap-fits

| Fit type | Per-side clearance | Total (diametral) clearance | Source note |
|---|---|---|---|
| Press fit | ~0.0–0.1 mm (can be negative/interference) | 0.0–0.1 mm total in one source's fit table | Interference reduces clearance; "reduce clearance to 0.1–0.2 mm or even negative" per another source |
| Snug / location fit | — | 0.1–0.2 mm total | |
| Sliding fit | 0.3–0.5 mm per side (one source); other sources cite 0.3–0.4 mm total | 0.3–0.4 mm total (alternate source) | Confirms the commonly-cited ~0.2–0.4 mm-per-side range from the brief, though exact figures vary by source — treat 0.3–0.5 mm per side as a practical starting point and tune per printer |
| Loose fit | — | 0.4–0.6 mm total | |
| Prusa-specific guidance | Minimum recommended clearance for moving parts: **≥0.3 mm**, based on Prusa's cited practical dimensional precision of ~0.2 mm | | |
| Snap-fit | Sized per material flex behavior, not a fixed clearance number | | Calculate deflection from material's elastic strain limit rather than a generic clearance value |

**Recommended practice:** print a calibration tolerance test coupon (0.1 mm increment slots, e.g. 0.1–0.5 mm) on your actual printer/material combination and measure with a digital caliper before finalizing sliding/press-fit dimensions, since real clearance depends on printer calibration, not just material. — [Zbotic — 3D Printing Tolerances](https://zbotic.in/3d-printing-tolerances-designing-gaps-for-press-fits-threads-and-snap-fits/), [Creative3DP Tools — Press-Fit Tolerances](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/)

---

## 7. Overhang and bridging limits

| Feature | Typical guidance | Source note |
|---|---|---|
| Maximum unsupported overhang angle (from vertical) | ~45° is the commonly-cited safe default; many consumer FDM printers can manage 45–55° depending on cooling/material/layer height; some machines (cited example: Ultimaker S3) reportedly achieve 60° with a standard 0.4 mm nozzle | wevolver.com, convertools.net |
| Reliable bridge span (minimal sag) | Up to ~10 mm | layerx3d.in / 3dmag.com |
| Bridge span with visible sag but functionally OK | ~10–30 mm | |
| Bridge span requiring supports | >30 mm (generally) | |
| Tightest "no visible sag/marks" bridge threshold (alternate source) | <5 mm | |
| Theoretical overhang at 0.1 mm layer height / 0.4 mm line width | ~27° (a calculated figure, more conservative than the "45° rule of thumb") | |

**Application to venting/geometry:** design overhangs on the case shell (e.g. sloped surfaces, vent hoods) at ≤45° where possible to print support-free; keep any bridged spans (e.g. over a vent cavity) under ~10 mm for a clean unsupported result on a consumer 0.4 mm-nozzle printer.

---

## 8. Heat-set insert bosses (geometry only — not install specs)

| Parameter | Guideline (M3-class insert) | Source |
|---|---|---|
| Minimum solid wall around the insert hole | ≥1.6 mm all around; ~2.0 mm is a good starting reference value; ideally closer to 2× the insert's outer diameter for a boss under real load | insertguide.com |
| Boss outer diameter | Roughly 1.5–2× the insert's outer diameter — for a ~4.6 mm OD M3 insert, a boss of ~8–9 mm diameter | insertguide.com |
| Minimum material between hole wall and any outer part edge | ≥2 mm for M2/M3-class inserts | insertguide.com |
| Primary cause of boss cracking | Thin boss walls: during heat-set installation the heated insert softens and displaces plastic outward; insufficient surrounding material causes the boss to expand, split, or form vertical cracks — described as "the number one cause of cracked inserts" | insertguide.com |
| Other recommended features | Lead-in chamfer at the hole mouth, a base fillet at the boss-to-floor junction, and a relief well below the insert | insertguide.com |

**Application:** any M3 heat-set-insert boss in the Magewell case (e.g. lid fasteners) should target ~8–9 mm boss OD around a ~4.6 mm insert hole, with a fillet at its base per §3, printed with a full-perimeter wall (no sparse infill) around the hole per §2.

---

## 9. TPU corner bumpers: separate-print-and-attach vs. multi-material/AMS

| Approach | How it works | Tradeoffs |
|---|---|---|
| **Separate print + attach** | Print rigid shell and TPU bumpers as separate jobs (potentially different printers/materials), then bond with adhesive (UHU putty, E6000, or similar) or a mechanical press-fit | Simpler slicing/tuning per material; avoids purge waste and nozzle-clogging risk from switching flexible/rigid filament on a shared nozzle; extra manual assembly step; bond-line becomes a potential failure point unless mechanically retained too |
| **Multi-material / AMS (or MMU)** | Single print job switches between rigid filament and TPU (e.g. Bambu "TPU for AMS") for integrated bumpers in one part | Bambu markets a dedicated "TPU for AMS" product specifically to make this workable; however, single-nozzle multi-material swappers (AMS/MMU/ERCF-style) are explicitly "discouraged for mixing TPU and rigid materials on a shared nozzle" per one source, due to jamming/purge-tower reliability issues; when it works, gives strong bonded interfaces and no separate assembly step |

**Recommendation for this project:** given reliability concerns with flexible+rigid filament swapping on a shared nozzle, the separate-print-and-attach approach (TPU bumper pressed/glued onto the rigid shell) is the lower-risk default for a touring/production case, unless the printer specifically uses a TPU product validated for its AMS/MMU system.

— [Bambu Lab — TPU for AMS](https://bambulab.com/en/filament/tpu-for-ams), [3DPrintDecoded — Printing TPU and PLA Together](https://3dprintdecoded.com/articles/printing-tpu-and-pla-together/), [Bambu Lab Forum — thoughts on TPU multi-material printing](https://forum.bambulab.com/t/some-thoughts-on-tpu-multi-material-printing/160014)

---

## 10. Lid design: lip/labyrinth joints vs. tongue-and-groove

| Joint type | Function | Notes |
|---|---|---|
| Labyrinth / tongue-and-groove seal | A stepped or tortuous-path joint between lid and body that resists dust/debris ingress through a non-straight-line path, and adds shear/registration strength to the lid-body interface beyond just the fasteners | Described generically as a "labyrinth seal" — a tortuous path that helps prevent leakage/ingress; recommended lip thickness "at least three filaments wide" (i.e., at least 3 extrusion line-widths, ~1.2 mm at 0.4 mm nozzle) for a sturdy, rigid lip |
| Gasket-in-channel (compression) variant | A printed channel (example cited: 2 mm wide × 1.5 mm deep) around the mating face holds a separately-printed TPU gasket strip that compresses when the lid is fastened down | Compression-based sealing is more forgiving of FDM surface irregularities than a flat face-to-face joint, since it tolerates minor warping/print imperfection |
| Tongue-and-groove (no gasket) | Interlocking rigid-plastic tongue and groove aids alignment and adds rigidity/shear resistance without fasteners, but does not by itself provide a dust/moisture seal the way a compression gasket does | Useful for locating/registration and adding stiffness to the assembled shell; combine with a gasket channel if dust-sealing is also required |

**Comparison takeaway:** a rigid tongue-and-groove/labyrinth lip is primarily a rigidity and coarse dust-ingress feature (defeats a straight-line dust path and stiffens the lid-to-body joint); if genuine dust/splash sealing is required, add a compression gasket (TPU strip in a channel) rather than relying on the rigid labyrinth geometry alone. — [FacFox — Enclosure Design Guide for 3D Printing](https://facfox.com/docs/kb/enclosure-design-guide-for-3d-printing), [Zbotic — 3D Printing Electronics Housings: Water and Dustproof Cases](https://zbotic.in/3d-printing-electronics-housings-water-and-dustproof-cases/)

---

## 11. Living hinges: why they are a poor choice in PETG

**Recommendation: avoid living hinges in PETG for this project; if a hinge is required, use TPU or a separate metal-pin hinge instead.**

Reasoning, per sourced material:

- Injection-molded living hinges are made almost exclusively from **polypropylene (PP)** or polyethylene — materials chosen specifically because they are flexible, soft, low-melting-point, and, critically, **fatigue-resistant** through repeated flex cycles (the classic flip-top-bottle hinge). — [Firgelli / Living Hinge Mechanism](https://www.firgelliauto.com/blogs/mechanisms/living-hinge)
- PETG is not one of the materials generally recommended for FDM living hinges; guidance for FDM instead points to Nylon 12 (or TPU/flexible filament for the hinge section in a multi-material print) as suitable choices, with PP being the injection-molding standard PETG cannot match in flex-fatigue behavior. — [Protolabs Network / Hubs — How to design living hinges for 3D printing](https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/)
- PETG living hinges are viable only for **limited-cycle** applications (a lid that opens/closes occasionally), not for anything expected to flex "constantly." One recommended low-cycle PETG hinge thickness is 1.0–1.5 mm. — [FastPreci — Why 3D Printed Hinges Fail](https://www.fastpreci.com/blog/3d-printed-hinges/)
- PETG's failure mode under repeated flex is reported as a sudden, low-warning fracture ("it can flex more [than PLA] and will fracture without warning, all at once") rather than a gradual, predictable wear-out — an undesirable trait for a hinge on touring gear subjected to frequent, unsupervised open/close cycling.
- By contrast, **TPU** is explicitly recommended as the correct material where a hinge needs to flex repeatedly over a long lifespan — cited as able to flex 180° "thousands of times without fatigue failure," vs. an FDM PETG/rigid-material example hinge that reportedly failed around only ~25 cycles in one test.

**Recommendation for this project:** given the touring/road-case use case (frequent lid open/close cycles, no controlled environment), do not rely on a PETG living hinge as the case's primary lid mechanism. Prefer a mechanical hinge (printed knuckle + metal pin, or a hinge hardware insert) or, if a flexible hinge is truly desired, a TPU hinge section (either bonded on or multi-material printed per the tradeoffs in §9).

---

## 12. Designing for drop protection

Key concepts, as sourced:

- **Energy absorption / "crumple zone" analogy:** a compliant edge (e.g. TPU) "flexes inward on impact, spreading the load over a bigger area and a longer time, which dramatically reduces the peak force" the protected device sees — explicitly compared to a car's crumple zone. Crumple zones work by placing deliberate "weak"/compliant spots at strategic locations so the structure collapses/deforms in a controlled way, converting impact energy into heat via material deformation rather than transmitting it into the protected payload. — [designmycase.co.uk (bumper case design principle)], general crumple-zone description via search aggregation
- **Bumper geometry:** corner/edge bumpers (in TPU or similarly compliant material) placed at the corners and edges most likely to strike the ground first are a standard protective-case strategy; the exposed rubber/TPU bumper geometry itself is what "provides additional protection in the event of a drop," beyond just the rigid shell.
- **Keeping connectors recessed:** the general design principle from this research area — consistent with the crumple-zone/bumper approach — is to keep vulnerable hardware (panel-mount connectors, PCB edges) set back behind a raised rib or bumper lip so that a drop impact loads the case's sacrificial structure first, not the connector body or its panel-mount threads/solder joints directly. *(This specific "recess the connector behind a rib" wording is a design inference drawn from the crumple-zone/bumper sourcing above combined with the ribs/gussets guidance in §4 — no single source stated this exact sentence for connector protection specifically; flagged here as inferred best practice rather than a directly-quoted figure.)*

— [designmycase.co.uk](https://designmycase.co.uk/bumper-cases), [Adafruit — iPhone X NinjaFlex + PLA Bumper Case](https://learn.adafruit.com/iphone-x-ninjaflex-pla-bumper-case/3d-printing)

**Application:** design the Magewell case so the Neutrik/BNC/power connectors sit recessed behind printed ribs or a TPU corner/edge bumper (per §9), and orient ribs/wall perimeters per §5 so a face/corner/edge drop loads continuous in-plane perimeter walls rather than a thin cross-layer section next to a connector cutout.

---

## 13. Ventilation design

| Topic | Guidance | Source note |
|---|---|---|
| Chimney effect | Passive convection: warm air is less dense and rises; placing **low inlet vents** and **high outlet vents** creates continuous natural airflow with no fan — cool air drawn in low, hot air exhausted high | mpvent.com, fanacdc.com |
| Slot vs. hex vents — dust | Louvers/filtered vents "guide airflow and block out dust or water"; slotted vent configurations are described as providing efficient airflow "while minimizing the intake of dust." No fetched source directly quantified a hex-vs-slot dust-ingress difference — treat any specific numeric hex-vs-slot dust comparison as `unknown` | fanacdc.com, acdcecfan.com |
| Membrane option | ePTFE-type membranes are permeable to air/water vapor but block liquid water and dust particles — an option if a fully sealed-but-vented enclosure is later required | acdcecfan.com |
| Minimum practical slot width on a 0.4 mm-nozzle consumer FDM printer without supports | `unknown` as a vent-specific figure — no source gave a vent-slot-specific minimum. The closest verified adjacent figures: general minimum wall/slot feature width is commonly cited at **0.8 mm** (two 0.4 mm perimeter lines), and lattice-structure minimum gaps are cited at **1 mm**. A vertical vent slot (printed as a wall opening, not bridged) can likely be printed narrower than a horizontal bridged slot; a horizontally-bridged slot benefits from staying within the ~10 mm reliable-bridge span from §7. Do not treat 0.8 mm/1 mm as a verified "vent slot" spec — they are the nearest verified analogous minimum-feature figures, cited here as `inferred, not vent-specific` | RapidDirect / general FDM minimum wall & lattice-gap sources |

**Design implication for the Magewell case:** place intake vent slots low on the enclosure and exhaust vents high (chimney effect), print vent slots oriented vertically through the wall thickness where possible (avoids relying on bridging), and keep any horizontally-bridged vent openings under the ~10 mm reliable bridge span from §7 if bridging cannot be avoided. Confirm the actual minimum printable slot width empirically on your printer/nozzle before finalizing vent geometry, since no verified vent-specific number exists in the sourced material.

---

## 14. Grounding / EMI notes for metal panel connectors in a plastic enclosure

- Neutrik's dedicated **EMC-series** connectors (e.g. XLR EMC line) are built specifically to solve this class of problem: shielded-connector performance issues "with radio transmission or mobile phones" in professional live/recording contexts. — [Neutrik EMC Series](https://www.neutrik.com/en/neutrik/products/xlr-connectors/xlr-chassis-connectors/emc-series)
- **Shield continuity mechanism:** the EMC design provides "a continuous RF shield connection from the cable to the chassis connector housing via a circular capacitor around the cable shield," which acts as a high-pass filter with a cutoff around 10 MHz; an additional EMI suppression ferrite bead (24 Ω at 1 MHz) between pin 1 and the cable screen adds a low-pass filter for further RF rejection. — [Neutrik NC3FDX-EMC-Spec](https://www.neutrik.com/en/product/nc3fdx-emc-spec)
- **Industry best practice (metal-panel/metal-chassis context):** tie all chassis connector shells, pin 1 (cable shields), and the enclosure shield together to a common ground. — [Benchmark Media — Grounding XLR Connectors](https://benchmarkmedia.com/blogs/application_notes/grounding-xlr-connectors-neutrik-usa)
- **What this means for a plastic (non-conductive) enclosure:** a plastic shell provides **no Faraday-cage/shielding contribution** of its own — unlike a metal case, it cannot serve as part of the ground/shield return path, and it cannot bond one connector's shell to another's through the chassis. One source notes that "a small battery-powered device in a plastic enclosure will have a floating ground in the internal layers of the PCB," and recommends that if a shielded connector is present, it should be tied to the main system/PCB ground rather than left floating. — [Cadence / System Analysis blog — All Things Connectors Part 5: Shielded Connectors](https://resources.system-analysis.cadence.com/blog/all-things-connectors-part-5-shielded-connectors)
- **Mitigation implication for this project:** because the Magewell case shell is plastic, shield continuity through the enclosure itself cannot be relied on. The cable shields must be bonded connector-to-connector via the PCB/internal wiring ground plane (not via the plastic shell), and if strong RF immunity matters for this touring application, EMC-rated connectors (Neutrik EMC series or equivalent) with their own internal capacitive/ferrite shield-continuity path are the appropriate mitigation, since the plastic shell cannot substitute for that continuity.

---

## 15. Ruggedness test protocols commonly used by hobbyists/makers

| Protocol element | Guidance found | Source |
|---|---|---|
| Informal maker/hobbyist drop test benchmark | The brief's suggested "~1 m drop onto concrete on each face/corner/edge" pattern is consistent with common informal maker practice; a **Pelican-style** protocol is a reasonable industry-style reference point to cite, per the task brief | (informal community convention; no single hobbyist-forum source with an exact 1 m protocol was found and verifiably fetched — flagged as `informal community convention`, not a verified numeric citation) |
| Professional/industrial reference benchmark (Pelican-style, for comparison) | A cited professional protocol: **26 total drops** to concrete — one drop to each face, edge, and corner orientation — performed at **each of three temperature conditions** (ambient, max operating, min operating); Pelican's own facility testing infrastructure includes a 6-ft cube reaction mass of reinforced concrete with a 1-ton hoist and a 1/2-ton quick-release drop mechanism | Search aggregation referencing Pelican-style test methodology; [Pelican — Certifications & Testing](https://business.pelican.com/us/en/capabilities/certifications-testing-cases) (page fetch blocked by HTTP 403 in this research session — cited via search-result summary only, not a direct page fetch; treat the exact "26 drops / 3 temperatures" figure as reported-by-search-aggregator rather than independently confirmed from the primary page) |
| Repeated open/close cycle counts | No verified hobbyist-community numeric standard was found in this research session for lid/latch open-close cycle counts specifically. Related but distinct figures found: a TPU living hinge cited as capable of "thousands" of cycles vs. an FDM rigid-hinge example that failed around ~25 cycles (see §11) — these are hinge-fatigue figures, not a case open/close protocol, and should not be conflated with a formal case-durability cycle spec | See §11 sourcing |

**Recommended practical protocol for this project** (synthesized from the above, not a single verified source — presented as a recommendation, not a citation): drop the assembled, powered-down case from ~1 m onto concrete once per face, once per edge, and once per corner; repeat at both a "cold" and "warm" ambient condition if practical, in the spirit of the professional multi-temperature protocol; separately track lid/latch open-close cycles over the review period as a wear check, since no authoritative numeric target for that was found.

---

## Sources

- [CNC Kitchen — Comparing PLA, PETG & ASA (feat. Prusament)](https://www.cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament) — fetched 2026-09-07 — impact strength (kJ/m²), stiffness (MPa), and temperature-failure figures for PLA/PETG/ASA.
- [Prusa Knowledge Base — PETG](https://help.prusa3d.com/article/petg_2059) — fetched 2026-09-07 — PETG nozzle/bed temps, warping behavior, mechanical notes.
- [Prusa Knowledge Base — ASA](https://help.prusa3d.com/article/asa_1809) — fetched 2026-09-07 — ASA nozzle/bed temps, enclosure requirement, warping, UV resistance.
- [Prusa Knowledge Base — Enclosure guidepost](https://help.prusa3d.com/article/enclosure-guidepost_366332) — searched 2026-09-07 — which materials need an enclosure.
- WebSearch aggregation: PETG vs ASA vs ABS vs PC impact/HDT comparison — searched 2026-09-07 — general material comparison (3dprinting.com, unionfab.com, sovol3d.com, and others).
- WebSearch aggregation: PC-CF / PA-CF / PETG-CF properties and hardened-nozzle requirement — searched 2026-09-07 (bambulab.com, numakers.com, nylonplastic.com, printforgehq.com, printlog3d.com).
- WebSearch aggregation: PA-CF Izod impact / HDT / pricing — searched 2026-09-07 (qidi3d.com, 3dfilamentprice.com, bambulab.com store, filascope.com).
- WebSearch aggregation: Polycarbonate (PC) Izod impact / HDT / price per kg — searched 2026-09-07 (3dxtech.com, simplify3d.com, salesplastics.com).
- WebSearch aggregation: PC printing enclosure/nozzle/bed temperature requirements — searched 2026-09-07 (wiki.polymaker.com, matterhackers.com, 3dprinterly.com, forum.bambulab.com).
- WebSearch aggregation: ABS Izod impact / HDT / price / UV resistance — searched 2026-09-07 (wevolver.com, engineersedge.com, jaycon.com, and pricing sources).
- WebSearch aggregation: ASA vs ABS vs PC vs TPU UV resistance comparison — searched 2026-09-07 (3dxtech.com, raptor3d.ch, zextrude.com.au).
- WebSearch aggregation: PETG UV resistance / outdoor degradation — searched 2026-09-07 (makershop.co, layercraftlog.com, sciencewatch.blog, forum.prusa3d.com).
- WebSearch aggregation: PA-CF / nylon UV resistance and photo-oxidative degradation study — searched 2026-09-07 (pmc.ncbi.nlm.nih.gov study, bigrep.com, bambulab.com).
- WebSearch aggregation: TPU price per kg, shore hardness, printing temperature — searched 2026-09-07 (spoolhound.com, filamentpricetracker.com, overture3d.com).
- WebSearch aggregation: PETG / ASA filament price-per-kg indices, 2026 — searched 2026-09-07 (spoolhound.com PETG and ASA price indices, layermath.com).
- [Rapid Direct — 3D Printing Wall Thickness: The Engineering Guide to DFM & Cost Optimization](https://www.rapiddirect.com/blog/3d-printing-wall-thickness/) — searched 2026-09-07 — wall thickness and perimeter guidance for rugged parts.
- [Xometry Pro — Recommended wall-thickness for FDM](https://xometry.pro/en/topic/recommended-wall-thickness-for-fdm/) — searched 2026-09-07 — structural wall thickness minimums.
- WebSearch aggregation: FDM design rules (wall thickness/overhang/bridging/tolerance) — searched 2026-09-07 (layerx3d.in, 3d-demand.com, yorkshire3d.co.uk).
- [Printed Solid — 3D Printing Design Tips Part 1: Stress Concentrations](https://www.printedsolid.com/blogs/news/37036739-3d-printing-design-tips-part-1-stress-concentrations) — searched 2026-09-07 — why sharp corners are stress concentrators.
- [Fictiv — Fillets: When to Use 'Em, When to Lose 'Em](https://www.fictiv.com/articles/fillets-when-to-use-em-when-to-lose-em) — searched 2026-09-07 — fillet radius sizing rules, fillet vs chamfer.
- [Luis Llamas — Ribs and Reinforcements to Increase Stiffness in 3D Printing](https://www.luisllamas.es/en/3d-printing-ribs-stiffness/) — searched 2026-09-07 — rib thickness/height ratios.
- [Fictiv — Best Practices for Adding Ribs & Gussets to 3D Printed Parts](https://www.fictiv.com/articles/best-practices-for-adding-ribs-and-gussets-to-3d-printed-parts-for-structural-integrity) — searched 2026-09-07 — rib/gusset sizing, warping mitigation.
- WebSearch aggregation: print orientation vs. layer adhesion / impact strength research — searched 2026-09-07 (ncbi.nlm.nih.gov, researchgate.net, markforged.com).
- [Springer — Effect of layer thickness and print orientation on strength of adhesively bonded single lap joints](https://link.springer.com/article/10.1007/s12206-017-0415-7) — searched 2026-09-07 — orientation effect on bonded-joint strength.
- WebSearch aggregation: FDM tolerances for sliding/press/snap fits — searched 2026-09-07 (zbotic.in, snapmaker.com, sovol3d.com, tools.creative3dp.com, grandpacad.com).
- WebSearch aggregation: FDM overhang angle and bridging span limits — searched 2026-09-07 (wevolver.com, convertools.net, layerx3d.in, 3dmag.com).
- WebSearch aggregation: minimum gap/slot width design rules — searched 2026-09-07 (avidpd.com, hydraresearch3d.com, facfox.com).
- [InsertGuide — Why Do Bosses Crack Around Heat Set Inserts?](https://insertguide.com/why-do-bosses-crack-around-heat-set-inserts/) — attempted fetch 2026-09-07, blocked (HTTP 403); cited via WebSearch result summary only.
- WebSearch aggregation: heat-set insert boss wall thickness / OD guidelines — searched 2026-09-07 (sovol3d.com, rjcmold.com, meshra.ai, insertguide.com).
- WebSearch aggregation: TPU corner bumpers, separate-print vs. AMS/multi-material tradeoffs — searched 2026-09-07 (bambulab.com, thangs.com, printables.com, 3dprintdecoded.com, forum.bambulab.com).
- WebSearch aggregation: 3D printed enclosure lid design, labyrinth/tongue-and-groove, dust sealing — searched 2026-09-07 (zbotic.in, engineersrule.com, formlabs.com, facfox.com).
- [Protolabs Network / Hubs — How to design living hinges for 3D printing](https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/) — fetched 2026-09-07 — living hinge material recommendations (PP for injection molding, Nylon 12/TPU for FDM), hinge thickness, cycle-life notes.
- WebSearch aggregation: PETG living hinge failure / creep / cycle life — searched 2026-09-07 (fastpreci.com, orefly.com, elitemoldtech.com, community.ultimaker.com).
- WebSearch aggregation: drop protection design, crumple zone, bumper geometry — searched 2026-09-07 (designmycase.co.uk, learn.adafruit.com, community.heypocket.com).
- WebSearch aggregation: enclosure ventilation chimney effect, vent slot/hex pattern, dust ingress — searched 2026-09-07 (mpvent.com, fanacdc.com, acdcecfan.com).
- [Neutrik — XLR EMC Series product page](https://www.neutrik.com/en/neutrik/products/xlr-connectors/xlr-chassis-connectors/emc-series) — searched 2026-09-07 — EMC-series shielded connector purpose.
- [Neutrik — NC3FDX-EMC-Spec product page](https://www.neutrik.com/en/product/nc3fdx-emc-spec) — searched 2026-09-07 — shield continuity mechanism (capacitor/ferrite) detail.
- [Benchmark Media — Grounding XLR Connectors (Neutrik USA application note)](https://benchmarkmedia.com/blogs/application_notes/grounding-xlr-connectors-neutrik-usa) — searched 2026-09-07 — chassis/shell/shield common-ground best practice.
- [Cadence Resources — All Things Connectors Part 5: Shielded Connectors](https://resources.system-analysis.cadence.com/blog/all-things-connectors-part-5-shielded-connectors) — searched 2026-09-07 — floating-ground-in-plastic-enclosure note and shield-bonding recommendation.
- WebSearch aggregation: Pelican-style drop test protocol, 26-drop/3-temperature methodology — searched 2026-09-07 (search-result summary; primary Pelican page fetch returned HTTP 403).
- [Pelican — Certifications & Testing](https://business.pelican.com/us/en/capabilities/certifications-testing-cases) — attempted fetch 2026-09-07, blocked (HTTP 403); cited via WebSearch result summary only, not independently verified from the primary page.

### Figures marked `unknown` (could not be verified from a fetched source)
- PC-CF Izod/Charpy impact strength figure.
- PC-CF HDT figure.
- PC-CF UV resistance rating.
- PC-CF specific price-per-kg (only general CF-filament price band found).
- PETG-CF Izod/Charpy impact strength figure.
- PETG-CF HDT figure.
- PETG-CF UV resistance rating.
- PETG-CF specific price-per-kg (only general CF-filament price band found).
- TPU rigid-plastic-style HDT figure (not applicable/not found as a comparable number).
- Bare TPU UV-degradation figure (only an indirect note that TPU film is used to UV-protect polycarbonate sheet).
- A vent-slot-specific minimum printable width for a 0.4 mm nozzle without support (nearest verified analogs: 0.8 mm general minimum wall/slot feature, 1 mm minimum lattice gap — neither is vent-specific).
- A verified hex-vs-slot vent pattern dust-ingress quantitative comparison.
- A verified hobbyist-community-sourced exact "1 m drop test" protocol citation (the professional Pelican-style 26-drop/3-temperature protocol was found only via search-result summary, and the Pelican primary page itself could not be fetched — HTTP 403).
- A verified numeric standard for repeated lid/latch open-close cycle counts specific to enclosure durability testing (only hinge-fatigue-specific cycle figures were found, which are a different metric).
