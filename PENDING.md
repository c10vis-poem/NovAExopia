# PENDING.md — NovAExopia

Durable cross-session backlog. Not rewritten each session — items persist until resolved or explicitly dropped.

- **`horizons-ui/` subfolder needs reconciling.** Added 2026-09-07 per Document 05 (commit `c197580`, "feat: add Document-05 top-level dirs"), which is the nested-repo model. Superseded now that RFMC's flat 8-repo model is the actual direction (2026-09-15 decision) — a new standalone Horizons UI repo is being built separately. Resolve this subfolder once that lands: likely removed.
- **No ingestion pass yet otherwise** — rest of `clean_md/`/`wiki_md/` are still POINTER.md stubs per NovAExorpus's RESUME.md.

## 2026-10-23
- Marketplace `novaexopia`: plugins not yet listed because no public source repo was found: cowork-plugin-management, obsidian-sync, shipwright (0.2.0). The remaining ~515 plugins from the operator's Drive `NewPlugins` folder are added in batches.

## 2026-10-28 (wiki admin tools)
- Store the Gemini key (`nvaex-secret set GEMINI_API_KEY`), install `google-genai` (the install did not finish in 280 s), run one live `gemini_infer.py draft`. Confirm the default model ids in `gemini_infer.py` against Google's model list.
- Not built: Gemini profile YAML, housekeeper, chunker (needs chunk schema decision E6), semantic half of lint. Operator decides E6 (chunk schema) and E10 (frontmatter schema).
- After merge: link `skills/wiki-admin-core/*` into `~/wiki-admin/.claude/skills` and run the skills in a `wiki-admin` session.
- Read the operator's full wiki-admin file set (140 to 200 files; location to confirm) before wiring further.
## 2026-10-28
- Web view tool: operator pairs wireless debugging, then `bash mcp_connectors/webview/bin/webview-connect --adb 127.0.0.1:<port>`; then finish the fork build (`node scripts/post-build.ts` in `NvAEx-chrome-devtools-mcp`) and test that the server lists its tools. Both were blocked by the auto-mode safety classifier.
- Web view tool, later: headless / own-Chromium mode for Hyperion-XI and AEthX-AEsc app WebViews, a search tool, a marketplace entry (after `feat/marketplace-batch-2` lands).
- Mods (see `mods/`): plugins panel with active/available count, environments/agent-configs side panel, Obsidian-style config file tree, context and cache-TTL gauge, browser choice cards with a prompt bar, Jev side panel. Only the old plugins-panel exists (in NvAEx-Recaps); move it here when mods work starts.

## 2026-11-05
- Operator goes item by item through Frankenstein-Review; fix each, then ship frankenstein-v2 through a PR. Not pushed.
- Build sub-agent harness plugin; add real REA server; port task-observer and code-review-graph whole; Claude-only split; hook source to Aesop-Xi.

## 2026-11-09 (security-breach session d1c1bec4, "Termux audit"; record: NvAEx-Recaps `Security Breach-d1c1bec4-e840-4acf-84d6-67a1d464a00f/`)
### Fixed on branch rules-fix-2026-11-09 (not merged)
- Step-aside switch removed from `aesops-enforcements/scripts/run-gate.sh` and greedy-crane `hooks/stop-gate.sh`, `hooks/quarantine.sh`.
- direction-gate: a `#` anywhere in the message, or the word "hashtag", is a direction (Claude Code can drop a leading `#`); okay, amend, override, defer and go ahead open the job at the start of any line; reads and skills that ENFORCEMENTS requires pass as part of the opening protocol. Tests: 43 + 208 pass.
- question-gate: the Rule 2 check-in (okay, amend, override, defer) is not flagged; the merge check catches only orders to merge.
- stop-gate: staged skill updates are a note, not a block.
- Repo settings for every agent: `.claude/settings.json`, `.mcp.json` (6 servers, each answered tools/list from the repo root), `.agents/plugins.json`, `CLAUDE.md` pointer to AGENTS.md.
### Rules still to finish (RULES-DRAFT.md, the eleven rules)
- `RULES.md` and `gates.tsv` still use the old ten-rule numbering; renumber to the eleven.
- Rule 4: add "unless the operator directs it"; operator decides whether rule files are covered.
- Rule 4 guard false positive: settings-guard blocks any command whose text mentions the hooks-off key with the value on, even inside a note.
- Rule 9: only "not found needs a search" exists; add claim-needs-a-read (file and line) and done-needs-a-real-test.
- Rule 11 conflict: task-gate and enforce-gate block on routed skills and reads; RULES-DRAFT says never a stop (a light and an RLVR record), while the operator said 2026-11-08 "skills are stopped on keywords". Operator decides.
- Rule 11 light and the bypass notice (custom mods) are not built.
- First-turn stop-gate items cost up to 3 blocks (TO-DO 2026-11-06): make them notes.
- `subagent-task-gate` lacks the spec's parameter-vs-target check and the claimed-step vs tool-history check (Read this, Subagent Persuasion 04-05).
### Hooks and plugins
- Duplicate hooks: `nvaex-wiki-admin` and greedy-crane register the same quarantine and worker-stop hooks; greedy-crane is current.
- Claude starts the `.mcp.json` servers and the plugin servers, so it sees two copies of each; pick one route per agent.
- `code-review-graph` MCP is configured only in the phone's `~/.claude.json` (phone venv path); give it a portable entry.
- `router-guard` startup hook (vault): trace its source; it warns about omniroute and terrestrial-brain.
- Aesop-Xi project settings switched every hook off (the hooks-off key set on, PR #83, 2026-10-31): fixed on its branch.
- After merge: switch the marketplace `ref` in every repo's `.claude/settings.json` from `rules-fix-2026-11-09` to `main`.
### Staged skill updates (vault `skill-updates/PENDING.md`)
- Hook specs (`skill-updates/2026-10-08/proposals/hooks-spec.md`): unbuilt hook designs; operator decides which to build.
- Upstream draft (`skill-updates/2026-10-08/proposals/task-observer-upstream.md`): fix already in the fork (aesop-task-observer PR #1); send upstream or drop.
### Observer
- Weekly review overdue since 2026-10-23 (33 open plus this session's). Log every correction from session d1c1bec4 as its own observation.
- Lost entry `0045-read-token-limit-friction.md` (no header).
### Incident follow-up
- Ten PRs were merged mid-session (NovAExopia #20-22, vault #78-79, Recaps #21-25) against Rule 8; review them.
- Session f45e5ad0 deleted 25 files (NvAEx-Recaps `handoff/2026-11-08/DELETED.md`); `weights-1-8.nexa` was not byte-identical to the kept copy.
- JEV has never answered: TypeSafe key not set (`nvaex-secret set TYPESAFE_API_KEY`).

## 2026-11-10 (session 437a362c)
- After Aesop-Xi merges: point `.claude/settings.json` marketplace `aesop-xi` at GitHub (`c10vis-poem/Aesop-Xi`,
  `main`) instead of the local folder, so other devices load the rules (operator runs it: settings are guarded).
- Marketplace `ref` here still `rules-fix-2026-11-09` for `novaexopia`/`nvaex-vault`: switch to `main` after merge.
- odometer and speedometer marketplace entries: operator decides (gas-gauge removed).
- `plugins/nvaex-wiki-admin` duplicates greedy-crane: operator decides (the wiki pipeline is being redesigned).
- Main-session agent audit (greedy-crane's skills and tools used, like the sub-agent gate): proposed, waiting on okay.

## 2026-11-12 (session b3e21f66, contract A)
- `tools/bootstrap.sh` calls `~/repos/aesop-xi/tools/bootstrap.sh` (no such folder; the clone is `~/repos/Aesop-Xi`),
  and the stack it would start is dropped. Owner decides: delete it, or point it at something current.
- Rule 8 read-only listing fix: patch and tests in `docs/audits/2026-11-12/rule8-find-fix.md`; owner applies.
