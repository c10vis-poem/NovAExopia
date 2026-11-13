# DRAFT list, INCOMPLETE: what is still to do (2026-11-12 22:05 PST)

NOT the master list: not everything has been read (owner, 21:59). Read so far: everything named below, plus the
contracts a5b45d30-A1, A2, B, C1, C2 and a96eac98-A, and NovAExopia `docs/plugins/contract-a/owner-steps.md`,
`recon.md`, `anthropic-guidance.md`. NOT read: the 2026-11-11 contracts of other sessions (Recaps
`contracts/2026-11-11/*`), the Recaps `Security Breach-d1c1bec4.../` files, `audits/2026-11-10-device-inventory/`,
the older handoffs (2026-11-06, -08, -10, -11 except cc782951-rules-live and 3c1dfa47 not read either), the Greedy-crane
compilation (24 files), the owner's ~140-200 wiki-admin files, Recaps `session-logs/`, the transcripts of sessions
a5b45d30, a96eac98, 7c7b204b. Files changed after 16:00 by a git checkout (not new writing) are not counted as read.

Built by session b3e21f66 from: its own work and contracts A, A2, A3; session a5b45d30
(NvAEx-Recaps `handoff/2026-11-12/handoff-a5b45d30-wiki-admin-report.md`, vault
`01-inbox/compiled/WIKI-ADMIN-REPORT-2026-11-12.md`); session a96eac98 (Recaps
`handoff/2026-11-12/open-questions-a96eac98.md`); Recaps `handoff/2026-11-12/handoff-cc782951-next.md`; this repo's
PENDING.md; Recaps `memory/active/enforcements.md` and `memory/active/wiki-admin.md`.
Status words: NOT LIVE = fixed and tested in code, not pushed or installed. OPEN = not started. OWNER = needs the
owner's decision or hand. Every item that deletes anything lists the files by name for the owner first.

## 0. Right now (blocks everything else)
1. NOT LIVE. The prompt hook times out (over 20 s) on every prompt since about 20:42: the owner's #go #push #ok
   #redo are lost. Cause: rules 1.0.1 runs every Check of every task up to the current one on every prompt and tool
   call. Fixed in 1.0.2 (Checks only at the stop, once each; closed tasks never re-checked). Install from a plain
   terminal (commands in section 9).
2. OWNER. Conflict: owner decision 2026-11-12 21:03 (session a96eac98) "No reads should be blocked in a contract.
   period." vs 1.0.2, which blocks reading `~/.claude/state` (to keep a pending quiz's answers hidden). Owner picks:
   reads always open (then the quiz answers must move out of state.json), or the state folder stays closed.
3. OWNER. Owner decision 21:00 (a96eac98): "If I say okay, that means okay. If I say Go, that means go." 1.0.2 still
   refuses a #go when the work order has a format error. To fix: #go always signs; format errors are the agent's to
   fix after.
4. OPEN. Push both fix branches (needs a recorded #push, or the owner's terminal): Aesop-Xi
   `fix/holes-2026-11-12` (2 commits, in `~/repos/wt/a3-aesop-xi`), NovAExopia `fix/holes-2026-11-12` (1 commit +
   this list). PRs with auto-merge.
5. OWNER. Remote control: "Disconnect remote control" shows, the session link says page not found.
   `~/.claude/.credentials.json` was rewritten 2026-11-12 16:52:30, mid-session. Which account it holds: not checked
   (needs `~/.claude.json` oauthAccount). The owner's "on by default" setting did not start it at launch: cause not
   found.

## 1. Rules plugin flaws (Aesop-Xi `plugins/aesops-enforcements`)
6. NOT LIVE. The same stop block came back after every turn. Fixed (named once; only a changed list blocks again).
7. NOT LIVE. "read-only" counted as a read claim. Fixed.
8. NOT LIVE. Read-only ls/find/wc/grep/stat/diff refused on protected folders (rule 8). Fixed for the plugin and
   owner copies (state folder: see item 2).
9. NOT LIVE. grep, sed, awk, diff, python could print secret files. Fixed.
10. NOT LIVE. Two hooks at once crashed (FileNotFoundError on `.state.tmp`). Fixed.
11. NOT LIVE. Lie-test holes 2-6: plain-word and "tests pass" claims; bare file names; quiz beaten by a folder
    search; split or built paths and scripts; sub-agent Last action. Fixed with tests.
12. NOT LIVE. Opening reads every document the opening files point to. "Nothing skipped" deferral check. Jev audit at
    the stop (decision 2). Prompt shape logged (paste vs typed). RULES.md rewritten for each.
13. OPEN. The hook sets the contract DONE when every line looks met, then refuses everything but Read until #ok or
    #redo (a5b45d30 flaw 2; this session's A2 the same). Owner: only he marks anything done; nothing locks the
    agent; "met" is a note, the contract stays ACTIVE until #ok.
14. OPEN. `contract.py:255` never checks the LAST task for "no STEP or REQUIRE": an empty last task signs and counts
    as met (a5b45d30 flaw 1).
15. OPEN. #redo sends the order back for a new #go instead of reopening the run; the owner typed #go 5x, #ok 2x,
    #redo 2x for one report (a5b45d30 flaw 3).
16. OPEN. `<` or `>` anywhere in a Bash command, even a quoted commit message (the Co-Authored-By email), is refused
    unless it is an exact STEP (a5b45d30 flaw 4; this session's breach 3). Same for `|` and `;` (breaches 1, 4).
17. OPEN. The stop hook re-opens the OPENING mid-session when another session changes an opening file or a newer
    Recaps handoff appears (a96eac98 flaw 7; a5b45d30: date change re-opened it). Owner: the opening is once.
18. OPEN. A signed STEP that touches a protected path is accepted at signing, then refused at run time, then the
    stop demands it: deadlock (a96eac98 flaws 9-10). Signing must check steps against protection.
19. OPEN. Reading the agent's own written file refused as "outside contract" (a96eac98 flaw 11). Decision 21:03.
20. OPEN. `#ßredo` (keyboard turned # into ß) not registered (a5b45d30 timeline 21:12). Accept look-alikes or tell
    the owner his verb was not seen.
21. OPEN. A pasted #push counted as the owner's (handoff cc782951 item 8). Shape logging is in 1.0.2; the fix needs
    one live paste after install.
22. OPEN. Hole 1 (sub-agent hand-back refused) was fixed by contract C for the tool name `SubagentHandback`;
    whether that is the real hand-back path is unproven (needs a live sub-agent run).
23. OPEN. Adapters so the rules and hooks run for other agents: AGY (format read: `.agents/hooks.json`, PreToolUse
    `decision: deny`, Stop `decision: continue`, camelCase; tools `run_command` CommandLine, `view_file`
    AbsolutePath, `write_to_file` TargetFile), Hermes (shell hooks in `~/.hermes/config.yaml`; its `hooks.md` is
    quarantine-flagged: owner releases; Hermes never proven to run here), DSH (not researched). Gemini CLI: not
    installed.
24. OPEN. Old-gates features (Aesop-Xi `docs/old-gates-features.md`, 82 features, tags `old-gates/*`): the owner's
    three categories (better version exists / still needed / delete with reason), then port or strike.
25. OPEN. RULES.md review with the owner, rules 2, 3, 5-11 (handoff cc782951); then remove the duplicate memory
    notes (frozen claims 1ac9cfb8 ... f66841fd) with the owner's okay; the harness rule (decision 14) into AGENTS.md.
26. OPEN. Bugs open a freelance fix contract that nothing blocks (decision 6).
27. OPEN. Sub-agent protocol and sub-agent auditor (owner 16:27; PENDING 2026-11-09: parameter-vs-target and
    claimed-step vs tool-history checks missing). No sub-agents until then.
28. OPEN. Rule 4 "unless the operator directs it"; Rule 11 conflict; first-turn stop items as notes; RULES.md and
    gates.tsv numbering (PENDING 2026-11-09).
29. OWNER. The 8 `.bak` files in the rules plugin (`RULES.md.bak5`, `contract.py.bak/.bak3/.bak4/.bak5/.bak8`,
    `hook.py.bak/.bak3`): delete.
30. OWNER. Old plugin leftovers, no longer installed: delete `~/.claude/plugins/cache/novaexopia/aesops-enforcements/0.1.0`,
    `.../nvaex-gates/0.1.0`, and Recaps `.wt-session-log-20b12ae6`, `-637ce09e`, `-8e5ac076`, `-b00b3006` (commit the
    19-line log of b00b3006 first).
31. OPEN. The leftover skills `ok`, `defer`, `reject`, `wrapup` come from Aesop-Xi `deploy/phone/commands/*.md`:
    what each does, still needed, who else has it; rebuild or remove.

## 2. jev-core and the Jev gates
32. NOT LIVE. jev-core 0.4.2: Gate 3 false alarms (edit count, 300-character key), scorecard names files, hooks
    quiet on bad input. The phone runs 0.4.0: even 0.4.1 was never installed (handoff said it was).
33. OWNER. jev-core kill switches in every hook (selftest lines 95-102) and the scorecard's "Silence:" line: remove?
34. OPEN. The six Jev gates (decision 9): one key, one config file and menu, per-gate on/off, strictness, questions,
    model, unsure/unreachable behaviour, log and status line. Exists: router only.
35. OPEN. JEV showed `local-fallback (no-key)` in session a5b45d30's launch: the TypeSafe key did not reach it there.

## 3. Repos onto one main, and the refresh
36. OPEN. `~/bin/repo-sync` and the shims are written; the real refresh has never run (only `--report`). Live check
    after the merges.
37. OWNER. `~/.zshrc`: a stray line 25 ("  and ~/bin/shims to undo") may still be there.
38. OWNER. The 24-item consolidation list (`docs/audits/2026-11-12/consolidate.md`): one decision each.
39. OPEN. Vault folder on branch `report/wiki-admin-2026-11-12` (deleted on GitHub): back to main (a5b45d30 item 1).
40. OPEN. Commit and PR: a5b45d30's handoff and contracts `a5b45d30-{A1,A2,B,C1,C2}.md`; a96eac98's
    `open-questions` file and contract `a96eac98-A.md`; this session's `b3e21f66-{A1,A2,A3}.md`; NovAExopia
    HANDOFF.md edits by a5b45d30 and a96eac98 (keep both).
41. OPEN. NovAExopia local branches `memory-trim-2026-11-11` (3a5fd11), `docs/contract-a-lie-test` (e1c04d6): in
    origin/main? (a96eac98 questions 1-4.)
42. OPEN. Marketplace ref `rules-fix-2026-11-09` -> `main` in every repo's settings; `aesop-xi` marketplace ->
    GitHub (owner's hand: settings).
43. OPEN. The four repos never merged (AEthX-AEsc, CloviX-AEyre, Hyperion-XI, NovusAExenti): their 2026-11-09
    agent settings branches.
44. OPEN. `repo-sync` and the shims into git so every device gets them.

## 4. Memory
45. OPEN. Agent-wide memory layer (`continuity/_agent.claims.jsonl`), `memory_freeze scope: agent|project`,
    definitions there; an agent file for dumbass memory; a start-up flag for any plugin a project turned off.
46. OPEN. Who turned the memory plugin off is still unknown (handoff cc782951 lines 15-17).

## 5. Mods
47. OPEN. Mods as pop-up selection menus like /config: Jev gates, rules and contracts, memory; the plugins panel with
    active/available counts, the environments/agent-configs side panel, the top-bar plugin menu, config file tree,
    context and cache-TTL gauge, browser choice cards, Jev side panel (decision 10, PENDING 2026-10-28).

## 6. Wiki admin (greedy-crane)
48. OWNER. The 26 greedy-crane audit items (report section 7), none approved.
49. OWNER. The 8 owner questions (report section 9): agy account (Pro or Ultra); second Gemini and second Claude
    account; Supabase project; OpenRouter key name; what may go in the public vault; `tablet-age-key.txt`; the
    duplicate vault copies and QAIRT dump; which Download folders are research.
50. OPEN. Work order D (report section 10): route tests (agy Flash, agy Argon/Carbon, EG2 server on 8085, Qwen 3.5
    0.8B on GenieX, OpenRouter, Supabase); read the Greedy-crane compilation (24 files) and compare; batch ledger
    for sets B-F; vendor folders with sha256 manifests; approved audit items.
51. OPEN. The 8 staged files in `01-inbox/`: promote by name with the owner's okay.
52. OPEN. Old wiki-admin backlog (PENDING 2026-10-28, memory/active/wiki-admin.md): Gemini profile, housekeeper,
    chunker (owner decides E6 chunk schema, E10 frontmatter), semantic lint; MAP.md (5 lines, routes nothing); the
    140-200 file set; link `skills/wiki-admin-core`; `honey`/`honey-px` not found (audit item 12).
53. OWNER. `plugins/nvaex-wiki-admin` duplicates greedy-crane: list its features, port or strike, then delete.

## 7. Clean-up and conflicts
54. OPEN. Conflicting rule files: `~/.claude/CLAUDE.md`, `~/.agents/AGENTS.md`, `~/CLAUDE.md`, this AGENTS.md
    (auto-merge on green vs #push; the sub-agent standing order vs no sub-agents).
55. OPEN. Duplicate skills: task-observer, corpus-verify, wiki-admin-ingest, notebooklm, gemini-api-dev,
    android-termux-operator, termux-helper.
56. OPEN. Two copies of each MCP server for Claude (`.mcp.json` and the plugins); code-review-graph only in
    `~/.claude.json`; `router-guard` start-up hook still warns about OmniRoute (PENDING 2026-11-09).
57. OWNER. Secrets: TinyFish key in plain text in `~/.zshrc` line 23 and `~/.claude/settings.json` (rotate);
    `tablet-age-key.txt` in shared Documents.
58. OWNER. `tools/bootstrap.sh` calls the missing `~/repos/aesop-xi`: delete or repoint.
59. OPEN. Task-observer: weekly review overdue since 2026-10-23; the session-start scan never ran this session;
    lost entry 0045; log this session's corrections.
60. OPEN. Two parallel work orders (sessions A and B) once items 1-4 are live.

## 7b. Added from the two sessions' contracts and the contract-a docs (2026-11-11)
61. OPEN. Every agent this session and both parallel sessions added END limit time lines themselves (a5b45d30-A1 60m,
    A2 20m, B 10m, C 5m; a96eac98-A 10m). Owner, 16:57: only the owner adds END lines. Rule written in 1.0.2
    RULES.md; nothing enforces it yet: refuse to sign an agent-added END line, or strip it.
62. OPEN. a96eac98-A: a signed STEP `cp <state>/notes.md ...` deadlocked (see item 18): signing must check STEP paths.
63. OPEN. Recaps contracts folder and handoff files of today are not committed (item 40) and Recaps itself is behind:
    commit + PR.
64. CHECK. recon.md (2026-11-11) false alarms and gate defects, each to re-test against 1.0.2: `Server:` name forms
    (both forms now matched in code: confirm live); question-form "read `X`" counted as a claim (NOT_A_CLAIM exists:
    confirm); edit voids every read (line hashes now: confirm); lines over 2000 characters (truncated match: confirm);
    non-text reads (binary record: confirm); `git -C <dir> push` hold (canonical_bash: confirm); `<root>/.contract/
    opening.md` writable (CONTRACT_DIR protected: confirm); protected-file change froze the session (now warns:
    confirm). 14,156 repeated stop items in one session (7c7b204b): the 1.0.2 "named once" fix: confirm live.
65. OPEN. anthropic-guidance.md: repeating notices (Gate 3, JEV route, unmet lines, breach counts) belong in the
    status line, not additionalContext. Not done. The JEV route line lists up to 19 skills every prompt.
66. OWNER. owner-steps.md step 3: status bar, replace the synced plugin's `statusline.sh` with the contract status
    line, or a wrapper that shows both.

## 8. Struck by the owner (do not do)
- The ~515-plugin marketplace backlog; Frankenstein-Review. (The 73-plugin batch in `~/repos/NovAExopia` waits on
  consolidation item 3.)

## 9. Install the fixes (owner, plain Termux terminal, not inside a session)
```
git -C ~/repos/Aesop-Xi merge --ff-only fix/holes-2026-11-12
claude plugin marketplace update aesop-xi
claude plugin update aesops-enforcements@aesop-xi --scope user
cd ~/repos/NovAExopia-main && claude plugin update aesops-enforcements@aesop-xi --scope project
claude plugin marketplace update novaexopia
claude plugin update nvaex-jev-core@novaexopia --scope user
cd ~/repos/NovAExopia-main && claude plugin update nvaex-jev-core@novaexopia --scope project
```
Then resume this session with the new hooks: `crane --resume b3e21f66-bc67-4e08-8b8d-372e71a17110`.
