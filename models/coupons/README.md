# models/coupons — Tier-4 physical calibration coupons

Printed and measured by hand before any full case is printed (`.claude/knowledge/architecture.md`
§9 Tier 4, `.claude/knowledge/testing.md` "The four tiers"). Every measured result goes back into
`lib/mcc/constants.scad` as a named `MCC_*` constant with a comment citing the coupon and the
measurement date — nowhere else. A number that only lives in a coupon file or a print-log entry is
invisible to the next case render.

Printer: **Bambu Lab X1 Carbon**, 256×256×256 mm, enclosed, 0.4 mm nozzle, ASA. See
`.claude/skills/print-check/SKILL.md` for the full go/no-go checklist this file assumes.

## What each coupon verifies

| Coupon | Verifies | Calibrates (file : symbol) |
|---|---|---|
| `neutrik-tile.scad` | A real Neutrik D-series connector (NAHDMI-W-B 23.6-class default, NE8FDP-B 24.0-class variant) actually drops into the cutout and screws down onto the rear bosses | `lib/mcc/constants.scad` : `MCC_HOLE_COMP` (cross-checks each `MCC_PANEL_PARTS[<part>].hole_d`) |
| `depth-mockup.scad` | The real mating patch cable's plug seats with a comfortable bend at the budgeted bay depth | `lib/mcc/constants.scad` : `MCC_PANEL_PARTS[<part>].plug_len` (cross-checks `.bend`) |
| `tg-ladder.scad` | Which tongue-and-groove per-side clearance slides freely without slop | `lib/mcc/constants.scad` : `MCC_CLR_TG` |
| `insert-boss.scad` | Which M3 heat-set insert bore diameter seats with firm hand pressure in ASA without splitting the boss | `lib/mcc/constants.scad` : `MCC_INSERT_M3` → `hole_d` entry |
| `tolerance-ladder.scad` | Which round peg/hole per-side clearance is a free slide vs. a firm press fit | `lib/mcc/constants.scad` : `MCC_CLR_SLIDE` (slide), `MCC_CLR_PRESS` (press) |

## Render

```powershell
.venv\Scripts\python scripts\build.py render --all --format both
.venv\Scripts\python scripts\build.py check --all
.venv\Scripts\python scripts\build.py golden
```

`render --all` picks up all five coupons automatically (`scripts/build.py`'s `discover_coupons()`
globs `models/coupons/*.scad`). `--format both` emits `.stl` (used for the Tier-3 mesh checks and
golden measurement) and `.3mf` (what actually goes to Bambu Studio) into
`exports/coupons/<name>/<part>.{stl,3mf}` — gitignored, local only.

`neutrik-tile` additionally supports a `-D connector="..."` override to swap the connector class it
cuts for. `scripts/build.py` names every render's outputs after the *part*, not the `-D` values, so
switching `connector` on a second render silently overwrites the first one's `neutrik-tile.stl`/
`.3mf` in place — there is no built-in per-variant naming. Render the two connector classes that
matter, saving each before rendering the next:

```powershell
# 1. default connector (NAHDMI-W-B, 23.6-class) — already covered by render --all above.
copy exports\coupons\neutrik-tile\neutrik-tile.stl  exports\coupons\neutrik-tile\neutrik-tile-NAHDMI-W-B.stl
copy exports\coupons\neutrik-tile\neutrik-tile.3mf  exports\coupons\neutrik-tile\neutrik-tile-NAHDMI-W-B.3mf

# 2. etherCON/RJ45 connector (NE8FDP-B, 24.0-class) — overwrites neutrik-tile.stl/.3mf, so rename after.
.venv\Scripts\python scripts\build.py render coupons/neutrik-tile --format both -D 'connector="NE8FDP-B"'
move exports\coupons\neutrik-tile\neutrik-tile.stl  exports\coupons\neutrik-tile\neutrik-tile-NE8FDP-B.stl
move exports\coupons\neutrik-tile\neutrik-tile.3mf  exports\coupons\neutrik-tile\neutrik-tile-NE8FDP-B.3mf

# restore the plain neutrik-tile.stl/.3mf to the default (NAHDMI-W-B) variant so `golden` keeps
# comparing against what tests/golden/coupons/neutrik-tile.json was written from.
copy exports\coupons\neutrik-tile\neutrik-tile-NAHDMI-W-B.stl exports\coupons\neutrik-tile\neutrik-tile.stl
copy exports\coupons\neutrik-tile\neutrik-tile-NAHDMI-W-B.3mf exports\coupons\neutrik-tile\neutrik-tile.3mf
```

Print **both** neutrik-tile variants — the 23.6-class hole (HDMI/USB/BNC family) and the 24.0-class
hole (etherCON/RJ45) are different diameters (`mcc_cutout_d()`); a fit confirmed on one says nothing
about the other.

## Orientation (Bambu Studio)

| Coupon | Orientation | Why |
|---|---|---|
| `neutrik-tile` | **Flange (front) face down on the bed.** As modeled: the tile's Z axis (connector-cutout axis) is already vertical when the part sits on its large flat face, so no rotation is needed — just place it flange-down, rear screw bosses pointing up. | The Ø23.8/24.2 mm cutout prints as a true circle with no bridging; the flange seat prints against the bed as a smooth, flat surface (print-check §3). |
| `depth-mockup` | **Flat, floor plate down on the bed**, walls rising vertically out of the floor. No supports needed. | A flat-printing U-channel: the floor plate is the bed-contact face, and both the panel wall and the mock-face wall stack directly on top of the floor (and of each other's ribs), so every layer has full support from the layer below. The only overhang is the connector cutout's horizontal hole, which prints with a short self-supporting bridge at its top — expected, not a defect (print-check §8 exception, noted in the coupon's own header comment). |
| `tg-ladder` | **Flat, base plate down.** | Base is a simple flat plate; tongues/grooves project upward, no bridging. Brim recommended — base footprint is 230×36 mm, the longest single dimension of any coupon here. |
| `insert-boss` | **Flat, base plate down**, boss bores facing up. | `mcc_heat_set_boss()` bores open upward (blind bore, axis vertical) — true-circle print, no bridging, matches the "hole axis vertical" rule for any boss/insert hole. |
| `tolerance-ladder` | **Flat, base plate down**, pegs facing up. | Peg/hole axis vertical for both the printed pegs and the through-holes in the base — true circles, no bridging. |

## Print settings (ASA, Bambu Studio) — print-check §4

Enclosure closed · nozzle ~260 °C · bed 105–110 °C · **Bambu ASA** (or Generic ASA) filament profile
· textured PEI or engineering plate + glue · 5 walls / 3 mm · aux/part-cooling fan low · brim on
`tg-ladder` (230 mm long, ASA warp risk at that length) · standard (not maxed) infill.

## Measurement forms

Fill in after printing and measuring with calipers. Write the accepted value back into
`lib/mcc/constants.scad` at the cited symbol, with a comment naming this coupon and the measurement
date (`.claude/knowledge/testing.md` "Where coupon measurements get written back"). If the coupon
also carries a `confidence` field for the thing it calibrates (e.g. a `MCC_PANEL_PARTS` row's
`plug_len`/`bend`), bump that row's `confidence` toward `"measured"` at the same time — a calibrated
number under a stale `confidence: "drawing"` still reads as unverified.

### neutrik-tile

- Print both variants (see "Render" above): NAHDMI-W-B (23.6-class) and NE8FDP-B (24.0-class).
- For each: press-fit the *real* connector (Neutrik NAHDMI-W-B / NE8FDP-B, black) into the cutout.
  - Does the flange seat flush against the tile's front face, with no visible gap or forced flex?
  - Do both M3-class screws line up with the rear bosses and thread in without cross-threading or
    stripping the boss?
  - Is there any slop (connector rocks/rotates in the hole) or is it a firm, square seat?
- **Good** = flush seat, both screws thread cleanly, no perceptible rock.
- Record: connector class, fit quality (slop / snug / tight-needs-force), whether either screw
  stripped the boss.
- Update: `lib/mcc/constants.scad` → `MCC_HOLE_COMP` (currently `0.2` mm). If the hole was too tight,
  increase; if there was excessive slop, decrease (in ~0.05 mm steps) and re-print this coupon to
  confirm before touching a full case.

### depth-mockup

- Slide the real mating patch cable's plug into the connector end and read the 5 mm scale tick where
  the plug body stops (or, for a cable that reaches through, where the cable's jacket/strain-relief
  boot meets the mock face block).
- Does the cable bend comfortably within the jig's lateral clearance, or does it bind against the
  stiffening ribs/floor edges?
- **Good** = the plug fully seats against (or short of) the mock face block with the cable's natural
  bend radius unforced.
- Record: connector class, measured seating depth (mm, from the flange front), whether the cable
  needed to bend tighter than comfortable.
- Update: `lib/mcc/constants.scad` → `MCC_PANEL_PARTS["<part>"]` → `plug_len` (replacing the current
  `assumed` value) and, if the lateral bend was noticeably tighter/looser than budgeted, `bend` too.
  Bump that row's `confidence` from `"drawing"` toward `"measured"`.

### tg-ladder

- Try to slide each tongue into its matching groove (5 pairs, labelled 0.15/0.20/0.25/0.30/0.35 mm
  per-side clearance).
- Find the **tightest** clearance that still slides freely along its full 14 mm engagement length by
  hand, with no force and no visible rock/play once seated.
- **Good** = smallest labelled clearance that slides in and out without forcing, but doesn't wobble.
- Record: which labelled clearance value felt right, and how the adjacent (tighter/looser) pairs
  compared.
- Update: `lib/mcc/constants.scad` → `MCC_CLR_TG` (currently `0.25` mm, per-side).

### insert-boss

- Heat the tip of a soldering iron (or the insert press) to ~250 °C. Press one M3 Ruthex RX-M3x5.7
  insert into each of the 6 bores (3.8/3.9/4.0/4.1/4.2/4.3 mm).
- For each: does the insert seat flush with firm, even hand pressure (steady sinking, no sudden
  plunge), and does the boss stay intact (no visible split/crack/bulge)?
- **Good** = firm, controlled seating to flush depth, boss unmarked. Too loose = insert sinks with no
  resistance or spins freely once cool. Too tight = boss cracks/splits or the insert won't reach flush
  depth.
- Record: which bore diameter(s) gave a good seat, and the failure mode (loose vs. split) for the
  ones that didn't.
- Update: `lib/mcc/constants.scad` → `MCC_INSERT_M3` → `hole_d` entry (currently `4.0` mm).

### tolerance-ladder

- Try each of the 7 peg/hole pairs (0.10 → 0.40 mm per-side clearance, 0.05 mm steps), Ø6 mm
  nominal peg.
- Find the **loosest** clearance that still counts as a **press fit** (needs deliberate hand force to
  seat, stays put under its own weight once pressed — this calibrates `MCC_CLR_PRESS`) and,
  separately, the **tightest** clearance that counts as a free **sliding fit** (slides under its own
  weight or light finger pressure, no wobble — this calibrates `MCC_CLR_SLIDE`).
- Record both clearance values and a one-line description of the fit at each step tried.
- Update: `lib/mcc/constants.scad` → `MCC_CLR_SLIDE` (currently `0.3` mm) and `MCC_CLR_PRESS`
  (currently `0.1` mm).

## print-log.md

`print-log.md` in this directory is a blank template — copy a row per print attempt (date, coupon,
filament, plate, settings, measured result) rather than overwriting history.
