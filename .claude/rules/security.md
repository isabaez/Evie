<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file, so put project notes in CLAUDE.md -->
# Security

These rules load in every session. The security baseline (Dependabot, the Security workflow, SECURITY.md in a
public repo) was set up by `/init-project`.

- **Dependabot PRs** go into `develop`: weekly version updates (minor and patch bundled, nothing newer than 7
  days) and security updates as soon as they're found. The dev reviews and merges them; never merge, close or
  dismiss one without asking.
- **Never weaken a check.** Don't disable, skip or `continue-on-error` the Security workflow, Dependabot or
  CodeQL, and don't add an ignore entry (`.gitleaksignore`, `osv-scanner.toml`, `.trivyignore`, a
  `zizmor: ignore` comment) or lower a severity without asking the dev and saying why.
- **Workflows**: least-privilege `permissions:` (`contents: read` unless a job needs more, set per job); third-party
  actions pinned to a full commit SHA with a `# vX.Y.Z` comment; `persist-credentials: false` on checkout;
  `${{ … }}` values from events reach `run:` only through `env:`; no `pull_request_target`.
- **Secrets**: never commit them (`.env` files, keys, `credentials*.json`, tokens in `.npmrc` or `.pypirc`); read
  them from the environment and never print them. A leaked secret gets revoked and rotated, not just deleted.
- **Private apps** require a login on every page and API route, and send `X-Robots-Tag: noindex` (or the
  `robots` meta tag) so nothing gets indexed.
- **Containers** run as a non-root `USER` and publish ports on `127.0.0.1` (`"127.0.0.1:8080:8080"`), never on
  every interface; a reverse proxy or tunnel is the way in.
- **New dependencies**: well-maintained packages only, and no version published in the last 7 days.
