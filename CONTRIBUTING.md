# Contributing to Evie

For people changing the code; getting it running is in the README.

<!-- init-project:contributing-workflow v3 — managed by /init-project; re-sync replaces everything up to the end marker, so put project notes below it -->
## How changes flow

| Branch | What it holds | How code gets in |
|---|---|---|
| `main` (or `master`) | What's live in production | A pull request from `develop` titled exactly `[ production deploy ]`, merged with a merge commit |
| `develop` | Reviewed work waiting to ship | Pull requests from `feature/` and `fix/` branches, and the maintainer's `changelog/` release notes, reviewed and merged by the maintainer |
| `beta` (or `deploy`) | Features still in review, merged together for testing | Branches merged in for QA; it is never merged anywhere else |

### Making a change

1. **Start from an issue.** Find one that covers the change, or open one that describes the problem and
   what "done" looks like.
2. **Branch from an up-to-date `develop`:**
   `git fetch origin && git switch --no-track -c feature/<issue>-<short-description> origin/develop`
   (`fix/` for fixes), lowercase and hyphenated: `feature/42-savings-fund-cards`.
3. **Commit** in small steps with clear, sentence-case messages. To pick up newer work, merge
   `origin/develop` into your branch; don't rebase or force-push a branch you have pushed.
4. **Open a pull request into `develop`** that starts with `Closes #<issue>`, then says what changed, why,
   and how you checked it. Run the checks below first. Leave `CHANGELOG.md` alone: the maintainer writes
   the release notes when releasing (below), from your pull request's description.

### Big changes

A large feature or fix can be split into sub-branches named `<branch>--<part>`
(`feature/42-savings-fund-cards--chart`), each merged back into its branch with `git merge --no-ff`. They
get no issue or pull request of their own, and all of them are merged back before the branch is reviewed.
Say up front which parts depend on which and which files they share, and merge the part the others build
on first. The branch's pull request lists the parts and why the work was split.

### Testing on the QA branch

The QA branch is `beta` (or `deploy` where the project uses that name). Commit your work first, then:
`git fetch origin && git switch beta && git pull --ff-only && git merge --no-ff origin/develop &&
git merge --no-ff <your-branch> && git push origin beta`. Found a problem? Fix it on your branch and merge
again. Never branch from the QA branch or merge it into anything, and never edit `CHANGELOG.md` there.

**Rebuilding it** (when it still holds work whose pull request was closed unmerged): note
`git rev-parse origin/beta` as `<old>`; `git worktree add --detach .claude/worktrees/qa-rebuild
origin/develop`; in that worktree run `git merge --no-ff origin/<branch>` for each branch with an open pull
request; then `git push --force-with-lease=beta:<old> origin HEAD:refs/heads/beta` and remove the worktree.
This is the only force push the workflow allows.

### Releasing to production

1. **Release notes** (the maintainer): from an up-to-date `develop`, cut `changelog/YYYY-MM-DD`, add a
   bullet to `CHANGELOG.md` for everything merged since the last release under `## [YYYY-MM-DD]` (what
   changed, why, and the issue number: "Export file names include the date, so exports from different days
   don't overwrite each other (#5)"), and open a pull request into `develop`. With Claude Code,
   `/update-changelog` does all of this. Merge it.
2. Open a pull request from `develop` into `main` titled exactly `[ production deploy ]` and merge it with a
   merge commit. Don't merge `main` back into `develop`; the extra merge commit on `main` is expected.

### Working with Claude Code

Claude follows this same workflow, with a few more limits: it asks before any git or GitHub command
that changes something, asks before creating or linking an issue, never merges into `develop` or `main`,
never opens a pull request into `main`, never edits `CHANGELOG.md` (only the maintainer's
`/update-changelog` does), and merges into the QA branch only when asked. A hook,
`.claude/hooks/git-guard.py`, blocks the commands this workflow never allows; the full rules are in
`.claude/rules/git-workflow.md`.
<!-- /init-project:contributing-workflow -->

## Checks before a pull request

```bash
for f in app.js bin/www routes/*.js models/models.js seed.js schedule.js; do node --check "$f"; done  # syntax of every JS file
```

- That is the only automated check: there are no lint, typecheck or test scripts yet.
- Trying the app by hand (`npm start`) needs a reachable MongoDB and Twilio credentials; see the README.

## QA in this project

The QA branch is `beta`. Nothing runs from it yet, so there is nothing to restart after merging into it.

## Code style

Conventions and accessibility rules are in [CLAUDE.md](CLAUDE.md) (Code conventions and accessibility, plus
`.claude/rules/`); they apply to changes made by hand too.
