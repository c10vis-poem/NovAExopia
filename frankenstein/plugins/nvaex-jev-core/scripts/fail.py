#!/usr/bin/env python3
"""PostToolUseFailure(Bash): date-aware nudge to research before patching. At most once per 10 minutes per session."""
import json, os, sys, time, datetime
d = json.load(sys.stdin)
if d.get("tool_name") != "Bash":
    sys.exit(0)
st = os.path.expanduser("~/.claude/state/nvaex-jev-core"); os.makedirs(st, exist_ok=True)
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
