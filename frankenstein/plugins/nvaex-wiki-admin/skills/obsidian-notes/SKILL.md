---
name: obsidian-notes
description: Check that a folder of Markdown is a valid, linked Obsidian vault that also renders on GitHub: lint broken/mis-cased/ambiguous links, orphans, duplicate basenames, missing indexes, bad frontmatter; write missing INDEX.md; convert wikilinks to relative links. Use for "is this a valid vault", "link these notes", "make an index". Operates on a folder you name, never on the live vault unless told.
---

# obsidian-notes (trimmed: lint + fixes only)

`VL = python3 ${CLAUDE_PLUGIN_ROOT}/scripts/vault_lint.py`. Stdlib only; `VL --help` has the exact rules.

1. **Lint first**: `VL <root>` (`--json`, `--exclude NAME ...`). Show the report before saying anything about the state. Exit 0 = no errors, 1 = errors left, 2 = root missing.
2. **Per finding**
   - Broken or mis-cased markdown link (case differences are a 404 on GitHub/Linux): fix when the right target is clear, else name it. Never invent the missing file.
   - Ambiguous wikilink: `VL <root> --to-markdown-links` rewrites only links with exactly one candidate; list the rest.
   - Folder without index: `VL <root> --fix-index` writes `INDEX.md` (never overwrites one).
   - Orphan: link from its folder index, or flag as a draft to delete. Duplicate basenames: rename only if both are yours.
   - Frontmatter error: fix the YAML.
3. **Write notes that link**: relative markdown links, an index per folder (`[title](path): when to read it`), a `Related:` line, frontmatter `title`, `date`, `tags: [a, b]`, distinct basenames.
4. Report counts before and after. Hand edits need a second `VL` run.

`--vault-init` and `--probe` (Obsidian CLI) exist but write config / need a running app: only on request.
