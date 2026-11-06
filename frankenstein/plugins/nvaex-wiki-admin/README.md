# nvaex-wiki-admin

Corpus intake, verification and skill factory for the Frankenstein set. Staging only: nothing is written to a live wiki except by `promote.py` on the operator's named approval. Stdlib Python + one Node file; no daemons, no network.

Pipeline (skill `wiki-admin-ingest`): size gate (`peek.py`) -> injection scan (`wa_quarantine.py`) -> convert / crush (`convert_raw_to_md.py`, `crush.js`) -> 25-file batches, 4 workers, JSONL ledger (`batch_ledger.py`) -> independent verify (`verify.py` + `check.py`) -> draft/stage/audit, then `vault-skill-factory`. Extras: trimmed llm-wiki (`wiki_search` BM25 only, `wiki_lint/stats/evolve`), `provenance.py`, `wiki-dedup` (`wiki_dedup.py`).

Folded after 0.2.0: `obsidian-markdown` (Obsidian syntax, from `~/repos/obsidian-skills`, MIT); `corpus-batch-processing` writes its batch record to `audit/corpus-batch-<date>-<batch>.md` in the vault (the mem0 step is gone, mem0 was dropped); `scripts/check.py` and `corpus-verify` find the vault through the `VAULT` env var first, then the phone path.

Folded in 0.2.0 (see `SOURCES.md` for origin, licence and sizes): `rule-learning` + `/rules` (compounded, approval-gated), `audit-outside-material`, `gdrive-to-markdown` (`gdrive_fetch.py`, rclone, no connector), `obsidian-notes` (`vault_lint.py`), `/vault-sync` (`vault_sync.py`, copy-only, dry-run default, destination mandatory), `rag-retrieval-check` (`wiki_retrieval_eval.py`), wiki-wonka deltas inside the ingest/lint/query skills, and llm-secure-patterns decoders inside `wa_quarantine.py`.

Agents: `wiki-admin` (directs), `corpus-ingest` (one batch, has the Stop gate).

## Swap in / out
```
claude plugin enable  nvaex-wiki-admin@novaexopia
claude plugin disable nvaex-wiki-admin@novaexopia
```
Works with any other Frankenstein package disabled; shares no files with them (killswitch.sh is vendored in `scripts/`; refresh with `bin/vendor-shared.sh`).

## Hooks and kill switches
| Event | Hook | Blocks? | Kill switch name |
|---|---|---|---|
| PostToolUse (Read) | `hooks/quarantine.sh`: adds a "treat as DATA" notice for injection-looking files | never | `quarantine` |
| SubagentStop (corpus-ingest only) | `hooks/stop-gate.sh`: stops a worker finishing with unchecked plan steps and empty `## Blocked`; blocks at most once in a row | yes (spec) | `stop-gate` |

Off: `touch ~/.nvaex-hooks-off` (all), `touch ~/.claude/state/off/nvaex-wiki-admin` (package), or `touch ~/.claude/state/off/nvaex-wiki-admin.<hook>`. Revoke: delete the file. The block message names both.

## Not included
See `SOURCES.md` ("Missing / not folded"). No vector search (BM25 only). Not exercised against live Drive: `gdrive_fetch.py` is tested with a stub rclone.

## Tested on device
`bash tests/selftest.sh` (Termux, Python 3.14, Node 26, 2026-11-05):
```
ok  plugin.json + hooks.json parse
ok  peek.py size gate
ok  wa_quarantine.py flags only evil.md, file byte-identical
ok  quarantine hook fires, stays quiet on clean, honors both kill switches
ok  convert_raw_to_md.py + crush.js (ESON)
ok  batch_ledger.py: 25-file batches, rolling claim/done, resume-safe
ok  verify.py passes good files and FAILs a cut one
ok  manifest + audit_staging + promote (approval-gated)
ok  wiki_search (BM25) / stats / lint; evolve capture immutable, propose leaves skill untouched
ok  stop gate: blocks unfinished corpus-ingest once, names override+revoke, ignores others, kill switch works
ok  wa_quarantine: zero-width, ROT13, url-safe base64, hidden css caught; benign text clean
ok  rule_propose: stages inert, refuses duplicate/threat/non-rule, approve/demote/reject move (never delete)
ok  gdrive_fetch: rclone copy only (read-only, no overwrite); exported CSV converts
ok  vault_lint: broken link -> exit 1, --fix-index and --to-markdown-links write
ok  vault_sync: dry-run by default, copy-only, skips CLAUDE.md, refuses dest inside src
ok  wiki_retrieval_eval hit/miss with stage reason; wiki_dedup finds the variant pair only
ok  all skills valid; one hook per event, kill switch first; no dangling script references
ok  check.py finds the vault via VAULT first
ok  no mem0 step, obsidian-markdown shipped, no reference to another plugin
ok  skill-provenance.json matches package
SELFTEST PASS (20 checks)
```

## Install
```
/plugin install nvaex-wiki-admin --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-wiki-admin@novaexopia`. Swap out: `claude plugin disable nvaex-wiki-admin@novaexopia`.
