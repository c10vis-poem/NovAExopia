# SOURCES (parts donors)

| Path here | Origin | Version / license |
|---|---|---|
| agents/*.md (rewritten), skills/wiki-admin-{ingest(rewritten),lint,query} | greedy-crane `~/repos/.review/NovAExorpus-fable/plugins/greedy-crane/` (agents/, skills/); paths edited to `${CLAUDE_PLUGIN_ROOT}/scripts`, Gemini route removed | 0.1.0, operator-owned |
| skills/corpus-verify, skills/corpus-batch-processing | greedy-crane skills/ | same |
| scripts/{convert_raw_to_md,verify,manifest,audit_staging,promote}.py | greedy-crane scripts/ (verify.py: DEFAULT_CHECK now package-local) | same |
| scripts/check.py | vault `tools/check.py` (read-only copy; the independent checker verify.py wraps) | operator-owned |
| scripts/wa_quarantine.py | greedy-crane `hooks/drafts/P6-quarantine.draft.py` (stand-in for llm-secure-patterns, see Missing) | same |
| scripts/worker-stop-gate.sh | `~/.claude/agents/hooks/worker-stop-gate.sh` logic; adapted: SubagentStop fields, agent filter, override+revoke message | operator-owned |
| scripts/peek.py, vendor/LICENSE.headroom | headroom 1.3.2, petrovicistefan/claude-code-plugins (synced plugin) | MIT |
| scripts/wiki_{search,lint,stats,evolve}.py, skills/llm-wiki/references/evolution-workflow.md, vendor/LICENSE.llm-wiki | llm-wiki 3.2.0, praneybehl/llm-wiki-plugin, `~/local-plugins/plugins/llm-wiki` (SKILL.md and command rewritten short) | MIT |
| vendor/eson/index.js, vendor/LICENSE.honey | NoVa-honey-for-devs `eso/index.js` (ESON reference encoder) | MIT |
| skills/vault-skill-factory, skills/wiki-dedup | obsidian-wiki (AEsops-obsidian-wiki synced copy) `.claude/skills/` | upstream license in that repo |
| scripts/killswitch.sh | `frankenstein/shared/killswitch.sh` via `bin/vendor-shared.sh` | package-owned |
| scripts/batch_ledger.py, scripts/crush.js (wrapper), scripts/provenance.py | NEW, written here (no donor) | package-owned |

Dropped on purpose: llm-wiki demo media/docs/eval/integrations (5.1 MB), fastembed/sqlite-vec setup, graph scripts, evolve loop/adapters, gemini_infer.py (network), docs/homework, package/, lockfiles.

## Missing (named in the spec, not found on the phone)
- `gdrive-to-markdown` (plugin or script): no match in ~/.claude/plugins, ~/local-plugins, ~/repos. Step 3 uses `convert_raw_to_md.py` plus the Drive connector.
- `llm-secure-patterns` source tree (`wa_quarantine.py` as a shipped file): only `~/.claude/plugins/data/llm-secure-patterns-synced` (empty data dir) exists; the greedy-crane draft stands in.
- `batch_ledger.py`: no copy anywhere; written new.
- `eson crush` command: only the encoder library exists in NoVa-honey-for-devs; `crush.js` is a 10-line wrapper.
- `agent-army` skill: present (synced) but NOT copied; the rolling 4-worker pool is the ledger plus `corpus-batch-processing`, so the package has no dependency on it.
- `agent-ingest-audit-optimize`, `compounded`: no match found; not built.
- `skill-provenance` plugin (synced) not copied (agent/eval/package scaffolding); `provenance.py` writes `skill-provenance.json` SHA-256 hashes instead.
- MinHash/SimHash script: none found; dedup is the `wiki-dedup` skill plus `audit_staging.py` content-hash duplicate check.
- `wiki-history-ingest` (one of the "29 oddballs"): not copied; history ingest is out of scope for the 6-step pipeline.
