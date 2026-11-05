---
name: burn
description: Check or drive the usage pacer. Use when the user asks about usage headroom, burn mode, brake mode, the burn queue, or cache keep-alive.
---
Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/burn.py" <cmd>`:
- `status`: current mode (unknown | brake | burn | idle) and why.
- `tick --dry-run`: show which pre-approved queue job would run. Drop `--dry-run` to run one.
- `keepalive`: ping every 4m30s while the session is active (run it in the background; it exits when idle).

Queue file (`BURN_QUEUE`, default `NovAExorpus/burn-queue.md`, read only). One job per line:
`- [x] smoulder | wiki-lint | python3 /path/to/script.py`
`[x]` means pre-approved. `[ ]` never runs. Tiers: smoulder (<=72h to reset), blaze (<=24h), inferno (<=6h). A job runs only once its tier window is open. Never edit the queue to approve a job yourself.
If status says `unknown`, no usage source is wired: say so, do not guess.
