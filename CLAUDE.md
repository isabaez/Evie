# Evie — working agreements

Evie is a 2016 group event-planning app: friends form a group, open a "list" of candidate events for a date range,
vote yes or no on each, and get SMS updates. Express 4 renders Handlebars views; Passport local login; Mongoose 4 on
MongoDB; Twilio SMS. `npm start` serves it on **port 3000** (`PORT` overrides) and needs a reachable MongoDB and
Twilio credentials. README.md is the product doc: read the section for the area you are touching before changing it.

## Commands

```bash
for f in app.js bin/www routes/*.js models/models.js seed.js schedule.js; do node --check "$f"; done  # syntax only; needs nothing installed
npm start        # dev server on :3000 via nodemon; the dev runs it; needs MONGODB_URI, ACCOUNT_SID, AUTH_TOKEN, FROM_PHONE
node seed.js     # loads events.json into MongoDB (EventMaster); the dev runs it; stays connected, stop it with Ctrl-C
```

- No lint, typecheck, test or build scripts exist.
- On Node 24, `npm ci` fails compiling `fsevents@1` (pulled in by `nodemon@1`); `npm ci --ignore-scripts` installs.
- `node schedule.js` requests `/listCheck` on the old Heroku URL, which no longer exists.

<!-- init-project:git-workflow v3 — managed by /init-project; re-sync replaces everything up to the end marker, so put project notes below it -->
## Git workflow

The full rules are in `.claude/rules/git-workflow.md`, which loads in every session; CONTRIBUTING.md describes the
same workflow for people. A hook (`.claude/hooks/git-guard.py`) blocks the commands the workflow never allows.

| Branch | Holds | Rules for Claude |
|---|---|---|
| `main` (or `master`) | Production | Never branch from it, open a PR into it, merge into it or push to it. The dev deploys by merging `develop` in a PR titled exactly `[ production deploy ]`. |
| `develop` | Reviewed work waiting for production; the base for all work | Cut every branch from an up-to-date `origin/develop` and open every PR into it. Never merge into it, commit on it or push to it. |
| `beta` (or `deploy`) | Features in review, merged together for QA | Merge a branch into it only when the dev asks. Never branch from it, merge it anywhere, or open a PR from or into it. |

- **Ask first:** show the exact command and wait for the dev's yes before any git or gh command that changes
  something (commit, push, pull, merge, switch, branches, worktrees, issues, PRs). Read-only commands run freely.
- **Issues:** every feature and fix has one; always ask before creating an issue or linking work to one.
- **Branches:** `feature/<issue>-<short-description>` or `fix/<issue>-<short-description>` from `origin/develop`;
  sub-branches `<branch>--<part>`. Catch up by merging `origin/develop` in; never rebase or force-push pushed work.
- **Pull requests:** into `develop`, body starting `Closes #<issue>`; run the project agents first. No changelog
  bullet: the dev writes the release notes with `/update-changelog`. The dev reviews and merges.
- **Always:** never stash, discard or reset uncommitted work; delete a branch only when the dev approves; never
  commit secrets; in a public repo keep personal and sensitive data out of files, commits, issues and PRs.
<!-- /init-project:git-workflow -->

### Branches in this project

- Production `master`, integration `develop` (the default branch), QA `beta`. All three started from the same 2019
  commit when the Claude Code setup created `develop` and `beta`.
- Nothing is deployed from any branch, so nothing restarts after a merge into `beta`.
- Before the setup, all history (2016-11 to 2019-03) was direct commits to `master`.

<!-- init-project:changelog v2 — managed by /init-project; re-sync replaces everything up to the end marker, so put project notes below it -->
## Changelog

`CHANGELOG.md` follows Keep a Changelog: `## [Unreleased]`, then releases `## [YYYY-MM-DD]` (the day the
`[ production deploy ]` merge reached production), newest first, each with `### Added`, `### Changed`, `### Removed`,
`### Fixed`, `### Security` in that order, only the ones that have bullets.
- **Only the dev writes it**, with `/update-changelog` before a production deploy: it cuts `changelog/<date>` from
  an up-to-date develop, writes a bullet for everything merged since the last release under `## [<date>]`, and opens
  a PR into develop. Claude never edits CHANGELOG.md or runs that skill on its own, and pull requests need no
  bullet. A hook blocks edits and commits of CHANGELOG.md outside a `changelog/` branch, so it is never changed on a
  feature branch, develop, production or the QA branch.
- One user-visible change per bullet, the reason in the wording, the issue at the end: "Export file names include
  the date, so exports from different days don't overwrite each other (#5)". Never invent a reason: ask the dev, and
  if there is none, state just the change. A correction to a release is a new bullet in the next one.
- Check it with `python3 .claude/skills/update-changelog/scripts/changelog.py lint CHANGELOG.md` from the repo root
  (`normalize --write` tidies it).
<!-- /init-project:changelog -->

## Architecture

- `bin/www` starts the HTTP server. `app.js` sets up hbs views, body parsers, static `public/`, a MongoDB-backed
  session (`connect-mongo`) and Passport's local strategy, then mounts `routes/auth.js` and `routes/index.js` on `/`.
- `routes/auth.js`: `/register`, `/login`, `/logout`. Registration saves an unverified user and redirects to
  `/verify/:id`, which texts a 4-digit code.
- `routes/index.js`: `/listCheck` and `/verify/:id` are public; then `router.use(...)` is the auth wall (signed in and
  `verified`); then groups (`/groups`, `/groups/:gid`), list creation (`POST /groups/:gid`), voting (`/eventLoad/:lid`,
  `/loadSession/:lid`, `/eventVote/:eid`), results (`/results/:lid`, `/actNow/:lid`) and `/message/:lid`,
  `/confirm/:eid`, `/deleteGroup/:gid`.
- Data (`models/models.js`): `User` → `Group` (users, lists) → `List` (one vote over a date range; status `Open`,
  `Closed` or `Complete`; `timeLimit`) → `Event` (one candidate; `tally` = ids of users who voted yes) → `EventMaster`
  (the event catalog, seeded from `events.json`).
- Voting progress lives in the session: `req.session.votes` holds each list's remaining event ids; each vote pops one.
- Views: `views/*.hbs` inside `views/layout.hbs`; `public/stylesheets/style.css` on top of Bootstrap 3.3.6 from a CDN.

## Recipes

### Add a page
1. Add the route in `routes/index.js` below the `router.use(...)` auth wall (above it only if it must be public).
2. Add `views/<name>.hbs`; it renders inside `views/layout.hbs`.
3. Pass data as `res.render`'s second argument and print it with `{{ }}`.
4. Link to it from an existing view such as `views/groups.hbs` or `views/singleGroup.hbs`.

### Add a field to a model
1. Declare it in the schema in `models/models.js`: Mongoose drops undeclared fields (`Group` has no `searchLocation`,
   so the value `POST /groups` sets is lost).
2. Set it where the document is created in `routes/index.js` or `routes/auth.js`.
3. Show it in the view that renders that document.

### Change a design element
1. Shared styles live in `public/stylesheets/style.css`; there are no tokens or CSS variables.
2. Bootstrap 3 classes do the layout; the only breakpoint is `@media only screen and (max-width: 500px)`.
3. CDN assets (Bootstrap, jQuery, Font Awesome) are all in `views/layout.hbs`.

<!-- init-project:conventions v1 — managed by /init-project; re-sync replaces everything up to the end marker, so put project notes below it -->
## Code conventions and accessibility

These apply to new and changed code; existing code is brought in line through its refactor issue, not in passing.
Stack-specific practice from the official docs is in `.claude/rules/`, which loads with the files it covers.
- **Names:** descriptive, not verbose. No single-letter names, loop counters and callback parameters included
  (`index`, `event`, `error`).
- **CSS:** BEM with descriptive block names (`savings-card__total--negative`); never style by id. Style state through
  its semantic attribute when one exists (`[aria-expanded="true"]`, `[aria-current]`, `:disabled`), else a modifier.
- **JS hooks:** prefer the framework's refs. When a script has to find an element, use a `js-` prefixed class
  (`js-period-toggle`) that is never styled; never hook onto a styling class.
- **Accessibility (WCAG 2.2 AA):** native elements first; everything works by keyboard alone, in a logical order,
  with a visible focus indicator and no traps; every control has an accessible name; text contrast 4.5:1 (3:1 for
  large text and UI parts); colour is never the only signal; respect `prefers-reduced-motion`; targets ≥ 24×24 px.
- **Legibility:** body text 16px or more, set in `rem`; line-height 1.5 or more; lines of about 80 characters at
  most; layouts survive 200% zoom and a 320px-wide viewport.
- **Helpers:** reuse the project's accessibility helpers (listed below). When a pattern repeats (visually hidden
  text, skip link, focus management, live announcements), add a helper instead of a one-off.
<!-- /init-project:conventions -->

### Conventions in this project

- CommonJS `require`, `var` and Node-style callbacks (`function (err, doc)`) everywhere; no promises or async/await.
- Handlers mostly `console.log(err)` and send nothing on error, so the request hangs. New code responds or calls
  `next(err)`.
- Rules files: `.claude/rules/express.md` (app setup and routes), `.claude/rules/handlebars.md` (views).

### Accessibility in this project

- No helpers exist: no visually hidden class, skip link, focus-visible styles, reduced-motion rule or live region.
- Form fields use `placeholder` with no `<label>` (`views/login.hbs`, `views/register.hbs`). No contrast check exists.
- Rules file: `.claude/rules/accessibility.md` (views and styles).

<!-- init-project:agents v2 — managed by /init-project; re-sync replaces everything up to the end marker, so put project notes below it -->
## Agents

Project agents live in `.claude/agents/`. Before opening or updating a PR, run the ones this project has that apply,
giving each the absolute path of the checkout or worktree. `test-engineer` goes first, alone; then the rest in one
message, except `design-reviewer`, which starts after `accessibility-auditor` returns (they share the browser).
- `test-engineer`: logic changed without matching tests. `code-reviewer`: always.
- `security-auditor`: the diff touches an area its "This project" section lists, or adds dependencies, endpoints,
  file or network access, or secret handling.
- `accessibility-auditor`, then `design-reviewer`: UI files changed.
- `docs-reviewer`: behaviour, commands, config, env vars or ports changed; it also checks CONTRIBUTING.md, the README's
  Claude section, that the PR body gives the reason and that CHANGELOG.md is untouched. `workstream-builder`: one
  sub-branch, in a worktree Claude made.
Fix each finding or list it as deferred in the PR body. Prefer these agents over the built-in `/code-review` and
`/security-review`: they know this project.
<!-- /init-project:agents -->

## Deployment

- Not deployed. It ran on Heroku in 2016; `schedule.js` still points at that app, which is gone.
- No Procfile, Dockerfile or CI deploy exists.

## Gotchas

- **SMS is broken.** The 2019 "npm install" commit moved `twilio` from ^2.9 to ^3.29, but `routes/index.js` still
  calls the v2 `twilio.sendMessage`, which v3 doesn't have. Every SMS path (`/verify/:id`, `/listCheck`,
  `/message/:lid`, `/confirm/:eid`) throws a TypeError.
- **Startup needs live services.** `routes/index.js` builds the Twilio client when it loads ("username is required"
  without `ACCOUNT_SID`), and Mongoose 4 crashes the process when the first connection to `MONGODB_URI` fails.
- **Mongoose 4.13 bundles the 2.2 MongoDB driver**, which needs an old server (MongoDB 5.0 or older); not tested here.
- **Passwords are plain text**: stored by `routes/auth.js`, compared in the `app.js` local strategy. The session
  secret is the literal `"secret"` in `app.js`.
- **GET routes change data with no ownership check**: `/deleteGroup/:gid`, `/message/:lid` and `/confirm/:eid` act
  on any id for any signed-in user.
- **`.gitignore` ignores a file named `process.env`**, the old local env file; there is no `.env.example`.
- `events.json` holds 40 Philadelphia events from summer 2016 (5 per type). List creation filters by date, except
  `nightlife` and `historic`, which are always added.
