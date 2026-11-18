<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file -->
# A README for a project with no code yet

## 1. Ask what it's for (plain text, then end the turn)

No AskUserQuestion here. Send one short message and stop:

> What is `<name>` for? Who will use it, and what should it do first?

## 2. Follow-ups (one AskUserQuestion)

| Header | Question | Options |
|---|---|---|
| `Stack` | Planned stack | the stack the dev named or implied (Recommended) / "Undecided"; none named → one or two stacks that fit / "Undecided (Recommended)" · Other = type it |
| `Runs on` | Where it runs | e.g. "This Mac only" / "A home server or Raspberry Pi" / "Hosted on the web" · Other |
| `License` | License (public repos only) | "No license for now" / "MIT" · Other = another SPDX id |

## 3. Draft

```markdown
# <Project name>

<One or two sentences: what it is for, who uses it, what it does first. The dev's words, tightened.>

**Status:** not started. **Planned stack:** <only if given>. **Runs on:** <only if given>.

## Getting it running

Nothing to run yet; this section fills in with the first code.

## Directory layout

Nothing here yet beyond the project's docs and Claude Code setup (`.claude/`).

## Working with Claude Code

<per sections.md, from what is installed>
```

- No invented commands: install and usage sections wait for the code.
- No badges, emojis or marketing lines. Drop a "Planned stack" or "Runs on" line with no answer.
- Public repo: no personal names, paths, hostnames or emails.
- License chosen → `gh api licenses/<spdx-id-lowercase> -q .body > "<scratch>/LICENSE"`, fill `[year]` and
  `[fullname]` (the GitHub owner unless the dev gives a name), and show it on the card.
- Offer to set the GitHub description to a one-line summary (350 characters at most; nothing sensitive in a public
  repo): `gh repo edit <owner>/<repo> --description "<line>"`, only if the dev says yes.
