---
name: memory-bank
description: Maintain the six-file memory-bank/ folder. Use on 'initialize/update/read memory bank' or when a repo has memory-bank/.
---
Folded from Memory Bank (templates condensed; its blocking Stop hook, CoC, SECURITY and PRIVACY docs are not included).

Files in `memory-bank/` at the repo root: `projectbrief` (goals, scope), `productContext` (why, UX goals), `systemPatterns` (architecture, decisions, patterns), `techContext` (stack, setup, constraints), `progress` (works, left, status, issues), `activeContext` (current focus, recent changes, next steps, active decisions, learnings).

- Start of a task: if `memory-bank/` exists, read all six, `activeContext` last. Note any missing file.
- Initialize: confirm before overwriting; derive real content from the code, README and configs, not empty stubs; one `# Title` plus the headings above per file.
- Update ("update memory bank" reviews all six): `activeContext` almost always; `progress` after milestones; the rest only when they changed. Overwrite stale text, do not append a log. About one page per file; split overflow into a linked sub-file. Write for a reader who has never seen the project.
