---
name: update-changelog
description: Writes the release notes in CHANGELOG.md (Keep a Changelog, releases named by date) when the dev is getting ready for a production deploy. Switches to develop, pulls the latest, cuts a changelog/YYYY-MM-DD branch, writes a bullet for everything merged into develop since the last release (what changed and why, ending with the issue number, asking the dev whenever a reason isn't written down), puts it all under a dated release heading, and opens a pull request into develop. Only the dev runs it, with /update-changelog; feature and fix branches never touch CHANGELOG.md.
argument-hint: "[YYYY-MM-DD]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/changelog.py *)
---

<!-- init-project:skill:update-changelog v2 — managed by /init-project; re-sync replaces up to the end marker, so keep project facts in "This project" below -->
# Update the changelog

CHANGELOG.md tells people what changed in each release and why. The diff already records what changed; the reason
is the part that gets lost, so every bullet carries it, and a reason nobody gave never goes in, because a guess in a
changelog reads as fact later. The format is in [reference/format.md](reference/format.md); CLAUDE.md › Changelog
has the short version.

This is a release step the dev runs with `/update-changelog [YYYY-MM-DD]` (default: today) before a production
deploy. Running it is the dev's go-ahead for the git steps in sections 1 and 6, so they don't need asking again one
by one. Claude never runs it on its own, and never edits CHANGELOG.md anywhere else (a hook blocks it outside a
`changelog/` branch).

`CL` below stands for `python3 ${CLAUDE_SKILL_DIR}/scripts/changelog.py` (read-only unless told to write, and it
writes only files named CHANGELOG.md). It never fetches. `<dir>` is the main checkout; draft in the session
scratchpad (or `mktemp -d`), called `<scratch>`. `<repo>` is `<owner>/<name>` from
`git -C "<dir>" remote get-url origin`; every gh call names it with `-R <repo>` so it works from any folder.
`<date>` is the argument, or today.

## Ground rules

- CHANGELOG.md is the only file this skill changes. Everything else in the checkout, committed or not, stays exactly
  as it is: never stage, commit, stash, reset or discard anyone's other changes.
- Bullets are written only on `changelog/<date>`, cut from an up-to-date develop. Never on develop, production or
  the QA branch (`beta`/`deploy`): CHANGELOG.md reaches the QA branch only when develop is merged into it.
- Public repo (`gh repo view <repo> --json visibility`): bullets describe features, never data; no personal paths,
  emails, names, hostnames, IPs, account IDs, tokens, or personal, financial or health data.

## Called from /init-project

init-project passes the setup worktree (already on its branch), the setup issue `#N`, a scratch directory, whether
the repo is public, and the mode `backfill`: create CHANGELOG.md from history with
[reference/backfill.md](reference/backfill.md), and nothing else. Skip sections 1 and 6: draft only in the scratch
directory, list your decisions for init-project's plan card instead of asking them yourself (plain-text reason
questions still go out first), and let init-project apply, verify and commit.

## 1. Get onto the changelog branch

1. `<dir>` = the main checkout: `git -C "<start>" worktree list --porcelain`, first `worktree` line.
2. `git -C "<dir>" fetch origin`, then check before switching anything:
   - `git -C "<dir>" status --porcelain --untracked-files=no` not empty → stop. Name the files and ask the dev to
     commit or move them first. Never stash or discard them.
   - `git -C "<dir>" worktree list` shows `develop` checked out in another worktree → stop and say where.
3. Note the branch the checkout is on now, for the report. Then:
   `git -C "<dir>" switch develop && git -C "<dir>" pull --ff-only`, and
   `git -C "<dir>" switch --no-track -c changelog/<date> origin/develop`.
   If `changelog/<date>` already exists (a second run that day), ask "Continue on it (Recommended)" / "Stop".
   Continuing means `git switch changelog/<date>`, then `git merge --no-ff origin/develop` when develop has moved on.
4. `CL status "<dir>"` → `kind: changelog`. No CHANGELOG.md → [reference/backfill.md](reference/backfill.md)
   creates it from history; then continue with section 2.

## 2. What needs a bullet

- `cp "<dir>/CHANGELOG.md" "<scratch>/CHANGELOG.md"`.
- `CL gaps "<dir>"`: every merged PR, branch merge and direct commit on develop that no bullet mentions yet. This is
  what this run writes up. Changelog-only merges (earlier runs of this skill) are never listed.
- Read each one as [reference/backfill.md](reference/backfill.md) §2 says: the PR body and the issue it closes, merge
  logs, commit messages. Open a diff only when those don't say what happened.

Sort each item. **Notable** (behaviour, commands, config, env vars, ports, data or schema, dependencies, security,
docs people rely on) gets a bullet. **Noise** (formatting, typos, comment-only edits, refactors with no visible
effect) folds into a related bullet or is left out. Name what you left out on the card.

## 3. The reason: find it, or ask

Sources, best first: the dev's words in this conversation; the PR body; the issue; commit message bodies; a comment
the change itself adds. Note the source for the card. No written reason → ask with one AskUserQuestion (up to 4
questions; more items → another round before drafting): a header naming the change, "Why did you <the change,
plainly>?", at most two reasons the diff suggests, each labelled "Guess: …", and "No reason (state just the
change)". The dev's own words come through Other. No plausible guess → ask in plain text, numbered, and end the turn.
A picked guess is the dev's answer; a skipped one means the bullet states just the change.

## 4. Write the release

In `<scratch>/CHANGELOG.md`:
1. Bullets per [reference/format.md](reference/format.md) under `[Unreleased]`, in the right category, one change
   per bullet, the reason in the wording, the ref at the end (`(#<issue>)`, else `(#<pr>)`, else the short hash).
2. `CL releases "<dir>" --apply "<scratch>/CHANGELOG.md"`: bullets for work that already reached production move
   under the release it shipped in, and a release cut earlier whose deploy landed on a later day is re-dated. Each
   `move:` line says why. `unresolved:` refs stay put; mention them.
3. `CL cut "<scratch>/CHANGELOG.md" --date <date> --write`: everything still under `[Unreleased]` moves to
   `## [<date>]`. If the deploy happens on a later day, the next run re-dates it (step 2).
4. `CL normalize "<scratch>/CHANGELOG.md" --write` and `CL lint "<scratch>/CHANGELOG.md"`, which must say ok
   (explain any warning on the card).

A correction to something already released is a new bullet in this release, never an edit to the old one.

## 5. Show and ask

Card: `git diff --no-index "<dir>/CHANGELOG.md" "<scratch>/CHANGELOG.md"`, the items covered (PR or hash and title),
the source of each reason, what was left out and why, and any release moves. One AskUserQuestion, header
`Changelog`: "Commit, push and open the PR into develop (Recommended)" / "Commit only" / "Leave it uncommitted".

## 6. Apply

`cp "<scratch>/CHANGELOG.md" "<dir>/CHANGELOG.md"`, then, as chosen:
- `git -C "<dir>" commit -m "Update the changelog for <date>" -- CHANGELOG.md` (the pathspec commits CHANGELOG.md
  alone);
- `git -C "<dir>" push -u origin changelog/<date>`;
- `gh pr create -R <repo> --base develop --head changelog/<date> --title "Changelog for <date>"` with a body that
  lists the items covered (`#<pr>` or hash, title) and any reasons the dev skipped. An open PR from this branch
  already → `gh pr edit` its body instead.

## 7. Finish

Verify: `CL lint "<dir>/CHANGELOG.md"` is ok, `CL gaps "<dir>"` lists only the items the card left out, and
`CL releases "<dir>"` says `moves: 0`. Report in two or three lines: the PR link (or what is left uncommitted), the
bullets added, reasons the dev skipped, and "The checkout is on changelog/<date> (it was on <branch>)". Next for the
dev: merge the changelog PR, then open the `[ production deploy ]` PR. If you had to discover a project fact that
"This project" below lacks (for example that the first PRs were imports), propose adding it.
<!-- /init-project:skill:update-changelog -->

## This project

<!-- Filled in by /init-project. Facts this skill needs: the production and QA branch names; public or private; history notes (import PRs, refs that are PR numbers rather than issues); anything unusual about releases. Facts only; nothing sensitive in a public repo. -->
- Production branch: `master`. QA branch: `beta`. Integration branch: `develop`.
- Public repository: keep personal details, hosts and data out of entries.
- History: six direct commits to `master` (2016-11-10 to 2019-03-05), no PRs and no tags; each commit date counts as a deploy (the app ran on Heroku then).
- Open Dependabot PRs #2–#4 and #6–#9 date from 2021–22; refs in that range are PR numbers, not issues.
