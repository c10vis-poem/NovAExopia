---
name: jev-router
description: "Read and honor TypeSafe Jev routing. Use at the start of a multi-step task and on JEV route:, DECISIONS: and RULE lines."
---
# JEV router (System 1)

Jev is the router and orchestrates the task audit layer; this skill only explains its output and decides nothing. Each prompt, Jev reads every package's generated `skills.json` outside your context, and the `JEV route:` line names every skill it picked, plus the groups that set the model tier (`groups.json`, this folder). With no index it lists every skill in the picked groups. There is no cap on groups or skills: load what the task needs from that list.

Level and groups come from TypeSafe Jev, or from the keyword rules when Jev is unavailable. The `JEV route:` line ends with which: `via typesafe <model> conf <level>/<group>` or `via local-fallback (<reason>)`. `LOW: check it` means Jev was unsure. The MCP tool `jev.route_task` gives the same answer as JSON. `rm -rf`, force push and similar shapes hold L3 whatever Jev says.

Levels (override when wrong):
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
