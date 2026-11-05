# nvaex-burn

Lean usage pacer: one stdlib script (`scripts/burn.py`, ~190 lines), no daemons.

- **Brake:** >=90% of the 5h window or >=95% of the 7d window. Sets a brake flag, halts job dispatch, and the prompt hook tells Claude to run `/nvaex-burn:sweep` (checkpoint).
- **Burn:** <=72h to weekly reset and >=25% unused. Runs one pre-approved job per `tick` from `burn-queue.md`: Smoulder (<=72h), Blaze (<=24h), Inferno (<=6h). A job runs once its tier window is open.
- **Keep-alive:** `burn.py keepalive` pings every 4m30s only while a prompt was seen in the last 30 min, then exits. Ping is `BURN_PING_CMD`; unset means log-only.
- **Notify:** POST JSON `{"text":...}` to `BURN_WEBHOOK_URL`. Off unless set.
- **Usage source is pluggable:** default reads `~/.claude/heavy-usage/usage-live.json` (heavy-usage statusLine capture); or set `BURN_USAGE_CMD` to a command printing `{"five_hour":{"used_percentage":N,"resets_at":epoch},"seven_day":{...}}`. No source, or a reading older than 30 min, means `unknown`: nothing burns, nothing brakes.

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

Env: `BURN_QUEUE`, `BURN_USAGE_FILE`, `BURN_USAGE_CMD`, `BURN_WEBHOOK_URL`, `BURN_PING_CMD`, `BURN_STATE`, `BURN_CHECKPOINT_DIR`.

## Tested on device
`bash tests/selftest.sh` (Termux, Android arm64, python3 stdlib, local webhook receiver). `claude plugin validate .` passed.
```
PASS no usage source -> unknown
PASS unknown burns nothing
PASS 5h>=90 -> brake
PASS 7d>=95 -> brake
PASS >72h -> idle
PASS 60h, 50% left -> burn
PASS <25% unused -> idle
PASS dry-run runs nothing
PASS approved smoulder job ran
PASS blaze not yet / unapproved never
PASS blaze runs at 10h
PASS [ ] job never runs
PASS brake sets flag, spawns nothing
PASS hook injects sweep under brake
PASS hook silent when no brake
PASS brake clears
PASS idle session: no ping
PASS active session: ping
PASS notify off by default
PASS notify POSTs webhook
PASS killswitch honoured
PASS killswitch off by default
PASS manifests parse
SELFTEST PASS
```
Not tested: a real usage source (none wired on this phone), a real keep-alive ping command, the hook inside a live Claude session.

## Install
```
/plugin install nvaex-burn --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-burn@novaexopia`. Swap out: `claude plugin disable nvaex-burn@novaexopia`.
