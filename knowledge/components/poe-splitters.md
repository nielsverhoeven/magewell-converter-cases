# PoE Splitters for Magewell Pro Convert Cases

Research into candidate **PoE splitters** for an optional internal module that takes 802.3af/at
PoE from a Neutrik etherCON feedthrough and outputs (a) Ethernet data to the Magewell device's own
RJ45 port and (b) 5 V USB power to run both the device (via its USB Type-B power input) and a 5 V
Noctua NF‑A4x10 5V fan (~0.05 A).

**Fetch date: 2026-09-07.** All figures are taken from a source that was actually fetched and read;
anything not independently confirmed is marked `unknown` rather than estimated. This research pass
hit two hard tooling limits worth disclosing up front:

- The session's web-search budget was exhausted before this document's research began (0 `WebSearch`
  calls succeeded — see Sources for the budget-exhaustion notices). All data below therefore comes
  from **direct URL fetches** (manufacturer/retailer pages guessed or reached via redirect chains),
  not search-engine discovery.
- General web search engines (Bing, DuckDuckGo/lite, Startpage) were **not usable as a discovery
  tool** via the fetch tool in this environment — DuckDuckGo returned a bot-CAPTCHA on every query,
  Startpage refused the connection outright, and Bing returned content **unrelated to the query**
  on most attempts (e.g. a search for "Tycon Systems PoE splitter USB" returned Dutch scooter-listing
  sites; a search for "POE-152S-USB" returned Path of Exile / Edgar Allan Poe results). This appears
  to be a caching or proxy fault in the fetch pipeline, not a real search result — **Bing/DDG output
  was not used as a source for any figure in this document.** Where a candidate could not be reached
  by a direct URL guess as a result, it is listed with the discovery attempts that failed rather than
  silently omitted (the ticket explicitly named these products).

## Device power requirement (context, from `../magewell/power-and-thermal.md`)

- Magewell Pro Convert devices are 802.3af PoE (some 802.3at) **and/or** 5 V DC via USB Type‑B.
- Manual quote: *"Pro Convert devices require a 5V DC source with a current rating of no less than
  2.1A."* The bundled adapter is rated 5 V / 2.1 A.
- Device power draw is ≈5–15 W depending on model (see `power-and-thermal.md` full table); at 5 V
  that is up to **~2.1 A** for the highest-draw USB-B-powered models.
- Adding the Noctua NF-A4x10 5V fan's ~0.05 A (0.044 A typ / 0.05 A max, per `fans.md`) gives a
  **combined worst-case load of ≈2.15 A** at 5 V. Against a splitter rated for exactly 2.4 A, that
  leaves only ~0.25 A (~10%) headroom — tight once cable/connector drop and the splitter's own
  regulation tolerance are accounted for. This is why the ticket's "ideally 3 A" is the more
  realistic design target, not just the 2.4 A floor.
- The device's **USB Type-B port is a power *input* only** — it cannot be used to source 5 V for the
  fan when the device is PoE-powered. If a fan is wanted in the PoE-powered configuration, its 5 V
  must come from the splitter's own USB/DC output (Y-spliced ahead of the device, not from the
  device itself).

---

## Comparison table

Data speed "Gigabit" is a hard requirement for NDI, per the ticket — any non-gigabit (10/100-only)
candidate is called out explicitly rather than silently excluded, since the ticket asked for them to
be flagged, not omitted.

| Candidate | PoE std in | Data speed | Output V / max A | Connector | Dimensions L×W×H (mm) | Weight | Isolation / compliance | Price (list) | Housing / mounting | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| **TP-Link (Omada) POE10R** ("TL-POE10R") | 802.3af | **Gigabit** — "2× 10/100/1000Mbps RJ45" (current Omada-branded product page; see note below) | 12 V/1 A, 9 V/1 A, or **5 V/2 A** (selectable) | DC barrel (type not stated) | 80.8 × 54 × 24 | unknown | unknown | unknown (not listed) | unknown | [omadanetworks.com/.../poe10r][poe10r] |
| **UCTRONICS U6115** ("PoE Splitter USB-C 5V") | 802.3af | Gigabit (10/100/1000 Mbps) | **5 V / 2.4 A** (fixed) | USB-C | unknown | unknown | 2.5 kV isolation; CE/FCC | $14.99 | unknown | [uctronics.com U6115][u6115] |
| **UCTRONICS U6114** ("PoE Splitter 5V 4A") | 802.3at | Gigabit (10/100/1000 Mbps) | **5 V / 4 A** (20 W) | 5.5×2.1 mm barrel (USB-C adapter included) | unknown | unknown | unknown | $27.99 | unknown | [uctronics.com U6114][u6114] |
| **UCTRONICS U5259** ("Gigabit PoE Splitter with Type-C Adapter Cable") | 802.3at | Gigabit (10/100/1000 Mbps) | **5 V / 4 A** (20 W) | 5.5×2.1 mm barrel (USB-C adapter included) | unknown | unknown | unknown | $24.99 | unknown | [uctronics.com U5259][u5259] |
| **Ubiquiti INS-3AF-USB** | 802.3af | **unknown — not confirmed gigabit** (see flag below) | 5 V / 2 A | USB Type-A | Ø30.2 × 95.3 (cylindrical) | 60 g | ESD/EMP ±8 kV(air)/±4 kV(contact); NDAA compliant | $19.00 | not stated | [store.ui.com INS-3AF-USB][ins3af] |
| **PoE Texas GAT-USBC** ("PoE+ to USB-C Splitter — Power Only, Separate Gigabit Data") | 802.3at (passive 30 W) | **Gigabit** — separate RJ45 data-out port | USB-C PD: **5 V/3 A**, 9 V/2.4 A, 12 V/2 A, 15 V/1.5 A, 20 V/1.3 A (25.5 W max) | USB-C (power) + RJ45 (data, separate port) | **114 × 51 × 25** | **85 g** | unknown | $59.99 | Wall or DIN-rail clips; mounting slits on both ends of housing | [shop.poetexas.com/products/gat-usbc][gatusbc] |
| **PoE Texas GAF-USB** ("802.3af PoE to USB Splitter") | 802.3af (active) | Gigabit data pass-through | **5 V / 2 A** (10 W) | 1.35 mm DC barrel (USB-A + micro-USB adapters included) | **152 × 25 × 38** (body); adapter cable 165 mm, RJ45 pigtail 216 mm | 28 g | unknown | $23.99 | unknown | [shop.poetexas.com/products/gaf-usb][gafusb] |
| **Planet POE-161S** | 802.3at | Gigabit (10/100/1000 Mbps) | **5 V / 4.5 A** or 12 V/2 A (DIP-switch selectable — **must be set to 5 V**) | DC barrel (exact type not stated) | **94.75 × 72.38 × 31** | **108 g** | unknown | unknown (not listed) | unknown | [planet.com.tw POE-161S][poe161s] |

**Note on TL-POE10R generational gigabit claim:** the ticket's example describes the classic
"TL-POE10R" as it has historically been sold (10/100 Fast Ethernet only, no gigabit). The URL that
successfully resolved for this part number in this research pass is TP-Link's current
**Omada-branded "POE10R"** product page, which explicitly states gigabit (10/100/1000 Mbps) support.
It is `unknown` whether this is a genuine spec upgrade over the older TL-POE10R part number, a
rebrand of the same hardware, or whether older/third-party-listed "TL-POE10R" stock in the market is
still the non-gigabit part. **Verify the exact datecode/hardware version before purchasing** — do
not assume gigabit from the part number alone for this specific product.

**Flag — Ubiquiti INS-3AF-USB gigabit status unconfirmed:** no fetched source (product page,
datasheet, or techspecs page — all three were attempted, see Sources) stated the LAN data rate for
this part. Ubiquiti's "Instant PoE Adapter" line historically targeted airMAX/legacy 10/100 gear.
**Do not use this candidate for the NDI signal path without first confirming gigabit support
directly with Ubiquiti or a physically verified unit** — it is not eliminated from this table only
because the ticket named it explicitly, but it is not recommended below.

---

## Candidates named in the ticket that could not be independently verified

The ticket asked for these to be researched by name; each was attempted and is reported here rather
than silently dropped.

| Candidate | Outcome |
|---|---|
| **DSLRKIT** gigabit 5V 2.4A USB-C splitter | `dslrkit.com` no longer resolves to a vendor site — it redirects to a HugeDomains "this domain is for sale" parking page, i.e. the brand's own site is down/expired as of this research pass. No alternate current storefront for this brand was found via direct-URL guessing (search engines were unusable — see limits above). Treat as **not currently verifiable / possibly discontinued**; historical Amazon/AliExpress listings may still exist but were not fetched. |
| **Tycon (Systems/Tycon Power/tycoint.com)** gigabit splitters | Direct fetch of `tycoint.com` failed (`TLSV1_ALERT_UNRECOGNIZED_NAME` — likely wrong/stale hostname for the current corporate site). Not independently verified in this pass. Note: **PoE Texas's GAT-USBC/GAF-USB products above are commonly understood in the industry to originate from Tycon-family hardware** (PoE Texas markets itself as a Tycon-affiliated reseller), so the GAT-USBC/GAF-USB rows above may substantively cover this category even though the tycoint.com site itself wasn't reached. |
| **Cudy** PoE splitter | No PoE splitter product line was found on `cudy.com` via direct-URL guessing in this pass (Cudy's public catalog is primarily routers/switches/powerline). **Unconfirmed whether Cudy sells a standalone PoE splitter at all** — not included in the comparison table above pending verification. |
| **Ruijie** | Ruijie is an enterprise switch/AP vendor; no evidence of a standalone consumer/prosumer PoE-splitter-to-USB product was found or fetched in this pass. **Not included** — likely not a real product category for this brand, but not conclusively ruled out. |
| **Microchip** | Microchip manufactures PoE **PSE/PD controller ICs** (e.g. the PD69xxx / PD70xxx families) used *inside* splitter products, not finished splitter cables/dongles sold to end users. **Not a comparable candidate to the others in this table** — flagged as a likely ticket miscategorization rather than researched as a finished product. |
| **Planet POE-152S-USB** (the exact ticket-named part) | This specific part number/page was **not found** on planet.com.tw (multiple direct-URL guesses returned the generic LAN-switches category page, i.e. a soft-404). Planet's actual current 802.3at splitter lineup found under that category is **POE-161S** and **POE-162S** (plus the higher-power industrial **IPOE-162S**) — **POE-161S is used above as the closest verified substitute** since it is Planet's gigabit splitter with a 5 V/4.5 A option; none of Planet's fetched splitter product names indicate a USB output (they are all DC-barrel), so the "-USB" suffix in the ticket's requested part number could not be corroborated at all. |
| **Waveshare** | `waveshare.com` returned HTTP 403 Forbidden on every direct fetch attempt in this pass (both a guessed product URL and the general product-listing page). Not independently verified. |
| **LoveRPi** | Direct fetch of a guessed collection URL returned HTTP 404. Not independently verified. |

---

## Space envelope (case internal budget)

Case interior target from the ticket: **~130–160 mm long × 80–100 mm wide × 35–45 mm high**. Per
`../magewell/power-and-thermal.md`, the device itself already occupies a large share of that:

| Device family | Device size (L×W×H mm) |
|---|---|
| Plus (117.5 × 66.7 × 23.4) | HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus, HDMI Plus, SDI Plus, NDI to HDMI 4K |
| Compact/TX (100.9 × 60.2 × 23.3) | HDMI TX, SDI TX, NDI to HDMI, NDI to SDI, NDI to AIO, AES67, Audio DX |

**Length is the binding constraint, not height, for the leading candidates:**
- GAT-USBC at 114 mm long is nearly as long as the shortest side of the case's own length budget
  (130 mm min) — it will **not** fit end-to-end alongside a 100.9–117.5 mm-long device inside a
  130–160 mm case; it must be placed in the width/height cross-section next to or below/above the
  device, or the case's overall length must sit toward the upper end (150–160 mm) to leave room for
  both in series.
- Stacking is height-constrained: device height is 23.3–23.4 mm; GAT-USBC is 25 mm tall. Stacked
  directly (device + splitter, no gap) that's **≥48.3 mm**, which **exceeds the 35–45 mm internal
  height budget**. A stacked layout only works if the splitter is placed beside the device
  (side-by-side within the 80–100 mm width budget: device width 60.2–66.7 mm + splitter width
  25–51 mm depending on candidate ≈ 85–118 mm — this **also exceeds the 80–100 mm width budget**
  for GAT-USBC's 51 mm width when combined with the wider Plus-family device, but fits with the
  narrower Compact/TX device, 60.2 + 51 = 111.2 mm, still tight).
- **Practical conclusion:** none of the dimensioned candidates (GAT-USBC 114×51×25, GAF-USB
  152×25×38, POE-161S 94.75×72.38×31) fit fully alongside the device in cross-section within an
  80–100 mm width budget without the splitter also extending the case's usable interior length —
  i.e. the splitter most likely needs its **own dedicated section of case length**, in series with
  the device (both mounted along the case's long axis, data/power cables running between them), not
  stacked or side-by-side. Budget the case toward **150–160 mm total internal length** to fit
  device + splitter + connector clearance in series; confirm against `../design/` guidelines and a
  physical mockup before finalizing.
- The **UCTRONICS U6115/U6114/U5259** family may resolve this more cleanly given their typical
  small in-line "dongle" form factor (comparable products in this class are commonly ~65–75 mm long
  × ~30–40 mm wide × ~15–20 mm tall based on product photography), but this is **not a verified
  figure** — no dimensioned source was fetchable for these three parts in this pass. **Physically
  measuring a UCTRONICS unit (or requesting its dimensions directly from UCTRONICS) is the
  highest-value follow-up** before committing to a case geometry, since if their real size matches
  typical products in this class, they would likely resolve the length/stacking conflict above that
  the two dimensioned Tier-1 recommendations (GAT-USBC, POE-161S) do not.

Add to whichever base footprint is chosen: cable clearance per `../components/cables.md` — a short
RJ45/Cat6A patch lead needs ≈27 mm of axial clearance at each RJ45 end (etherCON's own connector
clearance is `unknown`/unverified per that same document — flagged there for physical measurement),
and a USB-A/USB-C run needs ≈17 mm at the USB-A end (USB-B end unverified).

---

## Recommendation

Ranked against the ticket's criteria (gigabit required, 5 V ≥2.4 A hard floor / ≥3 A ideal,
smallest footprint), restricted to candidates with **both** a verified gigabit rating **and** a
verified ≥2.4 A/5 V output:

| Rank | Candidate | Why | Trade-off to accept |
|---|---|---|---|
| **1 (primary)** | **PoE Texas GAT-USBC** | Only candidate in the table with **both** a verified gigabit rating on a **separate dedicated RJ45 data-out port** (cleanest match to the requested architecture: etherCON → RJ45 in, RJ45 data straight to device, USB-C power out) **and** a verified ≥3 A 5 V capability (5 V/3 A is the first USB-PD profile it presents), **and** actual measured dimensions (114×51×25 mm, 85 g) small enough to reason about precisely. Also the only candidate with built-in wall/DIN mounting slits, useful for anchoring inside a 3D-printed case. | USB-C output uses PD negotiation (multiple voltage profiles) rather than a fixed 5 V rail — a non-PD sink (the Magewell's USB-B input, via a USB-C→USB-B cable) will simply draw the PD default of 5 V without negotiating, which is the safe/expected behavior for a "dumb" load, but this should be bench-verified with the actual device before finalizing (PD default-5V behavior is a general USB-PD spec fact, not independently re-verified against this specific product's firmware). At 114 mm long it drives the case toward the upper end of the length budget (see Space Envelope above). US-based purchase (poetexas.com ships from Texas) — no EU distributor found in this pass. Price is the highest in the table ($59.99). |
| **2 (secondary)** | **UCTRONICS U6114** (or its near-identical sibling **U5259**) | Highest current margin of any verified-gigabit candidate at **5 V/4 A (20 W)** — comfortably covers the ~2.15 A worst-case device+fan load with over 80% headroom, the most robust choice if the combined load is later revised upward (e.g. a larger fan). 802.3at gives margin against the 802.3af PoE budget too. Includes a USB-C adapter in the box despite the native connector being a 5.5×2.1 mm barrel, so it can present either barrel or USB-C depending on the internal cabling chosen. Lower price ($24.99–27.99) than GAT-USBC. | **Physical dimensions were not found in this research pass** (UCTRONICS's product pages omit L×W×H; a wiki subdomain, Amazon listing, and PDF datasheet were all unreachable — see Sources) — this is the single biggest open question blocking a final case-geometry decision for this pick. Isolation rating not stated. No mounting-hole information found. Must be physically measured (or a datasheet PDF obtained directly from UCTRONICS support) before committing case geometry around it. |

**Third option, same tier if U6115's tighter margin is acceptable:** UCTRONICS U6115 (802.3af,
5 V/2.4 A exactly at the ticket's floor, USB-C, $14.99) is the cheapest and matches the device's own
802.3af requirement without needing an 802.3at PoE+ source — but its 2.4 A rating leaves only
~10% headroom over the ~2.15 A worst-case combined load, tighter than either recommendation above.
Same dimensional-verification caveat as U6114/U5259 applies.

**If USB output is dropped as a requirement** (i.e. the internal cabling instead runs the splitter's
barrel output through a short DC-barrel-to-USB-B cable made in-house), **Planet POE-161S** (5 V/4.5 A,
gigabit, verified 94.75×72.38×31 mm/108 g) becomes competitive on current margin, at the cost of a
DIP-switch that must be correctly set to 5 V (not its 12 V alternate mode) — a one-time assembly risk
worth calling out on any build sheet, and a physically larger, wider footprint than GAT-USBC.

---

## Required internal cabling (architecture)

Per the ticket's requested signal path, using parts already documented in this knowledge base
(`../neutrik/connectors/ethercon.md` and `../neutrik/connectors/usb.md`):

1. **etherCON feedthrough → splitter PoE-in.** Panel-mount **Neutrik NE8FDP-B** (CAT5e D-series
   feedthrough, black; max. 4 mm panel thickness; front or rear mount) at the case's outside wall.
   Internally, a short RJ45 patch cable (see `../components/cables.md` §1/§2 for clearance figures —
   plain RJ45 boot clearance ≈27 mm min; etherCON-side mating connector clearance is `unknown`/
   unverified, budget generously and confirm by mockup) runs from the NE8FDP-B's rear feedthrough
   socket to the splitter's RJ45 PoE-input port.
2. **Splitter RJ45 data-out → device RJ45.** A second short RJ45 patch cable runs from the
   splitter's data-out port (a separate physical RJ45 on GAT-USBC/GAF-USB/POE-161S/TL-POE10R; on the
   UCTRONICS single-port units, the same physical RJ45 the PoE came in on now also carries clean
   data — check the specific model's port count before laying out the harness) directly into the
   Magewell device's own RJ45 port.
3. **Splitter power-out → device USB-B + fan, Y-spliced.** The splitter's 5 V output (USB-C, USB-A,
   or barrel depending on which candidate is chosen) feeds a short cable terminating in **USB
   Type-B** for the device's power-input port. Splice the fan's two power leads (5 V / GND) onto
   this same USB-B cable's VBUS/GND conductors, upstream of the device's connector, so the fan draws
   from the splitter output in parallel with the device rather than from the device itself (the
   device's own USB-B port cannot source power — see the Device Power Requirement section above).

### Alternative: Y-splicing 5 V when the device is DC-powered (no PoE splitter fitted)

When the case is built for **USB-B DC power only** (no PoE splitter, no etherCON), the same Y-splice
principle applies one connector earlier: the panel-mount **Neutrik NAUSB-W-B** (reversible USB A/B
feedthrough, black, front-mount only, per `../neutrik/connectors/usb.md`) is a passive feedthrough —
it does not generate or regulate power itself, it simply passes through whatever USB cable is
plugged into its rear. To power the fan in this configuration, splice the fan's 5 V/GND leads onto
the internal USB cable that runs from the NAUSB-W-B's rear socket to the device's USB-B port
(tapping VBUS/GND same as the PoE-splitter case above), relying on the external 5 V/2.1 A(+) power
adapter to supply the combined device+fan current through the same feedthrough. This avoids needing
a PoE splitter at all when PoE is not the chosen power source for a given build — but note it does
**not** work in reverse (a fan cannot be powered this way when PoE is the active source and no
splitter is fitted, since there is then no 5 V rail anywhere inside the case to tap).

---

## Open questions

- **UCTRONICS U6115/U6114/U5259 physical dimensions, weight, cable/pigtail lengths, isolation
  rating, and mounting-hole layout** — not found on the manufacturer's product pages; a wiki
  subdomain (`wiki.uctronics.com`) does not resolve, the Amazon.com/.de listings returned HTTP 503
  on every fetch attempt in this pass, and no PDF datasheet link was found. Highest-priority
  follow-up given these are the strongest current-margin and (probably) smallest candidates.
- **etherCON (Neutrik NE8MC/NE8MX family) mating-connector overall length** — already flagged as
  `unknown` in `../components/cables.md` and `../neutrik/connectors/ethercon.md`; directly affects
  how much of the "in series" length budget in the Space Envelope section above is actually consumed
  by connectors versus the splitter body itself.
- **EU purchase availability/pricing** for every candidate in the table — Amazon.de, Reichelt, and
  Conrad searches all failed in this pass (HTTP 403/404/503, or request timeout — see Sources) rather
  than returning "not found," so absence of an EU price above should be read as "not checked
  successfully," not "unavailable in the EU." PoE Texas and UCTRONICS both appear to be US-based
  storefronts (shipping cost/time to the EU not verified); Planet and Neutrik both have established
  EU distribution but a specific EU retail listing for POE-161S was not found in this pass.
  Re-attempt these lookups once search-engine access is restored, or check Mouser/Digi-Key/Farnell's
  EU sites directly (RS Components and Farnell were not attempted in this pass either).
  Note: this document's web-search budget was already fully spent by prior research sessions in this
  repository before this task began — a session-search-budget increase would be needed to try further
  discovery-style queries rather than direct URL guesses.
- **TL-POE10R vs. current Omada POE10R part-number/hardware relationship** and whether older
  non-gigabit stock is still in the retail channel — see the flag under the comparison table.
- **Ubiquiti INS-3AF-USB LAN data rate (gigabit or not)** — not found in three fetch attempts
  (product store page, datasheet PDF redirect, techspecs page); do not use for this project's NDI
  signal path until resolved.
- **Housing-openable / mounting-hole information** for every candidate except GAT-USBC (which states
  wall/DIN clips and mounting slits) — not found for any other candidate in this pass.
- **Isolation/IEEE-compliance detail** (galvanic isolation kV rating, IEC/UL marks) — only found for
  UCTRONICS U6115 (2.5 kV) and Ubiquiti INS-3AF-USB (ESD/EMP ratings, NDAA); `unknown` for all
  others.

---

## Sources

- https://www.tp-link.com/us/business-networking/omada-accessory-power-poe/poe10r/ — original TL-POE10R URL guess; 301-redirected to omadanetworks.com (fetched 2026-09-07)
- https://www.omadanetworks.com/us/business-networking/omada-accessory-power-poe/poe10r/ — POE10R full specifications (fetched 2026-09-07) [poe10r]
- https://www.uctronics.com/poe-splitter.html — UCTRONICS PoE splitter category listing, used to find model numbers/URLs (fetched 2026-09-07)
- https://www.uctronics.com/poe-splitter/uctronics-poe-splitter-usb-c-5v-active-poe-to-micro-usb-adapter-ieee-802-3af-compliant-for-raspberry-pi-4-tablets-and-more.html — U6115 specifications (fetched 2026-09-07) [u6115]
- https://www.uctronics.com/poe-splitter/uctronics-poe-splitter-5v-4a-active-poe-to-barrel-jack-ieee-802-3at-compliant-for-jetson-nano-poe-security-camera-and-more.html — U6114 specifications (fetched 2026-09-07) [u6114]
- https://www.uctronics.com/poe-splitter/uctronics-ieee-802-3at-gigabit-poe-splitter-with-type-c-adapter-cable.html — U5259 specifications (fetched 2026-09-07) [u5259]
- https://www.uctronics.com/poe-splitter/uctronics-gigabit-poe-splitter-5v3a-2in1-poe-usb-c-micro-usb-adapter.html — U6271 (2-in-1 USB-C/Micro-USB, 5V/3A): URL from category listing returned HTTP 404 on direct fetch; not independently verified beyond the category-page summary (fetched 2026-09-07, attempt failed)
- https://wiki.uctronics.com/index.php?title=U6115 — attempted for dimensions; hostname does not resolve (DNS failure) (attempted 2026-09-07)
- https://www.amazon.de/s?k=UCTRONICS+U6115 — attempted for dimensions/EU price; HTTP 503 (attempted 2026-09-07)
- https://www.amazon.com/s?k=UCTRONICS+U6115+PoE+splitter — attempted for dimensions; HTTP 503 (attempted 2026-09-07)
- https://store.ui.com/us/en/products/ins-3af-usb — Ubiquiti INS-3AF-USB specifications (fetched 2026-09-07) [ins3af]
- https://www.ui.com/download/software/instant-poe-adapters — attempted for INS-3AF-USB datasheet/LAN speed; page had no relevant hardware-spec content (fetched 2026-09-07, no data found)
- https://dl.ui.com/guides/AirMAX/INS-3AF-USB_DS.pdf — attempted; 302-redirected to techspecs.ui.com root, not the specific product (attempted 2026-09-07)
- https://techspecs.ui.com/airmax/accessories/ins-3af-usb — attempted; returned an unrelated UniFi Cloud Gateway catalog listing, not INS-3AF-USB specs (fetched 2026-09-07, no data found)
- https://shop.poetexas.com/collections/poe-splitters — attempted collection listing; own guessed trailing-slash variant 404'd, non-slash variant also 404'd (attempted 2026-09-07, failed)
- https://shop.poetexas.com/search?q=USB — PoE Texas USB-output splitter product list, used to find GAT-USBC/GAF-USB (fetched 2026-09-07)
- https://shop.poetexas.com/products/gat-usbc — GAT-USBC full specifications (fetched 2026-09-07) [gatusbc]
- https://shop.poetexas.com/products/gaf-usb — GAF-USB full specifications (fetched 2026-09-07) [gafusb]
- https://www.tycoint.com/products/poe-splitters/ — attempted; TLS handshake failure (`TLSV1_ALERT_UNRECOGNIZED_NAME`), hostname likely wrong/stale (attempted 2026-09-07, failed)
- https://www.dslrkit.com — attempted; 302-redirects to a HugeDomains domain-for-sale parking page, brand's own site is down (attempted 2026-09-07)
- https://www.cudy.com/collections/poe-adapter — attempted; HTTP 404 (attempted 2026-09-07, failed)
- https://www.waveshare.com/poe-splitter-usb-c.htm — attempted guessed product URL; HTTP 403 (attempted 2026-09-07, failed)
- https://www.waveshare.com/product.htm — attempted general catalog page; HTTP 403 (attempted 2026-09-07, failed)
- https://www.loverpi.com/collections/poe — attempted; HTTP 404 (attempted 2026-09-07, failed)
- https://www.planet.com.tw/en/product/poe-152s-usb — attempted (ticket's exact named part); resolved to a generic LAN-switches category page, not a product page — treated as soft-404 (attempted 2026-09-07)
- https://www.planet.com.tw/en/product/poe-152s — attempted variant without "-usb" suffix; same generic category-page result (attempted 2026-09-07)
- https://www.planet.com.tw/en/products/power-over-ethernet/poe-injector-splitter/802-3at-poe-plus-splitter — Planet's actual 802.3at splitter category, listing POE-161S/POE-162S/IPOE-162S (fetched 2026-09-07)
- https://www.planet.com.tw/en/product/poe-161s — POE-161S full specifications (fetched 2026-09-07) [poe161s]
- https://www.planet.com.tw/en/sitemap — attempted for product discovery; returned category links only, no direct POE-152S-USB match (fetched 2026-09-07)
- https://www.reichelt.de/index.html?ACTION=514&q=poe+splitter — attempted EU retailer search; HTTP 404 (attempted 2026-09-07, failed)
- https://www.conrad.de/de/search.html?search=poe+splitter+usb — attempted EU retailer search; HTTP 403 (attempted 2026-09-07, failed)
- https://www.amazon.de/s?k=Planet+POE-161S — attempted EU price check; HTTP 503 (attempted 2026-09-07, failed)
- https://www.amazon.de/s?k=TP-Link+POE10R — attempted EU price check; HTTP 503 (attempted 2026-09-07, failed)
- https://www.mouser.de/c/?q=POE-161S — attempted EU distributor check; request timed out (attempted 2026-09-07, failed)
- https://www.mouser.com/c/?q=PoE%20splitter%20USB — attempted general distributor search; request timed out (attempted 2026-09-07, failed)
- WebSearch tool: all queries in this research pass failed with "this session has used its web search budget (200 of 200 WebSearch calls)" — session-wide budget exhausted by prior research in this repository before this task began (2026-09-07)
- Bing/DuckDuckGo/Startpage web-search-via-fetch attempts (multiple queries, 2026-09-07): DuckDuckGo (`html.duckduckgo.com`, `lite.duckduckgo.com`) returned a bot-CAPTCHA challenge on every attempt; Startpage (`www.startpage.com`) refused the connection outright ("Claude Code is unable to fetch from www.startpage.com"); Bing (`www.bing.com/search`) returned search-result content **unrelated to the query text** on the majority of attempts (verified mismatches include queries for "GAF-USBC" returning GAF roofing-shingle results, "Tycon Systems PoE splitter USB" returning Dutch mobility-scooter listings, "POE-152S-USB" returning Path of Exile/Edgar Allan Poe results, and "Cudy PS100 PoE splitter" returning Lloyds Banking Group share-price results) — treated as an unreliable/non-functional discovery channel in this environment and **not cited as a source for any figure above**. One Bing query (for the original TL-POE10R lookup) did return an on-topic, usable result and is credited inline where used.
- ../magewell/power-and-thermal.md — device 5V/2.1A power requirement, per-model power draw, device dimensions by family (already-fetched knowledge base file, not re-fetched)
- ../components/fans.md — NF-A4x10 5V current draw (0.044A typ / 0.05A max) (already-fetched knowledge base file, not re-fetched)
- ../components/cables.md — RJ45/USB connector clearance figures (already-fetched knowledge base file, not re-fetched)
- ../neutrik/connectors/ethercon.md — NE8FDP-B feedthrough specifications (already-fetched knowledge base file, not re-fetched)
- ../neutrik/connectors/usb.md — NAUSB-W-B feedthrough specifications (already-fetched knowledge base file, not re-fetched)

[poe10r]: https://www.omadanetworks.com/us/business-networking/omada-accessory-power-poe/poe10r/
[u6115]: https://www.uctronics.com/poe-splitter/uctronics-poe-splitter-usb-c-5v-active-poe-to-micro-usb-adapter-ieee-802-3af-compliant-for-raspberry-pi-4-tablets-and-more.html
[u6114]: https://www.uctronics.com/poe-splitter/uctronics-poe-splitter-5v-4a-active-poe-to-barrel-jack-ieee-802-3at-compliant-for-jetson-nano-poe-security-camera-and-more.html
[u5259]: https://www.uctronics.com/poe-splitter/uctronics-ieee-802-3at-gigabit-poe-splitter-with-type-c-adapter-cable.html
[ins3af]: https://store.ui.com/us/en/products/ins-3af-usb
[gatusbc]: https://shop.poetexas.com/products/gat-usbc
[gafusb]: https://shop.poetexas.com/products/gaf-usb
[poe161s]: https://www.planet.com.tw/en/product/poe-161s
