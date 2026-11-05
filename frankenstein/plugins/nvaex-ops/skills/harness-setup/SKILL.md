---
disable-model-invocation: true
name: harness-setup
description: Scan a project and draft its agent instructions (AGENTS.md or CLAUDE.md), starting from a stack scan. Use when the operator wants a first harness for a repo. Drafts only; writes nothing until the operator approves the text.
---

# harness-setup

Our own short version of a harness bootstrap. It needs only what this package ships.

## Steps
1. Scan: `python3 -I scripts/stack_scan.py PROJECT_DIR` (path relative to this skill). It lists languages by file count, build and test commands it can see (`package.json` scripts, `Makefile` targets, `pyproject`, `gradlew`, `Cargo.toml`, `go.mod`), CI files, existing instruction files, and top-level folders. Read-only; it ignores `.git`, `node_modules`, `build`.
2. Read what it cannot know: README, the entry points, one test file. Do not guess commands the scan did not find; mark them "unverified".
3. Draft the instruction file with only these sections: what the project is (2 lines), how to build/test (commands you saw), layout (the top folders), rules that are not obvious from the code, and what an agent must never do here. Keep it under about 60 lines. If the project has no `AGENTS.md`, prefer `AGENTS.md` (any agent reads it); use `CLAUDE.md` only for Claude-specific rules (hooks, skills, subagents, plugins).
4. Show the draft and the target path. Write only after the operator says yes.
5. Verify: run the build or test command you wrote, and say plainly if it was not run.
6. Then offer `harness-audit` on the result.

Not included: nine-phase orchestration, agent-team generation, playbook libraries, hook/MCP generation. Add those one at a time when a project proves it needs them.
