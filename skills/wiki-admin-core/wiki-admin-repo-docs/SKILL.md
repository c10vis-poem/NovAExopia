---
name: wiki-admin-repo-docs
description: Create or update a repository's agent-facing docs in its openwiki/ folder (OpenWiki format), using the session's own model with no API key. Use when the operator asks to document a repo, refresh a repo's docs, or after merges change a repo. Init writes quickstart plus at most 8 pages; update is git-diff driven, surgical, and may be a no-op.
---

# wiki-admin repo docs (OpenWiki format)

Per-repo docs live in each repo's `openwiki/`; the corpus wiki lives in the vault. Format spec: `~/repos/NvAEx-openwiki-for-claude-code/plugins/openwiki/reference/openwiki-format.md` (layout, `.last-update.json`, the exact AGENTS.md/CLAUDE.md reference block, security). Never call the `openwiki` CLI (dropped) and never require a key. Never read `.env` files or document secrets.

## Init (no `openwiki/quickstart.md` yet)
1. If `openwiki/` already has real content, switch to Update. Never clobber.
2. Git context: `git status --short`, `git rev-parse HEAD`, `git log --max-count=20 --name-status --oneline`.
3. Inventory with `rg --files` (exclude `.git`, `node_modules`, build output, `openwiki/`); short targeted reads, not every file. Several large domains: read-only subagents summarise, they never write.
4. Plan pages with their evidence **outside the repo** (scratchpad), never inside `openwiki/`.
5. Write `openwiki/quickstart.md` first, then the smallest set of linked pages, at most 8. Every claim grounded with a source path. Existing docs: be the map over them, not a copy.
6. Merge or remove thin and single-file-directory pages.
7. Add the reference block to the repo's `AGENTS.md` (the operator's repos use AGENTS.md as the instruction file).
8. Write `openwiki/.last-update.json` (`command: "init"`, `updatedAt` from `date -u +%Y-%m-%dT%H:%M:%S.000Z`, `gitHead`, `model`).

## Update
1. **No-op check:** metadata has `gitHead`, `git status --short --untracked-files=all` is empty (ignoring the metadata file), and HEAD equals `gitHead` or every changed path is inside `openwiki/`: stop, report "current", edit nothing.
2. Changes since `gitHead` (`git log <gitHead>..HEAD --name-status --oneline`, `git show` on high-signal commits).
3. Impact plan: source change -> page -> edit -> why. A page with no tied change is not touched.
4. Surgical edits: replace stale sentences, no formatting-only edits, soft budget (under ~5 changed source files: at most 1-2 pages; quickstart only if setup/navigation changed).
5. Check the AGENTS.md reference block; refresh only if missing or stale.
6. Rewrite `.last-update.json` only if content changed.

Repo changes go through the repo's own pipeline (branch, commit, PR); the docs are not "wiki truth" for the corpus until ingested through `wiki-admin-ingest`.

## Built from (credit) and what this replaces
OpenWiki for Claude Code `/openwiki:generate` + `/openwiki:update` (`~/repos/NvAEx-openwiki-for-claude-code/plugins/openwiki/skills/`), openwiki-skills `/openwiki-init` + `/openwiki-update` (fork c10vis-poem/NvAEx-openwiki-skills: the strict no-op check, plan kept outside the repo, one canonical page per concept), `~/.claude/skills/openwiki` (search/read an existing repo OpenWiki). Replaces for the wiki admin: `/openwiki:generate`, `/openwiki:update`, `/openwiki-init`, `/openwiki-update`. `/openwiki:schedule` stays as is (no overlap).
