#!/usr/bin/env python3
# init-project-file v1 — managed by /init-project; re-sync replaces this file
"""Read-only check of the /init-project managed blocks in a Markdown file (CLAUDE.md, CONTRIBUTING.md).

  blocks.py list FILE                      id, version and status of every managed block
  blocks.py check FILE --against OTHER     every block in OTHER is in FILE and unchanged (exit 1 if not)
  blocks.py check FILE --against-ref REF   the same, against FILE as committed at REF (e.g. HEAD)

A managed block runs from a start marker line to its end marker line; marker-shaped lines inside fenced code are
examples, not markers. The project's own text outside blocks is never compared.
"""
import os
import re
import subprocess
import sys

START_RE = re.compile(r"^<!--\s*init-project:(?P<id>[a-z0-9:-]+)\s+v(?P<ver>\d+)\b.*-->\s*$")
END_RE = re.compile(r"^<!--\s*/init-project:(?P<id>[a-z0-9:-]+)\s*-->\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def fence_mask(lines):
    mask, fence = [False] * len(lines), None
    for index, line in enumerate(lines):
        match = FENCE_RE.match(line)
        if fence is not None:
            mask[index] = True
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) \
                    and not match.group(2).strip():
                fence = None
            continue
        if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = match.group(1)
            mask[index] = True
    return mask


def parse(lines):
    """{id: {"version", "start", "end", "status", "lines"}}; status ok | unterminated | duplicate | orphan-end | nested."""
    blocks, open_blocks, found = [], {}, []
    fenced = fence_mask(lines)
    for index, line in enumerate(lines):
        if fenced[index]:
            continue
        start = START_RE.match(line)
        if start:
            block_id = start.group("id")
            if block_id in open_blocks:
                open_blocks.pop(block_id)["status"] = "unterminated"
            block = {"id": block_id, "version": int(start.group("ver")), "start": index, "end": None, "status": "ok"}
            blocks.append(block)
            open_blocks[block_id] = block
            continue
        end = END_RE.match(line)
        if end:
            block_id = end.group("id")
            if block_id in open_blocks:
                open_blocks.pop(block_id)["end"] = index
            else:
                blocks.append({"id": block_id, "version": None, "start": index, "end": index, "status": "orphan-end"})
    for block in open_blocks.values():
        block["status"] = "unterminated"
    complete = [b for b in blocks if b["status"] == "ok"]
    for first in complete:
        for second in complete:
            if first is not second and first["start"] < second["start"] <= first["end"]:
                first["status"] = second["status"] = "nested"
    counts = {}
    for block in blocks:
        if block["status"] == "ok":
            counts[block["id"]] = counts.get(block["id"], 0) + 1
    for block in blocks:
        if block["status"] == "ok" and counts[block["id"]] > 1:
            block["status"] = "duplicate"
        if block["status"] == "ok":
            block["lines"] = [l.rstrip() for l in lines[block["start"]:block["end"] + 1]]
        found.append(block)
    return found


def read_lines(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()


def cmd_list(path):
    for block in parse(read_lines(path)):
        version = "v%d" % block["version"] if block["version"] is not None else "v?"
        print("%s\t%s\t%s" % (block["id"], version, block["status"]))
    return 0


def cmd_check(path, other_lines, label):
    mine = {b["id"]: b for b in parse(read_lines(path)) if b["status"] == "ok"}
    problems = [b for b in parse(read_lines(path)) if b["status"] != "ok"]
    failed = False
    for block in problems:
        print("broken: %s (%s) in %s" % (block["id"], block["status"], path))
        failed = True
    for block in parse(other_lines):
        if block["status"] != "ok":
            continue
        current = mine.get(block["id"])
        if current is None:
            print("missing: %s (in %s)" % (block["id"], label))
            failed = True
        elif current["lines"] != block["lines"]:
            print("changed: %s differs from %s" % (block["id"], label))
            failed = True
        else:
            print("same: %s v%d" % (block["id"], block["version"]))
    print("blocks: %s" % ("changed" if failed else "unchanged"))
    return 1 if failed else 0


def main(argv):
    if len(argv) == 2 and argv[0] == "list":
        return cmd_list(argv[1])
    if len(argv) == 4 and argv[0] == "check" and argv[2] == "--against":
        if not os.path.isfile(argv[3]):
            print("no %s: nothing to compare (a new file)" % argv[3])
            return 0
        return cmd_check(argv[1], read_lines(argv[3]), argv[3])
    if len(argv) == 4 and argv[0] == "check" and argv[2] == "--against-ref":
        path = os.path.abspath(argv[1])
        top = subprocess.run(["git", "-C", os.path.dirname(path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True).stdout.strip()
        rel = os.path.relpath(path, top)
        shown = subprocess.run(["git", "-C", top, "show", "%s:%s" % (argv[3], rel)], capture_output=True, text=True)
        if shown.returncode != 0:
            print("no %s at %s: nothing to compare" % (rel, argv[3]))
            return 0
        return cmd_check(path, shown.stdout.splitlines(), "%s:%s" % (argv[3], rel))
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
