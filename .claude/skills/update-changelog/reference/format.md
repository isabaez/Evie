<!-- init-project-file v2 — managed by /init-project; re-sync replaces this file -->
# CHANGELOG.md format

Based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), with releases named by the date they reached
production. `scripts/changelog.py lint` checks everything below that a script can check.

## Shape

```markdown
# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); releases are named by the date they reached production,
and each entry says why the change was made.

## [Unreleased]

### Added

- Shopping-list export writes a CSV of every item marked low, so the list can be pasted into the shared notes (#5)

### Fixed

- Expiring items are compared against the local date, so late-evening checks no longer list tomorrow's items (#8)

## [2026-09-20]

### Changed

- Export files use semicolons between columns, so Numbers opens them as columns in regions that use a decimal comma (#6)
```

- `# Changelog`, then the intro paragraph (keep the project's own wording if it has one).
- `## [Unreleased]` always exists and comes first, even when empty.
- Releases: `## [YYYY-MM-DD]`, the date of the `[ production deploy ]` merge (the production branch's commit date),
  newest first. Two deploys on the same day share one heading.
- Categories, in this order, only those with bullets: `### Added` (new features), `### Changed` (changes to existing
  behaviour), `### Removed` (features taken out), `### Fixed` (bug fixes), `### Security` (vulnerabilities fixed,
  hardening, secrets handling). `### Deprecated` is accepted from older files but not written.
- No text directly under a version heading, and no empty categories or releases.

## Bullets

- **One user-visible change per bullet**, written for someone using or working on the project, not a commit
  message. Start with the thing that changed, in the present tense: "Export file names include the date …", not
  "Added date to export".
- **The reason is part of the sentence** ("…, so exports from different days don't overwrite each other"). Take it
  from something written down or from the dev; if there is none, state just the change. Never guess.
- **Refs at the end:** `(#<issue>)` for work that had an issue (from `feature/<issue>-…` or `fix/<issue>-…`),
  `(#<pr>)` for a merged PR without one, a short commit hash for a direct commit: `(1a2b3c4)`. Several refs are
  comma-separated: `(#12, #13)`. The refs are how later runs match bullets to merged work: `gaps` skips work a
  bullet already names, and `releases` moves a bullet when its work ships.
- **Breaking changes** start with `**Breaking:**` and say what someone must do.
- Name commands, settings, env vars and pages as they appear in the code (`npm run seed`, `PORT`), in backticks.
- Several related changes from one branch may be several bullets, in their own categories, all ending with the same
  ref.

## What doesn't get a bullet

Formatting, typos, comment-only edits, refactors and test-only changes with no visible effect, CI tweaks, and
changelog-only commits. Fold a small related fix into the bullet it belongs with instead of listing it alone.

## Who writes it, and when

- Only the dev's `/update-changelog`, before a production deploy, on a `changelog/YYYY-MM-DD` branch cut from an
  up-to-date develop. It writes a bullet for everything merged into develop that no bullet names yet, puts it all
  under `## [YYYY-MM-DD]`, and opens a pull request into develop; the dev merges it, then `[ production deploy ]`.
- Feature, fix and sub-branches never change CHANGELOG.md, and it is never edited on develop, production or the QA
  branch.
- `changelog.py releases` compares each bullet's refs with what reached the production branch: shipped bullets move
  under their deploy's date, a release cut whose deploy happened a day later is re-dated, and a cut still waiting
  for its deploy is left alone.
- `[Unreleased]` stays as the first heading and is normally empty; a backfill leaves work that is merged but not
  deployed there, and the next run cuts it.
- `.gitattributes` sets `CHANGELOG.md merge=union`, so a local merge keeps both sides' lines. After any merge that
  touches it, `changelog.py normalize --write` tidies the structure and `lint` finds what it can't fix.
