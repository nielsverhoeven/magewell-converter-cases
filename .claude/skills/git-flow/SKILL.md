---
name: git-flow
description: How to pick a branch, sequence commits, and prepare a PR/release/hotfix under this repo's Git Flow model; use before creating any branch, committing to main/develop, or preparing a PR/tag.
---

# git-flow

This repo uses Git Flow (nvie/AVH semantics). The full recipe book with worked plain-git + `git
flow` command tables is `CONTRIBUTING.md` — read it once. This file is the condensed operating
guide: which branch a task belongs on, the command sequence, and when to stop and ask the user.
The AVH `git flow` extension is **not installed** by default in this environment; use plain git
unless the user confirms the extension is present.

## Picking the branch

| Task | Branch from | Prefix | Merges into |
|---|---|---|---|
| A feature, a new case variant, a coupon, a doc change, a bug fix that isn't urgent-on-a-release | `develop` | `feature/<kebab-topic>` (`feature/issue-<n>-<topic>` if a GitHub issue exists) | `develop` via PR |
| Preparing a release (version bump, CHANGELOG move, frozen goldens) | `develop` | `release/vX.Y.Z` | `main` (tagged) **and** `develop` |
| An urgent fix on a version already released | `main` | `hotfix/vX.Y.Z` (the new patch version) | `main` (tagged) **and** `develop` |
| Long-lived maintenance of an old major | a `main` tag | `support/vX.x` | — (rare; ask the user before creating one) |

If a task doesn't obviously fit one row — e.g. "should this be its own feature branch or ride along
with an open one" — ask the user rather than guessing; branch topology is cheap to get right up
front and annoying to unwind later.

## Command sequences

Plain git first, `git flow` equivalent second. Full versions with more inline explanation are in
`CONTRIBUTING.md`; this is the copy-pasteable core.

**Start a feature:**
```
git checkout develop && git pull
git checkout -b feature/<kebab-topic>
```
`git flow feature start <kebab-topic>`

**Commit on the feature branch** — this is fine to do locally without asking, once the user has
asked for the work:
```
git add <specific files>
git commit -m "feat(<scope>): <summary>

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

**Publish + PR** (always ask first — see "When to ask" below):
```
git push -u origin feature/<kebab-topic>
gh pr create --base develop --title "..." --body "... 🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

**Start a release:**
```
git checkout develop && git pull
git checkout -b release/vX.Y.Z
```
`git flow release start vX.Y.Z` — then bump the version, move `CHANGELOG.md` `[Unreleased]` entries
into `## [X.Y.Z] - YYYY-MM-DD`, and only run `python scripts/build.py golden --update` if the diffs
were reviewed and are intentional.

**Finish a release** (ask before every push/PR/merge/tag step):
```
git push -u origin release/vX.Y.Z
gh pr create --base main --title "release: vX.Y.Z" --body "..."
# after the render check is green and the PR is merged (--no-ff):
git checkout main && git pull
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
# back-merge into develop:
gh pr create --base develop --head release/vX.Y.Z --title "chore: back-merge vX.Y.Z into develop"
```
`git flow release finish vX.Y.Z` does the merge + tag + back-merge + branch delete locally, but
skips the PR/CI gate — prefer the PR route so `render` gates the merge into `main`.

**Start / finish a hotfix:** same shape as a release, but branch from `main`, and both the tagged
merge into `main` and the merge into `develop` are mandatory (a hotfix that never reaches `develop`
gets silently reverted by the next release).
```
git checkout main && git pull
git checkout -b hotfix/vX.Y.Z
# ... fix, commit, push, PR into main, merge --no-ff, tag vX.Y.Z, push tag ...
# ... then a second PR/merge hotfix/vX.Y.Z -> develop ...
```

## Naming rules

- Feature: `feature/<kebab-topic>`, or `feature/issue-<n>-<topic>` when a GitHub issue exists
  (`.claude/knowledge/ticket-source.md`). Don't invent an issue number — check with `gh issue list`
  first if unsure whether one exists.
- Release / hotfix: `release/vX.Y.Z` / `hotfix/vX.Y.Z` — always the full SemVer with a leading `v`,
  matching the tag it will produce.
- Tags: annotated, `vX.Y.Z`, message `vX.Y.Z` or a short release summary. Never a lightweight tag.

## Commit messages

Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `test:`, `refactor:`, optional
scope — `feat(compact): add shell`. Every commit made by Claude Code ends with:
```
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```
Every PR body written by Claude Code ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## When to ask the user

**Always ask, every time, no exceptions:** `git push` (including force-push, which is otherwise
close to forbidden — see the Team Charter git safety rules), opening a PR, merging a PR, creating or
pushing a tag, merging any branch into `main` or `develop` by any method.

**Fine to do without asking**, once the user has already asked for the underlying work: creating a
local `feature/*` branch, committing to it, running `python scripts/build.py all` locally.

**Never do, full stop:** commit directly on `main` or `develop` (even a one-line fix — branch off
first), force-push `main` or `develop`, skip the `render` CI check before merging, delete `main` or
`develop`.

## Version bump + tagging a release

1. Confirm the bump size against `CONTRIBUTING.md`'s SemVer table (MAJOR = previously printed parts
   become incompatible; MINOR = new variant/coupon/feature; PATCH = fix, no golden change).
2. On `release/vX.Y.Z`: update the version wherever it's recorded, move `CHANGELOG.md`
   `[Unreleased]` into a dated `[X.Y.Z]` section.
3. `python scripts/build.py all --release` must be green — this also enforces the release gate (no
   `WARNING: unmeasured port` in the render output).
4. PR into `main`, merge `--no-ff` only after `render` is green, then tag and push the tag (ask
   first, per above).
5. Back-merge into `develop`.

## Handling a golden change in a PR

A `tests/golden/*.json` diff is not automatically wrong, but it is never silent:

1. Confirm which dimension/geometry actually moved and why (a real design change vs. an
   accidental regression from an unrelated edit).
2. State that in the PR description's "Goldens changed?" section (the PR template has a slot for
   this) — what changed and why the new value is correct.
3. If it's a real change, `python scripts/build.py golden --update` to refresh the baseline, then
   re-run `build.py all` to confirm it's now clean.
4. If it's unexplained, treat it as a regression — find the cause before updating the golden, don't
   update-to-make-CI-pass.

## Troubleshooting

| Situation | Fix |
|---|---|
| Accidentally committed on `develop` | `git branch feature/x` (captures the commit), `git reset --hard origin/develop` (restores develop), then continue on `feature/x`. |
| Accidentally committed on `main` | Same pattern: `git branch hotfix/x` or `feature/x` first, then `git reset --hard origin/main`. |
| Feature branch fell behind `develop` | `git checkout feature/x && git fetch origin && git rebase origin/develop` (or `git merge origin/develop` if the branch is already public/shared — never rebase a branch others have pulled). |
| Wrong base branch on an open PR | Retarget the PR in GitHub (`gh pr edit --base <branch>`) rather than closing and reopening, so review history survives. |
| Tag pushed to the wrong commit | Ask the user before deleting/re-pushing a tag — `git push --delete origin vX.Y.Z` is a shared-history rewrite of a public release marker, not a local cleanup. |
| `release/*` or `hotfix/*` merged into `main` but the `develop` back-merge was forgotten | Open the back-merge PR immediately — the next release from `develop` would otherwise silently drop the fix. |
| Need to abandon a feature branch entirely | Ask the user before deleting a pushed branch (`git push origin --delete feature/x`); a local-only branch can be deleted (`git branch -D`) without asking since nothing shared depends on it. |
