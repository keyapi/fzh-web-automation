#!/usr/bin/env python
"""SessionStart hook: inject git status into Claude context."""
import json, subprocess, os, sys

sys.stdout.reconfigure(encoding="utf-8")

try:
    data = json.load(sys.stdin)
    cwd = data.get("cwd", os.getcwd())
    os.chdir(cwd)
except (json.JSONDecodeError, FileNotFoundError):
    pass

def git(*args):
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace",
        )
        return r.stdout.strip()
    except Exception:
        return "N/A"

branch = git("branch", "--show-current") or "N/A"
raw = git("status", "--porcelain")
changes = len([l for l in raw.split("\n") if l.strip()])
last = (git("log", "--oneline", "-1") or "N/A")[:80]
last_time = git("log", "-1", "--format=%cr") or "N/A"

context = f"[SessionStart] branch:{branch} | uncommitted:{changes} files | last:{last} ({last_time})"
out = {"continue": True, "hookSpecificOutput": {"additionalContext": context}}
print(json.dumps(out, ensure_ascii=False))
