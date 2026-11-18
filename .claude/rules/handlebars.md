---
paths:
  - "views/**/*.hbs"
---
# Handlebars views

- Print values with `{{value}}`, which HTML-escapes them. Use the triple-stash `{{{ }}}` only for trusted HTML; the
  one legitimate use here is `{{{body}}}` in `views/layout.hbs`.
  Source: https://handlebarsjs.com/guide/expressions.html#html-escaping (checked 2026-11-17)
- A helper that returns `Handlebars.SafeString` must escape every argument with `Handlebars.escapeExpression` first.
  Source: https://handlebarsjs.com/guide/expressions.html#html-escaping (checked 2026-11-17)
