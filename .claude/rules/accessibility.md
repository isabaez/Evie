---
paths:
  - "views/**/*.hbs"
  - "public/stylesheets/**/*.css"
---
# Accessibility

- Every form control has a `<label for>` matching its `id`; a `placeholder` is not a label. Hide a label visually
  with a visually hidden class, never `display: none`.
  Source: https://www.w3.org/WAI/tutorials/forms/labels/ (checked 2026-11-17)
- After a server-rendered form error, name the error in the page `<title>` and `<h1>`, list each error above the
  form with a link to its field, tie the message to the field with `aria-describedby`, and never signal it by
  colour alone.
  Source: https://www.w3.org/WAI/tutorials/forms/notifications/ (checked 2026-11-17)
- Text contrast at least 4.5:1 (3:1 for large text); keyboard focus always visible; pointer targets at least
  24×24 CSS px.
  Source: https://www.w3.org/WAI/WCAG22/quickref/ (1.4.3, 2.4.7, 2.5.8; checked 2026-11-17)
- Every `<img>` has `alt`: the event title for the event photo in `views/eventVote.hbs`, "Evie" for the logo
  (`public/evie.png`, on most views). An icon-only link (the `.fa-times-circle` delete link in `views/groups.hbs`)
  needs a text name such as `aria-label`.
  Source: https://www.w3.org/WAI/WCAG22/quickref/ (1.1.1; checked 2026-11-17)
