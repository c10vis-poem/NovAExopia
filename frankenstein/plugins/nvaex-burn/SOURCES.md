# Sources

No upstream file was copied verbatim. Logic and constants were re-derived (not copied) into `scripts/burn.py`; the only copied file is the shared kill switch.

| Package file | Origin | Upstream | License |
|---|---|---|---|
| scripts/killswitch.sh | frankenstein/shared/killswitch.sh | this repo | n/a |
| burn.py tier table (72h/24h/6h), 25% min unused, `assess()` idea | burn-baby-burn 0.3.0 `hooks.off-20261028/burn.ts` (synced c612c9ee...) | Mehdi / eel-brah | MIT |
| burn.py brake thresholds (90% 5h, 95% 7d), usage-live.json format, `/sweep` idea | heavy-usage 1.3.1 `scripts/usage-lib.js`, `usage-statusline.js`, `skills/sweep` (synced 619aabc9...) | Heavy C Development Studio LLC | MIT |
| burn.py keep-alive cadence and active-only rule | cache-caffeine 0.12.2 README/`wake.ts` (synced 271e15b5...) | Luis Perez Morales | MIT |
| burn.py webhook POST (JSON) | notify 0.1.0 `hooks.off-20261028/notify.sh` (synced 0e5ea5c6...) | dz1922 | MIT |

Dropped on purpose: the 5-agent planner, quotes/toasts/mod UI (burn-baby-burn), statusLine chaining and sweep engine/scouts (heavy-usage), the `wake.ts` limit-reset scheduler, Slack/Teams/Lark/Telegram/desktop channels (notify), all `.tsx` mod code.

## Missing
- `Claude-Trinity` / `code-janitor` cleanup recipes: not found on the phone (searched ~/.claude/plugins/{synced,cache,store}, ~/local-plugins, ~/repos by name). Not invented. Queue jobs can call any command, so a janitor sweep can be added as a queue line once the part exists.
- `NovAExorpus/burn-queue.md`: does not exist yet on the device (probed the vault path). The reader treats a missing queue as empty.
- A live usage source: `~/.claude/heavy-usage/usage-live.json` is absent (heavy-usage statusLine not wired). Status reports `unknown` and nothing burns until a source exists.
