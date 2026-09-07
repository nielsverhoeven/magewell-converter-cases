# BNC / SDI, 75 Ω (D-series)

Uses the standard D-series cutout — see `../d-series-cutout.md`. Flange 26 × 31 mm.

## Chassis (panel-mount) connectors

| Part | Description | Grounding | Mount | Depth behind panel | Signal types |
|---|---|---|---|---|---|
| **NBB75DFG** | Grounded BNC chassis connector, feedthrough, nickel D-shape housing, true 75 Ω, gold-plated cage-type center contact, machined brass body | **Grounded** — shell bonded to D-shape chassis housing | Front only | **34 mm** (front flange face to rear tip — drawing ST-NBB75DFG, cross-checked against its DXF) | HD, SDI, Video, AES/EBU, Composite, YUV, RGB, RGBH, RGBHV |
| **NBB75DFGB** | Same as NBB75DFG, black housing | Grounded | Front only | same as NBB75DFG (not independently re-verified) | same |
| **NBB75DFI** | Isolated BNC chassis connector, feedthrough, nickel D-shape housing | **Isolated** — "solves potential grounding problems and prevents common-mode influence with other connections conducted over the same panel ground potential" | Front only | assumed same as NBB75DFG (mechanically near-identical family; not independently re-verified — open question) | same signal types (assumed) |
| **NBB75DFIB** | Same as NBB75DFI, black housing | Isolated | Front only | assumed same as NBB75DFG | same |
| **NBB75DSI** | Named in the request; not individually fetched — likely a solder-cup (vs. feedthrough) isolated variant based on Neutrik's naming pattern (D = D-series, S = solder, I = isolated), **unconfirmed** — verify at `https://www.neutrik.com/en/product/nbb75dsi` |
| **NBB75DFIX** / 12G-SDI-rated variant | Named in the request as a possible 12G-SDI part. **Not found under this exact name in this research pass.** NBB75DFG's own VSWR spec (≤1.08/>28 dB up to 3 GHz) does not explicitly claim 12G-SDI (12G-SDI needs clean performance well beyond 3 GHz — typically quoted to 12 GHz). **Open question: whether a dedicated 12G-SDI-rated D-series BNC exists** — not confirmed either way in this pass. |

## Grounding: when to use DFG vs. DFI

- **NBB75DFG (grounded)**: use when you want the BNC shell/shield bonded through the connector to
  the case/chassis ground — simplest option, matches how most single-BNC installations are wired.
- **NBB75DFI (isolated)**: use when **multiple BNC/coax connectors share one metal panel** and you
  need to avoid ground loops / common-mode noise between them (e.g., multiple SDI outputs on the same
  case) — the isolated version keeps each connector's shield from being forced to the same panel
  potential through the chassis, only through the cable's own shield path.

For this project (a single Pro Convert NDI unit with likely one SDI in / one SDI out, or similar),
grounded **NBB75DFG** is the simpler default unless a specific ground-loop symptom is observed;
switch to **NBB75DFI** if multiple BNCs are ganged on the same panel and interference is a concern.

## Mating cable connector

| Part | Description | Cable OD | Impedance | Notes |
|---|---|---|---|---|
| **NBNC75BLP9X** | UHD-optimized BNC cable plug, crimp | 6.3 mm | 75 Ω | Approved cables incl. Belden 1505A, Canare L-4CFB, Sommer vector 0.8/3.7; return loss ≤1.06/>30 dB up to 6 GHz; crimp size (shield) 6.47 mm hex, (pin) 1.07 mm; contact resistance ≤3 mΩ (inner) / ≤2 mΩ (outer). "Fully compatible with conventional BNC chassis connectors" per Neutrik — mates with NBB75DFG/NBB75DFI (not explicitly named on the plug's own page, but standard BNC bayonet interface applies). |

## Electrical / mechanical (NBB75DFG)

- Impedance: 75 Ω (true 75 Ω design, meets HD-SDI requirements)
- Contact resistance: ≤3 mΩ (inner), ≤2 mΩ (outer)
- Dielectric strength: 1.5 kVdc; insulation resistance > 5 GΩ; rated voltage <50 V
- VSWR: ≤1.03/>37 dB to 1 GHz, ≤1.05/>32 dB to 2 GHz, ≤1.08/>28 dB to 3 GHz
- Insertion force <25 N; lifetime >1000 mating cycles
- Locking device: Bayonet
- Materials: contacts brass (CuZn39Pb3) with 0.2 µm AuCo center contact plating; insert PTFE;
  insulation shell POM (Polyacetal); shell plating Optalloy®; D-shape housing zinc diecast
  (ZnAl4Cu1), galvanic-Ni plated
- Temperature range: −30 °C to +85 °C

## Downloads

- Datasheet: `https://www.neutrik.com/en/product/nbb75dfg.pdf`
- Technical drawing (PDF): `https://www.neutrik.com/media/8619/download/nbb75dfg-2.pdf?v=1`
  (drawing ST-NBB75DFG)
- DXF: `https://www.neutrik.com/media/12043/download/nbb75dfg-3.dxf?v=1`
- STEP: `https://www.neutrik.com/media/12639/download/3-d-nbb75dfi.stp?v=1`

## Price class

Not gathered in this research pass — open question.

## Open questions

- Exact depth-behind-panel for NBB75DFI (assumed identical to NBB75DFG; not independently drawn).
- Whether a dedicated 12G-SDI-rated D-series BNC part exists.
- NBB75DSI part details (solder-cup isolated variant, unconfirmed).
- Panel thickness rating for the NBB75D* family (not stated on the fetched datasheet).
