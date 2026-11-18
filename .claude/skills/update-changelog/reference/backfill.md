<!-- init-project-file v2 — managed by /init-project; re-sync replaces this file -->
# Backfill: create CHANGELOG.md from the project's history

For a project with no CHANGELOG.md. The result lists what shipped in each production release, and what is merged
but not yet released, with reasons wherever someone wrote them down. `CL` is
`python3 ${CLAUDE_SKILL_DIR}/scripts/changelog.py`; run `git -C "<dir>" fetch origin` first.

## 1. The history

`CL history "<dir>" --json` gives:
- `deploys`: every state of the production branch (main or master), oldest first, with its date;
- `items`: the merged work on develop, oldest first: merged PRs (`pr`, `branch`, `issue`, `title`), merges of other
  branches, and direct commits, each with `shipped_in` (the date of the first deploy that contained it) or null;
- `releases`: item hashes grouped by release date, plus `Unreleased`.
Merges that only sync permanent branches are already expanded, and empty, scaffold-only and changelog-only commits
are already dropped. No develop → stop and say so: the project needs its branches first (/init-project Step 1).

## 2. Read each item (read-only)

- A merged PR `pr=#P`: `gh pr view P -R <repo> --json title,body,closingIssuesReferences,files`, and
  `gh issue view <n> -R <repo> --json title,body` for the issue it closes (or the one its branch names).
- A merge without a PR: `git -C "<dir>" log --format='%h %s%n%b' <sha>^1..<sha>^2`.
- A direct commit: `git -C "<dir>" show --stat --format='%s%n%n%b' <sha>`.
- Open a diff only when the titles don't say what happened: `git -C "<dir>" show <sha> -- <path>`.

## 3. Draft the bullets

- Per item, one to three bullets in the right categories, per [format.md](format.md). An import or "V1" PR, or the
  project's first real build, gets a short `### Added` summary of what the project does (three to six bullets, from
  its PR body, the README, or the files it added). Its reason is the project's purpose as the README states it, when
  it states one; that isn't a missing reason.
- Consecutive direct commits on the same topic become one bullet with all their hashes as refs.
- Noise commits (typos, formatting, README touch-ups) fold into a related bullet or are left out; list them on the
  card.
- Refs: `(#<issue>)` when the branch or PR names one, else `(#<pr>)`, else the short hash(es).
- Each bullet goes under the release in `shipped_in`, or `[Unreleased]` when it's null.
- More than about 20 items: split them by release into up to 5 slices and launch that many Explore agents in one
  message. Each gets the directory, its items, this file and format.md, and returns drafted bullets plus its list of
  items with no written reason. Merge their drafts yourself.

## 4. Reasons

Take each reason from the PR body, the issue, or commit message bodies. Collect every item whose reason isn't
written anywhere and ask once, in plain text, before showing the draft, then end the turn:

> Backfilling the changelog. I couldn't find why these were done:
> 1. 2026-08-14 · Chime on completion (#4): plays a sound when a chore is marked done.
> Reply with the reasons by number; "skip" leaves that bullet stating just the change.

Use the dev's words, tightened. Never fill in a plausible reason yourself.

## 5. Write and check

`<scratch>/CHANGELOG.md`: the intro from format.md, `## [Unreleased]` (work merged into develop but not deployed
yet; the dev's next `/update-changelog` cuts it into a release), then the releases, newest first. Then:
- `CL normalize "<scratch>/CHANGELOG.md" --write`, then `CL lint "<scratch>/CHANGELOG.md"` → ok.
- Coverage: once the file is in the checkout, `CL gaps "<dir>" --all` lists only the items you deliberately left out.
  Name them on the card.
- Public repo: describe features, never data (see update-readme's `reference/sensitive.md` for the count-only scan).
