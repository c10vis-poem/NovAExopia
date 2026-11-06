---
name: rea-review
description: Adversarial multi-reviewer check of a contested claim or fork-strip decision; only verified quotes move the verdict.
---
# rea-review (from colosseum, trimmed)

1. **Blind drafts.** Spawn 3 `adversarial-reviewer` agents in parallel, each given the question and the same evidence files, no view of each other. Each returns JSON: `position`, `probability` (0.02..0.98), `claims[]` of `{text, source, quote}`.
2. **Baseline.** Pooled probability = mean of logit(p), then back. Majority position = baseline.
3. **Verify every quote.** For each claim, save the source page or file text, then run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/rea-review/quote_check.py --quote "<q>" --page-file <file>`.
   `v` exact: counts. `n` near or qualifier dropped: review by hand, counts as 0. `u` not found or number/negation differs: 0.
4. **Move the verdict only on `v` evidence** (or a named logical error). Any other position change is conformity: record it, do not count it.
5. **Differ from baseline** only if a `v` quote refutes a majority claim and an independent reviewer agrees.
6. **Report** the verdict, baseline, each claim with its v/n/u, and unresolved disputes as conditional answers. Never present a deadlock as consensus.

Sources: local files or pages already fetched (use `claw.search` / `claw.scrape` when claw-mcp is enabled). Reviewers do not browse. No external AI CLIs, no network from this skill.
