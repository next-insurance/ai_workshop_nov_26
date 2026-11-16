#!/usr/bin/env python3
"""Run: python3 .claude/hooks/test_block_main.py"""
from block_main import block_reason

BLOCKED = [
    ("git push origin main", "feature"),
    ("git push -f origin HEAD:main", "feature"),
    ("git add . && git push origin main", "feature"),
    ("rtk git push origin main", "feature"),
    ("gh pr merge 12 --squash", "feature"),
    ("git push", "main"),
    ("git merge feature", "main"),
]
ALLOWED = [
    ("git push origin feature/main-page", "feature"),
    ("git push -u origin my-branch", "feature"),
    ("git merge main", "feature"),
    ("ls", "main"),
    ("git commit -m 'blocks gh pr merge and git push origin main'", "feature"),
    ('git commit -m "msg with \\"git push origin main\\" inside"', "feature"),
]

for cmd, branch in BLOCKED:
    assert block_reason(cmd, branch), f"should block: {cmd!r} on {branch}"
for cmd, branch in ALLOWED:
    assert not block_reason(cmd, branch), f"should allow: {cmd!r} on {branch}"
print("all passed")
