#!/usr/bin/env bash
# Run: .claude/hooks/test-block-main.sh  (from a non-main branch)
h="$(dirname "$0")/block-main.sh"; fail=0
check() { jq -n --arg c "$2" '{tool_input:{command:$c},cwd:"."}' | "$h" 2>/dev/null; [[ $? == "$1" ]] || { echo "FAIL ($1): $2"; fail=1; }; }
check 2 "git push origin main"
check 2 "git push -f origin HEAD:main"
check 2 "git add . && git push origin main"
check 2 "gh pr merge 12 --squash"
check 0 "git push origin feature/main-page"
check 0 "git push -u origin my-branch"
check 0 "git merge main"
check 0 "ls"
check 2 "rtk git push origin main"
check 0 "git commit -m 'blocks gh pr merge and git push origin main'"
check 0 'git commit -m "msg with \"git push origin main\" inside"'
[[ $fail == 0 ]] && echo "all passed"; exit $fail
