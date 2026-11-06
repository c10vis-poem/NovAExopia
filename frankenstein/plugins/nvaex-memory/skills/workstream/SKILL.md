---
name: workstream
description: Park ideas and keep per-workstream notes in NvAEx-Recaps. Use on 'park this', 'add a workstream', 'what was open on X'.
---
Folded from memory-toolkit 1.9.13 (workstream, park, handoff text); its 37KB memory.js is not included. Plain files, no daemon.

Dir: `<recaps>/memory/workstreams/` (`$NVAEX_RECAPS`, default `~/repos/NvAEx-Recaps`; fallback `~/.claude/state/nvaex-memory/memory/`).
- `workstreams.json`: `{"<name>": ["keyword", ...]}`; the source of truth for routing. Add: edit the JSON.
- Park: write `<name>/<slug>.md` with frontmatter `name, description, type: project` and sections What / Why / Context (key details that die with this conversation). Convert relative dates to absolute.
- Per-workstream handoff: `<name>/handoff.md`, overwritten (state, next, context; under 20 lines).
- Lookup: `grep -ril <keyword> <dir>` then read the match; summarize, do not dump.
Do not store what git log, the code, or CLAUDE.md already say. Commit/push of the Recaps repo is the operator's step.
