#!/usr/bin/env python3
# init-project-file v1 — managed by /init-project; re-sync replaces this file
"""Check that every in-page link `](#anchor)` in a Markdown file points at a heading (GitHub slug rules).

  check_anchors.py FILE     prints "anchors ok" (exit 0) or "broken: a, b" (exit 1)
"""
import re
import sys


def slugs(text):
    text = re.sub(r"`{3}.*?`{3}", "", text, flags=re.S)
    seen, out = {}, set()
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        out.add(slug if count == 0 else "%s-%d" % (slug, count))
    return out, text


def main(path):
    with open(path, encoding="utf-8") as handle:
        known, body = slugs(handle.read())
    broken = sorted({anchor for anchor in re.findall(r"\]\(#([^)]+)\)", body) if anchor not in known})
    if broken:
        print("broken: " + ", ".join(broken))
        return 1
    print("anchors ok")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) == 2 else 2)
    sys.exit(main(sys.argv[1]))
