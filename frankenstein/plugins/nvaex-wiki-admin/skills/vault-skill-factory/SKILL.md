---
name: vault-skill-factory
description: Turn mature curated wiki pages into a reviewable Agent Skill package. Writes only to a review directory; never installs.
---

# Vault skill factory (trimmed obsidian-wiki skill)

Inputs from the operator: the wiki folder, the review directory (`<review>`; outside the wiki and outside any skills folder). Ask once if either is unknown.

1. **Cluster**: seed from a topic/tag/page; expand by tag and wikilink neighbours (`wiki_search.py`). Keep pages with `lifecycle: reviewed|verified` or `tier: core`; drop drafts unless asked. List names and count and get a yes. Fewer than ~3 mature pages: say so and offer to widen.
2. **Design**: `name` (kebab-case, subject of the cluster; must not collide with an installed skill), `description` = the trigger (when, in the phrasings a user says, and what), the reasoning approach (questions answered, method, caveats; distilled, not pasted), and which page bodies become `references/`.
3. **Write** `<review>/<name>/`: `SKILL.md` (lean: trigger plus compact guide), `references/<topic>.md` per sub-theme, `references/sources.md` (every page used by `[[link]]` plus its upstream `sources:`), and `SKILL_FACTORY.md` (date, cluster pages with lifecycle/tier, filter used; excluded from the installed skill). Keep `^[inferred]` / `^[ambiguous]` markers; never launder synthesis into fact.
4. **Report and stop**: path, cluster (count and names), description. Install is the operator's decision, project-local only; never run a setup script or symlink into a global skills dir.

Checklist: output only under `<review>`; cluster confirmed; description accurate; depth in references; markers kept; provenance present; nothing installed.
