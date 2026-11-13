# Everything onto one main (contract A2, task 1), 2026-11-12 17:01-17:10

Sources: `repo-sync --report` over 107 folders (~/.local/state/repo-sync/last.txt), `gh pr list --state all` and
`gh pr view` for the owner's repos, `git status --short` and `git diff --stat` per repo named below.

Not decisions (the refresh handles them): forks that are only behind GitHub (NovA-skills 3, NovAE-context7 77,
NvAEx-prime-agent 224, reverse-skill 179, speech-to-speech 1671, termux-app-store 330, and others). In forks,
`gh pr list` and the mirrored branches show the upstream project's PRs and branches, not the owner's.
"Not in main" from the report is a false alarm for branches whose PR was merged (squash merge, main changed since).

## Decisions (owner: merge or drop, per number)

### NovAExopia
| # | What | Holds | Recommend |
|---|---|---|---|
| 1 | this session's edits in NovAExopia-main | AGENTS.md memory section rewrite; PENDING.md 2026-11-12 items; docs/audits/2026-11-12/ (rule8-find-fix.md, this file) | merge |
| 1b | same folder, jev-core Gate 3 fix | health.py, fail.py, hooks.json, tests/selftest.sh; NOT TESTED (A2 has no line to run the selftest) | merge after one selftest run |
| 2 | .claude/harness-scope.json (untracked) | `{"profile": "writing"}`; what wrote it: not found | drop (leave out of git) |
| 3 | ~/repos/NovAExopia folder on feat/marketplace-batch-2 | uncommitted marketplace.json +739 lines: the marketplace batch (the ~515-plugin backlog struck 16:40) | drop: committed onto that branch, folder moves to main |
| 4 | PR #14 claude/project-thread-99s33n (2026-10-25) | notify-vault workflow mints a GitHub App token instead of the PAT. Same branch open in CloviX-AEyre #11, Hyperion-XI #10, NovusAExenti #10, vault #59 (vault adds tools/vault-app setup); AEthX-AEsc merged it (#15) | one answer for all five; merge only if the GitHub App is set up (not checked) |
| 5 | 8 local branches (aesop-enforcements-2026-11-08, feat/plugin-marketplace, gemini-skills-adopt-2026-11-07, hooks-in-settings-2026-11-08, rules-fix-2026-11-09, ship-wait-for-checks-2026-11-08, webview-and-mods, wiki-admin-tools) | PRs #13 #15 #16 #20-#23 merged; gemini-skills checked file by file 2026-11-12 (RESTART-HERE.md 34-35) | in main: nothing to merge |

### Aesop-Xi
| # | What | Holds | Recommend |
|---|---|---|---|
| 6 | 8 untracked .bak files in plugins/aesops-enforcements | RULES.md.bak5, contract.py.bak/.bak3/.bak4/.bak5/.bak8, hook.py.bak/.bak3 | drop (protected: the owner deletes them) |
| 7 | second folders Aesop-Xi-contract-a (contract-c/fixes, #91 merged) and wt-docs (docs/memory-2026-10-23, #78 merged) | nothing unmerged | move both to newest main |
| 8 | PR #84 hooks/safety-net-enable-all (2026-11-03) | the old hook system (run-hook.sh): turn every hook back on | drop (close): superseded by aesops-enforcements |
| 9 | local branches with no PR: fix/opening-deadlock-2026-11-10, fix/opening-one-source-2026-11-10, gates-dev-2026-11-10, rebuild-2026-11-10 | the old gates, saved as tags old-gates/* (handoff 2026-11-12 lines 30-32) | drop |
| - | old-gates-features.md | PR #93 MERGED; the phone was 1 commit behind | refresh brings it |

### NvAEx-Recaps
| # | What | Holds | Recommend |
|---|---|---|---|
| 10 | uncommitted | memory/layers.jsonl (+1 line), memory/2026-11-12.md, memory/weekly/2026-W45.md, contracts/2026-11-12/ (owner copies the rules hook wrote), 4 .wt-session-log-* folders | merge |
| 11 | PR #14 session-2026-11-05b (RLM, JEV and REA notes), PR #5 recaps 2026-10-24 (10 lines) | notes only | merge |

### Vault (NovAExorpus)
| # | What | Holds | Recommend |
|---|---|---|---|
| 12 | uncommitted | wa_quarantine.py: a rule that forbids an act ("cannot print secret files") is no longer flagged as an order, and the script skips scanning itself; checkpoints.log +5 lines; 01-inbox/ 7 drafts (wiki-admin-refine 3, corpus-survey 3, compiled/PLAYBOOK.md) | merge; drop wa_quarantine.py.bak |
| 13 | PR #73 "Delete AGENTS.md" (2026-11-04) | deletes the vault AGENTS.md ("Start here") | drop (close) |
| 14 | PR #72 "homework: finish P1 and P3" (2026-11-04) | handoff/2026-10-31 homework files, PENDING and RESUME one line each | owner decides |
| 15 | PR #71 "MEMORY: 2026-11-03 startup rules" | MEMORY.md +8, agents/CLAUDE.global.md (new) | owner decides (likely superseded) |
| 16 | PR #58 "Jev corpus triage workspace and benchmark" (2026-10-24) | 27 files, 9,838 lines (Jev-Corpus-Triage/) | owner decides |
| 17 | local branch backup/local-main-044d369 | no PR | owner decides |

### Other repos of the owner
| # | What | Holds | Recommend |
|---|---|---|---|
| 18 | AEthX-AEsc, CloviX-AEyre, Hyperion-XI, NovusAExenti: each on rules-fix-2026-11-09, NO PR in any of them | per-repo agent settings from 2026-11-09: .claude/settings.json, .mcp.json, .agents/plugins.json, CLAUDE.md pointer, AGENTS.md (+107 to +121 lines each). Never merged | merge, after the marketplace ref in their settings is main (PENDING.md: ref still rules-fix-2026-11-09) |
| 19 | NovusAExenti wiki-admin-fixes-2026-10-29 (local only) | executor-core/corpus-ingest agent package (13 files) | drop: greedy-crane's corpus-ingest replaces it |
| 20 | aesop-task-observer on task-observer-sonnet (no PR) | SKILL.md +1 line | owner decides |
| 21 | dsh-jev uncommitted | packages/core/src/index.ts and index.test.ts (+92 -6), .tgz/ | owner decides (work in progress?) |
| 22 | OmniRoute (dropped stack): 4 uncommitted, fetch failed | - | drop (leave) |
| 23 | ECC-aesop (parked): 1 uncommitted | - | leave |
| 24 | honey-main: second folder of NoVa-honey-for-devs | nothing unmerged | move to newest main |
