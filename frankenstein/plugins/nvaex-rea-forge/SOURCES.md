# Sources
| path | origin | version | license |
|---|---|---|---|
| skills/code-map/{SKILL.md,scripts/generate.mjs,template/engine.html,reference/schema.md,LICENSE} | plugin `code-map` (Sadi Mohammad Mustafa), `~/.claude/plugins/synced/a5d13a90-.../73654592-.../` | 0.1.0 | MIT |
| scripts/*.py, skills/rea-harvest, skills/rea-sync, agents/*, commands/* | authored here, informed by blueprint Sec. 2 row 4 and 3B | 0.1.0 | MIT |

Dropped from code-map: examples/ (demo JSON).

## Used as external tools (not copied)
- `code-review-graph` CLI (`~/bin/code-review-graph`), optional via `--crg`.
- `~/repos/NvAEx-rea` (REA MCP, TypeScript, ~large) and `~/repos/NvAEx-reverse-skill`: present, NOT copied; too heavy for a hot-swap package. Use them in place for deep binary/APK teardown.

## Missing (not found on the phone; not invented)
- `claude-war-room` (the two agents `code-archaeologist` / `integration-verifier` were authored fresh as thin read-only prompts).
- `turbocharge` `customize-and-sync`: turbocharge exists at `~/local-plugins/plugins/turbocharge` but has no such skill (grep for customize/sync found nothing); `scripts/sync.py` is a minimal patch-ledger replacement.
- `mcp2cli`: not installed; `wrap.py` is a plain shell-shim fallback.
- `NvAEx-code-review-graph` fork dir: not at `~/repos/`; the installed `code-review-graph` CLI is used.
- `ECC-aesop` (88 skills), `graphify` clustering: not bundled (out of scope for a small package; graphify skill is separately installed).
