---
description: Freeze claims so later sessions treat them as settled
argument-hint: "[claim text]"
allowed-tools: Bash(python3:*)
---
If arguments were given, run: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vnext.py" freeze --text "$ARGUMENTS"
Otherwise pick the settled decisions and constraints from this conversation (one per line, max 8), pipe them to python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vnext.py" freeze, and show the operator what was frozen.
