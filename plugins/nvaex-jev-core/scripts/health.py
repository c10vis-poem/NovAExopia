#!/usr/bin/env python3
"""PostToolUse: Gate 3 (execution health). Non-blocking. Speaks only when something actually repeats:
- the same call (tool + input) three times within the last 10 calls: "Is a step repeating?";
- a repair loop: a file edited 3, 6, 9 ... times in a row, each edit right after a failed call (fail.py counts
  failures). An edit with no failure before it is ordinary work and resets the count. Said once, on that edit."""
import hashlib, json, os, sys
try:
    d = json.load(sys.stdin)
    assert isinstance(d, dict)
except Exception:
    sys.exit(0)  # empty or bad input: nothing to do, nothing on the owner's screen (2026-11-12)
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
# The whole input decides "the same call": target first, then a hash of everything. It used to be the first 300
# characters of the sorted JSON, where "content" comes before "file_path", so the same text written to four files
# looked like one call repeated (2026-11-12).
target = inp.get("file_path") or inp.get("command") or inp.get("path") or inp.get("url") or inp.get("skill") or ""
key = f"{tool} {target} {hashlib.sha256(json.dumps(inp, sort_keys=True).encode()).hexdigest()[:16]}"
s["recent"] = (s["recent"] + [key])[-10:]
msgs = []
if s["recent"].count(key) == 3:
    msgs.append(f"Gate 3 health: the same {tool} call ran 3 times in the last 10 calls. Is a step repeating?")
try:
    nf = int(open(os.path.join(st, f"fails-{sid}.n")).read())
except Exception:
    nf = 0
path = inp.get("file_path")
if tool in ("Edit", "Write", "MultiEdit") and path:
    failed_first = nf > s.get("nf_prev", 0)
    c = s["edits"].get(path, 0) + 1 if failed_first else 0
    s["edits"][path] = c
    if c and c % 3 == 0:
        msgs.append(f"Gate 3 repair loop: {os.path.basename(path)} edited {c}x, each right after a failed call. "
                    "Re-read the error before editing again.")
s["nf_prev"] = nf
tmp = f"{f}.{os.getpid()}.tmp"  # write then rename: two hooks at once never leave a half-written file
with open(tmp, "w") as fh:
    json.dump(s, fh)
os.replace(tmp, f)
if msgs:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": " ".join(msgs)}}))
