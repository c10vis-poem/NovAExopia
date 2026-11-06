# nvaex-burn

Lean usage pacer: one stdlib script (`scripts/burn.py`, ~190 lines), one small MCP server, no daemons.

- **Brake:** >=90% of the 5h window or >=95% of the 7d window. Sets a brake flag, halts job dispatch, and the prompt hook tells Claude to run `/nvaex-burn:sweep` (checkpoint).
- **Burn:** <=72h to weekly reset and >=25% unused. Runs one pre-approved job per `tick` from `burn-queue.md`: Smoulder (<=72h), Blaze (<=24h), Inferno (<=6h). A job runs once its tier window is open.
- **Keep-alive:** `burn.py keepalive` pings every 4m30s only while a prompt was seen in the last 30 min, then exits. Ping is `BURN_PING_CMD`; unset means log-only.
- **Notify:** POST JSON `{"text":...}` to `BURN_WEBHOOK_URL`. Off unless set.
- **Usage source is pluggable:** default reads `~/.claude/state/nvaex-burn/usage.json` (to be written by the operator's custom usage display; heavy-usage is removed); or set `BURN_USAGE_CMD` to a command printing `{"five_hour":{"used_percentage":N,"resets_at":epoch},"seven_day":{...}}`. No source, or a reading older than 30 min, means `unknown`: nothing burns, nothing brakes.

## MCP server (`mcp/burn-mcp`)
Stdlib, thin: each tool runs a script in `scripts/`. Stdio only, starts with the plugin through `.mcp.json`.

| Tool | Does |
|---|---|
| `burn.status` | mode (unknown, brake, burn, idle) and why. Runs `burn.py status` |
| `burn.keepalive` | one ping if a prompt was seen in the last 30 min. Runs `burn.py keepalive --once`; the looping form stays a command because it would hang a tool call |
| `burn.notify` | message to `BURN_WEBHOOK_URL`, off if unset. Runs `burn.py notify` |
| `ag.cloud_dispatch` | writes a job file to `AG_JOBS_DIR` (default `~/.claude/state/nvaex-burn/jobs`); POSTs it only if `AG_BRIDGE_URL` is set and `send=true`. Runs `scripts/cloud_dispatch.py` |

`hook` and `tick` are not tools: the hook fires on an event, and `tick` runs queued jobs as an explicit command. Kill switch: under `~/.nvaex-hooks-off`, `~/.claude/state/off/nvaex-burn` or `nvaex-burn.mcp`, every tool returns `{"disabled": ...}` and runs nothing.

`ag.cloud_dispatch` moved here from the JEV server. It is job dispatch, and this package is the one that handles job queues and budget; it has the same "POST only when the env var is set" shape as `burn.py notify`, and being Python it moved unchanged. No `AG_*` variable or job folder existed on this phone when it moved (the old names were `JEV_AG_BRIDGE_URL`, `JEV_JOBS_DIR`).

## Queue format (read only; the vault is never written)
`BURN_QUEUE` (default `~/storage/shared/Documents/NovAExorpus/burn-queue.md`):
```
- [x] smoulder | wiki-lint | python3 /path/job.py
- [ ] blaze | not-approved | never runs
```
`[x]` = pre-approved. Done ids are kept in `~/.claude/state/nvaex-burn/done`, not in the queue. Dispatch is explicit: `python3 scripts/burn.py tick` (use `--dry-run` first).

## Swap in / out
```
claude plugin enable nvaex-burn@novaexopia
claude plugin disable nvaex-burn@novaexopia
```
Self-contained; works with any other package disabled.

## Hooks and kill switches
One hook: `UserPromptSubmit` (stamps activity, injects brake notice; never blocks, fails open). Off if any exists:
- `~/.nvaex-hooks-off`
- `~/.claude/state/off/nvaex-burn`
- `~/.claude/state/off/nvaex-burn.userpromptsubmit`

Env: `BURN_QUEUE`, `BURN_USAGE_FILE`, `BURN_USAGE_CMD`, `BURN_WEBHOOK_URL`, `BURN_PING_CMD`, `BURN_STATE`, `BURN_CHECKPOINT_DIR`, `AG_JOBS_DIR`, `AG_BRIDGE_URL`.

## Tested on device
`bash tests/selftest.sh` (Termux, Android arm64, python3 stdlib, local webhook receiver, runs the registered hook command through the kill switch). Output tail:
```
PASS hook exits 0 on garbage stdin
PASS exactly one hook entry
PASS killswitch runs before burn.py
PASS hook silent under switch .nvaex-hooks-off
PASS hook silent under switch nvaex-burn
PASS hook silent under switch nvaex-burn.userpromptsubmit
PASS killswitch off by default
PASS default usage path
PASS no stale heavy-usage path
PASS notify LICENSE kept
PASS manifests parse
PASS burn-mcp selftest: 16 checks
PASS .mcp.json names burn-mcp
SELFTEST PASS
```
Not tested: a real usage source (none wired), a real keep-alive ping command, the hook inside a live Claude session. No `/burn` command file: the `burn` skill covers it.

## Install
```
/plugin install nvaex-burn --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-burn@novaexopia`. Swap out: `claude plugin disable nvaex-burn@novaexopia`.
