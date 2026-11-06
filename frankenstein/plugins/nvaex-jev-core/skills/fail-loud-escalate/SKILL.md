---
name: fail-loud-escalate
description: Use when writing error handling, fallbacks or retries, or when repeated attempts keep failing without new evidence.
---
# Fail loud, escalate don't thrash

## Fail loud
A swallowed error is a bug with a delay timer. Banned: empty catch, catch-log-continue when the caller cannot proceed correctly, `|| default` masking a failed operation, broad catches to keep going, unlimited or silent retries, returning null/empty on internal error.

Before any fallback ask: is the system correct when this branch runs? Yes (documented default, optional feature): fine, and name it (`DEFAULT_TIMEOUT_S = 30`). No: let it propagate to a layer that can handle it, with a message naming what broke and on which input. Internal invariants crash early. External edges degrade explicitly and say so. If deleting the try/catch makes the bug easier to find, the try/catch is the bug.

## Escalate
The trigger is what the next idea is made of: a variation of the last attempt (thrashing) versus a new hypothesis from new evidence. By the second failure it is visible; by the third it is certain. Also thrashing: "should work now" a third time; each fix breaks something else; picking which half of contradictory evidence to believe; editing code you do not understand to see what happens.

Then: stop, revert edits that did not help, write the handoff (exact symptom and repro, verified facts with evidence, hypotheses eliminated and how, failed attempts, what is unexplored), and recommend who takes it: stronger model, human, or fresh session. A clean handoff in ten minutes beats an hour of damage.
