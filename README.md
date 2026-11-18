# Evie

Evie is a small web app for groups of friends deciding where to go out. A group opens a vote over a date range, each
member votes yes or no on candidate events, one at a time, and everyone gets a text message when voting closes and when the
winning event is confirmed. Built in 2016 with Express, Handlebars, MongoDB and Twilio; it is no longer deployed.

## Getting it running locally

**Prerequisites**

- Node.js. The code predates current releases; on Node 24, install with `--ignore-scripts` (below).
- A MongoDB server. Mongoose 4.13 ships an old driver, so use MongoDB 5.0 or older.
- A Twilio account with a phone number that can send SMS. Signing up requires a texted verification code.

**Install**

```bash
npm ci --ignore-scripts   # plain `npm ci` fails building fsevents@1 (pulled in by nodemon@1) on recent Node
```

**Configure** with environment variables (there is no `.env` loader; export them in your shell):

| Variable | Used by | Purpose |
|---|---|---|
| `MONGODB_URI` | `app.js`, `seed.js` | MongoDB connection string |
| `ACCOUNT_SID`, `AUTH_TOKEN` | `routes/index.js` | Twilio credentials |
| `FROM_PHONE` | `routes/index.js` | The Twilio number texts are sent from |
| `PORT` | `bin/www` | HTTP port (default 3000) |

**Seed and run**

```bash
node seed.js   # writes the 40 events in events.json to MongoDB; stop it with Ctrl-C once it has logged them
npm start      # nodemon ./bin/www; the app answers on http://localhost:3000
```

Without `ACCOUNT_SID` or a reachable `MONGODB_URI` the server exits on startup. The SMS calls also need updating for
the installed Twilio library before verification codes can be sent (see the Gotchas in [CLAUDE.md](CLAUDE.md)).

**Checks:** there are no tests or linters; `node --check` on each JS file is the one check (see
[CONTRIBUTING.md](CONTRIBUTING.md)).

## Directory layout

```text
app.js              Express setup: views, sessions in MongoDB, Passport local login, route mounting
bin/www             starts the HTTP server on PORT (default 3000)
routes/auth.js      register, log in, log out
routes/index.js     SMS verification, groups, lists, voting, results and the text messages
models/models.js    Mongoose schemas: User, Group, List, Event, EventMaster
views/              Handlebars templates, wrapped by views/layout.hbs
public/             logo and stylesheets/style.css (on top of Bootstrap 3 from a CDN)
events.json         the event catalog (Philadelphia, summer 2016) that seed.js loads
seed.js             loads events.json into MongoDB
schedule.js         pinged the old hosted app's /listCheck to close expired votes (that host is gone)
```

## Working with Claude Code

This project is set up for [Claude Code](https://code.claude.com/docs). [CLAUDE.md](CLAUDE.md) holds the rules
Claude follows here; [CONTRIBUTING.md](CONTRIBUTING.md) describes the same workflow for people.

**Skills** (run with `/<name>`, or Claude runs them when they apply):
- `/update-changelog`: the dev runs it before a production deploy to write the release notes in CHANGELOG.md.
- `/update-readme`: checks this README against the code and fixes what drifted.
- `/update-claude-md`: keeps CLAUDE.md accurate; `/update-claude-md deep` audits it thoroughly.
- `/update-contributing`: keeps CONTRIBUTING.md in step with the workflow.

**Agents** (Claude runs them before opening a pull request):
- `code-reviewer`: reviews every branch for bugs, regressions and rule breaks.
- `security-auditor`: when a change touches login, sessions, user data, SMS or dependencies.
- `test-engineer`: when logic changes without tests (there is no test runner yet, so it proposes one).
- `docs-reviewer`: when behaviour, commands, config or environment variables change.
- `accessibility-auditor`, then `design-reviewer`: when views or styles change.
- `workstream-builder`: builds one sub-branch of a split-up change in its own worktree.

**Rules** in `.claude/rules/`, loaded with matching files:
- `express.md`: security headers, session cookies, login rate limits, error handling (`app.js`, `routes/`).
- `handlebars.md`: output escaping in `views/`.
- `accessibility.md`: labels, form errors, contrast, focus, target size and alt text (views and styles).
- `git-workflow.md`: the full git workflow, loaded in every session.

**Hooks:** a git guard blocks the git and gh commands the workflow never allows (merging into `develop` or
`master`, force pushes, discarding uncommitted work, editing CHANGELOG.md outside a release branch, …).
