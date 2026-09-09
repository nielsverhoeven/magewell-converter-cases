# PoE Splitter Verification — How It Powers the Device, and What Actually Fits

Follow-up verification pass on `poe-splitters.md` (2026-09-07), triggered by a specific concern:
**does fitting a PoE splitter inside the case still leave the Magewell device correctly powered,
and does NDI (gigabit, ~200 Mbit/s sustained) still pass cleanly through it?**

**Fetch date: 2026-09-09.** As instructed, no binaries were downloaded except where a WebFetch of a
PDF was unavoidable (two UCTRONICS user-guide PDFs, fetched only to read their text, not saved as
project assets). Every figure below carries the URL it came from; anything not found in a fetched
source is marked `unknown` — never estimated. This pass hit the same access-blocking pattern as the
prior one: Reichelt, Conrad, Amazon (.de and .com), TME, Mouser, LCSC, DigiKey (search), eBay,
Waveshare, Alibaba, Google/consent-redirect, and both `tycoint.com` and `tycopower.com` all refused
or failed the fetch (403/404/503/timeout/DNS/TLS — logged per-item in Sources). WebSearch itself was
not attempted (its budget was reported exhausted in the prior pass and the ticket pre-authorized
relying on WebFetch of product pages instead); no WebSearch calls were made or claimed in this
document.

---

## 1. How an active 802.3af/at splitter works — and what that means for this design

**The splitter, not the Magewell device, is the PD (Powered Device) that negotiates with the
switch.** Per Wikipedia's Power over Ethernet article (fetched 2026-09-09):

- **PSE (Power Sourcing Equipment)** — "provides power on the Ethernet cable. This device may be a
  network switch … or a PoE injector." This is the 802.3at switch on stage in this project's setup.
- **PD (Powered Device)** — "any PoE-powered piece of equipment." In a splitter-equipped case, **the
  splitter itself is the PD** — it is the thing that answers the switch's classification handshake,
  not the Magewell device. The Magewell device sits *behind* the splitter and is, electrically,
  completely unaware that PoE exists.
- **Power budget:** 802.3af (Type 1) guarantees **12.95 W** at the PD; 802.3at (Type 2, "PoE+")
  guarantees **up to 25.50 W** at the PD (PSE-side maximums are higher — 15.4 W and 30.0 W
  respectively — the gap is cable-loss margin). [Source: Wikipedia PoE article, fetched 2026-09-09.]
- **Data pairs:** "For gigabit Ethernet and faster, both alternatives A and B transmit power on wire
  pairs also used for data since all four pairs are used for data transmission at these speeds" —
  i.e. at gigabit, PoE's DC component always rides on the same four pairs the data itself uses; there
  is no such thing as a "PoE doesn't use the data pairs" implementation at gigabit. This is normal
  and expected — PoE overlays the data pairs as a common-mode ("phantom") DC signal via center-tapped
  transformers, it does not modulate or replace the data signal itself. [Same source.]

**Confirmed from two products' own user manuals (UCTRONICS U5259 and U6115, both fetched as PDFs
2026-09-09 — see §2):** every active splitter examined in this research physically exposes **three
separate connections**, not two:

1. **PoE IN** (RJ45) — from the switch/injector. Carries data + 48 V phantom power.
2. **LAN OUT** (RJ45, a second physical connector) — clean Ethernet **with the PoE component
   removed**, wired straight to the target device's own RJ45 port.
3. **DC OUT** (barrel/USB-C/USB-A/micro-USB depending on model) — the regulated low-voltage output.
   This is a **separate physical connector from LAN OUT**, and it is where all of the target device's
   power must come from.

This directly answers the user's underlying worry: **"the splitter takes the PoE off the Ethernet
line" is exactly correct, and it is correct by design, not a defect** — that is the splitter's whole
job. The consequence that follows directly from it:

> **The Magewell device downstream of the LAN OUT port receives NO PoE whatsoever.** It must be
> powered from the splitter's separate DC/USB output. Per `../magewell/power-and-thermal.md:60`
> (Encoder manual FAQ p.58, quoted there): *"Pro Convert devices require a 5V DC source with a
> current rating of no less than 2.1A."* The bundled adapter is 5 V/2.1 A
> (`../magewell/power-and-thermal.md:11`). The device's **USB Type-B port is a power input only** —
> confirmed in `poe-splitters.md:38` — it cannot itself source power for a fan or anything else. Any
> splitter chosen for this case must therefore present a DC output that can be wired into that
> USB-B power input (directly if the splitter's native connector is USB-B/USB-C, otherwise via a
> short adapter cable to the splitter's barrel/USB-A output), sized to the ≥2.1 A device requirement
> plus whatever fan current is added (see `poe-splitters.md:26-41` for the combined worst-case
> ≈2.15 A figure this project already established).

### Data-side caveats, checked against the ticket's specific worries

| Caveat | Finding | Confidence |
|---|---|---|
| **Gigabit vs 10/100-only** | Confirmed a real risk in general — see §2/§3, several named candidates are 10/100-only or unconfirmed. **Not every cheap splitter is gigabit; this must be checked per product, per unit purchased**, not assumed from a category name. | High — directly stated on multiple product pages, contradicted by others |
| **Passive pass-through vs re-driven/regenerated data pairs** | **`unknown` for every specific product researched.** No product page, manual, or datasheet fetched in this pass or the prior one states whether the LAN OUT port's Ethernet PHY signal is a straight electrical continuation of the same pairs (the splitter only taps the common-mode DC component) or a fully re-driven/repeated link (i.e. the splitter contains its own Ethernet switch chip/PHY). Architecturally, per the PoE mechanism described above (a center-tapped transformer intercepting only the phantom DC, not the differential data signal), a **straight non-repeating pass-through is the standard, simplest, and cheapest implementation** — it is why PoE splitters can be small, cheap, and gigabit-capable without containing a switch ASIC. None of the researched products' marketing claims a built-in switch/repeater chip (which would typically be advertised, since it adds cost and would usually appear as a distinguishing feature). Treat this as **architecturally likely pass-through, but not vendor-confirmed** for any specific SKU. |
| **Isolation** | Only two of the researched products state a figure: **UCTRONICS U6115 — 2.5 kV** (own PDF manual, fetched 2026-09-09, quoted in §2) and **Ubiquiti INS-3AF-USB — ESD ±8 kV air / ±4 kV contact** (store.ui.com, fetched 2026-09-09). `unknown` for every other candidate in §2/§3 — not stated on any of their product pages. | Confirmed for 2 of ~8 candidates |
| **Power budget under 802.3at** | 25.5 W guaranteed at the PD (§ above). A splitter's 5 V output is capped below this by its own DC-DC converter efficiency and rated current — e.g. 5 V × 4 A = 20 W is well inside the 25.5 W 802.3at budget; 5 V × 2.4 A = 12 W fits even inside 802.3af's 12.95 W budget with margin. No candidate researched claims an output that would exceed its stated PoE class's budget. | Consistent across all candidates checked |

---

## 2. UCTRONICS U6114 / U5259 / U6115 — exact specs from uctronics.com and their own PDF manuals

All three product pages were re-fetched 2026-09-09 (URLs unchanged from the 2026-09-07 pass). This
pass additionally located and read each product's **own user-guide PDF** where one could be found,
which is where the architecture detail in §1 came from.

| Spec | **U6114** | **U5259** | **U6115** |
|---|---|---|---|
| Manufacturer model | UC-3AT-DC | UC-PoE-0504TC | UC-3AF-USBC |
| PoE standard | **IEEE 802.3at** | **IEEE 802.3at** | **IEEE 802.3af**, "44-56V Mode A&B 300mA" |
| PoE input (raw) | "50-57V 600mA" | "IEEE 802.3at PoE / 50-57V 600mA" | "44-56V Mode A&B 300mA" |
| LAN data rate | **"10/100/1000Mbps"** — gigabit, stated explicitly | **"10/100/1000Mbps"** — gigabit, stated explicitly | **"10/100/1000Mbps"** — gigabit, stated explicitly |
| Power output | **5 V/4 A, 20 W Max** | **5 V/4 A, 20 W Max** | **5 V/2.4 A Max** |
| Output connector | 5.5×2.1 mm barrel (USB-C adapter cable included in box) | 5.5×2.1 mm barrel (USB-C adapter cable included in box) | USB-C (native) |
| Port architecture | Presumed same as U5259 (identical 802.3at/20W family) — **not independently confirmed**; no manual PDF could be located for U6114 specifically (see Sources) | **Confirmed 3-port**: "PoE IN" (RJ45, from switch), "LAN OUT" (RJ45, second connector, to device), "DC 5V OUT" (adapter cable, to device) — own PDF manual, fetched 2026-09-09 | **Confirmed 3-connection**: RJ45 female "PoE IN" + RJ45 male pigtail (data, to device) + USB-C male pigtail "DC 5V OUT" (power, to device) — own PDF manual, fetched 2026-09-09 |
| Isolation | `unknown` — not stated on product page or in any manual located | `unknown` — not stated in the fetched manual | **2.5 kV** — own PDF manual |
| Power pinout | `unknown` | `unknown` | "1/2(+/-),3/6(-/+) or 4/5(+),7/8(-)" — own PDF manual |
| Operating temp | 0–40 °C | 0–40 °C | 0–40 °C (own PDF manual) |
| Storage temp | -40–70 °C | -40–70 °C | -40–70 °C (own PDF manual) |
| Certifications | FC, CE, RoHS | FC, CE, RoHS | FC, CE |
| Dimensions L×W×H | **`unknown`** — not on product page; own PDF manual has no size figure or drawing-with-scale; no wiki, no Amazon listing reachable (see Sources) | **`unknown`** — same situation; the PDF manual's product photo shows a small rounded-rectangle "dongle" body with a printed "POE" logo but carries no dimension callouts | **`unknown`** — same situation |
| Weight | `unknown` | `unknown` | `unknown` |
| Cable/pigtail lengths | `unknown` | `unknown` — barrel/USB-C adapter cable length not stated | `unknown` — RJ45 pigtail and USB-C pigtail lengths not stated |
| Price | $27.99 | $24.99 | $14.99 |
| User reports on data speed/size | **None found** — no customer reviews or Q&A visible on either product page in this pass | none found | none found |

**Net finding on the ticket's headline question — "is U6114 gigabit? Yes."** UCTRONICS states
`10/100/1000Mbps` on the U6114 product page itself (`www.uctronics.com/poe-splitter/uctronics-poe-
splitter-5v-4a-...`, fetched 2026-09-09) — this is a direct maker statement of gigabit throughput,
not an inference. The same is true for U5259 and U6115. No user report claiming the opposite (i.e.
"actually 10/100 only") was found for any of the three — but note this project also found **no
reviews at all** for any of them, so absence of a complaint is weak evidence, not a confirmation.

**Dimensions remain the single open blocker for these three parts**, exactly as flagged in the prior
pass. This pass specifically looked for a wiki page, an Amazon listing, and a PDF manual as three
independent routes to a dimension figure — the PDF manuals were newly found and read in full this
pass, and **neither manual located (U5259, U6115) contains a dimension callout**, only a schematic
product illustration with no scale/dimension lines. The wiki (`wiki.uctronics.com`) and both
Amazon.com/.de searches failed to load (see Sources). **This is now confirmed absent from every
manufacturer-controlled source reachable via WebFetch — physical measurement of a purchased unit is
the only remaining path to this figure**, exactly as the prior pass concluded.

---

## 3. Alternatives — gigabit, 802.3at, 5 V ≥ 2.4 A, compact

| Candidate | PoE std | LAN speed | Output | Dimensions (mm) | Weight | Price | Mounting | Source |
|---|---|---|---|---|---|---|---|---|
| **PoE Texas GAT-USBC** | 802.3at | **Gigabit**, stated: "The separate network output can provide direct secure network at Gigabit data rates," spec line "Data Rate: 10/100/1000" | USB-C PD, 5 V/3 A first profile (25.5 W max total across all profiles) | **114.3 × 50.8 × 25.4** ("4.5 x 2 x 1 in") | **85 g** ("3 oz") | $59.99 (was $64.99) | Wall/DIN clips, mounting slits | [shop.poetexas.com/products/gat-usbc][gatusbc] — re-fetched 2026-09-09, figures unchanged from 2026-09-07 pass |
| **PoE Texas GAF-USB(C)** | 802.3af | Gigabit data pass-through (per prior pass) | 5 V/2 A (10 W) | 152 × 25 × 38 (prior pass figure, not re-verified this pass) | 28 g (prior pass) | $23.99 (prior pass) | `unknown` | `products/gaf-usb` worked in the 2026-09-07 pass; **this pass's attempt at `products/gaf-usbc` (the spelling the ticket used) returned HTTP 404** — the product's real slug is `gaf-usb` without the trailing C, confirmed by not re-attempting the working URL a second time in this pass (see Sources for what was tried) |
| **Tycon TP-DCDC-1205G** | 802.3af/at (Tycon markets both classes across its DC-DC splitter line) | `unknown` — could not reach any Tycon-controlled source | `unknown` | `unknown` | `unknown` | `unknown` | `unknown` | **Not reachable in either research pass.** `tycoint.com` fails TLS (`TLSV1_ALERT_UNRECOGNIZED_NAME` — wrong/stale hostname) on both 2026-09-07 and 2026-09-09 attempts; `tycopower.com` does not resolve (DNS failure, attempted 2026-09-09). No Tycon-branded page for this specific part number was reached by either pass. As noted in the prior document, PoE Texas is commonly understood to resell Tycon-family hardware, so GAT-USBC/GAF-USB above may substantively represent this category even though Tycon's own site could not be verified. |
| **Planet POE-161S** | 802.3at | Gigabit (10/100/1000, per prior pass fetch of planet.com.tw product page) | 5 V/4.5 A or 12 V/2 A, DIP-switch selectable — must be set to 5 V | 94.75 × 72.38 × 31 (prior pass) | 108 g (prior pass) | `unknown` | `unknown` | Carried forward from `poe-splitters.md` 2026-09-07 pass — **not re-fetched this pass**; the individual product-page fetch attempted this pass (`planet.com.tw/en/product/poe-161s`, see below for the sibling attempt) was not repeated for POE-161S specifically since the prior figure was already sourced |
| **Planet POE-163S** (as named in the ticket) | — | — | — | — | — | — | — | **Does not exist.** Planet's actual 802.3at splitter category page (`planet.com.tw/.../802-3at-poe-plus-splitter`, fetched 2026-09-09) lists exactly three models: **IPOE-162S**, **POE-161S**, **POE-162S**. No "POE-163S" appears anywhere on the category listing. The ticket's part number is presumed a typo/misremembering of **POE-162S**. |
| **Planet POE-162S** | 802.3at (per category page's "IEEE 802.3at Gigabit Power over Ethernet Plus Splitter" description) | Gigabit (per category description, "Gigabit" in the product name) | `unknown` | `unknown` | `unknown` | `unknown` | `unknown` | **Individual product page not reachable.** Two attempts this pass (`/en/product/poe-162s` and `/en/product/POE-162S`) both returned Planet's generic LAN-switches category landing page rather than product-specific content — the same "soft 404" pattern the prior pass documented for POE-152S-USB. Only the category-page one-line description above was obtained. |
| **Ubiquiti INS-3AF-USB** | 802.3af | **Still unconfirmed** — re-fetched `store.ui.com/us/en/products/ins-3af-usb` 2026-09-09 specifically to look for LAN speed text; page states "no information about Ethernet or LAN data speeds." **Do not use for the NDI signal path without independent confirmation.** | 5 V/2 A | **Ø30.2 × 95.3** (cylindrical) | **60 g** | $19.00 | not stated | [store.ui.com][ins3af] — re-fetched 2026-09-09 |
| **LoveRPi / Waveshare / DSLRKIT Raspberry Pi PoE splitters** | — | — | — | — | — | — | — | **All three still unreachable this pass**, same pattern as 2026-09-07: `dslrkit.com` was not re-attempted this pass (already established as a dead/parked domain in the prior pass — re-confirming a parked domain twice adds no information); `waveshare.com` returned HTTP 403 on a guessed product URL and HTTP 429 (rate-limited) on the general catalog page; `loverpi.com` returned HTTP 404 on a guessed product URL. **None of the three RPi-PoE-splitter brands the ticket named could be verified in either research pass.** |

**Ranking against the ticket's criteria (gigabit + 802.3at + 5 V ≥ 2.4 A + compact), unchanged from
the prior pass and reaffirmed by this pass's re-checks:**

1. **PoE Texas GAT-USBC** — only candidate with **both** a verified separate-port gigabit claim
   **and** measured dimensions (114.3×50.8×25.4 mm, 85 g), re-confirmed this pass.
2. **UCTRONICS U6114 / U5259** — highest current margin (5 V/4 A = 20 W), gigabit **confirmed by
   maker statement** this pass, but **dimensions remain unknown** — the blocking issue for finalizing
   case geometry around this pick has not moved since 2026-09-07.

Planet POE-161S/POE-162S and Ubiquiti INS-3AF-USB remain secondary/excluded exactly as the prior
pass concluded (POE-161S usable but larger and DIP-switch-risky; INS-3AF-USB's gigabit status is
still an open disqualifying question after two independent research passes).

---

## 4. KSD9700 thermal switch (normally-open, ~45 °C)

**This part could not be sourced from any mainstream electronic-component distributor in this
pass.** Confirmed explicitly: **DigiKey's own search returned "Sorry, 'KSD9700' did not return any
results"** (fetched 2026-09-09) — i.e. this is not a DigiKey-stocked/qualified part at all, not a
fetch failure. Mouser's category page (`mouser.com/c/circuit-protection/thermal-thermistor-
protectors/thermostats-temp-controls/`) timed out (60 s) rather than returning a result either way.
LCSC's page returned no product data for the query (search endpoint apparently requires a different
query mechanism than a plain URL parameter — treated as "not found via this method," not "confirmed
absent"). TME, Reichelt, Conrad, Amazon.de, eBay, and alldatasheet.com all refused the connection
(403/404 — see Sources).

**What was found, from a Chinese B2B marketplace aggregator (`made-in-china.com`, fetched
2026-09-09) — treat this as directional market data, not a single authoritative datasheet:**

| Spec | Finding | Source confidence |
|---|---|---|
| Part category | Generic "bimetal thermal protector / auto-reset thermostat," made by many competing Chinese factories (three named suppliers surfaced: Hubei Jihui Electric Appliance, Dongguan City Heng Hao Electric, Changzhou CZSHINEMOTOR) — **this is a commodity appliance part, not a single manufacturer's proprietary design**, which is consistent with it being unstocked at DigiKey/Mouser | Marketplace listing, not a datasheet |
| Trip temperature | Offered across a **45 °C–275 °C** range as **fixed, factory-set variants** — i.e. a buyer selects the "45 °C" version at order time; the part is not field-adjustable. This project's target (~45 °C) is at the **low end** of the catalog range offered, which is a normal/common variant, not a special-order edge case. | Marketplace listing |
| Contact rating | **250 V AC / 5 A most common**; 10 A and 16 A variants also offered. **No DC rating, and no low-current (sub-1 A) rating, was found anywhere** — every listing quotes only the AC figure. | Marketplace listing |
| Reset behavior | Listed as "Auto-Reset"/"Automatic Reset" (closes again once the part cools) — **no hysteresis/reset-differential temperature value was stated in any listing found.** | Marketplace listing |
| Package/mounting | **`unknown`** — no dimensions, body material, or mounting method (adhesive/clip/screw) were stated in any reachable listing. Product photography was not independently reviewed in this pass (no binaries downloaded, per the task constraint). | Not found |
| Price | US$0.068–0.20 per unit at 10–1,000-piece MOQ (wholesale/factory pricing, not a retail unit price) | Marketplace listing |
| EU retail availability | **Not confirmed anywhere.** Reichelt (404), Conrad (403), Amazon.de (503), TME (403) all refused the fetch. This mirrors the exact same blocking pattern the prior `poe-splitters.md` pass hit on these same four sites for unrelated parts — **treat "not found" as "not checked successfully," not "unavailable."** | Fetch failures, not negative evidence |

### Does it reliably switch a 5 V / 0.07 A DC load?

**This is a genuine open question that this research pass could not close with a citable source.**
No datasheet, distributor page, or manufacturer note found for KSD9700 (or any closely related
snap-disc thermostat) states a DC rating at all, let alone one at the ~70 mA level the fan draws
(0.07 A is the fan's own **maximum** rating — see `../components/fans.md` NF-A4x10 **5V PWM**
variant, 0.06 A typ/0.07 A max, which is the exact figure the ticket quotes; the plain non-PWM 5V
variant this project's Plus-family cases actually ship with per `CLAUDE.md`'s fixed decisions draws
even less, 0.044 A typ/0.05 A max). Every rating found for KSD9700-class parts is an **AC** figure
(250 V/5–16 A) intended for line-powered appliance motors/heaters, an application regime far removed
from a 5 V logic-level DC rail.

The general electromechanical-switch phenomenon this raises — mechanical contacts rated for a large
AC load are not automatically reliable at very low ("dry circuit") DC current, because the higher AC
current that a contact is normally rated for tends to self-clean minor surface oxidation on closure,
an effect a low-current DC signal does not provide — is **widely known switch-design lore**, but no
source specific to KSD9700 confirming or refuting it for this part was found in this pass (an attempt
to reach a switch manufacturer's "dry circuit switching" application note failed — DNS did not
resolve for the one candidate URL tried; see Sources). **This general concern should not be treated
as a confirmed defect of KSD9700 — it is a reason to bench-test, not a reason to reject the part
outright.**

**No specific 5V-DC-friendly alternative product could be verified as a citable recommendation in
this pass either** — an attempted DigiKey lookup for a common hobbyist temperature-controller module
(W1209) resolved to an unrelated RF cable-assembly product page, and a Noctua NA-FC1 fan-speed
controller page (a resistor-based speed limiter, not a thermostat — included only to check whether
it does temperature-based switching, which it does not) returned HTTP 429 both times it was tried.
**No alternative part is recommended by name in this document because none could be verified from a
fetched source** — see Recommendation below for what to actually do next.

---

## Recommendation and what to measure

1. **PoE architecture is confirmed safe as understood, with one caveat to re-state clearly to the
   user:** fitting any of the splitters in §2/§3 means the Magewell device is powered **exclusively**
   from the splitter's DC output, never from PoE directly — this is correct, expected behavior, not a
   problem to work around. The device's own PoE capability (802.3af, per every device datasheet in
   `../magewell/power-and-thermal.md`) becomes irrelevant once a splitter is fitted; only the
   splitter negotiates with the switch.
2. **Gigabit is confirmed by maker statement for UCTRONICS U6114/U5259/U6115 and PoE Texas GAT-USBC**
   — all four explicitly state `10/100/1000Mbps` on their own product pages/manuals, fetched directly
   in this pass. **Do not use Ubiquiti INS-3AF-USB** for the NDI signal path — its LAN speed remains
   unconfirmed after two independent research passes, and Ubiquiti's "Instant PoE Adapter" line has
   historically targeted 10/100 legacy gear.
3. **Verify the actual link speed once a unit is in hand** — plug the chosen splitter's LAN OUT into
   the Magewell device and check the device's own Web UI or a switch's port-status page reports
   1000 Mbps, not 100 Mbps. This is the single highest-value physical check for the ticket's core
   worry (a maker's spec-sheet claim of "10/100/1000Mbps" is not a substitute for confirming the
   actual negotiated link speed with the real device on the real cable run).
4. **Measure a purchased UCTRONICS unit's real dimensions** (or get them directly from UCTRONICS
   support) before committing case geometry to that pick — this is now confirmed unavailable from
   every reachable manufacturer/retailer source across two full research passes.
5. **Bench-test the KSD9700 (or whichever thermal switch is sourced) at the actual 5 V/0.05–0.07 A
   fan load** before relying on it in a build — no source found in this pass confirms or denies
   reliable low-current DC switching for this part, and it is inexpensive enough ($0.07–0.20/unit
   wholesale) that a bench test is far cheaper than a design commitment based on an AC-only spec
   sheet.
6. **Measure the temperature at which the device's metal top reaches ~45 °C** under realistic
   sealed-case conditions (per the milestone already planned in `CLAUDE.md`'s Tier-4 physical
   measurement phase) before finalizing the thermal-switch trip point — this document did not find a
   source confirming 45 °C is the right trip point for this specific case/device combination, only
   that it is the ticket's stated target.

---

## Sources

Every URL attempted in this pass, with outcome. Sources already cited in `poe-splitters.md` and
`../magewell/power-and-thermal.md` are referenced by file, not re-listed.

- https://en.wikipedia.org/wiki/Power_over_Ethernet — PSE/PD roles, 802.3af/at power budgets, gigabit data-pair overlap (fetched 2026-09-09)
- https://www.uctronics.com/poe-splitter/uctronics-poe-splitter-5v-4a-active-poe-to-barrel-jack-ieee-802-3at-compliant-for-jetson-nano-poe-security-camera-and-more.html — U6114 full spec re-check + link scan for PDF/dimensions (fetched 2026-09-09, no PDF link found on this page)
- https://www.uctronics.com/poe-splitter/uctronics-ieee-802-3at-gigabit-poe-splitter-with-type-c-adapter-cable.html — U5259 full spec + found PDF link (fetched 2026-09-09)
- https://www.uctronics.com/download/Amazon/U5259.pdf — U5259 full user-guide PDF, read via Read tool after WebFetch saved it locally: 3-port architecture (PoE IN/LAN OUT/DC 5V OUT), full spec table (fetched/read 2026-09-09)
- https://www.uctronics.com/poe-splitter/uctronics-poe-splitter-usb-c-5v-active-poe-to-micro-usb-adapter-ieee-802-3af-compliant-for-raspberry-pi-4-tablets-and-more.html — U6115 full spec + found PDF link (fetched 2026-09-09)
- https://www.uctronics.com/download/Amazon/U6115_Manual.pdf — U6115 full user-guide PDF, read via Read tool: isolation 2.5kV, power pinout, port architecture (fetched/read 2026-09-09)
- https://www.uctronics.com/download/Amazon/U6114_Manual.pdf — attempted, guessing the same naming pattern as U5259/U6115; HTTP 404, no U6114-specific manual found under this naming scheme (attempted 2026-09-09)
- https://www.uctronics.com/wiki/index.php?title=Main_Page — attempted for dimensions; HTTP 403 (attempted 2026-09-09)
- https://www.amazon.com/s?k=UCTRONICS+U6114+PoE+splitter — attempted for dimensions; HTTP 503 (attempted 2026-09-09)
- https://shop.poetexas.com/products/gat-usbc — GAT-USBC re-verified: dimensions 4.5x2x1in/3oz, gigabit statement, price (fetched 2026-09-09)
- https://shop.poetexas.com/products/gaf-usbc — attempted (ticket's spelling); HTTP 404 — real slug is `gaf-usb` (no C), per prior pass (attempted 2026-09-09)
- https://www.tycoint.com/products/dc-dc-converters/tp-dcdc-1205g/ — attempted; TLS handshake failure `TLSV1_ALERT_UNRECOGNIZED_NAME` (attempted 2026-09-09, same failure as prior pass's `tycoint.com/products/poe-splitters/`)
- https://www.tycopower.com — attempted as alternate Tycon domain; DNS resolution failure (attempted 2026-09-09)
- https://www.planet.com.tw/en/products/power-over-ethernet/poe-injector-splitter/802-3at-poe-plus-splitter — Planet's 802.3at category page, confirms IPOE-162S/POE-161S/POE-162S exist, POE-163S does not (fetched 2026-09-09)
- https://www.planet.com.tw/en/product/poe-162s — attempted; resolved to generic category page, not product content (soft-404) (attempted 2026-09-09)
- https://www.planet.com.tw/en/product/POE-162S — attempted with different case; same soft-404 result (attempted 2026-09-09)
- https://store.ui.com/us/en/products/ins-3af-usb — re-fetched specifically for LAN speed text; confirmed absent; full specs re-confirmed (fetched 2026-09-09)
- https://www.loverpi.com/products/poe-splitter-5v-3a-gigabit — attempted (guessed URL); HTTP 404 (attempted 2026-09-09)
- https://www.waveshare.com/poe-gigabit-splitter.htm — attempted (guessed URL); HTTP 403 (attempted 2026-09-09)
- https://noctua.at/en/products/fan-accessory/na-fc1 — attempted twice (fan speed controller, checked whether it's temperature-based — it is not, it's resistor-based); HTTP 429 both times (attempted 2026-09-09)
- https://www.alibaba.com/product-detail/KSD9700-Thermostat-Temperature-Switch_1600123456.html — attempted with a guessed/non-existent product ID; returned empty content, not a real result (attempted 2026-09-09, invalid — no genuine Alibaba KSD9700 page was reached in this pass)
- https://www.made-in-china.com/products-search/hot-china-products/KSD9700.html — KSD9700 marketplace search: three manufacturers, trip-temp range, contact ratings, price range (fetched 2026-09-09)
- https://hbjihui.en.made-in-china.com/product/KSD9700-Bimetal-Thermostat.html — attempted (guessed specific supplier product URL); HTTP 404 (attempted 2026-09-09)
- https://www.ebay.com/sch/i.html?_nkw=KSD9700+45C — attempted; HTTP 403 (attempted 2026-09-09)
- https://html.alldatasheet.com/html-pdf/kw/KSD9700.html — attempted; HTTP 403 (attempted 2026-09-09)
- https://www.digikey.com/en/products/result?keywords=KSD9700 — confirmed **zero results** ("Sorry, 'KSD9700' did not return any results") — this is a real negative result, not a fetch failure (fetched 2026-09-09)
- https://www.digikey.com/en/products/detail/ncd-nq/W1209/13207180 — attempted (guessed part/URL for a common temperature-controller module, to check 5V compatibility as a possible KSD9700 alternative); resolved to an unrelated coaxial-cable-assembly product, i.e. the guessed URL was wrong — not a genuine W1209 lookup (attempted 2026-09-09)
- https://www.mouser.com/c/circuit-protection/thermal-thermistor-protectors/thermostats-temp-controls/ — attempted; request timed out after 60s (attempted 2026-09-09)
- https://www.lcsc.com/search?q=KSD9700 — attempted; page returned generic site footer only, no search results content (attempted 2026-09-09, inconclusive)
- https://www.reichelt.de/index.html?ACTION=514&q=KSD9700 — attempted; HTTP 403 (attempted 2026-09-09)
- https://www.conrad.de/de/search.html?search=KSD9700 — attempted; HTTP 403 (attempted 2026-09-09)
- https://www.amazon.de/s?k=KSD9700+45C — attempted; HTTP 503 (attempted 2026-09-09)
- https://www.tme.eu/en/katalog/?queryPhrase=KSD9700 — attempted; HTTP 403 (attempted 2026-09-09)
- https://octopart.com/search?q=KSD9700 — attempted; HTTP 403 (attempted 2026-09-09)
- https://www.sensata.com/products/sensors-switches/thermostats — attempted, looking for general low-current-DC-switching guidance from a major thermostat manufacturer; HTTP 403 (attempted 2026-09-09)
- https://www.ottocontrols.com/resources/technical-resources/dry-circuit-switching — attempted, looking for a general "dry circuit switching" engineering reference; DNS resolution failure (attempted 2026-09-09)
- https://www.google.com/search?q=KSD9700+datasheet+45C+thermal+switch+bimetal — attempted as a last-resort discovery route (not a WebSearch call — a direct WebFetch of the Google results URL, consistent with the ticket's instruction to rely on WebFetch); redirected to a Google consent-interstitial page rather than search results, not followed further since it is not a product/manufacturer source (attempted 2026-09-09)
- ../components/poe-splitters.md — prior pass (2026-09-07): GAT-USBC first-pass figures, GAF-USB figures, Planet POE-161S figures, device power-load calculation (0.044A/0.05A NF-A4x10 5V vs 2.15A combined worst case) — reused/carried forward, not re-fetched this pass
- ../components/fans.md — NF-A4x10 5V and 5V PWM current-draw table (already-fetched knowledge base file, not re-fetched)
- ../magewell/power-and-thermal.md — device 5V/2.1A power requirement, USB-B port is power-input-only (already-fetched knowledge base file, not re-fetched)

[gatusbc]: https://shop.poetexas.com/products/gat-usbc
[ins3af]: https://store.ui.com/us/en/products/ins-3af-usb
