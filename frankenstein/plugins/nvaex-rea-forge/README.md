# nvaex-rea-forge
Fork harvester. `/rea-harvest <repo> [--crg]` scans a repo (Python AST; optional Tree-sitter graph via `code-review-graph`), extracts CLI entrypoints, longest functions, prompt files/strings and telemetry hits, writes `CAPABILITY_CARD.json`, and picks a packaging gate (skill / cli-wrap / mcp-core). `wrap.py` makes a shell shim + `SKILL.md` for a CLI (fallback for the missing `mcp2cli`). `code-archaeologist` + `integration-verifier` agents form the adversarial strip loop. `rea-sync` keeps local patches across upstream updates. Bundled `code-map` skill draws an HTML architecture map.

## Swap
```
claude plugin enable  nvaex-rea-forge@novaexopia
claude plugin disable nvaex-rea-forge@novaexopia
```
Self-contained, stdlib Python 3 only, no network, no daemons.

## Hooks / kill switch
None registered, so nothing to kill-switch. Scripts only run when you invoke them; they never write into the target repo (graph data goes to `--out`).

## Use
```
python3 scripts/harvest.py <repo> --out /tmp/x [--crg]
python3 scripts/wrap.py /tmp/x/CAPABILITY_CARD.json [--index N] [--bin-dir ~/.local/bin]
python3 scripts/sync.py save|check|apply <fork> <ref|patch-dir>
```
Parts used and missing: see SOURCES.md.

## Tested on device
`sh tests/selftest.sh` (Termux, arm64, 2026-11-04):
```
PASS plugin.json
PASS harvest-card
PASS wrap-runs
PASS wrap-skill
PASS sync-roundtrip
PASS code-map-loads
SELFTEST PASS
```
Note: generated shims use `#!/usr/bin/env sh`; on this phone run them as `sh shim` unless termux-exec is active.

## Install
```
/plugin install nvaex-rea-forge --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-rea-forge@novaexopia`. Swap out: `claude plugin disable nvaex-rea-forge@novaexopia`.
