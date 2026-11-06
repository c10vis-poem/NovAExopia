# FOLD-MAP (2026-11-05, mapper)

Binding: CONTRACT.md + FOLD-BRIEF.md. Read-only survey; no package file was changed. Source list: keep-list-2026-10-30.md section 1 (119), minus 8 removed by the brief, plus 4 added, plus the 2 whole ports and TinyFish.

Path legend: `S1` = `~/.claude/plugins/synced/a5d13a90-190b-42eb-ad1b-69c924919b1b_b410cc73-6e72-411c-a9de-4edf62ec27d7/`, `S2` = `~/.claude/plugins/synced/bf59ea3a-5000-437b-87d6-20241bb754e6_3a64471e-06ab-454b-baf7-caf79c84e4fa/`, followed by the first 8 hex of the plugin folder. Size = `du -sk` of the source folder (KB), whole, before trimming. Where a name has two plugins (caveman, handoff, notify, turbocharge, context-handoff) the keep list's `#1`/`#2` was matched by description; noted in the row.

Status vocabulary: `already in package` (per that package's SOURCES.md, includes re-derived ideas), `to fold`, `whole port`, `replaced by claw` (brief; `NOT YET` when claw cannot do the job today), `cannot fold` (reason given).

## Counts by status (118 rows)

| status | rows |
|---|---|
| already in package | 19 |
| to fold | 86 |
| whole port | 2 |
| replaced by claw | 6 |
| cannot fold | 5 |
| total | 118 |

Not rows (removed by the brief, not folded): pmm, claude-code-cost, claude-code-feedback, claude-war-room, burn-baby-burn, cache-guard, cache-ttl-timer, heavy-usage. Brief also removes shipwrights, Pragmatic PM Toolkit, thinking-partner, token-saver, Token Inspector, and usage bars: none of those are in keep list section 1 except the eight named. Arithmetic: 119 - 8 + 4 added + 2 whole ports + TinyFish = 118.

## Fold table

| keep | on phone? (path) | KB | home package | what to take | what to strip | status | note |
|---|---|---|---|---|---|---|---|
| adaptive-agent | NOT FOUND | - | nvaex-memory | (nothing on phone) |  | cannot fold: not on phone (name scan of 493 plugin.json in synced/local-plugins/cache + find -iname in ~/repos found none) |  |
| agent-recall | S1/80cdebec | 692 | dumbass-memory-mcp | SQLite KG table shape + recall query only | own MCP server (.mcp.json), hooks, 692KB | to fold | Graph tier is already Streams 1+2 in dumbass; fold only if it adds something CRG/graphify lack |
| anchor-memory | S1/63003d0a | 575 | nvaex-memory | memory_lint.py (322 lines), spec.md (verbatim) | hooks, other skills, 575KB | already in package |  |
| ccfind | S1/d85d1d81 | 2163 | nvaex-memory | ccfind.mjs + SKILL.md (verbatim) | demos, gifs, CI | already in package | UNTRIMMED: 73KB mjs + 14KB SKILL copied whole |
| chat-autoexporter | S1/cb3937a3 | 74 | nvaex-memory | pre-compact + session-end transcript export step | hooks (re-wire into nvaex-memory Stop/SessionEnd), 74KB | to fold | nvaex-memory recap already reads transcripts; may be redundant |
| claude-patterns | S1/23529d87 | 120 | nvaex-memory | pattern-to-rule/skill capture prompt (approval-gated) | .mcp.json, hooks, 120KB | to fold |  |
| compounded | S1/ab9b0379 | 830 | nvaex-wiki-admin | approval-gated rule learning skill + commands | agents, hooks, 830KB | to fold | spec row 3; SOURCES.md says "no match found" but it is on the phone |
| jevmem | S1/7d57870a | 71 | nvaex-jev-core | (none: jevmem CLI/hosted) | hooks, CLI call | cannot fold: plugin holds no code, only a launcher for the npm `jevmem` CLI, which POSTs to https://api.typesafe.ai/v1/systemone with a TypeSafe key (README line 46); contract rule 6 local-first. Function covered by dumbass memory.record_claim; operator decision to drop |  |
| memory-agent | S1/55175215 | 2403 | nvaex-memory | daily KB + autoPromote:false design (reimplemented in memory.py) | LLM extraction pipeline, polling capture, 2.4MB | already in package |  |
| memory-toolkit | S1/07e6b314 | 514 | nvaex-memory | workstream + handoff skill text | hooks, 514KB | to fold |  |
| remember | S1/043db339 | 8606 | nvaex-memory | tiered daily-to-weekly log idea | node/dist bundle (8.6MB), hooks, commands | to fold | nvaex-memory recap is single-tier today |
| whydone | S1/a4c444d8 | 1314 | nvaex-memory | SCHEMA v1 entry format + nudge-only Stop (reimplemented) | 409KB CLI, blocking Stop | already in package |  |
| context-handoff | S1/96328962 | 1040 | nvaex-memory | handoff manifest + handoff-search skills | build/, package-lock, .mcp.json, hooks, .codex-plugin, 1MB | to fold | #1 = S1/96328962 (auto-save before compact); S1/9ceee32b is the other one |
| handoff | S1/d56b622d | 93 | nvaex-memory | per-branch note save/load skill | hooks (re-wire into nvaex-memory SessionStart), 93KB | to fold | #1 = S1/d56b622d |
| better-compact | S1/126098c7 | 117 | nvaex-memory | compaction steering text (goal, next step, files, decisions) | hook runtime, 117KB | to fold | Becomes a PreCompact instruction; nvaex-memory has no PreCompact entry yet |
| claude-context-optimizer | S1/43b5eda8 | 2121 | nvaex-memory | report skills + task-state agent | read-cache.js hook (blocks reads), 2.1MB | to fold |  |
| context-window | S1/10c1f421 | 181 | nvaex-ui-cockpit | pane listing context entrants | hook bundle, 181KB | to fold | Borderline with "usage display" removal: it shows what entered context, not tokens/limits. Confirm. |
| headroom | S1/b9db7a50 | 137 | nvaex-wiki-admin | peek.py size gate (copied) + /peek command |  | already in package |  |
| bake-claude-md-files | S1/b26c0aab | 6172 | NEW nvaex-ops | rule-to-check skill | 6.1MB payload, examples | to fold |  |
| chuck | S1/9fe74888 | 137 | nvaex-jev-core | per-prompt rule selection + contradiction flag into jev-router | hook runtime, 137KB | to fold |  |
| claude-md-management | S1/8bc81ed2 | 1137 | NEW nvaex-ops | revise-claude-md + claude-md-improver skills | commands duplicates, 1.1MB | to fold |  |
| claude-perfectionist | S1/23de33ce | 363 | NEW nvaex-ops | harness grading skill | extra commands, 363KB | to fold |  |
| instructions-cleanup | S1/a9b6796d | 100 | NEW nvaex-ops | minimal-patch conflict fixer skills |  | to fold |  |
| frontier-simplify | S1/f14c17b3 | 5900 | nvaex-jev-core | 2-3 rules: cut invented process, cap repeat reviews | 5.9MB assets | to fold |  |
| loop-and-gate-build-kit | S1/de15c98b | 151 | nvaex-jev-core | human decision-gate skill |  | to fold |  |
| no-cape | S1/79d761f9 | 226 | nvaex-jev-core | escalate/fail-loud/verify rules text | hooks, commands, 226KB | to fold |  |
| superpowers | S1/6ba53849 | 2686 | nvaex-jev-core | verification-before-completion, writing-plans, systematic-debugging ONLY | all other skills, SessionStart "MUST invoke" hook, 2.7MB | to fold | Brief: rip apart |
| claude-code-audit-stack | S1/69f86485 | 124 | nvaex-jev-core | claim-auditor agent prompt (read-only) | hooks, other agents, 124KB | to fold | SOURCES.md says present, not copied |
| claude-eta | S1/617c008b | 3666 | nvaex-jev-core | 5-call cadence + repeat-edit loop idea (health.py) | TS dist, telemetry/admin server, 3.7MB | already in package |  |
| colosseum | S1/2c6cd435 | 1642 | nvaex-rea-forge | adversarial reviewer + verified-quote rule | web-search calls (use claw.search once it exists), hooks, 1.6MB | to fold |  |
| llm-dark-patterns | S1/1fee4b38 | 5788 | nvaex-jev-core | 13 of 30 checks reimplemented in scorecard.py | blocking Stop hooks, 5.8MB | already in package | UNTRIMMED gap: 17 checks missing; hooks/*.sh absent on phone |
| spec-drift | S1/f3bd4ce7 | 684 | nvaex-jev-core | requirements-vs-built compare (gate 1) | hooks, commands, 684KB | to fold |  |
| agent-design | S1/f4af7fc2 | 107 | NEW nvaex-ops | agent-vs-workflow decision skill |  | to fold |  |
| agent-ingest-audit-optimize | S1/7f76ffa9 | 2743 | nvaex-wiki-admin | audit-outside-material skill, reversible-change step | 2.7MB refs | to fold | spec row 3; SOURCES.md says "no match found" but it is on the phone |
| agent-smith | S1/22e89ec4 | 1451 | NEW nvaex-ops | analyze-agent / create-agent commands | 1.4MB | to fold | Added keep |
| claude-code-setup | S1/a382e72d | 641 | NEW nvaex-ops | claude-automation-recommender skill | 641KB | to fold |  |
| harness | S1/9a37b89a | 21263 | NEW nvaex-ops | team-architecture SKILL.md only | 21MB of references/assets | to fold |  |
| harness-architect | S1/ddde7304 | 1785 | NEW nvaex-ops | 9-phase builder/auditor command | 1.8MB | to fold |  |
| harness-scope | S1/37e770d1 | 822 | nvaex-ui-cockpit | profile dir/selector/rule shape (profiles.py) |  | already in package |  |
| wizard | S1/d0666aa1 | 3099 | NEW nvaex-ops | repeatable task to workflow skill | agents, hooks, 3.1MB | to fold | Overlaps claw.workflows (workflows.json); decide one |
| agent-army | S1/f90aefa8 | 890 | nvaex-wiki-admin | (not copied) rolling pool = batch_ledger.py + corpus-batch-processing |  | already in package | Re-derived, no dependency on upstream |
| agent-discussion | S1/4e3163e1 | 69 | nvaex-jev-core | shared-file protocol skill for Claude/Gemini |  | to fold |  |
| backlog | S1/b38c2c6a | 777 | nvaex-jev-core | cross-session task list skill | agents, hooks, 777KB | to fold |  |
| cc | S1/ff18ea72 | 229 | nvaex-jev-core | peer-session visibility commands | hooks (writes shared state; needs killswitch), 229KB | to fold |  |
| crewmarshal | S1/48061658 | 517 | nvaex-jev-core | plan/review with outside executors skill | hooks, 517KB | to fold |  |
| noetic-control-room | S1/9dee1509 | 138 | nvaex-jev-core | coordinator briefing skill |  | to fold |  |
| skill-creator | S1/4af84cf1 | 300 | NEW nvaex-ops | official skill builder | duplicate of anthropic-skills:skill-creator, 300KB | to fold | Already ships with Claude; may need no copy |
| skill-discovery | S1/03992290 | 374 | NEW nvaex-ops | cross-agent skill inventory | 374KB | to fold |  |
| skill-gate | S1/144a7e2e | 183 | nvaex-jev-core | per-project confirm list as nudge, not block | blocking hook, 183KB | to fold |  |
| skill-provenance | S1/8e385b2f | 3203 | nvaex-wiki-admin | provenance.py writes skill-provenance.json SHA-256 | agent/eval/package scaffolding, 3.2MB | already in package |  |
| plugin-dev | S1/cdcf6ad2 | 778 | NEW nvaex-ops | official plugin-dev skills | agents duplicates, 778KB | to fold |  |
| plugin-manager | S1/7ae1da3c | 2373 | nvaex-ui-cockpit | toggle action for plugins-panel | visual UI bundle, 2.4MB | to fold | Panel exists in cockpit; plugin-manager not credited in its SOURCES.md |
| plugin-packaging | S1/64f14bc3 | 119 | NEW nvaex-ops | repair-install skill |  | to fold |  |
| skills-updater | S1/f1135d06 | 46 | NEW nvaex-ops | audit/update skill (point at forks, not upstream) |  | to fold |  |
| turbocharge | S1/71dabb73 | 89 | nvaex-rea-forge | customize-plugin, sync-plugin-customizations, setup-plugin-customization (replace scripts/sync.py stub) | .cursor-plugin, logo, 89KB | to fold | #2 = S1/71dabb73. rea-forge SOURCES.md says no such skill; it checked the other turbocharge (S1/0e956c57) |
| mcp-debugging | S1/bc6c6954 | 108 | NEW nvaex-ops | connection/auth repair skill |  | to fold |  |
| mcp-server-dev | S1/c06bc0ae | 223 | NEW nvaex-ops | official MCP build guide |  | to fold |  |
| mcp-tunnels | S1/2a6339cf | 62 | NEW nvaex-ops | tunnel command text |  | to fold |  |
| mcp2cli | S1/3763173a | 126 | nvaex-rea-forge | skill + generator to replace wrap.py fallback | agents, 126KB | to fold | On phone as plugin; SOURCES.md says not installed |
| tool-schemas | S1/50c218e4 | 131 | NEW nvaex-ops | schema repair skill |  | to fold |  |
| apify | S1/d9b3b793 | 333 | claw-mcp | (nothing) | .mcp.json, agents, 333KB | replaced by claw | NOT YET: claw.scrape works only as basic fetch; no crawl/bulk driver |
| claude-bridge | S1/263ff246 | 253 | claw-mcp | (nothing) | .mcp.json, agents | replaced by claw | NOT YET: claw.browser CDP websocket actions are not implemented |
| firecrawl | S1/543cc003 | 195 | claw-mcp | (nothing) | skills, commands, 195KB | replaced by claw | NOT YET: no search/map/crawl in claw |
| modern-web-guidance | S1/f0ceeefd | 2035 | NEW nvaex-ops | chrome-extensions + current-web skill | 2MB, 2 other skills | to fold |  |
| playwright | S1/22bf1341 | 35 | claw-mcp | CDP interceptor / selector parts for WebView + claw.browser, from ~/repos/playwright-mcp (354KB) | server, browsers, ~77MB of ~/repos/playwright | to fold | Parts only. Phone plugin S1/22bf1341 is just .mcp.json: nothing to rip there |
| searchoclock | S1/ed67ab32 | 2975 | nvaex-jev-core | date-aware research-on-failure prompt | commands, agents, hooks, 3MB; needs claw.search | to fold |  |
| watch-video | S1/b911d56b | 1230 | claw-mcp | (nothing) | 1.2MB | replaced by claw | NOT YET: claw has no video tool among its 6 |
| airquote | S1/890ae788 | 394 | nvaex-jev-core | dictation-cleanup rules merged into drunken-master stage 0 | hooks, 394KB | to fold | Overlaps drunken-master |
| drunken-master | S1/fda4eab2 | 297 | nvaex-jev-core | SKILL.md (verbatim) |  | already in package | UNTRIMMED: 9.7KB SKILL.md whole |
| local-whisper | S1/55855313 | 130 | NEW nvaex-ops | STT skill (Whisper cpp wrapper text) |  | to fold | Added keep; voice lane. Models stay out of the repo |
| tts | S1/4aab4b25 | 1206 | NEW nvaex-ops | TTS skill | hooks (auto-speak), commands, 1.2MB | to fold |  |
| create-smartfolder | S1/e40abd7f | 418 | nvaex-memory | MAP.md router concept (memory.py map) | 258KB kit, 36KB SKILL | already in package | UNTRIMMED: licenses/create-smartfolder.LICENSE 18KB CC-BY full text |
| gdrive-to-markdown | S1/6aaccdd0 | 1384 | nvaex-wiki-admin | step-3 converter | 1.4MB | to fold | SOURCES.md says not on phone; it is. Uses the claude.ai Drive connector, which dies with the account-side removal: needs a local rclone path |
| llm-wiki | S1/a37bed19 | 5516 | nvaex-wiki-admin | wiki_search/lint/stats/evolve scripts | 5.1MB media/docs | already in package |  |
| obsidian-notes | S1/3cacb896 | 712 | nvaex-wiki-admin | vault validity skill |  | to fold |  |
| obsidian-sync | S1/842c82fd | 73 | nvaex-wiki-admin | sync-to-vault skill/commands |  | to fold | Writes the vault at run time; build must not |
| rag-evaluation | S1/9bf3e930 | 115 | nvaex-wiki-admin | retrieval debug skill (test harness for wiki) |  | to fold |  |
| wiki-wonka | S1/cc779a20 | 3800 | nvaex-wiki-admin | ingest/query/lint prompt deltas only | agents, hooks, 3.8MB | to fold | Overlaps wiki-admin-ingest/lint/query already in package |
| desktop-commander | S1/8d52a3a6 | 150 | NEW nvaex-ops | PDF/DOCX/Excel guidance skills | the MCP server (npm, Node; not in this 150KB plugin) | to fold | Terminal/process part = claw.device or Bash; do not fold the server |
| code-map | S1/73654592 | 443 | nvaex-rea-forge | SKILL.md, generate.mjs, engine.html | examples | already in package | UNTRIMMED: engine.html 51KB, generate.mjs 7KB whole |
| graph-indexer | S1/4812944f | 50 | dumbass-memory-mcp | (nothing) | agents, hooks, .mcp.json, 50KB | cannot fold: functionally = code-review-graph (whole port) + dumbass Stream 1; its MCP already fails CONNECTION_CLOSED. Needs operator OK to drop |  |
| code-review | S1/59d0c87c | 54 | NEW nvaex-ops | review command text |  | to fold |  |
| review-council | S1/00380f92 | 183 | NEW nvaex-ops | six reviewer agent prompts | hooks, 183KB | to fold |  |
| claude-security | S1/a800bba9 | 526 | NEW nvaex-ops | scan/verify skill + agents | hooks, 526KB | to fold |  |
| llm-secure-patterns | S1/6358786b | 1436 | nvaex-wiki-admin | real wa_quarantine.py + patterns | hooks, 1.4MB | to fold | Package ships a greedy-crane stand-in; SOURCES.md says plugin missing, but it is on the phone |
| public-repo-readiness | S1/92c1d35f | 66 | NEW nvaex-ops | secret/private-data audit skill |  | to fold |  |
| adb-mcp | S1/7c8a91c6 | 87 | claw-mcp | (nothing) | .mcp.json, skills | replaced by claw | claw.device exists (battery, wifi, notify, adb-devices only); install/tap/build/test not implemented |
| kotlin-lsp | S1/56194a74 | 42 | NEW nvaex-ops | Kotlin LSP skill |  | to fold |  |
| firebase | S1/585936f9 | 27 | NEW nvaex-ops | (nothing to take) |  | cannot fold: plugin is a 27KB .mcp.json only (firebase-tools via npx), no skill text. Write a short skill new if wanted |  |
| gcp-devkit | S1/56b106a3 | 269 | NEW nvaex-ops | Cloud Run/IAM/Firestore/Terraform skills | agents, hooks, 269KB | to fold |  |
| google-multi-account | S1/ba923796 | 296 | NEW nvaex-ops | setup/reauth skills | its .mcp.json server (fails ENOENT: posix_spawn "stdio") | to fold | Added keep |
| cloudflare | S1/a512755b | 2307 | NEW nvaex-ops | workers/D1/R2/Vectorize skills (prefer ~/repos/NvAEx-cloudflare-skills, 1.5MB) | .mcp.json, 2.3MB | to fold |  |
| supabase-expert | S1/d6bbd0c2 | 101 | NEW nvaex-ops | RLS/Auth/Storage skills |  | to fold |  |
| design | S1/afe29730 | 103 | NEW nvaex-ops | critique/a11y skills for Compose UIs | .mcp.json, 103KB | to fold |  |
| building-with-typesafe-jev | S1/5ac9a71c | 8183 | nvaex-jev-core | two-stage idea only (router) | 8.2MB refs, hosted API runtime | already in package |  |
| claude-jev | S1/4a989cf6 | 780 | nvaex-jev-core | two-stage idea only | hosted api.typesafe.ai runtime | already in package |  |
| jev | S1/d8e07c35 | 106 | nvaex-jev-core | L0-L3 level idea only (route.py) | hooks, 106KB | already in package |  |
| claude-deconstruct | S1/a4c0b055 | 124 | NEW nvaex-ops | first-principles skill | .mcp.json, hooks | to fold |  |
| consensus | S1/a1fc638c | 128 | claw-mcp | multi-model second opinion via claw.infer | hooks, commands, direct API keys | to fold | claw.infer only does openrouter (needs OPENROUTER_API_KEY) |
| devil-advocate | S1/2cbb6e96 | 147 | NEW nvaex-ops | adversary skill | commands, agents | to fold |  |
| prompt-design | S1/ed17a8ad | 117 | NEW nvaex-ops | prompt/agent/rule design skill |  | to fold |  |
| context7 | S1/d5615f22 | 39 | NEW nvaex-ops | (nothing in plugin) | .mcp.json only; use fork ~/repos/aesop-context7-skill (244KB) | to fold | Docs access as skill + CLI shim, not an MCP server (blueprint 4B.4) |
| github | S1/8cc1afaf | 35 | NEW nvaex-ops | (nothing in plugin) | .mcp.json only; fork ~/repos/github-mcp-server | to fold | Same: gh CLI covers it; no MCP server |
| build-companion | NOT FOUND | - | NEW nvaex-ops | (nothing on phone) |  | cannot fold: not on phone (same probes as adaptive-agent) |  |
| human-in-the-loop | S1/f5234247 | 7392 | NEW nvaex-ops | operator-only task pane as a list skill | hooks, 7.4MB | to fold |  |
| claudestrophobic | S1/c04385b9 | 108 | NEW nvaex-ops | stale session lister (delete step needs operator OK) |  | to fold |  |
| claudebase | S1/91e6ac8a | 475 | NEW nvaex-ops | backup/restore ~/.claude to private repo | hooks, 475KB | to fold | Writes outside the worktree at run time; fine at run time, not build time |
| cut-weight | S1/5c75f9c6 | 133 | nvaex-memory | SKILL.md, references, inventory.py (verbatim) |  | already in package | UNTRIMMED: 13.7+11+6.3KB whole |
| env-setup-wizard | S1/6f20df63 | 145 | NEW nvaex-ops | verified setup-script skill |  | to fold |  |
| notify | S1/0e5ea5c6 | 104 | nvaex-burn | webhook POST (derived into burn.py) | Slack/Teams/Lark/Telegram/desktop | already in package | #1 = S1/0e5ea5c6. Telegram dropped; keep = notification, not usage display |
| caveman | S1/5b256fd0 | 118 | NEW nvaex-ops | concise-mode skill | assets, 118KB | to fold | #1 = S1/5b256fd0. honey skill already covers this; fold only if operator wants both |
| Memory Bank | S1/02abfee3 | 85 | nvaex-memory | memory-bank skill | scripts/memory-bank-hook.sh, CoC/PRIVACY/SECURITY docs | to fold | Added keep |
| mindmap-skills | S1/fd6bdacf | 284 | nvaex-rea-forge | skills/mindmap (one) | mindmap-zh, examples, docs, tests, .github, README.zh | to fold | Added keep; plugin name is "mindmap" |
| Prompt Enhancer | ~/local-plugins/plugins/prompt-enhancer | 74 | NEW nvaex-ops | skills/ (as is, it is tiny) |  | to fold | Added keep |
| claude-time | S1/bd69ea1e | 54 | nvaex-jev-core | current-time injector as part of the existing UserPromptSubmit entry | separate hook entry (one per event rule), PRIVACY | to fold | Added keep |
| task-observer | S2/task-observer; fork ~/repos/aesop-task-observer | 1648 | own plugin dir under plugins/ | WHOLE: SKILL.md, references/, scripts/, USER-GUIDE (from the operator fork) | .git, .github, .code-review-graph; nothing else | whole port | Fork differs from S2 stock (SKILL.md, ceilings.txt): port the fork. Packaging as its own plugin dir, not inside nvaex-ops. jev-core SOURCES.md refuses a copy to avoid double trigger: disable the global ~/repos copy when the plugin is enabled |
| code-review-graph | ~/repos/NovA-code-review-graph | 17796 | own plugin dir under plugins/ | WHOLE: code_review_graph/, skills/, hooks/, pyproject, uv.lock, CLAUDE.md | .git (27MB), .venv, .venv-debian, .code-review-graph (114MB graph.db), .pytest_cache, .beads | whole port | Own plugin dir, not inside nvaex-ops. 17.8MB without venvs. dumbass Stream 1 reads its graph.db: keep schema v13 pinned |
| TinyFish (plugin tinyfish + claude.ai connector) | S2/4709b2dd (181KB); cache/anthropic-plugin-directory/tinyfish | 181 | claw-mcp | (nothing) | .mcp.json, 5 skills | replaced by claw | NOT YET: claw.search "not-implemented"; no run_web_automation equivalent. Brief says replaced; blueprint sec 4B.1 does not list TinyFish. Donors on phone: ~/repos/NvAEx-LEJ-Perplexity-Powered-Search-for-Claude 126KB, Novus-perplexity-cli 25MB, c10vis-crawl4ai 31MB |

## Homes: how many keeps land where

| home | rows | note |
|---|---|---|
| nvaex-ops (NEW) | 46 | too many for one plugin; see Conflicts 5 |
| nvaex-jev-core | 23 | heavy too |
| nvaex-memory | 16 | |
| nvaex-wiki-admin | 12 | |
| claw-mcp | 8 | 6 replaced, consensus, playwright parts |
| nvaex-rea-forge | 5 | colosseum, turbocharge #2, mcp2cli, mindmap, (code-map already) |
| nvaex-ui-cockpit | 3 | context-window, plugin-manager, harness-scope |
| dumbass-memory-mcp | 2 | agent-recall, graph-indexer |
| nvaex-burn | 1 | notify webhook (already) |
| own plugin dir | 2 | task-observer, code-review-graph |
| jev-rea-mcp | 0 | no keep maps to it; it is the server for jev-core, no donor needed; now inside nvaex-jev-core |
| (counts above are the table rows' home column) | | |

## Proposed nvaex-ops contents (NEW package, groups)

- harness-dev: bake-claude-md-files, claude-md-management, claude-perfectionist, instructions-cleanup, agent-design, agent-smith, claude-code-setup, harness, harness-architect, wizard, skill-creator, skill-discovery, plugin-dev, plugin-packaging, skills-updater, mcp-debugging, mcp-server-dev, mcp-tunnels, tool-schemas, claude-deconstruct, devil-advocate, prompt-design, Prompt Enhancer, caveman (24)
- security and review: code-review, review-council, claude-security, public-repo-readiness (4)
- repo care: claudestrophobic, claudebase, env-setup-wizard, human-in-the-loop, build-companion (not found) (5)
- Android and voice: kotlin-lsp, local-whisper, tts, modern-web-guidance, desktop-commander (5)
- Google and cloud: firebase (thin), gcp-devkit, google-multi-account, cloudflare, supabase-expert, design, context7, github (8)

## Still untrimmed, per existing package

Sizes are bytes of files in the worktree today. "Whole" = copied verbatim per SOURCES.md.

- **nvaex-jev-core** (115KB, 16 files): `skills/drunken-master/SKILL.md` 9.7KB whole; `LICENSE-llm-dark-patterns` 11KB (Apache text, required). `scorecard.py` has 13 of 30 checks; 17 not done (donor `hooks/*.sh` absent). `route.py` level heuristic, no taxonomy CSV. Nothing from spec-drift, skill-gate, claude-code-audit-stack, context-protector, safe-bash.
- **nvaex-memory** (359KB, 34 files): `skills/ccfind/scripts/ccfind.mjs` 73KB + `SKILL.md` 14KB whole; `skills/cut-weight` ~31KB whole (inventory.py 13.7KB, SKILL 11KB, quarantine-protocol 6.3KB); `memory_lint.py` 11KB (322 lines, as spec); `licenses/` 48KB, of which `create-smartfolder.LICENSE` 18.7KB (CC-BY full text, can be shortened to a notice only if the licence allows; check). Not built: memsearch-aesop (`~/repos/memsearch-aesop` 8.4MB) and OB1 schemas (`~/repos/OB1`), by SOURCES.md.
- **nvaex-wiki-admin** (430KB, 42 files): `scripts/check.py` 33KB and `wiki_search.py` 33KB, `wiki_evolve.py` 30KB, `wiki_lint.py` 15KB, `evolution-workflow.md` 20KB, `wiki-dedup/SKILL.md` 15KB, `corpus-verify/SKILL.md` 11KB, `convert_raw_to_md.py` 8.5KB. These are copies, not rewrites; wiki_search and wiki_evolve (63KB together) are the best trim candidates. Stand-in `wa_quarantine.py` (real one now found). Missing in SOURCES.md but present on phone: gdrive-to-markdown, compounded, agent-ingest-audit-optimize, llm-secure-patterns.
- **nvaex-rea-forge** (174KB, 17 files): `skills/code-map/template/engine.html` 51KB whole (the biggest single file in any plugin), `generate.mjs` 7KB. `sync.py` and `wrap.py` are minimal stand-ins: turbocharge #2 (S1/71dabb73) and mcp2cli (S1/3763173a) are on the phone. SOURCES.md's claude-war-room "Missing" is true to the brief now (removed), but the plugin is on the phone (S1/2c68a910, 475KB).
- **nvaex-ui-cockpit** (139KB, 23 files): hooks are .tsx rewrites; licences ~4KB. `token-cache-gauge` is a usage display (see Conflicts 1). `tests/gauge.test.tsx` tied to it. No `skills/`, so the cockpit has no discoverable docs besides README. Not built: JEV telemetry feed.
- **nvaex-burn** (76KB, 10 files): `burn.py` 7.7KB is a rewrite, nothing copied. Inert: `usage-live.json` source (heavy-usage statusLine) is not wired and heavy-usage is removed. See Conflicts 1.
- **claw-mcp** (99KB): `claw.search` not implemented; CDP websocket actions not implemented; infer = openrouter only; Kotlin jar untested; no video, no crawl. Both python and kotlin ship (two implementations of the same tools).
- **dumbass-memory-mcp** (47KB): Supabase/OB1 mirror not built; graphify reads JSON not the spec's sqlite.
- **jev-rea-mcp** (43KB): taxonomy CSV, ag-bridge.sh, wiki-task-auditor not present; static inspect only. (Since 2026-11-06 inspect lives in `nvaex-rea-forge` `rea-mcp` and cloud dispatch in `nvaex-burn` `burn-mcp`.)

## Conflicts with the brief and with CONTRACT.md

1. **nvaex-burn and nvaex-ui-cockpit are built from plugins the brief removes.** burn.py is derived from burn-baby-burn and heavy-usage (both on the removed list); the cockpit's token-cache-gauge is derived from cache-ttl-timer, context-bar, gas-gauge and is itself a usage display. Brief: "nvaex-burn's scope is unchanged unless the mapper finds a conflict". Conflict found: (a) the brake/burn thresholds read a usage source that only heavy-usage provided and that is now absent, so burn is inert until the operator's custom usage display writes it; (b) token-cache-gauge duplicates that custom display. Both packages are re-derived rewrites (no upstream files copied), so removal of the stock plugins does not break them; the question is whether the gauge mod stays. Not decided here.
2. **"Replaced by claw" is not true yet.** The brief removes TinyFish, firecrawl, apify, claude-bridge, watch-video, adb-mcp and playwright-the-server; claw-mcp cannot search, crawl, drive a page (CDP actions), watch video, or run adb install/tap/test. Removing the stock ones first leaves no web tools on either account. Order: build claw.search/scrape/browser/device from the phone-side donors first, then remove. Donors on the phone: `~/repos/NvAEx-LEJ-Perplexity-Powered-Search-for-Claude` (126KB), `NovA-openrouter-mcp`, `playwright-mcp` (354KB), `NvAEx-chrome-devtools-mcp`, `c10vis-crawl4ai`, `Novus-perplexity-cli`, `NvAEx-DroidDesk`. TinyFish is in the brief's replaced list but not in blueprint 4B.1's list of seven (blueprint lists Playwright, pplx-unofficial, adb-mcp, claude-bridge, watch-video, use-gcloud, openrouter-mcp).
3. **Operator's question "WebTools config already established in the Frankenstein?"** Answer from the files: claw-mcp exists with the 6 tool schemas, and `claw.scrape` works as a basic fetch; `claw.search` returns not-implemented. So the config exists, the web capability does not.
4. **Whole ports vs package rules.** task-observer: jev-core SOURCES.md deliberately did not copy it (double trigger with the global ~/repos/aesop-task-observer). A whole port makes the plugin the single copy; disable the global one when the plugin is enabled. The fork (`~/repos/aesop-task-observer`) differs from the stock S2 plugin; port the fork. CONTRACT rule 2 (standard plugin shape): neither has a `.claude-plugin/plugin.json` of this marketplace's shape (S2 task-observer has one; NovA-code-review-graph has none at its root). Whole ports need a wrapper plugin.json only. code-review-graph is 17.8MB (without .git/.venv/graph.db), which dwarfs every other package; CONTRACT rule 1 (self-contained) holds, size does not matter to the contract, but report it.
5. **nvaex-ops (46 skills) and nvaex-jev-core (23) are over the routing threshold** the blueprint itself uses (>30 flat tools/skills = 15.7% misrouting). Suggest splitting nvaex-ops into nvaex-harness-dev (24 harness-dev rows) and nvaex-ops (security, repo care, Android, voice, Google, cloud: 22 rows), or relying on harness-scope profiles. The brief allows one NEW package; a second needs operator OK.
6. **SOURCES.md "Missing" claims that the phone contradicts** (so the "do not invent" rule does not cover them anymore; they can be folded): gdrive-to-markdown, compounded, agent-ingest-audit-optimize, llm-secure-patterns (wiki-admin); mcp2cli, turbocharge customize-and-sync (rea-forge: it checked turbocharge S1/0e956c57, the wrong one); cache-caffeine (S1/271e15b5, used by burn already); claude-war-room (removed anyway). Still genuinely not on the phone: adaptive-agent, build-companion, plugin-eval, plugin-improver, statusline-pro, claude-hud, context-protector, safe-bash, Claude-Trinity/code-janitor, pplx-unofficial-mcp, use-gcloud-mcp. Probe for all: name scan of 493 plugin.json under synced (both accounts)/local-plugins/cache plus `find -iname` in ~/repos; "not found by those probes", not "does not exist".
7. **Two caveats on "cannot fold".** jevmem and graph-indexer are functionally covered elsewhere (jev-core local router + dumbass record_claim; code-review-graph + dumbass Stream 1) but are keeps by the list. Marked cannot fold pending the operator's OK to drop. google-multi-account's MCP, graph-indexer's MCP, jevmem's MCP and claude-bridge's chrome-devtools MCP currently fail to connect this session (ENOENT stdio / CONNECTION_CLOSED).
8. **claude.ai connectors** (Drive, Gmail, Calendar, Sheets, Slides, Docs, Supabase, Hugging Face, TinyFish, AgentMail) are account-side, not plugins on the phone. gdrive-to-markdown, drive-find and google-multi-account all depend on them; removing "stock" on the accounts will break those unless a local route (rclone, direct API) is built. The map does not list connectors as rows.
9. **Playwright** donor lives in `~/repos/playwright-mcp` (354KB) and `~/repos/playwright` (77MB), not in the synced plugin (a 35KB `.mcp.json`).
10. **Contract rule 4** (one hook entry per event per package): airquote, claude-time, chuck, better-compact, chat-autoexporter, memory-bank, handoff, cc, backlog all want hooks; each must be merged into the package's existing entry for that event (jev-core already uses UserPromptSubmit, PostToolUse, Stop; nvaex-memory SessionStart, Stop, SessionEnd; wiki-admin PostToolUse, SubagentStop). better-compact needs PreCompact, new to nvaex-memory.
