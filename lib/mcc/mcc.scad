//////////////////////////////////////////////////////////////////////
// LibFile: mcc/mcc.scad
//   Barrel. `include`s constants.scad and `use`s every L1/L2 library file built so far
//   (architecture.md:94-97). Model/coupon/test files `include <mcc/mcc.scad>` (never `use` it —
//   `use` would not propagate the constants.scad variables or the transitively-used L1/L2
//   modules/functions out to the includer). Library files import their own direct dependencies,
//   never this barrel (architecture.md:96-97 "importing the barrel from inside the library
//   creates cycles").
//
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>

include <constants.scad>
use <util.scad>
use <ports.scad>
use <layout.scad>
use <neutrik.scad>
use <fasteners.scad>
use <fan.scad>
use <poe_splitter.scad>
use <ghost.scad>
use <panel.scad>
use <cradle.scad>
use <mounts.scad>
use <vents.scad>
use <shell.scad>

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
