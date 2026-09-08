---
name: git-flow
description: Pick a branch, sequence commits and prepare a PR/release under this repo's simplified Git Flow (feature/* → main, releases via tags)
---

# git-flow

This repo uses a **simplified Git Flow**: `main` is the only long-lived branch (integration and
release both), everything else is a short-lived `feature/*` branch merged in via PR, and releases
are annotated `vX.Y.Z` tags on `main`. There is no `develop`, `release/*`, `hotfix/*`, or `support/*`
branch, and no AVH `git flow` extension — plain git only. The full recipe book is `CONTRIBUTING.md`
— read it once. This file is the condensed operating guide: which branch a task belongs on, the
command sequence, and when to stop and ask the user.

## Picking the branch

Everything — a feature, a new case variant, a coupon, a doc change, a routine fix, or an urgent fix
on something already released — is a `feature/*` branch off `main`, merged back into `main` via PR.

| Task | Naming |
|---|---|
| Ordinary work | `feature/<kebab-topic>` |
| Work tracked by a GitHub issue | `feature/issue-<n>-<topic>` |
| An urgent fix on something already released | `feature/hotfix-<topic>` (or `feature/issue-<n>-<topic>` if an issue tracks it) |

A hotfix is **not** a separate branch type — same branch-from-`main`, same PR-into-`main`, same
CI gate as everything else. There's no separate hotfix workflow to remember.

If a task doesn't obviously fit — e.g. "should this ride along with an already-open feature branch"
— ask the user rather than guessing.

## Command sequences

Full versions with more inline explanation are in `CONTRIBUTING.md`; this is the copy-pasteable
core.

**Start a feature:**
```
git switch -c feature/<kebab-topic> main
```

**Commit on the feature branch** — this is fine to do locally without asking, once the user has
asked for the work:
```
git add <specific files>
git commit -m "feat(<scope>): <summary>

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

**Keep it current if `main` moves:**
```
git fetch origin
git merge main
```
Never rebase a branch that's already been pushed or has an open PR — merge `main` into it instead.

**Publish + PR** (always ask first — see "When to ask" below):
```
git push -u origin feature/<kebab-topic>
gh pr create --base main --title "..." --body "... 🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

**Merge** (ask first): squash or a regular merge commit, maintainer's call, once `render` is green.
Delete the feature branch afterward.

**Release by tag** (ask before every push/PR/merge/tag step):
```
git switch -c feature/release-vX.Y.Z main
# move CHANGELOG.md [Unreleased] -> ## [X.Y.Z] - YYYY-MM-DD, bump the version wherever recorded
python scripts/build.py all --release
git push -u origin feature/release-vX.Y.Z
gh pr create --base main --title "chore(release): vX.Y.Z" --body "..."
# after the render check is green and the PR is merged:
git checkout main && git pull
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```
Pushing the tag triggers the `render.yml` release job — verify the GitHub Release carries the
expected `*.stl`/`*.3mf`/`*.manifest.json` assets before announcing it.

## Naming rules

- `feature/<kebab-topic>`, or `feature/issue-<n>-<topic>` when a GitHub issue exists
  (`.claude/knowledge/ticket-source.md`). Don't invent an issue number — check with `gh issue list`
  first if unsure whether one exists.
- `feature/hotfix-<topic>` for an urgent fix on something already released.
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
pushing a tag, merging any branch into `main` by any method.

**Fine to do without asking**, once the user has already asked for the underlying work: creating a
local `feature/*` branch, committing to it, running `python scripts/build.py all` locally.

**Never do, full stop:** commit directly on `main` (even a one-line fix — branch off first),
force-push `main`, skip the `render` CI check before merging, delete `main`.

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
| Accidentally committed on `main` | `git switch -c feature/x` (captures the commit), `git switch main && git reset --hard origin/main` (restores `main`), then continue on `feature/x`. |
| Forgot the `Co-Authored-By` footer | Amend the commit (`git commit --amend`) before it's pushed. Once it's pushed, leave it — don't rewrite shared history to fix a footer. |
| Feature branch fell behind `main` | `git fetch origin && git merge origin/main` on the feature branch. Rebase is fine only if the branch is still purely local and has no open PR. |
| Wrong base branch on an open PR | It should always be `main` — retarget with `gh pr edit --base main` rather than closing and reopening, so review history survives. |
| Tag pushed to the wrong commit | Ask the user before deleting/re-pushing a tag — `git push --delete origin vX.Y.Z` is a shared-history rewrite of a public release marker, not a local cleanup. |
| Need to abandon a feature branch entirely | Ask the user before deleting a pushed branch (`git push origin --delete feature/x`); a local-only branch can be deleted (`git branch -D`) without asking since nothing shared depends on it. |
