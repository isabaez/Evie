---
name: update-claude-md
description: Keeps CLAUDE.md accurate, concise and effective so Claude works well in this project: overview, commands, git workflow, changelog rules, architecture, recipes for common changes (adding a feature, changing design elements), code conventions and accessibility rules grounded in the official docs for the project's stack, project agents, deployment and gotchas. Verifies every command, path and claim against the code, keeps CLAUDE.md near 200 lines by moving file-type-specific detail into path-scoped .claude/rules/ files, and never edits the init-project managed blocks. Use when the dev asks to update, check, audit or deep-dive CLAUDE.md ("/update-claude-md deep"), and after a change to commands, architecture, conventions, accessibility helpers or deployment.
argument-hint: "[deep]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/blocks.py *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/conventions_scan.py *)
---

<!-- init-project:skill:update-claude-md v2 — managed by /init-project; re-sync replaces up to the end marker, so keep project facts in "This project" below -->
# Update CLAUDE.md

CLAUDE.md loads into every Claude Code session in this project, so every line costs context every time and has to
earn its place: facts Claude can't cheaply work out, rules that prevent mistakes, commands that work. Keep it under
about 200 lines; detail for particular file types goes into `.claude/rules/`, which loads with matching files.
Layout: [reference/layout.md](reference/layout.md). Checking facts: [reference/audit.md](reference/audit.md).
Official sources for best practices: [reference/stack-sources.md](reference/stack-sources.md).

`<dir>` is the checkout you work in; draft in the session scratchpad (or `mktemp -d`), called `<scratch>`.

## Ground rules

- Facts, not advice: each line names the file, command, token or decision it applies to, and is checked against the
  code or given by the dev.
- The init-project managed blocks (Git workflow, Changelog, Code conventions and accessibility, Agents) are
  read-only: never edit between their markers. If one looks wrong or stale, say "re-sync with /init-project"; project
  additions go directly below its end marker. The same goes for `.claude/rules/git-workflow.md` (an
  `init-project-file` header): never edit it.
- Keep the dev's structure and voice: add rather than reorder, and never drop a project fact without saying where it
  went.
- Never run installs, services, docker, seeders or networked or paid jobs; see reference/audit.md for which commands
  may run.
- The layout's sections are this skill's job; anything beyond the layout (a new kind of section, a FAQ) goes in only
  with the dev's yes.
- CLAUDE.md and `.claude/rules/*.md` are the only files this skill edits. Public repo: nothing sensitive (no
  personal paths, emails, names, hostnames, IPs, account IDs or personal data).

## Called from /init-project

init-project passes the setup worktree (already on its branch, with the managed blocks already in place), the setup
issue `#N`, a scratch directory, whether the repo is public, and a mode: `setup` (complete the project sections and
rules files) or `resync` (only facts next to blocks that changed). Skip *Where to work* and *Finish*: draft only in
the scratch directory, list your decisions for init-project's plan card instead of asking them yourself, and let
init-project apply, verify and commit. Conventions gaps go to init-project's Follow-ups step.

## 1. Where to work

- On a `feature/` or `fix/` branch (or one of its `--` sub-branches): edit there.
- On `develop`, `main` or `master`: ask "Link #n / Create an issue / Draft only" (always ask before creating or
  linking an issue), then `git -C "<dir>" worktree add --no-track -b fix/<issue>-claude-md-<short-description>
  "<dir>/.claude/worktrees/claude-md-<short-description>" origin/develop` and work there.
- On the QA branch (`beta`/`deploy`): never edit.

## 2. Which file

`.claude/CLAUDE.md` if it exists, else `CLAUDE.md`; call it CM. CM is a symlink → ask which file to edit. Leave
`AGENTS.md` and `CLAUDE.local.md` alone, but say so if they contradict CM.

## 3. Map it to the layout

List CM's sections against reference/layout.md: each goes to a slot, and is kept, moved, renamed, added or cut (cut
only with the dev's yes). The managed blocks' order is fixed; project text moves freely around them. To put a section
in its slot (an old `## Gates` becomes `## Commands` above the git-workflow block), cut it and paste it there without
touching any line between markers, and show the move on the card. "Add rather than reorder" is about the dev's own
extra sections: they keep their order, after Gotchas.

## 4. Facts

Per reference/audit.md, write or correct: the overview (stack, **ports in bold**, how to run it, a pointer to the
README); Commands (verified, or marked `# unverified: <why>`); Branches in this project (the real names: main or
master, beta or deploy, plus service steps after a QA merge); Architecture (how the pieces fit, the data flow, where
state lives); Recipes (two to four, each at most six steps with real paths: adding a feature like the ones this code
has, changing design elements such as tokens and shared styles, adding a page, route or endpoint); Deployment (how it
ships, from which branch); Gotchas (traps that bit before, from history, comments and issues, and traps visible in the
code now: a missing lockfile, config or entry point, a script that isn't executable, a stylesheet nothing imports).

## 5. Conventions and accessibility

1. `python3 ${CLAUDE_SKILL_DIR}/scripts/conventions_scan.py "<dir>"` inventories CSS class naming (the BEM share),
   JS hooks (`js-` classes, styled hooks, id or styling-class selectors), single-letter names, and accessibility
   helpers (visually hidden text, skip link, focus styles, reduced motion, live regions, dialogs, contrast checks).
2. Best practices from the official sites in reference/stack-sources.md, in this order: the UI framework, the CSS
   approach, accessibility patterns for components this project has, the server framework, the language's style
   guide. About six pages in a normal run (more with `deep`); deeper pages on the same official sites are better
   than landing pages. Distill the rules that matter for this code into `.claude/rules/<topic>.md` (e.g.
   `svelte.md`, `css.md`, `python.md`, `accessibility.md`), 60 lines at most each, with `paths:` frontmatter
   (`paths: ["src/**/*.svelte"]`) and a source URL plus "checked YYYY-MM-DD" per rule. Don't restate the managed
   conventions block.
3. Below the conventions block, `### Conventions in this project`: project facts with evidence (units and money,
   the tokens file, the data-access layer, dependency policy, where helpers live), minus anything that only restates
   the block (an old "use BEM" line). When the stack makes a convention awkward (CSS Modules exporting camelCase
   names, a framework's own naming), ask: "Keep <pattern> as a documented exception" / "Follow the convention in new
   code (Recommended)"; only an approved exception is written here. `### Accessibility in this project`: the helpers
   that exist, where, and whether anything loads them (from the scan), the project's own rules (e.g. larger touch
   targets on a kiosk), and the contrast check, if any.
4. What the scan finds that doesn't meet the conventions, and helpers that are missing, are proposals for follow-up
   issues (asked first), never fixed in this change.

## 6. deep (`/update-claude-md deep`)

Everything above, plus an effectiveness pass, reported as a table before drafting:
- contradictions across CM, `.claude/rules/`, the agents' "This project" sections and the skills;
- vague lines made concrete, or cut;
- procedures longer than about six steps moved into a skill or rules file;
- README duplication replaced by a pointer;
- stale lines: `git -C "<dir>" log -1 --format=%cs -- <path>` for files CM describes;
- a line budget: CM's lines per section, and each rules file.

## 7. Draft, show, apply

Draft CM (and any rules files) in `<scratch>` (or at the draft path /init-project gives). Check that every managed
block is untouched: `python3 ${CLAUDE_SKILL_DIR}/scripts/blocks.py check <draft> --against <before>`, where `<before>`
is `<dir>/<CM path>`, or in setup mode init-project's draft as it was right after the blocks went in. Card:
`git diff --no-index`, the line count before → after, and the rules files. One AskUserQuestion: Q1 "Apply the
CLAUDE.md update?" (Apply / Skip); Q2 new sections or rules files (multiSelect, up to 4). Apply, then re-check the
commands you cited.

## 8. Finish

Standalone: `git -C "<dir>" commit -m "Bring CLAUDE.md in line with the code" -- <CM path> .claude/rules`, then ask
"Push and open a PR into develop?". If yes: `git -C "<dir>" push -u origin <branch>` and `gh pr create -R <owner>/<name> --base develop` (the repo from
`git -C "<dir>" remote get-url origin`) with a body starting `Closes #<issue>`.
Remove a worktree you created once it is clean. If you had to discover a project fact that "This project" lacks,
propose adding it.
<!-- /init-project:skill:update-claude-md -->

## This project

<!-- Filled in by /init-project. The CM path; the stack and the official docs used (with the date checked); the rules files and what each covers; the line budget; convention exceptions the dev approved. Facts only; nothing sensitive in a public repo. -->
- CLAUDE.md lives at the repo root.
- Stack: Node.js + Express 4, Handlebars views (`hbs`), Passport local auth, Mongoose 4 (MongoDB), Twilio SMS. CommonJS, no build step, no tests.
- The app is slated for a rebuild as a static demo; describe what the code does now, not the plan.
