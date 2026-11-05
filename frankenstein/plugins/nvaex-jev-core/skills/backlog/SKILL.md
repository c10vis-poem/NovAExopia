---
name: backlog
description: Use to keep a task list that survives sessions: add tasks, see what is next, mark progress, and hand off to the next session.
---
# Backlog

File-backed, stdlib, no server: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/backlog.py <cmd>`. Store: `$NVAEX_BACKLOG` or `~/.claude/state/nvaex-jev-core/backlog.jsonl`.

| Command | Does |
|---|---|
| `add "verb-first text" [-p H\|M\|L] [--project X] [--after ID]` | new task; prints its id |
| `list [--all]` | open tasks, blocked ones marked, highest priority first |
| `next` | the one task to do now (unblocked, highest priority) |
| `start ID` / `done ID` / `block ID "why"` | state changes |
| `handoff` | what is done, in progress, blocked, next; paste into the next session |

Rules: one-line tasks (under 200 chars), start with a verb, say what done looks like. 5-10 tasks per goal; fewer means too big, more means over-planning. Dependencies (`--after`) only for real ordering. At session end, run `handoff` and put it where the next session reads it. Never create a task named "plan the work".
