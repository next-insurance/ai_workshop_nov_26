#!/usr/bin/env bash
# ✋ Code gate: no code until the Superpowers plan exists and a human approved it.
# PreToolUse on Edit|Write. Exit 2 = block; stderr goes to the agent.
CODE_DIR="src/"                 # your repo: the folder that holds your code
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
file=$(cat | grep -o '"file_path" *: *"[^"]*"' | head -1 | sed 's/.*: *"//; s/"$//')
case "$file" in
  *"/$CODE_DIR"*|"$CODE_DIR"*) ;;  # a code file: check the gate
  *) exit 0 ;;                     # docs, tests, config: allowed
esac
plan=$(ls -t docs/superpowers/plans/*.md 2>/dev/null | head -1)
if [ -n "$plan" ] && grep -qs '^Approved-by:' "${plan%.md}.APPROVED"; then
  exit 0
fi
echo "Blocked: code can't change yet. Order is design doc, then plan," >&2
echo "then a human writes ${plan:-docs/superpowers/plans/<plan>.md} -> .APPROVED. Finish your phase and stop." >&2
exit 2
