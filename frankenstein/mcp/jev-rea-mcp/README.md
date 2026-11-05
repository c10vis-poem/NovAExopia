# jev-rea-mcp

Stdlib-only Python stdio MCP server (boots in ~100 ms, no daemon, no network by default). Four tools:

| Tool | What |
|---|---|
| `jev.route_task` | task text -> level L0-L3 + domain groups (taxonomy CSV if present, else built-in rules) |
| `jev.audit_gate` | 5-gate checklist (spec, dry-run, health, verification, handoff); reports missing evidence; never blocks |
| `rea.inspect_target` | read-only repo/dir summary (extensions, manifests, entrypoints, sensitive-looking filenames, git HEAD) |
| `ag.cloud_dispatch` | writes a job file to `$JEV_JOBS_DIR` (default `~/.claude/state/jev-rea-mcp/jobs`); POSTs only if `JEV_AG_BRIDGE_URL` is set and `send=true` |

## Swap in / out
Add to a repo's `.mcp.json` (swap out = delete the entry):
```json
{"mcpServers":{"jev-rea-mcp":{"command":"python3","args":["-I","/ABS/PATH/TO/NovAExopia/frankenstein/mcp/jev-rea-mcp/server.py"]}}}
```
The bundled `.mcp.json` uses `${CLAUDE_PLUGIN_ROOT}` for when the folder is loaded via the marketplace entry. Depends on no other package.

## Hooks / kill switch
No hooks registered, so nothing to switch off. Removing the `.mcp.json` entry is the off switch.

## Config
`JEV_TAXONOMY_CSV` (default `data/taxonomy.csv`), `JEV_JOBS_DIR`, `JEV_AG_BRIDGE_URL` (unset = never contacts cloud).

## Tested on device
`sh tests/selftest.sh` (Termux, Python 3.14), real stdio round trip: initialize, tools/list, all four tools/call.
```
PASS initialize
PASS tools/list 4 tools
PASS route_task L3
PASS audit_gate incomplete, non-blocking
PASS inspect_target read-only sees server.py
PASS cloud_dispatch writes job, does not send
round-trip ms: 108
SELFTEST OK
```
See SOURCES.md for missing parts.

## Install
```
/plugin install jev-rea-mcp --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install jev-rea-mcp@novaexopia`. Swap out: `claude plugin disable jev-rea-mcp@novaexopia`.
