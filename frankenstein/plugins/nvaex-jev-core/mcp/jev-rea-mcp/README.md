# jev-rea-mcp

Stdlib-only Python stdio MCP server (boots in ~100 ms, no daemon). It ships inside `nvaex-jev-core`: installing that plugin starts it through the plugin's `.mcp.json`. Five tools:

| Tool | What |
|---|---|
| `jev.route_task` | task text -> level L0-L3, domain groups, model tier, skills. Calls `scripts/jev_route.py`, the router the hook uses: TypeSafe Jev, with keyword rules as fallback. `source` is `typesafe` or `local-fallback`, `error` is the reason. See the plugin README, Routing |
| `jev.audit_gate` | 5-gate checklist (spec, dry-run, health, verification, handoff); reports missing evidence; never blocks |
| `rea.inspect_target` | read-only repo/dir summary (extensions, manifests, entrypoints, sensitive-looking filenames, git HEAD) |
| `jev.remember` | local project memory, replaces the jevmem CLI (no network, no key, no hosted API). `action=add` (text, tags, project) or `action=recall` (query, tags, project, limit). Append-only JSONL, file mode 0600; secret shapes redacted on add; exact duplicates not stored twice; recall ranks by word overlap (tags weigh double), newest first |
| `ag.cloud_dispatch` | writes a job file to `$JEV_JOBS_DIR` (default `~/.claude/state/jev-rea-mcp/jobs`); POSTs only if `JEV_AG_BRIDGE_URL` is set and `send=true` |

## Swap in / out
`claude plugin enable|disable nvaex-jev-core@novaexopia`. The server needs nothing outside the plugin folder.

## Hooks / kill switch
The server has no hooks of its own. Disabling the plugin is the off switch. `~/.claude/state/off/nvaex-jev-core.typesafe` stops the Jev call only.

## Config
`JEV_TAXONOMY_CSV` (default `skills/jev-router/taxonomy.csv`), `JEV_JOBS_DIR`, `JEV_AG_BRIDGE_URL` (unset = never contacts cloud), `JEV_TIERS_JSON` (default `skills/jev-router/tiers.json`), `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`, `JEV_MEMORY_DIR` (default `~/.nvaex/jev-memory`; `~` and `$VARS` expanded; read at call time, so nothing is created at import and a recall on a missing dir creates nothing; the dir and `memory.jsonl` appear on the first add).

Migrating from jevmem: its `JEVMEM.md` lines are not imported. Add them with `jev.remember`; jevmem's guard, always-on rules and audit have no equivalent here.

## Tested on device
`bash tests/selftest.sh` (Termux, Python 3.14, isolated HOME and cwd), real stdio round trip: initialize, tools/list (5), every tool/call, plus jev.remember add/recall/duplicate/redaction/tilde/default-dir/nothing-in-cwd. With no key, so `jev.route_task` runs the fallback here; its Jev path is tested in the plugin selftest. See SOURCES.md for missing parts.
