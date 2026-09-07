# Ticket source

Status: **no external ticket system is configured for this repo.**

## Where work is tracked

Work is tracked as **GitHub issues** in this repository. The repo owner/name is read from the git
remote rather than hardcoded here, since it can change:

```
git remote -v
```

As of this file's creation, `origin` is `https://github.com/nielsverhoeven/magewell-converter-cases`
— if that remote is absent, unreachable, or the repo hasn't been pushed yet, treat the ticket source
as **"not yet pushed"** and fall back to the local plan file described below rather than guessing at
an owner/repo.

No Jira, Linear, Asana, or other external tracker is connected to this repo. If a subagent's routing
table (e.g. the Team Charter) names one of those as a default, it does not apply here — this repo
uses GitHub issues only.

## Where researchers write plans

- **If a GitHub issue already exists for the task**, `researcher` writes its findings/plan back as a
  comment on that issue (`gh issue comment <n> --body-file <plan>`, or the equivalent GitHub MCP
  tool if connected).
- **If no issue exists** (a plan was requested ad hoc, or the repo isn't pushed yet), write the plan
  to `docs/plans/<date>-<slug>.md` instead — `<date>` in `YYYY-MM-DD` form, `<slug>` a short
  kebab-case description of the task. Create `docs/plans/` if it doesn't exist yet; nothing else
  currently owns that directory.

## Branch naming for tracked work

When a GitHub issue exists for a task, its feature branch references the issue number:
`feature/issue-<n>-<topic>` (e.g. `feature/issue-12-vents`), so the branch and the tracked work are
traceable to each other at a glance. When no issue exists — ad hoc work, or the repo isn't pushed
yet — fall back to the plain `feature/<kebab-topic>` naming from `CONTRIBUTING.md`; don't invent an
issue number to force the numbered form. See the `git-flow` skill and `CONTRIBUTING.md` for the full
branching model.

## Notes for future maintenance

- If this repo later adopts an external tracker, update this file's "Where work is tracked" section
  — don't leave it claiming "no external tracker" once one exists.
- Do not invent issue numbers or assume a specific GitHub issue exists without checking
  (`gh issue list` or the GitHub MCP tools) — an agent that fabricates a ticket reference creates a
  worse trail than no reference at all.
