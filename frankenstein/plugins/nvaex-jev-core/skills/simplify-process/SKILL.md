---
name: simplify-process
description: Use when producing a doc, plan, spec, PRD or tooling around work. Stops invented process, gates, metrics and repeat reviews nobody asked for.
---
# Simplify the process

You over-build the process around the work, not the code. Rules:

1. **One request, one artifact.** No companion ADR, matrix, ledger, index or board. If a second one is load-bearing, name it in one line and let the user ask.
2. **Numbers and process you were not given are fiction:** no SLOs, KPIs, phased rollouts, sign-offs, definition-of-done lists.
3. **Size follows the ask.** Past about 5x the request, you inflated it: cut, do not justify.
4. **Ambiguity shrinks scope.** State one assumption, build the smallest thing, continue.
5. **Verify the product, never the process.** Do not write checks that pin counts, inventories or document links; they fail while the software is fine. Do not build machinery that authorizes your own work.
6. **Cap repeat reviews.** Two review rounds on the same artifact, then ship or ask. A third round needs new evidence.
7. **Notice the loop:** recent edits are mostly to checking machinery, or a validator is being fixed by another validator. Stop, name it, propose deleting it. Never answer a failure by making the rules heavier.

Say what you skipped in one line: `skipped: ceremony - rollout, KPIs. Say the word.`
