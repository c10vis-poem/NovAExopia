# Sources
Sizes are file bytes: donor whole plugin dir (before) -> what is shipped here (after).

| shipped path | origin plugin (phone path under `~/.claude/plugins/synced/a5d13a90-.../`) | version | license | before -> after |
|---|---|---|---|---|
| skills/code-map/{SKILL.md,scripts/generate.mjs,template/engine.html,reference/schema.md,LICENSE} | `code-map` (Sadi Mohammad Mustafa), `73654592-.../` | 0.1.0 | MIT | engine.html 51,131 -> 41,537 (comments and indentation stripped, script syntax-checked); examples/ dropped; SKILL.md dangling `examples/` links removed |
| skills/rea-review/{SKILL.md,quote_check.py,LICENSE}, agents/adversarial-reviewer.md | `colosseum` (Jinho Choi), `2c6cd435-.../` (adversarial reviewer + verified-quote rule) | 1.0.0 | MIT | 1,642 KB -> ~13 KB. Kept: quote matcher (English only), participant prompt reduced to a read-only reviewer, protocol rules 4-6,8,10 as 6 steps. Stripped: WebSearch/WebFetch calls (claw.search later), 7 hooks/scripts, external-CLI relay, 4 workflows, evals, Korean docs, logo, 3 modes |
| skills/rea-customize/{SKILL.md,LICENSE}, skills/rea-sync/SKILL.md, scripts/upstream.py | `turbocharge` #2 (Andre Guerlain), `71dabb73-.../` (customize-plugin, setup-plugin-customization, sync-plugin-customizations) | 0.1.0 | MIT | 89 KB (3 SKILLs 24,208 B) -> 2.4 KB of skills + 2.8 KB script. Stripped: auto commit/push/clone steps, cron wording, cursor-plugin, logo. Replaced the old `sync.py` patch-ledger stub |
| skills/mcp2cli/{SKILL.md,LICENSE}, scripts/mcp2cli.py | `mcp2cli` (mason), `3763173a-.../` (mcp-analyze, mcp-codegen) | 0.1.0 | MIT | 126 KB -> 1.4 KB skill + 3.6 KB generator. Stripped: agent, 3 commands, skill-author, TS/commander/tsup scaffolds and tier templates (the generator is stdlib Python and needs no codegen) |
| skills/mindmap/{SKILL.md,scripts/check.py,LICENSE} | `mindmap-skills` plugin `mindmap` (Haixia Cheng), `fd6bdacf-.../` (also in account `bf59ea3a-...`) | 0.3.0 | MIT | 284 KB -> 1.8 KB. Kept: skills/mindmap input rules and Markmap format. Stripped: mindmap-zh, examples, docs, tests, workflows, README.zh, judge-panel, degrade-rich.mjs, render.sh (needs `npx` and network) |
| scripts/harvest.py, scripts/wrap.py, skills/rea-harvest, agents/code-archaeologist, agents/integration-verifier, commands/rea-harvest.md | authored here (blueprint Sec. 2 row 4, 3B) | 0.2.0 | MIT | n/a |

**Package total (file bytes, git HEAD vs now):** 86,566 -> 107,563. The package grew by the four new folds (+~35 KB incl. 5 LICENSE files and a 6.9 KB selftest) net of the code-map trim (-9.6 KB) and removing sync.py (-1.4 KB); donors totalled ~3.7 MB.

## Used as external tools (not copied)
- `code-review-graph` CLI (`~/bin/code-review-graph`), optional via `--crg` in harvest.py.
- `~/repos/NvAEx-rea` and `~/repos/NvAEx-reverse-skill`: present, not copied (too heavy for a hot-swap package); use in place for binary/APK teardown.

## Missing / not folded
- `claude-war-room`: removed by the operator 2026-11-05; the two authored agents stay as thin read-only prompts.
- `wrap.py` is kept: it wraps a harvested CLI entrypoint from a CAPABILITY_CARD, which `mcp2cli` (MCP servers only) does not do.
- `NvAEx-code-review-graph` fork dir: not at `~/repos/` by `ls`; the installed `code-review-graph` CLI is used.
- `ECC-aesop`, `graphify` clustering: not bundled (graphify is a separate install).

## Moved in from this repo
| shipped path | from | note |
|---|---|---|
| scripts/inspect_target.py | `nvaex-jev-core/mcp/jev-rea-mcp/server.py` `inspect()` (spec "REA static repo inspection") | moved unchanged; read-only stdlib walk; no NvAEx-rea code used |
| mcp/rea-mcp/ | written here | custom-first; no donor code |

## Missing
- REA dynamic inspection (NvAEx-rea is a TS/Node reverse-engineering suite, `~/repos/NvAEx-rea`): only static read-only inspection here; dynamic analysis would need a daemon/Node and is out of contract.
