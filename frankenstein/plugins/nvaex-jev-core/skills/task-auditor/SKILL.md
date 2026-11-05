---
name: task-auditor
description: 5-gate audit for L2+ tasks (pre-execution spec, dry-run, execution health, post-execution verification, handoff audit). Use before starting and before declaring done on any multi-step or irreversible task.
---

# Task auditor: 5 gates

1. **Pre-execution spec.** State goal, files in scope, done-test in 3 lines. Quote the operator's ask.
2. **Dry run.** List the exact commands/edits you will run and what each changes. Skip for read-only work.
3. **Execution health.** Every 5 tool calls (the hook prompts you): on plan? repeating a step? same file edited 3 times means stop and re-read the error.
4. **Post-execution verification.** Run the done-test. Cite command and output. Tests edited to pass do not count.
5. **Handoff audit.** Every claim in the summary (count, state, file content) cites the file or command it came from. List what was not checked.

Non-blocking: the Stop hook scores dark patterns (false success, phantom completion, test edited to pass, silent truncation, ...) and only warns.
