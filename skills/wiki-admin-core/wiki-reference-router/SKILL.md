---
name: wiki-reference-router
description: Use when an agent needs to retrieve factual knowledge, schemas, or protocols from local multi-format references without modifying raw files.
---

# Wiki Reference Router

Source: operator doc `_02.wiki-admn-docs/wiki-reference-router.md.txt` (Drive id 1P0kwlDCgk4hBVCy5uDmm09w1cEIlpk2g). The three directives below are that text, unchanged. The "In this stack" section maps them onto today's folders.

## Purpose and scope

Governs how agents locate, parse, and cite multi-format documents housed inside `references/` directories across repositories. The instructions inside this skill remain pure Markdown, while referenced assets may include .md, .txt, .csv, .json, .yaml, or code files.

## Operational directives

1. **Never assume monolithic Markdown.**
   - Raw references are preserved in their native format under `references/`. Do not expect all references to be converted to .md.
2. **Deterministic lookup chain.**
   - Step 1: Read the local `MAP.md` to identify which reference folder holds the target domain.
   - Step 2: Open the specific target reference file (e.g., `references/aesop_protocols.md`, `references/termux_wiki.txt`, `references/horizons_frontend.json`).
   - Step 3: Extract only the requested facts, tables, or code signatures without dumping whole files into conversational memory.
3. **Immutability guarantee.**
   - References are read-only. Never write, update, or append notes directly to `references/` files. Any synthesized conclusions must be written to `02_wiki_md/` or episodic logs.

## In this stack

- Reference folders today are each repo's `raw/` and `clean_md/`, plus the vault's `raw_database/`. They are read-only exactly like `references/`.
- When `MAP.md` names no folder for the domain, query the manifest instead: `python3 tools/wiki-admin/manifest.py query <word> --manifest <repo>/manifest.jsonl`. Open only the paths it returns.
- "Written to `02_wiki_md/`" means: written to the staging inbox `01-inbox/` first. A page reaches the wiki only through `tools/wiki-admin/promote.py` after the verify step passed and the operator approved it.
- Cite every extracted fact with its path (and line or heading). A fact with no path is not a fact for the wiki.
