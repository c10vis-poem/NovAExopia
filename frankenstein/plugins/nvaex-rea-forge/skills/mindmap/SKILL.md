---
name: mindmap
description: Turn a file, pasted text or a topic into a Markmap mindmap .md. Use for "/mindmap <input>" or when a document needs a quick visual outline.
---
# mindmap (trimmed from mindmap-skills by Haixia Cheng)

Input: a file path, pasted text, a URL (fetch with `claw.scrape` or any available fetch; if it fails, ask, never invent content), or a short topic.

Build: if the source is already outlined, mirror it, each node a phrase of at most 8 words. Otherwise 4 to 7 branches, 3 to 4 levels, short labels.

Write `<name>.mindmap.md` next to the source (or cwd), never overwrite: use `-2`, `-3` suffixes. Exact shape:
```
---
title: <title>
markmap:
  colorFreezeLevel: 2
  maxWidth: 300
---

# <one central topic>

## <branch>
- <point>
  - <sub-point>
```
Then check it: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/mindmap/scripts/check.py <file>` (exit 0 only if valid). View at markmap.js.org or a Markmap editor extension. No HTML rendering here: it needs `npx markmap-cli` and the network.
