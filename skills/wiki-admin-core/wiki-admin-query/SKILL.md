---
name: wiki-admin-query
description: Answer a question from the corpus wiki using only wiki pages, with every claim cited. Use when the operator asks "what do we know about X", "where is Y decided", or any question the wiki should answer. Read-only on the wiki; the answer is saved for review, not filed as truth.
---

# wiki-admin query

## Rules (from llm-wiki-nocode `/llmwiki-query`)
- Use only facts from wiki pages you read. Not in a page you read: leave it out. No training data, no inference.
- No answer in the wiki: say "The wiki does not contain information on this topic." Partial: "The wiki mentions X but does not include Y."
- Read at least 3 and at most 8 pages per question. Cite every claim with `[[path/slug]]`. Code blocks verbatim.

## Retrieval order (cheapest first; from obsidian-wiki `wiki-query`)
1. **Index pass:** `manifest.py query <terms> --manifest <wiki>/manifest.jsonl` and the wiki `index.md`. No page reads yet.
2. **Section pass:** grep the candidate pages for the terms; read only the matching sections.
3. **Full read** of a page only when the section pass is inconclusive. Follow `## Connections` / wikilinks one page at a time.
4. **Repo questions** ("how does X work in repo R"): read that repo's `openwiki/quickstart.md` first, then the linked page (from OpenWiki for Claude Code `/openwiki:ask`).
5. **Large-context question across many pages** (more than the 8-page budget would hold): send the selected pages to Gemini with `gemini_infer.py ask "<question>" <pages...>`; it uses the large-context model and the same "only these pages" rule. Its answer is a draft like any other.

## Output
Save the answer to `questions_pending/<date>-<slug>.md` with the pages read and the citations. The operator moves it to `questions_approved/` if it should be filed back into the wiki; filing then goes through `wiki-admin-ingest` step 4 onwards.

## Built from (credit) and what this replaces
llm-wiki-nocode `/llmwiki-query` (rules, page budget, pending/approved), obsidian-wiki `wiki-query` (index -> section -> full read order), OpenWiki for Claude Code `/openwiki:ask` (repo questions via `openwiki/`). Replaces for the wiki admin: `/llmwiki-query`, obsidian-wiki `/wiki-query`, `/openwiki:ask`, llm-wiki-compiler `/wiki-query`.
