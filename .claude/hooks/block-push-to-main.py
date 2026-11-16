#!/usr/bin/env python3
"""Pre-shell hook: stop the agent from pushing to main.
Works as a Claude Code PreToolUse hook and as a Cursor beforeShellExecution hook.
Simplified from ai-sdlc-graph/.claude/hooks/block-push-to-main.py"""
import json, subprocess, sys

PROTECTED = ("main", "master")
REASON = ("Direct push to main is blocked in this repo. Push a side branch instead:\n"
          "  git switch -c feat/<name> && git push -u origin feat/<name>\n"
          "If a direct push is really needed, ask the user to run it themselves.")

# 1. read the tool call the agent wants to make
data = json.load(sys.stdin)
is_claude = "tool_input" in data
cmd = data.get("tool_input", {}).get("command", "") if is_claude else data.get("command", "")


def allow():
    if not is_claude:
        print(json.dumps({"permission": "allow"}))
    sys.exit(0)


# 2. find the `git push` part (the command may be chained with && or ;)
parts = cmd.replace("&&", ";").replace("||", ";").split(";")
pushes = [p for p in parts if "git" in p.split() and "push" in p.split()]
if not pushes:
    allow()                                      # not a push → allow
words = pushes[0].split()
targets = [w for w in words[words.index("push") + 1:]
           if not w.startswith("-") and w != "origin"]

# 3. decide
if any(t.split(":")[-1] in PROTECTED for t in targets):
    blocked = True                               # git push origin main · HEAD:main
elif targets:
    blocked = False                              # git push origin feat/x
else:                                            # bare `git push`: which branch am I on?
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True,
                            cwd=data.get("cwd") or ".").stdout.strip()
    blocked = branch in PROTECTED

# 4. to block: print a "deny" decision. The agent sees REASON.
if not blocked:
    allow()
if is_claude:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": REASON}}))
else:
    print(json.dumps({"permission": "deny",
                      "user_message": "Blocked a direct push to main.",
                      "agent_message": REASON}))
sys.exit(0)
