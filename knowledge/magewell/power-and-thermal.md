# Magewell Pro Convert — Power and Thermal Reference

All figures as published on each model's magewell.com tech-specs page / datasheet PDF, fetched
2026-09-07 (see `sources.md`). `unknown` = not published. Retailer-sourced figures are marked
unverified and are never used in place of an official figure.

## Full table

| Model | PoE | DC input | Max power | Op. temp | Fan |
|---|---|---|---|---|---|
| Pro Convert HDMI 4K Plus | 802.3af | 5 V via USB Type-B, ~2 A max (adapter 5 V/2.1 A) | ~10 W | 0–45 °C | yes* |
| Pro Convert SDI 4K Plus | 802.3af | 5 V, ~1.5 A | ~7 W | 0–45 °C | yes* |
| Pro Convert 12G SDI 4K Plus | 802.3af | 5 V, ~1.65 A | ~8.5 W | 0–45 °C | yes* |
| Pro Convert HDMI Plus | 802.3af | 5 V via USB-B, ~1.5 A (adapter 5 V/2.1 A) | ~8 W | 0–45 °C | uncertain* |
| Pro Convert SDI Plus | 802.3af | 5 V via USB-B, ~1.5 A (adapter 5 V/2.1 A) | ~7 W | 0–45 °C | uncertain* |
| Pro Convert HDMI TX | 802.3af | 5 V via USB-B, ~1.5 A max (adapter 5 V/2.1 A) | ~6 W | 0–40 °C | no |
| Pro Convert SDI TX | 802.3af | 5 V via USB-B, ~1.5 A max (adapter 5 V/2.1 A) | ~7 W | 0–40 °C | no |
| Pro Convert for NDI to HDMI | 802.3af | 5 V via USB-B, ~1.1 A (adapter 5 V/2.1 A) | ~5 W | 0–40 °C | no |
| Pro Convert for NDI to HDMI 4K | 802.3af | 5 V, ~1.6 A | ~7.2 W | 0–45 °C | yes (variable speed) |
| Pro Convert for NDI to SDI | 802.3af | 5 V, ~1.05 A | ~5.5 W | 0–40 °C | no |
| Pro Convert for NDI to AIO | 802.3af | 5 V, ~1.05 A | ~5.5 W | 0–40 °C | no |
| Pro Convert IP to HDMI | 802.3af/at | USB-C, 5 V/12 V, 10 W | ~6.62 W | 0–40 °C | no |
| Pro Convert IP to HDMI 4K | 802.3at | USB-C, 12 V, 20 W | ~12.12 W | 0–40 °C | no |
| Pro Convert IP to AIO 4K | 802.3at | USB-C, 12 V, 20 W | ~15.1 W | 0–40 °C | no |
| Pro Convert IP to USB | none | USB-C, 5 V/1 A from host | ~3.8 W | 0–50 °C | no |
| Pro Convert AES67 | 802.3af | 5 V via USB-B (adapter 5 V/2.1 A), draw ~1 A | ~5 W | –10–50 °C | no |
| Pro Convert Audio DX | 802.3af | 5 V via USB-B (adapter 5 V/2.1 A) | ~5 W | –10–50 °C | no |

`*` See the fan contradiction below and in `housing-families.md`.

### Fan contradiction (full detail)

- **4K Plus report** (HDMI 4K Plus / SDI 4K Plus / 12G SDI 4K Plus): Web-UI Dashboard shows a "Fan
  Speed" field (manual p.17–19); the field is described as "not available for TX products" — implying
  it is available, and therefore a fan is present, for the rest of the (non-TX) line.
- **Plus report** (HDMI Plus / SDI Plus): flags this as explicitly **uncertain** — their own
  datasheets list no fan, contradicting the implication above.
- **NDI-decoder report** (covers NDI to HDMI 4K, which shares the Plus chassis): quotes the shared
  decoder manual p.18 directly — variable-speed fan is "ONLY available for 4K products." This directly
  contradicts the broader "all non-TX products" reading from the 4K Plus report.
- **Resolution used in this knowledge base:** fan = **yes** for the four 4K-capable Plus-family
  models (HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus, NDI to HDMI 4K); fan = **uncertain** for
  HDMI Plus and SDI Plus (not 4K-capable, datasheets silent, but adjacent Web-UI text is ambiguous
  about whether it applies to them). This is an editorial resolution based on the more specific,
  directly-quoted "4K products only" manual text — it is not a confirmed fact for HDMI Plus/SDI Plus
  either way. Verify physically (e.g. listen for a fan, or check the Web-UI dashboard) before relying
  on this for a sealed-case thermal design.

## Heat budget per housing family

| Family | Members | Power range | Notes |
|---|---|---|---|
| (a) Plus — 117.5 × 66.7 × 23.4 mm | HDMI 4K Plus, SDI 4K Plus, 12G SDI 4K Plus, HDMI Plus, SDI Plus, NDI to HDMI 4K | 7–10 W | Highest-power family; 4K-capable members have an internal fan (see above), so a sealed/gasketed case risks trapping heat particularly for the ~10 W HDMI 4K Plus. |
| (b) Compact/TX — 100.9 × 60.2 × 23.3 mm | HDMI TX, SDI TX, NDI to HDMI, NDI to SDI, NDI to AIO, AES67, Audio DX | 5–7 W | Fanless across the whole family; lower power than (a), but no vent grille observed — rely on the metal body as a heatsink, don't fully seal in an insulating case shell. |
| (c) IP decoder — 120 × 79.3 × 24.5 mm | IP to HDMI, IP to HDMI 4K, IP to AIO 4K | 6.62–15.1 W | Fanless but relies on louvered top vents for passive convection — these must not be blocked by a case; IP to AIO 4K at ~15.1 W is the single highest-power model in the entire range. |
| (d) IP to USB — 98.1 × 56.78 × 18 mm | IP to USB | ~3.8 W | Lowest power in the range and no vents observed; thinnest chassis (18 mm). |

## Manual warnings (dust / cooling)

- Encoder manual FAQ (p.58): "Pro Convert devices require a 5V DC source with a current rating of no
  less than 2.1A." — applies to the USB-B-powered models; relevant to case design only in that the
  power adapter/cable routing must support this current, not a thermal note.
- Encoder manual (p.18): keep the unit free from dust; if internal core temperature approaches
  100 °C, supply cooler air to the unit. This is the primary explicit thermal-management guidance
  found across the reports — case designs should preserve airflow to any vent openings and avoid
  trapping dust around them.
- No model-specific thermal derating curves, junction/core temperature limits, or airflow (CFM)
  specifications were found in any source.

## Sources

Per-model tech-specs/datasheet URLs are listed in each model's file under `models/` and grouped by
topic in `sources.md`. Manual page references above are as cited in the raw research reports (see
`sources.md` for the manual URLs).
