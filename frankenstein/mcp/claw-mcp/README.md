# claw-mcp

One MCP server for device, browser, scrape, search and inference I/O: `claw.search`, `claw.scrape`, `claw.browser`, `claw.device`, `claw.infer`, `claw.workflows` (blueprint 4B, server 1). stdio only.

Two implementations, same 6 tool schemas; `bin/claw-mcp` picks the Kotlin jar if built, else the Python shim:

| | status | covers |
|---|---|---|
| `python/claw_mcp.py` (stdlib) | Tested on device | scrape, browser `version`/`tabs`, device (battery, wifi, notify, adb-devices), infer (openrouter, needs `OPENROUTER_API_KEY`), workflows. `claw.search` and CDP websocket actions return `isError` "not-implemented". |
| `kotlin/` (JVM, Gradle) | **Untested**: JDK 21 is on the phone, kotlinc/gradle are not | same drivers; embeddable (`Server.handle`) in AEthX-AEsc. Build: `sh bin/build-kotlin.sh` on a machine with gradle. |

## Swap in / out
Add to a repo's `.mcp.json` (swap out = delete the entry or `claude mcp remove claw`):
```json
{"mcpServers":{"claw":{"command":"sh","args":["<path-to>/frankenstein/mcp/claw-mcp/bin/claw-mcp"]}}}
```
(`sh`, not the script directly: Termux has no `/usr/bin/env`.) Per-repo scope via `.claude/harness-scope.json` (AEthX-AEsc loads claw-mcp).

## Hooks and kill switches
No hooks. The server itself honours the kill switch at start: `touch ~/.claude/state/off/claw-mcp` (or `claw-mcp.server`, or `~/.nvaex-hooks-off`) and it exits 0 offering no tools; remove the file to restore.

## Env
`CDP_PORT` (9222), `OPENROUTER_API_KEY`, `CLAW_WORKFLOWS` (path to workflows JSON: `{"name":[{"tool":"claw.device","arguments":{...}}]}`). `bin/webview-connect` brings up the adb forward to Chrome (see mcp_connectors/webview).

## Tested on device
`sh tests/selftest.sh` (Python shim, Termux arm64, 2026-11-04):
```
PASS initialize
PASS tools/list has the 6 tools
PASS tools/call claw.workflows list
PASS search reports not-implemented
PASS kill switch silences server
SELFTEST PASS
```
Also ran by hand: workflow `phone-status` returned real `termux-battery-status`; `claw.browser tabs` returned a clean `Connection refused` error with no adb link up.

## Install
```
/plugin install claw-mcp --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install claw-mcp@novaexopia`. Swap out: `claude plugin disable claw-mcp@novaexopia`.
