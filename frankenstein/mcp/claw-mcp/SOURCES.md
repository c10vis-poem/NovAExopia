# SOURCES

## Copied
| path here | origin | version | license |
|---|---|---|---|
| bin/webview-connect | `NovAExopia` worktree `mcp_connectors/webview/bin/webview-connect` (own repo) | 2026-11-04 | repo license |
| bin/killswitch.sh | `frankenstein/shared/killswitch.sh` | - | repo license |

Used as reference, not copied: `mcp_connectors/webview/bin/webview-mcp` (CDP via adb forward :9222; claw.browser uses the same endpoint).

## Written new (custom first)
`python/claw_mcp.py`, `kotlin/**`, `bin/claw-mcp`, `bin/build-kotlin.sh`, `tests/selftest.sh`, `workflows.json`.

## Missing (not on the phone, not invented)
- Spec's "Device and browser toolkit architecture proposal.md" (Drive 1Drfd5mN9O1T4O8zM0qCEjjUebv9v342n): not read; tool arguments are my minimal guess from the 6 tool names.
- Kadb (Kotlin ADB lib), OkHttp driver code, Playwright/pplx/adb-mcp/claude-bridge/watch-video/use-gcloud/openrouter-mcp sources: not copied. `NovA-openrouter-mcp` exists in ~/repos but its multimodal Python server was not folded in.
- A search provider (claw.search): none wired.
