# nvaex-memory-vnext

Unified memory-as-skill. Replaces memory daemons with files and three tiny hooks. Stdlib Python + the copied ccfind (Node).

| Piece | What it does |
|---|---|
| anchor-memory | `@meta` anchors in memory/decisions.md / FACTS.md; drift linter (`vnext.py lint`) |
| continuity | SessionStart snapshot (<=60 lines: frozen claims, recent .whydone, drift) + `/nvaex-memory-vnext:freeze` |
| whydone | nudge-only Stop hook (once per session, repos with a `.whydone/` dir only) + log skill |
| memory-agent | SessionEnd: appends prompts + last answer to `NvAEx-Recaps/memory/YYYY-MM-DD.md` and `layers.jsonl`, `autoPromote: false` |
| ccfind | BM25 search over past sessions (`skills/ccfind`) |
| create-smartfolder | `vnext.py map <dir>` writes tiered MAP.md routers |
| cut-weight | archive-not-delete repo cleanup (SHA-256 manifest) |

## Swap in / out
```
claude plugin enable  nvaex-memory-vnext@novaexopia
claude plugin disable nvaex-memory-vnext@novaexopia
```
Works with any other Frankenstein package disabled. Nothing else to change.

## Hooks and kill switches (one entry per event, all fail open, none block)
| Event | Hook name | Does |
|---|---|---|
| SessionStart | `session-start` | snapshot + drift lint |
| Stop | `stop` | whydone nudge (systemMessage only) |
| SessionEnd | `session-end` | daily recap |

Off for everything: `touch ~/.nvaex-hooks-off`. Off for this package: `touch ~/.claude/state/off/nvaex-memory-vnext`. One hook: `touch ~/.claude/state/off/nvaex-memory-vnext.<hook-name>`. Remove the file to turn back on.

## Paths
Recaps repo: `$NVAEX_RECAPS` or `config.json` `recaps` (default `~/repos/NvAEx-Recaps`); writes under `memory/`. If the repo is missing it falls back to `~/.claude/state/nvaex-memory-vnext/memory/`. It never commits or pushes: that is the operator's step. Frozen claims: `<recaps>/memory/continuity/<project>.claims.jsonl`.

## Tested on device
`bash tests/selftest.sh` (Termux, Android arm64; temp dirs only):
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
PASS killswitch off via file
PASS killswitch on by default
PASS hook command runs through killswitch (off => silent)
PASS hook command runs (on => nudge)
PASS ccfind finds session
PASS cut-weight inventory runs
SELFTEST PASS
```

## Install
```
/plugin install nvaex-memory-vnext --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-memory-vnext@novaexopia`. Swap out: `claude plugin disable nvaex-memory-vnext@novaexopia`.
