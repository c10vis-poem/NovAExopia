#!/usr/bin/env sh
# SubagentStop for corpus-ingest only. The one blocking hook (spec: worker may not stop with
# unchecked plan steps). Block message names override + revoke. Fails open.
R="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
sh "$R/scripts/killswitch.sh" nvaex-wiki-admin stop-gate && exit 0
exec bash "$R/scripts/worker-stop-gate.sh" || exit 0
