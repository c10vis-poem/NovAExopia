#!/usr/bin/env python3
"""PreToolUse(Skill): nudge, never block, when a skill is on the project's confirm list (<project>/.claude/skill-gate.json)."""
import json, os, sys
d = json.load(sys.stdin)
name = (d.get("tool_input") or {}).get("skill") or (d.get("tool_input") or {}).get("name") or ""
try:
    c = json.load(open(os.path.join(d.get("cwd") or os.getcwd(), ".claude/skill-gate.json")))
except Exception:
    sys.exit(0)
if c.get("mode") == "off" or name not in c.get("blocked", []):
    sys.exit(0)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
    f"Skill '{name}' is on this project's confirm list. Ask the user yes/no (or an alternative) before using it. "
    "Turn off: mode \"off\" in .claude/skill-gate.json."}}))
