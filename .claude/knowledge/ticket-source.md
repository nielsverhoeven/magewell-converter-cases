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
- **If no issue exists yet**, one is opened first (user rule 2026-09-29, #68: every feature, bug and
  task gets a GitHub issue before any work). Only if the repo isn't pushed, write the plan to
  `docs/plans/<date>-<slug>.md` instead — `<date>` in `YYYY-MM-DD` form, `<slug>` a short kebab-case
  description of the task. A gated plan is also copied to `docs/plans/` with its architect verdict.

## Branch naming for tracked work

This repo has a single long-lived branch, `main`; every piece of work — including urgent fixes — is
a `feature/*` branch off `main`, merged back via PR. Every task has its GitHub issue first (user rule
2026-09-29, #68), so its feature branch always references the issue number:
`feature/issue-<n>-<topic>` (e.g. `feature/issue-12-vents`), its PR closes the issue, and the
records it creates are numbered after it (CLAUDE.md "Record ids follow GitHub issues"). Don't invent
an issue number — open the issue first. See the `git-flow` skill and `CONTRIBUTING.md` for the full
branching model.

## Notes for future maintenance

- If this repo later adopts an external tracker, update this file's "Where work is tracked" section
  — don't leave it claiming "no external tracker" once one exists.
- Do not invent issue numbers or assume a specific GitHub issue exists without checking
  (`gh issue list` or the GitHub MCP tools) — an agent that fabricates a ticket reference creates a
  worse trail than no reference at all.
