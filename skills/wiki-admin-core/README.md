# wiki-admin-core

Skills the wiki-admin agent (NovusAExenti `executor-core/wiki-admin/`) loads. Text comes from the operator's `_02.wiki-admn-docs` Drive folder; each SKILL.md names its Drive id.

| Skill | What it answers |
|---|---|
| [wiki-reference-router](wiki-reference-router/SKILL.md) | Where is a fact, and how do I read it without touching the source? |
| [w5h-extraction](w5h-extraction/SKILL.md) | What did the operator actually decide in this transcript (who, what, when, where, why, how)? |
| [wiki-admin-ingest](wiki-admin-ingest/SKILL.md) | How does a raw file become a reviewed wiki page without losing anything? |
| [wiki-admin-query](wiki-admin-query/SKILL.md) | What does the wiki say about X, with citations? |
| [wiki-admin-lint](wiki-admin-lint/SKILL.md) | Is the wiki (or the staged inbox) healthy enough to promote? |
| [wiki-admin-repo-docs](wiki-admin-repo-docs/SKILL.md) | How do I create or refresh a repo's `openwiki/` docs? |

The last four are customized merges of overlapping tools (OpenWiki for Claude Code, openwiki-skills, llm-wiki-nocode, obsidian-wiki, llm-wiki-compiler). Each SKILL.md ends with what it was built from and which originals it replaces for the wiki admin. Operator decision: the OpenWiki TUI / LangChain `openwiki` CLI is dropped and is not wired in.

The scripts these skills call live in `tools/wiki-admin/`.
