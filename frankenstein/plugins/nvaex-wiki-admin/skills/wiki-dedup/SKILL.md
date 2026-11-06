---
name: wiki-dedup
description: Find and, with confirmation, merge wiki pages covering the same concept. Audit by default; not for link repair.
---

# Wiki dedup

1. **Candidates (cheap, titles/aliases/tags only)**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wiki_dedup.py <wiki> [--min 0.75]` prints JSON pairs (HIGH >= 0.90, MEDIUM >= min). Content-hash duplicates in staging: `audit_staging.py`.
2. **Verdict per pair** (read both pages in full, only for candidates): `merge` (same concept: abbreviation, alias, accidental copy), `keep-separate` (related but distinct: GPT-3 vs GPT-4, technique vs application), `needs-review` (overlap plus real differences). One sentence of reason each.
3. **Report** pairs, scores, verdicts, reason. In audit mode stop here and ask which to merge.
4. **Merge (only on named pairs)**: choose the canonical page; fold the other's unique claims, sources, aliases and tags into it (integrate, do not append blindly; keep provenance); replace the old page with a stub `redirects_to: "[[canonical]]"` plus the old aliases; rewrite `[[old]]` and `[[old|text]]` to the canonical slug in every other page, skipping code fences and the stub; grep for survivors. Never `rm`. If the wiki is a git repo root, commit a clean snapshot first so a merge can be reverted.
5. Log what was merged. Nothing is deleted; stubs stay so old links resolve.
