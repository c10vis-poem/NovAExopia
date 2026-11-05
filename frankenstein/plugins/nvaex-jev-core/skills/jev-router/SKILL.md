---
name: jev-router
description: Two-stage skill router plus per-project decision memory. Use at the start of a multi-step task to pick a domain group and then 1-2 skills, and honor the "JEV route:", "DECISIONS:" and "RULE" lines the UserPromptSubmit hook injects.
---
# JEV router (System 1)

Stage 1: up to 3 groups from `groups.json` (this folder). Stage 2: at most 2 skills inside them. Never more.

Levels (hook estimate; override when wrong):
- L0 trivial: answer inline.
- L1 one bounded task: 1 skill, no subagent.
- L2 multi-step: task-auditor gates; subagents with isolated scope for independent parts.
- L3 cross-repo or irreversible: L2 plus operator confirmation before any destructive step.
Model tier (`tiers.json`, this folder; the hook line shows `tier <model>`): L0 haiku-5-5, L1 sonnet-5-5, L2 opus-5-5, L3 fable-5-1; a task type can raise it (debug, coordinate -> opus; plan -> fable) but never lower it. Use it when sizing a subagent's model. If the line has no tier, the file is missing: pick by judgment.
"no group matched": proceed inline, do not guess a skill. `groups.json` is plain data; edit to retarget.

## Project memory the hook reads (all optional)
- `<project>/.nvaex/decisions.jsonl` (and `~/.nvaex/decisions.jsonl`), one JSON per line: `{"decision":"use sqlite","rejected":["postgres"],"tags":["db","storage"],"status":"active"}`. A prompt that shares a tag injects `Decided: ...`; one that names a rejected option injects `CONTRADICTION?`. On a contradiction, ask the user whether the decision changed before acting; if it did, set the old line's status to `superseded` and add the new one.
- `<project>/.nvaex/rules/*.md`: first line `keywords: a, b`; the body is injected when the prompt contains a keyword.
- `<project>/.claude/skill-gate.json`: `{"mode":"confirm","blocked":["skill-name"]}`. The PreToolUse hook only adds a note asking the user before that skill runs. `mode: off` disables it.
