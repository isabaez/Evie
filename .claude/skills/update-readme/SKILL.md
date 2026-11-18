---
name: update-readme
description: Keeps README.md accurate and useful for someone arriving at the project: its name and a one- or two-sentence introduction, how to get it running locally, the directory layout, and a "Working with Claude Code" section listing the project's skills, agents, rules and hooks. Checks every claim (commands, ports, env var names, paths, versions, features) against the code, fixes drift in the README's own structure and voice, and asks before adding anything beyond that. Use when the dev asks to update, write or check the README, and after a change to setup steps, commands, the directory layout, features, or the project's Claude skills and agents.
argument-hint: "[audit | new]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check_anchors.py *)
---

<!-- init-project:skill:update-readme v2 — managed by /init-project; re-sync replaces up to the end marker, so keep project facts in "This project" below -->
# Update the README

The README is for a person arriving at the project: what it is, how to get it running, where things are, and how
Claude Code is set up here. It must be true: every command, port, path and feature it mentions matches the code.
Required parts: [reference/sections.md](reference/sections.md). Checking claims:
[reference/audit.md](reference/audit.md). A project with no code yet: [reference/new.md](reference/new.md). Public
repos: [reference/sensitive.md](reference/sensitive.md).

`<dir>` is the checkout you work in; draft in the session scratchpad (or `mktemp -d`), called `<scratch>`.

## Ground rules

- Never run start, dev or serve scripts, docker, installs, seeders, migrations, or anything networked or paid to
  check a claim. Read files; use `git`, `grep`, `ls`, and `python3 -c` for JSON or TOML. Never open `.env` files.
- Keep the README's structure, headings, voice and anchors. Targeted edits only: no rewrites, reordering, badges,
  emojis, marketing lines or boilerplate sections.
- Nothing beyond fixes and the required parts goes in without the dev's yes.
- README.md is the only file this skill edits (plus docs the dev approves on the card).

## Called from /init-project

init-project passes the setup worktree (already on its branch), the setup issue `#N`, a scratch directory, whether
the repo is public, and a mode (`setup` or `resync`). Skip *Where to work* and *Finish*: draft only in the scratch
directory, list your decisions for init-project's plan card instead of asking them yourself (the plain-text purpose
question in reference/new.md still goes out first), and let init-project apply, verify and commit.

## 1. Where to work

- On a `feature/` or `fix/` branch (or one of its `--` sub-branches): edit there.
- On `develop`, `main` or `master`: ask "Link #n / Create an issue / Draft only" (always ask before creating or
  linking an issue), then `git -C "<dir>" worktree add --no-track -b fix/<issue>-readme-<short-description>
  "<dir>/.claude/worktrees/readme-<short-description>" origin/develop` (`feature/` for a new section) and work there.
- On the QA branch (`beta`/`deploy`): never edit; find the branch the change belongs to.

## 2. Mode

`new` when there is no README or the project has no code yet: follow reference/new.md. Otherwise `audit`.

## 3. The required parts, present and true

Map the README's sections to the four required parts in reference/sections.md (e.g. "Running it" is local setup,
"Layout" is the directory layout). Draft what's missing in the README's voice, where its structure suggests: the
intro at the top, setup early, the layout after setup, the Claude section near the end (before license or credits).

## 4. Claim audit

Follow reference/audit.md: list every checkable claim, verify each against the code, and build the drift table
(Wrong, Stale, Missing, Cosmetic, Questions, plus Sensitive for a public repo). A README over about 15 KB: split it
by `##` sections into up to 5 slices and launch that many Explore agents in one message.

## 5. Working with Claude Code (rebuilt on every run)

Rebuild the section from what is installed, per reference/sections.md: `.claude/skills/*/SKILL.md` (name and what it
does), `.claude/agents/*.md` (name and when it runs), `.claude/rules/*.md` (what each covers), the hooks in
`.claude/settings.json` (what they block), and links to CLAUDE.md and CONTRIBUTING.md. It lists exactly what exists,
so an added or removed skill or agent shows up here.

## 6. Proposals

Anything else that would help a newcomer (troubleshooting, an architecture sketch, screenshots, a FAQ, a license):
list it on the card with a one-line reason, and add only what the dev picks.

## 7. Draft, show, apply

`cp "<dir>/README.md" "<scratch>/README.md"` (or write it new), one targeted edit per approved row, then
`python3 ${CLAUDE_SKILL_DIR}/scripts/check_anchors.py "<scratch>/README.md"` → `anchors ok`. Card: the drift table,
the proposals and `git diff --no-index "<dir>/README.md" "<scratch>/README.md"`. One AskUserQuestion: Q1 "Apply the
README update?" (Apply / Skip); Q2 the proposals (multiSelect, up to 4). Apply: copy it back, re-grep each fixed claim
against its evidence, and for a public repo run the sensitive scan (0, or each hit explained).

## 8. Finish

Standalone: `git -C "<dir>" commit -m "Bring the README in line with the code" -- README.md`, then ask "Push and open
a PR into develop?". If yes: `git -C "<dir>" push -u origin <branch>` and `gh pr create -R <owner>/<name> --base develop` (the repo from
`git -C "<dir>" remote get-url origin`) with a body starting `Closes #<issue>`.
Remove a worktree you created once it is clean. If you had to discover a project fact that "This project" lacks,
propose adding it.
<!-- /init-project:skill:update-readme -->

## This project

<!-- Filled in by /init-project. README size and whether audits fan out; which existing sections map to the four required parts; sections tied to code (e.g. a setup section that must match service files); numbers or counts that must stay current. Facts only; nothing sensitive in a public repo. -->
- README.md is about 4.5 KB (no fan-out). Written at setup: intro (top paragraph), `## Getting it running locally`, `## Directory layout`, `## Working with Claude Code`.
- Local setup needs MongoDB and Twilio credentials (`MONGODB_URI`, `ACCOUNT_SID`, `AUTH_TOKEN`, `FROM_PHONE`); the setup section must match the env vars read in `app.js`, `routes/index.js` and `seed.js`.
- `events.json` holds the seeded event list; keep any count in the README in step with it.
