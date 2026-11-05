---
name: create-smartfolder
description: Generate tiered MAP.md routers for a folder tree so an agent reads a small map first and opens only what it needs. Use when a directory is large or poorly navigable.
---
Run: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vnext.py" map <dir> [--depth 2] [--force]`
Writes MAP.md at each level (folder table: file count + first-line description from README/CLAUDE/AGENTS). Files it generated carry a marker and are refreshed on re-run; hand-written MAP.md files are never overwritten without --force.
Then tell the agent to read MAP.md first. Upstream create-smartfolder's full kit (status boards, sidecars) is intentionally not included; see SOURCES.md.
