---
name: my-tasks
description: Hand the operator tasks only they can do (secrets in .env, approvals, decisions, commands on their own machine) as a persistent list instead of burying the ask in chat. Use when you need something from the operator and can keep working without it.
---

# My tasks

Replaces the human-in-the-loop plugin's pane with a plain file list (`~/.claude/state/my-tasks.tsv`, override `NVAEX_TASKS`).

When blocked on something only the operator can do:

1. `bash "${CLAUDE_PLUGIN_ROOT}/scripts/mytasks.sh" add "<what>" "<why and what done looks like>"`
2. Keep working on what is not blocked.
3. Before finishing, run `... list` and tell the operator the open tasks.
4. When the operator replies, record it: `done N`, `answer N "<text>"` or `reject N "<reason>"`.

Never put secrets in a task. Say where they go ("add STRIPE_KEY to .env"), not the value.
