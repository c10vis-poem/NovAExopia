#!/usr/bin/env python3
"""PostToolUseFailure(Bash): date-aware nudge to research before patching. At most once per 10 minutes per session."""
import json, os, sys, time, datetime
try:
    d = json.load(sys.stdin)
    assert isinstance(d, dict)
except Exception:
    sys.exit(0)  # empty or bad input: nothing to do, nothing on the owner's screen (2026-11-12)
# Harmless exits are not failures: exit 1 from a search with no match or a compare with differences.
_cmd = ((d.get("tool_input") or {}).get("command") or "").strip()
_first = os.path.basename(_cmd.split()[0]) if _cmd else ""
if "Exit code 1" in str(d.get("error") or "")[:40] and _first in ("grep", "egrep", "fgrep", "rg", "diff", "cmp", "test", "["):
    sys.exit(0)
st = os.path.expanduser("~/.claude/state/nvaex-jev-core"); os.makedirs(st, exist_ok=True)
# Count every real failure (any tool) for Gate 3: health.py calls an edit a repair only when a failure came first.
_n = os.path.join(st, "fails-%s.n" % d.get("session_id", "x"))
try:
    _c = int(open(_n).read())
except Exception:
    _c = 0
open(_n, "w").write(str(_c + 1))
if d.get("tool_name") != "Bash":
    sys.exit(0)
f = os.path.join(st, "fail-%s.t" % d.get("session_id", "x"))
try:
    if time.time() - float(open(f).read()) < 600:
        sys.exit(0)
except Exception:
    pass
open(f, "w").write(str(time.time()))
cmd = ((d.get("tool_input") or {}).get("command") or "")[:120]
err = str(d.get("error") or "")[:160]
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUseFailure", "additionalContext":
    f"research-on-failure: today is {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d}. `{cmd}` failed ({err}). "
    "Your remembered fix may be stale: check the installed version and search current dated sources "
    "(claw.search or WebSearch) before patching. Prefer the durable fix; label a quick patch a stop-gap."}}))
