#!/usr/bin/env python3
# init-project-file v2 — managed by /init-project; re-sync replaces this file
"""Claude Code PreToolUse hook: block the git and gh commands this project's workflow never allows.

The rules are in .claude/rules/git-workflow.md; this hook enforces only its "never" rules:
  - pull requests: never into main/master or the QA branch (beta/deploy), never from a permanent branch,
    never retargeted there, never merged by Claude (`gh pr merge`);
  - merges: never into main/master/develop, never from the QA branch into anything else;
  - commits: never on main/master/develop; on the QA branch only to finish a merge;
  - pushes: never to main/master/develop, never forced (except the QA rebuild's
    `--force-with-lease=<qa>:<sha>`), never deleting a permanent branch;
  - never rebase a pushed branch, never branch from production or QA (except creating develop),
    never delete or rename a permanent branch;
  - never discard uncommitted work (stash, reset --hard, clean, checkout/restore of files, forced switches);
  - CHANGELOG.md changes only on a changelog/ branch (the dev's /update-changelog), commits and file edits alike;
  - never commit secret files: .env files, .claude/settings.local.json, private keys and certificates (*.pem, *.key,
    *.p12, *.pfx, id_rsa*, id_ed25519*, … but not *.pub), credentials*.json, and an .npmrc or .pypirc that holds a
    token or password (a `${VAR}` reference is fine).
"Ask first" rules (issues, merges into the QA branch, deleting other branches) are not checked here.

Bash commands are split into simple commands; `cd`, `git -C` and branch switches earlier in the same command are
followed. A block exits 2 with the reason on stderr. Anything else exits 0. An internal error exits 1: Claude Code
shows it and lets the command run. It never fetches or touches the network. This is a guardrail for Claude's own
commands, not a security boundary.
"""
import json
import os
import re
import shlex
import subprocess
import sys

PRODUCTION = ("main", "master")
QA = ("beta", "deploy")
PERMANENT = PRODUCTION + ("develop",) + QA
NO_MERGE_INTO = PRODUCTION + ("develop",)
NO_BRANCH_FROM = PRODUCTION + QA
CHANGELOG = "CHANGELOG.md"
CHANGELOG_BRANCH_RE = re.compile(r"^changelog/")
SECRET_RE = re.compile(r"(^|/)(\.env(\.(?!example$|sample$|template$|dist$)[^/]+)?|\.claude/settings\.local\.json"
                       r"|[^/]+\.(pem|key|p12|pfx)|id_(rsa|dsa|ecdsa|ed25519)(?![^/]*\.pub$)[^/]*|credentials[^/]*\.json)$",
                       re.IGNORECASE)
TOKEN_FILES = (".npmrc", ".pypirc")
TOKEN_RE = re.compile(r"(_authToken|_auth|_password|password|token)\s*[=:]\s*(?!\$\{)[^\s#;]+", re.IGNORECASE)
SEPARATORS = {"&&", "||", ";", "|", "&", ";;", "|&", "(", ")"}
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
UNKNOWN = object()  # a branch switch we can't follow (e.g. `git switch -`)
SEE = " (.claude/rules/git-workflow.md)"


class Blocked(Exception):
    pass


def block(message):
    raise Blocked("Blocked by the git guard: " + message + SEE)


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True, text=True)
    except OSError:
        return 1, ""
    return r.returncode, r.stdout.strip()


def holds_token(top, name):
    """True when the staged (else the working-tree) copy of an .npmrc or .pypirc has a literal token or password."""
    if not top:
        return False
    code, text = git(top, "show", ":" + name)
    if code != 0:
        try:
            with open(os.path.join(top, name), encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            return False
    return bool(TOKEN_RE.search(text))


def segments(command):
    """Split a shell command into simple commands (lists of words). Newlines separate commands too."""
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    current, out = [], []
    for token in lexer:
        if token in SEPARATORS:
            if current:
                out.append(current)
            current = []
        else:
            current.append(token)
    if current:
        out.append(current)
    return out


def strip_prefixes(words):
    """Drop leading VAR=value assignments and `env`/`command`/`exec`/`time`/`nohup` wrappers."""
    while words:
        if ASSIGNMENT_RE.match(words[0]):
            words = words[1:]
        elif words[0] in ("env", "command", "exec", "time", "nohup", "builtin"):
            words = words[1:]
            while words and words[0].startswith("-"):
                words = words[1:]
        else:
            break
    return words


def option_value(args, names, short=None):
    """The value of --name VALUE / --name=VALUE / -XVALUE, or None."""
    for i, word in enumerate(args):
        for name in names:
            if word == name and i + 1 < len(args):
                return args[i + 1]
            if name.startswith("--") and word.startswith(name + "="):
                return word.split("=", 1)[1]
        if short and word.startswith(short) and len(word) > len(short) and not word.startswith("--"):
            return word[len(short):]
    return None


def positionals(args, valued=()):
    """Non-option words, skipping the values of options in `valued`; everything after `--` is positional."""
    out, i = [], 0
    while i < len(args):
        word = args[i]
        if word == "--":
            out.extend(args[i + 1:])
            break
        if word.startswith("-") and word != "-":
            if word in valued:
                i += 2
                continue
            i += 1
            continue
        out.append(word)
        i += 1
    return out


def has(args, *flags):
    for word in args:
        if word == "--":
            return False
        if word in flags:
            return True
        for flag in flags:
            if flag.startswith("--") and word.startswith(flag + "="):
                return True
    return False


def short_flags(args):
    """Letters of bundled short options (-fd → {'f','d'}), before any `--`."""
    letters = set()
    for word in args:
        if word == "--":
            break
        if word.startswith("-") and not word.startswith("--") and len(word) > 1:
            letters.update(word[1:])
    return letters


class Guard:
    def __init__(self):
        self.tops = {}
        self.branches = {}  # top -> branch name, None (detached) or UNKNOWN, after switches earlier in the command
        self.remote_names = {}

    def top(self, cwd):
        if cwd not in self.tops:
            code, out = git(cwd, "rev-parse", "--show-toplevel") if os.path.isdir(cwd) else (1, "")
            self.tops[cwd] = out if code == 0 and out else None
        return self.tops[cwd]

    def branch(self, cwd):
        top = self.top(cwd)
        if top is None:
            return UNKNOWN
        if top not in self.branches:
            code, out = git(top, "symbolic-ref", "--short", "-q", "HEAD")
            self.branches[top] = out if code == 0 and out else None
        return self.branches[top]

    def set_branch(self, cwd, name):
        top = self.top(cwd)
        if top is not None:
            self.branches[top] = name

    def remotes(self, cwd):
        top = self.top(cwd)
        if top not in self.remote_names:
            code, out = git(top, "remote") if top else (1, "")
            self.remote_names[top] = set(out.split()) if code == 0 and out else {"origin"}
        return self.remote_names[top]

    def short(self, cwd, ref):
        """`origin/develop`, `refs/remotes/origin/develop`, `refs/heads/develop` → `develop`."""
        for prefix in ("refs/heads/", "refs/remotes/", "remotes/"):
            if ref.startswith(prefix):
                ref = ref[len(prefix):]
                break
        if "/" in ref and ref.split("/", 1)[0] in self.remotes(cwd):
            ref = ref.split("/", 1)[1]
        return ref

    def ref_exists(self, cwd, ref):
        top = self.top(cwd)
        return bool(top) and git(top, "rev-parse", "--verify", "-q", ref)[0] == 0

    def in_merge(self, cwd):
        top = self.top(cwd)
        if not top:
            return False
        code, path = git(top, "rev-parse", "--git-path", "MERGE_HEAD")
        return code == 0 and os.path.exists(path if os.path.isabs(path) else os.path.join(top, path))

    # ------------------------------------------------------------------ gh

    def gh(self, words, cwd):
        rest = words[1:]
        i = 0
        while i < len(rest) and rest[i].startswith("-"):
            i += 2 if rest[i] in ("-R", "--repo") else 1
        if i >= len(rest):
            return
        group, args = rest[i], rest[i + 1:]
        if group == "api":
            joined = " ".join(args)
            if re.search(r"/pulls/\d+/merge\b|/merges\b", joined):
                block("Claude never merges pull requests; the dev merges them.")
            return
        if group != "pr":
            return
        j = 0
        while j < len(args) and args[j].startswith("-"):
            j += 2 if args[j] in ("-R", "--repo") else 1
        if j >= len(args):
            return
        action, args = args[j], args[:j] + args[j + 1:]
        if action == "merge":
            block("Claude never merges pull requests; the dev reviews and merges them.")
        if action not in ("create", "edit"):
            return
        base = option_value(args, ("--base", "-B"), "-B")
        if base and self.short(cwd, base) in PRODUCTION + QA:
            block("pull requests never go into %s. Feature, fix and changelog branches go into develop; the dev "
                  "opens the `[ production deploy ]` pull request." % base)
        if action == "create":
            head = option_value(args, ("--head", "-H"), "-H")
            if head and ":" in head:
                head = head.split(":", 1)[1]
            if not head:
                current = self.branch(cwd)
                head = current if isinstance(current, str) else None
            if head in PERMANENT:
                block("pull requests come from a feature/, fix/ or changelog/ branch, not from %s." % head)

    # ------------------------------------------------------------------ git

    def git_command(self, words, cwd):
        rest = words[1:]
        i = 0
        while i < len(rest) and rest[i].startswith("-"):
            word = rest[i]
            if word == "-C" and i + 1 < len(rest):
                target = os.path.expanduser(rest[i + 1])
                cwd = target if os.path.isabs(target) else os.path.normpath(os.path.join(cwd, target))
                i += 2
            elif word in ("-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"):
                i += 2
            else:
                i += 1
        if i >= len(rest):
            return
        sub, args = rest[i], rest[i + 1:]
        handler = getattr(self, "git_" + sub.replace("-", "_"), None)
        if handler and self.top(cwd) is not None:
            handler(args, cwd)

    def git_merge(self, args, cwd):
        if has(args, "--abort", "--quit"):
            return
        branch = self.branch(cwd)
        if branch in NO_MERGE_INTO:
            block("Claude never merges into %s; work reaches it only through a pull request the dev merges." % branch)
        if has(args, "--continue"):
            return
        for source in positionals(args, ("-m", "-F", "-s", "-X", "--strategy", "--strategy-option", "--file",
                                         "--into-name", "--cleanup")):
            name = self.short(cwd, source)
            if name in QA and name != branch:
                block("the QA branch (%s) is a dead end: never merge it into anything." % name)

    def git_pull(self, args, cwd):
        branch = self.branch(cwd)
        sources = positionals(args, ("-s", "-X", "--strategy", "--strategy-option", "--depth", "-j", "--jobs"))
        for source in sources[1:]:
            name = self.short(cwd, source.split(":", 1)[0])
            if name in QA and name != branch:
                block("the QA branch (%s) is a dead end: never pull it into anything." % name)
        if branch in NO_MERGE_INTO and not has(args, "--ff-only"):
            top = self.top(cwd)
            if git(top, "config", "--get", "pull.ff")[1] != "only":
                block("on %s, pull only with `git pull --ff-only` so nothing is ever merged into it." % branch)

    def git_commit(self, args, cwd):
        branch = self.branch(cwd)
        if branch in NO_MERGE_INTO:
            block("never commit on %s: cut a feature/ or fix/ branch from origin/develop." % branch)
        if branch in QA and not self.in_merge(cwd):
            block("never commit on the QA branch (%s), except to finish a merge into it." % branch)
        top = self.top(cwd)
        specs = positionals(args, ("-m", "--message", "-F", "--file", "-C", "-c", "--reuse-message",
                                   "--reedit-message", "--author", "--date", "--fixup", "--squash", "-t",
                                   "--template", "--cleanup", "--trailer", "-S", "--gpg-sign"))
        if specs:
            code, out = git(cwd, "diff", "--name-only", "HEAD", "--", *specs)
            if code != 0:
                code, out = git(cwd, "diff", "--name-only", "--cached", "--", *specs)
            names = out.splitlines() + [s for s in specs if os.path.basename(s) == CHANGELOG]
        else:
            names = git(top, "diff", "--name-only", "--cached")[1].splitlines()
            if "a" in short_flags(args) or has(args, "--all"):
                names += git(top, "diff", "--name-only")[1].splitlines()
        if isinstance(branch, str) and not CHANGELOG_BRANCH_RE.match(branch):
            if any(os.path.basename(n) == CHANGELOG for n in names):
                block("CHANGELOG.md changes only on a changelog/ branch made by the dev's /update-changelog; "
                      "leave it out of this commit (`git restore --staged CHANGELOG.md`).")
        secrets = [n for n in names if SECRET_RE.search(n)]
        secrets += [n for n in names if os.path.basename(n) in TOKEN_FILES and holds_token(top, n)]
        if secrets:
            block("never commit %s: unstage it with `git restore --staged`." % ", ".join(sorted(set(secrets))))

    def git_push(self, args, cwd):
        valued = ("-o", "--push-option", "--repo", "--receive-pack", "--exec")
        words = positionals(args, valued)
        refspecs = words[1:]
        branch = self.branch(cwd)
        if has(args, "--mirror", "--all", "--branches"):
            block("never push every branch at once (it would push develop or production directly).")
        deleting = "d" in short_flags(args) or has(args, "--delete")
        destinations = []
        forced = "f" in short_flags(args) or has(args, "--force")
        for spec in refspecs:
            if spec.startswith("+"):
                forced, spec = True, spec[1:]
            src, _, dst = spec.partition(":")
            dst = dst or src
            if dst in ("HEAD", "@"):
                dst = branch if isinstance(branch, str) else dst
            name = self.short(cwd, dst)
            if deleting or src == "":
                if name in PERMANENT:
                    block("never delete the permanent branch %s." % name)
                continue
            destinations.append(name)
        if not refspecs and isinstance(branch, str):
            code, upstream = git(self.top(cwd), "rev-parse", "--abbrev-ref", "%s@{push}" % branch)
            destinations.append(self.short(cwd, upstream) if code == 0 and upstream else branch)
        for name in destinations:
            if name in NO_MERGE_INTO:
                block("never push to %s directly; it changes only through pull requests the dev merges." % name)
        lease = option_value(args, ("--force-with-lease",))
        if has(args, "--force-with-lease"):
            target = lease.split(":", 1)[0] if lease else None
            qa_rebuild = (target in QA and ":" in (lease or "") and destinations
                          and all(d == target for d in destinations))
            if not qa_rebuild:
                block("never force-push. The one exception is rebuilding the QA branch with "
                      "`--force-with-lease=<qa>:<old sha>` (CONTRIBUTING.md).")
        if forced:
            block("never force-push. The one exception is rebuilding the QA branch with "
                  "`--force-with-lease=<qa>:<old sha>` (CONTRIBUTING.md).")

    def git_rebase(self, args, cwd):
        if has(args, "--abort", "--quit", "--continue", "--skip", "--edit-todo", "--show-current-patch"):
            return
        refs = positionals(args, ("--onto", "-s", "--strategy", "-X", "--strategy-option", "-x", "--exec"))
        branch = self.short(cwd, refs[1]) if len(refs) > 1 else self.branch(cwd)
        if not isinstance(branch, str):
            return
        if branch in PERMANENT:
            block("never rebase %s." % branch)
        for remote in self.remotes(cwd):
            if self.ref_exists(cwd, "refs/remotes/%s/%s" % (remote, branch)):
                block("%s has been pushed: catch up by merging origin/develop in, never by rebasing." % branch)

    def check_start(self, cwd, new, start):
        if start is None:
            current = self.branch(cwd)
            if not isinstance(current, str):
                return
            start = current
        name = self.short(cwd, start)
        if name in NO_BRANCH_FROM and not (new == "develop" and name in PRODUCTION):
            block("never branch from %s: cut branches from an up-to-date origin/develop." % name)

    def git_switch(self, args, cwd):
        if has(args, "--discard-changes", "--force") or "f" in short_flags(args):
            block("never discard uncommitted work (no forced switch); the dev may have changes in progress.")
        create = option_value(args, ("-c", "-C", "--create", "--force-create"))
        refs = positionals(args, ("-c", "-C", "--create", "--force-create", "--orphan", "-t", "--track"))
        if create:
            self.check_start(cwd, create, refs[0] if refs else None)
            self.set_branch(cwd, create)
        elif has(args, "--orphan"):
            self.set_branch(cwd, option_value(args, ("--orphan",)))
        elif has(args, "--detach", "-d"):
            self.set_branch(cwd, None)
        elif refs:
            self.set_branch(cwd, UNKNOWN if refs[0] == "-" else self.short(cwd, refs[0]))

    def git_checkout(self, args, cwd):
        if has(args, "--force") or "f" in short_flags(args):
            block("never discard uncommitted work (no `checkout -f`); the dev may have changes in progress.")
        create = option_value(args, ("-b", "-B", "--orphan"))
        if "--" in args:
            paths = args[args.index("--") + 1:]
            if paths and not has(args, "--ours", "--theirs"):
                block("never discard uncommitted work (`checkout -- <paths>` overwrites the dev's edits).")
            return
        refs = positionals(args, ("-b", "-B", "--orphan", "-t", "--track", "--conflict"))
        if create:
            self.check_start(cwd, create, refs[0] if refs else None)
            self.set_branch(cwd, create)
            return
        if not refs:
            return
        target = refs[0]
        if target == "-":
            self.set_branch(cwd, UNKNOWN)
            return
        is_commit = self.ref_exists(cwd, target + "^{commit}")
        if target == "." or len(refs) > 1 or (not is_commit and os.path.exists(os.path.join(cwd, target))):
            if not has(args, "--ours", "--theirs"):
                block("never discard uncommitted work (`checkout <paths>` overwrites the dev's edits).")
            return
        is_branch = self.ref_exists(cwd, "refs/heads/" + target) or any(
            self.ref_exists(cwd, "refs/remotes/%s/%s" % (r, target)) for r in self.remotes(cwd))
        self.set_branch(cwd, target if is_branch and not has(args, "--detach") else None)

    def git_branch(self, args, cwd):
        letters = short_flags(args)
        refs = positionals(args, ("-u", "--set-upstream-to", "--contains", "--no-contains", "--merged",
                                  "--no-merged", "--points-at", "--sort", "--format", "--color", "--column",
                                  "-t", "--track"))
        if letters & {"d", "D"} or has(args, "--delete"):
            for name in refs:
                if self.short(cwd, name) in PERMANENT:
                    block("never delete the permanent branch %s." % name)
            return
        if letters & {"m", "M"} or has(args, "--move"):
            old = refs[0] if len(refs) > 1 else self.branch(cwd)
            if isinstance(old, str) and old in PERMANENT:
                block("never rename the permanent branch %s." % old)
            return
        listing = letters & {"a", "r", "l", "v", "c", "C", "u"} or has(
            args, "--list", "--all", "--remotes", "--show-current", "--contains", "--no-contains", "--merged",
            "--no-merged", "--points-at", "--set-upstream-to", "--unset-upstream", "--edit-description", "--copy")
        if listing or not refs:
            return
        if (letters & {"f"} or has(args, "--force")) and refs[0] in PERMANENT:
            block("never move the permanent branch %s." % refs[0])
        self.check_start(cwd, refs[0], refs[1] if len(refs) > 1 else None)

    def git_worktree(self, args, cwd):
        if not args:
            return
        action, rest = args[0], args[1:]
        if action == "remove" and (has(rest, "--force") or "f" in short_flags(rest)):
            block("never `worktree remove --force`: it deletes uncommitted and ignored files.")
        if action == "add":
            create = option_value(rest, ("-b", "-B"))
            if create:
                refs = positionals(rest, ("-b", "-B", "--reason"))
                self.check_start(cwd, create, refs[1] if len(refs) > 1 else None)

    def git_stash(self, args, cwd):
        if args and args[0] in ("list", "show"):
            return
        block("never stash: uncommitted work stays exactly where the dev left it.")

    def git_reset(self, args, cwd):
        if has(args, "--hard", "--merge"):
            block("never `reset --hard`: it discards uncommitted work.")

    def git_clean(self, args, cwd):
        if "n" in short_flags(args) or has(args, "--dry-run"):
            return
        block("never `git clean`: it deletes untracked files the dev may need.")

    def git_restore(self, args, cwd):
        staged_only = (has(args, "--staged") or "S" in short_flags(args)) and not (
            has(args, "--worktree") or "W" in short_flags(args))
        if not staged_only:
            block("never discard uncommitted work (`restore` without --staged overwrites the dev's edits).")

    # ------------------------------------------------------------------ entry points

    def bash(self, command, cwd):
        if not re.search(r"\b(git|gh)\b", command):
            return
        try:
            parts = segments(command)
        except ValueError:
            return  # unbalanced quotes: the shell will reject it anyway
        for words in parts:
            words = strip_prefixes(words)
            if not words:
                continue
            if words[0] in ("cd", "pushd") and len(words) > 1:
                target = os.path.expanduser(words[1])
                cwd = target if os.path.isabs(target) else os.path.normpath(os.path.join(cwd, target))
                continue
            name = os.path.basename(words[0])
            if name == "gh":
                self.gh(words, cwd)
            elif name == "git":
                self.git_command(words, cwd)

    def edit(self, path, cwd):
        if not path or os.path.basename(path) != CHANGELOG:
            return
        path = path if os.path.isabs(path) else os.path.join(cwd, path)
        folder = os.path.dirname(path)
        while folder and not os.path.isdir(folder):
            folder = os.path.dirname(folder)
        branch = self.branch(folder) if folder else UNKNOWN
        if branch is UNKNOWN:
            return
        if branch is None or not CHANGELOG_BRANCH_RE.match(branch):
            block("CHANGELOG.md is written only by the dev's /update-changelog, on a changelog/ branch; "
                  "this checkout is on %s." % (branch or "a detached HEAD"))


def main():
    try:
        data = json.load(sys.stdin)
        tool = data.get("tool_name") or "Bash"
        tool_input = data.get("tool_input") or {}
        cwd = data.get("cwd") or os.getcwd()
        guard = Guard()
        try:
            if tool in EDIT_TOOLS:
                guard.edit(tool_input.get("file_path") or tool_input.get("notebook_path"), cwd)
            else:
                guard.bash(tool_input.get("command") or "", cwd)
        except Blocked as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0
    except Exception as exc:  # never block on our own bug; make it visible instead
        print("git-guard hook error (not blocking): %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
