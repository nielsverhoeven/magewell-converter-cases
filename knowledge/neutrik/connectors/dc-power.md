# DC power (D-series)

## Does Neutrik offer a D-size DC barrel/coax jack?

**No — not found.** This research pass checked Neutrik's multimedia connector category listing
(USB Type A/B, USB Type C/mediaCON, HDMI, D-SUB, Multimedia Accessories) and the general D-series
XLR/power pages; no DC barrel/coax power jack product surfaced anywhere in the D-shape chassis
family. Neutrik's DC/low-voltage power solutions in the D-size footprint are the **4-pole XLR**
parts below, not a coaxial barrel jack. Treat "no D-size barrel jack" as reasonably confident but not
100% exhaustively verified — if one exists it was not linked from any page reached in this pass
(**open question** if you need to rule it out completely).

## XLR4 DC power (the de-facto D-series DC power connector)

Uses the standard D-series cutout — see `../d-series-cutout.md`. Flange 26 × 31 mm.

| Part | Description | Gender | Rated current/contact | Wiring | Depth behind panel |
|---|---|---|---|---|---|
| **NC4FD-L-1** | 4-pole female receptacle, solder cups, nickel housing, silver contacts, universal D-size metal body, UL-recognized | Female | **10 A** | Solder cups (max. 1.5 mm² / 16 AWG) | Not independently drawn in this pass; expect similar to the 3-pole XLR D-series depth of **~21.7 mm** (see `../d-series-cutout.md` XLR source drawing) since NC4FD-L-1 shares the same "L" solder-cup mechanical family as NC3FD-L-1 — **not confirmed, open question** |
| **NC4MD-L-1** | 4-pole male receptacle, solder cups, nickel housing, silver contacts | Male | 10 A | Solder cups | Same caveat as above |

Both: capacitance between contacts ≤7 pF; contact resistance ≤5 mΩ; dielectric strength 1.5 kVdc;
insulation resistance >10 GΩ; rated voltage <50 V; insertion/withdrawal force ≤20 N; lifetime
>1000 mating cycles; latch lock; shell zinc diecast (ZnAl4Cu1) nickel-plated; IP40; UL 94 V-0;
temperature −30 °C to +80 °C; IEC 61076-2-103 compliant.

### Common 12 V DC pinout convention (industry practice, not a Neutrik-published spec)

The request notes the common convention of **pin 1 = −, pin 4 = +** for 4-pin XLR DC power. This is
a widely used lighting/broadcast industry convention (popularized for things like on-camera monitor
and LED-light DC power), **not something stated on Neutrik's own NC4FD-L-1/NC4MD-L-1 product pages**
in this research pass — Neutrik sells the connector as a generic 4-pole XLR; the pinout is assigned
by the system integrator. **Do not treat pin 1/pin 4 polarity as a hardware-enforced Neutrik
standard** — it must be explicitly documented and consistently wired in this project's own designs
since a miswired mating cable could reverse polarity into the Magewell converter.

## powerCON / TRUE1 (mains, briefly — per request)

| Part | Description | Chassis shape | Rating |
|---|---|---|---|
| **NAC3MPX-TOP** | powerCON TRUE1 TOP appliance inlet connector, locking, 1/4" flat tab terminals | **D-size** — confirmed via its D-size rubber sealing cover accessory (SCNAC-01) | 16 A / 250 V AC (EU, EN 60320-1) or 20 A / 250 V AC (US, UL 498). IP65/UL50E Type 4 in combination with cap SCNAC-MPX |

This is a **mains AC** connector family (100–250 V AC class hardware), not intended as a low-voltage
DC connector — included here only because the request asked for it briefly and because it does use
the same D-size chassis shape as everything else in this document. **Do not use powerCON/TRUE1 for
the Magewell's 12 V DC input** unless you specifically need its locking mains-rated mechanism and are
prepared to document the (non-standard) DC use — the XLR4 parts above are the conventional choice for
low-voltage DC in this connector family.

## Recommendation for this project

For the Magewell Pro Convert's DC input, **NC4FD-L-1** (female chassis receptacle, so the case
presents a female socket and the external power brick's cable carries the male NC4MP/NC4MX-style
plug) is the standard choice, consistent with broadcast/AV industry practice for 12 V-class DC power
in a D-series panel. Confirm the exact current draw of the Magewell Pro Convert's DC input against
the connector's 10 A/contact rating (almost certainly ample headroom for typical <2 A converter
draw).

## Downloads

- NC4FD-L-1: datasheet `https://www.neutrik.com/en/product/nc4fd-l-1` (technical drawing/DXF links
  present on the page but not individually captured in this pass)
- NC4MD-L-1: `https://www.neutrik.com/en/product/nc4md-l-1`
- NAC3MPX-TOP: `https://www.neutrik.com/en/product/nac3mpx-top`

## Price class

Not gathered in this research pass — open question.

## Open questions

- Exact depth-behind-panel for NC4FD-L-1/NC4MD-L-1 (no dimensioned drawing fetched in this pass —
  estimated from the mechanically similar 3-pole XLR "L" family at ~21.7 mm, unconfirmed).
- Exhaustive confirmation that no D-size DC barrel/coax jack exists anywhere in Neutrik's catalog
  (reasonably confident based on category browsing, not exhaustively proven).
- Exact mating cable connector part numbers for NC4FD-L-1/NC4MD-L-1 (e.g. NC4MX/NC4MXX-style cable
  plugs) — not looked up in this pass.
