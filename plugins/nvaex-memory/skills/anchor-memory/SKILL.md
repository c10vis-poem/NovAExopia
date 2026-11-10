---
name: anchor-memory
description: Lint memory ledgers (decisions.md, FACTS.md) for DRIFT, BROKEN, DANGLING, DUPLICATE. Use when writing a durable fact.
---
Write a decision/fact with an anchor so it can be verified later. Block syntax and kinds: [spec.md](spec.md).

Run the linter (stdlib, read-only), with the `memory.lint` MCP tool or:
```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/memory.py" lint --root <repo> [--json] [--files memory/decisions.md]
```
Ledger files default to memory/decisions.md + memory/FACTS.md, or `memory.ledger_files` in anchor.config.json.
On a finding: fix the entry, or mark it `status: superseded` with a new entry that `supersedes` it. Never delete history.
