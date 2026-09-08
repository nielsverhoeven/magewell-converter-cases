# Design guidelines knowledge base

FDM enclosure design and thermal/cooling sizing reference for the Magewell Pro Convert case.
Fetched/searched 2026-09-07 — see `../components/sources.md` for the full URL list.

- **`fdm-rugged-enclosure-guidelines.md`** — material choice, wall/rib/fillet rules, tolerances,
  inserts, hinges, bumpers, ventilation, EMI grounding. Headline: **ASA** shell for UV/outdoor
  durability (PETG as the simpler no-enclosure alternative); avoid **PETG living hinges** — use a
  metal-pin or TPU hinge instead.
- **`thermal-guidelines.md`** — convection/fan-sizing math, vent placement, fan noise vs. venue
  ambient, USB/12V/PoE fan power. Headline: a 10W/15°C-ΔT case needs an **active fan ≥2.3–2.5 CFM
  (~4 m³/h)** free-air; prefer a **buck converter** over an LDO for 12V→5V fan power.
- **`../components/sources.md`** — consolidated source list for this directory and `../components/`.

---

## Known inconsistencies to resolve

These are figures for the *same* quantity that come out different across the five knowledge files.
The source files were **not edited** to fix them — resolve deliberately (re-fetch the blocked page,
pick one figure and note why, or measure directly) before relying on the number in a CAD/BOM
decision.

**None currently open.** The four items originally listed here (NF-A4x10 5V current, NF-A6x25 max
input power, NF-A4x20 ULNA rating, M3 insert hole diameter) were all resolved 2026-09-08 — see the
"Resolved" subsection below for what changed and why.

No inconsistency was found for **USB port current budget** — only `thermal-guidelines.md` §8 states
this figure (USB 2.0: 500mA / 5 unit loads; USB 3.0: 900mA / 6 unit loads, both per the USB-IF spec,
sourced from Wikipedia's USB 3.0 article), and no other file among the five gives a conflicting
number.

---

## Resolved (2026-09-08)

Rule applied throughout: **the file that cites the manufacturer's spec page wins.**

1. **NF-A4x10 5V current draw — and a direct fetch-status contradiction on the same URL.**
   `components/fans.md` had the real, directly-fetched Noctua-published figure (**0.044 A typ /
   0.05 A max**, 44–50 mA) while `design/thermal-guidelines.md` §8 used a **~120 mA** order-of-
   magnitude 12V→5V estimate and claimed its own fetch of the identical URL returned HTTP 429.
   **Change:** corrected `design/thermal-guidelines.md` §8's NF-A4x10 row, its accompanying caveat
   paragraph, its "figures marked unknown" list, and its Sources entry to cite `fans.md`'s real
   figure directly (`components/fans.md:22`). The HTTP 429 remark was not simply deleted — it's now
   framed as a separate, later fetch attempt from that document's own research pass (re-confirmed
   still blocked on 2026-09-07 while making this fix) that does not override `fans.md`'s earlier
   *successful* fetch of the same page, which is the authoritative account. `fans.md` itself needed
   no change — it was already correct per the "manufacturer-spec-page file wins" rule.

2. **NF-A6x25 max input power / non-existent variant name.** `design/thermal-guidelines.md` §7 and
   §8 both labelled this fan **"NF-A6x25 FLX"** — a name that does not appear anywhere in
   `fans.md`'s NF-A6x25 table (only 5V, 5V PWM, and 12V PWM exist there) — and §8 quoted **1.44 W**,
   matching neither of `fans.md`'s two real Noctua-published figures (1.3 W max for 5V, 0.96 W max
   for 12V PWM). **Change:** renamed the fan to **NF-A6x25 5V** in both §7 and §8 (its RPM/CFM/
   dB(A) figures match `fans.md:50` exactly), replaced 1.44 W with the real 5V figures — **0.187 A
   typ / 0.26 A max, 0.935 W typ / 1.3 W max** — and added the separate NF-A6x25 **12V PWM** figure
   (0.96 W max, `fans.md:52`) alongside it for contrast rather than conflating the two variants.

3. **NF-A4x20 ultra-low-noise (ULNA) 8.5 dB(A) claim.** Verified against `fans.md`: its NF-A4x20
   table documents only a standard Low-Noise Adaptor (12.2 dB(A)) for this frame size, no ULNA row.
   **Change:** attempted to settle this by fetching Noctua's own NF-A4x20 5V PWM and 12V PWM spec
   pages directly (2026-09-07) — both returned HTTP 429, same as the NF-A4x10 case above. Took the
   task's fallback option: `design/thermal-guidelines.md` §7 now carries a footnote marking 8.5
   dB(A) as **unconfirmed against a first-party Noctua source** — re-verified as still present on
   the already-cited QuietPC retailer listing (re-fetched 2026-09-07), but not corroborated by
   `fans.md` or a direct Noctua page. Effectively `unknown` at manufacturer level; the sourced
   retailer figure itself was kept rather than deleted, since it is still real, attributable data.
   `fans.md` was not changed — no ULNA figure was obtained to add to it.

4. **M3 heat-set insert hole diameter.** `components/fasteners-and-hardware.md` carries two
   disagreeing figures from different source families (~4.0 mm nominal, Ruthex/community; 4.24–
   4.30 mm, a third-party per-material CAD-pocket chart) — this is an inconsistency *within* that
   one file, not across files, so the "manufacturer-spec-page wins" rule doesn't cleanly apply
   (neither source is a manufacturer datasheet). **Change:** neither figure was deleted or picked as
   a winner; added a "Which figure this project uses" note at the top of §1 instead, pointing to
   this project's actual tie-breaker: the library default `MCC_INSERT_M3.hole_d = 4.0` in
   `lib/mcc/constants.scad`, calibrated for real ASA prints by the `insert-boss` coupon
   (`models/coupons/insert-boss.scad`, bore ladder 3.8–4.3 mm) rather than by trusting either
   knowledge-base figure blindly.
