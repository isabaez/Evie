#!/usr/bin/env python3
# init-project-file v1 — managed by /init-project; re-sync replaces this file
"""Inventory how a project's code measures up to CLAUDE.md's conventions block. Read-only.

  conventions_scan.py [DIR] [--examples N]

Sections: css (class naming: BEM, camelCase, short or state classes; styled js- hooks), hooks (how scripts find
elements), names (single-letter variables and parameters), a11y (helpers present, unused or missing), then a
SUMMARY. Counts plus file:line examples. Heuristic: regexes over tracked files, good enough to size a refactor and
spot missing helpers, not a linter.
"""
import argparse
import os
import re
import subprocess
from collections import Counter, defaultdict

STYLE_EXT = (".css", ".scss", ".sass", ".less")
MARKUP_EXT = (".html", ".htm", ".svelte", ".vue", ".jsx", ".tsx", ".jinja", ".j2")
SCRIPT_EXT = (".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".svelte", ".vue", ".html", ".htm")
PY_EXT = (".py",)
SKIP_PARTS = {"node_modules", "dist", "build", ".venv", "venv", "vendor", "__pycache__", ".git", ".svelte-kit",
              "coverage", "drizzle", ".claude"}
MAX_BYTES = 1_000_000

BEM_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:__[a-z0-9]+(?:-[a-z0-9]+)*)?(?:--[a-z0-9]+(?:-[a-z0-9]+)*)?$")
CAMEL_RE = re.compile(r"^[a-z]+[A-Z][A-Za-z0-9]*$")
SELECTOR_CLASS_RE = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")
MARKUP_CLASS_RE = re.compile(r"""\bclass(?:Name)?\s*=\s*(?:"([^"]*)"|'([^']*)')""")
SVELTE_CLASS_DIRECTIVE_RE = re.compile(r"\bclass:([\w-]+)")
MODULE_CLASS_RE = re.compile(r"\b(?:s|styles|css|classes)\.([A-Za-z_][\w]*)")
STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
QUERY_RE = re.compile(r"""(querySelector(?:All)?|closest|matches)\(\s*(['"`])(.+?)\2""")
BY_ID_RE = re.compile(r"getElementById\(|getElementsByClassName\(")
REF_RE = re.compile(r"\buseRef\(|\bbind:this\b|\bref=\{|\$refs\b")
JS_SINGLE_RES = (
    re.compile(r"\b(?:const|let|var)\s+([A-Za-z])\s*(?==|;|,)"),
    re.compile(r"\bfor\s*\(\s*(?:let|var|const)\s+([A-Za-z])\b"),
    re.compile(r"\bcatch\s*\(\s*([A-Za-z])\s*\)"),
    re.compile(r"(?:^|[=(,:\s])([A-Za-z])\s*=>"),
)
JS_PARAMS_RES = (
    re.compile(r"\bfunction\s*[\w$]*\s*\(([^)]*)\)"),
    re.compile(r"\(([^()]*)\)\s*=>"),
)
PY_SINGLE_RES = (
    re.compile(r"^\s*([A-Za-z])\s*(?::[^=\n]+)?=(?!=)", re.M),
    re.compile(r"\bfor\s+([A-Za-z])\s+in\b"),
    re.compile(r"\bexcept\s+[\w.]+\s+as\s+([A-Za-z])\b"),
    re.compile(r"\bimport\s+[\w.]+\s+as\s+([A-Za-z])\b"),
    re.compile(r"\bwith\s+[^:]+\s+as\s+([A-Za-z])\s*:"),
)
PY_PARAMS_RES = (re.compile(r"\bdef\s+\w+\s*\(([^)]*)\)"), re.compile(r"\blambda\s+([^:]*):"))
A11Y_CHECKS = (
    ("visually_hidden", re.compile(r"\.(visually-hidden|sr-only|vh|screen-reader-text)\b")),
    ("skip_link", re.compile(r"skip[-_ ]link|skip to (main|content)", re.I)),
    ("focus_visible", re.compile(r":focus-visible")),
    ("reduced_motion", re.compile(r"prefers-reduced-motion")),
    ("live_region", re.compile(r"aria-live|role=[\"'](status|alert)[\"']")),
    ("dialog", re.compile(r"<dialog\b|showModal\(|role=[\"']dialog[\"']|aria-modal")),
    ("inert", re.compile(r"\binert\b")),
)
ZOOM_RE = re.compile(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", re.I)
OUTLINE_NONE_RE = re.compile(r"outline\s*:\s*(none|0)\b")


def tracked_files(top):
    out = subprocess.run(["git", "-C", top, "ls-files", "-z"], capture_output=True, text=True)
    if out.returncode == 0:
        files = [f for f in out.stdout.split("\0") if f]
    else:
        files = []
        for root, dirs, names in os.walk(top):
            dirs[:] = [d for d in dirs if d not in SKIP_PARTS and not d.startswith(".")]
            files += [os.path.relpath(os.path.join(root, n), top) for n in names]
    keep = []
    for f in files:
        if any(part in SKIP_PARTS for part in f.split("/")[:-1]):
            continue
        path = os.path.join(top, f)
        if os.path.isfile(path) and os.path.getsize(path) <= MAX_BYTES:
            keep.append(f)
    return keep


def read(top, rel):
    with open(os.path.join(top, rel), encoding="utf-8", errors="replace") as handle:
        return handle.read()


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def strip_css(text):
    """Selectors only: comments removed, declaration bodies emptied (nested rules keep their selectors)."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(?m)//[^\n]*$", "", text)
    return re.sub(r"\{[^{}]*\}", "{}", re.sub(r":\s*[^;{}]+;", ";", text))


def classify(name):
    if name.startswith("js-"):
        return "js-hook"
    if len(name) <= 2:
        return "short"
    if re.match(r"^(is|has)-", name):
        return "state"
    if CAMEL_RE.match(name):
        return "camelCase"
    if BEM_RE.match(name):
        if "__" in name:
            return "bem-element"
        if "--" in name:
            return "bem-modifier"
        return "block"
    return "other"


def scan(top, examples):
    files = tracked_files(top)
    report = defaultdict(list)
    classes = {}               # name -> (kind, first location)
    styled_js = []
    hooks = Counter()
    hook_examples = defaultdict(list)
    refs = 0
    singles = Counter()
    single_examples = []
    a11y = {name: [] for name, _ in A11Y_CHECKS}
    helper_usage = Counter()
    zoom, outline_none = [], []
    stylesheets = markup = 0
    texts = {}

    def add_class(name, where):
        if name.endswith(("-", "_")) or not re.match(r"^-?[A-Za-z_][\w-]*$", name):
            return  # a class name built at runtime ("sort-button--{dir}") or not a name at all
        if name not in classes:
            classes[name] = (classify(name), where)

    for rel in files:
        lower = rel.lower()
        ext = os.path.splitext(lower)[1]
        if ext not in STYLE_EXT + MARKUP_EXT + SCRIPT_EXT + PY_EXT:
            continue
        try:
            text = read(top, rel)
        except OSError:
            continue
        texts[rel] = text
        css_parts = []
        if ext in STYLE_EXT:
            stylesheets += 1
            css_parts.append((0, text))
        for match in STYLE_BLOCK_RE.finditer(text):
            css_parts.append((match.start(1), match.group(1)))
        for offset, css in css_parts:
            selectors = strip_css(css)
            for match in SELECTOR_CLASS_RE.finditer(selectors):
                name = match.group(1)
                add_class(name, "%s" % rel)
                if name.startswith("js-"):
                    styled_js.append("%s: .%s" % (rel, name))
            for match in OUTLINE_NONE_RE.finditer(css):
                if ":focus-visible" not in css:
                    outline_none.append("%s:%d" % (rel, line_of(text, offset + match.start())))
        if ext in MARKUP_EXT:
            markup += 1
            for match in MARKUP_CLASS_RE.finditer(text):
                value = match.group(1) if match.group(1) is not None else match.group(2)
                for name in re.findall(r"[-\w]+", re.sub(r"\{[^}]*\}", " ", value or "")):
                    add_class(name, "%s:%d" % (rel, line_of(text, match.start())))
            for match in SVELTE_CLASS_DIRECTIVE_RE.finditer(text):
                add_class(match.group(1), "%s:%d" % (rel, line_of(text, match.start())))
        if ext in (".jsx", ".tsx"):
            for match in MODULE_CLASS_RE.finditer(text):
                add_class(match.group(1), "%s:%d" % (rel, line_of(text, match.start())))
        if ext in SCRIPT_EXT:
            refs += len(REF_RE.findall(text))
            for match in QUERY_RE.finditer(text):
                selector = match.group(3).strip()
                if selector.startswith("#"):
                    kind = "id"
                elif selector.startswith(".js-") or " .js-" in selector:
                    kind = "js-class"
                elif selector.startswith("."):
                    kind = "styling-class"
                elif selector.startswith("["):
                    kind = "data-attribute" if selector.startswith("[data-") else "attribute"
                else:
                    kind = "element-or-mixed"
                hooks[kind] += 1
                if len(hook_examples[kind]) < examples:
                    hook_examples[kind].append("%s:%d %s('%s')" % (rel, line_of(text, match.start()), match.group(1),
                                                                    selector[:50]))
            for match in BY_ID_RE.finditer(text):
                hooks["id"] += 1
                if len(hook_examples["id"]) < examples:
                    hook_examples["id"].append("%s:%d %s" % (rel, line_of(text, match.start()), match.group(0)[:-1]))
            found = []
            for rx in JS_SINGLE_RES:
                found += [(m.start(1), m.group(1)) for m in rx.finditer(text)]
            for rx in JS_PARAMS_RES:
                for m in rx.finditer(text):
                    for param in re.split(r"\s*,\s*", m.group(1)):
                        name = re.sub(r"[=:].*$", "", param.strip()).strip("{}[] .")
                        if re.fullmatch(r"[A-Za-z]", name):
                            found.append((m.start(1), name))
            for index, name in sorted(set(found)):
                singles[rel] += 1
                if len(single_examples) < examples:
                    single_examples.append("%s:%d %s" % (rel, line_of(text, index), name))
        if ext in PY_EXT:
            found = []
            for rx in PY_SINGLE_RES:
                found += [(m.start(1), m.group(1)) for m in rx.finditer(text)]
            for rx in PY_PARAMS_RES:
                for m in rx.finditer(text):
                    for param in re.split(r"\s*,\s*", m.group(1)):
                        name = re.sub(r"[=:].*$", "", param.strip()).lstrip("*").strip()
                        if re.fullmatch(r"[A-Za-z]", name):
                            found.append((m.start(1), name))
            for index, name in sorted(set(found)):
                singles[rel] += 1
                if len(single_examples) < examples:
                    single_examples.append("%s:%d %s" % (rel, line_of(text, index), name))
        for name, rx in A11Y_CHECKS:
            for m in rx.finditer(text):
                if len(a11y[name]) < examples:
                    a11y[name].append("%s:%d" % (rel, line_of(text, m.start())))
                break
        for m in re.finditer(r"""class(?:Name)?\s*=\s*["'][^"']*\b(visually-hidden|sr-only|vh|screen-reader-text)\b""",
                             text):
            helper_usage[m.group(1)] += 1
        if ext in MARKUP_EXT:
            for m in ZOOM_RE.finditer(text):
                zoom.append("%s:%d" % (rel, line_of(text, m.start())))
    for rel in files:  # config files can import stylesheets too (vite, svelte, package.json)
        if rel not in texts and os.path.splitext(rel)[1] in (".json", ".cjs", ".mjs", ".js", ".ts"):
            try:
                texts[rel] = read(top, rel)
            except OSError:
                pass
    unloaded = set()
    for rel in {where.split(":")[0] for hits in a11y.values() for where in hits}:
        if os.path.splitext(rel)[1] not in STYLE_EXT:
            continue
        name = os.path.basename(rel)
        stem = re.sub(r"^_", "", os.path.splitext(name)[0])
        use_rx = re.compile(r"@(?:use|import|forward)\s+['\"][^'\"]*\b%s\b" % re.escape(stem))
        if not any(other != rel and (name in body or use_rx.search(body)) for other, body in texts.items()):
            unloaded.add(rel)
    contrast = [f for f in files if re.search(r"contrast", os.path.basename(f), re.I)]
    pkg = os.path.join(top, "package.json")
    if os.path.isfile(pkg) and re.search(r"\"[^\"]*contrast[^\"]*\"\s*:", read(top, "package.json")):
        contrast.append("package.json script")
    return {
        "files": files, "stylesheets": stylesheets, "markup": markup, "classes": classes, "styled_js": styled_js,
        "hooks": hooks, "hook_examples": hook_examples, "refs": refs, "singles": singles,
        "single_examples": single_examples, "a11y": a11y, "helper_usage": helper_usage, "zoom": zoom,
        "outline_none": outline_none, "contrast": contrast, "unloaded": unloaded,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("dir", nargs="?", default=".")
    parser.add_argument("--examples", type=int, default=5)
    args = parser.parse_args()
    top = subprocess.run(["git", "-C", os.path.abspath(args.dir), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip() or os.path.abspath(args.dir)
    r = scan(top, args.examples)
    kinds = Counter(kind for kind, _ in r["classes"].values())
    total = sum(kinds.values())
    bem_like = kinds["bem-element"] + kinds["bem-modifier"] + kinds["block"]
    print("## css")
    print("files: %d stylesheets, %d markup files" % (r["stylesheets"], r["markup"]))
    print("classes: %d unique (%s)" % (total, ", ".join("%s %d" % (k, kinds[k]) for k in
          ("bem-element", "bem-modifier", "block", "camelCase", "short", "state", "js-hook", "other") if kinds[k])))
    print("bem_compatible: %s" % ("%d%% (blocks, elements and modifiers)" % round(100 * bem_like / total) if total else "n/a"))
    for kind in ("camelCase", "short", "state", "other"):
        names = [n for n, (k, _) in r["classes"].items() if k == kind][:args.examples]
        if names:
            print("example_%s: %s" % (kind, ", ".join(".%s (%s)" % (n, r["classes"][n][1]) for n in names)))
    print("styled_js_hooks: %s" % ("; ".join(r["styled_js"][:args.examples]) or "none"))
    print("\n## hooks")
    print("selectors: %s; framework refs %d" % (", ".join("%s %d" % kv for kv in sorted(r["hooks"].items())) or "none",
                                                r["refs"]))
    for kind, items in sorted(r["hook_examples"].items()):
        print("example_%s: %s" % (kind, "; ".join(items)))
    print("\n## names")
    count = sum(r["singles"].values())
    print("single_letter: %d in %d files" % (count, len(r["singles"])))
    if count:
        print("top_files: %s" % ", ".join("%s (%d)" % kv for kv in r["singles"].most_common(args.examples)))
        print("examples: %s" % "; ".join(r["single_examples"]))
    print("\n## a11y")
    for name, _ in A11Y_CHECKS:
        where = r["a11y"][name]
        line = "present (%s)" % ", ".join(where) if where else "missing"
        if where and all(w.split(":")[0] in r["unloaded"] for w in where):
            line = "defined but not loaded (%s: nothing imports it)" % ", ".join(where)
        if name == "visually_hidden" and where:
            used = sum(r["helper_usage"].values())
            line += "; used %d time(s) in markup" % used
        print("%s: %s" % (name, line))
    print("zoom_blocked: %s" % ("; ".join(r["zoom"][:args.examples]) or "no"))
    print("outline_removed_without_focus_visible: %s" % ("; ".join(r["outline_none"][:args.examples]) or "none"))
    print("contrast_check: %s" % (", ".join(r["contrast"]) or "none"))
    print("\n## SUMMARY")
    notes = []
    if total and bem_like < total:
        notes.append("CSS: %d of %d class names don't fit BEM (%s)" % (
            total - bem_like - kinds["js-hook"], total,
            ", ".join("%s %d" % (k, kinds[k]) for k in ("camelCase", "short", "state", "other") if kinds[k])))
    if r["styled_js"]:
        notes.append("CSS: %d styled js- hook(s)" % len(r["styled_js"]))
    styling_hooks = r["hooks"]["styling-class"] + r["hooks"]["id"]
    if styling_hooks:
        notes.append("Hooks: %d lookups by styling class or id (use js- classes or refs)" % styling_hooks)
    if count:
        notes.append("Names: %d single-letter names in %d files" % (count, len(r["singles"])))
    for name, _ in A11Y_CHECKS:
        if not r["a11y"][name] and name in ("visually_hidden", "skip_link", "focus_visible", "reduced_motion",
                                            "live_region"):
            notes.append("A11y: no %s helper" % name.replace("_", " "))
    if r["a11y"]["visually_hidden"] and not sum(r["helper_usage"].values()):
        notes.append("A11y: a visually-hidden helper is defined but never used")
    if r["unloaded"]:
        notes.append("A11y: helpers sit in %s, which nothing imports" % ", ".join(sorted(r["unloaded"])))
    if r["zoom"]:
        notes.append("A11y: zoom is blocked in the viewport meta tag")
    if r["outline_none"]:
        notes.append("A11y: focus outlines removed without a :focus-visible replacement")
    for note in notes or ["nothing to report"]:
        print("- " + note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
