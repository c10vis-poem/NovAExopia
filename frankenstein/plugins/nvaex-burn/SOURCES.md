# Sources

No upstream file was copied verbatim. Logic and constants were re-derived (not copied) into `scripts/burn.py`; the only copied files are the shared kill switch and the notify LICENSE.

| Package file | Origin | Upstream | License |
|---|---|---|---|
| licenses/notify.LICENSE | notify 0.1.0 LICENSE (MIT), kept for the derived webhook POST | dz1922 | MIT |
| scripts/killswitch.sh | frankenstein/shared/killswitch.sh | this repo | n/a |
| burn.py tier table (72h/24h/6h), 25% min unused, `assess()` idea | burn-baby-burn 0.3.0 `hooks.off-20261028/burn.ts` (synced c612c9ee...) | Mehdi / eel-brah | MIT |
| burn.py brake thresholds (90% 5h, 95% 7d), usage-live.json format, `/sweep` idea | heavy-usage 1.3.1 thresholds and `skills/sweep` idea (synced 619aabc9...); plugin itself removed, default usage file moved to `~/.claude/state/nvaex-burn/usage.json` | Heavy C Development Studio LLC | MIT |
| burn.py keep-alive cadence and active-only rule | cache-caffeine 0.12.2 README/`wake.ts` (synced 271e15b5...) | Luis Perez Morales | MIT |
| burn.py webhook POST (JSON) | notify 0.1.0 `hooks.off-20261028/notify.sh` (synced 0e5ea5c6...) | dz1922 | MIT |

Dropped on purpose: the 5-agent planner, quotes/toasts/mod UI (burn-baby-burn), statusLine chaining and sweep engine/scouts (heavy-usage), the `wake.ts` limit-reset scheduler, Slack/Teams/Lark/Telegram/desktop channels (notify), all `.tsx` mod code.

## Moved in from this repo
| Path here | From | Note |
|---|---|---|
| scripts/cloud_dispatch.py | `nvaex-jev-core/mcp/jev-rea-mcp/server.py` `dispatch()` (spec "ag.cloud_dispatch") | moved, env names and default job folder changed |
| mcp/burn-mcp/ | written here | custom-first; no donor code |

## Missing
- ag-bridge.sh (Antigravity GCP Cloud Run bridge): not found. `ag.cloud_dispatch` only writes job files unless `AG_BRIDGE_URL` is set.
- `Claude-Trinity` / `code-janitor` cleanup recipes: not found on the phone (searched ~/.claude/plugins/{synced,cache,store}, ~/local-plugins, ~/repos by name). Not invented. Queue jobs can call any command, so a janitor sweep can be added as a queue line once the part exists.
- `NovAExorpus/burn-queue.md`: does not exist yet on the device (probed the vault path). The reader treats a missing queue as empty.
- A live usage source: `~/.claude/state/nvaex-burn/usage.json` is absent (the operator's custom usage display will write it). Status reports `unknown` and nothing burns until a source exists.

## Sizes (FOLD-MAP row: notify)
- notify source folder: 104KB before; taken: the POST idea only (~10 lines in burn.py) plus LICENSE (1KB). Slack/Teams/Lark/Telegram/desktop dropped.
- Package: 76KB before (10 files) -> bytes after: see README; commands/burn.md removed (duplicate of skill), licenses/ added.
