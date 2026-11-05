---
disable-model-invocation: true
name: harness-audit
description: Audit a project's agent harness (instruction files, settings, hooks, MCP config, skills) for broken paths, over-broad permissions, leaked secrets and malformed skills. Diagnosis only. Use when asked to check or clean a harness.
---

# harness-audit

Our own compact audit. Read-only: it reports, it never edits.

1. Run `python3 -I scripts/config_audit.py PROJECT_DIR` (path relative to this skill). Add `--json` for structured output. Exit 1 means at least one HIGH finding.
2. What it checks: `AGENTS.md`/`CLAUDE.md` (missing, empty, over 200 lines, two files that disagree); `.claude/settings*.json` and `.mcp.json` (valid JSON, wildcard Bash permissions, hook commands and MCP commands that point at programs or files that do not exist); every `SKILL.md` (frontmatter, name equals folder, description); secret-looking lines in those files (location only, value never printed).
3. Report findings by level (HIGH, MEDIUM, LOW, INFO) with the file and what is wrong. Do not fix in the same step. Offer fixes one by one; settings and hook changes need the operator's approval.
4. For a stack overview first, run the `harness-setup` scan. For a skill-only listing use `skill-inventory`.

Honest limits: it checks that things exist and parse, not that a hook does something sensible. The `.claude/settings` and hook checks apply to Claude Code; the instruction-file, MCP, skill and secret checks apply to any agent.
