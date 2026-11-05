# Sources
Custom-first: no third-party code copied. `server.py` is written new against the spec (Section 4B, server 2).

## Read, not copied (data formats the server consumes)
| Part | Where read | Use |
| --- | --- | --- |
| code-review-graph `graph.db` schema (`nodes`, `edges`) | `~/repos/NovA-code-review-graph/.code-review-graph/graph.db` (schema v13 era) | Stream 1, opened read-only |
| graphify `graph.json` (node-link: `nodes[].label/community/source_file`) | `~/ARCHIVE-2026-10-31/home/graphify-self-graph/graph.json` | Stream 2, loaded read-only |

## Missing
- Supabase / OB1 pgvector mirror (Stream 4 cloud half): optional, off by default, not built in 0.1.0. No OB1 schema file read on this phone this session.
- `graphify_topology.db`: graphify emits `graph.json`, not a SQLite db on this phone; server reads the JSON (`DUMBASS_GRAPHIFY_JSON`).
- Argon rulings docs 03/05/06 (linked in spec) not on device; streams follow the blueprint text only.
