# models/brackets — mounting-bracket assemblies

Flat, single-part plates that carry the tool-less dovetail mount rail (`lib/mcc/rail.scad`,
issue #25 / D-15) so a case clicks onto some external mounting surface instead of (or in addition
to) sitting on its own floor. Structurally identical in shape to a `models/coupons/` target — no
base/lid split, no device record, no variant config — and discovered the same way, by
`scripts/build.py`'s `discover_brackets()` (mirrors `discover_coupons()` exactly; see
`docs/plans/2026-09-09-mount-rail-and-brackets.md` §3.2, `.claude/knowledge/layout-patch-wall.md`
§17.2).

## What each bracket carries

| Bracket | Carries | Mounting surface |
|---|---|---|
| `tv-bracket.scad` | VESA 100×100 (M4) + 200×200 (M6/M8) through-clearance hole patterns, sharing one centre; a "+" cross of stiffening ribs on the non-rail face; the male mount rail on the rail face | Sandwiched between a TV's own back panel and its existing wall/stand mount — the same screws that normally go TV→mount now go TV→(through this plate)→mount, clamping it captive. No new fasteners added to the BOM for the VESA side (see `BOM.md` "Mounting brackets"). |

Issue #27's truss bracket (`truss-bracket.scad`) is **deferred** — `layout-patch-wall.md` §17.1,
blocked on measurement M14 (a half-coupler's real bolt pattern) and a user safety sign-off (R26).
Not part of this directory yet.

## Orientation (issue #26's own acceptance criterion)

The rail lives on one flat face of the plate, the ribs on the other (`tv-bracket.scad`'s own
header comment has the full derivation and the exact `rotate([0,0,180])` reasoning). Convention:
**mount with the plate's own +Y axis pointing up** — the ordinary, unsurprising way to hang a
symmetric VESA square. With the rail placed as authored, a case slid onto it then hangs with its
patch (cable) wall facing down. See `.claude/skills/print-check/SKILL.md` for the one-line
go/no-go version of this note, and `tv-bracket.scad`'s `part == "assembly"` preview branch (a
ghost case mated onto the rail) for the render used to verify it visually rather than trust the
transform algebra alone.

**Open point, not blocking (flagged for the user/architect):** the VESA hole pattern is itself
left-right/up-down symmetric, so nothing in the hardware prevents installing the plate rotated
180° from the convention above — which would hang the case with its patch wall UP instead. No
keying feature exists to prevent this; would need an asymmetric marking feature to fix, out of
this ticket's scope.

## Render

```powershell
.venv\Scripts\python scripts\build.py render brackets/tv-bracket --format both
.venv\Scripts\python scripts\build.py check --all
.venv\Scripts\python scripts\build.py golden
```

`render --all` picks up every bracket automatically (`discover_brackets()` globs
`models/brackets/*.scad`).

## Orientation (Bambu Studio)

| Bracket | Orientation | Why |
|---|---|---|
| `tv-bracket` | **Flat, rail face up on the bed is easiest to print without supports on the taper's own 45°-ish flanks** — either face can print down since the plate is flat and thin, but printing rail-face-up keeps the dovetail taper and latch tab the only overhanging features, both within this repo's normal self-supporting-angle budget (same class of feature as `models/coupons/rail-latch.scad`'s own male half). | Flat plate, minimal warp risk at 6 mm thick; matches the existing rail-latch coupon's own proven orientation for the same dovetail profile. |
