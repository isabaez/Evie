<!-- init-project-file v2 — managed by /init-project; re-sync replaces this file -->
# The four required parts

Every README has these, in the README's own structure and voice. Existing sections that already do the job count:
map them rather than adding duplicates.

## 1. Name and introduction

`# <Project name>`, then one or two sentences: what it is, who it's for, and what it does first. No badges or
slogans. A scope line is welcome when it matters ("Personal and local-only: no accounts, nothing leaves this Mac").

## 2. Getting it running locally

- **Prerequisites** with versions from the code: `engines` in package.json, `.nvmrc`, `.python-version`,
  `requires-python`, Dockerfile `FROM` tags, the lockfile's resolved versions.
- **Install, configure, run, test**, as copyable commands verified against package.json scripts, the Makefile,
  `bin/` scripts or `pyproject.toml`. Configuration names env vars from `.env.example` or the code, never values.
- The URL and port the app answers on (from the dev server config, compose `ports:`, or the code's default).
- Anything that runs services, installs or writes data says so ("starts Postgres in Docker").

## 3. Directory layout

A fenced tree of the top-level folders and the files people touch, each with a short purpose, 25 lines at most:

```text
client/        React single-page app (CSS Modules, hand-rolled SVG charts)
server/        Hono API, Drizzle queries, the analytics layer
shared/        Zod schemas: the contract between client and server
drizzle/       generated migrations (never edited by hand)
start.sh       one-command local start: database, migrations, seed, dev server
```

Leave out generated, vendored and ignored folders (`node_modules/`, `dist/`, `.venv/`) unless people need to know
about them. Check every path exists: `git -C "<dir>" ls-files <path> | head -1`.

## 4. Working with Claude Code

Rebuilt from what is installed every time the skill runs. Shape:

```markdown
## Working with Claude Code

This project is set up for [Claude Code](https://code.claude.com/docs). [CLAUDE.md](CLAUDE.md) holds the rules
Claude follows here; [CONTRIBUTING.md](CONTRIBUTING.md) describes the same workflow for people.

**Skills** (run with `/<name>`, or Claude runs them when they apply):
- `/update-changelog`: the dev runs it before a production deploy to write the release notes in CHANGELOG.md.
- `/update-readme`: checks this README against the code and fixes what drifted.
- `/update-claude-md`: keeps CLAUDE.md accurate; `/update-claude-md deep` audits it thoroughly.
- `/update-contributing`: keeps CONTRIBUTING.md in step with the workflow.

**Agents** (Claude runs them before opening a pull request): `code-reviewer`, `security-auditor`, …, one line each.

**Rules:** `.claude/rules/` holds stack-specific conventions that load with matching files, and
`git-workflow.md`, the full git workflow, which loads in every session.

**Hooks:** a git guard blocks the git and gh commands the workflow never allows (merging into `develop` or
`main`, force pushes, discarding uncommitted work, editing CHANGELOG.md outside a release branch, …).
```

One line per skill, agent and rules file, taken from its description, so the list matches what exists. Include
the project's own skills (those without an init-project marker) too.
