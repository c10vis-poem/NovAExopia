# dumbass-memory-mcp

Stdlib Python stdio MCP server (one file, `server.py`), the memory tools of `nvaex-memory`. 12 tools: 5 over 4 streams, 7 that run `scripts/memory.py`. No daemon, no network.

| Tool | Does |
| --- | --- |
| `memory.query` | search episodic claims (current scope), CRG nodes, graphify labels |
| `memory.record_claim` | store a claim in the branch shard, register its SHA-256 |
| `memory.ast_impact` | reverse-edge blast radius of a CRG node (depth, limit) |
| `memory.cas_verify` | hash file/text, check/register in ledger, compare `expect_sha256` |
| `memory.scope_status` | scope, shards, stream availability, ledger size |
| `memory.snapshot` | the continuity text the SessionStart hook injects; writes nothing |
| `memory.freeze` | lock settled project claims: `action=add` (text), `list`, `unfreeze` (id) |
| `memory.task` | active task state: `action=add` (name), `patch` (object, null deletes a key), `state`, `done` |
| `memory.recap` | transcript to the daily recap file, rolls finished weeks; `written=null` means nothing new |
| `memory.export` | transcript to readable text under state (redacted, 0600); returns the file |
| `memory.map` | write tiered MAP.md routers (path, depth, force) |
| `memory.lint` | check anchored ledgers; drift comes back as `findings`, not as an error |

The last 7 hold no logic: each runs `../../scripts/memory.py`, the same script the hooks run. They take `cwd` (the project folder) because the server's own working folder may not be the project. `nudge` and the hook entries stay hooks and are not tools.

`memory.record_claim` and `memory.freeze` do different jobs: record_claim logs a searchable claim on one branch; freeze locks a settled claim for the whole project, and every later session sees it at start.

Streams: 1 `code_review_graph.db` (read-only, `DUMBASS_CRG_DB`, default `<data>/code_review_graph.db` then `./.code-review-graph/graph.db`); 2 graphify `graph.json` (read-only, `DUMBASS_GRAPHIFY_JSON`, default `<data>/graphify_topology.json` then `./graphify-out/graph.json`); 3 `<data>/episodic_scopes/<repo>_<branch>.db` (WAL, busy_timeout 5000, scope `scope://<repo>/<branch>`, default from git or `DUMBASS_SCOPE`); 4 `<data>/sha256_cas.db`. Data dir: `DUMBASS_DATA_DIR`, default `~/.nvaex/memory`. Supabase mirror: off, not built in 0.1.0.

## Swap in / out
Ships inside `nvaex-memory`, beside the skills that use it. Installing that plugin starts it through the plugin's `.mcp.json`; `claude plugin enable|disable nvaex-memory@novaexopia` swaps it. It is no longer a plugin of its own.

## Hooks and kill switches
The server has no hooks; the package's are in its README. Kill switch: if `~/.nvaex-hooks-off`, `~/.claude/state/off/dumbass-memory-mcp` or `~/.claude/state/off/nvaex-memory` exists, every tool returns `{"disabled": ...}` and touches nothing. Revoke by removing the file.

## Tested on device
`bash tests/selftest.sh` (Termux, arm64, Python 3.14, real stdio round trip with fixtures, plus the real CRG db read-only):
```
PASS initialize
PASS tools/list has the 5 stream tools + 7 memory.py tools, no nudge
PASS record_claim returns sha256
PASS query hits all 3 streams
PASS ast_impact walks callers to depth 2
PASS cas_verify match + register
PASS cas ledger remembers
PASS claim registered in ledger
PASS scope_status counts
PASS shard is WAL
PASS freeze stores a claim
PASS freeze wrote where memory.py writes it
PASS freeze list shows it
PASS task add + patch
PASS task over cap is a tool error with the reason
PASS snapshot returns frozen claim + active task
PASS task done
PASS unfreeze removes it
PASS snapshot empty when nothing to inject
PASS recap writes the daily file, secret redacted
PASS recap once per session
PASS recap with no transcript is a tool error
PASS export writes redacted 0600 file
PASS map writes MAP.md
PASS lint finds drift (drift is a result, not an error)
PASS lint clean on ledgers with no drift
PASS server copies no memory.py logic
PASS clean exit on EOF
PASS kill switch disables tools
PASS package off switch disables tools
PASS real CRG db read-only query
SELFTEST OK
```
