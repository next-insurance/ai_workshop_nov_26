#!/usr/bin/env python3
"""Block Cursor agent git pushes to main/master.

Cursor runs this on beforeShellExecution (.cursor/hooks.json). A human pushing
in a terminal is not intercepted.

Stdin is the beforeShellExecution payload: a top-level "command" and "cwd".
Stdout is always {"permission": "allow"} or {"permission": "deny", ...}.
Empty stdout is invalid for this event and would block the command.
"""
import json
import re
import subprocess
import sys

PROTECTED = ("main", "master")
REASON = (
    "Direct push to main/master is blocked in this repo. Open a PR instead:\n"
    "  git switch -c feat/<name> && git push -u origin feat/<name> && gh pr create --base main\n"
    "If a direct push is genuinely required, ask the user to run it themselves."
)


GIT_GLOBAL_OPTS_WITH_VALUE = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path")


def is_git_push(cmd):
    """Does this shell command actually run `git push`?

    Tokenised, not grepped. A word-boundary regex treats a hyphen as a boundary,
    so a command that merely mentions a path like `block-push-to-main.py` can
    look like a push. This walks argv instead.
    """
    for seg in re.split(r"&&|\|\||;|\|", cmd):
        toks = seg.split()
        for i, tok in enumerate(toks):
            if tok != "git" and not tok.endswith("/git"):
                continue
            args, j = toks[i + 1:], 0
            while j < len(args):
                if args[j] in GIT_GLOBAL_OPTS_WITH_VALUE:
                    j += 2
                elif args[j].startswith("-"):
                    j += 1
                else:
                    break
            if j < len(args) and args[j] == "push":
                return True
    return False


def targets_protected(cmd, cwd):
    if not is_git_push(cmd):
        return False

    # Scope every question below to the `git push` SEGMENT, never the whole command line. A chain
    # like `git push -u origin sdlc/x && gh pr create --base main` names a protected branch — in a
    # different command, about a different thing — and reading the whole line denies it.
    seg = next((s for s in re.split(r"&&|\|\||;|\|", cmd) if is_git_push(s)), cmd)

    # Explicit protected target: `origin main`, ` main `, `HEAD:main`, `:main`.
    if re.search(r"(?:^|[\s:])(?:main|master)(?:\s|$)", seg) or re.search(
        r"HEAD:(?:main|master)\b", seg
    ):
        return True

    # The push's positional (non-flag) args.
    toks = seg.split()
    args = toks[toks.index("push") + 1:] if "push" in toks else []
    refs = [t for t in args if not t.startswith("-") and t != "origin"]
    if refs:
        return False  # an explicit non-protected ref is named -> allow (feature push)

    # Bare push (no explicit ref): block only if the current branch is protected.
    try:
        branch = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        branch = ""
    return branch in PROTECTED


def emit(deny):
    if deny:
        json.dump(
            {
                "permission": "deny",
                "user_message": REASON,
                "agent_message": REASON,
            },
            sys.stdout,
        )
        return
    json.dump({"permission": "allow"}, sys.stdout)


def decide():
    try:
        data = json.load(sys.stdin)
    except Exception:
        emit(False)
        return

    emit(targets_protected(data.get("command") or "", data.get("cwd") or "."))


if __name__ == "__main__":
    decide()
    sys.exit(0)
