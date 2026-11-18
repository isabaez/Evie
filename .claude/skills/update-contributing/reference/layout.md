<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file -->
# CONTRIBUTING.md layout

```markdown
# Contributing to <Project>

<1–2 lines: who this is for (people changing the code) and where to start: the README for getting it running.>

<!-- init-project:contributing-workflow v1 … -->
## How changes flow
…
<!-- /init-project:contributing-workflow -->

## Checks before a pull request

<one bash block of the commands from CLAUDE.md › Commands that gate a PR, each with a `# what it checks` comment;
then bullets for anything they need (a clean env, a running database)>

## QA in this project

<the QA branch's real name when it isn't beta; services to restart after merging into it (e.g.
`docker compose restart engine`); where the QA copy of the app runs>

## Releasing this project

<what happens after `[ production deploy ]` merges: how the app gets deployed and where; "run deploy scripts only
from a checkout of main">

## Code style

Conventions and accessibility rules are in [CLAUDE.md](CLAUDE.md) (Code conventions and accessibility, plus
`.claude/rules/`); they apply to changes made by hand too.
```

- Keep the maintainer's existing sections and wording; add the missing ones after the block.
- Leave out a project section that has nothing true to say yet (no checks exist, no deploy): don't pad it.
- Commands come from the code and are verified, never invented. Paths are repo-relative.
- Public repo: no personal names, hostnames, IPs or paths.
