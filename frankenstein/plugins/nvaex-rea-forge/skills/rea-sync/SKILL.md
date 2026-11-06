---
name: rea-sync
description: Merge a new upstream release into a customized fork and re-apply local intent. Use after upstream tags a release.
---
# rea-sync (from turbocharge sync-plugin-customizations, trimmed)

1. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/upstream.py next <fork>`: `current <tag>` means stop; exit 3 means a prior sync failed, resolve it first. Only stable tags are targets, never a branch tip.
2. In the fork: `git remote add upstream <url>` if absent, `git fetch upstream --tags`, then `git merge <tag> --no-edit` (add `--allow-unrelated-histories` only if git refuses for unrelated histories).
3. **Clean merge:** run `upstream.py prune <fork> <upstream-skills-dir>` to drop intent sections for skills upstream removed. Set `lastSyncedTag` to the new tag in `.turbocharge/settings.json`.
4. **Conflict:** for each conflicted `SKILL.md`, read the conflict, the `## <skill>` intent section, and upstream's clean copy; resolve so upstream's new content stays and the intent is re-applied. If you cannot, `git merge --abort`, set `"syncStatus":"failed","failedTag":"<tag>"` in settings.json, and write the conflict plus intent to `.turbocharge/kickstart-<skill>.md` for the operator.
5. Never push or commit from this skill; hand the diff to the operator's PR pipeline.
