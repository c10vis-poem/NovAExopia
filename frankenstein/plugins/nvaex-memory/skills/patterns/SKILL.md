---
name: patterns
description: Find recurring patterns in recent sessions; propose captures (rule, note, fix). Use on /patterns or 'keeps coming up'.
---
Folded from claude-patterns 1.0.0 (Instinct Engine). The vault prefs interview, journal reads and install-ping are dropped.

1. Gather, silently: `ccfind search <topic> --json` for recent sessions, the last 10-15 entries of `memory/decisions.md` if present, and the latest `<recaps>/memory/*.md` days.
2. Look for: same topic 3+ times in different sessions; repeating decision logic ("when X, always Y"); operator corrections that echo earlier ones; a task that took 5+ tool calls though routine; a backtrack whose working path is worth keeping.
3. Present at most 5 proposals, each quoting the exact phrase or event, the count, and the proposed capture (rule text, note, or "bake into skill S"). Ask which to capture.
4. After approval only: apply the approved captures in one pass. A CLAUDE.md rule goes through the operator's normal edit approval.
End-of-session self-check: if a trigger fired, offer one line ("you corrected me on X twice; capture as a rule?"). Do not run a full scan unasked.
