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

1. **NF-A4x10 5V current draw — and a direct fetch-status contradiction on the same URL.**
   `components/fans.md` records `https://www.noctua.at/en/products/nf-a4x10-5v/specifications` as
   successfully fetched, giving a real Noctua-published current of **0.044A typ / 0.05A max**
   (44–50 mA). `design/thermal-guidelines.md` §8 cites the **identical URL** as returning **HTTP
   429** on every attempt, treats the real figure as unverified, and instead estimates **~120 mA**
   by scaling the fan's 12V power rating down to 5V (explicitly flagged there as an
   order-of-magnitude, non-vendor estimate). The two documents disagree by roughly **2.4–2.7×** on
   the same physical quantity, and disagree on whether the source page was even reachable.
   **Action:** trust `fans.md`'s directly-fetched 44–50 mA figure over `thermal-guidelines.md`'s
   §8 estimate for NF-A4x10-class USB power-budget planning; re-derive the rest of §8's per-fan 5V
   current table from `fans.md`'s real 5V-SKU figures where a matching row exists, rather than the
   12V-power-scaling method.

2. **NF-A6x25 max input power.** `components/fans.md` gives two Noctua-published max-power figures
   for this frame size: **1.3W** (5V variant) and **0.96W** (12V PWM variant, current draw itself
   marked `unknown`/typ). `design/thermal-guidelines.md` §8 gives a third figure, **1.44W**,
   attributed to "NF-A6x25 FLX" (implied 12V) via a QuietPC listing — a model/variant name that does
   not appear as a row in `fans.md`'s NF-A6x25 table at all (fans.md has no 12V FLX 3-pin variant for
   this frame size, only 5V, 5V PWM, and 12V PWM). None of the three power figures match.
   **Action:** confirm which specific NF-A6x25 SKU thermal-guidelines.md's 1.44W figure actually
   describes before using it for a 12V power budget; fans.md's own 12V PWM row (0.96W max) is the
   more traceable Noctua-sourced figure for a 12V A6x25 fan.

3. **NF-A4x20 ultra-low-noise rating.** `design/thermal-guidelines.md` §7 cites an **8.5 dB(A)**
   Ultra-Low-Noise-Adaptor (ULNA) figure for "NF-A4x20 FLX." `components/fans.md`'s NF-A4x20 table
   only documents a standard Low-Noise Adaptor (12.2 dB(A)) for this frame size — it does not list a
   ULNA option for NF-A4x20 anywhere (ULNA only appears there for the NF-A8 FLX). Minor/lower
   priority, but worth confirming a NF-A4x20 ULNA accessory actually exists before quoting 8.5 dB(A)
   in a design decision.

4. **M3 heat-set insert hole diameter** (flagged here for visibility even though it's an
   inconsistency *within* a single file, `components/fasteners-and-hardware.md`, not across files):
   that file itself carries two different hole-diameter figures from two different source families —
   a **~4.0mm nominal** figure (Ruthex/community consensus, corroborated across several
   retailer/forum sources) vs. a **4.24mm** PLA CAD-pocket figure from a third-party per-material
   chart (tools.creative3dp.com), with ABS/ASA/PC running 4.29–4.30mm on that same chart. The file
   already flags this itself and recommends printing a hole-diameter test coupon rather than trusting
   either number blindly — repeated here because it matches the class of figure this consistency
   pass was asked to check.

No inconsistency was found for **USB port current budget** — only `thermal-guidelines.md` §8 states
this figure (USB 2.0: 500mA / 5 unit loads; USB 3.0: 900mA / 6 unit loads, both per the USB-IF spec,
sourced from Wikipedia's USB 3.0 article), and no other file among the five gives a conflicting
number.
