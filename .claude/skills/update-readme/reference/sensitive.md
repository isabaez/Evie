<!-- init-project-file v1 — managed by /init-project; re-sync replaces this file -->
# Sensitive information (public repos)

A public repo publishes every file, commit message, issue and PR. Before anything goes into one, scan it, counting
only: `grep -cE` or `grep -lE`, never printing or quoting a value. Locate a hit by line number
(`grep -nE '<pattern>' <file> | cut -d: -f1`) and view it masked:
`sed -n '<n>p' <file> | perl -pe 's#(?:<pattern>).*#[REDACTED]#'`. Run the token and key-format patterns before
reading a file, and read a file with such a hit only in ranges that skip that line.

| Kind | Pattern (extended regex) | Skip |
|---|---|---|
| Emails | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | `example.com`, `noreply` |
| Personal paths | `/Users/[^/ ]+\|/home/[^/ ]+\|C:\\Users\\` | |
| IP addresses | `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` | `127.0.0.1`, `0.0.0.0` |
| Hostnames | `\.(local\|lan\|home\|internal)([^A-Za-z0-9._-]\|$)`, and this machine's `hostname -s` as a whole word (`grep -cw`) when it is 4 characters or longer | |
| Tokens, account IDs | `(token\|secret\|password\|api[_-]?key\|account[_-]?id)["']?[[:space:]]*[:=]` | |
| Key formats | `AKIA[0-9A-Z]{16}\|gh[pousr]_[A-Za-z0-9]{20,}\|sk-[A-Za-z0-9_-]{20,}\|BEGIN [A-Z ]*PRIVATE KEY` | |

Also read for personal, financial or health data that no pattern catches: real-looking names, amounts, balances,
account numbers, birth dates, symptom or medication rows, in examples, sample files and image alt text.

Report rows as `file:line | kind | count | proposed fix`, and describe the fix ("replace with `you@example.com`"),
never the value. A first name the project's own docs already use for its maintainer is fine.

Scan what the project wrote, not the managed files /init-project installs (`.claude/skills/`, `.claude/agents/`,
`.claude/hooks/`): their text is checked when the templates change, and it names these patterns on purpose. The Skip
column applies to every scan: drop those matches before counting.
