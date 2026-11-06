---
name: anchor-memory
description: Check memory ledgers (memory/decisions.md, memory/FACTS.md) for stale entries. Entries carry a machine-checkable @meta block; the linter flags DRIFT, BROKEN, DANGLING, DUPLICATE. Use when writing a durable decision/fact, or when the session snapshot reports memory drift.
---
Write a decision/fact with an anchor so it can be verified later. Block syntax and kinds: [spec.md](spec.md).

Run the linter (stdlib, read-only):
```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/memory.py" lint --root <repo> [--json] [--files memory/decisions.md]
```
Ledger files default to memory/decisions.md + memory/FACTS.md, or `memory.ledger_files` in anchor.config.json.
On a finding: fix the entry, or mark it `status: superseded` with a new entry that `supersedes` it. Never delete history.
