<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file -->
# Checking CLAUDE.md's facts

## Commands (the Commands section, "Checks before a pull request" in CONTRIBUTING.md)

- **Sources:** package.json scripts (`check`, `lint`, `typecheck`, `test`, `build`), CI `run:` lines, the test layout
  (`tests/`, `*.test.*`, `test_*.py`), tool configs (e.g. `drizzle.config.*` → `npx drizzle-kit check`).
- **Verified** when the script or file exists and CI or the test layout uses it.
- **Run one only if** it needs no install, network, docker, `.env` or service. A fresh worktree has no
  `node_modules`: `npx <tool>` would download a missing package, so use `npm exec --no -- <tool>` (fails instead of
  downloading) or mark it `# unverified: needs npm ci`.
- **Format:** one bash block, one command per line with a `# what it checks` comment, then bullets for traps (needs a
  clean env, needs `.env`, uses the network).

## Other sections

- **Overview and ports:** from compose `ports:`, the dev server config, `.listen(`/`serve(`/`app.run(` defaults.
- **Architecture:** read the entry points and the main folders; name them. Nothing speculative.
- **Recipes:** base each on a recent change of that kind (`git -C "<dir>" log --oneline -- <folder>`) so the steps
  match how the code is really extended; every path must exist.
- **Deployment:** the named scripts, hosts and paths exist; a deploy that copies the working tree (rsync, scp, a
  host-side `docker build .`) runs only from a checkout of the production branch; never from the QA branch.
- **Gotchas:** from comments marked as traps, fix commits ("fix: …"), issues, and the dev's own notes. Each names the
  file and the trap.
- **Conventions in this project:** only what the code shows, with evidence: the same pattern in several files, or a
  lint or config rule. Nothing clear → leave it out; never guess.

## Existing CLAUDE.md files

- A hand-written branching or git section is replaced by the managed Git workflow block (by /init-project). Its
  project-specific lines (worktree setup, services tied to the main checkout, history notes) move under
  `### Branches in this project`, wording kept.
- Lines that conflict with the managed blocks (branch names without issue numbers, merging into develop, rebasing
  pushed branches) are shown old → new for the dev to confirm.
- "Workstreams" in older text means sub-branches; propose the one-word change.
