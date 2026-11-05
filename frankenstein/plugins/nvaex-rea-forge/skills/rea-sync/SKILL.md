---
name: rea-sync
description: Keep local mods on a fork across upstream updates (customize-and-sync). Use when a fork has local patches and upstream moved.
---
# rea-sync
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync.py save <fork> <upstream-ref>` stores local mods as `patches/0001-local-mods.patch`.
After the operator updates the fork from upstream (`gh repo sync`, per fork workflow), run `sync.py check <fork> patches` then `sync.py apply <fork> patches`. A FAIL means a conflict: show it, do not force. Never fetch, commit or push from this skill.
