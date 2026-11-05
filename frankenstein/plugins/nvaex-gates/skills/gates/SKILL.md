---
name: gates
description: What to do when an nvaex-gates hook blocks a call or a turn. Use when a tool call or Stop returns "BLOCKED (...)", when the operator asks about the rules, overrides, or gate status, or before telling the operator a hook is in the way.
---

# Working with the gates

The full list is `RULES.md` at the plugin root. Every block names its override and its revoke.

1. Do what the block asks when you can: Read the file, load the skill, run the step. Read is never blocked by resume-gate.
2. If only the operator can clear it, state the one thing that is missing and the verb they would type. Never hand them an either/or menu to clear a gate.
3. Never try to get around a block: no retry loop, no `gate off`, no edit to `~/.claude/state`. state-guard refuses those, and the loop breaker is a last resort for broken gates, not a way through.
4. Check-ins, `/ok push` and `#no-ship` are the operator's words only. A subagent hand-back never counts.
5. `gate status` shows what is on, off or missing. It is read-only, run it freely.
