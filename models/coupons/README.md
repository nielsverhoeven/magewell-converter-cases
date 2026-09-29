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
| `neutrik-tile.scad` | A real Neutrik D-series connector (NAHDMI-W-B 23.6-class default, NE8FDP-B 24.0-class variant) passes through a **standing** section of the case's patch wall (D36: no panel plate; D40: perfectly round seat hole and window) and seats flush despite any sag at the top of the printed arch; its two ⌀2.5 mm fixing bores (D41: plain M3×0.5 tap-drill bores, no printed thread) line up with the flange holes and are round; once the threading route is chosen (architecture.md §12 Q20) the thread holds ≥5 in/out cycles (M19) | `lib/mcc/constants.scad` : `MCC_HOLE_COMP` (cross-checks each `MCC_PANEL_PARTS[<part>].hole_d`); reports on `MCC_FIXING_BORE_D` (a user decision — report, don't tune) |
| `depth-mockup.scad` | The real mating patch cable's plug seats with a comfortable bend at the budgeted bay depth | `lib/mcc/constants.scad` : `MCC_PANEL_PARTS[<part>].plug_len` (cross-checks `.bend`) |
| `tg-ladder.scad` | Which tongue-and-groove per-side clearance slides freely without slop | `lib/mcc/constants.scad` : `MCC_CLR_TG` |
| `insert-boss.scad` | Which M3 heat-set insert bore diameter seats with firm hand pressure in ASA without splitting the boss | `lib/mcc/constants.scad` : `MCC_INSERT_M3` → `hole_d` entry |
| `tolerance-ladder.scad` | Which round peg/hole per-side clearance is a free slide vs. a firm press fit | `lib/mcc/constants.scad` : `MCC_CLR_SLIDE` (slide), `MCC_CLR_PRESS` (press) |
| `side-bolt.scad` | The captive 1/4"-20 side bolt (D-09, **flush per D-13**): the real slotted screw seats with its head recessed, a DIN 6799 E-clip snaps into the pocket and holds the screw captive, the screw reaches its engagement length into a nut behind the EPDM pad, and the ASA **central support web** (root fillet retired by D-13) carries real clamp load down to the coupon's own base plate without cracking or needing slicer supports | `lib/mcc/constants.scad` : `MCC_SIDE_BOLT_HEAD_D`/`_HEAD_H`/`_HEAD_REC_D`/`_HEAD_REC_H`, `MCC_SIDE_BOLT_WEB_T`, `MCC_SIDE_BOLT_CLIP`, `MCC_SIDE_BOLT_POCKET_D`/`_POCKET_H`, `MCC_SIDE_BOLT_ENGAGE`, `MCC_SIDE_BOLT_PAD_OD`/`_PAD_ID`, `MCC_SIDE_BOLT_SCREW_LEN`, `MCC_GAP_FAR`, `MCC_SIDE_BOLT_PROUD`, `MCC_SIDE_BOLT_SUPPORT_WEB_T`, `MCC_SIDE_BOLT_AXIS_Z` |
| `rail-lock.scad` | The tool-less dovetail mount rail (D-15; wide, flush, ≥ 0.5 mm clearance since D44; 136 mm since D64.1) and its **top lock** (D63.1): the dovetail slides freely with the expected play, the groove roof (a ~66 mm bridge printed exactly like the case floor, split once by the lock's full-width slot) does not sag into the 0.5 mm roof gap, the case-side lead-in guides the rail in, and — with the rail plate vertical and the groove half loaded and hanging — the lock clicks, cannot be pulled off along the rail, and releases when the groove half is pulled about 1 mm away from the plate and slid | `lib/mcc/constants.scad` : `MCC_RAIL_ROOF_CLR` (raise it if the roof sags — never narrow the rail), `MCC_RAIL_LOCK_ENGAGE` (the e-ladder); confirms (does not calibrate) `MCC_RAIL_MATE_CLR`, a user decision |

## Render

```powershell
.venv\Scripts\python scripts\build.py render --all --format both
.venv\Scripts\python scripts\build.py check --all
.venv\Scripts\python scripts\build.py golden
```

`render --all` picks up every coupon automatically (`scripts/build.py`'s `discover_coupons()`
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
| `neutrik-tile` | **Standing on its foot, as modelled** — the wall section stands exactly like the case's patch wall (D36). | It has to test the real print orientation: the round hole's arch printed standing (D40, architecture.md R39) and the horizontal ⌀2.5 fixing bores (D41). A flat-printed tile would pass where the case fails. |
| `depth-mockup` | **Flat, floor plate down on the bed**, walls rising vertically out of the floor. No supports needed. | A flat-printing U-channel: the floor plate is the bed-contact face, and both the panel wall and the mock-face wall stack directly on top of the floor (and of each other's ribs), so every layer has full support from the layer below. The only overhang is the connector cutout's horizontal hole, which prints with a short self-supporting bridge at its top — expected, not a defect (print-check §8 exception, noted in the coupon's own header comment). |
| `tg-ladder` | **Flat, base plate down.** | Base is a simple flat plate; tongues/grooves project upward, no bridging. Brim recommended — base footprint is 230×36 mm, the longest single dimension of any coupon here. |
| `insert-boss` | **Flat, base plate down**, boss bores facing up. | `mcc_heat_set_boss()` bores open upward (blind bore, axis vertical) — true-circle print, no bridging, matches the "hole axis vertical" rule for any boss/insert hole. |
| `tolerance-ladder` | **Flat, base plate down**, pegs facing up. | Peg/hole axis vertical for both the printed pegs and the through-holes in the base — true circles, no bridging. |
| `side-bolt` | **Print flat on the base**, wall slab vertical, boss/support-web horizontal off the wall, self-supporting. As modeled: the small base pad is the bed-contact face and stands in for the case's interior floor; the wall slab rises vertically off it and the boss protrudes horizontally off the wall at the real (unscaled) axis height above the base — the same orientation the far wall prints in on a full case. No rotation needed. | Matches how `shell.scad` will eventually orient this feature (a horizontal boss off a vertical wall). Since D-13 the boss is flush and a **central vertical support web** (`mcc_captive_side_bolt_boss()`'s `support_web_t`/`web_to_floor_h`) — not a root fillet — carries the cantilever down to the base plate; whether that web alone prints clean without slicer supports is exactly what this coupon exists to verify. |
| `rail-lock` | **Print as modelled, no rotation:** the groove half stands directly on the bed, groove mouth down (like the case floor); the rail half stands on its own plate, rail up (like a bracket). Two thin snap-off strips join them — break them off before testing. | Both halves in their production print pose: the groove roof prints as the same ~66 mm bridge as on a real base (architecture.md R40), the lock's roof slot, its backing and the lead-in print like the case's, and the rail's lock strips stand on its top like on a bracket. |

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
- For each: fit the *real* connector (Neutrik NAHDMI-W-B / NE8FDP-B, black) into the cutout.
  - Measure the seat hole and the window with calipers **horizontally and vertically**: the top of
    the round hole prints as an arch (D40, architecture.md R39) — note any sag at the top.
  - Does the connector body pass, and does the flange seat flush against the tile's front face,
    with no visible gap or forced flex?
  - Do both ⌀2.5 mm fixing bores line up with the flange's two screw holes, and are they round and
    about ⌀2.5 (a ⌀2.5 drill shank should pass with light friction)? They are plain tap-drill
    bores (D41, no printed thread): a stock M3 machine screw does **not** thread in until the bore
    has been threaded.
  - Only once the user has picked the threading route (architecture.md §12 Q20): thread one tile
    that way and screw the connector in and out **≥5 times** — does it hold without stripping?
  - Is there any slop (connector rocks/rotates in the hole) or is it a firm, square seat?
- **Good** = connector passes, flush seat, no perceptible rock, both bores aligned and round, and
  (after Q20) the chosen thread survives ≥5 cycles.
- Record: connector class, horizontal/vertical hole diameters, fit quality (slop / snug /
  tight-needs-force), bore diameter and alignment, and — after Q20 — the threading route and how
  many cycles it survived.
- Update: `lib/mcc/constants.scad` → `MCC_HOLE_COMP` (currently `0.2` mm). If the hole was too tight,
  increase; if there was excessive slop, decrease (in ~0.05 mm steps) and re-print this coupon to
  confirm before touching a full case. Report the hole-sag and bore results to the teamlead
  (architecture.md M19): the round hole shape and `MCC_FIXING_BORE_D` are user decisions (D40/D41) —
  do not change them from this coupon.

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

### side-bolt

- Hardware needed: one 1/4"-20 slotted screw (~23.5 mm overall, `MCC_SIDE_BOLT_SCREW_LEN` = 19.05 mm
  under the head), one DIN 6799 nominal-size-5 E-clip, one 1/4"-20 nut (stands in for the device's
  own threaded hole, held behind the pad face), and a ⌀18/⌀8 mm EPDM pad (or the nearest sourced
  substitute, `fasteners-and-hardware.md:186`).
- Does the screw head sit **at or below** the coupon's outer surface once driven home (no proud
  metal — the "drop rule")?
- Does the DIN 6799 E-clip snap into the pocket by hand, and does it then hold the screw captive
  (screw cannot pull out, but the clip can still be picked back out with a small tool to release
  it)?
- Hold a 1/4"-20 nut behind the pad face (simulating the device's thread) and drive the screw in:
  does it reach its full `engage` (6.0 mm assumed) length of thread engagement before the head
  bottoms out in its recess?
- Inspect the retaining web (behind the head recess) and the **central support web** (D-13 — runs
  from the boss down to the base plate, replacing the old root fillet) after repeated
  screw-in/screw-out cycles: any cracking, splitting, or visible stress whitening in the ASA,
  especially at the web-to-boss and web-to-base junctions?
- Does the boss print without needing slicer-added support material in the recommended orientation
  (flat on the base, wall vertical, boss horizontal)? The support web (`support_web_t`/
  `web_to_floor_h`) is exactly what this print is testing for self-support — if it still needs
  slicer supports in practice, note whether a thicker `MCC_SIDE_BOLT_SUPPORT_WEB_T` or simply
  enabling supports for this one feature is the more practical fix.
- **Good** = head fully recessed, clip snaps in and retains the screw, full `engage` reached before
  the head bottoms out, no cracking at either web, and the boss either prints clean or the support
  requirement is recorded as an accepted trade-off.
- Record: which hardware was actually used (exact screw/clip/nut/pad part numbers if sourced),
  fit/retention quality, any cracking, and the support-material finding.
- Update: `lib/mcc/constants.scad` → the `MCC_SIDE_BOLT_*` block (head ⌀/height once a real screw
  is sourced, per M5; `MCC_SIDE_BOLT_CLIP` once DIN 6799 is confirmed, per M4; `MCC_SIDE_BOLT_ENGAGE`
  once the device's thread depth is measured, per M2; `MCC_SIDE_BOLT_AXIS_Z` once the device's side
  hole `v` is measured, per M1 — this coupon renders at the current `pos [0,0]` placeholder) and
  bump `confidence` from `"assumed"` toward `"measured"` as each figure is confirmed.

### rail-lock

- Hardware needed: a luggage/fish scale, a dummy mass of the heaviest case (weigh one assembled case
  with its device; ≈ 0.8 kg `assumed` until weighed) that can be strapped to the groove half, a
  temporary loop (string/cable tie), a board to screw or clamp the rail half to vertically, calipers.
- Snap the two joining strips off first.
- **Roof sag (R40):** before inserting anything, measure the groove roof's height above the groove
  half's bottom face at mid-width, at both ends and in the middle (nominal 4.0 mm), and the lock slot's
  ceiling (nominal 5.1 mm). The rail's own top is 3.5 mm tall and its strips 4.6 mm: the roof must stay
  clear of the rail top, and the strip tops must pass under the roof with the groove half lifted.
- **Play (R41):** lying flat, slide the rail half in from the open (+X) end until it stops. With the
  strips *not yet* under the roof (rail only partly in), measure the lateral play (≈ 1.15 mm total)
  and how far the groove half lifts off the rail's plate before it binds (≈ 1.0 mm; the lock needs at
  least `MCC_RAIL_LOCK_ENGAGE` + 0.3 = 0.9 mm of it).
- **Lock, hanging:** clamp the rail half's plate vertical, slide axis horizontal, the rail's strips'
  square faces toward the rail's free end. Strap the dummy mass to the groove half. Hang the groove
  half on the rail's free end and push it along: it must ride over the strips without binding and
  click in. Then (a) pull the groove half along the rail, away from the stop, via the loop at the rail
  line: it must not release up to ≥ 50 N (record where and how it fails if it does); (b) push the
  groove half up from below with about 3 × its weight, then pull it along the rail: no release;
  (c) tug the groove half's lower edge outward, away from the plate, then pull along the rail: no
  release; (d) pull the groove half away from the plate until it stops (≤ 1.2 mm) and slide it off: it
  must release one-handed.
- **e-ladder:** the teamlead or tester produces the extra 3MFs at `LOCK_E` 0.4 / 0.5 / 0.7 for you
  (`python scripts/build.py render coupons/rail-lock -D LOCK_E=0.4`, then 0.5, then 0.7, copying
  `exports/coupons/rail-lock/rail-lock.3mf` aside after each run, then re-running
  `render coupons/rail-lock` without `-D` to restore the release export) — you do not run `build.py`
  yourself. Print each and repeat "Play" and "Lock, hanging" on it, and pick the largest strip that
  never binds.
- **Cycling:** 100 insert/remove cycles on the production copy, then repeat "Play" and "Lock,
  hanging"; inspect the strips' square faces and the slot's +X wall for crushing or wear.
- **Good** = no roof contact, smooth slide-in with a clean click, locked against (a)–(c), one-handed
  pull-and-slide release, play within the expected figures, no wear after 100 cycles.
- Record: roof and slot heights, play and lift, click quality, the pull forces reached in (a), the
  e-ladder results, wear after cycling.
- Update: `lib/mcc/constants.scad` → `MCC_RAIL_ROOF_CLR` if the roof sags into the gap (raise it;
  never narrow the rail — user decision D44), `MCC_RAIL_LOCK_ENGAGE` from the e-ladder. If the play is
  objectionable, report it — `MCC_RAIL_MATE_CLR` is a user decision, not a coupon result.

## print-log.md

`print-log.md` in this directory is a blank template — copy a row per print attempt (date, coupon,
filament, plate, settings, measured result) rather than overwriting history.
