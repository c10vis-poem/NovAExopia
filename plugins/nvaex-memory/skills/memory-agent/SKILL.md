---
name: memory-agent
description: Explain or review the daily episodic recap written at SessionEnd to NvAEx-Recaps/memory before promoting to MEMORY.md.
---
Mechanical, no model calls, no daemon. Secrets are redacted, instruction-shaped text is filtered.
Target: $NVAEX_RECAPS or config.json "recaps" (default ~/repos/NvAEx-Recaps) /memory/. If that repo is absent it falls back to ~/.claude/state/nvaex-memory/memory/ and never creates the repo.
Promotion into MEMORY.md is NOT automatic: review the day file, and let the JEV auditor (or the operator) promote. layers.jsonl rows carry `"autoPromote": false`.
Re-run is idempotent per session id. Commit/push of NvAEx-Recaps is the operator's step.
Tiers: a finished ISO week is rolled into `memory/weekly/<YYYY-Www>.md` (session headings + first prompt) at the same SessionEnd; daily files are kept. Before compaction, a readable transcript copy goes to `~/.claude/state/nvaex-memory/exports/` (last 20, secrets redacted, never in the repo).
