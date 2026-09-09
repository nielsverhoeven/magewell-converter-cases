# Implementation plan — fan bay Y/Z footprint + duplicated intake-clearance literal (deviation D23)

Status: **PLANNED, not implemented.** Researched 2026-09-09 against `.claude/knowledge/architecture.md`
(rev 11) and `.claude/knowledge/layout-patch-wall.md` (rev 11) as they stand on `main`. **No GitHub
issue exists for this yet** — per `.claude/knowledge/ticket-source.md`, this plan file is itself the
durable record; there is nothing to post a ticket comment to.
**Team Charter gate reminder:** this is a code-changing plan and must go through `solution-architect`
validation before any developer starts. In particular the architect should rule on the two open
choices in §7 and confirm the T1-46 numbering is still free at implementation time.

---

## 0. The ask, restated precisely

Resolve **deviation D23** (`.claude/knowledge/architecture.md` §13, recorded 2026-09-09 in the
`solution-architect`'s verdict on `docs/plans/2026-09-09-fan-switch.md` §9.4, item 6):

> `mcc_fan_envelope()` (`lib/mcc/fan.scad:39`) is defined but **never called** anywhere in
> `shell.scad` — the fan bay's *depth* reservation is not actually wired up today, only the fan's
> live cutout is. **UPHELD, fix owner is a separate ticket, not this PR.** Nuance for the record:
> the bay's *depth* **is** reserved unconditionally by T1-18(c) at `shell.scad:376`; what is
> missing is **a single definition of the 5 mm intake clearance** — duplicated at `fan.scad:42`
> and `shell.scad:375` — **and any Y/Z footprint check**.

So D23's scope, as the architect scoped it, is exactly two things:

1. **One definition** of the fan bay's 5 mm intake clearance (today a bare literal `5` in two
   places: `fan.scad:42` inside `mcc_fan_envelope()`, and `shell.scad:375` inside the T1-18(c)
   assert as `... + 5`).
2. **A Y/Z footprint check** for the fan bay (today only its X depth is checked, via T1-18(c)).

It does **not** ask for the fan bay to be geometrically cut/subtracted for real — every existing
reservation in this repo (the PoE-splitter bay's T1-28, the fan bay's own T1-18(c)) is enforced by
**pure-number Tier-1 asserts**, never a CSG collision test, and this plan follows that same pattern.

**Do not touch:** `architecture.md`, `layout-patch-wall.md` (solution-architect owns both — it will
record D23 as Resolved there once this plan is validated and implemented), `BOM.md` (no part,
dimension, or default value changes), any GitHub issue (none exists).

---

## 1. Verified findings (re-derived from the code, not assumed)

- `lib/mcc/fan.scad:39-46` `mcc_fan_envelope(name)` — a plain, ungated reservation-box module
  (`cube(...)`, no `%`, no `MCC_SHOW_GHOST` gate). Grep of `lib/**`, `models/**`, `tests/**` confirms
  it is called **nowhere**. Its intake clearance is the literal `clr = 5;` at `fan.scad:42`.
- `lib/mcc/shell.scad:375` recomputes the same figure independently for the T1-18(c) assert
  (`shell.scad:376-377`): `fan_env_depth = struct_val(mcc_fan_spec("NF-A4x10"), "frame")[2] + 5;` —
  a second literal `5`, and a second hard-typed `"NF-A4x10"` string (also at `vents.scad:148`).
- T1-18(c) **does** run unconditionally (regardless of `cfg.fan`) and correctly reserves the bay's
  **X depth**. This is the "depth is reserved" half of the architect's nuance note (§0).
- **Nothing checks the bay's Y or Z footprint.** `mcc_case_layout()` publishes `splitter_bay_x/y/z`
  for the PoE-splitter bay but no `fan_bay_*` equivalent, and no assert checks the fan's Y-band
  against the `(+X, −Y)` corner lid-fastener boss/gusset, the connector bay's own Y-reach, or the
  floor/ceiling.
- **`layout.scad` cannot call `mcc_fan_spec()` today even if it wanted to** — it lives in `fan.scad`,
  an L1 *geometry provider*, and `layout.scad`'s own header contract (`layout.scad:8-11`) forbids
  `use`-ing one. So the Y/Z footprint check needs the move in §3 as a **precondition**, not a nicety.
- `architecture.md` **rev 11** (§3, lines 9-11, written for `docs/plans/2026-09-09-fan-switch.md` /
  issue #32, **not yet implemented** — `git log` shows no merge) already records this exact move —
  *"the pure accessor `mcc_fan_spec()` moves down to L0 `constants.scad` (with `MCC_FAN_DEFAULT`)
  so `layout.scad` can read the fan frame without importing an L1 geometry provider"* — as that
  plan's own dispatch step **B7** (`fan-switch.md` §9.6), noting *"no geometry change; no golden may
  move from this step."* **This plan performs that same move**, since it is required for the Y/Z
  check regardless. See §10 for what this means for whoever implements #32 afterward.
- Precedent for "un-orphaning" an `*_envelope()` module without wiring it into production geometry:
  `mcc_side_bolt_envelope()` (`fasteners.scad:343-355`) is **never called from `shell.scad` either**
  — it is exercised only from `tests/test_fasteners.scad:74`
  (`translate([220, 40, 0]) mcc_side_bolt_envelope();`, comment: *"gated behind `MCC_SHOW_GHOST` ...
  instantiate it anyway so a syntax/argument regression still fails the render."*). This plan follows
  that precedent for `mcc_fan_envelope()` — see §6.
- `mcc_splitter_envelope()` (`poe_splitter.scad:50-66`) is `mcc_fan_envelope()`'s closest sibling
  (architecture.md §6: *"`fan.scad` and `poe_splitter.scad` each expose an `*_envelope()` function
  used for reservation"*) and is **also** a plain, ungated `cube()`. See open choice §7.1.
- `tests/test_shell.scad`'s `VARIANT_FAN` branch (compact, `pro-convert-for-ndi-to-hdmi`) already
  exercises `mcc_fan_cutout()`; nothing here changes that branch or its golden.
- Numeric fan-bay world AABB today (default `fan_y = y_dev_c`, `z_conn_c = 25.5` fixed on every SKU):

  | Family (SKU) | `L` | `W` | `fan_y` | `fan_bay_x` | `fan_bay_y` | `fan_bay_z` |
  |---|---|---|---|---|---|---|
  | compact (`...-ndi-to-hdmi`) | 193.9 | 159.85 | −30.825 | [78.95, 93.95] | [−50.825, −10.825] | [5.5, 45.5] |
  | plus (`...-hdmi-plus`) | 210.5 | 166.35 | −30.825 | [87.25, 102.25] | [−50.825, −10.825] | [5.5, 45.5] |

  Margins against what §5's new asserts guard, compact: **14.96 mm** −Y to the corner boss,
  **12.10 mm** +Y to the connector bay's reach, **2.5 mm** to the floor and to the ceiling. All four
  pass today by construction — regression guards (T1-38's role in the fan-switch plan), not fixes to
  a live failure.

---

## 2. Design

**A.** `constants.scad` (L0): add `MCC_FAN_DEFAULT = "NF-A4x10"` and `MCC_FAN_INTAKE_CLR = 5.0`; move
the pure function `mcc_fan_spec()` here from `fan.scad` — single source of truth for both old
literals and the new `layout.scad` footprint check.

**B.** `fan.scad` (L1): remove the now-moved `mcc_fan_spec()`; `mcc_fan_envelope()` reads
`MCC_FAN_INTAKE_CLR` instead of its own local `clr = 5`; `mcc_fan_envelope()`/`mcc_fan_cutout()`
default `name` to `MCC_FAN_DEFAULT` so no call site needs to hard-type `"NF-A4x10"`.

**C.** `layout.scad` (L1): publish `fan_bay_x`/`fan_bay_y`/`fan_bay_z` (world AABB) from
`mcc_case_layout()` (same "read the L0 table directly, never a module" idiom as `splitter_bay_*`).
Add four new Tier-1 asserts, **T1-46a–d**, checking the bay's Y/Z footprint against the `(+X, −Y)`
corner lid-fastener boss/gusset, the connector bay's own reach, and the floor/ceiling.

**D.** `shell.scad` (L2): T1-18(c) reads `fan_bay_x[0]` from the layout struct instead of
recomputing `... + 5` — removes the second literal and the `mcc_fan_spec("NF-A4x10")` call.

**E.** `vents.scad` (L2): drop the `"NF-A4x10"` literal at the `mcc_fan_cutout()` call site.

**F.** Tests: `test_constants.scad` gains a "Fans" pin block; new `test_fan.scad` exercises
`mcc_fan_envelope()` (previously uncalled) per the `test_fasteners.scad` precedent; `test_layout.scad`
gains assertions on the new `fan_bay_*` fields.

No `architecture.md`/`layout-patch-wall.md`/`BOM.md` edits (§0). No golden should move (§9).

---

## 3. `lib/mcc/constants.scad` — ordered steps

1. Locate the existing "Section: Fans" block (currently around line 528, containing `MCC_FANS` and
   ending just before `MCC_VENT_AREA_RATIO`). Replace it with:

   ```openscad
   // -----------------------------------------------------------------------------------------
   // Section: Fans
   // knowledge/components/fans.md.
   // -----------------------------------------------------------------------------------------

   // [name, [["frame",[w,h,d]], ["pitch",p], ["hole_d",d]]] -- keep the existing per-row sourcing
   // comments verbatim (fans.md:15-18/42-45); only reproduced here without them for brevity.
   MCC_FANS = [
       ["NF-A4x10", [["frame", [40, 40, 10]], ["pitch", 32], ["hole_d", 4.3]]],
       ["NF-A6x25", [["frame", [60, 60, 25]], ["pitch", 50], ["hole_d", 4.3]]],
   ];

   // Default fan part, key into MCC_FANS. Mirrors MCC_SPLITTER_DEFAULT's role for MCC_SPLITTERS
   // below. architecture.md rev 11 §3.
   MCC_FAN_DEFAULT = "NF-A4x10";

   // Intake clearance beyond the fan's own frame depth, mm. assumed -- generic unobstructed-intake
   // allowance; no sourced figure in knowledge/components/fans.md (frame/pitch/hole_d only). Single
   // source of truth for the figure previously duplicated as a bare literal `5` at fan.scad's
   // mcc_fan_envelope() and shell.scad's T1-18(c) block. architecture.md §13 D23.
   MCC_FAN_INTAKE_CLR = 5.0;

   // Function: mcc_fan_spec()
   // Description:
   //   Looks up a fan record (frame/pitch/hole_d) from MCC_FANS by name. MOVED HERE from
   //   lib/mcc/fan.scad (L1) -- architecture.md rev 11 §3: a pure accessor over an L0 table was
   //   misplaced at L1, and layout.scad ("functions only, never an L1 geometry provider") needs it
   //   without importing fan.scad. fan.scad keeps calling this function unchanged.
   function mcc_fan_spec(name) =
       let(ind = search([name], MCC_FANS)[0])
       assert(ind != [], str("mcc: unknown fan \"", name, "\""))
       MCC_FANS[ind][1];

   MCC_VENT_AREA_RATIO = 1.0; // unchanged -- kept here verbatim, do not move or edit.
   ```

   This replaces the existing `MCC_FANS` block through `MCC_VENT_AREA_RATIO` with the above; nothing
   else in the file shifts meaning.

2. Nothing else in `constants.scad` changes. Do **not** touch `MCC_SPLITTERS`,
   `MCC_END_ZONE_NEG_EXTRA_SPLITTER`, or any other section.

---

## 4. `lib/mcc/fan.scad` — ordered steps

1. Delete the `mcc_fan_spec()` function (current lines 17-26) — it now lives in `constants.scad`
   (§3). Delete its doc comment along with it.

2. Change the module signature and body of `mcc_fan_envelope()` (current lines 28-46) — keep its
   existing doc comment, just update the "no sourced figure" clearance sentence to point at the new
   constant, and change the code to:

   ```openscad
   // Arguments:
   //   name = fan name, key into MCC_FANS. Default: MCC_FAN_DEFAULT. The real non-overlap
   //   enforcement is layout.scad's fan_bay_x/y/z asserts (T1-46a-d), not a CSG test against this
   //   module's own output -- same pattern as the PoE-splitter bay's T1-28.
   module mcc_fan_envelope(name = MCC_FAN_DEFAULT) {
       spec  = mcc_fan_spec(name);
       frame = struct_val(spec, "frame");
       translate([0, 0, (frame[2] + MCC_FAN_INTAKE_CLR) / 2])
           cube([frame[0], frame[1], frame[2] + MCC_FAN_INTAKE_CLR], center = true);
   }
   ```

3. Change `mcc_fan_cutout()`'s signature only (body unchanged): `name` gets the same default —
   `module mcc_fan_cutout(name = MCC_FAN_DEFAULT, wall_t = MCC_WALL, grille = false) {` — and update
   its doc-comment "Arguments" line for `name` to say `Default: MCC_FAN_DEFAULT.`

4. Leave `_mcc_fan_grille_2d()` untouched entirely.

---

## 5. `lib/mcc/layout.scad` — ordered steps

1. In `mcc_case_layout()`'s `let()` block, immediately after the existing binding
   `fan_pos = [L / 2, fan_y, z_conn_c],` (`layout.scad:404`), insert:

   ```openscad
        // Fan bay world AABB (architecture.md §13 D23). Reads MCC_FANS/MCC_FAN_INTAKE_CLR directly
        // (L0) -- this file may never `use` fan.scad (an L1 geometry provider). fan_bay_x is the
        // SAME quantity shell.scad's T1-18(c) checks against (read from this struct there now).
        fan_frame = struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame"),
        _fan_bay_square_check = assert(fan_frame[0] == fan_frame[1],
            str("mcc: T1-46 fan_bay_y/fan_bay_z assume a square MCC_FANS[\"", MCC_FAN_DEFAULT,
                "\"] frame (got ", fan_frame, ") -- rework the Y/Z half-extent below before making a "
                "non-square fan the default"))
            0,
        fan_bay_depth = fan_frame[2] + MCC_FAN_INTAKE_CLR,
        fan_bay_x = [L / 2 - MCC_WALL - fan_bay_depth, L / 2 - MCC_WALL],
        fan_bay_y = [fan_y - fan_frame[0] / 2, fan_y + fan_frame[0] / 2],
        fan_bay_z = [z_conn_c - fan_frame[0] / 2, z_conn_c + fan_frame[0] / 2],
   ```

   Do not use `fan_frame[1]` — the guard assert above is what makes reusing `fan_frame[0]` for both
   Y and Z half-extents safe (both current `MCC_FANS` rows are square; see §7's assumption list).

2. In the returned struct list (`layout.scad:475-489`), add one line immediately after
   `["fan_pos", fan_pos], ["fan_y", fan_y],`:

   ```openscad
        ["fan_bay_x", fan_bay_x], ["fan_bay_y", fan_bay_y], ["fan_bay_z", fan_bay_z],
   ```

3. In the existing Tier-1 assert chain (`layout.scad:452-474`), add four new asserts immediately
   after the existing T1-28 assert (`layout.scad:472-474`) and before the closing `[` that starts
   the returned list:

   ```openscad
       // Fan bay Y/Z footprint (architecture.md §13 D23) -- regression guards against the (+X,-Y)
       // corner lid-fastener boss/gusset, the connector bay's own plug reach, and the
       // floor/ceiling; all four pass today by construction (§1's worked numbers), so they exist
       // to catch a FUTURE change to fan_y/MCC_FANS/MCC_T_PATCH, not a live failure.
       assert(fan_bay_y[0] >= corners[1][1] + max(MCC_WALL / 2, boss_od_lid / 2) - MCC_EPS,
           str("mcc: T1-46a fan bay -Y edge ", fan_bay_y[0],
               " intrudes on the (+X,-Y) corner lid-fastener boss/gusset on \"", mcc_dev_slug(dev), "\""))
       assert(fan_bay_y[1] <= W / 2 - MCC_T_PATCH - d_bay_free + MCC_EPS,
           str("mcc: T1-46b fan bay +Y edge ", fan_bay_y[1],
               " intrudes on the connector bay's own plug reach on \"", mcc_dev_slug(dev), "\""))
       assert(fan_bay_z[0] >= MCC_FLOOR_T - MCC_EPS,
           str("mcc: T1-46c fan bay bottom ", fan_bay_z[0],
               " is below the interior floor on \"", mcc_dev_slug(dev), "\""))
       assert(fan_bay_z[1] <= MCC_FLOOR_T + H_int + MCC_EPS,
           str("mcc: T1-46d fan bay top ", fan_bay_z[1],
               " is above the interior ceiling on \"", mcc_dev_slug(dev), "\""))
   ```

   `corners[1]` is the `(+X, −Y)` corner (`layout.scad:423-424`). `boss_od_lid` (`layout.scad:437`),
   `d_bay_free` (`layout.scad:320`), `W`, `H_int` (`layout.scad:324`) are already bound earlier in
   the same `let()` — no new bindings are needed for the assert bodies.

4. **Numeric self-check**: for `pro-convert-for-ndi-to-hdmi` (compact), confirm
   `fan_bay_x == [78.95, 93.95]`, `fan_bay_y == [-50.825, -10.825]`, `fan_bay_z == [5.5, 45.5]`, and
   all four new asserts pass with the margins in §1's table. If any differ, re-read §1/§5 before
   continuing — do not adjust the assert thresholds to make a different number pass.

---

## 6. `lib/mcc/shell.scad` and `lib/mcc/vents.scad` — ordered steps

1. In `mcc_shell_base()` (`shell.scad:361-377`), replace:

   ```openscad
    pos_ext = [for (p = mcc_ports_external(dev)) if (mcc_port_face(p)[0] > 0) p];
    axial_terms = [for (p = pos_ext) mcc_plug_axial(mcc_port_kind(p))];
    fan_env_depth = struct_val(mcc_fan_spec("NF-A4x10"), "frame")[2] + 5;
    assert(struct_val(l, "x_dev_hi") + max(concat([0], axial_terms)) <= L / 2 - MCC_WALL - fan_env_depth + MCC_EPS,
        str("mcc: T1-18(c) +X axial cable clearance fails on \"", mcc_dev_slug(dev), "\""));
   ```

   with:

   ```openscad
    pos_ext = [for (p = mcc_ports_external(dev)) if (mcc_port_face(p)[0] > 0) p];
    axial_terms = [for (p = pos_ext) mcc_plug_axial(mcc_port_kind(p))];
    fan_bay_x = struct_val(l, "fan_bay_x"); // single source of truth: layout.scad's
                                             // mcc_case_layout() (constants.scad
                                             // MCC_FAN_INTAKE_CLR) -- no local recompute.
    assert(struct_val(l, "x_dev_hi") + max(concat([0], axial_terms)) <= fan_bay_x[0] + MCC_EPS,
        str("mcc: T1-18(c) +X axial cable clearance fails on \"", mcc_dev_slug(dev), "\""));
   ```

   Keep the long explanatory comment above this block (`shell.scad:361-372`, the BNC-double-count
   history) exactly as it is — do not duplicate or move it.

2. Do not add any call to `mcc_fan_envelope()` inside `mcc_shell_base()`/`mcc_shell_lid()` — this
   plan does not wire the envelope into production geometry (§1's `mcc_side_bolt_envelope()`
   precedent); it is exercised from a test file only (§8).

3. `vents.scad:148`, inside the `face == [1, 0, 0]` branch of `mcc_vents()`: change

   ```openscad
                mcc_fan_cutout("NF-A4x10", wall_t = MCC_WALL, grille = true);
   ```

   to:

   ```openscad
                mcc_fan_cutout(wall_t = MCC_WALL, grille = true);
   ```

   (relies on `mcc_fan_cutout()`'s new default from §4 step 3 — behavior is unchanged, since
   `MCC_FAN_DEFAULT == "NF-A4x10"`.) Leave the surrounding rotate/translate comment block
   (`vents.scad:142-145`) untouched.

---

## 7. Open choices for the architect (do not resolve silently either way)

### 7.1 Should `mcc_fan_envelope()` gain internal `%`/`MCC_SHOW_GHOST` gating?

Two live styles exist for an `*_envelope()` module: `mcc_side_bolt_envelope()`
(`fasteners.scad:343-355`) is internally gated (`if (MCC_SHOW_GHOST) { %cyl(...); }`) — a review-only
ghost; `mcc_splitter_envelope()` (`poe_splitter.scad:50-66`), `mcc_fan_envelope()`'s own documented
sibling (architecture.md §6), is a **plain, ungated** `cube()`. This plan (§4 step 2) leaves
`mcc_fan_envelope()` **ungated**, matching the closer sibling, on the reasoning that "reservation
shape, not ghost" is the role architecture.md §6 assigns both. **The architect should confirm this**
— if the ruling is "both should be ghosts," add the `MCC_SHOW_GHOST` gate inside `mcc_fan_envelope()`
and flag `mcc_splitter_envelope()`'s missing gate as its own follow-on deviation.

### 7.2 Should T1-18(c) move from `shell.scad` into `layout.scad`?

This plan (§6 step 1) keeps T1-18(c) in `shell.scad`, only changing it to read `fan_bay_x[0]` from
the struct. The alternative — moving the whole assert into `layout.scad` (it now needs no L1
geometry provider either) — is a larger diff than D23's own scope calls for ("a single definition"
and "a Y/Z footprint check", not a relayering of an already-working assert).
**Recommendation: keep it in `shell.scad`.** Flag if the architect disagrees; moving it afterward is
mechanical, not a redesign.

---

## 8. Tests — ordered steps

1. **`tests/test_constants.scad`**: add a new block (after the existing `MCC_END_ZONE_NEG_EXTRA_SPLITTER`
   check, before the closing `echo`s), matching that file's existing style:

   ```openscad
   // Fans (architecture.md §13 D23): MCC_FAN_DEFAULT/MCC_FAN_INTAKE_CLR are DERIVED-source
   // constants now read by both fan.scad and layout.scad -- pin them, and pin mcc_fan_spec()'s
   // equivalence for both MCC_FANS rows.
   assert(MCC_FAN_DEFAULT == "NF-A4x10",
       str("mcc test_constants: MCC_FAN_DEFAULT = ", MCC_FAN_DEFAULT, ", expected \"NF-A4x10\""));
   assert(MCC_FAN_INTAKE_CLR == 5.0,
       str("mcc test_constants: MCC_FAN_INTAKE_CLR = ", MCC_FAN_INTAKE_CLR, ", expected 5.0"));
   assert(struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame") == [40, 40, 10],
       str("mcc test_constants: mcc_fan_spec(MCC_FAN_DEFAULT) frame = ",
           struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame"), ", expected [40,40,10]"));
   assert(struct_val(mcc_fan_spec("NF-A6x25"), "frame") == [60, 60, 25],
       str("mcc test_constants: mcc_fan_spec(\"NF-A6x25\") frame = ",
           struct_val(mcc_fan_spec("NF-A6x25"), "frame"), ", expected [60,60,25]"));
   ```

   Add `MCC_FAN_DEFAULT`/`MCC_FAN_INTAKE_CLR` to the final summary `echo()` alongside the existing
   `MCC_GAP_FAR`/`MCC_SIDE_BOLT_PROUD`/`MCC_END_ZONE_NEG_EXTRA_SPLITTER` line.

2. **New file `tests/test_fan.scad`** (mirrors `tests/test_fasteners.scad`'s structure and header
   style exactly):

   ```openscad
   //////////////////////////////////////////////////////////////////////
   // tests/test_fan.scad
   //   Tier-2 headless smoke test (architecture.md §9). Exercises mcc_fan_spec()'s default-name
   //   equivalence, mcc_fan_cutout()'s default, and mcc_fan_envelope() -- previously uncalled
   //   anywhere (D23) -- so a signature/argument regression fails the render, matching
   //   tests/test_fasteners.scad's precedent for mcc_side_bolt_envelope().
   // Run:
   //   openscad --backend=Manifold -o out.csg tests/test_fan.scad
   //////////////////////////////////////////////////////////////////////

   $fa = 1; $fs = 0.4;

   include <mcc/mcc.scad>

   assert(mcc_fan_spec(MCC_FAN_DEFAULT) == mcc_fan_spec("NF-A4x10"),
       "mcc test_fan: mcc_fan_spec(MCC_FAN_DEFAULT) != mcc_fan_spec(\"NF-A4x10\")");

   // mcc_fan_cutout() default vs. explicit name -- both as negatives so the file stays solid.
   translate([0, 0, 0])
       difference() {
           cube([50, 50, MCC_WALL], center = false);
           translate([25, 25, 0]) mcc_fan_cutout(wall_t = MCC_WALL, grille = true);
       }
   translate([60, 0, 0])
       difference() {
           cube([50, 50, MCC_WALL], center = false);
           translate([25, 25, 0]) mcc_fan_cutout(name = MCC_FAN_DEFAULT, wall_t = MCC_WALL, grille = true);
       }

   // mcc_fan_envelope() (D23) -- plain, ungated (§7.1); exercised so a regression fails the render.
   translate([0, 100, 0]) mcc_fan_envelope();
   translate([60, 100, 0]) mcc_fan_envelope(MCC_FAN_DEFAULT);

   echo("mcc test_fan: OK");

   // vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
   ```

   `build.py`'s `smoke` globs `tests/test_*.scad` automatically — no `build.py` change needed.

3. **`tests/test_layout.scad`**: add assertions on the new struct fields, immediately after the
   existing `fan_pos` check (`test_layout.scad:62`):

   ```openscad
   fbx = struct_val(l, "fan_bay_x"); fby = struct_val(l, "fan_bay_y"); fbz = struct_val(l, "fan_bay_z");
   assert(_mcc_near(fbx[0], 78.95, 1e-3) && _mcc_near(fbx[1], 93.95, 1e-3), str("fan_bay_x=", fbx));
   assert(_mcc_near(fby[0], -50.825, 1e-3) && _mcc_near(fby[1], -10.825, 1e-3), str("fan_bay_y=", fby));
   assert(fbz == [5.5, 45.5], str("fan_bay_z=", fbz));
   ```

   (`l`/`DEV`/`VARIANT` are already in scope at that point in the file — `DEV` is
   `pro-convert-for-ndi-to-hdmi`, matching the compact-family numbers in §1's table.)

4. Run, in order: `python scripts/build.py smoke` (must show `test_constants.scad`, `test_fan.scad`,
   `test_layout.scad`, `test_shell.scad` all PASS — `test_fan.scad` is new, the other three are
   pre-existing files this plan edits), then `python scripts/build.py render`, then
   `python scripts/build.py check --all`, then `python scripts/build.py golden` (no `--update` —
   see §9), then `python scripts/build.py all` as the final green gate.

---

## 9. Golden impact

**None expected.** `MCC_FAN_INTAKE_CLR` (5.0) and `MCC_FAN_DEFAULT` (`"NF-A4x10"`) are the exact same
values the two literals already held — a refactor of *where* a number lives, not a change to it. If
`python scripts/build.py golden` reports **any** delta on any part, treat that as a bug and find it
before proceeding — do **not** `--update` past it (inverse of the fan-switch plan's B2 zero-delta
trap: there an unexpected zero delta hid a bug; here any nonzero delta would).

---

## 10. Sequencing with other in-flight plans

- **`docs/plans/2026-09-09-fan-switch.md` (issue #32, architect-approved, not yet implemented).** Its
  dispatch order (`fan-switch.md` §9.6) includes, as step **B7**, the identical
  `mcc_fan_spec()`/`MCC_FAN_DEFAULT` move this plan performs in §3-§4. **Land this plan first.**
  Whoever implements #32 afterward should find that move already done and **skip** it, going straight
  to `MCC_SWITCHES`/`switch.scad`. Both plans touch the same `constants.scad` "Fans" region, the same
  `layout.scad` `let()` block (this plan's `fan_bay_*` vs. #32's `switch_y`/`switch_pos`, both right
  after `fan_pos`), and the same `shell.scad` `mcc_shell_base()` block (this plan's T1-18(c) edit vs.
  #32's new cutout call after the fan-cutout conditional) — landing this plan first avoids a 3-file
  merge conflict.
- **`docs/plans/2026-09-09-mount-rail-and-brackets.md` (#25/#26/#27).** Touches `layout.scad`'s
  `mcc_floor_keepout()`/`constants.scad` in a different section (floor keep-out) — lower conflict
  risk. Check its merge status first; re-verify this plan's line anchors if it landed in between.
- **Branch**: no GitHub issue exists for D23, so per `ticket-source.md` use
  `feature/fan-bay-reservation`, off `main` (not off `feature/plans-2026-09-09`). Rename to
  `feature/issue-<n>-fan-bay-reservation` if an issue is opened first.

---

## PLAN-ASSUMPTIONS (flag to the user/architect, do not silently resolve differently)

1. **PLAN-ASSUMPTION 1** — `mcc_fan_envelope()` stays **ungated** (no `%`/`MCC_SHOW_GHOST`), matching
   its sibling `mcc_splitter_envelope()` rather than `mcc_side_bolt_envelope()`. See §7.1. If the
   architect rules the other way, only `fan.scad`'s `mcc_fan_envelope()` body changes (§4 step 2) —
   nothing else in this plan depends on the choice.
2. **PLAN-ASSUMPTION 2** — T1-18(c) stays in `shell.scad` (only its inline recompute is removed), not
   moved into `layout.scad`. See §7.2.
3. **PLAN-ASSUMPTION 3** — the new `fan_bay_y`/`fan_bay_z` half-extents both use `fan_frame[0]`,
   guarded by an assert that fails loudly if a future non-square `MCC_FANS` row is ever made the
   default (§5 step 1). Both current rows (`NF-A4x10`, `NF-A6x25`) are square, so this is not
   exercised today — it is a stop-and-report guard, not a design decision to silently generalize.
4. **PLAN-ASSUMPTION 4** — this plan lands **before** `docs/plans/2026-09-09-fan-switch.md` (#32).
   If the teamlead instead dispatches #32 first, its own B7 step already performs the
   `mcc_fan_spec()`/`MCC_FAN_DEFAULT` move — in that case, re-scope this plan down to just the Y/Z
   footprint check (§5 steps 2-4, §6, §8) and drop §3/§4/§7's now-already-done constant/fan.scad
   work, re-verifying line anchors against whatever #32 actually landed.

---

## Acceptance checklist

- [ ] `constants.scad`: `MCC_FAN_DEFAULT`, `MCC_FAN_INTAKE_CLR`, relocated `mcc_fan_spec()` added;
      no other constant changed.
- [ ] `fan.scad`: `mcc_fan_spec()` removed; `mcc_fan_envelope()` uses `MCC_FAN_INTAKE_CLR`;
      `mcc_fan_envelope()`/`mcc_fan_cutout()` both default `name` to `MCC_FAN_DEFAULT`.
- [ ] `layout.scad`: `fan_bay_x`/`fan_bay_y`/`fan_bay_z` published from `mcc_case_layout()`;
      T1-46a-d added; square-frame guard assert added.
- [ ] `shell.scad`: T1-18(c) reads `fan_bay_x[0]` from the struct; no local `mcc_fan_spec("NF-A4x10")`
      call remains; no new call to `mcc_fan_envelope()` was added to `mcc_shell_base()`/`mcc_shell_lid()`.
- [ ] `vents.scad`: `mcc_fan_cutout()` call site no longer passes an explicit `"NF-A4x10"`.
- [ ] `tests/test_constants.scad`, new `tests/test_fan.scad`, `tests/test_layout.scad` updated per §8.
- [ ] `python scripts/build.py all` green; `python scripts/build.py golden` shows **zero** deltas.
- [ ] No edits to `architecture.md`, `layout-patch-wall.md`, `BOM.md`, or any GitHub issue.
- [ ] Both open choices in §7 carry an explicit architect ruling (not silently resolved either way).

> **Superseded by §11.** The checklist above is the *plan's* checklist. Where §11 (the architect
> verdict) contradicts it — the ghost gate, the shell call site, the square-frame guard, the new
> clearance constant — **§11 wins**. Use §11.9's checklist.

---

## 11. Architect verdict — solution-architect, 2026-09-09 (architecture.md rev 12)

**Verdict: APPROVED WITH CHANGES — 6 blocking (B1–B6).** The plan's shape is right and matches the
idiom this repo has settled on everywhere else: the reservation of record is a **pure numeric AABB
published by `mcc_case_layout()` and enforced by Tier-1 asserts**, never a CSG intersection, and
`layout.scad` reads the L0 table directly instead of importing an L1 geometry provider (the rev-9
`MCC_RAIL_*` rule, the rev-11 `MCC_SWITCHES` rule). D23's two named deliverables — one definition of
the intake clearance, and a Y/Z footprint check — are both delivered.

What is wrong is around the edges: two of the four asserts are **bare-tangency** where every
comparable rule in this repo carries a 2 mm clearance term; the Y/Z half-extents are taken off the
wrong frame axes and then propped up by a guard assert; the module is left as an ungated solid box
that is neither a reservation nor a ghost; and the plan's `constants.scad` step invites a developer
to retype `MCC_FANS` and drop its sourcing citations.

### 11.1 Rulings on the plan's open choices (§7) and PLAN-ASSUMPTIONs

| Ref | Question | Ruling |
|---|---|---|
| **R1** | Does struct-published AABB + numeric asserts + a test-only module satisfy D23? | **Yes for the reservation, no for the module.** The AABB *is* the reservation (see B1); D23's `%`-ghost half is **also required** (B2), placed by `shell.scad`. Option (iii) — delete — is rejected: the ghost has review value and its sibling `mcc_splitter_envelope()` is not being deleted either. §6's "**function**" wording is **upheld and the code is the deviation**: a *module* returning a solid can never be consumed by the reservation machinery, because §3 forbids `layout.scad` (where the checks live) from `use`-ing `fan.scad`. `architecture.md` §6 is rewritten in rev 12 accordingly |
| **R2** / PA-1 | Gate `mcc_fan_envelope()` behind `%` + `MCC_SHOW_GHOST`? | **Yes — OVERRULES PLAN-ASSUMPTION 1** (B2). §7 "Ghost rendering" is unambiguous: a visual-only body is `%`-ed *and* flag-gated, both belts. `mcc_side_bolt_envelope()` (`fasteners.scad:352`) is the correct precedent, not the splitter. `mcc_splitter_envelope()` must follow **but not in this PR** — it is logged as deviation **D24** and fixed together with the pending D7 rework of the same module |
| **R3** / PA-2 | T1-18(c) stays in `shell.scad`? | **UPHELD — keep it in `shell.scad`**, reading `fan_bay_x[0]` from the struct exactly as §6 step 1 writes it. Its other inputs (`mcc_plug_axial()` per +X port) are already gathered there, D23's scope is not a relayering, and the smaller diff is the safer diff. On the T1-28 duplication (`layout.scad:472` **and** `shell.scad:380`): **acceptable, do not collapse it here.** Both read the same struct field, so they cannot disagree numerically; it is noise, not risk. Logged as deviation **D25** for a future cleanup pass |
| **R4** | Minimum clearance in T1-46a? | **Yes — required (B3).** New L0 constant **`MCC_FAN_BAY_CLR = 2.0`**, `assumed`, provenance = this repo's recurring 2 mm keep-out web (`knowledge/design/fdm-rugged-enclosure-guidelines.md:127`, `knowledge/components/fasteners-and-hardware.md:123-131`) — the same 2.0 already inside `MCC_SIDE_BOLT_KEEPOUT_D`'s `+ 2 * 2.0` (`constants.scad:261`) and `MCC_APERTURE_LIP_WEB_MIN`. Applied to **T1-46a and T1-46b only**. **Not** to T1-46c/d: those bound the bay against the *interior cavity surface*, and a reserved volume is allowed to touch the shell it bolts to. The rule, stated once: **clearance is required against another feature, never against the cavity boundary** |
| **R5** | Which +Y figure is the contract — the plan's `W/2 − MCC_T_PATCH − d_bay_free`, or `layout-patch-wall.md:778`'s `fan_y ≤ −25.7`? | **The plan's expression is the contract; `−25.7` is wrong and is corrected to `−20.7` (B4 + a knowledge-doc fix I have made).** `W/2 − MCC_T_PATCH − d_bay_free = W/2 − MCC_WALL − MCC_PANEL_SEAT_T − max_bay_depth` is the exact plane the deepest plug reaches (compact: `79.925 − 8 − 70.65 = +1.275`). The rev-11 `−25.7` used the *conservative* rev-2 convention (`W/2 − MCC_T_PATCH − mcc_bay_depth`), which double-counts `MCC_WALL + MCC_PANEL_SEAT_T = 5 mm`, and then folded in an unnamed 2 mm clearance: `79.925 − 8 − 75.65 − 2 − 20 = −25.725`. Correct cap with `MCC_FAN_BAY_CLR` named: `fan_y ≤ 1.275 − 2 − 20 = **−20.725**`. See §11.4 — this correction has a consequence for issue #32's record |
| **R6** | `mcc_fan_spec()` → `constants.scad`, this plan first? | **CONFIRMED, both parts.** It is already mandated (rev 11 §3, #32's step B7); this plan may land it first, and **#32's implementer then skips B7 entirely** and goes straight to `MCC_SWITCHES`/`switch.scad`. A **pure function containing `assert()` is legal in `constants.scad`** — §3's hard rule bans *modules* (they break `include` idempotency); a function body is only evaluated when called, so an assert inside one costs nothing at include time. Recorded in `architecture.md` §3 rev 12 so it is not re-litigated |
| **R7** / PA-3 | Square-frame guard, or the real axis mapping? | **OVERRULED — use the real mapping and DELETE the guard (B5).** Under the ghost's `rotate([0,-90,0])` the fan's local **X → world +Z** and local **Y → world Y**. So `fan_bay_y` takes `fan_frame[**1**]` and `fan_bay_z` takes `fan_frame[**0**]`. Numerically identical today (both `MCC_FANS` rows are square), so **no golden and no test number moves** — but a guard that exists only to prop up a shortcut is worse than not taking the shortcut, and it would have shipped a genuinely wrong Y/Z swap the day a 40 × 20 blower entered the table |
| **R8** | Is T1-46 free? Sub-lettering? Goldens? | **Confirmed on all three.** Highest allocated ID is T1-45 (rev 11); **T1-46 is the next free ID** and I have reserved T1-46a–d in `layout-patch-wall.md` §9 as part of this verdict. Sub-lettering a–d for several clauses of one geometric contract matches T1-34a–d and T1-42a/b/c. **Goldens: zero delta is the requirement, not the expectation** — with `MCC_SHOW_GHOST = false` the ghost emits nothing at all, and `%` is excluded from CSG even when it does. Any nonzero delta on any part means the gate is broken; do not `--update` |
| PA-4 | This plan lands before #32 | **UPHELD** — and it is now the *required* order, since #32's B7 is this plan's §3/§4 |

### 11.2 Blocking changes (B1–B6)

| # | Change | Why |
|---|---|---|
| **B1** | **State in the code, once, which artefact is the reservation.** The comment on the new `layout.scad` bindings must say: *the reservation of record is `fan_bay_x/y/z` + T1-46a-d; `mcc_fan_envelope()` is only its `%`-ghost.* Exact text in §11.3 | This is the whole content of D23. `fan.scad:32-36`'s current doc comment claims the module "is the thing `shell.scad` reserves against" — a reader trusted that and it was false. Replace that sentence too |
| **B2** | **`mcc_fan_envelope()` becomes `%` + `MCC_SHOW_GHOST`-gated, AND `shell.scad` places it** — with `rotate([0,**-**90,0])`, not `vents.scad`'s `rotate([0,90,0])`. Exact snippets in §11.3 | R1/R2. **The transform trap is real and is B2-of-rev-11 all over again:** `mcc_fan_cutout()`'s local `Z` spans the wall and is placed outward; `mcc_fan_envelope()`'s local `Z` starts at the mounting plane and grows *inward* (`fan.scad:13-15`). Copying `vents.scad:146-148`'s rotate puts the whole reservation **outside the case**, and because it is a ghost **nothing** would report it. Note also: OpenSCAD only **warns** on an unknown module — if anyone strips `use <fan.scad>` from `shell.scad` the call silently becomes a no-op, so that import line keeps a do-not-remove comment |
| **B3** | **Add `MCC_FAN_BAY_CLR = 2.0` (L0) and use it in T1-46a/b.** Not in T1-46c/d | R4 |
| **B4** | **T1-46b's bound is `W / 2 - MCC_T_PATCH - d_bay_free - MCC_FAN_BAY_CLR`** (compact `−0.725`, plus `+2.525`) | R5. The plan's bound was right but bare; the doc figure it disagreed with was the wrong one and I have fixed the doc, not the code |
| **B5** | **`fan_bay_y` from `fan_frame[1]`, `fan_bay_z` from `fan_frame[0]`; delete `_fan_bay_square_check`** | R7 |
| **B6** | **Do NOT retype the `MCC_FANS` block.** `constants.scad`'s §3 step 1 is replaced by an *insertion* after `constants.scad:541` (`];`), leaving lines 533-541 and the `MCC_VENT_AREA_RATIO` block byte-identical | The plan's replacement block reproduces `MCC_FANS` "without the per-row sourcing comments, for brevity". A Sonnet-tier developer pasting it literally deletes the `fans.md:15-18/42-45` citations — a direct violation of `CLAUDE.md`'s "never invent a dimension; cite `knowledge/<file>.md:<line>`". Nothing is gained by moving the table |

### 11.3 Corrected code — implement exactly this

**(a) `lib/mcc/constants.scad`** — replaces the plan's §3 step 1 entirely. **Insert** after line 541
(the `];` closing `MCC_FANS`) and before the `MCC_VENT_AREA_RATIO` comment block at line 543. Do not
touch `MCC_FANS` or `MCC_VENT_AREA_RATIO`.

```openscad
// Default fan part, key into MCC_FANS. Mirrors MCC_SPLITTER_DEFAULT's role for MCC_SPLITTERS
// below. architecture.md rev 11 §3 (issue #32 B7) / rev 12 §6.
MCC_FAN_DEFAULT = "NF-A4x10";

// Intake clearance beyond the fan's own frame depth, mm. assumed -- generic unobstructed-intake
// allowance; no sourced figure in knowledge/components/fans.md (frame/pitch/hole_d only). Single
// source of truth for the figure previously duplicated as a bare literal `5` at fan.scad's
// mcc_fan_envelope() and inside shell.scad's T1-18(c) block. architecture.md §13 D23.
MCC_FAN_INTAKE_CLR = 5.0;

// Minimum clearance between the reserved fan bay (frame + MCC_FAN_INTAKE_CLR) and any OTHER
// feature: the (+X,-Y) corner lid-fastener boss/gusset on -Y, the connector bay's plug envelope
// on +Y (T1-46a/b, layout-patch-wall.md §9). assumed -- this repo's recurring 2 mm keep-out web
// (knowledge/design/fdm-rugged-enclosure-guidelines.md:127,
// knowledge/components/fasteners-and-hardware.md:123-131), the same 2.0 that gives
// MCC_SIDE_BOLT_KEEPOUT_D its `+ 2 * 2.0` above and MCC_APERTURE_LIP_WEB_MIN its value.
// Deliberately NOT applied to the bay's Z bounds (T1-46c/d): those bound the bay against the
// interior CAVITY surface, and a reserved volume may touch the shell it bolts to. Rule
// (architecture.md §6 rev 12): clearance is required against another FEATURE, never against the
// cavity boundary.
MCC_FAN_BAY_CLR = 2.0;

// Function: mcc_fan_spec()
// Usage:
//   spec = mcc_fan_spec(name);
// Description:
//   Looks up a fan record (frame/pitch/hole_d) from MCC_FANS by name, e.g. "NF-A4x10" or
//   "NF-A6x25". MOVED HERE from lib/mcc/fan.scad (L1) -- architecture.md rev 11 §3 / rev 12: a
//   pure accessor over an L0 table was misplaced at L1, and layout.scad ("functions only, never an
//   L1 geometry provider") needs it without importing fan.scad. A pure function carrying an
//   assert() is legal here: §3's hard rule bans MODULES in constants.scad (they break `include`
//   idempotency); a function body is evaluated only when called.
function mcc_fan_spec(name) =
    let(ind = search([name], MCC_FANS)[0])
    assert(ind != [], str("mcc: unknown fan \"", name, "\""))
    MCC_FANS[ind][1];
```

**(b) `lib/mcc/fan.scad`** — the plan's §4 steps 1, 3, 4 stand as written. Step 2 is replaced by:

```openscad
// Module: mcc_fan_envelope()
// Usage:
//   mcc_fan_envelope([name]);
// Description:
//   REVIEW-ONLY ghost of the fan bay's reserved keep-out volume: the fan's own frame footprint
//   extruded to its frame depth plus MCC_FAN_INTAKE_CLR. `%`-ed and gated behind MCC_SHOW_GHOST
//   (default false), like every other ghost in this repo -- architecture.md §7 "Ghost rendering",
//   both belts: `%` is the mechanism, the flag is the review signal.
//   THIS MODULE IS NOT THE RESERVATION. The reservation of record is numeric: fan_bay_x/y/z from
//   mcc_case_layout() (layout.scad), enforced by T1-46a-d there and by T1-18(c) in shell.scad.
//   architecture.md §6 rev 12 / §13 D23 -- a solid box cannot be the reservation, because §3
//   forbids layout.scad (where the checks live) from `use`-ing this file at all.
//   LOCAL FRAME: Z = 0 at the fan's mounting plane (the wall's INNER face), growing toward +Z INTO
//   the case interior. That is the OPPOSITE sense to mcc_fan_cutout() below, whose local
//   Z = [0, wall_t] spans the wall outward. Callers therefore need rotate([0,-90,0]) for this
//   module and rotate([0,90,0]) for the cutout -- see shell.scad's and vents.scad's call sites.
// Arguments:
//   name = fan name, key into MCC_FANS. Default: MCC_FAN_DEFAULT.
module mcc_fan_envelope(name = MCC_FAN_DEFAULT) {
    spec  = mcc_fan_spec(name);
    frame = struct_val(spec, "frame");
    depth = frame[2] + MCC_FAN_INTAKE_CLR;
    if (MCC_SHOW_GHOST) {
        %translate([0, 0, depth / 2])
            cube([frame[0], frame[1], depth], center = true);
    }
}
```

Also update `fan.scad`'s file-header Z-axis note (lines 13-15) to state **both** senses, in the same
words as the module doc above. And update **`fasteners.scad:333-340`**, whose comment now says
`mcc_side_bolt_envelope()` is `%`-gated "(unlike the fan/splitter envelopes)" — after this change
the fan envelope *is* gated; the sentence must read "unlike `mcc_splitter_envelope()`, which is not
gated yet — deviation D24".

**(c) `lib/mcc/layout.scad`** — replaces the plan's §5 step 1 bindings (insert after
`fan_pos = [L / 2, fan_y, z_conn_c],`, `layout.scad:404`):

```openscad
        // Fan bay reserved world AABB (architecture.md §6 reservation rule, §13 D23).
        // THIS IS THE RESERVATION OF RECORD -- mcc_fan_envelope() (fan.scad) is only its %-ghost.
        // Reads MCC_FANS/MCC_FAN_INTAKE_CLR directly (L0): this file may never `use` fan.scad, an
        // L1 geometry provider (§3). fan_bay_x is the SAME quantity shell.scad's T1-18(c) checks
        // against -- it reads it from this struct, it does not recompute it.
        // AXIS MAPPING (do not swap): the bay is the fan frame seen through the +X end wall, i.e.
        // through rotate([0,-90,0]) -- fan-local X -> world +Z, fan-local Y -> world Y, fan-local
        // +Z (frame depth + intake) -> world -X, inward from the wall's inner face.
        fan_frame = struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame"),
        fan_bay_depth = fan_frame[2] + MCC_FAN_INTAKE_CLR,
        fan_bay_x = [L / 2 - MCC_WALL - fan_bay_depth, L / 2 - MCC_WALL],
        fan_bay_y = [fan_y - fan_frame[1] / 2, fan_y + fan_frame[1] / 2],
        fan_bay_z = [z_conn_c - fan_frame[0] / 2, z_conn_c + fan_frame[0] / 2],
```

Struct fields (plan §5 step 2) unchanged. The plan's §5 step 3 assert block is replaced by:

```openscad
    // T1-46a-d: the fan bay's Y/Z footprint (architecture.md §6/§13 D23, layout-patch-wall.md
    // §5/§9). Evaluated UNCONDITIONALLY, like T1-18(c) -- §6 reserves the bay even when
    // cfg.fan == false. All four pass by construction today (compact slack: 12.96 / 10.10 / 2.50 /
    // 2.50 mm), so they are regression guards against a future change to fan_y, MCC_FANS,
    // MCC_T_PATCH or the lid-fastener ring -- not fixes to a live failure.
    assert(fan_bay_y[0] >= corners[1][1] + max(MCC_WALL / 2, boss_od_lid / 2) + MCC_FAN_BAY_CLR - MCC_EPS,
        str("mcc: T1-46a fan bay -Y edge ", fan_bay_y[0], " is within MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR,
            " of the (+X,-Y) corner lid-fastener boss/gusset at y=", corners[1][1], " on \"",
            mcc_dev_slug(dev), "\""))
    assert(fan_bay_y[1] <= W / 2 - MCC_T_PATCH - d_bay_free - MCC_FAN_BAY_CLR + MCC_EPS,
        str("mcc: T1-46b fan bay +Y edge ", fan_bay_y[1], " is within MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR,
            " of the connector bay's plug envelope at y=", W / 2 - MCC_T_PATCH - d_bay_free, " on \"",
            mcc_dev_slug(dev), "\""))
    assert(fan_bay_z[0] >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: T1-46c fan bay bottom ", fan_bay_z[0], " is below the interior floor on \"",
            mcc_dev_slug(dev), "\""))
    assert(fan_bay_z[1] <= MCC_FLOOR_T + H_int + MCC_EPS,
        str("mcc: T1-46d fan bay top ", fan_bay_z[1], " is above the interior ceiling on \"",
            mcc_dev_slug(dev), "\""))
```

**(d) `lib/mcc/shell.scad`** — the plan's §6 step 1 stands as written (T1-18(c) reads
`fan_bay_x[0]`). The plan's §6 step 2 is **overruled**: add the ghost. Keep the local
`fan_bay_x = struct_val(l, "fan_bay_x");` binding from step 1 and reuse it. Place this as the
**last child of `mcc_shell_base()`'s outer `union()`** — never inside the `difference()`:

```openscad
        // Fan bay reservation ghost (architecture.md §6 rev 12, §13 D23). The reservation of RECORD
        // is numeric -- fan_bay_x/y/z from mcc_case_layout(), enforced by T1-46a-d there and by
        // T1-18(c) above. This is its review-only visualization: mcc_fan_envelope() is `%`-ed and
        // gated behind MCC_SHOW_GHOST (default false), so it emits nothing in any export and no
        // golden can move.
        // TRANSFORM -- do NOT copy vents.scad:146-148's. mcc_fan_cutout()'s local Z spans the wall
        // and is placed with rotate([0,90,0]) (local +Z -> world +X, outward); mcc_fan_envelope()'s
        // local Z starts at the mounting plane and grows INTO the interior (fan.scad header), so it
        // needs rotate([0,-90,0]) (local +Z -> world -X). With rotate([0,90,0]) the whole
        // reservation lands OUTSIDE the case and, being a ghost, no check would report it.
        // The origin comes from the struct (fan_bay_x[1] == L/2 - MCC_WALL) so the ghost and the
        // asserted AABB cannot drift apart.
        translate([fan_bay_x[1], fan_pos[1], fan_pos[2]])
            rotate([0, -90, 0])
                mcc_fan_envelope();
```

and annotate the import so nobody prunes it (`shell.scad:20`) — an unknown module is a **warning**,
not an error, in OpenSCAD:

```openscad
use <fan.scad>         // mcc_fan_envelope() -- the reservation ghost in mcc_shell_base(). Do not
                       // remove: an unknown module call only WARNS, it does not fail the render.
```

**(e) `lib/mcc/vents.scad`** — the plan's §6 step 3 stands, unchanged.

**(f) Tests.** The plan's §8 stands, with three changes:
1. `tests/test_constants.scad` also pins **`MCC_FAN_BAY_CLR == 2.0`** and echoes it.
2. `tests/test_fan.scad`: with `MCC_SHOW_GHOST = false` the two `mcc_fan_envelope()` calls now emit
   nothing, so the gated branch would never be evaluated. Add, immediately **after** the
   `include <mcc/mcc.scad>` line (the standard include-then-override idiom):
   ```openscad
   MCC_SHOW_GHOST = true;   // exercise mcc_fan_envelope()'s gated %-branch (fasteners.scad's
                            // test-only precedent left it un-evaluated; a bad argument inside the
                            // `if` would not fail the render otherwise).
   ```
   Keep the plan's two `mcc_fan_envelope()` call sites. `tests/` are smoke-only, never goldened.
3. `tests/test_layout.scad`: the plan's expected numbers are **unchanged** by B5 (both `MCC_FANS`
   rows are square), so `fbx == [78.95, 93.95]`, `fby == [−50.825, −10.825]`, `fbz == [5.5, 45.5]`
   still stand. If any differs, stop and report — do not adjust the expectation.

### 11.4 Consequence for issue #32's record — read this before touching `fan_y`

R5's correction changes a number in the rev-11 `#32` ruling. `layout-patch-wall.md` §5 and
`architecture.md`'s rev-11 header both say the +Y travel available to `fan_y` on compact is
**≤ 5.1 mm** (cap `−25.7`). The correct figures are **cap `−20.7`, travel ≤ 10.1 mm**. I have
corrected both documents (`layout-patch-wall.md` §5, §18.6 addendum).

**This does not reopen D-18, and a developer must not act on it.** The ⌀20.2 IP65 R13-112A was
rejected on *three* grounds, and the arithmetic was only one: moving `fan_y` toward +Y pushes the
fan into the +X end zone exactly where the slot-3/slot-4 patch cables turn toward the patch wall,
which §5's "exhaust away from the patch wall" rule exists to prevent (`architecture.md:1401-1403`),
and **R20 says `fan_y` moves on measurement, not on a switch's convenience**. Compact stays
`["fan_switch", false]`. Whether the extra 5 mm is worth revisiting once M17 lands is a **user**
question and is already parked at `architecture.md` §12 Q19.

### 11.5 Scope confirmations

- **`mcc_splitter_envelope()` is out of scope here** (deviation **D24**, fixed with D7). Do not
  touch `poe_splitter.scad` in this PR.
- **T1-28's duplicate in `shell.scad:380` is out of scope here** (deviation **D25**).
- The plan's §0 "do not touch `architecture.md` / `layout-patch-wall.md`" is correct **and still
  correct**: the architect has already made those edits as part of this verdict (rev 12). The
  developer edits neither.
- No `BOM.md` change, no new GitHub issue, no envelope figure moves on any SKU.
- Branch `feature/fan-bay-reservation` off `main`, per the plan's §10.

### 11.6 What must fail if the developer gets it wrong

- Golden delta on **any** part ⇒ the ghost is not gated (or `%` was dropped). **A bug, not a
  refresh.** Do not `--update`.
- `bbox` or `parts` moving on any SKU ⇒ same cause.
- `build.py smoke` must show `test_constants.scad`, `test_fan.scad`, `test_layout.scad`,
  `test_shell.scad` all PASS, with `test_fan.scad` new.
- Render `models/pro-convert-hdmi-plus/case.scad -D part=\"assembly\"` once with
  `-D MCC_SHOW_GHOST=true` and confirm by eye that the fan-bay ghost sits **inside** the case,
  against the +X wall. That is the only check that catches a flipped `rotate` — no assert can.

### 11.7 Where this is recorded

`architecture.md` **rev 12**: header, §3 (pure-function-with-assert carve-out), §6 (the reservation
rule rewritten — numeric AABB is the reservation, `*_envelope()` is a ghost), §9 (T1-46), §13 (D23
resolution, new D24/D25). `layout-patch-wall.md` **rev 12**: §5 (fan bay reserved AABB + the
corrected `fan_y` cap), §9 (T1-46a–d), §11 (rev-12 constants addendum), §18.6 (the #32 correction),
new **§19** (this ruling, in full).

### 11.8 One-line verdict

**APPROVED WITH CHANGES — 6 blocking (B1–B6). No user decision required; dispatch to a developer
once B1–B6 are folded in.**

### 11.9 Acceptance checklist (supersedes the one above)

- [ ] `constants.scad`: `MCC_FAN_DEFAULT`, `MCC_FAN_INTAKE_CLR`, **`MCC_FAN_BAY_CLR`**, relocated
      `mcc_fan_spec()` **inserted after line 541**; `MCC_FANS` and `MCC_VENT_AREA_RATIO` byte-identical (B6).
- [ ] `fan.scad`: `mcc_fan_spec()` removed; `mcc_fan_envelope()` **`%` + `MCC_SHOW_GHOST`-gated**,
      reads `MCC_FAN_INTAKE_CLR`, doc rewritten per §11.3(b); both modules default to `MCC_FAN_DEFAULT`;
      file-header Z-axis note states both senses (B1, B2).
- [ ] `fasteners.scad:333-340` comment corrected (the fan envelope is gated now; D24 named).
- [ ] `layout.scad`: `fan_bay_x/y/z` published, **`[1]` for Y and `[0]` for Z**, **no square-frame
      guard**; T1-46a–d with `MCC_FAN_BAY_CLR` on a/b only (B3, B4, B5).
- [ ] `shell.scad`: T1-18(c) reads `fan_bay_x[0]`; **the ghost call site added with
      `rotate([0,-90,0])`** as the last child of the outer `union()`; `use <fan.scad>` annotated (B2).
- [ ] `vents.scad`: no explicit `"NF-A4x10"` left.
- [ ] Tests per §11.3(f), including `MCC_SHOW_GHOST = true;` in `test_fan.scad`.
- [ ] `python scripts/build.py all` green; `golden` shows **zero** deltas; one manual
      `MCC_SHOW_GHOST=true` assembly render eyeballed (§11.6).
- [ ] No edits to `architecture.md`, `layout-patch-wall.md`, `BOM.md`, `poe_splitter.scad`, or any
      GitHub issue.
