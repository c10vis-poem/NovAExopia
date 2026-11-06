---
name: handoff
description: Write or refresh the git branch's handoff note. Use when finishing work, before ending a session, or on /handoff.
---
Capture what the diff cannot show. Folded from handoff 1.0.0 (branch notes) and context-handoff (field rules); the manifest MCP is not included.

Skip trunk branches (`main master dev develop trunk release/* hotfix/*`): they never load a note.

1. `branch=$(git rev-parse --abbrev-ref HEAD); note="$(git rev-parse --git-common-dir)/handoffs/${branch//\//__}.md"; mkdir -p "$(dirname "$note")"`
   (inside `.git`: follows the branch across worktrees, never shows in a diff).
2. **Overwrite** `$note` (never append). First line exactly `<!-- commit: $(git rev-parse HEAD) -->` (the loader flags the note STALE when HEAD moved).
3. Sections, telegraphese, no code snippets, under ~25KB:
   - **Goal**: what and why (core intent).
   - **Status**: done and working; deliberately not done.
   - **Open / next**: verb-anchored next action, blockers, pending decisions.
   - **Decisions**: choice + reason + alternative rejected.
   - **Failed**: `Approach -> Result -> Lesson` so the next session does not repeat it.
   - **Gotchas**: non-obvious coupling, things that look wrong but are intentional, env vars, conventions.
   - **Map**: `file:line` of load-bearing code.
   - **Verify**: exact build/test commands and what green looks like.
   Record human decisions only where you can point at them in the conversation.
4. Tell the operator it saved. Loading skips with `HANDOFF_SKIP=1`.

Search old notes: `grep -il <term> "$(git rev-parse --git-common-dir)"/handoffs/*.md`, then read only the match. Prune notes whose branch is gone, after the operator confirms.
