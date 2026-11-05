# SOURCES (parts donors)

| Path here | Origin | Version / license |
|---|---|---|
| agents/*.md (rewritten), skills/wiki-admin-{ingest(rewritten),lint,query} | greedy-crane `~/repos/.review/NovAExorpus-fable/plugins/greedy-crane/` (agents/, skills/); paths edited to `${CLAUDE_PLUGIN_ROOT}/scripts`, Gemini route removed | 0.1.0, operator-owned |
| skills/corpus-verify, skills/corpus-batch-processing | greedy-crane skills/ | same |
| scripts/{convert_raw_to_md,verify,manifest,audit_staging,promote}.py | greedy-crane scripts/ (verify.py: DEFAULT_CHECK now package-local) | same |
| scripts/check.py | vault `tools/check.py` (copy; the independent checker verify.py wraps). Changed 2026-11-05: vault found via `VAULT` env first, then the phone path, so it no longer matches the vault copy byte for byte | operator-owned |
| scripts/wa_quarantine.py | greedy-crane `hooks/drafts/P6-quarantine.draft.py`, extended with llm-secure-patterns decoders/patterns (see folded rows) | same |
| scripts/worker-stop-gate.sh | `~/.claude/agents/hooks/worker-stop-gate.sh` logic; adapted: SubagentStop fields, agent filter, override+revoke message | operator-owned |
| scripts/peek.py, vendor/LICENSE.headroom | headroom 1.3.2, petrovicistefan/claude-code-plugins (synced plugin) | MIT |
| scripts/wiki_{search (embedding path cut),lint,stats,evolve}.py, skills/llm-wiki/references/evolution-workflow.md, vendor/LICENSE.llm-wiki | llm-wiki 3.2.0, praneybehl/llm-wiki-plugin, `~/local-plugins/plugins/llm-wiki` (SKILL.md, command and evolution-workflow.md rewritten short) | MIT |
| vendor/eson/index.js, vendor/LICENSE.honey | NoVa-honey-for-devs `eso/index.js` (ESON reference encoder) | MIT |
| skills/vault-skill-factory (rewritten self-contained), skills/wiki-dedup (rewritten around new scripts/wiki_dedup.py) | obsidian-wiki (AEsops-obsidian-wiki synced copy) `.claude/skills/`; ideas only | upstream license in that repo |
| scripts/killswitch.sh | `frankenstein/shared/killswitch.sh` via `bin/vendor-shared.sh` | package-owned |
| scripts/batch_ledger.py, scripts/crush.js (wrapper), scripts/provenance.py | NEW, written here (no donor) | package-owned |
| skills/rule-learning, scripts/rule_propose.py, commands/rules.md, vendor/LICENSE.compounded | compounded 1.x, ankitkr3 (S1/ab9b0379): rule mode of compounded-author, skill_propose.py/pin_skill.py logic | MIT |
| skills/audit-outside-material, vendor/LICENSE.agent-ingest-audit-optimize | agent-ingest-audit-optimize (S1/7f76ffa9), L. L. Sobral: SKILL.md states, audit steps, classifications, stop conditions; reversible-change step from WORKFLOW.md | MIT |
| skills/gdrive-to-markdown, scripts/gdrive_fetch.py, convert_raw_to_md.py `.csv`, vendor/LICENSE.gdrive-to-markdown | gdrive-to-markdown 1.0.1, beaverbeard (S1/6aaccdd0): the two hard rules and image-loss note; connector path replaced by rclone | MIT |
| skills/obsidian-notes, scripts/vault_lint.py (verbatim), vendor/LICENSE.obsidian-notes | obsidian-notes, M. Rogers (S1/3cacb896): `skills/obsidian-notes/scripts/vault_lint.py`, SKILL.md steps 1-3 | MIT |
| scripts/vault_sync.py, commands/vault-sync.md, vendor/LICENSE.obsidian-sync | obsidian-sync, chenlei (S1/842c82fd): `sync_to_obsidian.py` exclusions, flattening, manifest; rewritten copy-only with mandatory dest, dry-run default | MIT |
| skills/rag-retrieval-check, scripts/wiki_retrieval_eval.py, vendor/LICENSE.rag-evaluation | rag-evaluation, S. Skripko (S1/9bf3e930): `rag-retrieval-check` SKILL.md stages and hit@k/RR/recall math; harness is new | MIT |
| skills/wiki-admin-{ingest,lint,query} "Deltas" sections, vendor/LICENSE.wiki-wonka | wiki-wonka, Coopera Code (S1/cc779a20): skills/{ingest,lint,query}/SKILL.md deltas only (no agents, hooks, wiki/ template) | MIT |
| scripts/wa_quarantine.py decoders, vendor/LICENSE.llm-secure-patterns | llm-secure-patterns, WildBlue (S1/6358786b): `templates/python/sanitize_web_content.py` zero-width set, URL-safe base64, ROT13 line test, hidden-CSS patterns, used detect-only | MIT |

| skills/obsidian-markdown (SKILL.md + 3 references), vendor/LICENSE.obsidian-skills | `~/repos/obsidian-skills` skills/obsidian-markdown at 31f9b7e, kepano; verbatim, 27 KB donor folder -> same | MIT |
| skills/corpus-batch-processing step 9 | edited 2026-11-05: mem0 `add_memory` step replaced by a batch-record file in the vault | package-owned |

## Size before / after (source folder KB, whole -> bytes kept here)
| Source | Before | After (bytes in package) |
|---|---|---|
| compounded | 830 KB | 5,856 (skill 1,681 + script 3,890 + cmd 285) |
| agent-ingest-audit-optimize | 2,743 KB | 2,797 |
| gdrive-to-markdown | 1,384 KB | 2,166 (skill + script) |
| obsidian-notes | 712 KB | 28,495 (vault_lint.py verbatim 26,794 + skill) |
| obsidian-sync | 73 KB | 2,746 |
| rag-evaluation | 115 KB | 4,727 (skill + harness) |
| wiki-wonka | 3,800 KB | about 2,400 (three delta sections) |
| llm-secure-patterns | 1,436 KB | +1,176 bytes in wa_quarantine.py |

Trims of what was already here (bytes): wiki_search.py 32,921 -> 22,553 (FastEmbed/sqlite-vec path removed); wiki-dedup SKILL 15,441 -> 1,436 (its obsidian-wiki CLI/QMD/config references pointed at nothing; replaced by wiki_dedup.py 2,959); vault-skill-factory 7,579 -> 1,837 (same dangling config); evolution-workflow.md 20,146 -> 1,326 (referenced an unshipped loop driver); corpus-verify SKILL 11,323 -> 8,092 (check.py internals, other-corpus notes). Package total 270,652 -> 295,526 bytes (42 -> 63 files; 11 licence files = 11.5 KB, 8 folded rows = +72 KB, trims = -52 KB). Largest remaining: check.py 33 KB (independent checker, needed), wiki_evolve.py 30 KB, vault_lint.py 27 KB (verbatim), wiki_search.py 22.5 KB.

Dropped on purpose: llm-wiki demo media/docs/eval/integrations (5.1 MB), fastembed/sqlite-vec setup and the hybrid search path, graph scripts, evolve loop/adapters, gemini_infer.py (network), docs/homework, package/, lockfiles. From the folded plugins: compounded trust ladder/DB/dashboard/hooks/export, agent-ingest-audit-optimize ledger/dashboard/evals/adapters (2.7 MB), obsidian-notes evergreen/research/evals, obsidian-sync symlink/move modes and vault autodetect, rag-evaluation incident-repair and answer-check skills, wiki-wonka agents/hooks/wiki template, llm-secure-patterns skills/templates/docs (only the detection patterns were used).

## Missing / not folded
- `batch_ledger.py`: no copy anywhere; written new. `eson crush` command: only the encoder library exists upstream; `crush.js` is a 10-line wrapper.
- `agent-army`: present (synced) but NOT copied; rolling 4-worker pool = ledger + `corpus-batch-processing`. `skill-provenance` plugin not copied; `provenance.py` writes SHA-256 hashes instead.
- MinHash/SimHash: none found by name scan; `wiki_dedup.py` is title/alias/tag scoring, `audit_staging.py` the content-hash check.
- `wiki-history-ingest` (one of the "29 oddballs"): not copied.
- `wa_quarantine.py` does not exist in llm-secure-patterns (probe: its tree has no such file; only `templates/python/sanitize_web_content.py`); the package script is the real one, with that template's patterns folded in.
- Superseded earlier "Missing" claims: gdrive-to-markdown, compounded, agent-ingest-audit-optimize, llm-secure-patterns ARE on the phone (S1) and are now folded.
- Not exercised against live Drive: `gdrive_fetch.py` is tested with a stub rclone (arguments and conversion), not with a real `biz:` listing.
