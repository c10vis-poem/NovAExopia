# nvaex-rea-forge
Fork harvester and packager. Parts folded from stock plugins (see SOURCES.md), nothing runs stock.

| piece | does |
|---|---|
| `/rea-harvest <repo> [--crg]` (`scripts/harvest.py`) | Python AST scan, optional Tree-sitter graph via `code-review-graph`; writes `CAPABILITY_CARD.json`, picks a packaging gate (skill / cli-wrap / mcp-core) |
| `scripts/wrap.py` | harvested CLI entrypoint -> shell shim + SKILL.md |
| `mcp2cli` skill + `scripts/mcp2cli.py` | MCP stdio server -> shell CLI + SKILL.md (stdlib, per-call server, nothing left running) |
| `rea-review` skill + `adversarial-reviewer` agent + `quote_check.py` | blind drafts, vote baseline, only verbatim quotes verified `v` move the verdict (from colosseum) |
| `rea-customize`, `rea-sync` + `scripts/upstream.py` | keep fork-vs-upstream intent, find the next stable upstream tag, prune stale intent; never commits or pushes (from turbocharge) |
| `code-map` skill | data.json -> self-contained HTML architecture map |
| `mindmap` skill + `check.py` | input -> Markmap `.md`, validated |
| `code-archaeologist`, `integration-verifier` agents | adversarial strip loop |

## Swap
```
claude plugin enable  nvaex-rea-forge@novaexopia
claude plugin disable nvaex-rea-forge@novaexopia
```
Self-contained, stdlib Python 3 plus Node built-ins, no network, no daemons.

## Hooks / kill switch
None registered, so nothing to kill-switch: every script runs only when invoked and never writes into the target repo.

## Use
```
python3 scripts/harvest.py <repo> --out /tmp/x [--crg]
python3 scripts/wrap.py /tmp/x/CAPABILITY_CARD.json [--index N] [--bin-dir DIR]
python3 scripts/mcp2cli.py gen <name> <outdir> <server cmd...>
python3 scripts/upstream.py init|next|prune <fork> ...
```

## Not done
- `rea-review` reviewers read local files or pages you saved; the `claw.search` hookup waits for claw-mcp.
- mindmap has no HTML render (needs `npx markmap-cli`, network).
- Generated shims use `#!/usr/bin/env sh`; on this phone run them as `sh shim` unless termux-exec is active.

## Tested on device
`sh tests/selftest.sh` (Termux, arm64, 2026-11-05). Checks run real code on fixtures: harvest card, wrapped CLI output, quote verdicts v/n/u, upstream tag selection and prune, mcp2cli against a fake stdio MCP server (call, error exit, SKILL text), Markmap validator, code-map validation and render. Mutating `upstream.py` makes it fail.
```
PASS manifest
PASS harvest-card
PASS wrap-runs
PASS wrap-skill
PASS quote-check
PASS upstream-sync
PASS mcp2cli
PASS mindmap
PASS code-map
INFO crg backend: code-review-graph
SELFTEST PASS
```

## Install
```
/plugin install nvaex-rea-forge --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein2` then `claude plugin install nvaex-rea-forge@novaexopia`.
