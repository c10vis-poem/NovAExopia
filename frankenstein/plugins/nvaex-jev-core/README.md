# nvaex-jev-core

System-1 router for the Frankenstein set. Local, stdlib Python, no network, no daemons, nothing blocks.

- **Stage-0 STT readback:** `drunken-master` skill (verbatim) plus a prompt hook that flags sound-alike/junk words and tells the model to print `Read as: ...` first.
- **JEV router:** `jev-router` skill + `skills/jev-router/groups.json` (7 groups, edit freely). Hook prints `JEV route: L0-L3 | groups | try skills`.
- **5-gate auditor:** `task-auditor` skill; Gate 3 is enforced as a nudge every 5 tool calls and on 3x repeat edits of one file.
- **Dark-pattern scorecard:** Stop hook, 13 checks (false_success, phantom_completion, test_modification_to_pass, silent_truncation, phantom_tool_call, vibe_eta, sycophancy, paternalism, wrap_up_bait, meta_commentary, disclaimer_spam, ai_tells, credential_leak). Warns via systemMessage, log at ~/.claude/state/nvaex-jev-core/scorecard.jsonl.

## Swap
```
claude plugin enable  nvaex-jev-core@novaexopia
claude plugin disable nvaex-jev-core@novaexopia
```
Self-contained; works with any other package disabled. Refresh vendored kill switch: `sh bin/vendor-shared.sh`.

## Hooks and kill switches
| Event | Hook name | Script |
|---|---|---|
| UserPromptSubmit | route | scripts/route.py |
| PostToolUse | health | scripts/health.py |
| Stop | scorecard | scripts/scorecard.py |

Off for all: `touch ~/.nvaex-hooks-off`. Off for the package: `touch ~/.claude/state/off/nvaex-jev-core`. One hook: `touch ~/.claude/state/off/nvaex-jev-core.<hook-name>`. Revoke: delete the file. `#skip-enforce` in a prompt skips routing. No hook blocks.

See SOURCES.md for origins and missing parts.

## Tested on device
Termux, Python 3.14, `sh tests/selftest.sh` (isolated HOME, runs the real hooks.json commands):
```
PASS manifest
PASS one entry per event
PASS drunken-master
PASS route+stage0
PASS skip-enforce
PASS gate3 every 5
PASS scorecard non-blocking
PASS clean stop exits 0
PASS global killswitch
PASS per-hook killswitch
SELFTEST PASS
```

## Install
```
/plugin install nvaex-jev-core --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-jev-core@novaexopia`. Swap out: `claude plugin disable nvaex-jev-core@novaexopia`.
