---
name: rea-customize
description: Record why a fork's skill differs from upstream. Use when changing a forked SKILL.md so a later sync can re-apply it.
---
# rea-customize (from turbocharge customize-plugin + setup, trimmed)

Forward only: describe the change, then make it; never reverse-engineer intent from a diff.

1. **Config.** `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/upstream.py init <fork> <upstream-url>` once; it writes `<fork>/.turbocharge/settings.json` (`upstreamRepo`, `lastSyncedTag`).
2. **Read both** the upstream copy and the fork copy of the SKILL.md before editing. Edit the fork copy only; the upstream copy is read-only.
3. **Write `<fork>/.turbocharge/intent.md`**, one section per skill, rewritten from scratch each time (current divergence only, never a delta):
```
## <skill-name>
**Upstream behavior:** ...
**This fork:** ...
**Upstream ref:** <lastSyncedTag>
```
4. Stop. Commit and push are the operator's step (fork workflow: branch, secret scan, PR); this skill never commits, pushes or clones.
