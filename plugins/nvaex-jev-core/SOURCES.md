# Sources

Donors live in `~/.claude/plugins/synced/a5d13a90.../<id8>/` (S1). Every upstream LICENSE is kept verbatim in `licenses/<donor>`; the two identical Apache-2.0 texts (llm-dark-patterns, searchoclock) are one file. All content below is rewritten and condensed, no donor file is copied verbatim; "before" is the donor folder (`du -sk`, from FOLD-MAP), "after" is bytes written here (approximate where a donor shares a file).

| Donor (id8, version, license) | Folded as | Stripped | Before | After |
|---|---|---|---|---|
| chuck (9fe74888, 0.4.0, Apache-2.0) | `scripts/route.py` decision ledger (tag match, rejected-option CONTRADICTION flag, 400-char cap) and keyword rule files, `jev-router` section | HTML wizards, TF-IDF engine, session store, star commands, context bracket, 18KB hook | 137 KB | ~1.9 KB |
| frontier-simplify (f14c17b3, 2.1.0, MIT) | `skills/simplify-process` (7 rules) | audit and review skills, benchmarks, dogfood, review scripts, 5.9MB assets | 5900 KB | 1.4 KB |
| loop-and-gate-build-kit (de15c98b, 0.3.0, MIT) | `skills/decision-gate` (Gate infinity, gates 0-9, operating rules) | per-gate prose, fan-out, pipeline snapshot, vault logging, templates | 151 KB | 1.5 KB |
| no-cape (79d761f9, 2.1.0, MIT) | `skills/fail-loud-escalate`, `skills/verify-before-done` | 12 other skills, command router, hooks.off (session-start, stop, prompt) | 226 KB | 3.0 KB (shared) |
| superpowers (6ba53849, 6.4.2, MIT) | `skills/verify-before-done` (merged with no-cape), `systematic-debugging`, `writing-plans` | 12 other skills, SessionStart "MUST invoke" hook, multi-harness manifests, docs | 2686 KB | 3.9 KB |
| claude-code-audit-stack (69f86485, MIT) | `agents/claim-auditor.md` (read-only, tools: Read) | other agents, hooks, examples, reports | 124 KB | 1.7 KB |
| spec-drift (f3bd4ce7, 1.0.0, MIT) | `skills/spec-check` (checklist capture + drift types) | commands, index/archive machinery, runtime tier, verified-at markers, fixtures, CI | 684 KB | 1.4 KB |
| agent-discussion (4e3163e1, 0.1.0, MIT) | `skills/peer-sessions` (shared-file protocol) | inotify watcher script (not on Termux; polling line instead), evals | 69 KB | 0.9 KB (shared) |
| backlog (b38c2c6a, 2.4.3, MIT) | `skills/backlog` + `scripts/backlog.py` (stdlib JSONL: add/list/next/start/done/block/handoff, dependencies) | npm MCP server, agentdb, 6 skills, planner agent, hooks, dist | 777 KB | 4.0 KB |
| cc (ff18ea72, 0.6.0, MIT) | `commands/peers.md` + `scripts/peers.py` (reads `~/.claude/sessions`, read-only, drops dead pids) | mailbox, cc_send MCP server, enrichment hooks (shared state, would need a kill switch), batch scripts | 229 KB | 1.1 KB |
| crewmarshal (48061658, 0.24.0, MIT) | `skills/delegate` (plan check, brief shape, dispatch, checkpoint verification, review to GO) | 11 skills (133KB), hooks, specs, plans, docs | 517 KB | 2.1 KB |
| noetic-control-room (9dee1509, 0.3.4, Apache-2.0) | `skills/delegate` (EPIC brief, READY landing, decision desk) | gh-desk and ready-check scripts, cloud-worker setup, templates | 138 KB | in delegate |
| skill-gate (144a7e2e, 0.2.2, MIT) | `scripts/gate.py` PreToolUse(Skill) nudge from `.claude/skill-gate.json`, `jev-router` section | blocking behaviour, focus-guard skill, list-skills helper, githooks, 201-line hook | 183 KB | ~1.3 KB |
| searchoclock (ed67ab32, 0.3.0, Apache-2.0) | `skills/research-on-failure`, `scripts/fail.py` PostToolUseFailure(Bash) date-aware nudge, debounced 10 min | 38KB searchoclock.sh, agents, command, PreToolUse and PostToolUse hooks, docs | 2975 KB | 2.3 KB |
| airquote (890ae788, 0.1.0, MIT) | `drunken-master` dictation-cleanup paragraph and keep-blocks rule; `route.py` strips code, paths, URLs before garble check | TypeScript register/rewrite hook, model call, modes, settings | 394 KB | ~0.6 KB |
| claude-time (bd69ea1e, 0.1.0, MIT) | one `Now:` line in the existing UserPromptSubmit entry | separate hook entry, jq dependency, message stamping | 54 KB | 0.2 KB |
| drunken-master (fda4eab2, 1.1.3, MIT) | `skills/drunken-master` condensed | Russian examples, long worked examples | 297 KB (SKILL 9.7 KB) | 3.1 KB |
| llm-dark-patterns (1fee4b38, 1.2.1, Apache-2.0) | `scripts/scorecard.py`: 26 message checks (was 13) using `packs/locale/en.txt` vocabulary and the hook regexes | blocking exits, Rust path, packs, paper, evaluation, 5.8MB | 5788 KB | 7.6 KB |
| claude-eta, claude-jev (4a989cf6, 0.1.1, MIT), building-with-typesafe-jev (5ac9a71c, MIT), jev | no code copied. Ideas: 5-call cadence and repeat-edit loop in `health.py`; two-stage router. `scripts/jev_route.py` is written here against the HTTP contract in building-with-typesafe-jev `api-reference.md`, checked against docs.typesafe.ai/api/system-one on 2026-11-06; the 0.75/0.65 gate and head-and-tail cut are claude-jev ideas | TS dist, MCP runtime, SDK, telemetry | 12.7 MB | 12 KB (jev_route.py, health.py) |

## Not folded
- **jevmem (7d57870a, 71 KB):** plugin holds only a launcher for the npm `jevmem` CLI, which POSTs to https://api.typesafe.ai with a TypeSafe key. Nothing copied. Its redaction list informed `jev_route.py`. Its add/search function is rebuilt locally as the `jev.remember` tool in `mcp/jev-rea-mcp` (no network, no key); its guard, always-on rules and audit_memory are not rebuilt. Operator's drop decision on the plugin itself (FOLD-MAP row 33) still pending.
- **llm-dark-patterns, 7 donor hooks not folded:** no-approval-sneak (PreToolUse), no-chat-retention, no-count-drift, no-credential-leak-in-handoff (TaskCreated), no-handoff-loop, no-ownership-violation (TaskCompleted), no-unreachable-symbol. They need other events (one hook entry per event rule) or repo state; the 5 `state-*` continuity hooks belong to nvaex-memory. The FOLD-MAP note "hooks/*.sh absent" was wrong: the 30 scripts exist under `hooks.off-20261028/` in the donor.
- **JEV-Level-0-3-Taxonomy-Classification-Matrix.csv:** Drive only; the fallback levels in `jev_route.py` stay a length and keyword heuristic.
- **context-protector, safe-bash:** no plugin of these names found under `~/.claude/plugins`, `~/local-plugins`, `~/repos`.
- **task-observer:** whole port with its own plugin dir (FOLD-MAP row 141), not in this package; disable the global `~/repos/aesop-task-observer` copy when it is enabled to avoid a double trigger.

## Derived, written here
| File | Derived from |
|---|---|
| `skills/jev-router/tiers.json`, tier line in `scripts/route.py` | CLAUDE.md Subagents standing order (haiku lookup / sonnet routine / opus-fable hard); Hyperion-XI `docs/FAST-TRACK-3APK-AESC.md` Part B (Tier 1 Architect plans; Board seat Architect = Fable 5.1); model ids from the operator 2026-11-05. Level-to-tier and task-type minimums are assigned here, marked as such inside the file. The doc's four seats (Gemini/Bridge/agy/Claude Code) are vendor seats, not Claude tiers: recorded under `external_seats_not_routed`, not routed |
| `skills/jev-router/` (+ groups.json), `scripts/route.py`, `scripts/jev_route.py` | claude-jev two-stage idea; chuck, skill-gate, claude-time, airquote parts above. Operator's order 2026-11-05: routing calls TypeSafe Jev (contract rule 6 allows network when the spec requires it). `jev_route.py` merges the old `route.py` rules and the old `jev-rea-mcp` rules: the server's keywords moved into `groups.json`, its L2/L3 patterns and taxonomy reader moved unchanged. Group `desc` text and the question wording are written here |
| `mcp/jev-rea-mcp/` | moved from `plugins/jev-rea-mcp`; its own `SOURCES.md` covers it |
| `skills/task-auditor/`, `scripts/health.py` | spec's 5 gates; claude-eta every-5-calls cadence and repeat-edit idea |
| `scripts/killswitch.sh` | `tools/plugin-shared/killswitch.sh` via `bin/vendor-shared.sh` |
