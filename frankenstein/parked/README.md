# Parked: emptied 2026-11-05

Everything that was parked from `nvaex-ops` has been rebuilt as our own code and the parked copies were removed. Nothing remains here except `dumbass-memory-mcp.plugin.json`, added 2026-11-06: the manifest from when that server was its own plugin. The server now ships inside `nvaex-memory`, so nothing reads this file.

| was parked | now |
|---|---|
| google-setup, google-reauth, google-add-account | `plugins/nvaex-ops/skills/google-setup` (+ `scripts/google_oauth.py`, loopback OAuth for claw-mcp's token files) |
| local-whisper | `skills/local-whisper` (+ `scripts/transcribe.sh`, Parakeet in proot) |
| tts | `skills/tts` (+ `scripts/speak.sh`) |
| skill-inventory | `skills/skill-inventory` (+ `scripts/inventory.py`) |
| kotlin-lsp | `skills/kotlin-lsp` (+ `scripts/kt_check.py`; no language server exists on this phone) |
| mcp-tunnel | `skills/mcp-tunnel` (+ `scripts/tunnel.sh`; needs `cloudflared`, absent: stops) |
| harness-setup, harness-audit | `skills/harness-setup`, `skills/harness-audit` (+ `stack_scan.py`, `config_audit.py`) |
| office-files | `skills/office-files` (+ `scripts/office.py`) |

No stock plugin, third-party MCP server or donor text is used by the rebuilt items. Per-item test status is in `plugins/nvaex-ops/README.md`.
