//////////////////////////////////////////////////////////////////////
// LibFile: mcc/shell.scad
//   L2. The composition root (architecture.md §3 rev 5, sanctioned exception): the ONLY L2 file
//   allowed to `use` its L2 peers cradle.scad/mounts.scad/vents.scad. Owns the outer box, the
//   tongue-and-groove closure, the patch wall's connector recess with the connectors cut straight
//   into it (D36 — never a bare `use <neutrik.scad>`, always through mcc_panel_wall_cut(),
//   architecture.md §5), the fan/splitter bay reservations, the side-bolt boss/cut, and the 6 lid-fastener bosses
//   with their gusset webs. `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>
use <layout.scad>
use <panel.scad>       // mcc_panel_wall_cut()
use <fasteners.scad>
use <fan.scad>         // mcc_fan_envelope() -- the reservation ghost in mcc_shell_base(). Do not
                       // remove: an unknown module call only WARNS, it does not fail the render.
use <switch.scad>
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
//   Private. The web that ties a lid-fastener boss at (x,y) to the nearest wall, spanning
//   z=[z_lo,z_hi] — so the boss is not a free-standing pillar. Direction (X or Y, toward whichever
//   wall is nearer) is picked per-call so corner bosses (equidistant from two walls at
//   MCC_FASTENER_INSET) still get exactly one web.
//   D38 (2026-09-28): the web is as WIDE AS THE BOSS — the hull of the boss circle and a boss-wide
//   bar running into the wall, i.e. a stadium that merges the boss into the wall. Its first form
//   was a MCC_WALL-wide bar that started at the boss's outer edge, so the two only touched along
//   the circle's tangent line — the modeller's "the supports barely touch the screw pillars".
//   The web's own footprint stops MCC_WEB_BORE_KEEP short of the boss's outer radius on the boss
//   side (an annulus overlap, never a coincident face), so the boss's insert bore stays clear.
//   It runs 0.5 mm into the floor and stops 0.5 mm inside the wall's outer face (both overlaps
//   with solid material, not touching faces — openscad-authoring "coincident faces").
// Arguments:
//   x, y       = boss centre, mm.
//   L, W       = case footprint, mm.
//   z_lo, z_hi = web Z range, mm.
//   boss_r     = boss radius, mm.
module _mcc_gusset_web(x, y, L, W, z_lo, z_hi, boss_r) {
    d_xpos = L / 2 - x; d_xneg = x - (-L / 2);
    d_ypos = W / 2 - y; d_yneg = y - (-W / 2);
    dmin = min([d_xpos, d_xneg, d_ypos, d_yneg]);
    // Unit direction toward the chosen wall, and the reach from the boss centre to 0.5 mm inside
    // that wall's outer face.
    dir = (dmin == d_xpos) ? [1, 0] : (dmin == d_xneg) ? [-1, 0] : (dmin == d_ypos) ? [0, 1] : [0, -1];
    reach = dmin - 0.5;
    assert(reach > boss_r, str("mcc: D38 boss at ", [x, y], " is not clear of its wall"));
    bore_keep = boss_r - MCC_WEB_BORE_KEEP;

    translate([x, y, z_lo - 0.5])
        linear_extrude(height = z_hi - z_lo + 0.5)
            difference() {
                hull() {
                    // 0.2 mm inside the boss's own (circumscribed) 64-gon: two near-identical
                    // polygons would leave zero-area slivers on the shared top/bottom planes.
                    circle(r = boss_r - 0.2, $fn = 64);
                    translate(dir * reach)
                        square([dir[0] == 0 ? 2 * boss_r : 0.02, dir[1] == 0 ? 2 * boss_r : 0.02], center = true);
                }
                circle(r = bore_keep, $fn = 64);
            }
}

// Function: _mcc_tg_rect()
// Description:
//   Private. [x0, y0, w, h] of the rectangle the tongue-and-groove frame is offset from (see
//   _mcc_tg_frame()), shared by the base's tongue and the lid's groove so the two can never disagree.
//   On the -Y and +-X sides it is the interior-cavity boundary (tongue flush with the wall's inner
//   face, layout-patch-wall.md §15 ruling 4); on the +Y patch side its edge sits MCC_TG_PATCH_INSET
//   from the wall's outer face, clear of the lid's countersinks (D62.1, D100.1, T1-62.1). T1-62.2
//   guards the constant here, where both halves consume it.
function _mcc_tg_rect(L, W) =
    assert(MCC_TG_PATCH_INSET >= MCC_WALL - MCC_EPS && MCC_TG_PATCH_INSET <= MCC_T_PATCH + MCC_EPS,
        str("mcc: T1-62.2 MCC_TG_PATCH_INSET=", MCC_TG_PATCH_INSET, " outside [MCC_WALL=", MCC_WALL,
            ", MCC_T_PATCH=", MCC_T_PATCH, "]"))
    [-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, L - 2 * MCC_WALL, W - MCC_WALL - MCC_TG_PATCH_INSET];

// Module: _mcc_tg_frame()
// Description:
//   Private. A rectangular picture-frame ring, radially offset from the edge of `rect`
//   (_mcc_tg_rect()) by [r_lo, r_hi] (positive = grow OUTWARD, toward the wall's own outer face;
//   negative = shrink INWARD, toward the interior) — the shared shape both the base's tongue (D-07,
//   r=[0,MCC_TG_W]) and the lid's matching groove (r=[-MCC_CLR_TG, MCC_TG_W+MCC_CLR_TG]) are built
//   from, so the two can never drift out of the "groove width = tongue width + 2*clearance"
//   relationship (tg-ladder.scad's own convention).
// Arguments:
//   rect       = [x0,y0,w,h] frame reference rect (_mcc_tg_rect()) -- NOT the interior cavity on
//                the +Y patch wall (D62.1).
//   r_lo, r_hi = radial offsets from `rect`'s edge, mm.
//   z0, height = Z placement.
module _mcc_tg_frame(rect, r_lo, r_hi, z0, height) {
    x0 = rect[0]; y0 = rect[1]; w = rect[2]; h = rect[3];
    translate([x0 - r_hi, y0 - r_hi, z0])
        difference() {
            cube([w + 2 * r_hi, h + 2 * r_hi, height]);
            translate([r_hi - r_lo, r_hi - r_lo, -MCC_EPS])
                cube([w + 2 * r_lo, h + 2 * r_lo, height + 2 * MCC_EPS]);
        }
}

// Module: _mcc_patch_wall_recess()
// Description:
//   Private, SUBTRACTIVE. The bezel recess the connectors sit in (D36, 2026-09-28 — the connectors
//   mount straight into the patch wall; there is no panel plate and no rabbet any more): a
//   MCC_PANEL_BEZEL_T-deep pocket in the wall's outer face over the old plate footprint, whose
//   floor is the flange-seat plane. The shell around it is the protective bezel (ruggedness rule:
//   connectors recessed behind the shell). Its ROOF is a chamfer rising outward (~50 deg), so the
//   wall — printed standing — never overhangs the recess (the old rabbet's 6 mm roof was the
//   "floating cantilever" D32 worked around). Both ends and the floor of the recess are plain
//   vertical/upward faces.
// Arguments:
//   size    = [w, h] recess footprint on the wall face, mm (layout "plate_size").
//   y_outer = the patch wall's outer face Y, mm (= +W/2).
//   z_c     = the connector centreline Z (z_conn_c), mm.
//   z_max   = highest Z the chamfer may reach (the wall top), mm.
module _mcc_patch_wall_recess(size, y_outer, z_c, z_max) {
    w = size[0]; h = size[1];
    d = MCC_PANEL_BEZEL_T;
    z0 = z_c - h / 2; z1 = z_c + h / 2;
    assert(z1 + d <= z_max + MCC_EPS,
        str("mcc: D36 recess chamfer tops out at z=", z1 + d, " above the wall top ", z_max));
    // Roof rise per mm of depth: a touch steeper than 45 deg. At exactly 45 deg the chamfer runs
    // through the wall's top outer edge (z1 + d == the wall top on every SKU), and a cut plane
    // through an existing edge leaves zero-area slivers; steeper, it exits through the wall top
    // ~0.5 mm inside the outer face instead.
    k = 1.2;
    // YZ profile, extruded along X (rotate maps 2-D x -> world Y, 2-D y -> world Z).
    translate([-w / 2, 0, 0])
        rotate([90, 0, 90])
            linear_extrude(height = w)
                polygon([[y_outer - d, z0], [y_outer + 1, z0], [y_outer + 1, z1 + (d + 1) * k],
                         [y_outer - d, z1]]);
}

// Module: _mcc_patch_wall_aperture()
// Description:
//   Private, SUBTRACTIVE. The whole patch-wall connector field for `dev` (D36): the bezel recess
//   plus, per slot, mcc_panel_wall_cut() — a perfectly round seat hole + body window (D40) and the
//   two plain ⌀2.5 fixing bores (D41), through the MCC_PANEL_SEAT_T + MCC_WALL of wall left behind
//   the recess.
// Arguments:
//   l   = mcc_case_layout() struct.
//   dev = device record.
module _mcc_patch_wall_aperture(l, dev) {
    W = struct_val(l, "W");
    z_c = struct_val(l, "z_conn_c");
    slot_x = struct_val(l, "slot_x");
    slots = mcc_slot_assignment(dev);
    y_seat = W / 2 - MCC_PANEL_BEZEL_T;
    wall_t = MCC_T_PATCH - MCC_PANEL_BEZEL_T;

    _mcc_patch_wall_recess(struct_val(l, "plate_size"), W / 2, z_c, MCC_FLOOR_T + _mcc_h_int());

    // The cut's local frame is the wall seen from outside: local Z -> world +Y (outward), local
    // Y -> world +Z (up), hence local X -> world -X. rotate([90, 0, 180]) is exactly that map.
    for (i = [0:1:len(slots) - 1])
        translate([slot_x[i], y_seat, z_c])
            rotate([90, 0, 180])
                mcc_panel_wall_cut(struct_val(slots[i], "part"), wall_t = wall_t);
}

// -----------------------------------------------------------------------------------------
// Section: mcc_shell_base() / mcc_shell_lid()
// -----------------------------------------------------------------------------------------

// Module: mcc_shell_base()
// Usage:
//   mcc_shell_base(dev, cfg);
// Description:
//   The base half: floor + 4 walls (open top) + the raised tongue along the top perimeter (D-07;
//   flush with the inner face of the 3 mm walls, MCC_TG_PATCH_INSET from the patch wall's outer
//   face — D62.1), the patch-wall connector recess + connector cuts (D36), the side-bolt boss/cut (far wall), the 6
//   lid-fastener heat-set bosses (each with a gusset web), the case's own floor features
//   (mounts.scad) and cradle (cradle.scad), minus the far/-X/+X wall vent arrays (vents.scad,
//   never the patch wall — T1-19). Fan/splitter bays are ALWAYS reserved (architecture.md §6):
//   the fan aperture is only actually cut when `cfg`'s "fan" flag is true; the splitter bay is
//   never cut into the shell at all (it is empty interior volume by construction — only the
//   reservation asserts below and mounts.scad's T1-17 touch it).
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list (keys: "fan", "splitter", optionally "fan_y", "rail" — see
//         models/pro-convert-for-ndi-to-hdmi/case.scad's own top-of-file comment for the full
//         contract. NOT "external_ports": that key is INERT/DROPPED, D12, architecture.md §13 —
//         the slot set comes solely from mcc_ports_external(dev), i.e. the device file's own
//         `panel` field per port).
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
    // T1-18(c), re-scoped (layout-patch-wall.md §9), BNC double-count FIXED (§16.3 / §15 ruling
    // 2026-09-08c C3, architecture.md §13 blocking pre-flight change): axial cable clearance for
    // the +X end zone vs. the fan bay's own clearance depth. The axial term now reads
    // mcc_plug_axial(kind) uniformly for every kind — no `kind == "bnc"` special case. The old
    // code charged BNC's mcc_plug_len("NBB75DFGB") (= 40.6, the Belden 4855R bend radius, a
    // LATERAL figure re-used for that part's plug_len/bend table entries) against this AXIAL
    // budget, which double-counted a lateral allowance and failed by 14.60 mm on every BNC-ended
    // SKU. mcc_plug_axial() carries its own dedicated, `assumed`, per-kind axial table
    // (constants.scad MCC_PLUG_AXIAL) so no geometry moves for hdmi_a (still 25.0, matching the
    // old non-BNC branch's 40-15 decomposition exactly — T1-18(c) stays at 0.00 mm slack on every
    // HDMI-ended SKU) while bnc gets its own honest (if still assumed) axial figure instead of a
    // borrowed lateral one.
    pos_ext = [for (p = mcc_ports_external(dev)) if (mcc_port_face(p)[0] > 0) p];
    axial_terms = [for (p = pos_ext) mcc_plug_axial(mcc_port_kind(p))];
    fan_bay_x = struct_val(l, "fan_bay_x"); // single source of truth: layout.scad's
                                             // mcc_case_layout() (constants.scad
                                             // MCC_FAN_INTAKE_CLR) -- no local recompute (D23, #36).
    assert(struct_val(l, "x_dev_hi") + max(concat([0], axial_terms)) <= fan_bay_x[0] + MCC_EPS,
        str("mcc: T1-18(c) +X axial cable clearance fails on \"", mcc_dev_slug(dev), "\""));
    // Reservation rule (architecture.md §6): the splitter bay must never intrude into the device's
    // own cradle footprint or the far-wall duct.
    assert(struct_val(l, "splitter_bay_x")[1] <= struct_val(l, "x_dev_lo") + MCC_EPS,
        "mcc: splitter bay reservation collides with the device envelope");
    // D16 (architecture.md §13, fixed by issue #25): no two mcc_floor_keepout() rows overlap (no
    // exemptions since D44).
    mcc_assert_floor_keepout_no_overlap(dev, cfg);

    union() {
        difference() {
            union() {
                _mcc_outer_shell_solid(L, W, 0, z_top, MCC_FLOOR_T, z_top + MCC_EPS);

                // Tongue (D-07): offset/shiplap, flush with the inner face of the -Y/+-X walls and
                // MCC_TG_PATCH_INSET from the patch wall's outer face (_mcc_tg_rect()). Grows OUTWARD
                // (toward the wall's own outer face) by MCC_TG_W from that rectangle, so it sits ON TOP
                // of solid wall material (every wall is >= MCC_TG_W thick) rather than cantilevering
                // out over open interior air.
                // Starts MCC_EPS below z_top so it genuinely penetrates the wall's own solid
                // there instead of merely sitting flush on its top face — an exact coincident
                // planar face between two independently-extruded solids is a known Manifold/
                // STL-export degeneracy (same class of fix as the bore cuts split out below).
                _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = 0, r_hi = MCC_TG_W,
                              z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);

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

                // Fan switch pad (rev 11, #32, D-18): the +X wall is thickened INWARD locally so
                // the recess cut below (mcc_switch_cutout(), in the outer difference()) has
                // somewhere to sit -- D-13 pattern, no envelope figure moves. Same translate/
                // rotate convention as vents.scad's fan cutout (local Z=0 -> world inner face,
                // architecture.md rev-11 header finding B2 -- switch_pos[0] is the OUTER face).
                if (mcc_fan_switch_enabled(cfg)) {
                    switch_pos_add = struct_val(l, "switch_pos");
                    translate([L / 2 - MCC_WALL, switch_pos_add[1], switch_pos_add[2]])
                        rotate([0, 90, 0])
                            mcc_switch_pad(mcc_switch_spec(MCC_SWITCH_DEFAULT), wall_t = MCC_WALL);
                }
            }

            _mcc_patch_wall_aperture(l, dev);

            // Bore/groove cuts for the tripod-insert and mount-rail-sill "boss from below" features,
            // which were split into a plain-solid ADD (above, inside the union) plus a separate
            // CUT (here, in the OUTER difference) — see cradle.scad's mcc_tripod_insert_bore_cut()
            // and mounts.scad's mcc_rail_features_cut() for why: a bore/groove differenced only
            // against its own boss's local geometry gets silently backfilled by an overlapping,
            // un-cut sibling solid (the floor slab).
            // mcc_floor_bore_cut() is RETIRED (architecture.md §6 rev 9, R5, issue #25) — this call
            // site is now mcc_rail_features_cut(), the mount rail's own groove cut.
            mcc_tripod_insert_bore_cut(dev, cfg);
            mcc_rail_features_cut(dev, cfg);

            translate([x_bolt, -W / 2 - MCC_SIDE_BOLT_PROUD, z_bolt])
                rotate([-90, 0, 0])
                    mcc_captive_side_bolt_cut();

            if (struct_val(cfg, "fan") == true)
                mcc_vents(dev, cfg, [1, 0, 0]);

            // Fan switch cutout (rev 11, #32, D-18): translate([L/2-MCC_WALL, ...]) -- NOT
            // switch_pos[0]=L/2 directly -- copying vents.scad:146 exactly (architecture.md
            // rev-11 header finding B2: the naive translate cuts X in [L/2,L/2+3], outside the
            // shell, removes zero material, and shows a golden delta of exactly zero).
            if (mcc_fan_switch_enabled(cfg)) {
                switch_pos_cut = struct_val(l, "switch_pos");
                translate([L / 2 - MCC_WALL, switch_pos_cut[1], switch_pos_cut[2]])
                    rotate([0, 90, 0])
                        mcc_switch_cutout(mcc_switch_spec(MCC_SWITCH_DEFAULT), wall_t = MCC_WALL);
            }

            mcc_vents(dev, cfg, [0, -1, 0]);
            mcc_vents(dev, cfg, [-1, 0, 0]);
        }

        // Fan bay reservation ghost (architecture.md §6 rev 12, §13 D23, issue #36). The
        // reservation of RECORD is numeric -- fan_bay_x/y/z from mcc_case_layout(), enforced by
        // T1-46a-d there and by T1-18(c) above. This is its review-only visualization:
        // mcc_fan_envelope() is `%`-ed and gated behind MCC_SHOW_GHOST (default false), so it emits
        // nothing in any export and no golden can move.
        // TRANSFORM -- do NOT copy vents.scad's. mcc_fan_cutout()'s local Z spans the wall and is
        // placed with rotate([0,90,0]) (local +Z -> world +X, outward); mcc_fan_envelope()'s local
        // Z starts at the mounting plane and grows INTO the interior (fan.scad header), so it
        // needs rotate([0,-90,0]) (local +Z -> world -X). With rotate([0,90,0]) the whole
        // reservation lands OUTSIDE the case and, being a ghost, no check would report it.
        // The origin comes from the struct (fan_bay_x[1] == L/2 - MCC_WALL) so the ghost and the
        // asserted AABB cannot drift apart.
        translate([fan_bay_x[1], fan_pos[1], fan_pos[2]])
            rotate([0, -90, 0])
                mcc_fan_envelope();
    }
}

// Module: mcc_shell_lid()
// Usage:
//   mcc_shell_lid(dev, cfg);
// Description:
//   The lid half: a flat MCC_LID_T slab spanning [H-MCC_LID_T, H], with the mating groove (D-07)
//   cut into its underside (MCC_TG_W+2*MCC_CLR_TG wide, MCC_TG_H deep, leaving 1.0 mm of lid above
//   it — rev-5 ruling 4 / T1-33; offset outward on the patch wall, D62.1), and 6 countersunk-screw holes
//   (mcc_lid_screw_hole(), M3 ISO 10642, non-captive — D100.1) at the same `lid_fastener_pos` the base's
//   bosses use, each countersink rim >= MCC_LID_CB_WEB_MIN clear of the groove (T1-62.1). No cradle, no floor
//   features, no side-bolt feature (all base-only).
//   The existing far-wall/end-wall vent bands (intake z=[5,23], exhaust z=[32,44]) sit entirely
//   below the lid's own Z range on every current SKU (verified below by assert rather than
//   assumed) and get no cut here — but the lid DOES cut its own, independent top-exhaust vent
//   field (issue #24, mcc_lid_vents_cut(), vents.scad), gated on cfg["lid_vents"] (default true).
//   The floor stays closed: mcc_shell_base() is untouched by issue #24.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_shell_lid(dev, cfg) {
    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W"); H = struct_val(l, "H");
    z_top = MCC_FLOOR_T + _mcc_h_int(); // 48.0, lid underside
    lid_pos = struct_val(l, "lid_fastener_pos");

    lv_cfg = struct_val(cfg, "lid_vents");
    lid_vents_flag = is_undef(lv_cfg) ? true : lv_cfg;

    assert(MCC_TG_H + 1.0 <= MCC_LID_T,
        str("mcc: T1-33 MCC_TG_H+1.0=", MCC_TG_H + 1.0, " exceeds MCC_LID_T=", MCC_LID_T));
    assert(MCC_TG_W + 2 * MCC_CLR_TG <= MCC_WALL - 0.8,
        str("mcc: T1-33 tongue+clearance ", MCC_TG_W + 2 * MCC_CLR_TG, " does not fit MCC_WALL-0.8=", MCC_WALL - 0.8));
    // T1-62.1: web = countersink rim to the groove ring's inner edge (gi = [x0, y0, x1, y1]).
    // T1-62.2 fires inside _mcc_tg_rect().
    tg = _mcc_tg_rect(L, W);
    gi = [tg[0] + MCC_CLR_TG, tg[1] + MCC_CLR_TG, tg[0] + tg[2] - MCC_CLR_TG, tg[1] + tg[3] - MCC_CLR_TG];
    cb_r = mcc_lid_screw_hole_rim_r(csk_d = MCC_LID_CSK_D);
    for (p = lid_pos) {
        web = min([p[0] - gi[0], gi[2] - p[0], p[1] - gi[1], gi[3] - p[1]]) - cb_r;
        assert(p[0] > gi[0] && p[0] < gi[2] && p[1] > gi[1] && p[1] < gi[3],
            str("mcc: T1-62.1 lid fastener ", p, " is not inside the groove ring on \"", mcc_dev_slug(dev), "\""));
        assert(web >= MCC_LID_CB_WEB_MIN - MCC_EPS,
            str("mcc: T1-62.1 lid fastener ", p, " countersink rim is ", web, " mm from the groove, below MCC_LID_CB_WEB_MIN=",
                MCC_LID_CB_WEB_MIN, " on \"", mcc_dev_slug(dev), "\""));
    }
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
        _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = -MCC_CLR_TG, r_hi = MCC_TG_W + MCC_CLR_TG,
                      z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);

        for (p = lid_pos)
            translate([p[0], p[1], z_top])
                mcc_lid_screw_hole(lid_t = MCC_LID_T);

        // Lid vent field (issue #24) — gated in this ONE place; mcc_lid_vents_cut() does not
        // re-read cfg["lid_vents"] itself (layout-patch-wall.md §17.4: "gate the field in one
        // place").
        if (lid_vents_flag)
            mcc_lid_vents_cut(dev, cfg);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
