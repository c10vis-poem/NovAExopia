---
name: wiki-admin-lint
description: Health check and promotion gate for the corpus wiki and the 01-inbox staging folder. Use before any promotion, after an ingest batch, or when the operator asks "check the wiki". Deterministic checks first (script), semantic checks second; never edits pages, only reports.
---

# wiki-admin lint (and the cross-audit gate)

## Phase 1: deterministic (script)
`python3 tools/wiki-admin/audit_staging.py <folder> --wiki <wiki> [--report <dir>]`

Runs the Cross-Auditor six checks (spec: `handoff/2026-10-24/extracts/latest-config-extract.md` line 333) plus the nocode Phase 1 lint:
1. **duplicates**: same content sha256 in staging and wiki, or two staged files with one hash.
2. **orphans**: pages nothing links to, and wikilinks pointing at pages that do not exist (broken links).
3. **naming canon**: file names kebab-case `[a-z0-9-]`, no vendor prefixes (`NovA-`), ligature names spelled as in NAMING-CANON.
4. **contradictions vs accepted ADRs**: not decidable by a script. Reported as `needs_human_review` when a page touches a topic that has an ADR; the semantic pass below handles it.
5. **missing MAP.md**: a folder with pages and no `MAP.md` (or index.md).
6. **credential leakage**: `sk-`, `m0sk_`, `AIza`, `ghp_`, `BEGIN PRIVATE KEY`, connection strings with passwords.
Plus: missing or incomplete frontmatter (`id, type, created, updated, sources`), `sources` paths that do not exist.

Each file gets `promotion_recommended`, `promotion_blocked` (any of 1, 2-broken-link, 3, 6, missing frontmatter) or `needs_human_review`. Output: `AUDIT.md` + `audit.jsonl`. "You do NOT modify staged files. You flag issues; you do not resolve them."

## Phase 2: semantic (agent, after Phase 1)
Contradictions between pages and against ADRs, stale claims (older than 18 months without `[as of YYYY-MM]`), missing pages for entities mentioned 3+ times, missing cross-references between pages sharing 3+ sources. For a big wiki, batch the pages to Gemini (`gemini_infer.py ask`). Severity: red (blocks promotion), yellow (fix soon), green (note). Report to `lint_pending/<date>.md`; fixes the operator approves move to `lint_approved/` and are applied through `wiki-admin-ingest`.

## Built from (credit) and what this replaces
Cross-Auditor six checks and verdicts (latest-config-extract L333), llm-wiki-nocode `/llmwiki-lint` (two phases, severity levels, pending/approved), obsidian-wiki `wiki-lint` (check list: orphans, broken links, frontmatter, stale content, contradictions, index consistency, provenance drift), llm-wiki-compiler `/wiki-lint` (stale, low coverage, missing cross-refs). Replaces for the wiki admin: `/llmwiki-lint`, obsidian-wiki `/wiki-lint`, llm-wiki-compiler `/wiki-lint`.
