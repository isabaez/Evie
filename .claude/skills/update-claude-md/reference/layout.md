<!-- init-project-file v2 — managed by /init-project; re-sync replaces this file -->
# CLAUDE.md layout

Target: under about 200 lines. The four managed blocks come from /init-project and are never edited here; the
project sections around them are this skill's job. Block markers are HTML comments, which Claude Code leaves out of
context, so they cost nothing.

```markdown
# <Project> — working agreements

<2–4 lines: the stack; ports in bold; how to run it; "README.md is the product doc: read the section for the area
you are touching before changing it.">

## Commands
<one bash block, one command per line with a `# what it checks` comment; then bullets for traps>

<!-- init-project:git-workflow v1 … -->
## Git workflow
<!-- /init-project:git-workflow -->

### Branches in this project
<the real names (main or master; beta or deploy); services to restart after a QA merge; worktree setup>

<!-- init-project:changelog v1 … -->
## Changelog
<!-- /init-project:changelog -->

## Architecture
<how the pieces fit; the data flow; where state lives; 5–15 lines>

## Recipes
### Add a <thing this project adds often>
### Change a design element
<2–4 recipes, each at most 6 steps with real paths>

<!-- init-project:conventions v1 … -->
## Code conventions and accessibility
<!-- /init-project:conventions -->

### Conventions in this project
### Accessibility in this project

<!-- init-project:agents v1 … -->
## Agents
<!-- /init-project:agents -->

## Deployment
## Gotchas

## <the project's own sections, e.g. Design feedback loop>   kept, same order
```

## House style

- Facts, not advice. Each bullet is something the code shows or the dev decided, naming the file, function or token:
  "**Money is integer cents** end to end. `formatCents` / `parseCents` in `src/lib/money.ts`."
- A bold lead phrase, then the reason or the trap that bit before. No filler, no generic tips.
- Don't repeat the README: point at it. Don't restate a managed block anywhere else.
- Detail for particular file types (framework idioms, CSS rules, test style) goes into `.claude/rules/<topic>.md`
  with `paths:` frontmatter; CM keeps one line pointing at it only if the rule matters outside those files.
- An existing CM keeps its sections; what doesn't fit a slot stays where it is, after Gotchas.
- A project with no code yet: the overview says what it will be; Commands is "None yet: add them with the first
  code."; no Architecture, Recipes or Conventions in this project.

## Rules files

```markdown
---
paths:
  - "src/**/*.svelte"
---
# Svelte

- Use runes (`$state`, `$derived`, `$effect`) for component state; `$effect` only for side effects.
  Source: https://svelte.dev/docs/svelte/what-are-runes (checked 2026-09-26)
```

One topic per file, 60 lines at most, only rules that apply to this project's code, each with its source. The
frontmatter `paths` lists globs for the files the rule is about; a file with no `paths` loads in every session, so
only accessibility rules that apply everywhere may omit it. The exception is `git-workflow.md`, installed and
re-synced by /init-project (its first line is an `init-project-file` header): it loads everywhere and isn't bound
by these limits. Never edit it, and don't count it in the rules-file budget.
