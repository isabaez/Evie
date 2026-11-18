---
name: update-contributing
description: Keeps CONTRIBUTING.md, the guide for people working on this project, in step with its git workflow: what main (or master), develop and beta (or deploy) are for, starting from an issue, feature/ and fix/ branch names, sub-branches for big changes, pull requests into develop (no changelog bullet: the maintainer writes the release notes before a production deploy), testing on the QA branch, and releasing to production, plus the checks to run before a pull request. Use when the dev asks to update or check CONTRIBUTING.md or how to contribute, and after a change to the workflow, the pre-PR checks, QA steps or the release process.
---

<!-- init-project:skill:update-contributing v3 — managed by /init-project; re-sync replaces up to the end marker, so keep project facts in "This project" below -->
# Update CONTRIBUTING.md

CONTRIBUTING.md explains the project's workflow to people; CLAUDE.md explains the same workflow to Claude, and the
two must agree. The workflow itself is the managed `contributing-workflow` block from /init-project, read-only here;
this skill keeps the project-specific parts around it true. Layout: [reference/layout.md](reference/layout.md).

`<dir>` is the checkout you work in; draft in the session scratchpad (or `mktemp -d`), called `<scratch>`.

## Ground rules

- The managed block is read-only: never edit between its markers. Wrong or stale → "re-sync with /init-project".
- Verify every command you cite the way update-claude-md's `reference/audit.md` describes; never run services,
  installs, docker or networked or paid jobs.
- CONTRIBUTING.md is the only file this skill edits. Public repo: nothing sensitive.

## Called from /init-project

init-project passes the setup worktree (already on its branch, with the managed block already in place), the setup
issue `#N`, a scratch directory, whether the repo is public, and a mode (`setup` or `resync`). Skip *Where to work*
and *Finish*: draft only in the scratch directory, list your decisions for init-project's plan card instead of
asking them yourself, and let init-project apply, verify and commit.

## 1. Where to work

- On a `feature/` or `fix/` branch (or one of its `--` sub-branches): edit there.
- On `develop`, `main` or `master`: ask "Link #n / Create an issue / Draft only" (always ask before creating or
  linking an issue), then `git -C "<dir>" worktree add --no-track -b fix/<issue>-contributing-<short-description>
  "<dir>/.claude/worktrees/contributing-<short-description>" origin/develop` and work there.
- On the QA branch (`beta`/`deploy`): never edit.

## 2. Create or update

Per reference/layout.md: a title and a one- or two-line intro (who it's for; setup lives in the README), the managed
block, then the project sections: `## Checks before a pull request` (the commands from CLAUDE.md › Commands that gate
a PR, each verified), `## QA in this project` (the QA branch's real name, and anything to restart after merging into
it), `## Releasing this project` (deploy steps beyond the block, and where it runs), and a `## Code style` pointer to
CLAUDE.md › Code conventions and accessibility (a pointer, not a copy). No managed block in the file and /init-project
unavailable: write only the project sections and say the workflow section comes from /init-project.

## 3. Consistency

Nothing in CONTRIBUTING.md contradicts CLAUDE.md: branch names, commands, QA and release steps. The two workflow
blocks are released together, so their versions match: compare
`python3 "<dir>/.claude/skills/update-claude-md/scripts/blocks.py" list "<dir>/CLAUDE.md"` (the `git-workflow` line)
with the same command on `<dir>/CONTRIBUTING.md` (the `contributing-workflow` line). Report any mismatch.

## 4. Draft, show, apply

Draft in `<scratch>/CONTRIBUTING.md` (or at the draft path /init-project gives); check the block is untouched:
`python3 "<dir>/.claude/skills/update-claude-md/scripts/blocks.py" check <draft> --against "<dir>/CONTRIBUTING.md"`
(a new file has nothing to compare). Card: the diff and the commands you verified. One AskUserQuestion: "Apply the
CONTRIBUTING.md update?" (Apply / Skip). Apply by copying the draft back.

## 5. Finish

Standalone: `git -C "<dir>" commit -m "Bring CONTRIBUTING.md in line with the workflow" -- CONTRIBUTING.md`, then ask
"Push and open a PR into develop?". If yes: `git -C "<dir>" push -u origin <branch>` and `gh pr create -R <owner>/<name> --base develop` (the repo from
`git -C "<dir>" remote get-url origin`) with a body starting `Closes #<issue>`.
Remove a worktree you created once it is clean. If you had to discover a project fact that "This project" lacks,
propose adding it.
<!-- /init-project:skill:update-contributing -->

## This project

<!-- Filled in by /init-project. The QA branch's name and anything to restart after merging into it; where deploy steps are documented; the pre-PR checks and which of them need a running service. Facts only; nothing sensitive in a public repo. -->
- QA branch: `beta`. Nothing runs from it yet (no deploy), so nothing restarts after merging into it.
- No deploy steps are documented; the original Heroku deploy is gone.
- No lint, typecheck or test scripts exist; the only package script is `start` (nodemon), which needs a live MongoDB and Twilio credentials.
