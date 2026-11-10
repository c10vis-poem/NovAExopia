#!/usr/bin/env python3
"""PostToolUse: Gate 3 (execution health). Every 5 tool calls print a checkpoint; flag repeat edits. Non-blocking."""
import json, os, sys
d = json.load(sys.stdin)
sid = d.get("session_id", "x")
st = os.path.expanduser("~/.claude/state/nvaex-jev-core")
os.makedirs(st, exist_ok=True)
f = os.path.join(st, f"health-{sid}.json")
try:
    s = json.load(open(f))
except Exception:
    s = {"n": 0, "edits": {}}
s["n"] += 1
inp = d.get("tool_input") or {}
path = inp.get("file_path")
if d.get("tool_name") in ("Edit", "Write", "MultiEdit") and path:
    s["edits"][path] = s["edits"].get(path, 0) + 1
msgs = []
if s["n"] % 5 == 0:
    msgs.append(f"Gate 3 health: {s['n']} tool calls. One line: on plan, or off? Is a step repeating?")
loops = [p for p, c in s["edits"].items() if c >= 3 and c % 3 == 0]
if loops:
    msgs.append("Gate 3 repair loop: " + os.path.basename(loops[0]) + f" edited {s['edits'][loops[0]]}x. Re-read the error before editing again.")
json.dump(s, open(f, "w"))
if msgs:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": " ".join(msgs)}}))
