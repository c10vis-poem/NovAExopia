---
name: delegate
description: Use when Claude plans and reviews while outside coding agents (Codex, Gemini, cloud sessions) implement, or when coordinating several workers on one repo.
---
# Delegate to outside executors

Claude architects and reviews. Executors implement on their own branch.

**Plan for delegation.** Plan detail follows the project, not a default. Before handoff check: each task has exact files and a failing-test-first step, interfaces between tasks are named, no two tasks share a file in one wave, acceptance can fail ("tests pass" is not acceptance), and the first task is unblocked. Assign by wave: lay shared contracts first, then fan out.

**Brief one worker.** First line fixed: `EPIC <id>: branch <prefix>/<id>-<slug>, scope and grants below.` Then scope as globs (narrow; overlapping scopes collide), grants (one-off path permission, usually none), acceptance, and protocol: branch from fresh integration branch, push every turn, open the PR, end with `EPIC <id> READY <sha> <pr-url>` or `EPIC <id> BLOCKED <reason>`. Strongest model for architecture, security and hard merges; a fast one for well-specified CRUD, UI polish, tests, docs. Show the brief to the user before sending unless told to send.

**Dispatch and wait.** One task per executor, in the background with a monitor. Never poll. Nobody idle while a ready task exists.

**Land READY.** Check the sha, the scope (diff outside scope fails), then checkpoint it: list every new symbol, grep its call-site in non-test code, drive the real path, read security-sensitive parts. Green tests over dead code are dead code. Merge `--no-ff` in a throwaway checkout, re-run checks, then push.

**Review to GO.** Use a reviewer other than the author, locked to one altitude (spec, plan, or diff). Each finding ships with fix options. Stop when a round finds nothing new; patches breed findings, so re-review only touched lines.

**Decision desk.** Anything only the human can decide is one issue with the full text and the recommended option marked. Do not bury it in chat.
