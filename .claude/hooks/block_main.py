#!/usr/bin/env python3
"""PreToolUse(Bash) hook: stop Claude from pushing or merging into main.

Exit 2 = block the tool call; stderr is shown to Claude.
"""
import json
import re
import subprocess
import sys

# Drop quoted strings so commit messages / echo text can't trigger a false block.
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'[^\']*\'', re.S)
GH_MERGE = re.compile(r"\bgh\s+pr\s+merge\b")
PUSH_MAIN = re.compile(r"\bgit\b[^;&|]*\bpush\b[^;&|]*[\s:/+]main(?=\s|$|[;&|])")
PUSH_OR_MERGE = re.compile(r"\bgit\b[^;&|]*\b(?:push|merge)\b")


def block_reason(command, branch):
    """Return why the command is blocked, or None if it's allowed."""
    # ponytail: regex over the command string; aliases or scripts that wrap git can slip past.
    cmd = QUOTED.sub("", command)
    if GH_MERGE.search(cmd):
        return "merging PRs is not allowed"
    if PUSH_MAIN.search(cmd):
        return "push to main"
    if branch == "main" and PUSH_OR_MERGE.search(cmd):
        return "push/merge while on main"
    return None


def current_branch(cwd):
    result = subprocess.run(
        ["git", "-C", cwd or ".", "branch", "--show-current"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def main():
    data = json.load(sys.stdin)
    command = (data.get("tool_input") or {}).get("command") or ""
    reason = block_reason(command, current_branch(data.get("cwd")))
    if reason:
        print(f"Blocked: {reason}. Push to a feature branch and open a PR instead.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
