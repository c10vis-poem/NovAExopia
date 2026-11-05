# nvaex-wiki-admin

Corpus intake, verification and skill factory for the Frankenstein set. Staging only: nothing is written to a live wiki except by `promote.py` on the operator's named approval. Stdlib Python + one Node file; no daemons, no network.

Pipeline (skill `wiki-admin-ingest`): size gate (`peek.py`) -> injection scan (`wa_quarantine.py`) -> convert / crush (`convert_raw_to_md.py`, `crush.js`) -> 25-file batches, 4 workers, JSONL ledger (`batch_ledger.py`) -> independent verify (`verify.py` + `check.py`) -> draft/stage/audit, then `vault-skill-factory`. Extras: trimmed llm-wiki (`wiki_search/lint/stats/evolve`), `provenance.py`, `wiki-dedup`.

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
See `SOURCES.md` ("Missing"): no `gdrive-to-markdown`, no shipped llm-secure-patterns, no hybrid-vector search deps (use `--no-embed`).

## Tested on device
`bash tests/selftest.sh` (Termux, Python 3.14, Node 26, 2026-11-04):
```
ok  plugin.json + hooks.json parse
ok  peek.py size gate
ok  wa_quarantine.py flags only evil.md, file byte-identical
ok  quarantine hook fires, stays quiet on clean, honors both kill switches
ok  convert_raw_to_md.py + crush.js (ESON)
ok  batch_ledger.py: 25-file batches, rolling claim/done, resume-safe
ok  verify.py passes good files and FAILs a cut one
ok  manifest + audit_staging + promote (approval-gated)
ok  wiki_search (BM25) / stats / lint / evolve load
ok  stop gate: blocks unfinished corpus-ingest once, names override+revoke, ignores others, kill switch works
ok  skill-provenance.json matches package
SELFTEST PASS (11 checks)
```

## Install
```
/plugin install nvaex-wiki-admin --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-wiki-admin@novaexopia`. Swap out: `claude plugin disable nvaex-wiki-admin@novaexopia`.
