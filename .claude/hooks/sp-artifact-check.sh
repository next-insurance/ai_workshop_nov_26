#!/usr/bin/env bash
# 📄 Artifact check: runs after every file edit, checks Superpowers artifacts.
# PostToolUse on Edit|Write. Exit 2 = the agent reads stderr and fixes the file.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
file=$(cat | grep -o '"file_path" *: *"[^"]*"' | head -1 | sed 's/.*: *"//; s/"$//')
file=${file#"$PWD/"}
log=".claude/hook-log.txt"; ts=$(date '+%H:%M:%S')
OPEN='TBD|TODO|NEEDS CLARIFICATION'
fail() { echo "$ts PostToolUse BLOCK $file" >> "$log"; echo "$file: $1" >&2; exit 2; }

case "$file" in
  *docs/superpowers/specs/*.md)
    n=$(grep -cE "$OPEN" "$file" 2>/dev/null); n=${n:-0}
    [ "$n" -gt 0 ] && fail "$n open TBD/TODO markers. Decide each one,
note the decision under Assumptions, and remove the marker."
    grep -qi '^#.*assumptions' "$file" || fail "no Assumptions heading. List every decision you made alone." ;;
  *docs/superpowers/plans/*.md)
    grep -qE "$OPEN" "$file" && fail "the plan has TBD/TODO placeholders. Write the real step."
    grep -qi 'test' "$file" || fail "the plan never says how the feature is tested. Add it."
    grep -q '^- \[[ xX]\]' "$file" || fail "no '- [ ]' steps. Write each step as a checkbox naming a file." ;;
  *) exit 0 ;;
esac
echo "$ts PostToolUse PASS $file" >> "$log"; exit 0
