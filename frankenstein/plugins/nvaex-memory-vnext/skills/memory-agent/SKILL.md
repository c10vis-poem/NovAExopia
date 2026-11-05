---
name: memory-agent
description: Daily episodic recap. At SessionEnd the plugin appends prompts and the last answer to NvAEx-Recaps/memory/YYYY-MM-DD.md plus a layers.jsonl row (autoPromote false). Use to explain where recaps go or to review them before promoting to MEMORY.md.
---
Mechanical, no model calls, no daemon. Secrets are redacted, instruction-shaped text is filtered.
Target: $NVAEX_RECAPS or config.json "recaps" (default ~/repos/NvAEx-Recaps) /memory/. If that repo is absent it falls back to ~/.claude/state/nvaex-memory-vnext/memory/ and never creates the repo.
Promotion into MEMORY.md is NOT automatic: review the day file, and let the JEV auditor (or the operator) promote. layers.jsonl rows carry `"autoPromote": false`.
Re-run is idempotent per session id. Commit/push of NvAEx-Recaps is the operator's step.
Tiers: a finished ISO week is rolled into `memory/weekly/<YYYY-Www>.md` (session headings + first prompt) at the same SessionEnd; daily files are kept. Before compaction, a readable transcript copy goes to `~/.claude/state/nvaex-memory-vnext/exports/` (last 20, secrets redacted, never in the repo).
