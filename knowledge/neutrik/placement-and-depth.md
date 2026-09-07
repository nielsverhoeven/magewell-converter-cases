# Placement, spacing, and depth clearance

## 1. Depth behind panel — summary table

All figures are **overall connector depth**, measured from the front flange face to the connector's
rearmost point, taken directly off official Neutrik dimensioned drawings (see `sources.md`). This is
the number to use as "how far this connector's own body sticks into the case" — it does **not**
yet include the internal patch cable's mating plug or bend radius (§3 below).

| Connector | Part | Depth behind panel | Mount variant | Source |
|---|---|---|---|---|
| etherCON (CAT5e feedthrough) | NE8FDP | **34.55 mm** | front-mount | drawing ST-NE8FDP |
| etherCON (CAT5e feedthrough) | NE8FDP | **36.3 mm** | rear-fixed | drawing ST-NE8FDP |
| HDMI feedthrough | NAHDMI-W | **40.65 mm** | front-mount | drawing doc 20003491 rev B |
| HDMI feedthrough | NAHDMI-W | **40.2 mm** | rear-fixed | drawing doc 20003491 rev B |
| USB feedthrough | NAUSB-W | **40.55 mm** | front-mount only | drawing ST-NAUSB-W |
| BNC feedthrough, 75 Ω | NBB75DFG | **34 mm** | front-mount only | drawing ST-NBB75DFG (cross-checked vs. its DXF) |
| XLR (3-pole, solder/PCB, non-feedthrough) | NC3FD-H / NC3FD-V / NC3MD-H / NC3MD-V | **21.7 mm** | both | Neutrik "D" series drawings 3102 St 10 01/39/08/38 |
| XLR4 DC power (solder cups) | NC4FD-L-1 / NC4MD-L-1 | **~21.7 mm (estimated)** | front (or rear via MFD) | **not independently drawn** — estimated from the mechanically similar 3-pole "L" solder-cup family; open question |
| BNC isolated | NBB75DFI | **~34 mm (estimated)** | front-mount only | not independently drawn; assumed identical to NBB75DFG; open question |
| Blanking plate | DBA-BL | **3.2 mm** (flat cover, not a feedthrough) | n/a | drawing ST-DUMMY_COVER |

**Design implication**: if the case wall sits at the panel plane and every connector needs to clear
the same internal depth, **budget at least ~41 mm of clear internal depth behind any D-series cutout
that might host HDMI or USB**, and ~35–37 mm if only etherCON/BNC/XLR connectors are used. This is
the connector body alone — see §3 for the additional clearance the internal patch cable needs.

## 2. Minimum center-to-center spacing for multiple D-connectors

**No official Neutrik "D-series multi-gang spacing" drawing was found and verified with hard numbers
in this research pass** — the NZPFD/NZPF1RU/NZPF3RU panel-frame family investigated turned out to be
specific to **opticalCON**, not a generic multi-D spacing reference, and its assembly-instruction PDF
had no numeric dimensions in the pages read. Treat the following as an **engineering
recommendation derived from the confirmed flange size**, not a sourced Neutrik spec:

- **Flange footprint is 26 mm (W) × 31 mm (H)** (confirmed, see `d-series-cutout.md`). Adjacent
  flanges must not overlap, and there must be enough flat panel material between cutouts for
  structural strength (particularly relevant for a 3D-printed wall, which is weaker than sheet
  metal) and for a screwdriver/driver bit to reach each connector's two diagonal mounting screws
  without fouling its neighbor.
- **Recommended minimum center-to-center spacing**:
  - Horizontal (connectors side by side): **≥ 30–32 mm** (26 mm flange + 4–6 mm keep-out web)
  - Vertical (connectors stacked): **≥ 35–38 mm** (31 mm flange + 4–7 mm keep-out web)
  - Increase the web further (to ~6–10 mm) if the wall is thin (≤2.5 mm) and you're relying on the
    surrounding plastic for stiffness with no internal rib/gusset behind it.
- **Weak corroborating data point** (not authoritative — third-party product, not a Neutrik spec):
  Penn-Elcom's punched 1U rack panel for 16 D-series connectors implies roughly **28 mm** average
  horizontal pitch across a 19" rack width; their 8-way and 24-way panels are consistent with a
  pitch in the high-20s to low-30s mm range. This aligns with, but does not independently verify
  beyond, the flange-derived recommendation above.

**Open question**: if a tighter, Neutrik-authoritative multi-gang spacing figure is required (e.g.
for a genuinely space-constrained case), request or locate Neutrik's own multi-connector panel
drawings (search terms: "NPPL", generic "D-panel", or contact Neutrik directly) — this was not found
in this pass.

## 3. Total depth needed: connector + internal patch cable clearance

Every connector in this family except the blanking plate is a **feedthrough** design — a short
internal patch cable/plug connects to the connector's rear-facing port, which then needs its own
depth plus a cable bend radius behind that. **Exact Neutrik-published boot/plug lengths were not
found in this research pass** for any of the mating cable connectors (NE8MX, NE8MX6, NBNC75BLP9X,
etc. — their datasheets give cable OD range and electrical specs, not a boot/plug overall length).
Treat the following as **general engineering guidance, not a sourced dimension**:

| Feedthrough connector | Connector depth (sourced) | Recommended additional clearance for mating plug + cable bend (engineering estimate, not sourced) | Suggested total internal depth to budget |
|---|---|---|---|
| NE8FDP (etherCON, RJ45) | 34.55–36.3 mm | ~20–25 mm (a standard RJ45 plug + Neutrik NE8MX boot is a rigid ~25–30 mm assembly that then needs room to curve away) | **~55–65 mm** |
| NAHDMI-W (HDMI) | 40.2–40.65 mm | ~25–35 mm (HDMI plugs are notably long, 20 mm+ before the cable exits, plus stiff cable requiring a wider bend radius than Cat5e/coax) | **~65–75 mm** |
| NAUSB-W (USB A/B) | 40.55 mm | ~15–20 mm (USB plugs are relatively short/compact) | **~55–60 mm** |
| NBB75DFG (BNC) | 34 mm | ~15–20 mm (BNC bayonet plug body ~20–25 mm, coax has a comparatively generous minimum bend radius — budget accordingly for the specific cable, e.g. Belden 1505A's bend radius) | **~50–55 mm** |

**These "suggested total internal depth" figures are conservative planning numbers for early case
layout, not a substitute for a real mechanical mock-up.** Before finalizing the case depth, either
(a) get the exact mating-plug dimensions from the specific patch cable to be used, or (b) physically
mock up the tightest connector (HDMI) with the actual cable intended for the build.

## 4. Grounding — quick reference

See `connectors/bnc-sdi.md` §"Grounding" for the full explanation. Summary:

- **NBB75DFG** = grounded (shell bonded to chassis) — default choice for a single BNC/SDI run.
- **NBB75DFI** = isolated — use when multiple BNC connectors share one metal/conductive panel and
  ground-loop/common-mode noise between them is a concern.
- **NAHDMI-W** ships with its shield grounded to chassis by default, with a **removable grounding
  tab** if an isolated/floating shield is needed.
- The 3D-printed case itself is non-conductive, so "chassis grounding" here only matters if/when a
  conductive shield, EMI gasket, or metal insert is added to the case — otherwise all these
  connectors' shells are electrically floating relative to each other regardless of the
  grounded/isolated distinction, since there's no continuous conductive panel tying them together.
  Flag this to the design team: **the grounded/isolated distinction is most relevant if this
  project later adds a conductive (metal-coated, foil-lined, or metal-inlay) panel** — for a plain
  PETG/PLA/ABS case it's a smaller concern.

## Open questions (carried from connector-specific files)

- Real multi-gang D-series spacing drawing from Neutrik (not found; current spacing guidance is
  derived from flange size + third-party rack-panel products, not an official spec).
- Exact boot/plug lengths for NE8MX, NE8MX6, NBNC75BLP9X, and any HDMI/USB cable assemblies planned
  for internal patch cables.
- Depth-behind-panel for NC4FD-L-1/NC4MD-L-1 and NBB75DFI (estimated by analogy, not independently
  drawn).
