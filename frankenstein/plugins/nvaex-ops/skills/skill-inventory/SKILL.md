---
disable-model-invocation: true
name: skill-inventory
description: List the skills in a plugin or skills folder and flag duplicate names, missing frontmatter and name/folder mismatches. Use before packaging or merging skill sets, or when asked what skills a folder holds.
---

# skill-inventory

A read-only lister. It makes no network calls, uploads nothing, and calls no model.

1. Run `python3 -I scripts/inventory.py DIR [DIR ...]` (path relative to this skill). Give it a plugin folder, `~/.claude/skills`, or several folders to compare; duplicates are checked across all of them.
2. Add `--json` for machine-readable output.
3. Exit 0 means clean; 1 means problems were printed (`PROBLEM <where>: <issue>`); 2 means bad arguments.
4. Report the count and each problem. Fixing a problem is a separate step: ask which copy to keep (keep the newer one, never delete the newer).

Checks: SKILL.md starts with a closed `---` frontmatter block; `name` and `description` set; `name` equals the folder name; no two skills share a name.
Out of scope: scanning other agents' config folders, security scoring, uploads.
