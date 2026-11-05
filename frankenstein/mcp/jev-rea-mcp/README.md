# jev-rea-mcp

Stdlib-only Python stdio MCP server (boots in ~100 ms, no daemon, no network by default). Five tools:

| Tool | What |
|---|---|
| `jev.route_task` | task text -> level L0-L3 + domain groups (taxonomy CSV if present, else built-in rules) + model tier from `data/tiers.json` (haiku-5-5 / sonnet-5-5 / opus-5-5 / fable-5-1) |
| `jev.audit_gate` | 5-gate checklist (spec, dry-run, health, verification, handoff); reports missing evidence; never blocks |
| `rea.inspect_target` | read-only repo/dir summary (extensions, manifests, entrypoints, sensitive-looking filenames, git HEAD) |
| `jev.remember` | local project memory, replaces the jevmem CLI (no network, no key, no hosted API). `action=add` (text, tags, project) or `action=recall` (query, tags, project, limit). Append-only JSONL, file mode 0600; secret shapes redacted on add; exact duplicates not stored twice; recall ranks by word overlap (tags weigh double), newest first |
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
`JEV_TAXONOMY_CSV` (default `data/taxonomy.csv`), `JEV_JOBS_DIR`, `JEV_AG_BRIDGE_URL` (unset = never contacts cloud), `JEV_TIERS_JSON` (default `data/tiers.json`, a copy of `nvaex-jev-core/skills/jev-router/tiers.json`; the selftest fails if the two differ), `JEV_MEMORY_DIR` (default `~/.nvaex/jev-memory`; `~` and `$VARS` expanded; read at call time, so nothing is created at import and a recall on a missing dir creates nothing; the dir and `memory.jsonl` appear on the first add).

Migrating from jevmem: its `JEVMEM.md` lines are not imported. Add them with `jev.remember`; jevmem's guard, always-on rules and audit have no equivalent here.

## Tested on device
`sh tests/selftest.sh` (Termux, Python 3.14, isolated HOME and cwd), real stdio round trip: initialize, tools/list (5), every tool/call, plus jev.remember add/recall/duplicate/redaction/tilde/default-dir/nothing-in-cwd.
```
PASS import creates nothing
PASS recall on missing dir creates nothing
PASS default data dir is ~/.nvaex/jev-memory
PASS data/tiers.json matches nvaex-jev-core copy
PASS initialize
PASS tools/list 5 tools
PASS route_task L3
PASS audit_gate incomplete, non-blocking
PASS inspect_target read-only sees server.py
PASS cloud_dispatch writes job, does not send
PASS route_task L3 -> fable tier
PASS route_task plan -> fable
PASS remember: recall on empty store is empty
PASS remember add: stored, secret redacted
PASS remember add: tilde expanded to HOME
PASS remember add: duplicate not stored twice
PASS remember recall: query + project match
PASS remember recall: tag filter
PASS remember recall: no match is empty
PASS remember add: empty text is an error
PASS remember: file mode 0600, one line per add
PASS remember: nothing written to cwd
round-trip ms: 111
SELFTEST OK
```
See SOURCES.md for missing parts.

## Install
```
/plugin install jev-rea-mcp --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install jev-rea-mcp@novaexopia`. Swap out: `claude plugin disable jev-rea-mcp@novaexopia`.
