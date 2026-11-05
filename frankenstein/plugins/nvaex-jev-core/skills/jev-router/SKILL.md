---
name: jev-router
description: Two-stage skill router. Use at the start of a multi-step task to choose a domain group (3-5) and then 1-2 skills in it, instead of scanning every skill. Honors the "JEV route:" line injected by the nvaex-jev-core UserPromptSubmit hook.
---

# JEV router (System 1)

Stage 1: pick up to 3 domain groups from `groups.json` (this folder): build, research, memory, wiki, device, review, plan.
Stage 2: inside those groups load at most 2 skills. Never load more.

Levels (hook estimate; override when wrong):
- L0 trivial: answer inline, no skill.
- L1 single bounded task: 1 skill, no subagent.
- L2 multi-step: task-auditor gates 1-5, subagents with isolated scope for independent parts.
- L3 cross-repo or irreversible: L2 plus operator confirmation before any destructive step.

If the hook line says "no group matched", do not guess a skill; proceed inline.
Edit `groups.json` to retarget; it is plain data.
