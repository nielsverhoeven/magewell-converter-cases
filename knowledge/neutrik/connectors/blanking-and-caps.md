# Blanking plates and dust caps (D-series)

## Blanking plate

| Part | Description | Dimensions | Material | Mounting |
|---|---|---|---|---|
| **DBA-BL** | Dummy-plate to cover unused D-shape cutouts | Flange 26.0 × 31.0 mm, corner radius R3.5 mm, thickness **3.2 mm**, mounting holes ⌀3.5 mm at the standard 19×24 mm diagonal spacing (identical pattern to every other D-series part — see `../d-series-cutout.md`) | **PA6.6** (nylon) | Same two screws as any other D-series connector — no cutout-side clearance needed since it fully covers the hole |
| **DBA-BL-B** | Same as DBA-BL — likely a color variant naming convention, but **not independently confirmed** in this pass (DBA-BL's own page did not mention color options) | assumed identical | assumed PA6.6 | assumed identical |

Source: drawing "ST-DUMMY_COVER" / "D-Flansch Dummy_Cover" —
`https://www.neutrik.com/media/8479/download/dba-2.pdf?v=1`. This drawing is the cleanest,
highest-confidence confirmation of the D-series mounting-hole pattern (19 × 24 mm, ⌀3.5 mm) found
in this entire research pass, since a blanking plate has no other features to potentially confuse the
dimension callouts with.

## Dust caps / hinged covers

| Part | Color | Fits | IP rating (unmated) | Material |
|---|---|---|---|---|
| **SCDX** | Black | D-size XLR, speakON, powerCON, USB, HDMI, D-SUB, Firewire, etherCON, BNC, Phono (RCA) — i.e. essentially every connector in this knowledge base | **IP42** | PP-R (polypropylene), UL 94 HB, −30 °C to +80 °C |
| **SCDX-6** | Blue | Same connector list (opticalCON multi-mode color-coding use) | IP42 | PP-R |
| **SCDX-9** | White | Same connector list (e.g. wall-outlet use) | IP42 | PP-R |

SCDX is a **hinged cover** that closes over the connector opening when unmated, sealing against
water/dust/dirt ingress to IP42 — this is separate from the connector's own "IP65 in mated
condition" rating quoted on etherCON IDC, USB, and HDMI datasheets (that mated-IP65 figure requires
the specific NKUSB-*/NKHDMI-*/SCDP-* sealed cable+gasket combination, not the SCDX cap).

**"SCNAC" note**: the request mentions "SCNAC etc." — confirmed to exist as **SCNAC-01** (D-size
rubber sealing cover for powerCON TRUE1 TOP, referenced on the NAC3MPX-TOP page) and **SCNAC-MPX**
(cap used with NAC3MPX-TOP for its IP65/UL50E Type 4 rating). These are the powerCON-specific
sealing caps, not literally "D-size dust caps" in the SCDX sense, but part of the same family of
Neutrik protective-cap accessories.

## Downloads

- DBA-BL: datasheet `https://www.neutrik.com/en/product/dba-bl.pdf`; drawing
  `https://www.neutrik.com/media/8479/download/dba-2.pdf?v=1`; STEP
  `https://www.neutrik.com/media/19043/download/3D%20Model%20dba-bl.stp?v=1`
- SCDX: `https://www.neutrik.com/en/product/scdx` (individual media download URLs not captured in
  this pass)

## Price class

Not gathered in this research pass — open question.

## Open questions

- Confirm DBA-BL-B exists as a genuine part number and is mechanically identical to DBA-BL.
- Individual SCDX/SCDX-6/SCDX-9 drawing dimensions (only the DBA-BL blanking-plate drawing was
  fetched in detail; SCDX is a cover that clips over an installed connector, not a flat plate, so its
  own protrusion depth was not captured — relevant if front-panel clearance for closed caps matters).
