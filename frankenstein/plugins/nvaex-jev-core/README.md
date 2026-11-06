# nvaex-jev-core

System-1 router and discipline set for the Frankenstein stack. Stdlib Python, no daemons, nothing blocks. One install gives the hooks, the skills and the `jev-rea-mcp` server with its 3 tools. The router asks TypeSafe Jev when a key is set; everything else is local.

## What is in it
| Part | Does |
|---|---|
| `drunken-master` | Stage 0: repairs garbled or dictated input, prints `Read as: ...` first |
| `jev-router` | gets the level (L0-L3) and skill group from TypeSafe Jev, or the keyword rules as fallback; picks a model tier (`tiers.json`); injects project decisions with a contradiction flag, rule files, the current time |
| `mcp/jev-rea-mcp` | MCP server, 3 tools: `jev.route_task` (same router as the hook), `jev.audit_gate`, `jev.remember`. See its README |
| `task-auditor` | 5 gates; Gate 3 nudges every 5 tool calls and on 3x repeat edits |
| `verify-before-done`, `systematic-debugging`, `writing-plans` | trimmed from superpowers |
| `fail-loud-escalate`, `simplify-process` | trimmed from no-cape, frontier-simplify |
| `decision-gate`, `spec-check` | human gates 0-9; requirements versus built |
| `delegate`, `peer-sessions`, `backlog` | outside executors, live sessions and shared-file debate, cross-session task list |
| `research-on-failure` | date-aware research before patching a failure |
| `agents/claim-auditor` | read-only math audit of probability and EV claims |
| `/peers` | lists other live Claude Code sessions |
| Stop scorecard | 26 dark-pattern checks, warns only |

Model tiers: `skills/jev-router/tiers.json` (the only copy) maps L0-L3 and task types to claude-haiku-5-5 / sonnet-5-5 / opus-5-5 / fable-5-1; the `JEV route:` line shows `tier <model>`. Each tier records its source in the file. Project memory that replaces the jevmem plugin is the `jev.remember` tool in `jev-rea-mcp`.

## Routing
`scripts/jev_route.py` is the one router. The hook (`scripts/route.py`) and `jev.route_task` both call `classify()`.

- **Jev call:** `POST https://api.typesafe.ai/v1/systemone`, `Authorization: Bearer <key>`, model `jev-latest` (`TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL` change these). Two typed questions on `state.task`: a Score for the level (4 described situations; the most probable level is used) and a Choice for the group (groups from `groups.json` plus `none_of_the_above`; a further option above 0.25 also counts).
- **Key:** the plugin's `typesafe_api_key` setting (masked, kept in secure storage, reaches hooks as `CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY`), or `TYPESAFE_API_KEY` in the environment. Without one, nothing leaves the phone.
- **Source is always stated.** The route line ends `via typesafe <model> conf <level>/<group>` (with `LOW: check it` under 0.65/0.75) or `via local-fallback (<reason>)`. The tool returns `source` and `error`. Reasons: `no-key`, `bad-key-format`, `typesafe-off`, `bad-base-url`, `no-groups-file`, `http-<status>`, `timeout`, `network`, `bad-response`, `error-<type>`. Reasons are fixed codes, never exception text, so a key cannot be quoted.
- **Fallback:** taxonomy CSV if present (`skills/jev-router/taxonomy.csv` or `JEV_TAXONOMY_CSV`), else keyword and length rules.
- **Code floor:** `rm -rf`, force push, `drop table`, rewriting history, all repos and cross-repo hold L3 whatever Jev says. Jev can raise a level, never lower one of these.
- **Timing:** hard deadline 2 s in the hook (`JEV_TIMEOUT`), 6 s in the tool, no retries; a 429 or 529 falls back for that prompt. The hook entry allows 5 s and always exits 0.
- **What leaves the phone:** with a key set, every routed prompt, after redaction: API keys and tokens, `name=value` secrets, bearer tokens, URL credentials, private keys, JWTs, email addresses, long opaque strings. Best effort, so do not paste secrets. Cut to 8000 characters. Slash commands and `#skip-enforce` prompts are never sent. Redirects are not followed, and plain http is refused except to localhost.
- **Off switch for the Jev call only:** `touch ~/.claude/state/off/nvaex-jev-core.typesafe`. Routing stays on, local only.
- **Log:** `~/.claude/state/nvaex-jev-core/route.jsonl`: level, groups, source, error, model, milliseconds. Never the prompt.
- **Live check:** `TYPESAFE_API_KEY=... sh tests/live.sh` sends one real request and exits 0 only if TypeSafe answered.

Project memory read by the router (all optional): `.nvaex/decisions.jsonl`, `.nvaex/rules/*.md`, `.claude/skill-gate.json`. Formats are in `skills/jev-router/SKILL.md`. Backlog: `python3 scripts/backlog.py`.

## Swap
```
claude plugin enable  nvaex-jev-core@novaexopia
claude plugin disable nvaex-jev-core@novaexopia
```
Self-contained; works with any other package disabled (the selftest copies it out of the tree and runs the hook and the server). `groups.json` also names skills held by other packages; with those disabled, the `try` hint can name a skill that is not loaded. Refresh the vendored kill switch: `sh bin/vendor-shared.sh`.

## Hooks (one entry per event, kill switch first)
| Event | Hook name | Script | Does |
|---|---|---|---|
| UserPromptSubmit | route | scripts/route.py | time, Stage 0, router (Jev or fallback), decisions, rules |
| PreToolUse (Skill) | gate | scripts/gate.py | note when a skill is on the project's confirm list |
| PostToolUse | health | scripts/health.py | Gate 3 cadence and repeat-edit loop |
| PostToolUseFailure (Bash) | fail | scripts/fail.py | date-aware research nudge, once per 10 min |
| Stop | scorecard | scripts/scorecard.py | 26 checks, log at `~/.claude/state/nvaex-jev-core/scorecard.jsonl` |

Off for all: `touch ~/.nvaex-hooks-off`. Off for the package: `touch ~/.claude/state/off/nvaex-jev-core`. One hook: `touch ~/.claude/state/off/nvaex-jev-core.<hook-name>`. Revoke: delete the file. `#skip-enforce` in a prompt skips routing. No hook blocks, so there is no override to name.

Origins, sizes, and what was not folded: `SOURCES.md`. Upstream licenses: `licenses/`.

## Tested on device
Termux, Python 3.14, `bash tests/selftest.sh` (isolated HOME; runs the real `hooks.json` commands and scripts). 97 checks pass, 0 fail, including the 21 of `mcp/jev-rea-mcp/tests/selftest.sh`, a run of the package copied out of the tree, and a check that fails if `groups.json` names a skill no package holds.

The Jev checks marked `FAKE` run against `tests/fake_typesafe.py`, a local stand-in that enforces the documented request shape. They prove the client: request shape, redaction, each fallback reason, deadline, no redirect. They do not prove Jev's answers. Against the real endpoint, the real client was run only with a deliberately invalid key: it got a real 401 and fell back with `http-401` in 144 ms. A successful live answer has not been seen yet: no TypeSafe key was on the phone. Run `tests/live.sh` once a key is set.

## Install
```
/plugin install nvaex-jev-core --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-jev-core@novaexopia`.
