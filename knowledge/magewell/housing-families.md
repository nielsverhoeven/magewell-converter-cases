# Magewell Pro Convert — Housing Families

Four distinct chassis are reused across the whole Pro Convert range. This file documents each one:
overall dimensions, which models share it, the power path, cooling, a text description of every
face (connectors in the left-to-right order documented in the manuals/photos, LEDs, switches,
mounting hole), and case-design implications.

Port order is taken from manual figures and product photos, not dimensioned drawings — no
dimensioned/annotated port-position drawing was found for any model. Enclosure alloy is not stated
in any source.

---

## (a) Plus — 117.5 × 66.7 × 23.4 mm

**Members:** Pro Convert HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus, HDMI Plus, SDI Plus, and — as
an outlier from the NDI-decoder family — Pro Convert for NDI to HDMI 4K.

Confirmed identical across all six datasheets/manual figures (manual figure is captioned "Pro
Convert HDMI 4K Plus/Pro Convert HDMI Plus" and "SDI 4K Plus/SDI Plus", i.e. one drawing shared by
both tiers). Mounting kit ACC10013 ("Pro Convert Plus Mounting Kit") fits HDMI Plus, HDMI 4K Plus,
SDI Plus, SDI 4K Plus, 12G SDI 4K Plus and NDI to HDMI 4K — confirming the shared chassis.

Sources: shared encoder manual https://www.magewell.com/files/documents/User_Manual/ProConvert_Encoder-UserManual_en_US.pdf ;
family manual https://www.magewell.com/files/documents/User_Manual/pro_convert_family_user_manual_v1.1_en.pdf ;
decoder manual https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf ;
per-model datasheets linked from each model's file.

### Power path
- 5 V DC via USB Type-B "+5V" port (doubles as Ethernet-over-USB RNDIS/ECM config port, default IP 192.168.66.1), bundled 5 V/2.1 A adapter.
- PoE, IEEE 802.3af, via the RJ45 "NDI+PoE" port.
- Manual FAQ p.58: "Pro Convert devices require a 5V DC source with a current rating of no less than 2.1A."
- Max power 7–10 W depending on model (see `power-and-thermal.md`).

### Cooling
- 4K-capable encoders (HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus) and NDI to HDMI 4K: internal fan,
  variable speed, exposed as a "Fan Speed" field in the Web-UI dashboard.
- HDMI Plus / SDI Plus (not 4K-capable): **fan presence is contradictory between sources** — see
  note below.
- Top face has a large circular perforated "MAGEWELL" grille, presumed to be the fan/vent opening
  (estimated from image, not explicitly confirmed as a vent in text).
- Manual p.18: keep the unit free of dust; if core temperature approaches 100 °C, supply cooler air.

**Fan contradiction, recorded in full:** The 4K Plus encoder report describes the Web-UI "Fan Speed"
field (manual p.17–19) as present and states it is "not available for TX products" — read literally
this implies the field (and a fan) is present on the whole non-TX (Plus) line, including HDMI
Plus/SDI Plus. The Plus-encoder report (HDMI Plus/SDI Plus) flags this explicitly as **uncertain**,
noting the datasheets for HDMI Plus/SDI Plus list no fan at all. The NDI-decoder report, quoting the
shared decoder manual p.18 directly, states variable-speed fan is "ONLY available for 4K products" —
which would exclude HDMI Plus/SDI Plus (not 4K-capable) from having a fan. No source directly states
"HDMI Plus has a fan" or "HDMI Plus has no fan" — both readings above are inferences from adjacent
text about other products. Recorded as: **yes** (fan present) for HDMI 4K Plus, SDI 4K Plus, 12G SDI
4K Plus, NDI to HDMI 4K; **uncertain** for HDMI Plus, SDI Plus.

### Face descriptions

**End A — data/power end** (order per encoder manual p.6–7 and family manual p.6–7, 10–11; left to right):
- Corner screw hole (enclosure fastener, not the mounting hole)
- SD-card slot (present but non-functional)
- USB Type-B "+5V" (power in + Ethernet-over-USB config)
- RJ45 "NDI+PoE" with Power LED
- QR-code sticker (device identification, not a physical feature)
- Corner screw hole

**End B — video/control end** (left to right, two rows):
- Top row: Tally "PREVIEW" LED — 16-position rotary switch (board index 0–F) — Tally "PROGRAM" LED
- Bottom row: HDMI IN (or SDI IN BNC) with Input LED — Mini-DIN-8 "PTZ+TALLY" port — HDMI OUT (or SDI OUT BNC) with Output LED

**Top face:** circular perforated "MAGEWELL" grille (vent, estimated from image).
**Bottom face:** not pictured in any source; 1/4"-20 threaded mounting hole is present somewhere on
the enclosure (used for the L-bracket and Fishtail bracket) but its exact face/position is not
documented for this family beyond "threaded hole."
**No** Kensington lock slot, **no** physical reset button (reset is software-only, via the USB-NET
web UI), **no** WiFi.

### In the box
USB 2.0 A-to-B cable, 5 V/2.1 A power adapter, Mini-DIN-8 breakout cable (to Mini-DIN-8 + DB9;
pinout PDF https://www.magewell.com/files/documents/Mini-DIN8%20to%20Tally%20(Mini-DIN8)%20+%20RS232%20(DB9)%20Breakout.pdf),
Tally light (part #99090 per the family manual), L-bracket #92240.

### Case-design implications
- Both short ends must reach the case wall: End A needs USB-B + RJ45 access; End B needs
  HDMI/SDI in+out (2 connectors) plus the Mini-DIN-8 PTZ/Tally port — three connectors on one face.
- The Mini-DIN-8 PTZ/Tally port has **no Neutrik D-size panel-mount equivalent** — if the case wants
  a bulkhead pass-through for this port, a round Mini-DIN-8 cutout (not a D-shape) is needed, or the
  port is left recessed/unused.
- The 16-position rotary switch and its two flanking Tally LEDs sit on End B in the family manual's
  figure (top row) — a case must leave this accessible (thumb/screwdriver reach) and the two LEDs
  visible.
- USB Type-B on End A is both the power input and the config/network port (RNDIS/ECM) — do not
  design the case assuming it is power-only; it needs a reachable, unobstructed connector face.
- Top circular grille is the likely fan/vent path for the 4K-capable models — do not seal it; leave
  clearance for airflow in the case design even for HDMI Plus/SDI Plus given the fan uncertainty.
- No published bottom-face drawing — verify the exact 1/4"-20 hole location physically or from a
  photo before designing a mounting boss.

---

## (b) Compact/TX — 100.9 × 60.2 × 23.3 mm

**Members:** Pro Convert HDMI TX, SDI TX, NDI to HDMI, NDI to SDI, NDI to AIO, AES67, Audio DX.

The HDMI TX datasheet prints "100.9smm" — treated as an extraction typo for "100.9 mm". Confirmed
shared chassis via mounting kit ACC10012 ("Pro Convert TX Mounting Kit"), which fits HDMI TX, SDI
TX, NDI to HDMI, NDI to AIO, NDI to SDI.

Sources: HDMI TX datasheet https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertHDMI_TX.pdf ;
SDI TX datasheet https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertSDI_TX.pdf ;
decoder manual https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf ;
AES67/Audio DX manuals linked from their model files.

### Power path
- 5 V DC via USB 2.0 Type-B "+5V", bundled 5 V/2.1 A adapter.
- PoE, IEEE 802.3af, via RJ45 "NDI+PoE" (encoders/decoders) or "ETH+POE" (AES67/Audio DX).
- Max power 5–7 W depending on model (see `power-and-thermal.md`).

### Cooling
- **Fanless** for every member of this family, confirmed explicitly: encoder manual p.19 states
  "Fan Speed … not available for TX products"; AES67/Audio DX are separately confirmed fanless.
  NDI to HDMI/SDI/AIO also have no fan (only NDI to HDMI 4K, which uses the larger (a) Plus chassis
  instead, has a fan).
- Metal body, no vent grille observed (estimated from image — TX top face is a printed label only).

### Face descriptions

**HDMI TX / SDI TX** (manual p.8–9, 11):
- Input end: HDMI IN (or SDI IN BNC) → Input LED → Mini-DIN-8 "PTZ+TALLY"
- Power/data end: USB 2.0 Type-B "+5V" → Power LED → RJ45 "NDI+POE"; QR-code sticker; SD-card slot
  (non-functional) on this end
- Long-edge side face: 16-position rotary switch (board index)
- Top: printed label only, no vent grille (estimated from image)
- Bottom: 1/4"-20 threaded hole (near the power end, estimated from image)
- No Kensington slot, no physical reset (web UI over USB-NET only), no WiFi
- **No HDMI/SDI loop-out** on TX models (unlike the Plus family)

**NDI to HDMI** (manual p.6–9):
- Face A: HDMI OUT → decoding LED → USB HOST (Type-A)
- Face B: USB 2.0 Type-B "+5V" → Power LED → RJ45 "NDI+PoE"
- Top, near Face A: SD-card slot (non-functional) + 1/4"-20 hole
- Top, near Face B: rotary switch, MENU button, SELECT button

**NDI to SDI**:
- Face A: SDI OUT BNC → LED → USB HOST
- Face B: USB-B → LED → RJ45

**NDI to AIO** (no USB host):
- Face A: HDMI OUT → LED → SDI OUT BNC
- Face B: USB-B (power only) → LED → RJ45

**AES67 / Audio DX**:
- Audio end: unbalanced 3.5 mm TRS IN then OUT, then balanced 4.4 mm TRRRS IN then OUT
- Network end: RJ45 "ETH+POE" and USB-B "+5V/USB+POWER"
- 16-position rotary switch on the edge near the network end
- 1/4"-20 hole near the audio end (Audio DX diagram labels it "Screw Mounting Hole")
- Bottom: central rubber pad + two screw heads (estimated from image)
- No Kensington slot, no reset button

Common across the family: no Kensington slot, no physical reset button, FCC Part 15, 2-year
warranty; L-bracket #92240 and Fishtail bracket STL both apply.

### In the box
USB 2.0 A-to-B cable, 5 V/2.1 A adapter, Mini-DIN-8 breakout cable (encoders/NDI decoders only),
Tally light, L-bracket #92240. AES67/Audio DX instead include 4.4 mm-to-dual-XLR-M and -F cables.

### Case-design implications
- HDMI TX / SDI TX have connectors split across **two** short ends (video+PTZ on one, USB/RJ45 on
  the other) plus a rotary switch on a **long edge** — the case needs a cutout on a side face, not
  just the ends.
- TX models have no loop-out, so only one video connector per short end (simpler bulkhead than the
  Plus family's two-connector video end).
- The Mini-DIN-8 PTZ/Tally port again has no Neutrik D-size panel equivalent (applies wherever this
  port appears in this family too: TX and NDI-to-HDMI/SDI models).
- USB-B is both power and the RNDIS/ECM config port here too — must remain reachable, not just a
  power jack.
- No vent grille observed on this family — a sealed case is thermally consistent with the fanless
  design, but leave nominal clearance since the manual's general dust/cool-air warning (p.18) still
  applies to the shared manual.
- Rotary switch position differs between sub-families: TX puts it on a long side face; NDI decoders
  and AES67/Audio DX put it near the network/data end on the top — check the specific model file
  before placing a switch cutout.
- AES67/Audio DX are **not compatible** with the ACC1001x rack kits despite sharing this chassis —
  don't assume rack-kit compatibility transfers within the family.

---

## (c) IP decoder — 120 × 79.3 × 24.5 mm

**Members:** Pro Convert IP to HDMI, IP to HDMI 4K, IP to AIO 4K.

Confirmed via photo comparison (same body, screw positions, rear cutouts; AIO variant adds one BNC
connector). This is a newer generation, distinct from the older NDI-to-HDMI-style decoders (which
use USB-B power and a rotary switch) — this family is powered over USB-C and uses a rotary
push-encoder instead.

Sources: shared QSG https://www.magewell.com/files/documents/Quick%20Start%20Guide%20for%20Pro%20Convert%20IP%20Decoder.pdf ;
online manual https://www.magewell.com/onlinehelp/pro-convert-ip-decoder/ ;
photo reference https://www.magewell.com/static/product/convert/pro-convert-ip-to-hdmi/product/4.webp .

### Power path
- USB-C: 5 V/12 V up to 10 W (IP to HDMI) or 12 V up to 20 W (IP to HDMI 4K, IP to AIO 4K).
- PoE: 802.3af/at (IP to HDMI) or 802.3at only (IP to HDMI 4K, IP to AIO 4K), via the ETH/PoE RJ45.
- Max power 6.62–15.1 W depending on model (see `power-and-thermal.md`).

### Cooling
- Fanless on all three models; two clusters of louvered vent slots on the top face provide passive
  airflow.

### Face descriptions

**Front (short face):**
- LEDs, left to right: PWR (blue), SIG (blue), PGM (red), PVW (green)
- Rotary encoder push-knob (combined switch + selector, not a bare rotary switch)

**Rear (short face), left to right:**
- HDMI OUT
- (AIO variant only) SDI OUT BNC
- USB HOST (USB 3.0 Type-A)
- CONFIG (USB-C, power-capable)
- Audio OUT, 3.5 mm
- ETH/PoE RJ45 with 2 status LEDs

**Top face:** two clusters of louvered vent slots.
**Rear panel:** 4 corner Phillips screws.
No Kensington slot, no visible reset button, single RJ45.
Mounting: 1/4"-20 threaded hole + the Fishtail bracket ships in the box as part STR00211 with
PAR10040 (thumbscrew-adapter fasteners), MECO0067 (M4×12 black screws ×2), MECO0068 (M4 nuts ×2).
IP to AIO 4K additionally documents Φ6.5 mm mounting holes.

### In the box
USB-C-to-C cable (ELE00114) and USB-C-to-A cable (ELE00066), both 80 cm; universal power adapter
ELE00125.

### Case-design implications
- Video/USB-host/config/audio/network are **all on one rear face** (6 connectors across HDMI/AIO's
  extra BNC, USB-A, USB-C, 3.5 mm, RJ45) — this face needs the widest single-face cutout of any
  family in this project.
- The front face's rotary push-encoder needs both rotational and axial (push) clearance, unlike the
  simple rotary switches on the other families.
- The two louvered vent clusters on top must stay unobstructed even though the units are fanless —
  they are the only cooling path.
- 4 corner Phillips screws on the rear panel are enclosure fasteners, not mounting features — don't
  confuse with the 1/4"-20 mounting hole.
- The in-box Fishtail bracket (STR00211 + PAR10040 + MECO0067/68) is the reference hardware kit to
  stay compatible with for any custom bracket design — see `accessories.md`.

---

## (d) IP to USB — 98.1 × 56.78 × 18 mm

**Members:** Pro Convert IP to USB only (SKU 623000000 / 62300, model ED0230A).

The smallest chassis in the range — roughly two-thirds the footprint of the IP decoder family and
noticeably thinner (18 mm vs 23.3–24.5 mm elsewhere).

Source: datasheet https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertIP_to_USB.pdf (rev 01/29/2026).

### Power path
- USB-C (SS/USB 3.0), 5 V/1 A drawn from the host device — no external adapter, no PoE.
- Max power ~3.8 W.

### Cooling
- Fanless, **no vents observed** (unlike the (c) IP decoder family, which has louvered vents).

### Face descriptions
- One end: USB-C (SuperSpeed) — connects to the host computer, both data and power.
- Other end: RJ45 "ETH".
- Two-tone metal end caps with a glossy black top panel.
- No further port/LED detail documented (no manual page reference found for this model beyond the
  datasheet); no mounting hole information found — **mounting: none found**.

### In the box
USB-C-to-C / USB-C-to-A style cables (ELE00113/ELE00114), 80 cm.

### Case-design implications
- Only two connectors, one per short end — the simplest bulkhead layout of any family, but the
  thinner 18 mm body means standard wall thicknesses/fastener bosses used for the other families may
  not fit without adjustment.
- No vents and no fan — the case can fully enclose this unit without dedicated airflow provisions
  based on available data, but there is no official thermal guidance beyond the 0–50 °C operating
  range (see `power-and-thermal.md`).
- No 1/4"-20 hole or other mounting feature has been found for this model — do not assume one
  exists; verify physically before designing a mount, or design a friction/strap mount instead.
