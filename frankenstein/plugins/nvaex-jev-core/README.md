# nvaex-jev-core

System-1 router and discipline set for the Frankenstein stack. Local, stdlib Python, no network, no daemons, nothing blocks.

## What is in it
| Part | Does |
|---|---|
| `drunken-master` | Stage 0: repairs garbled or dictated input, prints `Read as: ...` first |
| `jev-router` | picks a skill group (L0-L3) and a model tier (`tiers.json`), injects project decisions with a contradiction flag, keyword rules, the current time |
| `task-auditor` | 5 gates; Gate 3 nudges every 5 tool calls and on 3x repeat edits |
| `verify-before-done`, `systematic-debugging`, `writing-plans` | trimmed from superpowers |
| `fail-loud-escalate`, `simplify-process` | trimmed from no-cape, frontier-simplify |
| `decision-gate`, `spec-check` | human gates 0-9; requirements versus built |
| `delegate`, `peer-sessions`, `backlog` | outside executors, live sessions and shared-file debate, cross-session task list |
| `research-on-failure` | date-aware research before patching a failure |
| `agents/claim-auditor` | read-only math audit of probability and EV claims |
| `/peers` | lists other live Claude Code sessions |
| Stop scorecard | 26 dark-pattern checks, warns only |

Model tiers: `skills/jev-router/tiers.json` maps L0-L3 and task types to claude-haiku-5-5 / sonnet-5-5 / opus-5-5 / fable-5-1; the `JEV route:` line shows `tier <model>`. Each tier records its source in the file. `jev-rea-mcp`'s `jev.route_task` returns the same tier from its own copy (`data/tiers.json`). Project memory that replaces the jevmem plugin is the `jev.remember` tool in `jev-rea-mcp`.

Project memory read by the router (all optional): `.nvaex/decisions.jsonl`, `.nvaex/rules/*.md`, `.claude/skill-gate.json`. Formats are in `skills/jev-router/SKILL.md`. Backlog: `python3 scripts/backlog.py`.

## Swap
```
claude plugin enable  nvaex-jev-core@novaexopia
claude plugin disable nvaex-jev-core@novaexopia
```
Self-contained; works with any other package disabled. Refresh the vendored kill switch: `sh bin/vendor-shared.sh`.

## Hooks (one entry per event, kill switch first)
| Event | Hook name | Script | Does |
|---|---|---|---|
| UserPromptSubmit | route | scripts/route.py | time, Stage 0, router, decisions, rules |
| PreToolUse (Skill) | gate | scripts/gate.py | note when a skill is on the project's confirm list |
| PostToolUse | health | scripts/health.py | Gate 3 cadence and repeat-edit loop |
| PostToolUseFailure (Bash) | fail | scripts/fail.py | date-aware research nudge, once per 10 min |
| Stop | scorecard | scripts/scorecard.py | 26 checks, log at `~/.claude/state/nvaex-jev-core/scorecard.jsonl` |

Off for all: `touch ~/.nvaex-hooks-off`. Off for the package: `touch ~/.claude/state/off/nvaex-jev-core`. One hook: `touch ~/.claude/state/off/nvaex-jev-core.<hook-name>`. Revoke: delete the file. `#skip-enforce` in a prompt skips routing. No hook blocks, so there is no override to name.

Origins, sizes, and what was not folded: `SOURCES.md`. Upstream licenses: `licenses/`.

## Tested on device
Termux, Python 3.14, `sh tests/selftest.sh` (isolated HOME; runs the real `hooks.json` commands and scripts; includes false-positive and kill-switch cases). Output tail (isolated HOME; the run also asserts tiers.json ids, route-line tier for L2 debug, L1 build and plan floor, and fail-open when the file is missing):
```
PASS per-package killswitch
PASS backlog next = unblocked highest
PASS blocked task marked waiting
PASS dependency released after done
PASS handoff groups states
PASS task over 200 chars rejected
PASS peers lists live only
SELFTEST PASS
```

## Install
```
/plugin install nvaex-jev-core --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-jev-core@novaexopia`.
