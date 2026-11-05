# dumbass-memory-mcp

Stdlib Python stdio MCP server (one file, `server.py`), 5 tools over 4 streams. No daemon, no network.

| Tool | Does |
| --- | --- |
| `memory.query` | search episodic claims (current scope), CRG nodes, graphify labels |
| `memory.record_claim` | store a claim in the branch shard, register its SHA-256 |
| `memory.ast_impact` | reverse-edge blast radius of a CRG node (depth, limit) |
| `memory.cas_verify` | hash file/text, check/register in ledger, compare `expect_sha256` |
| `memory.scope_status` | scope, shards, stream availability, ledger size |

Streams: 1 `code_review_graph.db` (read-only, `DUMBASS_CRG_DB`, default `<data>/code_review_graph.db` then `./.code-review-graph/graph.db`); 2 graphify `graph.json` (read-only, `DUMBASS_GRAPHIFY_JSON`, default `<data>/graphify_topology.json` then `./graphify-out/graph.json`); 3 `<data>/episodic_scopes/<repo>_<branch>.db` (WAL, busy_timeout 5000, scope `scope://<repo>/<branch>`, default from git or `DUMBASS_SCOPE`); 4 `<data>/sha256_cas.db`. Data dir: `DUMBASS_DATA_DIR`, default `~/.nvaex/memory`. Supabase mirror: off, not built in 0.1.0.

## Swap in / out
Add to a repo's `.mcp.json` (see `.mcp.json` here; replace the path with the absolute path of this folder):
```json
{
  "mcpServers": {
    "dumbass-memory": {
      "command": "python3",
      "args": ["-I", "<ABS_PATH_TO>/frankenstein/mcp/dumbass-memory-mcp/server.py"],
      "env": { "DUMBASS_DATA_DIR": "~/.nvaex/memory" }
    }
  }
}
```
Or: `claude mcp add dumbass-memory -- python3 -I <abs>/server.py`. Swap out: delete the entry (`claude mcp remove dumbass-memory`). Self-contained, depends on no other package.

## Hooks and kill switches
No hooks. Kill switch: if `~/.nvaex-hooks-off` or `~/.claude/state/off/dumbass-memory-mcp` exists, every tool returns `{"disabled": ...}` and touches nothing. Revoke by removing the file.

## Tested on device
`bash tests/selftest.sh` (Termux, arm64, Python 3.14, real stdio round trip with fixtures, plus the real CRG db read-only):
```
PASS initialize
PASS tools/list has 5 tools
PASS record_claim returns sha256
PASS query hits all 3 streams
PASS ast_impact walks callers to depth 2
PASS cas_verify match + register
PASS cas ledger remembers
PASS claim registered in ledger
PASS scope_status counts
PASS shard is WAL
PASS clean exit on EOF
PASS kill switch disables tools
PASS real CRG db read-only query
SELFTEST OK
```

## Install
```
/plugin install dumbass-memory-mcp --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install dumbass-memory-mcp@novaexopia`. Swap out: `claude plugin disable dumbass-memory-mcp@novaexopia`.
