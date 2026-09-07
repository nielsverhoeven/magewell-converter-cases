# Audio 3.5 mm / 6.35 mm (D-series)

Uses the standard D-series cutout — see `../d-series-cutout.md`. Flange 26 × 31 mm (confirmed
explicitly on NJ3FP6C's own page as "D Series (31 x 26 mm)").

## 6.35 mm (1/4") — confirmed

| Part | Description | Poles | Locking | Mating plug compatibility |
|---|---|---|---|---|
| **NJ3FP6C** | Locking 1/4" phone jack, D-size shell, nickel metal housing, silver contacts | 3-pole (stereo/TRS-capable) | Locking (secures against accidental disconnection) | "All mono and stereo plugs specified acc. EIA RS-453 (A-gauge)" — i.e. standard 6.35 mm plugs |

Downloads: technical drawing `nj3fp6c-1.pdf`, DXF `nj3fp6c-2.dxf`, STEP `nj3fp6c-3.stp` (all linked
from `https://www.neutrik.com/en/product/nj3fp6c`, individual media URLs not captured in this pass).

## 3.5 mm — does a D-size mini-jack exist?

**Not confirmed to exist.** This research pass checked Neutrik's "Plugs & Jacks" category page
(`https://www.neutrik.com/en/products/audio/plugs-and-jacks`) and found only category headers
(Plugs / Jacks / Discontinued) without a full product listing rendered through WebFetch, and no
3.5 mm-specific D-size product surfaced through any other page reached in this pass. Neutrik's
well-known D-size phone-jack product is the **6.35 mm NJ3FP6C** above; no equivalent 3.5 mm D-size
part was located.

**Recommendation**: treat "no 3.5 mm D-size jack" as the working assumption for this project, but
mark it as an **open question** — if a 3.5 mm connection is required (e.g. for an auxiliary audio
monitor jack), either (a) directly browse
`https://www.neutrik.com/en/products/audio/plugs-and-jacks` for a "Jacks" sub-listing that this pass
could not fully render, or (b) plan to panel-mount a non-Neutrik 3.5 mm jack with its own
(non-D-series) cutout.

## Price class

Not gathered in this research pass — open question.

## Open questions

- Full "Jacks" sub-category listing under Neutrik's Plugs & Jacks page (page rendered only
  top-level headers to this pass's WebFetch call — a follow-up fetch or manual browse is needed to
  be certain no 3.5 mm D-size part exists).
- NJ3FP6C depth-behind-panel (drawing not fetched in this pass, only the product description page).
- Mating cable connector part number for NJ3FP6C's locking mechanism (a matching locking 1/4" cable
  plug, if Neutrik sells one specifically keyed to the locking feature).
