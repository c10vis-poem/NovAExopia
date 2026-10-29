# tools/wiki-admin

Scripts the wiki admin (NovusAExenti `executor-core/file-administrator/`) runs. Each answers one question; together they are the gate **convert -> verify -> draft -> stage -> audit -> promote**. Nothing here edits a raw source, and nothing writes the live wiki except `promote.py` on an operator approval.

| Script | Question it answers | Exit codes |
|---|---|---|
| `convert_raw_to_md.py RAW OUT` | Which raw files became Markdown, and which did not (EMPTY, ERROR, unsupported), by name? | 0 ok, 1 any empty/error |
| `verify.py CLEAN --raw RAW` | Did conversion lose any named detail? Runs the vault `tools/check.py` (different extractors), canary first. | 0 pass, 1 not pass, 2 canary broken |
| `manifest.py build ROOT [--per-tier]` / `query WORDS --manifest F` | Where is a file about X, without scanning folders? | 0 |
| `gemini_infer.py draft/w5h/extract/ask/serve` | Bulk drafting, W5+H, large-context answers on Gemini, with a privacy filter and dry-run | 0 ok, 3 refused |
| `audit_staging.py STAGING --wiki WIKI` | Is each staged page safe to promote? Cross-Auditor six checks + lint | 0, 1 any blocked |
| `promote.py PAGE --wiki W --audit A --approved-by NAME` | Move one approved page into the wiki, refusing anything the audit or a later edit invalidates | 0 promoted, 1 refused |
| `selftest.sh` | Do all of the above still work? Round trip on synthetic files, no key needed | 0 pass |

## Gemini setup (operator)
1. Key: `nvaex-secret set GEMINI_API_KEY` (never in a file in a repo). The script reads `GEMINI_API_KEY` or `GOOGLE_API_KEY` from the environment and never prints it.
2. SDK: `pip install google-genai`.
3. Models: `GEMINI_MODEL` (default `gemini-3.8-flash`), `GEMINI_MODEL_LARGE` for `ask` (default `gemini-4-argon`, 1M context). Defaults checked on ai.google.dev/gemini-api/docs/models, 2026-10-28.
4. Without a key every call is a dry run: the request is built, logged and a `dry_run: true` draft is written; `audit_staging.py` blocks such drafts.
5. Call log: `~/.local/state/wiki-admin/gemini-calls.jsonl` (`WIKI_ADMIN_LOG` overrides).
6. As an MCP server: `claude mcp add wiki-admin-gemini -- python3 <repo>/tools/wiki-admin/gemini_infer.py serve` (tools `gemini_draft`, `gemini_w5h`, `gemini_ask`).

## Sources reused
- `convert_raw_to_md.py`: operator's `convert-raw-to-md.py` (Drive id 1LRsROVSTq9BJcaHho5sz8eitOHln-xvj), same extractors except HTML (pandoc, because markdownify shares BeautifulSoup with the checker).
- `verify.py`: vault `tools/check.py` unchanged (corpus-verify skill, Hard rule 5).
- `manifest.py`: `~/wiki-admin/tools/wiki_admin.py` fields kept (it still runs as `manifest.py ROOT OUT`), schema from `_log-schema-and-JSONL-strctr.md`, fixes from the generate-jsonl-markers.py weakness list (`handoff/2026-10-24/extracts/wiki-admin-extract.md` B9).
- `audit_staging.py`: Cross-Auditor six checks (`handoff/2026-10-24/extracts/latest-config-extract.md` L117, L333) + llm-wiki-nocode lint Phase 1.
- `promote.py`: capture -> stage -> verify -> promote (extract B11); revision check idea from obsidian-wiki `wiki-stage-commit`.
