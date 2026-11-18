<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file, so put project notes in CLAUDE.md below the Git workflow block -->
# Git workflow

These rules load in every session. CONTRIBUTING.md describes the same workflow for people; CLAUDE.md › Git workflow
is the summary. A hook (`.claude/hooks/git-guard.py`) blocks the commands marked **(hook)**. Treat a block as the
rule working: never look for another way to do the same thing.

## Ask first

Before any git or gh command that changes something, show the exact command(s) and wait for the dev's yes. That
covers commit, push, pull, merge, switch or checkout, creating or deleting a branch, worktree add or remove, and
creating, editing, commenting on or closing issues and pull requests. One yes covers the commands it listed, not
later ones. Read-only commands run freely: status, log, diff, show, blame, fetch, `branch --list`,
`worktree list`, `gh … view`, `gh … list`, `gh … status`. A skill the dev invoked counts as the yes for the git
steps its instructions and its card list.

## Branches

| Branch | Holds | Rules for Claude |
|---|---|---|
| `main` (or `master`) | Production | Never branch from it **(hook)**, open a PR into it **(hook)**, merge into it **(hook)**, commit on it **(hook)** or push to it **(hook)**. The dev deploys by merging `develop` in a PR titled exactly `[ production deploy ]`. |
| `develop` | Reviewed work waiting for production; the base for all work | Cut every branch from an up-to-date `origin/develop` and open every PR into it. Never merge into it **(hook)**, commit on it **(hook)** or push to it **(hook)**; pull it only with `--ff-only` **(hook)**. |
| `beta` (or `deploy`) | Features in review, merged together for QA | Merge a branch into it only when the dev asks. Never branch from it **(hook)**, merge it anywhere **(hook)**, or open a PR from or into it **(hook)**. Commit on it only to finish a merge **(hook)**. |

Never merge a pull request (`gh pr merge`) **(hook)**: the dev reviews and merges. Never delete, rename or move a
permanent branch **(hook)**.

## Issues

Every feature and fix has a GitHub issue. Always ask the dev before creating an issue or linking work to an existing
one: search first (`gh issue list --search "<words>"`), then propose "link #n" or the title and body.

## Feature and fix branches

- `feature/<issue>-<short-description>` or `fix/<issue>-<short-description>`, lowercase and hyphenated
  (`feature/42-savings-fund-cards`). Start from the remote, whatever is checked out:
  `git fetch origin && git switch --no-track -c <branch> origin/develop`.
- Catch up by merging `origin/develop` in. Never rebase **(hook)** or force-push **(hook)** a branch that has been
  pushed.
- **Sub-branches.** A big feature or fix may get sub-branches cut from it, named `<branch>--<short-sub-description>`
  (`feature/42-savings-fund-cards--chart`), with no issue and no PR. State their dependency order and file collisions
  up front, then merge each back with `git merge --no-ff`: the foundation before the ones that depend on it start,
  all of them before final review. Parallel ones run in worktrees under `.claude/worktrees/`; work on one file stays
  in one sub-branch. Ask once before deleting merged ones.

## Pull requests

When the branch is ready: run the project agents (CLAUDE.md › Agents), and `update-readme`, `update-claude-md` or
`update-contributing` when the change touches what they cover. Then, with the dev's yes: `git push -u origin
<branch>` and `gh pr create --base develop` **(hook: never into production or QA, never from a permanent branch)**,
with a body that starts `Closes #<issue>`, then says what changed and why, how it was verified, and which
sub-branches were merged in and why the work was split. The dev reviews and merges.

## Changelog

Claude never edits CHANGELOG.md and never runs `update-changelog`: the dev runs `/update-changelog` before a
production deploy, and it writes the release on its own `changelog/<date>` branch. Pull requests need no changelog
bullet. Edits to CHANGELOG.md and commits that include it are blocked outside a `changelog/` branch **(hook)**, so
it is never changed on a feature branch, develop, production or the QA branch.

## QA, only when the dev asks

In the main checkout: `git fetch origin`; stop and ask if tracked files have uncommitted changes;
`git switch <qa-branch> && git pull --ff-only`; `git merge --no-ff origin/develop`, then `git merge --no-ff <branch>`;
`git push origin <qa-branch>`. Fix problems on the branch and merge it again. Rebuilding the QA branch is described
in CONTRIBUTING.md; its `--force-with-lease=<qa>:<old sha>` push is the only force push allowed **(hook)**.

## Production

The dev runs `/update-changelog`, merges its pull request, then merges `[ production deploy ]`. Afterwards `main` has
a merge commit `develop` lacks: expected. If `main` ever has code `develop` lacks, tell the dev.

## Always

- Never stash, discard or reset uncommitted work **(hook: `stash`, `reset --hard`, `clean`, `checkout`/`restore` of
  files, forced switches)**; the dev may be using GitHub Desktop.
- Delete a branch only when the dev approves. Never `worktree remove --force` **(hook)**.
- Never commit secrets **(hook: `.env` files and `.claude/settings.local.json`)**.
- In a public repo keep personal paths, emails, names, hostnames, IPs, account IDs, tokens and personal, financial
  or health data out of files, commits, issues and PRs.
