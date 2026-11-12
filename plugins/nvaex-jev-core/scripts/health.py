#!/usr/bin/env python3
"""PostToolUse: Gate 3 (execution health). Non-blocking. Speaks only when something actually repeats:
- the same call (tool + input) three times within the last 10 calls: "Is a step repeating?";
- a file edited for the 3rd, 6th, 9th ... time, said once on that edit (it used to repeat on every later call)."""
import json, os, sys
d = json.load(sys.stdin)
sid = d.get("session_id", "x")
st = os.path.expanduser("~/.claude/state/nvaex-jev-core")
os.makedirs(st, exist_ok=True)
f = os.path.join(st, f"health-{sid}.json")
try:
    s = json.load(open(f))
except Exception:
    s = {}
s.setdefault("n", 0)
s.setdefault("edits", {})
s.setdefault("recent", [])
s["n"] += 1
tool = d.get("tool_name") or ""
inp = d.get("tool_input") or {}
key = tool + " " + json.dumps(inp, sort_keys=True)[:300]
s["recent"] = (s["recent"] + [key])[-10:]
msgs = []
if s["recent"].count(key) == 3:
    msgs.append(f"Gate 3 health: the same {tool} call ran 3 times in the last 10 calls. Is a step repeating?")
path = inp.get("file_path")
if tool in ("Edit", "Write", "MultiEdit") and path:
    s["edits"][path] = s["edits"].get(path, 0) + 1
    c = s["edits"][path]
    if c % 3 == 0:
        msgs.append(f"Gate 3 repair loop: {os.path.basename(path)} edited {c}x. Re-read the error before editing again.")
json.dump(s, open(f, "w"))
if msgs:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": " ".join(msgs)}}))
