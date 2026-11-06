---
name: cut-weight
description: Archive repo residue (old plans, audits, duplicate docs, scratch), never delete. Use for repo bloat or folder cleanup.
---
Trimmed fold of cut-weight 0.4.5. Modes: **audit** (no project edits; write output outside the project) or **cleanup** (default).

1. Inventory (read-only): `python3 "${CLAUDE_PLUGIN_ROOT}/skills/cut-weight/scripts/inventory.py" <root> --out <run-dir>/inventory.json`. It lists files and Markdown; it does not judge relevance.
2. Run dir: sibling `<project>-graveyard/<UTC-timestamp>-<id>/`, outside every Git worktree. Recovery rules and `manifest.json` fields: [quarantine-protocol.md](references/quarantine-protocol.md).
3. Read current guidance (README, AGENTS/CLAUDE.md, plans, roadmap) before judging; follow links across folders.
4. Dispose each group with evidence:

| Disposition | Meaning |
|---|---|
| KEEP | current consumer, unique knowledge, or explicit user decision |
| CONSOLIDATE | move unique content into the authoritative doc, archive the original |
| ARCHIVE | superseded/finished; copy to graveyard with SHA-256, then remove |
| LOCAL_ONLY | keep in place, ignore and untrack |
| DELETE | proven regenerable output only, within authorized scope |
| ASK | consequential doubt; leave untouched, ask 2-4 grouped questions |

Age, filename, or a stale link alone never decides. Uncertain residue is ARCHIVE or ASK, never a silent delete. No auto-commit, no history rewrite, no permanent purge unless asked.
5. Repair surviving AGENTS.md/CLAUDE.md/README links, verify archived hashes and surviving links, re-run affected checks, and report dispositions plus exact recovery paths.
