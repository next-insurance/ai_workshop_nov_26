#!/usr/bin/env bash
# PreToolUse(Bash) hook: stop Claude from pushing or merging into main.
# Exit 2 = block the tool call; stderr is shown to Claude.
input=$(cat)
# Drop quoted strings so commit messages / echo text can't trigger a false block.
cmd=$(jq -r '.tool_input.command // empty' <<<"$input" | perl -0pe 's/"(\\.|[^"\\])*"|\x27[^\x27]*\x27//g')
cwd=$(jq -r '.cwd // empty' <<<"$input")
branch=$(git -C "${cwd:-.}" branch --show-current 2>/dev/null)

block() { echo "Blocked: $1. Push to a feature branch and open a PR instead." >&2; exit 2; }

# ponytail: regex over the raw command string; aliases or scripts that wrap git can slip past.
grep -Eq '\bgh[[:space:]]+pr[[:space:]]+merge\b' <<<"$cmd" && block "merging PRs is not allowed"
grep -Eq '\bgit\b[^;&|]*\bpush\b[^;&|]*[[:space:]:/+]main([[:space:]]|$|[;&|])' <<<"$cmd" && block "push to main"
if [[ "$branch" == "main" ]]; then
  grep -Eq '\bgit\b[^;&|]*\b(push|merge)\b' <<<"$cmd" && block "push/merge while on main"
fi
exit 0
