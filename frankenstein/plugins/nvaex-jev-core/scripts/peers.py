#!/usr/bin/env python3
"""List live Claude Code sessions from <config>/sessions/*.json. Read-only. Usage: peers.py [name-substring]"""
import glob, json, os, sys, time
base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
want = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
rows = []
for f in glob.glob(os.path.join(base, "sessions", "*.json")):
    try:
        s = json.load(open(f)); os.kill(int(s["pid"]), 0)
    except Exception:
        continue
    t = (s.get("updatedAt") or s.get("startedAt") or 0) / 1000
    rows.append((s.get("name", "?"), s.get("status", "?"), s.get("cwd", "?"), int(time.time() - t) // 60))
rows = [r for r in rows if want in r[0].lower()]
print(f"{len(rows)} live session(s)")
for n, st, cwd, age in sorted(rows):
    print(f"{n:16} {st:8} {age:>5}m  {cwd}")
