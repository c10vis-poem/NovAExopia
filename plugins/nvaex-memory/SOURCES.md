# Sources (parts donors; custom first)

Size = source folder `du -sk` (FOLD-MAP) -> what landed here (bytes). Package total: 211,020 B / 34 files before this pass, 147,119 B / 34 files after (incl. 8.8KB Apache text for Memory Bank + notices) (`git ls-tree -l HEAD` vs `find -printf %s`; `du -sk` 359 -> ~313 because of 4K blocks).

| Path here | Origin | Version | License | Source size -> here | How |
|---|---|---|---|---|---|
| scripts/memory_lint.py, skills/anchor-memory/spec.md | anchor-memory (Rishabh Choudhry) | 0.1.0 | MIT | 575KB -> 11.4KB + 1.3KB | copied verbatim (322-line stdlib linter, spec as named) |
| skills/ccfind/scripts/ccfind.mjs, SKILL.md | ccfind (Evghenii Pogonii) | 0.19.0 | MIT | 2163KB -> 44.2KB + 1.2KB (was 72.9KB + 14.3KB) | trimmed: install/uninstall (edits shell rc), open and pick (spawn terminals, TUI), bench, client-advice and cleanEnv removed; index/search/show/stats kept; SKILL.md rewritten short. No network code |
| skills/cut-weight/** | cut-weight (Matthew Cohen) | 0.4.5 | MIT | 133KB -> 1.8KB SKILL + 6.3KB quarantine-protocol.md + 13.7KB inventory.py (was 31KB + 6.3KB + 13.7KB wrapper refs) | SKILL.md rewritten short; six reference files dropped (agent-artifacts, entry-points, evidence-signals, intent-review, review-loop, workflow-handoff); quarantine-protocol.md and inventory.py verbatim |
| scripts/memory.py snapshot/freeze | continuity (vikash) | 1.5.1 | MIT | design only, reimplemented | upstream bundles are 150-900KB JS with auto-commit and blocking Stop |
| scripts/memory.py nudge, skills/whydone | whydone (Danil Chevgan) | 1.4.1 | MIT | 1314KB -> reimplemented | nudge-only; entry format follows SCHEMA v1; 409KB CLI not copied |
| scripts/memory.py recap, config.json | memory-agent (Volodymyr Isai) | 0.1.0 | MIT | 2403KB -> reimplemented | mechanical daily KB; upstream LLM pipeline and polling capture not copied |
| scripts/memory.py map, licenses/create-smartfolder.LICENSE | create-smartfolder (Paul Hess) | 6.6.0 | CC-BY-4.0 AND MIT | 418KB -> concept only; LICENSE 18.7KB -> 0.3KB notice | CC BY 4.0 s3(a)(2) lets a URI to the legal text satisfy the notice; nothing from upstream is copied |
| scripts/memory.py `branch_note`, skills/handoff | handoff (Florian Koch) + context-handoff | 1.0.0 / (fold) | MIT | 93KB + 1040KB -> 1.9KB skill + ~20 lines | branch note in `.git/handoffs/`, commit stamp, trunk exclude, STALE flag; context-handoff contributes the telegraphese field rules and the failed-approach format. Stripped: workstream/prune subcommands, bash+jq hooks, `generate_handoff_manifest` MCP (743KB bundle), build/, package-lock, .codex-plugin |
| scripts/memory.py `RESUME` + SessionStart(compact) | better-compact (koenvdheide) | v3 brief | MIT | 117KB -> 1 constant | the `session.compact` mod needs `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS`; folded as a resume checklist injected after compaction, not as a summarizer instruction. The 45% status line is usage display (operator is building a custom one): dropped |
| scripts/memory.py `export_chat` + PreCompact hook | chat-autoexporter (Boralio AI) | 1.0.2 | MIT | 74KB -> ~15 lines | readable transcript to state dir (0600, last 20, secrets redacted); not written into any repo. Upstream export-chat.js/.sh dropped |
| skills/patterns | claude-patterns (Mycelium AI) | 1.0.0 | MIT | 120KB -> 1.3KB | proposal-only scan; vault prefs interview, journal reads, headless auto-capture, install-ping, .mcp.json, workflows dropped |
| skills/workstream | memory-toolkit (Ilya Gorsky) | 1.9.13 | MIT | 514KB -> 1.2KB | workstream + park + per-workstream handoff text as plain files; memory.js (37KB), watcher, hooks, tests dropped |
| scripts/memory.py `rollup` | remember | (tiering idea) | Community License (idea only, nothing copied) | 8606KB -> ~20 lines | finished ISO week -> `memory/weekly/<week>.md`; dailies kept; upstream node dist bundle, Haiku pipeline, hooks, commands not copied |
| scripts/memory.py `task` (+ snapshot re-injection) | claude-context-optimizer (cco-task) | (fold) | MIT | 2121KB -> ~25 lines | bounded patchable task state, 4000-char cap. Not folded: cco report skills and context-analyzer agent (need the tracker.js hook; usage display is the operator's custom build) |
| skills/memory-bank | Memory Bank | (fold) | Apache-2.0 (licenses/memory-bank.LICENSE) | 85KB -> 1.3KB | six-file structure and update rules; blocking Stop hook, CoC/PRIVACY/SECURITY/CONTRIBUTING docs dropped |
| licenses/*.LICENSE, NOTICE-derived.md | upstream LICENSE files for copied/reimplemented-with-source-text plugins; copyright notices for the reworded ones (MIT); Memory Bank Apache-2.0 text | | | kept | |

## Missing / not folded
- adaptive-agent: not on the phone (FOLD-MAP: name scan of 493 plugin.json plus `find -iname` in ~/repos found none). Nothing invented.
- memsearch-aesop and OB1 schemas: not in this package's task text; not built.
- JEV auditor gate / `jevmem` promotion step: belongs to nvaex-jev-core; this package never promotes.
- Upstream memory-agent LLM extraction/merge pipeline: deliberately excluded (daemon-like, model calls).
- context-handoff `generate_handoff_manifest` MCP and cco report skills: not folded, reasons above.
