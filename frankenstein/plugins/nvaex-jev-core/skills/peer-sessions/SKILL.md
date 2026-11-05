---
name: peer-sessions
description: Use to see other live Claude Code sessions on this device, to message one, or to debate with another agent (Claude, Gemini) through a shared file.
---
# Peer sessions

**Who else is running:** `/peers` (or `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/peers.py`). It reads `~/.claude/sessions/*.json`, drops dead pids, and prints name, status, cwd, age. Read-only; it writes nothing. Before editing a file in a repo another live session has as its cwd, check the list.

**Shared-file discussion with another agent** (one file, append only, turns by marker):
1. Name yourself (one lowercase word). File: `./discussion.md` unless told otherwise. Missing file: create it with `# Discussion: <topic>`, `<!-- status:active -->`, then `[TURN: <you>]`. Existing: read it and join.
2. First turn is an Intro (100-150 words): neutral, concrete facts from the codebase or docs, no advocacy. Later turns: `**you (Round N):** <150 words max>` then `[TURN: other]`. Use `[TURN: NEXT]` if the partner is unknown.
3. Wait by polling the last marker, at most every 20 s: `until tail -n 5 discussion.md | grep -q "TURN: you"; do sleep 20; done` (stop on AGREED or DEADLOCKED).
4. Before appending, re-read the last 10 lines: if the marker changed, someone wrote; re-read first.
5. Engage the other side's exact points. After round 3, if you agree end with `[AGREED: <one-line summary>]`. At round 12 or a stall write the unresolved points and `[DEADLOCKED]`. Then report to the user. Seek the best outcome, not a win; synthesise when circling.
