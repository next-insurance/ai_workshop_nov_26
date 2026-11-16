#!/usr/bin/env bash
# 🚦 Phase gate: an agent can't finish while the Superpowers artifacts are inconsistent.
# SubagentStop + Stop. Exit 2 = keep working; stderr says what to fix.
TEST_CMD="npm test --silent"     # your repo: a test command that runs once and exits
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
event=$(cat | grep -o '"hook_event_name" *: *"[A-Za-z]*"' | sed 's/.*"\([A-Za-z]*\)"$/\1/')
log=".claude/hook-log.txt"; counter=".claude/.gate-attempts"; ts=$(date '+%H:%M:%S')
spec=$(ls -t docs/superpowers/specs/*.md 2>/dev/null | head -1)
plan=$(ls -t docs/superpowers/plans/*.md 2>/dev/null | head -1)
[ -z "$spec$plan" ] && exit 0      # no feature yet: nothing to check

problem=""
if [ -n "$spec" ] && grep -qsE 'TBD|TODO|NEEDS CLARIFICATION' "$spec"; then
  problem="$spec still has open TBD/TODO markers"
elif [ -n "$plan" ] && [ -z "$spec" ]; then
  problem="$plan exists without a design doc"
elif [ -n "$plan" ] && grep -qs '^- \[[xX]\]' "$plan" && ! $TEST_CMD > .claude/.gate-output.txt 2>&1; then
  problem="plan steps are ticked but the tests fail:
$(tail -20 .claude/.gate-output.txt)"
fi

if [ -z "$problem" ]; then
  echo "$ts ${event:-?} PASS ${plan:-$spec}" >> "$log"; echo 0 > "$counter"; exit 0
fi
n=$(( $(cat "$counter" 2>/dev/null || echo 0) + 1 ))
if [ "$n" -gt 3 ]; then
  echo "$ts ${event:-?} GAVE UP ${plan:-$spec}" >> "$log"; echo 0 > "$counter"; exit 0
fi
echo "$n" > "$counter"
echo "$ts ${event:-?} BLOCK #$n ${plan:-$spec}" >> "$log"
echo "Phase gate (attempt $n/3): $problem. Fix it before you finish." >&2
exit 2
