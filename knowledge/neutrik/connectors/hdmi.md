# HDMI (D-series)

Uses the standard D-series cutout — see `../d-series-cutout.md`. Flange 26 × 31 mm.

## Chassis (panel-mount) connectors

| Part | Description | HDMI version | Mount | Panel thickness | Depth behind panel |
|---|---|---|---|---|---|
| **NAHDMI-W** | HDMI feedthrough adapter, D-shape housing, 19-pole HDMI receptacle at both ends | **HDMI 2.0** (per "Standard compliance" field on datasheet) | Front **or** rear | **max. 2 mm** | **40.65 mm (front-mount)** / **40.2 mm (rear-fixed)** — drawing doc 20003491 rev B |
| **NAHDMI-W-B** | Same as NAHDMI-W, black housing | HDMI 2.0 | Front or rear | max. 2 mm | same as NAHDMI-W (not independently re-verified) |

No newer HDMI 2.1 / 8K-rated D-series variant was found in this research pass — as of 2026-09-07
Neutrik's own datasheet for NAHDMI-W states **HDMI 2.0** compliance (4K@60Hz-class, not 8K/48Gbps
HDMI 2.1). **Open question**: check `https://www.neutrik.com/en/neutrik/products/multimedia-connectors/hdmi`
directly for any newer part not surfaced by this pass's queries.

## Key mechanical notes

- **Panel thickness is capped at 2 mm** — noticeably tighter than etherCON (up to 4 mm) or the
  general D-series XLR guidance (1–3 mm). If your case design uses a single wall thickness at every
  connector cutout, HDMI is the limiting connector — see `../d-series-cutout.md` §3.
- Locking device: Push-Pull (not a latch/bayonet like the other D-series families)
- **Removable screen-to-chassis grounding**: NAHDMI-W ships with the HDMI cable shield bonded to the
  connector chassis by default. A grounding tab can be cut off (illustrated on the datasheet as "CUT
  OFF TO ELIMINATE GROUNDING") if a floating/isolated shield is required — relevant if grounding
  loops are a concern between the HDMI run and other panel connectors.
- Shielded system, continuous 360° shield for EMI protection

## Mating

No dedicated Neutrik HDMI cable-plug part number was identified in this research pass (NAHDMI-W is a
feedthrough adapter — any standard HDMI plug/cable inserts directly into its rear-facing port, no
special Neutrik-branded mating cable connector is required, unlike etherCON/BNC which have their own
Neutrik cable-connector families).

## Electrical / mechanical

- Contacts: bronze (CuSn), gold-plated
- Shell: zinc diecast (ZnAl4Cu1), nickel-plated
- IP65 ingress protection in mated condition, achieved together with **NKHDMI-\*** cable and
  **SCDP-\*** sealing gasket (exact NKHDMI-* suffix not individually captured in this pass)
- Lifetime > 1000 mating cycles; UL 94 V-0; temperature −25 °C to +85 °C

## Downloads

- Datasheet: `https://www.neutrik.com/en/product/nahdmi-w.pdf`
- Technical drawing (PDF): `https://www.neutrik.com/media/8976/download/Drawing%20NAHDMI-W.pdf?v=10`
- DXF: `https://www.neutrik.com/media/12191/download/Drawing%20NAHDMI-W.dxf?v=11`
- STEP: `https://www.neutrik.com/media/12190/download/nahdmi.stp?v=1`
- IP65 test report: `https://www.neutrik.com/media/9197/download/multimedia-series-ip-65-test-report.pdf?v=1`

## Price class

Not gathered in this research pass — open question. (General industry expectation is that HDMI
feedthrough D-connectors sit at the higher end of this connector family's price range, but this is
not sourced — do not treat as a hard figure.)

## Open questions

- Whether a newer HDMI 2.1/8K D-series part exists beyond NAHDMI-W (HDMI 2.0).
- Exact NKHDMI-* mating cable part numbers.
- Confirm NAHDMI-W-B mechanical dimensions match NAHDMI-W exactly (assumed, color-only difference).
