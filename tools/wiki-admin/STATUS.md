# STATUS (2026-10-28, branch wiki-admin-tools)

## Built and tested (real runs on sample files)
- `bash tools/wiki-admin/selftest.sh` -> `SELFTEST PASS` (synthetic PDF/DOCX/HTML: converter reports EMPTY/ERROR/unsupported, verify passes then FAILs a cut file, manifest rebuild byte-identical, Gemini dry-run draft + privacy refusal, audit blocks, promote moves only the approved page).
- Converter on 9 real/mixed files (vault PDF, DOCX, HTML, TXT, MD + blank PDF, broken PDF, .xyz, same-stem twin): 5 converted, 2 EMPTY, 1 ERROR, 1 unsupported, all named in REPORT.md; rerun -> 5 unchanged (sha256).
- `verify.py`: canary ok; 5/5 PASS (one "+ UPSTREAM DEFECT"); after cutting a PDF's text to 2/3 -> FAIL naming lost acronyms; converter labelled with the checker's library -> NOT-INDEPENDENT.
- `gemini_infer.py`: dry-run draft/w5h/ask (logged, no key printed); private tag, #pii, credential pattern -> REFUSED exit 3; MCP stdio initialize / tools/list / tools/call answered.
- `audit_staging.py` + `promote.py`: bad name, broken link, credential, missing source, dry-run draft, duplicate -> promotion_blocked; promote refused blocked pages, a missing approver and a file changed after audit; promoted the recommended page and logged it.

## Built, untested
- Live Gemini call (no GEMINI_API_KEY stored; `pip install google-genai` did not finish within 280 s on Termux and left no module; run it by hand).
- The four customized skills (`skills/wiki-admin-core/wiki-admin-*`) and the two operator skills: text only, not run in a wiki-admin session.

## Not started
- Lint report automation for Phase 2 (semantic), housekeeper sweep, chunker (no chunk schema chosen: open question E6).

## Sources read
Drive `_02.wiki-admn-docs`: wiki-reference-router, w5h-extraction, convert-raw-to-md.py, chunk/trajectory/rlvr schemas, manifest schema, wiki node template. Vault: `tools/check.py`, `handoff/2026-10-24/extracts/wiki-admin-extract.md`, `latest-config-extract.md`, `docs/WIKI-ADMIN-GUIDE.md`. Local: `~/wiki-admin/{AGENTS.md,MEMORY.md,GRILL-INPUTS.md,tools/wiki_admin.py}`, llmwiki commands, obsidian-wiki wiki-ingest/query/lint/stage-commit, openwiki plugin generate/update/ask, openwiki-skills init/update (via gh api).

## Operator decisions applied
OpenWiki TUI / CLI dropped; overlapping tools merged into customized skills (each SKILL.md lists what it replaces); Gemini is the inference route; the agent lives in NovusAExenti `executor-core/file-administrator/`.
