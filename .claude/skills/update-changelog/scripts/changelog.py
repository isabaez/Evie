#!/usr/bin/env python3
# init-project-file v2 — managed by /init-project; re-sync replaces this file
"""CHANGELOG.md helper for the update-changelog skill: Keep a Changelog, releases named by date.

Read-only, except that `normalize --write`, `releases --apply FILE` and `cut --write` write one file,
and only a file named CHANGELOG.md. It never fetches: run `git fetch origin` first.

  changelog.py status   [DIR]                       where this checkout stands (start here)
  changelog.py lint     FILE                        format errors (exit 1) and warnings
  changelog.py normalize FILE [--write]             tidy structure after merges: order, merge duplicates, drop empties
  changelog.py gaps     [DIR] [--all]               merged work on develop that no bullet mentions
  changelog.py history  [DIR] [--json]              deploys and merged items, with the release each shipped in
  changelog.py releases [DIR] [--apply FILE]        move shipped bullets under their release date (catch-up)
  changelog.py cut      FILE --date YYYY-MM-DD [--write]   move [Unreleased] under a release heading

File shape: `# Changelog`, an intro, `## [Unreleased]`, then `## [YYYY-MM-DD]` releases newest first
(the date the `[ production deploy ]` merge reached production). Only the dev's /update-changelog writes it, on a
`changelog/YYYY-MM-DD` branch cut from develop; feature and fix branches never touch it. Under each: `### Added`, `### Changed`,
`### Removed`, `### Fixed`, `### Security` (and `### Deprecated`, accepted but not written), in that
order, only the ones with bullets. Each bullet says what changed and why, and ends with its refs:
`(#12)`, `(#12, #13)` or a short commit hash `(1a2b3c4)`.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict

CHANGELOG = "CHANGELOG.md"
CATEGORIES = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
PRODUCTION = ("main", "master")
QA = ("beta", "deploy")
SYNC_BRANCHES = PRODUCTION + ("develop",) + QA
UNRELEASED = "Unreleased"

VERSION_RE = re.compile(r"^## \[(?P<name>[^\]]+)\]\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CATEGORY_RE = re.compile(r"^### (?P<name>\S.*?)\s*$")
BULLET_RE = re.compile(r"^[-*] \S")
REFS_RE = re.compile(r"\(\s*((?:#\d+|[0-9a-f]{7,40})(?:\s*,\s*(?:#\d+|[0-9a-f]{7,40}))*)\s*\)\s*\.?\s*$")
LINKDEF_RE = re.compile(r"^\[[^\]]+\]:\s+\S")
CONFLICT_RE = re.compile(r"^(<{7}|>{7})( |$)")
CHANGELOG_BRANCH_RE = re.compile(r"^changelog/(?P<date>\d{4}-\d{2}-\d{2})$")
BRANCH_RE = re.compile(r"^(?P<type>feature|fix)/(?P<issue>\d+)-(?P<desc>[a-z0-9][a-z0-9-]*?)(?:--(?P<sub>[a-z0-9][a-z0-9-]*))?$")
ISSUE_IN_BRANCH_RE = re.compile(r"(?:^|/)(?:feature|fix)/(\d+)-")
PR_MERGE_RE = re.compile(r"^Merge pull request #(\d+) from [^/\s]+/(\S+)")
BRANCH_MERGE_RE = re.compile(r"^Merge (?:remote-tracking )?branch '([^']+)'(?: of \S+)?(?: into (\S+))?")
SQUASH_RE = re.compile(r"\(#(\d+)\)\s*$")
SCAFFOLD = {"README.md", "README", "LICENSE", "LICENSE.md", ".gitignore", ".gitattributes"}


class Refusal(Exception):
    """Printed to stderr; exit code 2."""


# ============================================================================ the file

class Bullet:
    def __init__(self, lines):
        self.lines = lines  # first line starts with "- ", the rest are indented continuations

    def text(self):
        return " ".join(l.strip() for l in self.lines)

    def refs(self):
        m = REFS_RE.search(self.text())
        if not m:
            return set(), set()
        nums, shas = set(), set()
        for token in re.split(r"\s*,\s*", m.group(1)):
            if token.startswith("#"):
                nums.add(int(token[1:]))
            else:
                shas.add(token)
        return nums, shas

    def key(self):
        return self.text()


class Section:
    def __init__(self, name, line):
        self.name = name
        self.line = line          # 1-based line of the heading
        self.notes = []           # text directly under the heading, before any category
        self.cats = OrderedDict()  # name -> [Bullet]
        self.cat_lines = {}       # name -> 1-based line of its first heading
        self.stray = []           # (line, text) outside any bullet

    def is_release(self):
        return bool(DATE_RE.match(self.name))


class Changelog:
    def __init__(self):
        self.head = []
        self.sections = []
        self.tail = []
        self.problems = []  # (line, message) found while parsing
        self.bad_headings = []

    # --- parse --------------------------------------------------------------------------------------------
    @classmethod
    def parse(cls, text):
        doc = cls()
        lines = text.splitlines()
        end = len(lines)
        while end > 0 and (not lines[end - 1].strip() or LINKDEF_RE.match(lines[end - 1])):
            end -= 1
        doc.tail = [l for l in lines[end:] if l.strip()]
        section, cat, bullet = None, None, None
        for index, line in enumerate(lines[:end]):
            number = index + 1
            if CONFLICT_RE.match(line) or line == "=======" and any(CONFLICT_RE.match(l) for l in lines):
                doc.problems.append((number, "merge conflict marker"))
                continue
            if line.startswith("## "):
                m = VERSION_RE.match(line)
                name = m.group("name").strip() if m else None
                if name is None or not (name == UNRELEASED or DATE_RE.match(name)):
                    doc.bad_headings.append((number, line))
                    name = "?" + line
                section, cat, bullet = Section(name, number), None, None
                doc.sections.append(section)
                continue
            if section is None:
                doc.head.append(line)
                continue
            if line.startswith("### "):
                m = CATEGORY_RE.match(line)
                cat = m.group("name") if m else line[4:]
                if cat in section.cats:
                    doc.problems.append((number, "### %s appears twice in [%s]" % (cat, section.name)))
                section.cats.setdefault(cat, [])
                section.cat_lines.setdefault(cat, number)
                bullet = None
                continue
            if not line.strip():
                continue
            if BULLET_RE.match(line):
                if cat is None:
                    section.stray.append((number, line))
                    bullet = None
                    continue
                bullet = Bullet([line])
                section.cats[cat].append(bullet)
                continue
            if line[:1] in (" ", "\t") and bullet is not None:
                bullet.lines.append(line)
                continue
            if cat is None:
                section.notes.append(line)
            else:
                section.stray.append((number, line))
        return doc

    # --- queries ------------------------------------------------------------------------------------------
    def section(self, name):
        for s in self.sections:
            if s.name == name:
                return s
        return None

    def bullets(self):
        for s in self.sections:
            for cat, items in s.cats.items():
                for b in items:
                    yield s, cat, b

    # --- render -------------------------------------------------------------------------------------------
    def render(self):
        out = list(self.head)
        while out and not out[-1].strip():
            out.pop()
        for s in self.sections:
            out += ["", "## [%s]" % s.name]
            if s.notes:
                out += [""] + s.notes
            for cat, items in s.cats.items():
                if not items:
                    continue
                out += ["", "### %s" % cat, ""]
                for b in items:
                    out += b.lines
        if self.tail:
            out += [""] + self.tail
        return "\n".join(out).rstrip("\n") + "\n"


def category_rank(name):
    return CATEGORIES.index(name) if name in CATEGORIES else len(CATEGORIES)


def normalize_doc(doc):
    """Structural tidy-up, idempotent. Refuses on conflict markers or unparseable headings."""
    if any(msg == "merge conflict marker" for _, msg in doc.problems):
        raise Refusal("CHANGELOG.md has merge conflict markers: resolve them by hand first")
    if doc.bad_headings:
        raise Refusal("line %d: '%s' is not a version heading ('## [Unreleased]' or '## [YYYY-MM-DD]')"
                      % doc.bad_headings[0])
    merged = OrderedDict()
    for s in doc.sections:
        target = merged.get(s.name)
        if target is None:
            target = merged[s.name] = Section(s.name, s.line)
        target.notes += [n for n in s.notes if n not in target.notes]
        for cat, items in s.cats.items():
            bucket = target.cats.setdefault(cat, [])
            seen = {b.key() for b in bucket}
            for b in items:
                if b.key() not in seen:
                    bucket.append(b)
                    seen.add(b.key())
    if UNRELEASED not in merged:
        merged[UNRELEASED] = Section(UNRELEASED, 0)
    sections = []
    for name, s in merged.items():
        s.cats = OrderedDict(sorted(((c, b) for c, b in s.cats.items() if b), key=lambda kv: category_rank(kv[0])))
        if name != UNRELEASED and not s.cats and not s.notes:
            continue
        sections.append(s)
    unreleased = [s for s in sections if s.name == UNRELEASED]
    releases = sorted((s for s in sections if s.name != UNRELEASED), key=lambda s: s.name, reverse=True)
    doc.sections = unreleased + releases
    return doc


def lint_doc(doc, text):
    errors, warnings = list(doc.problems), []
    first = next((l for l in text.splitlines() if l.strip()), "")
    if first.strip() != "# Changelog":
        errors.append((1, "the first line must be '# Changelog'"))
    if sum(1 for l in doc.head if l.strip()) < 2:
        warnings.append((1, "no intro under the title (say it follows Keep a Changelog, releases named by date)"))
    for number, line in doc.bad_headings:
        errors.append((number, "'%s' is not '## [Unreleased]' or '## [YYYY-MM-DD]'" % line))
    names = [s.name for s in doc.sections if not s.name.startswith("?")]
    if names.count(UNRELEASED) != 1:
        errors.append((1, "there must be exactly one '## [Unreleased]' (found %d)" % names.count(UNRELEASED)))
    elif names[0] != UNRELEASED:
        errors.append((doc.section(UNRELEASED).line, "'## [Unreleased]' must come before every release"))
    dates = [s for s in doc.sections if s.is_release()]
    seen = {}
    for s in dates:
        if s.name in seen:
            errors.append((s.line, "release [%s] appears twice (first at line %d)" % (s.name, seen[s.name])))
        seen.setdefault(s.name, s.line)
    for a, b in zip(dates, dates[1:]):
        if b.name > a.name:
            errors.append((b.line, "releases must be newest first: [%s] comes after [%s]" % (b.name, a.name)))
    bullet_seen = {}
    for s in doc.sections:
        if s.notes and s.name != "?":
            warnings.append((s.line, "text directly under [%s] outside a category" % s.name))
        order = [c for c in s.cats]
        for cat in order:
            if cat not in CATEGORIES:
                errors.append((s.cat_lines.get(cat, s.line), "'### %s' is not one of %s" % (cat, ", ".join(CATEGORIES))))
            elif not s.cats[cat]:
                errors.append((s.cat_lines.get(cat, s.line), "'### %s' under [%s] is empty" % (cat, s.name)))
        known = [c for c in order if c in CATEGORIES]
        if known != sorted(known, key=category_rank):
            errors.append((s.line, "categories under [%s] must be in the order %s" % (s.name, ", ".join(CATEGORIES))))
        for number, line in s.stray:
            errors.append((number, "text outside a bullet or category: %s" % line.strip()[:60]))
    ref_home = {}
    for s, cat, b in doc.bullets():
        key = b.key()
        if key in bullet_seen:
            errors.append((s.line, "the same bullet appears twice: %s" % key[:70]))
        bullet_seen.setdefault(key, s.name)
        if "{{" in key and "}}" in key:
            errors.append((s.line, "unfilled placeholder in a bullet: %s" % key[:70]))
        nums, shas = b.refs()
        if not nums and not shas:
            warnings.append((s.line, "bullet under [%s] has no ref at the end, e.g. (#12): %s" % (s.name, key[:60])))
        for r in ["#%d" % n for n in nums] + sorted(shas):
            if r in ref_home and ref_home[r] != s.name:
                warnings.append((s.line, "%s has bullets under both [%s] and [%s]" % (r, ref_home[r], s.name)))
            ref_home.setdefault(r, s.name)
    return errors, warnings


def read_doc(path):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise Refusal("cannot read %s (%s)" % (path, exc.strerror))
    return text, Changelog.parse(text)


def guarded_write(path, text):
    if os.path.basename(path) != CHANGELOG:
        raise Refusal("refusing to write %s: this script only writes files named %s" % (path, CHANGELOG))
    if os.path.islink(path):
        raise Refusal("%s is a symlink; edit the target by hand" % path)
    tmp = path + ".tmp-changelog"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


# ============================================================================ git

def git(top, *args):
    r = subprocess.run(["git", "-C", top] + list(args), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def gout(top, *args):
    out = git(top, *args)
    return out.strip() if out is not None else None


def ref_exists(top, ref):
    return gout(top, "rev-parse", "--verify", "-q", ref + "^{commit}") is not None


def first_ref(top, candidates):
    for ref in candidates:
        if ref_exists(top, ref):
            return ref
    return None


class Repo:
    def __init__(self, directory):
        top = gout(os.path.abspath(directory), "rev-parse", "--show-toplevel")
        if not top:
            raise Refusal("%s is not inside a git repository" % directory)
        self.top = top
        self.develop = first_ref(top, ["origin/develop", "develop"])
        self.production = first_ref(top, ["origin/main", "origin/master", "main", "master"])
        self.qa = first_ref(top, ["origin/beta", "origin/deploy", "beta", "deploy"])
        self.branch = gout(top, "symbolic-ref", "--short", "-q", "HEAD")
        self._files = {}
        self._deploys = None

    # --- commits ------------------------------------------------------------------------------------------
    def files(self, sha, against=None):
        key = (sha, against)
        if key not in self._files:
            if against:
                out = git(self.top, "diff", "--name-only", against, sha)
            else:
                out = git(self.top, "diff-tree", "--no-commit-id", "-r", "--name-only", "--root", sha)
            self._files[key] = [l for l in (out or "").splitlines() if l]
        return self._files[key]

    def records(self, *range_args):
        fmt = "%H%x1f%P%x1f%cs%x1f%s%x1f%b%x1e"
        out = git(self.top, "log", "--first-parent", "--format=" + fmt, *range_args) or ""
        for rec in out.split("\x1e"):
            rec = rec.strip("\n")
            if rec:
                sha, parents, date, subject, body = (rec.split("\x1f") + [""] * 5)[:5]
                yield sha, parents.split(), date, subject, body.strip()

    def items(self, tip, stops=(), _depth=0):
        """Merged work reachable from `tip` along first parents (not from `stops`), newest first.

        A sync merge (from main, master, develop, beta or deploy) is expanded: the work it brought in
        is walked through its second parent, still excluding `stops` and its own first parent.
        """
        if not tip:
            return
        rng = [tip] + ["^" + s for s in stops]
        for sha, parents, date, subject, body in self.records(*rng):
            if len(parents) >= 2:
                m, mb = PR_MERGE_RE.match(subject), BRANCH_MERGE_RE.match(subject)
                pr = int(m.group(1)) if m else None
                branch = m.group(2) if m else (mb.group(1) if mb else None)
                if branch and branch.startswith("origin/"):
                    branch = branch[len("origin/"):]
                if branch and branch.startswith("changelog/"):
                    continue  # the dev's changelog pull request: never a gap
                if branch in SYNC_BRANCHES:
                    if _depth < 20:  # work that reached here through another permanent branch
                        yield from self.items(parents[1], tuple(stops) + (parents[0],), _depth + 1)
                    continue
                if self.files(sha, against=parents[0]) in ([], [CHANGELOG]):
                    continue  # nothing merged, or a changelog-only catch-up
                issue_match = ISSUE_IN_BRANCH_RE.search(branch or "")
                title = body.splitlines()[0] if (m and body) else subject
                yield Item("merge", sha, date, title, pr=pr, branch=branch,
                           issue=int(issue_match.group(1)) if issue_match else None)
            else:
                files = self.files(sha)
                if not files or files == [CHANGELOG]:
                    continue
                if not parents and set(files) <= SCAFFOLD:
                    continue  # a root commit with only scaffolding
                squash = SQUASH_RE.search(subject)
                yield Item("commit", sha, date, subject, pr=int(squash.group(1)) if squash else None)

    def deploys(self):
        """First-parent states of production, oldest first: [(sha, date, subject)]."""
        if self._deploys is None:
            self._deploys = []
            if self.production:
                recs = list(self.records(self.production))
                recs.reverse()
                for sha, parents, date, subject, _ in recs:
                    if not parents and set(self.files(sha)) <= SCAFFOLD:
                        continue
                    self._deploys.append((sha, date, subject))
        return self._deploys

    def is_ancestor(self, a, b):
        return subprocess.run(["git", "-C", self.top, "merge-base", "--is-ancestor", a, b],
                              capture_output=True).returncode == 0

    def shipped_in(self, sha):
        """Date of the earliest production state that contains `sha`, else None."""
        deploys = self.deploys()
        lo, hi, found = 0, len(deploys) - 1, None
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.is_ancestor(sha, deploys[mid][0]):
                found, hi = mid, mid - 1
            else:
                lo = mid + 1
        return deploys[found][1] if found is not None else None

    def changelog_added(self):
        if not self.develop:
            return None
        added = (gout(self.top, "log", "--first-parent", "--diff-filter=A", "--format=%H", self.develop,
                      "--", CHANGELOG) or "").split()
        return added[-1] if added else None


class Item:
    def __init__(self, kind, sha, date, title, pr=None, branch=None, issue=None):
        self.kind, self.sha, self.date, self.title = kind, sha, date, title
        self.pr, self.branch, self.issue = pr, branch, issue
        self.shipped = None

    def refs(self):
        return ["#%d" % n for n in (self.issue, self.pr) if n] or [self.sha[:7]]

    def describe(self):
        bits = [self.kind]
        if self.pr:
            bits.append("pr=#%d" % self.pr)
        if self.issue:
            bits.append("issue=#%d" % self.issue)
        if self.branch:
            bits.append("branch=%s" % self.branch)
        bits += ["sha=%s" % self.sha[:7], "date=%s" % self.date]
        return " ".join(bits) + ' title="%s"' % self.title.replace('"', "'")

    def as_json(self):
        return {"kind": self.kind, "sha": self.sha[:7], "date": self.date, "title": self.title, "pr": self.pr,
                "branch": self.branch, "issue": self.issue, "shipped_in": self.shipped, "refs": self.refs()}


def mentioned(item, nums, shas):
    if item.pr in nums or item.issue in nums:
        return True
    return any(item.sha.startswith(s) for s in shas)


def checkout_kind(branch):
    if branch is None:
        return "detached", None, None
    if branch == "develop":
        return "develop", None, None
    if branch in PRODUCTION:
        return "production", None, None
    if branch in QA:
        return "qa", None, None
    if CHANGELOG_BRANCH_RE.match(branch):
        return "changelog", None, None
    m = BRANCH_RE.match(branch)
    if m:
        parent = branch.split("--", 1)[0] if m.group("sub") else None
        return ("sub-branch" if parent else m.group("type")), int(m.group("issue")), parent
    loose = ISSUE_IN_BRANCH_RE.search(branch)
    return "other", (int(loose.group(1)) if loose else None), None


# ============================================================================ reconcile (catch-up)

def reconcile(doc, repo):
    """Move bullets to the release they shipped in. Returns (moves, unresolved)."""
    items = list(repo.items(repo.develop)) if repo.develop else []
    by_num, by_sha = {}, []
    for it in items:
        it.shipped = repo.shipped_in(it.sha)
        for n in (it.pr, it.issue):
            if n:
                by_num.setdefault(n, []).append(it)
        by_sha.append(it)
    deploys = repo.deploys()
    last_deploy = deploys[-1][1] if deploys else None
    moves, unresolved, plan = [], [], []
    for s, cat, b in list(doc.bullets()):
        nums, shas = b.refs()
        resolved = [it for n in nums for it in by_num.get(n, [])]
        resolved += [it for it in by_sha if any(it.sha.startswith(x) for x in shas)]
        if not resolved:
            if nums or shas:
                unresolved.append((s.name, b.key()))
            continue
        if any(it.shipped is None for it in resolved):
            actual = UNRELEASED
        else:
            actual = max(it.shipped for it in resolved)
        if s.name == actual:
            continue
        pending = s.is_release() and last_deploy is not None and s.name >= last_deploy
        if pending and actual == UNRELEASED:
            continue  # a manual cut waiting for its deploy: never undone
        if s.is_release() and last_deploy is None and actual == UNRELEASED:
            continue  # no deploy yet: a cut can only be pending
        plan.append((s, cat, b, actual, "shipped %s" % actual if actual != UNRELEASED else "not shipped yet"))
    for s, cat, b, target, why in plan:
        s.cats[cat].remove(b)
        dest = doc.section(target)
        if dest is None:
            dest = Section(target, 0)
            doc.sections.append(dest)
        dest.cats.setdefault(cat, []).append(b)
        moves.append((s.name, target, cat, b.key(), why))
    normalize_doc(doc)
    return moves, unresolved


# ============================================================================ commands

def cmd_lint(args):
    text, doc = read_doc(args.file)
    errors, warnings = lint_doc(doc, text)
    for line, msg in sorted(errors):
        print("ERROR line %d: %s" % (line, msg))
    for line, msg in sorted(warnings):
        print("WARN line %d: %s" % (line, msg))
    bullets = sum(1 for _ in doc.bullets())
    print("lint: %s (%d releases, %d bullets, %d errors, %d warnings)" % (
        "ok" if not errors else "failed", sum(1 for s in doc.sections if s.is_release()), bullets,
        len(errors), len(warnings)))
    return 1 if errors else 0


def cmd_normalize(args):
    text, doc = read_doc(args.file)
    out = normalize_doc(doc).render()
    if out == text:
        print("normalize: already normal")
        return 0
    if args.write:
        guarded_write(args.file, out)
        print("normalize: written")
    else:
        sys.stdout.write(out)
    return 0


def cmd_cut(args):
    if not DATE_RE.match(args.date):
        raise Refusal("--date must be YYYY-MM-DD")
    text, doc = read_doc(args.file)
    normalize_doc(doc)
    unreleased = doc.section(UNRELEASED)
    count = sum(len(v) for v in unreleased.cats.values())
    if not count:
        raise Refusal("[Unreleased] is empty: nothing to release")
    target = doc.section(args.date) or Section(args.date, 0)
    if target not in doc.sections:
        doc.sections.append(target)
    for cat, items in unreleased.cats.items():
        target.cats.setdefault(cat, []).extend(items)
    unreleased.cats = OrderedDict()
    out = normalize_doc(doc).render()
    print("cut: %d bullets moved from [Unreleased] to [%s]" % (count, args.date), file=sys.stderr)
    if args.write:
        guarded_write(args.file, out)
    else:
        sys.stdout.write(out)
    return 0


def cmd_history(args):
    repo = Repo(args.dir)
    if not repo.develop:
        print("develop: missing (no origin/develop or develop); nothing to walk")
        return 0
    items = list(repo.items(repo.develop))
    items.reverse()
    for it in items:
        it.shipped = repo.shipped_in(it.sha)
    deploys = repo.deploys()
    if args.json:
        releases = OrderedDict()
        for it in items:
            releases.setdefault(it.shipped or UNRELEASED, []).append(it.sha[:7])
        print(json.dumps({"develop": repo.develop, "production": repo.production,
                          "deploys": [{"sha": d[0][:7], "date": d[1], "subject": d[2]} for d in deploys],
                          "items": [it.as_json() for it in items],
                          "releases": releases}, indent=2))
        return 0
    print("## deploys (%s, oldest first)" % (repo.production or "no production branch"))
    for sha, date, subject in deploys:
        print('deploy: %s %s "%s"' % (date, sha[:7], subject.replace('"', "'")))
    print("\n## items (%s, oldest first)" % repo.develop)
    for it in items:
        print("item: %s shipped=%s" % (it.describe(), it.shipped or "unreleased"))
    print("\n## releases")
    counts = OrderedDict()
    for it in items:
        counts[it.shipped or UNRELEASED] = counts.get(it.shipped or UNRELEASED, 0) + 1
    for name in sorted((n for n in counts if n != UNRELEASED), reverse=True):
        print("release: [%s] items=%d" % (name, counts[name]))
    print("unreleased: items=%d" % counts.get(UNRELEASED, 0))
    return 0


def find_gaps(repo, doc, include_all=False):
    if not repo.develop:
        return None, []
    start = None if include_all else repo.changelog_added()
    stop = None
    if start:
        parent = gout(repo.top, "rev-parse", "-q", "--verify", start + "^1")
        stop = parent or None
    nums, shas = set(), set()
    for _, _, b in (doc.bullets() if doc else []):
        n, s = b.refs()
        nums |= n
        shas |= s
    gaps = [it for it in repo.items(repo.develop, (stop,) if stop else ()) if not mentioned(it, nums, shas)]
    return start, gaps


def cmd_gaps(args):
    repo = Repo(args.dir)
    path = os.path.join(repo.top, CHANGELOG)
    doc = read_doc(path)[1] if os.path.isfile(path) else None
    start, gaps = find_gaps(repo, doc, args.all)
    if not repo.develop:
        print("develop: missing; nothing to compare")
        return 0
    print("base: %s" % repo.develop)
    print("since: %s" % ("%s (CHANGELOG.md added)" % start[:7] if start else "the first commit"))
    for it in gaps:
        print("gap: %s" % it.describe())
    print("gaps: %d" % len(gaps))
    return 0


def cmd_releases(args):
    repo = Repo(args.dir)
    path = args.apply or os.path.join(repo.top, CHANGELOG)
    text, doc = read_doc(path)
    moves, unresolved = reconcile(doc, repo)
    for src, dst, cat, key, why in moves:
        print("move: [%s] -> [%s] (%s; %s): %s" % (src, dst, cat, why, key[:80]))
    for name, key in unresolved:
        print("unresolved: [%s] %s" % (name, key[:80]))
    print("moves: %d" % len(moves))
    if args.apply and moves:
        guarded_write(args.apply, doc.render())
        print("applied to %s" % args.apply)
    return 0


def cmd_status(args):
    repo = Repo(args.dir)
    findings = []
    kind, issue, parent = checkout_kind(repo.branch)
    print("## checkout")
    print("dir: %s" % repo.top)
    print("branch: %s" % (repo.branch or "(detached HEAD)"))
    print("kind: %s" % kind)
    if issue:
        print("issue: #%d" % issue)
    if parent:
        print("parent: %s (bullets belong on the parent branch)" % parent)
    print("develop: %s" % (repo.develop or "missing"))
    print("production: %s" % (repo.production or "missing"))
    print("qa: %s" % (repo.qa or "none"))
    if kind == "production":
        findings.append(("NOTE", "on-production", "CHANGELOG.md is never edited here; /update-changelog cuts a changelog/ branch from develop"))
    elif kind == "qa":
        findings.append(("NOTE", "on-qa", "CHANGELOG.md is never edited on the QA branch"))
    elif kind == "develop":
        findings.append(("NOTE", "on-develop", "/update-changelog cuts changelog/<date> from here; never commit on develop"))
    elif kind in ("feature", "fix", "sub-branch"):
        findings.append(("NOTE", "feature-branch", "feature and fix branches never edit CHANGELOG.md"))
    elif kind in ("other", "detached"):
        findings.append(("NOTE", "not-a-changelog-branch", "CHANGELOG.md is edited only on a changelog/<date> branch"))

    path = os.path.join(repo.top, CHANGELOG)
    doc = None
    print("\n## file")
    if os.path.isfile(path):
        text, doc = read_doc(path)
        errors, warnings = lint_doc(doc, text)
        print("changelog: present (%d releases, %d bullets)" % (sum(1 for s in doc.sections if s.is_release()),
                                                             sum(1 for _ in doc.bullets())))
        print("lint: %s" % ("ok" if not errors else "%d errors" % len(errors))
              + ("" if not warnings else ", %d warnings" % len(warnings)))
        if errors:
            findings.append(("ASK", "lint-errors:%d" % len(errors), "run lint; `normalize` fixes structure, the rest is by hand"))
        unreleased = doc.section(UNRELEASED)
        print("unreleased_bullets: %d" % sum(len(v) for v in (unreleased.cats.values() if unreleased else [])))
    else:
        print("changelog: absent")
        findings.append(("ASK", "no-changelog", "no CHANGELOG.md: backfill it (reference/backfill.md)"))
    attr = gout(repo.top, "check-attr", "merge", "--", CHANGELOG) or ""
    print("union_merge: %s" % ("yes" if attr.endswith(": union") else "no"))

    st = git(repo.top, "status", "--porcelain", "--untracked-files=all") or ""
    changed, cl_dirty = [], False
    for line in st.splitlines():
        name = line[3:].split(" -> ")[-1].strip('"')
        if name == CHANGELOG:
            cl_dirty = True
        else:
            changed.append("%s %s" % (line[:2].replace(" ", "."), name))
    print("\n## uncommitted")
    print("files: %s" % (", ".join(changed) or "none"))
    print("changelog_dirty: %s" % ("yes" if cl_dirty else "no"))

    if kind == "changelog" and repo.develop:
        own = (gout(repo.top, "rev-list", "--no-merges", "%s..HEAD" % repo.develop) or "").split()
        print("\n## branch")
        print("release_date: %s" % CHANGELOG_BRANCH_RE.match(repo.branch).group("date"))
        print("own_commits: %d" % len(own))
        others = sorted({f for sha in own for f in repo.files(sha)} - {CHANGELOG})
        if others:
            findings.append(("ASK", "not-changelog-only:%d" % len(others),
                             "this branch changes more than CHANGELOG.md: %s" % ", ".join(others[:5])))
        changed_vs_develop = git(repo.top, "diff", "--quiet", "%s...HEAD" % repo.develop, "--", CHANGELOG) is None
        upstream = gout(repo.top, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        ahead = gout(repo.top, "rev-list", "--count", "@{u}..HEAD") if upstream else None
        print("pr_ready: changelog %s vs %s; %s; %s" % (
            "changed" if changed_vs_develop else "unchanged", repo.develop,
            "changelog uncommitted" if cl_dirty else "committed",
            ("pushed" if ahead == "0" else "%s commit(s) not pushed" % ahead) if upstream else "no upstream yet"))

    if doc is not None and repo.develop:
        probe = Changelog.parse(doc.render())
        moves, unresolved = reconcile(probe, repo)
        start, gaps = find_gaps(repo, doc)
        deploys = repo.deploys()
        print("\n## releases")
        print("last_deploy: %s" % ("%s %s" % (deploys[-1][1], deploys[-1][0][:7]) if deploys else "none yet"))
        print("pending_moves: %d (run `releases --apply CHANGELOG.md` on a draft)" % len(moves))
        print("unresolved_refs: %d" % len(unresolved))
        print("gaps: %d since CHANGELOG.md was added (run `gaps`)" % len(gaps))
        if moves:
            findings.append(("ASK", "pending-moves:%d" % len(moves), "shipped bullets to move first"))
        if gaps:
            findings.append(("ASK", "gaps:%d" % len(gaps), "merged work with no bullet"))

    print("\n## FINDINGS")
    for level, code, msg in findings:
        print("%s %s: %s" % (level, code, msg))
    if not findings:
        print("none")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("dir", nargs="?", default=".")
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("lint")
    s.add_argument("file")
    s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("normalize")
    s.add_argument("file")
    s.add_argument("--write", action="store_true")
    s.set_defaults(fn=cmd_normalize)
    s = sub.add_parser("gaps")
    s.add_argument("dir", nargs="?", default=".")
    s.add_argument("--all", action="store_true")
    s.set_defaults(fn=cmd_gaps)
    s = sub.add_parser("history")
    s.add_argument("dir", nargs="?", default=".")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_history)
    s = sub.add_parser("releases")
    s.add_argument("dir", nargs="?", default=".")
    s.add_argument("--apply", metavar="FILE")
    s.set_defaults(fn=cmd_releases)
    s = sub.add_parser("cut")
    s.add_argument("file")
    s.add_argument("--date", required=True)
    s.add_argument("--write", action="store_true")
    s.set_defaults(fn=cmd_cut)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except Refusal as exc:
        print("changelog.py: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
