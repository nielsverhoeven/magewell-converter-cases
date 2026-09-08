//////////////////////////////////////////////////////////////////////
// LibFile: mcc/shell.scad
//   L2. The composition root (architecture.md §3 rev 5, sanctioned exception): the ONLY L2 file
//   allowed to `use` its L2 peers cradle.scad/mounts.scad/vents.scad. Owns the outer box, the
//   tongue-and-groove closure, the patch-wall stepped rabbet + discrete windows (never a bare
//   `use <neutrik.scad>` — goes through mcc_panel_cutout()/mcc_panel_plate() per architecture.md
//   §5), the fan/splitter bay reservations, the side-bolt boss/cut, and the 6 lid-fastener bosses
//   with their gusset webs. `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>
use <layout.scad>
use <panel.scad>       // mcc_panel_cutout(), mcc_panel_fixing_pos() indirectly via layout.scad
use <fasteners.scad>
use <fan.scad>
use <poe_splitter.scad>
use <cradle.scad>
use <mounts.scad>
use <vents.scad>

// -----------------------------------------------------------------------------------------
// Section: Private helpers shared by base and lid
// -----------------------------------------------------------------------------------------

// Function: _mcc_h_int()
// Description:
//   Private. Interior clear height (floor top to lid underside), mm — always 45.0 on every
//   current SKU (MCC_PANEL_BAND/MCC_PLATE_H never vary), matches mcc_case_layout()'s own H_int.
function _mcc_h_int() = MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND;

// Module: _mcc_outer_shell_solid()
// Description:
//   Private. The additive box both base and lid start from, minus the interior cavity (open at
//   z=z_top so the caller can further carve floor/lid-specific features), inset by MCC_WALL on
//   -Y/±X and MCC_T_PATCH on +Y (the patch wall's thicker bezel+seat+lip stack, §2.1).
// Arguments:
//   L, W  = case footprint, mm.
//   z_lo, z_hi = outer solid's own Z range.
//   cav_z_lo, cav_z_hi = interior cavity's Z range (independent of the outer solid's own range —
//                        e.g. the base's cavity opens past its own top face so the lid can close
//                        over it).
module _mcc_outer_shell_solid(L, W, z_lo, z_hi, cav_z_lo, cav_z_hi) {
    difference() {
        translate([-L / 2, -W / 2, z_lo])
            cube([L, W, z_hi - z_lo]);
        translate([-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, cav_z_lo])
            cube([L - 2 * MCC_WALL, W - MCC_WALL - MCC_T_PATCH, cav_z_hi - cav_z_lo]);
    }
}

// Module: _mcc_gusset_web()
// Description:
//   Private. A MCC_WALL-thick rectangular web from a lid-fastener boss at (x,y) to the nearest
//   wall's inner face, spanning z=[z_lo,z_hi] — so the boss is not a free-standing cantilever
//   pillar (this file's module contract). Direction (X or Y, toward whichever wall is nearer) is
//   picked per-call so corner bosses (equidistant from two walls at MCC_FASTENER_INSET) still get
//   exactly one web, per the task contract's "a ... gusset web to THE NEAREST wall" (singular).
// Arguments:
//   x, y       = boss centre, mm.
//   L, W       = case footprint, mm.
//   z_lo, z_hi = web Z range, mm.
//   boss_r     = boss radius, mm (the web starts at the boss's own edge, not its centre).
module _mcc_gusset_web(x, y, L, W, z_lo, z_hi, boss_r) {
    d_xpos = L / 2 - x; d_xneg = x - (-L / 2);
    d_ypos = W / 2 - y; d_yneg = y - (-W / 2);
    dmin = min([d_xpos, d_xneg, d_ypos, d_yneg]);

    if (dmin == d_xpos)
        translate([x + boss_r - MCC_EPS, y - MCC_WALL / 2, z_lo])
            cube([d_xpos - boss_r + 2 * MCC_EPS, MCC_WALL, z_hi - z_lo]);
    else if (dmin == d_xneg)
        translate([x - d_xneg - MCC_EPS, y - MCC_WALL / 2, z_lo])
            cube([d_xneg - boss_r + 2 * MCC_EPS, MCC_WALL, z_hi - z_lo]);
    else if (dmin == d_ypos)
        translate([x - MCC_WALL / 2, y + boss_r - MCC_EPS, z_lo])
            cube([MCC_WALL, d_ypos - boss_r + 2 * MCC_EPS, z_hi - z_lo]);
    else
        translate([x - MCC_WALL / 2, y - d_yneg - MCC_EPS, z_lo])
            cube([MCC_WALL, d_yneg - boss_r + 2 * MCC_EPS, z_hi - z_lo]);
}

// Function: _mcc_cavity_rect()
// Description:
//   Private. [x0, y0, w, h] of the interior-cavity footprint (the same rectangle
//   _mcc_outer_shell_solid() subtracts), shared by the tongue/groove helper below so the two can
//   never disagree about where the cavity boundary actually is.
function _mcc_cavity_rect(L, W) =
    [-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, L - 2 * MCC_WALL, W - MCC_WALL - MCC_T_PATCH];

// Module: _mcc_tg_frame()
// Description:
//   Private. A rectangular picture-frame ring, radially offset from the interior-cavity boundary
//   by [r_lo, r_hi] (positive = grow OUTWARD, toward the wall's own outer face; negative = shrink
//   INWARD, toward the interior) — the shared shape both the base's tongue (D-07, r=[0,MCC_TG_W])
//   and the lid's matching groove (r=[-MCC_CLR_TG, MCC_TG_W+MCC_CLR_TG]) are built from, so the two
//   can never drift out of the "groove width = tongue width + 2*clearance" relationship
//   (tg-ladder.scad's own convention).
// Arguments:
//   cav        = [x0,y0,w,h] cavity rect (_mcc_cavity_rect()).
//   r_lo, r_hi = radial offsets from the cavity boundary, mm.
//   z0, height = Z placement.
module _mcc_tg_frame(cav, r_lo, r_hi, z0, height) {
    x0 = cav[0]; y0 = cav[1]; w = cav[2]; h = cav[3];
    translate([x0 - r_hi, y0 - r_hi, z0])
        difference() {
            cube([w + 2 * r_hi, h + 2 * r_hi, height]);
            translate([r_hi - r_lo, r_hi - r_lo, -MCC_EPS])
                cube([w + 2 * r_lo, h + 2 * r_lo, height + 2 * MCC_EPS]);
        }
}

// Module: _mcc_patch_wall_rabbet()
// Description:
//   Private, SUBTRACTIVE. The ONE continuous stepped rabbet for the whole panel plate
//   (layout-patch-wall.md §2.5): a 6 mm-deep pocket (from the wall's outer face) over the plate's
//   own rim_w border ring (accommodating the plate's 3 mm rim thickness), 5 mm deep over the field
//   (accommodating the 2 mm field) — implemented as a 5 mm full-footprint cut plus an extra 1 mm
//   frame-shaped cut (footprint minus the field inset) reaching from 5 mm to 6 mm. Both sized to
//   the plate footprint + MCC_CLR_SLIDE per side. Residual structural lip: 3 mm behind the field,
//   2 mm behind the rim ring (both >= the 2.0 mm minimum).
// Arguments:
//   plate_size = [w, h] plate footprint (unclearanced), mm.
//   rim_w      = plate rim width, mm (matches mcc_panel_plate()'s own default, 6).
//   y_outer    = the patch wall's outer face Y, mm (= +W/2).
//   z_c        = the panel band's Z centre (z_conn_c), mm.
module _mcc_patch_wall_rabbet(plate_size, rim_w, y_outer, z_c) {
    w = plate_size[0] + 2 * MCC_CLR_SLIDE;
    h = plate_size[1] + 2 * MCC_CLR_SLIDE;
    fw = plate_size[0] - 2 * rim_w; // field width (no extra clearance -- an internal step boundary)
    fh = plate_size[1] - 2 * rim_w;

    field_depth = MCC_PANEL_BEZEL_T + MCC_PANEL_SEAT_T; // 5.0
    rim_depth   = MCC_PANEL_BEZEL_T + MCC_WALL;          // 6.0
    assert(MCC_T_PATCH - rim_depth >= 2.0,
        str("mcc: patch-wall rabbet residual lip ", MCC_T_PATCH - rim_depth, " below the 2.0 mm minimum over the rim"));
    assert(MCC_T_PATCH - field_depth >= 2.0,
        str("mcc: patch-wall rabbet residual lip ", MCC_T_PATCH - field_depth, " below the 2.0 mm minimum over the field"));

    // Full-footprint cut, 5 mm deep (the field's own depth).
    translate([-w / 2, y_outer - field_depth, z_c - h / 2])
        cube([w, field_depth + MCC_EPS, h]);

    // Rim-frame extra 1 mm, from 5 mm to 6 mm depth -- only over the border ring.
    difference() {
        translate([-w / 2, y_outer - rim_depth, z_c - h / 2])
            cube([w, rim_depth - field_depth + MCC_EPS, h]);
        translate([-fw / 2, y_outer - rim_depth - MCC_EPS, z_c - fh / 2])
            cube([fw, rim_depth - field_depth + 2 * MCC_EPS, fh]);
    }
}

// Module: _mcc_patch_wall_window()
// Description:
//   Private, SUBTRACTIVE. ONE discrete window through the 3 mm structural lip behind the rabbet
//   (layout-patch-wall.md §2.5, rev 6 — deviation D9, §15 ruling 2026-09-08b). REV 6: a union() of
//   three separate 2-D profiles — NEVER a hull() — so the assembled patch wall reads as *exactly
//   round* from outside: (i) the body opening, a plain clearance circle truncated-teardropped
//   above its 45 deg tangent line (mcc_aperture_window()'s d_win/cap_h — self-supporting, and the
//   body-opening boundary hides entirely behind the plate's own smaller cutout); (ii)+(iii) two
//   plain boss-relief circles at the plate's own screw positions, small enough
//   (< MCC_APERTURE_SELF_SUPPORT_MAX_D) to need no teardrop of their own. The rev-5 hull() of the
//   same three circles produced a diagonal blob *narrower than the plate's own D cutout on its
//   two diagonal flanks*, so its outline showed through every plate hole — the user rejected it on
//   sight (2026-09-08) and was right: the hull also removed ~35% more of the structural lip than
//   the union, exactly where the plate's 2 mm flange seat needs backing (architecture.md §5 R4).
//   For DBA-BL-B (a blank — no body opening) only the two relief circles are emitted, since the
//   blank still carries the plate's usual rear screw bosses (panel.scad's mcc_panel_plate() gives
//   every slot the same bosses regardless of part).
// Arguments:
//   part  = panel part number at this slot (key into MCC_PANEL_PARTS).
//   y_lo, y_hi = the lip's own Y range to cut through (y_lo < y_hi).
//   x_c, z_c   = slot centre (slot_x(i), z_conn_c), mm.
module _mcc_patch_wall_window(part, y_lo, y_hi, x_c, z_c) {
    aw = mcc_aperture_window(part);
    d_win = aw[0]; d_rel = aw[1]; cap_h = aw[2]; w_flat = aw[3];
    is_blank = mcc_panel_hole_d(part) == 0;
    sx = MCC_D_SCREW_PITCH[0] / 2; sz = MCC_D_SCREW_PITCH[1] / 2;

    // T1-34a (layout-patch-wall.md §2.5/§9, rev 6) -- the union's own shape rules, checked once
    // per slot at render time. Retires T1-34 (satisfied, but under-specified, by the rejected
    // hull()).
    assert(is_blank || w_flat <= MCC_APERTURE_BRIDGE_MAX + MCC_EPS,
        str("mcc: T1-34a window w_flat=", w_flat, " exceeds MCC_APERTURE_BRIDGE_MAX=", MCC_APERTURE_BRIDGE_MAX, " for \"", part, "\""));
    assert(d_rel <= MCC_APERTURE_SELF_SUPPORT_MAX_D + MCC_EPS,
        str("mcc: T1-34a relief d_rel=", d_rel, " exceeds MCC_APERTURE_SELF_SUPPORT_MAX_D=", MCC_APERTURE_SELF_SUPPORT_MAX_D, " for \"", part, "\""));
    assert(is_blank || cap_h > mcc_cutout_d(part) / 2,
        str("mcc: T1-34a cap_h=", cap_h, " does not clear mcc_cutout_d(part)/2=", mcc_cutout_d(part) / 2, " for \"", part, "\""));

    translate([0, (y_lo + y_hi) / 2, 0])
        rotate([90, 0, 0])
            linear_extrude(height = y_hi - y_lo, center = true)
                translate([x_c, z_c])
                    union() {
                        if (!is_blank)
                            teardrop2d(d = d_win, ang = 45, cap_h = cap_h, $fn = 96);
                        // Relief positions must coincide with the PLACED plate's rear bosses, not
                        // with the plate's authored front-view pattern. The plate is authored with
                        // its screw holes/bosses at local (-9.5, +12) and (+9.5, -12) (Neutrik
                        // front view, mcc_neutrik_d_cutout()); case.scad places it with
                        // rotate([-90,0,0]), which maps local (x, y) -> world (x, z = -y). This 2-D
                        // frame is (x, z) (rotate([90,0,0]) above maps 2-D y -> world z), so the
                        // bosses land at (-sx, -sz) and (+sx, +sz). Using the un-flipped diagonal
                        // here mirrors the pattern against the plate (user-reported 2026-09-08:
                        // "screw holes look rotated 90 deg vs the holes in the base").
                        translate([-sx, -sz]) circle(d = d_rel, $fn = 64);
                        translate([sx, sz]) circle(d = d_rel, $fn = 64);
                    }
}

// Module: _mcc_patch_wall_aperture()
// Description:
//   Private, SUBTRACTIVE. The whole patch-wall aperture for `dev`: one rabbet (see above) plus one
//   window per slot (T1-34a-d, rev 6), plus the 4 plate-retention M3 heat-set bores at
//   mcc_panel_fixing_pos() (deviation D6 -- matches the ALREADY-IMPLEMENTED mcc_panel_plate()
//   exactly, never the doc's own superseded numbers).
// Arguments:
//   l   = mcc_case_layout() struct.
//   dev = device record.
module _mcc_patch_wall_aperture(l, dev) {
    W = struct_val(l, "W");
    plate_size = struct_val(l, "plate_size");
    z_c = struct_val(l, "z_conn_c");
    slot_x = struct_val(l, "slot_x");
    n_slots = struct_val(l, "n_slots");
    slots = mcc_slot_assignment(dev);
    rim_w = MCC_PLATE_RIM_W; // mcc_panel_plate()'s own default rim_w -- named once, constants.scad.

    y_outer = W / 2;
    y_lip_lo = W / 2 - MCC_T_PATCH; // patch-wall inner face
    y_lip_hi = W / 2 - MCC_T_PATCH + MCC_WALL; // = rabbet floor at field depth (5mm in), i.e. y_outer-5

    _mcc_patch_wall_rabbet(plate_size, rim_w, y_outer, z_c);

    for (i = [0:1:n_slots - 1]) {
        s = slots[i];
        part = struct_val(s, "part");
        _mcc_patch_wall_window(part, y_lip_lo - MCC_EPS, y_lip_hi + MCC_EPS, slot_x[i], z_c);
    }
}

// Module: _mcc_patch_wall_fixing_bosses()
// Description:
//   Private, ADDITIVE. Each of the 4 plate-retention M3 heat-set-insert bosses stands rearward off
//   the rabbet lip's inner face (§2.3 "bosses standing rearward off the rabbet lip") at
//   mcc_panel_fixing_pos() (deviation D6, matches the ALREADY-IMPLEMENTED mcc_panel_plate()
//   exactly). `anchor = BOTTOM` places the boss's own local Z=0 at the rear tip (deepest into the
//   interior, world Y = y_lip_inner - boss_h) and local Z=boss_h at the front, plate-facing
//   bearing face flush with the rabbet lip's inner face (world Y = y_lip_inner).
//   DEVIATION D10, RESOLVED (rev 6, 2026-09-08 — architecture.md §13): this boss now carries a
//   real M3 bore, resolved LOCALLY inside this module via a per-boss difference() rather than the
//   split add-then-cut-in-the-outer-difference() pattern used for the tripod/VESA floor bosses
//   (mcc_tripod_insert_bore_cut() / mcc_floor_bore_cut() in mcc_shell_base() — see that module's
//   own comment for why that split exists there: an overlapping un-bored sibling solid backfills a
//   bore cut only in the outer difference()). That split pattern is NOT needed here because
//   nothing else in the union() overlaps one of these bosses — and it was independently retried
//   and confirmed NOT to fix the failure below.
//   ROOT CAUSE, diagnosed by isolated bisection (not merely "the rabbet cut interferes" — that
//   turned out not to be it; the failure reproduces even with the aperture entirely absent): the
//   boss's front (plate-facing) face is flush with y_lip_inner, exactly where the wall's own solid
//   material begins. Unioning a PLAIN (unbored) cylinder there against the wall merges cleanly
//   (`build.py check --all`: parts=1) with any amount of overlap, none, or several mm. The instant
//   the boss carries ANY blind bore — mcc_heat_set_bore()'s own padded cylinder, or a bare
//   hand-rolled one, regardless of overlap depth (MCC_EPS through 2 mm, all tried) — the union
//   comes back with the boss adrift as its own disconnected component (`n_parts` = 1(shell) + one
//   per bored boss). This is a genuine Manifold/pinned-OpenSCAD-2025.09.07 robustness limit for
//   "solid-with-a-blind-cavity unioned flush against a face of another solid", not a modelling
//   error in this file, and not fixable by re-ordering this file's own CSG tree (isolated,
//   minimal repros confirm it — see this milestone's own verification notes).
//   FIX (escalation option (a), generalised): make the bore a genuine THROUGH-hole, open at BOTH
//   the front (plate-facing) face AND the boss's own rear tip, instead of a blind pocket. Nothing
//   in this boss's own function needs the rear tip to stay solid (unlike mcc_neutrik_d_bosses(),
//   this boss carries no other feature there), so there is no design cost. The bore keeps T1-35's
//   two-diameter shape (insert.hole_d for the insert's own length, MCC_M3_CLR_D screw clearance for
//   the remainder) — it simply no longer stops short of either end. Verified by isolated bisection
//   AND by `build.py check --all`: `base.stl` watertight, parts=1. The insert side faces the rear
//   tip (deepest into the interior, most accessible before the lid closes); the M3 clearance side
//   faces the plate — the screw enters through the plate's own already-cut clearance hole
//   (mcc_panel_plate()) and drives through the clearance bore into the insert. T1-35.
// Arguments:
//   plate_size = [w, h] plate footprint, mm.
//   rim_w      = plate rim width, mm.
//   y_outer    = patch wall outer face Y, mm.
//   z_c        = panel band Z centre, mm.
module _mcc_patch_wall_fixing_bosses(plate_size, rim_w, y_outer, z_c) {
    boss_h = 7; // matches mcc_neutrik_d_bosses()'s own default boss_h (architecture.md §5).
    boss_od = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od");
    y_lip_inner = y_outer - MCC_T_PATCH;
    insert_hole_d = struct_val(MCC_INSERT_M3, "hole_d");

    // T1-35: no solid material anywhere on the screw axis between the boss's own front (plate-
    // facing) face and the insert. insert_bore_depth (from the rear tip) + thru_depth (screw
    // clearance, to the front) together span the WHOLE boss_h -- a genuine through-hole, not a
    // blind pocket (see the module comment above for why a blind pocket does not render here).
    insert_bore_depth = struct_val(MCC_INSERT_M3, "len") + MCC_INSERT_BORE_EXTRA;
    thru_depth = boss_h - insert_bore_depth;
    assert(thru_depth >= 0,
        str("mcc: T1-35 fixing-boss thru_depth=", thru_depth, " negative — boss_h=", boss_h,
            " too short for insert_bore_depth=", insert_bore_depth));

    for (p = mcc_panel_fixing_pos(plate_size, rim_w))
        translate([p[0], y_lip_inner - boss_h, z_c + p[1]])
            rotate([-90, 0, 0])
                difference() {
                    cyl(h = boss_h, d = boss_od, circum = true, anchor = BOTTOM, $fn = 64);
                    // Insert bore: opens past the rear tip (Z=-MCC_EPS, anchor=BOTTOM) so it
                    // genuinely punches through rather than kissing the boss's own end cap, and
                    // extends forward by insert_bore_depth.
                    translate([0, 0, -MCC_EPS])
                        cyl(h = insert_bore_depth + MCC_EPS, d = insert_hole_d, circum = true, anchor = BOTTOM, $fn = 64);
                    // Screw-clearance through-bore: carries the axis the rest of the way past the
                    // front (plate-facing) face, for the same reason.
                    if (thru_depth > 0)
                        translate([0, 0, insert_bore_depth])
                            cyl(h = thru_depth + MCC_EPS, d = MCC_M3_CLR_D, circum = true, anchor = BOTTOM, $fn = 64);
                }
}

// -----------------------------------------------------------------------------------------
// Section: mcc_shell_base() / mcc_shell_lid()
// -----------------------------------------------------------------------------------------

// Module: mcc_shell_base()
// Usage:
//   mcc_shell_base(dev, cfg);
// Description:
//   The base half: floor + 4 walls (open top) + the raised tongue along the inner top perimeter
//   (D-07), the patch-wall stepped rabbet + windows, the side-bolt boss/cut (far wall), the 6
//   lid-fastener heat-set bosses (each with a gusset web), the case's own floor features
//   (mounts.scad) and cradle (cradle.scad), minus the far/-X/+X wall vent arrays (vents.scad,
//   never the patch wall — T1-19). Fan/splitter bays are ALWAYS reserved (architecture.md §6):
//   the fan aperture is only actually cut when `cfg`'s "fan" flag is true; the splitter bay is
//   never cut into the shell at all (it is empty interior volume by construction — only
//   mounts.scad's tie-down and the reservation asserts below touch it).
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list (keys: "external_ports", "fan", "splitter", optionally
//         "fan_y", "vesa").
module mcc_shell_base(dev, cfg) {
    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W"); H = struct_val(l, "H");
    h_int = _mcc_h_int();
    z_top = MCC_FLOOR_T + h_int; // 48.0 -- base walls run floor..z_top; the tongue continues above it.
    x_bolt = struct_val(l, "side_bolt_x"); z_bolt = struct_val(l, "side_bolt_z");
    fan_pos = struct_val(l, "fan_pos");
    lid_pos = struct_val(l, "lid_fastener_pos");
    boss_r_lid = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od") / 2;

    // --- Tier-1 asserts owned by this module ---
    assert(mcc_bbox_ok([L, W, H]),
        str("mcc: mcc_shell_base bbox ", [L, W, H], " exceeds the printable envelope"));
    assert(MCC_SIDE_BOLT_PROUD == 0,
        "mcc: T1-29 MCC_SIDE_BOLT_PROUD must be 0 (flush, D-13) for the production shell");
    // T1-18(c), re-scoped (layout-patch-wall.md §9): axial cable clearance for the +X end zone vs.
    // the fan bay's own clearance depth.
    pos_ext = [for (p = mcc_ports_external(dev)) if (mcc_port_face(p)[0] > 0) p];
    axial_terms = [for (p = pos_ext)
        let(kind = mcc_port_kind(p), panel = mcc_port_panel(p))
        (kind == "bnc") ? mcc_plug_len("NBB75DFGB") : mcc_dev_side_allow(kind) - mcc_bend_envelope(panel)];
    fan_env_depth = struct_val(mcc_fan_spec("NF-A4x10"), "frame")[2] + 5;
    assert(struct_val(l, "x_dev_hi") + max(concat([0], axial_terms)) <= L / 2 - MCC_WALL - fan_env_depth + MCC_EPS,
        str("mcc: T1-18(c) +X axial cable clearance fails on \"", mcc_dev_slug(dev), "\""));
    // Reservation rule (architecture.md §6): the splitter bay must never intrude into the device's
    // own cradle footprint or the far-wall duct.
    assert(struct_val(l, "splitter_bay_x")[1] <= struct_val(l, "x_dev_lo") + MCC_EPS,
        "mcc: splitter bay reservation collides with the device envelope");

    union() {
        difference() {
            union() {
                _mcc_outer_shell_solid(L, W, 0, z_top, MCC_FLOOR_T, z_top + MCC_EPS);

                // Tongue (D-07): offset/shiplap, flush with the wall's inner face, rev-5 ruling 4.
                // Grows OUTWARD (toward the wall's own outer face) by MCC_TG_W from the
                // interior-cavity footprint, so it sits ON TOP of solid wall material (every wall
                // is >= MCC_TG_W thick) rather than cantilevering out over open interior air.
                // Starts MCC_EPS below z_top so it genuinely penetrates the wall's own solid
                // there instead of merely sitting flush on its top face — an exact coincident
                // planar face between two independently-extruded solids is a known Manifold/
                // STL-export degeneracy (same class of fix as the bore cuts split out below).
                _mcc_tg_frame(_mcc_cavity_rect(L, W), 0, MCC_TG_W, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);

                // Side-bolt boss (far wall, D-09/D-13) -- exact placement per the developer contract.
                translate([x_bolt, -W / 2 - MCC_SIDE_BOLT_PROUD, z_bolt])
                    rotate([-90, 0, 0])
                        mcc_captive_side_bolt_boss(web_to_floor_h = z_bolt - MCC_FLOOR_T);

                // 6 lid-fastener heat-set bosses, h=45 (top at z=48), each with a gusset web.
                for (p = lid_pos) {
                    translate([p[0], p[1], MCC_FLOOR_T])
                        mcc_heat_set_boss(h = z_top - MCC_FLOOR_T);
                    _mcc_gusset_web(p[0], p[1], L, W, MCC_FLOOR_T, z_top, boss_r_lid);
                }

                mcc_cradle(dev, cfg);
                mcc_floor_features_add(dev, cfg);

                _mcc_patch_wall_fixing_bosses(struct_val(l, "plate_size"), MCC_PLATE_RIM_W, W / 2, struct_val(l, "z_conn_c"));
            }

            _mcc_patch_wall_aperture(l, dev);

            // Bore cuts for the tripod-insert and VESA "boss from below" features, which were
            // split into a plain-solid ADD (above, inside the union) plus a separate bore CUT
            // (here, in the OUTER difference) — see cradle.scad's mcc_tripod_insert_bore_cut() and
            // mounts.scad's mcc_floor_bore_cut() for why: a bore differenced only against its own
            // boss's local geometry gets silently backfilled by an overlapping, un-bored sibling
            // solid (the floor slab). The 4 patch-wall plate-fixing bosses do NOT need this split
            // — their bore (D10, rev 6, resolved) is cut locally inside
            // _mcc_patch_wall_fixing_bosses() itself, since nothing else in the union() overlaps
            // one of those bosses; see that module's own comment for the fuller history.
            mcc_tripod_insert_bore_cut(dev, cfg);
            mcc_floor_bore_cut(dev, cfg);

            translate([x_bolt, -W / 2 - MCC_SIDE_BOLT_PROUD, z_bolt])
                rotate([-90, 0, 0])
                    mcc_captive_side_bolt_cut();

            if (struct_val(cfg, "fan") == true)
                mcc_vents(dev, cfg, [1, 0, 0]);

            mcc_vents(dev, cfg, [0, -1, 0]);
            mcc_vents(dev, cfg, [-1, 0, 0]);

            mcc_floor_features_cut(dev, cfg);
        }
    }
}

// Module: mcc_shell_lid()
// Usage:
//   mcc_shell_lid(dev, cfg);
// Description:
//   The lid half: a flat MCC_LID_T slab spanning [H-MCC_LID_T, H], with the mating groove (D-07)
//   cut into its underside (MCC_TG_W+2*MCC_CLR_TG wide, MCC_TG_H deep, leaving 1.0 mm of lid above
//   it — rev-5 ruling 4 / T1-33), and 6 captive-thumbscrew holes at the same `lid_fastener_pos`
//   the base's bosses use. No cradle, no floor features, no side-bolt feature (all base-only). No
//   vent cuts on this SKU: both vent bands (intake z=[5,23], exhaust z=[32,44]) sit entirely below
//   the lid's own Z range (verified below by assert rather than assumed).
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_shell_lid(dev, cfg) {
    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W"); H = struct_val(l, "H");
    z_top = MCC_FLOOR_T + _mcc_h_int(); // 48.0, lid underside
    lid_pos = struct_val(l, "lid_fastener_pos");

    assert(MCC_TG_H + 1.0 <= MCC_LID_T,
        str("mcc: T1-33 MCC_TG_H+1.0=", MCC_TG_H + 1.0, " exceeds MCC_LID_T=", MCC_LID_T));
    assert(MCC_TG_W + 2 * MCC_CLR_TG <= MCC_WALL - 0.8,
        str("mcc: T1-33 tongue+clearance ", MCC_TG_W + 2 * MCC_CLR_TG, " does not fit MCC_WALL-0.8=", MCC_WALL - 0.8));
    // This SKU's vent bands never cross into the lid's own Z range -- confirmed, not assumed
    // (plan §3.2's own caveat: "confirm this numerically before assuming it generalizes").
    assert(struct_val(l, "vent_intake_z")[1] <= z_top,
        "mcc: intake vent band crosses into the lid on this SKU -- lid-side venting is not implemented");
    assert(struct_val(l, "vent_exhaust_z")[1] <= z_top,
        "mcc: exhaust vent band crosses into the lid on this SKU -- lid-side venting is not implemented");

    difference() {
        translate([-L / 2, -W / 2, z_top])
            cube([L, W, MCC_LID_T]);

        // Groove (D-07): the picture-frame-shaped cut that receives the base's tongue. MCC_CLR_TG
        // wider on BOTH its inner and outer edge than the tongue — "groove width = tongue width +
        // 2*clearance", this repo's own tg-ladder.scad convention — via the same _mcc_tg_frame()
        // helper mcc_shell_base()'s tongue uses, so the two can never drift apart.
        _mcc_tg_frame(_mcc_cavity_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);

        for (p = lid_pos)
            translate([p[0], p[1], z_top - MCC_EPS])
                mcc_captive_thumbscrew_hole(lid_t = MCC_LID_T + 2 * MCC_EPS);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
