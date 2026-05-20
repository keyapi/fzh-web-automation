#!/usr/bin/env bash
# SessionStart hook — 注入 git 状态到 Claude 上下文
input=$(cat)
cwd=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd','.'))" <<< "$input" 2>/dev/null || echo ".")
cd "$cwd" 2>/dev/null || true

branch=$(git branch --show-current 2>/dev/null || echo "N/A")
changes=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
last_commit=$(git log --oneline -1 2>/dev/null | tr '\n' ' |' || echo "N/A")
last_time=$(git log -1 --format=%cr 2>/dev/null || echo "N/A")

echo "{\"continue\":true, \"hookSpecificOutput\":{\"additionalContext\":\"[SessionStart] 分支:$branch | 未提交:$changes文件 | 最近:$last_commit($last_time)\"}}"
