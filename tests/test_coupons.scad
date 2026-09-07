//////////////////////////////////////////////////////////////////////
// tests/test_coupons.scad
//   Documentation-only. `use`s nothing from lib/mcc/** — coupons are standalone top-level files
//   (models/coupons/*.scad) rendered directly by scripts/build.py, not exercised through a
//   library `use`/`include` chain. This file records the render command shape for each coupon so
//   it is discoverable from tests/ alongside the rest of the Tier-2 suite, and still renders
//   cleanly to .csg (exit 0) so it participates in the same "render every test" verification
//   pass as the other tests here.
//
// Render commands (PowerShell; see also scripts/render.ps1, which wraps scripts/build.py):
//   $env:OPENSCADPATH = "<repo>\lib"
//   & "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
//       -o out\neutrik-tile.stl models\coupons\neutrik-tile.scad
//   & "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
//       -D 'connector="NE8FDP-B"' -o out\neutrik-tile-ne8fdp.stl models\coupons\neutrik-tile.scad
//   & "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
//       -o out\depth-mockup.stl models\coupons\depth-mockup.scad
//   & "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
//       -o out\tg-ladder.stl models\coupons\tg-ladder.scad
//   & "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
//       -o out\insert-boss.stl models\coupons\insert-boss.scad
//   & "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
//       -o out\tolerance-ladder.stl models\coupons\tolerance-ladder.scad
//
// Run this file itself:
//   openscad --backend=Manifold -o out.csg tests/test_coupons.scad
//////////////////////////////////////////////////////////////////////

echo("mcc test_coupons: documentation only, see render commands above — OK");

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
