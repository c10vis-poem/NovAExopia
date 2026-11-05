# nvaex-ops

Operator toolbox: stock plugins stripped to the skills, commands and agents the operator keeps, folded into one package. No hooks, no MCP servers, no network at install. Swap with `claude plugin enable|disable nvaex-ops@novaexopia`.

## What is in it
| Group | Skills / commands / agents |
|---|---|
| Harness and plugin authoring | harness, harness-evolve, agent-architecture-decide, /analyze-agent, /create-agent, hook-development, plugin-structure, skill-development, plugin-package-repair, skills-updater, mcp-connect, build-mcp-server, tool-interface-repair, prompt-design, prompt-enhance, deconstruct, devil-advocate |
| CLAUDE.md and rules | claude-md-improver, /revise-claude-md, bake-claude-md-files, claude-perfectionist, rule-file-repair, rule-scope-audit, claude-automation-recommender |
| Review and security | /review-pr, review-council (+6 reviewers), public-repo-readiness |
| Repo and session care | sessions-list, projects-list, claude-backup-push/pull/setup, env-setup-wizard, my-tasks, github-cli |
| Google and cloud | cloud-run-deploy, firestore-rules, iam-audit, terraform-gcp, cloudflare, wrangler, workers-best-practices, durable-objects, supabase, design-critique, accessibility-review, context7 |

Routing: 15 skills are model-visible; the rest carry `disable-model-invocation: true` (user-invoked) so the package stays under the 30-tool misrouting threshold.

## Rebuilt in-house (were parked)
Our own code, agent-neutral (plain Markdown steps plus stdlib scripts; paths are relative to each skill, no Claude tool names):
| Skill | Script | What it does |
|---|---|---|
| google-setup | `google_oauth.py` | one skill for setup, add account, reauth of claw-mcp's Google token files (loopback OAuth, `check` lists files without values) |
| local-whisper | `transcribe.sh` | offline speech-to-text: ffmpeg then Parakeet (`parakeet-cli`, glibc) inside proot debian |
| tts | `speak.sh` | `termux-tts-speak`, falls back to `espeak-ng`; `--out` writes a WAV |
| skill-inventory | `inventory.py` | lists skills, flags duplicates and bad frontmatter |
| kotlin-lsp | `kt_check.py` | structural Kotlin check; no language server or compiler exists on this phone |
| mcp-tunnel | `tunnel.sh` | Cloudflare tunnel via `cloudflared`; stops because `cloudflared` is not installed |
| harness-setup, harness-audit | `stack_scan.py`, `config_audit.py` | stack scan and config audit |
| office-files | `office.py` | read/replace/split docx, xlsx, pptx, pdf |
`frankenstein/parked/` is empty (README only).

## Stock-plugin independence
No skill, agent or command points at another plugin: the selftest fails on any `<plugin>:<name>` reference that is not `nvaex-ops:<name>` or does not resolve to a file here. `claude-backup-*` scans for secrets with the shipped `.sync-manifest.json` and fails closed if it is missing.
The claude-security fold was removed (Anthropic-proprietary, no redistribution; this repo is public). Every remaining license in `licenses/` is MIT or Apache-2.0.

## Not folded
wizard, skill-creator, caveman, modern-web-guidance, firebase, build-companion: reasons in `SOURCES.md`.

## Hooks
None registered. Nothing here blocks or runs on its own, so there is no kill switch to wire.

## Tested on device
`bash tests/selftest.sh` (Termux, Android arm64, 2026-11-05):
```
ok  plugin.json valid; no hooks, no MCP server (nothing to kill-switch)
ok  all skills: name==dir, description set; 14 model-visible (<=20), rest user-invoked
ok  every script a skill points at exists in the package
ok  skill-dir refs resolve (env_audit, context7)
ok  all .py parse, all .sh pass bash -n
ok  upstream licenses kept (28 files), SOURCES.md present
ok  mytasks.sh: add/list/done/reject/answer, ids increment, injection sanitised, bad id fails
ok  context7.sh rejects an empty invocation
ok  cc.py (sessions/projects lister) starts
ok  every <plugin>:<name> reference is nvaex-ops:<name> and resolves (6 distinct)
ok  no claude-security skill, agents, workflow, scripts or license in the package
ok  tts: espeak-ng wrote a WAV; bad engine rejected
ok  local-whisper: espeak WAV -> Parakeet in proot read back 'Self-test'
ok  skill-inventory: this package clean; planted duplicate and missing frontmatter flagged
ok  kotlin-lsp: structural check passes a template string, fails unbalanced code (no compiler/LSP on this phone)
ok  mcp-tunnel: stops without token; with a stub cloudflared the token reaches it from env and is never printed
ok  google-setup: loopback OAuth against a fake token endpoint (PKCE, state check, 0600 file, no secret printed, reauth replaces)
ok  harness-setup scan runs; harness-audit flags planted wildcard permission and bad JSON, clean on this package
ok  office-files: docx/xlsx/pptx/pdf read, replace (original untouched), pdf page split
ok  claude-backup scan_for_secrets: clean passes, planted token fails, missing manifest fails closed
SELFTEST PASS (20 checks)
```
Per rebuilt item (what was proved, honestly):
- local-whisper: run for real. An espeak-ng WAV was transcribed by Parakeet in proot debian ("The quick brown fox jumps over the lazy dog." read back exactly; 2.2 s).
- tts: run for real. `termux-tts-speak` spoke (exit 0; audible output not confirmed by a listener), espeak-ng WAV written.
- skill-inventory: run for real on this package (0 problems) and on `~/.claude/skills` (found real duplicate names across synced copies).
- kotlin-lsp: structural check run for real on repo `.kt` files and planted bad code. No Kotlin compiler, gradle, ktlint or language server exists here: LSP is NOT available.
- mcp-tunnel: `cloudflared` is absent, so the skill stops (verified). The run path was tested only with a stub `cloudflared`.
- google-setup: `check` run for real (no token folder on this phone). The login flow was tested only against a fake token endpoint on 127.0.0.1. Real Google consent has not been done.
- harness-setup / harness-audit: run for real on this package and on `~` (found real findings); audit logic proved on planted fixtures.
- office-files: run for real on docx, xlsx, pptx and pdf files built during the test (python-docx and PyMuPDF made the docx and pdf; xlsx and pptx are hand-built minimal files, so real Excel/PowerPoint files with more structure are untested).
`claude plugin validate` was not re-run after this change.
Not tested: live context7, claudebase push/pull against GitHub, any skill's prose behaviour (skills were checked for existence and references only).
