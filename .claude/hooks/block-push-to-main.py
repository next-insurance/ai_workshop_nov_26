#!/usr/bin/env python3
"""PreToolUse hook: stop Claude from pushing to main.
Simplified from ai-sdlc-graph/.claude/hooks/block-push-to-main.py"""
import json, subprocess, sys

PROTECTED = ("main", "master")
REASON = ("Direct push to main is blocked in this repo. Push a side branch instead:\n"
          "  git switch -c feat/<name> && git push -u origin feat/<name>\n"
          "If a direct push is really needed, ask the user to run it themselves.")

# 1. read the tool call Claude wants to make
data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

# 2. find the `git push` part (the command may be chained with && or ;)
parts = cmd.replace("&&", ";").replace("||", ";").split(";")
pushes = [p for p in parts if "git" in p.split() and "push" in p.split()]
if not pushes:
    sys.exit(0)                                  # not a push → allow
words = pushes[0].split()
targets = [w for w in words[words.index("push") + 1:]
           if not w.startswith("-") and w != "origin"]

# 3. decide
def dest(t):  # "+HEAD:refs/heads/main" -> "main"
    return t.split(":")[-1].lstrip("+").removeprefix("refs/heads/")

if any(dest(t) in PROTECTED for t in targets):
    blocked = True                               # git push origin main · HEAD:main
elif targets:
    blocked = False                              # git push origin feat/x
else:                                            # bare `git push`: which branch am I on?
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True,
                            cwd=data.get("cwd", ".")).stdout.strip()
    blocked = branch in PROTECTED

# 4. to block: print a "deny" decision. Claude sees REASON.
if blocked:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": REASON}}))
sys.exit(0)
