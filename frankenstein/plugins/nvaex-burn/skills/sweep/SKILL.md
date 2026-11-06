---
name: sweep
description: Checkpoint session state before a usage limit hits. Use when nvaex-burn reports BRAKE or on /nvaex-burn:sweep.
---
1. Stop starting new background work.
2. Write a short checkpoint (goal, done, next step, open files, uncommitted changes) to `${BURN_CHECKPOINT_DIR:-$HOME/.claude/state/nvaex-burn/checkpoints}/<UTC timestamp>.md`. Point `BURN_CHECKPOINT_DIR` at the NvAEx-Recaps memory folder to land it there.
3. Report the path and stop. Resume after the window resets.
