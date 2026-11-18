<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file -->
# Claim audit

Source of truth: the checkout you work in (`<dir>`). Read files only; never run start or dev scripts, docker,
installs, seeders, migrations, or anything networked or paid. Never open `.env`; env var names come from
`.env.example` or the code.

## 1. Inventory

List every checkable claim by category: **commands and scripts** (`npm run x`, `./bin/start.sh --logs`) · **env vars
and config** · **ports, URLs, binding** ("local only", "no server") · **routes, pages, API, CLI subcommands** ·
**paths** · **versions** · **features** ("drag to reorder") · **deploy and ops** (rsync, docker, cron, systemd,
backups) · **tests and CI**.

## 2. Verify each claim

- **Commands:** `python3 -c 'import json;print(json.load(open("<dir>/package.json")).get("scripts"))'`; `bin/*`,
  `Makefile`, `pyproject.toml` `[project.scripts]`. The file a command runs exists and handles the flag (grep it).
- **Ports and binding:** Dockerfile `EXPOSE`; compose `ports:` and `environment:`; `vite.config.*` `server.port`;
  `.listen(`, `app.run(`, `serve(`, `--port`, `PORT` defaults; `0.0.0.0` versus `127.0.0.1`.
- **Env vars, JS/TS:** `grep -rnoE 'process\.env\.[A-Z_][A-Z0-9_]*|import\.meta\.env\.[A-Z_][A-Z0-9_]*|\$env/(static|dynamic)/(private|public)' "<dir>" --exclude-dir=node_modules --exclude-dir=.git`
- **Env vars, Python:** `grep -rnoE "os\.(environ(\.get)?|getenv)[(\[][\"'][A-Z_][A-Z0-9_]*" "<dir>" --include='*.py' --exclude-dir=.venv`, plus compose `env_file:`.
- **Routes:** SvelteKit `src/routes/**/+page*.svelte` and `+server.*`; Next `app/**/page.*`; Express and Hono
  `(app|router)\.(get|post|put|patch|delete|use|route)\(`; Flask and FastAPI
  `@(app|router|bp)\.(route|get|post|put|delete)\(`; plain `*.html`.
- **Paths:** `ls "<dir>/<path>"`. **Versions:** package.json deps and `engines`, the lockfile, `.nvmrc`,
  `.python-version`, `requires-python`, Dockerfile `FROM`.
- **Features:** find the code that does it (UI strings, handlers, writes). A claim with no code is Wrong; shipped
  behaviour with no claim is Missing.
- **Since the README last changed:** `git -C "<dir>" log --no-merges --date=short --format='%h %ad %s' "$(git -C "<dir>" log -1 --format=%H origin/develop -- README.md)"..origin/develop`
  (develop's history, not this branch's own commits) and the merged PRs
  (`gh pr list -R <owner>/<name> --state merged --base develop --json number,title,mergedAt`): each user-visible
  change the README lacks is Missing.
- **Deploy:** named scripts, hosts and paths exist; a deploy that copies the working tree (rsync, scp, a host-side
  `docker build .`) must say to run it "from a checkout of `main`" (or `master`).
- **Tests and CI:** `.github/workflows/*.yml` `run:` lines; test folders.

## 3. Drift table (the plan card)

Grouped, empty groups left out. Columns: `# | section | claim → reality | evidence (file:line) | proposed edit`.
- **Wrong:** contradicts the code; following it fails.
- **Stale:** was true once; renamed, removed or changed since.
- **Missing:** shipped behaviour, commands, config or ports the README never mentions.
- **Cosmetic:** broken links or anchors, typos, formatting.
- **Questions the code can't settle:** intent, audience, deliberate gaps, measured numbers. Clear options become
  questions for the dev.
- **Sensitive** (public repos): per reference/sensitive.md.

A measured number keeps its "measured when": update the figure and the date, or mark it "(unverified)". A renamed
heading means fixing every `](#anchor)` that points to it.

## 4. Big READMEs (over about 15 KB)

`grep -n '^## ' "<dir>/README.md"` gives the sections and line ranges. Group them into up to 5 slices of similar size
and launch that many Explore agents in one message. Each prompt gives `<dir>`, the README path and line range, the
never-run rule, sections 1 and 2 of this file, and whether the repo is public; each returns only rows, or `none`:
`section | claim | reality | evidence file:line | proposed text`. Dedupe the rows, read the evidence of every Wrong
row yourself, then build the table.
