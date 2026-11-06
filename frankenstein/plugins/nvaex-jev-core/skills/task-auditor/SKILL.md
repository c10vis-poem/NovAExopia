---
name: task-auditor
description: 5-gate audit for L2+ tasks (spec, dry-run, health, verification, handoff). Use before starting and before done.
---
# Task auditor: 5 gates

1. **Pre-execution spec.** Goal, files in scope, done-test in 3 lines; quote the operator's ask. For features, write the checklist with the spec-check skill.
2. **Dry run.** List the exact commands and edits and what each changes. Skip for read-only work.
3. **Execution health.** Every 5 tool calls (the hook prompts): on plan? repeating a step? Same file edited 3 times: stop, re-read the error, use systematic-debugging.
4. **Verification.** Use verify-before-done: run the done-test, cite command and output. Tests edited to pass do not count. Reports with probability or EV math: give them to the claim-auditor agent.
5. **Handoff audit.** Every claim in the summary (count, state, file content) cites the file or command it came from. List what was not checked.

Non-blocking: the Stop hook scores 26 dark patterns (false success, phantom completion, test edited to pass, fake stats or citations, cliffhanger endings, unproven rollback claims, ...) and only warns.
