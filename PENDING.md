# PENDING.md — NovAExopia

Durable cross-session backlog. Not rewritten each session — items persist until resolved or explicitly dropped.

- **`horizons-ui/` subfolder needs reconciling.** Added 2026-09-07 per Document 05 (commit `c197580`, "feat: add Document-05 top-level dirs"), which is the nested-repo model. Superseded now that RFMC's flat 8-repo model is the actual direction (2026-09-15 decision) — a new standalone Horizons UI repo is being built separately. Resolve this subfolder once that lands: likely removed.
- **No ingestion pass yet otherwise** — rest of `clean_md/`/`wiki_md/` are still POINTER.md stubs per NovAExorpus's RESUME.md.

## 2026-10-23
- Marketplace `novaexopia`: plugins not yet listed because no public source repo was found: cowork-plugin-management, obsidian-sync, shipwright (0.2.0). The remaining ~515 plugins from the operator's Drive `NewPlugins` folder are added in batches.

## 2026-10-28 (wiki admin tools)
- Store the Gemini key (`nvaex-secret set GEMINI_API_KEY`), install `google-genai` (the install did not finish in 280 s), run one live `gemini_infer.py draft`. Confirm the default model ids in `gemini_infer.py` against Google's model list.
- Not built: Gemini profile YAML, housekeeper, chunker (needs chunk schema decision E6), semantic half of lint. Operator decides E6 (chunk schema) and E10 (frontmatter schema).
- After merge: link `skills/wiki-admin-core/*` into `~/wiki-admin/.claude/skills` and run the skills in a `wiki-admin` session.
- Read the operator's full wiki-admin file set (140 to 200 files; location to confirm) before wiring further.
