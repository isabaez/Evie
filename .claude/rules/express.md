---
paths:
  - "app.js"
  - "bin/www"
  - "routes/**/*.js"
---
# Express

This app is on Express 4; the official docs now describe 5.x. Rules below hold for both unless noted.

- Disable the `X-Powered-By` header (`app.disable('x-powered-by')`) and set security headers with Helmet.
  Source: https://expressjs.com/en/advanced/best-practice-security.html (checked 2026-11-17)
- Give the session cookie a generic `name`, and set `secure`, `httpOnly` and an expiry; take the session secret from
  an environment variable, never a literal.
  Source: https://expressjs.com/en/advanced/best-practice-security.html (checked 2026-11-17)
- Rate-limit `POST /login` (failed attempts per username and IP, and per IP per day).
  Source: https://expressjs.com/en/advanced/best-practice-security.html (checked 2026-11-17)
- Never pass a user-supplied URL to `res.redirect` without checking it is a local path.
  Source: https://expressjs.com/en/advanced/best-practice-security.html (checked 2026-11-17)
- Every handler ends the request: on error, respond or call `next(err)`. Express 4 does not catch rejected promises;
  wrap async work in try/catch and call `next(err)` yourself.
  Source: https://expressjs.com/en/advanced/best-practice-performance.html (checked 2026-11-17)
- Don't listen for `uncaughtException`; let the process crash and a supervisor restart it. Run with
  `NODE_ENV=production` in production.
  Source: https://expressjs.com/en/advanced/best-practice-performance.html (checked 2026-11-17)
