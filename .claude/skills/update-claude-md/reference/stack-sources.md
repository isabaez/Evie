<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file -->
# Official sources for best practices

Fetch these with WebFetch (official documentation only; no blogs or tutorials), then keep only the rules that apply
to this project's code. These are starting points: a deeper page on the same official site (Svelte's runes page,
the APG's disclosure pattern) usually holds the rules, and is preferred. Cite the page and the date you checked it
next to each rule. A stack not listed: find its official documentation site first
(`WebSearch "<tool> official documentation"`) and use only that.

| Topic | Pages |
|---|---|
| Accessibility | https://www.w3.org/TR/WCAG22/ · https://www.w3.org/WAI/WCAG22/quickref/ · https://www.w3.org/WAI/ARIA/apg/patterns/ |
| HTML, CSS, JavaScript | https://developer.mozilla.org/en-US/docs/Web/Accessibility · https://developer.mozilla.org/en-US/docs/Web/CSS · https://developer.mozilla.org/en-US/docs/Web/JavaScript |
| BEM | https://getbem.com/naming/ · https://en.bem.info/methodology/naming-convention/ |
| React | https://react.dev/reference/rules · https://react.dev/learn/you-might-not-need-an-effect |
| Svelte and SvelteKit | https://svelte.dev/docs/svelte/overview · https://svelte.dev/docs/kit/introduction |
| Vite | https://vite.dev/guide/ · https://vite.dev/guide/features.html#css-modules · https://vite.dev/config/shared-options.html#css-modules |
| Vitest | https://vitest.dev/guide/ |
| TypeScript | https://www.typescriptlang.org/docs/handbook/intro.html · https://www.typescriptlang.org/tsconfig/ |
| Hono | https://hono.dev/docs/guides/best-practices |
| Drizzle ORM | https://orm.drizzle.team/docs/overview |
| Node.js | https://nodejs.org/en/learn |
| Python | https://peps.python.org/pep-0008/ · https://docs.python.org/3/library/ |
| Flask | https://flask.palletsprojects.com/en/stable/ · https://flask.palletsprojects.com/en/stable/web-security/ |
| SQLite | https://www.sqlite.org/docs.html · https://docs.python.org/3/library/sqlite3.html |
| Docker | https://docs.docker.com/build/building/best-practices/ · https://docs.docker.com/compose/ |

What to look for: naming and structure rules, the framework's own guidance on state and effects, security notes
(escaping, CSRF, secrets), accessibility patterns for the components this project has, and anything the code already
gets wrong often. Skip generic advice the project doesn't need.
