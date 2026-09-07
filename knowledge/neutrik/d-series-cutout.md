# Neutrik D-series panel cutout — specification

This is the single mechanical standard shared by (almost) every connector referenced in this
knowledge base: etherCON, USB, HDMI, BNC, XLR (incl. the DC-power XLR4), and the D-size phone jack
all mount into the **same cutout and screw pattern**. Confirmed by cross-referencing five independent
official Neutrik drawings (NE8FDP, NAHDMI-W, NBB75DFG, NAUSB-W, DBA-BL blanking plate) plus the
official XLR "D" series drawing hosted by RS Components — all agree on the numbers below. See
`sources.md` for URLs.

## 1. Geometry — what to cut

The cutout is a **single circular hole**, not a stadium/rounded-rectangle shape (this contradicts
some hobbyist/forum descriptions — the official drawings are unambiguous: the dimension is always
called out as "⌀", a diameter, with a "≥" minimum tolerance, not a two-axis rounded-rect callout).

**Two clearance holes** for the connector's mounting screws sit outside that circle, on a diagonal.

```
                    19.0 mm
              (hole-to-hole, X)
        ┌───────────────────────┐
        │                       │
     ●──┼───┐                   │        ● = mounting hole (screw clearance)
        │   │                   │        ○ = main circular cutout
        │   │      ○○○○○        │
  24.0  │   │    ○       ○      │  24.0 mm
  mm    │   │   ○    +    ○     │  (hole-to-hole, Y)
 (hole- │   │    ○       ○      │
  to-   │   │      ○○○○○        │
  hole) │   │                   │
        │   │                ┌──┼──●
        │   │                │  │
        └───────────────────────┘
```

- Main hole: circular, diameter **≥ 24.0 mm** (etherCON NE8FDP, XLR NC3xD) or **≥ 23.6 mm** (HDMI
  NAHDMI-W, USB NAUSB-W, BNC NBB75DFG) depending on the specific connector's shell OD. All drawings
  specify this as a **minimum** ("≥Ø…") — cutting it slightly larger is acceptable and safer for a
  3D-printed part than cutting it undersized.
  - **Recommendation for a generic/parametric OpenSCAD module that must fit any D-series connector:
    Ø24.2–24.4 mm nominal** (24.0 mm official minimum + typical FDM hole-shrink allowance of
    0.2–0.4 mm). If you know the exact connector in advance, you can go as small as its specific
    minimum (23.6 or 24.0 mm) plus your printer's own hole-undersize compensation.
  - Centered at the same point as the two mounting-hole pattern below.
- Two mounting-screw clearance holes, positioned diagonally opposite each other relative to the
  cutout center, at:
  - **±9.5 mm horizontally** (19.0 mm hole-to-hole) and **±12.0 mm vertically** (24.0 mm
    hole-to-hole) from the center of the main circular hole.
  - Hole diameter: **⌀3.1–3.5 mm depending on connector** (NAHDMI-W/NAUSB-W: ⌀3.1 mm min; NE8FDP:
    ⌀3.2 mm min; NBB75DFG/XLR female: ⌀3.4 mm min; XLR male/DBA-BL blanking plate: ⌀3.5 mm).
    **Recommendation: ⌀3.5 mm clearance hole** to safely fit the self-tapping screws Neutrik ships
    with any D-series connector, or to pass an M3 machine screw with a little clearance.
  - Orientation: the two holes are diagonal (top-left/bottom-right or top-right/bottom-left
    depending on which way the part is installed) — not top/bottom or left/right pairs. Follow the
    orientation shown on the specific connector's own drawing if the part is asymmetric (e.g. RJ45
    or BNC port not centered) — see individual `connectors/*.md` files.

### Coordinate description (for an OpenSCAD cutout module)

Origin at the cutout center (= geometric center of the 19×24 mm mounting-hole rectangle):

| Feature | X | Y | Diameter |
|---|---|---|---|
| Main cutout | 0 | 0 | ≥ 24.0 mm (24.2–24.4 mm recommended nominal) |
| Mounting hole A | −9.5 mm | +12.0 mm | ⌀3.5 mm recommended (3.1–3.5 mm per connector) |
| Mounting hole B | +9.5 mm | −12.0 mm | ⌀3.5 mm recommended |

A minimal parametric module would therefore need exactly three parameters beyond the standard ones:
`cutout_d` (default 24.3), `hole_d` (default 3.5), and the fixed `19 × 24 mm` hole pitch (this pitch
is NOT connector-specific — treat it as a constant of the D-series standard).

## 2. Outer flange / housing footprint

Confirmed identical across every connector drawing examined: **26.0 mm wide × 31.0 mm tall**,
rectangular with rounded corners, corner radius **R3.5 mm** (from the DBA-BL blanking-plate
drawing). Tolerance band is roughly +0.1/−0.2 mm on width and +0.1/−0.3 mm on height depending on
part revision — negligible next to normal 3D-print clearance allowances.

This is the minimum flat, unobstructed panel area you must reserve around each cutout (see
`placement-and-depth.md` for spacing between adjacent connectors).

## 3. Panel thickness support

No single number applies to the whole family — it is connector-specific:

| Source | Panel thickness |
|---|---|
| General D-series page (XLR chassis connectors) | 1–3 mm, countersunk mounting holes for M3 bolts/rivets, or M3-tapped-thread shell variant available |
| NE8FDP (etherCON feedthrough) | max. 4 mm |
| NAHDMI-W (HDMI feedthrough) | max. 2 mm (front **or** rear mounting) |
| NE8FDY-C6 (etherCON CAT6 IDC) | max. 3 mm |
| NBB75DFG (BNC) | not stated on datasheet; front-mount only — treat as ≤ 3 mm pending drawing confirmation (**open question**) |
| NAUSB-W (USB) | not stated on datasheet; front-mount only — treat as ≤ 3 mm pending drawing confirmation (**open question**) |

**For a 3D-printed case wall, design the connector-mounting boss/wall thickness at the cutout to
2.0–3.0 mm** to stay safely within every connector's supported range (etherCON tolerates up to
4 mm, but HDMI is capped at 2 mm — if you need to mix connector types in one uniform wall thickness,
2 mm is the safe common denominator; verify against `connectors/hdmi.md` before finalizing).

## 4. Mounting hardware

- Neutrik ships **self-tapping mounting screws** with front-mount D-connectors that thread directly
  into the two ⌀3.1–3.5 mm holes in a thin metal or plastic panel (no nut needed) — description
  confirmed on NE8FDP and DBA-BL product pages ("mounting screws included").
- For rear-side fixing (e.g. when front access to the screw heads is impossible, or to add a nut
  instead of relying on self-tapping bite in a 3D-printed panel), Neutrik sells the **MFD** — "the
  fixing plate with M3 thread offers efficient and ease mounting of all D-sized chassis connectors
  by M3 screws," fastened with **two M3 screws** (source: Neutrik MFD page + Elite Core Audio
  distributor page). This is the recommended approach for a 3D-printed case: tap or heat-set an M3
  insert at each of the two hole positions, or use the MFD plate against the inside face if you want
  a captured nut plate instead of threading straight into printed plastic.
- Screwdriver: Neutrik's own XLR-family documentation references a "00" flathead screwdriver
  (part # SD-1) for connector insert/shell assembly — not relevant to panel mounting itself.

## 5. Front-mount vs. rear-mount variants

"Front mount" = connector flange sits against the front (outward-facing) side of the panel, screw
heads accessible from outside. "Rear mount" = flange sits against the inside face, screws accessed
from inside the enclosure (or via the MFD plate). Support varies by connector:

| Connector | Front mount | Rear mount | Notes |
|---|---|---|---|
| NE8FDP (etherCON feedthrough) | Yes | Yes | Both variants shown on the official drawing with slightly different overall depth (34.55 mm front vs. 36.3 mm rear-fixed) — see `placement-and-depth.md` |
| NAHDMI-W (HDMI) | Yes | Yes | Both shown, max. 2 mm panel thickness applies to both |
| NE8FDY-C6 (etherCON CAT6 IDC) | Yes | Yes | max. 3 mm panel thickness |
| NAUSB-W (USB) | Yes | No | Datasheet states "Front mounting" only |
| NBB75DFG (BNC) | Yes | No | Datasheet states "Front mounting" only |
| XLR D-series (NC3xD-H/V/L) | Yes | Optional via MFD | H/V variants are PCB-mount; L (solder-cup) variants typically front-mount with self-tapping screws, or rear-mount via MFD |

## 6. "A-series" / universal-D notes

The ticket asked about "A-series"/universal-D differences. Across all research performed here,
Neutrik's own materials consistently call this **"D-shape"**, **"D-size"**, or **"D sized 24 mm
panel cutout"** — no separate "A-series" cutout standard was found for these connector families
(XLR, etherCON, USB, HDMI, BNC, D-SUB). **Open question**: if "A-series" refers to something else in
Neutrik's naming (it does not appear in any product page, category page, or drawing fetched in this
research pass), flag it back to the requester for clarification — it may be a mix-up with a different
manufacturer's or a different Neutrik series' naming (e.g. XLR "A-series" round chassis, which is a
*different*, non-D-shaped standard entirely, used by non-D-housing XLR chassis connectors like
NC3FAH2 etc.). Do not assume compatibility between "A-series" round XLR chassis and the D-shape
cutout described in this document.

## 7. Variants noted but not dimensionally verified here

- **DBA-BL / DBA-BL-B** blanking plate: dimensions fully captured (see
  `connectors/blanking-and-caps.md`); black variant assumed to share identical mechanical dimensions
  (only a color/material difference) — not independently confirmed for -B, low risk.
- **"D-size with wider flange"**: no such variant was surfaced in this research pass. Not found on
  any Neutrik category or product page. Treat as **unconfirmed / open question**.

## Open questions

- Exact panel-thickness rating for NBB75DFG and NAUSB-W (datasheets omit it; would require reading
  the dimensioned drawing's side-view panel schematic more closely, or a direct Neutrik query).
- Whether a "D-size with wider flange" variant genuinely exists (not found).
- Whether "A-series" is a real, distinct Neutrik cutout standard relevant to this project, or a
  misremembering of the round (non-D) XLR chassis series.
