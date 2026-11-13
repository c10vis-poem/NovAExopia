# nvaex-memory

Unified memory-as-skill. Files, four tiny hooks and one MCP server replace memory daemons. Stdlib Python plus the trimmed ccfind (Node). Parts and sizes: [SOURCES.md](SOURCES.md).

| Piece | What it does |
|---|---|
| anchor-memory | `@meta` anchors in memory/decisions.md / FACTS.md; drift linter (`memory.py lint`) |
| continuity | SessionStart snapshot (<=60 lines): frozen claims, active task state, branch handoff, recent .whydone, drift. `/nvaex-memory:freeze`; `memory.py task add\|patch\|state\|done` (4000-char cap) |
| handoff | per-branch note in `.git/handoffs/`, loaded on startup/clear, flagged STALE when HEAD moved; trunk branches never load |
| workstream | park ideas and per-workstream notes as plain files in NvAEx-Recaps |
| whydone | nudge-only Stop (once per session, repos with a `.whydone/` dir only) + log skill |
| memory-agent | SessionEnd: prompts + last answer to `memory/YYYY-MM-DD.md`, `layers.jsonl` (`autoPromote: false`); finished weeks roll into `memory/weekly/<week>.md`, dailies kept |
| PreCompact export | readable transcript copy in `~/.claude/state/nvaex-memory/exports/` (0600, last 20, secrets redacted) |
| after compaction | snapshot adds a resume checklist (goal, next, files, decisions, blockers, state) |
| patterns | proposal-only scan for recurring patterns; nothing written without approval |
| memory-bank | six-file `memory-bank/` structure, read at task start |
| ccfind | BM25 search over past sessions: index, search, show, stats |
| create-smartfolder | `memory.py map <dir>` writes tiered MAP.md routers |
| cut-weight | archive-not-delete repo cleanup (SHA-256 manifest) |
| `mcp/dumbass-memory-mcp` | MCP server, 12 tools: `memory.query`, `record_claim`, `ast_impact`, `cas_verify`, `scope_status`, plus `memory.snapshot`, `freeze`, `task`, `recap`, `export`, `map`, `lint`, which run `scripts/memory.py`. See its README |

## Swap in / out
```
claude plugin enable  nvaex-memory@novaexopia
claude plugin disable nvaex-memory@novaexopia
```
Works with any other Frankenstein package disabled.

## Hooks (one entry per event, all fail open, none block; no off switch: memory is never turned off)
| Event | Hook name | Does |
|---|---|---|
| SessionStart | `session-start` | snapshot |
| PreCompact | `pre-compact` | transcript export |
| Stop | `stop` | whydone nudge (systemMessage only) |
| SessionEnd | `session-end` | daily recap + weekly rollup |

There is no kill switch (owner, 2026-11-13: memory is never turned off). Each hook runs `scripts/memory.py` directly.

## Paths
Recaps repo: `$NVAEX_RECAPS` or `config.json` `recaps` (default `~/repos/NvAEx-Recaps`); writes under `memory/`. If the repo is missing it falls back to `~/.claude/state/nvaex-memory/memory/`. It never commits or pushes: that is the operator's step. Frozen claims: `<recaps>/memory/continuity/<project>.claims.jsonl`. Task state: `~/.claude/state/nvaex-memory/tasks/<project>.json`.

## Not folded
adaptive-agent (not on the phone), context-handoff manifest MCP, cco usage reports. See SOURCES.md "Missing".

## Tested on device
`bash tests/selftest.sh` (Termux, Android arm64; temp dirs only, never the real Recaps repo or ~/.claude/state):
```
PASS manifests parse
PASS one hook per event
PASS lint flags drift (exit 1)
PASS lint names stale-b
PASS freeze stored
PASS snapshot is SessionStart JSON
PASS snapshot <= 60 lines
PASS injection phrase filtered
PASS unfreeze works
PASS nudge emits systemMessage, no block
PASS nudge once per session
PASS nudge honours stop_hook_active
PASS daily recap written
PASS secret redacted
PASS layers.jsonl autoPromote false, one row
PASS MAP.md tiered
PASS hook command runs (nudge)
PASS ccfind finds session
PASS cut-weight inventory runs
PASS hooks = 4 events, one entry each, no kill switch
PASS branch note loaded at startup
PASS branch note flagged STALE after HEAD moves
PASS branch note not loaded on resume
PASS trunk branch never loads a note
PASS task patch sets and null deletes
PASS compact snapshot: active task + resume checklist
PASS task over cap rejected, state unchanged
PASS finished task not re-injected
PASS export wrote readable transcript, secret redacted
PASS export file is 0600
PASS weekly file for finished week
PASS dailies kept, current week not rolled
PASS rollup does not overwrite an existing week
PASS ccfind show prints the session
PASS ccfind stats works
PASS no skill references a missing file
PASS every skill has frontmatter name+description
PASS dumbass-memory-mcp selftest
     (30 checks in the server selftest)
PASS .mcp.json starts the server from inside this package
SELFTEST PASS
```

## Install
```
/plugin install nvaex-memory --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/NovAExopia-main` then `claude plugin install nvaex-memory@novaexopia`.
