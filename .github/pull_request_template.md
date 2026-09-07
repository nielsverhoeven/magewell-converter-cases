<!--
Target-branch reminder (see CONTRIBUTING.md for the full model):
  feature/*          -> develop
  release/*, hotfix/* -> main  (plus a back-merge PR into develop)
Never target main from a feature branch, and never commit directly on main or develop.
-->

## Summary

<!-- What does this PR do and why? One or two sentences. -->

## Checklist (definition of done, CONTRIBUTING.md)

- [ ] `python scripts/build.py all` passes locally
- [ ] The `render` CI check is green on this PR
- [ ] Docs and code comments are English
- [ ] Every Neutrik panel connector is the black `-B` variant, no exceptions
- [ ] Any deviation from `.claude/knowledge/architecture.md` is recorded in that file's §13
      Deviations log

## Goldens changed?

- [ ] No golden diff (`tests/golden/*.json` unchanged)
- [ ] Golden diff present — justified below:

<!-- If a golden changed, explain what dimension/geometry changed and why the new value is correct,
     not just that the diff exists. An unexplained golden diff is treated as a regression. -->

## BOM changed?

- [ ] No BOM change
- [ ] `BOM.md` updated (new/changed parts, connectors, inserts, fasteners, cables) — see the
      `bom-update` skill

## Printed / measured coupons?

<!-- Only relevant for changes that touch fit-critical dimensions (panel cutouts, tongue-and-groove,
     heat-set bosses, clearances). List which coupon(s) from models/coupons/** were printed and
     measured to justify this change, or note "n/a" if the change doesn't touch a fit parameter. -->

- [ ] n/a — no fit-critical dimension changed
- [ ] Coupon(s) printed and measured:

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
