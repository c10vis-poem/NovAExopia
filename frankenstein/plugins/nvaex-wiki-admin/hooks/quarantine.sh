#!/usr/bin/env sh
# PostToolUse(Read): flag injection-looking files as DATA. Never blocks, fails open.
R="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
sh "$R/scripts/killswitch.sh" nvaex-wiki-admin quarantine && exit 0
exec python3 "$R/scripts/wa_quarantine.py" --hook 2>/dev/null || exit 0
