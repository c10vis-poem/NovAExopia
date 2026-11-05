---
name: llm-wiki
description: Trimmed llm-wiki toolset for a Markdown wiki: section-level search (BM25), structural lint, stats, and evolve (propose, evaluate, apply, roll back evidence-linked improvements). Use for "search the wiki", "lint the wiki", "wiki stats", "wiki evolve".
---

# llm-wiki (trimmed)

`S=${CLAUDE_PLUGIN_ROOT}/scripts`. A wiki is a folder of Markdown pages with frontmatter (`type, tags, sources, updated`) and an `index.md`.

- Search: `python3 $S/wiki_search.py "terms" --wiki <wiki> [--json] [--top N]` (stdlib BM25).
- Lint: `python3 $S/wiki_lint.py <wiki> [--json]` (orphans, broken `[[links]]`, oversized pages, frontmatter, stale dates). Report; never edit.
- Stats: `python3 $S/wiki_stats.py <wiki>`.
- Evolve: `/wiki-evolve` (read `references/evolution-workflow.md` first). Small rules: `rule-learning`. `python3 $S/wiki_evolve.py --help`. `apply` needs a reviewed proposal and the operator's named approval.

Answer questions from pages you read, cite `[[slug]]`; if the wiki lacks it, say so.
Upstream: praneybehl/llm-wiki-plugin (MIT). Cut from 5.4 MB to the files above.
