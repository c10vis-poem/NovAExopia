# Session wrap-up protocol

Triggered ONLY by the `/wrapup` command (`commands/wrapup.md` in this plugin); mentioning "wrap up" in a sentence does nothing. Wrap-up mode unlocks the git gate. Do the steps in order, then tell the operator. The Stop gate names them W1-W8 (`scripts/stop-gate.sh`, header) and refuses to close while any is missing. The Stop gate won't let the session close until every START HERE item is confirmed done (`#ok N`) or deferred (`#defer N`, then in PENDING.md) by the operator. An item an earlier session already left unfinished needs the operator's reason to be deferred again (`/defer N why: <reason>`), or it has to be finished (H9).

1. **Commit** every repo touched this session onto local topic branches (good messages, no `git add -A` of old work). Don't push one by one.
2. **Task-observer:** log this session's corrections and rule violations as observations, and mark resolved ones.
3. **Memory:** save new durable facts and feedback, and update or delete stale notes. Write a handoff note only from files actually read (list what was read and what wasn't).
4. **PENDING.md** (vault): add new open items, remove finished ones. If housekeeping is due, run `/housekeeping` now: the Stop gate holds the wrap-up until it is done or the operator types `#housekeeping-defer`.
4b. **Per-repo docs, for EVERY repo touched this session** — done here at wrap-up, not scattered through the session:
   - `AGENTS.md`: update it if this session changed the repo's rules, workflow, layout or conventions.
   - `MEMORY.md`: **every repo gets one.** Create it if missing (durable facts about the repo: what it is, decisions, gotchas, current state, dated). Add anything new learned this session.
   - `PENDING.md`: add this repo's new open items, remove finished ones.
   - Commit these onto the session branch with the rest of the repo's work, so they ship together.
5. **RESUME.md** (vault, plus any repo worked in that keeps one): **rewrite from scratch**: state, decisions, open items in order, next steps, sources read/not read, and **today's date in the first 40 lines**. Enforced: in wrap-up mode the Stop gate (`stop-gate.sh`, W5) refuses to end the turn until the repo's and the vault's RESUME.md have changed this session and carry today's date. Results go to the repo the work is for, not to the vault RESUME (obs 0043).
6. **Ship now:** the vault ships with `vault-ship` (the Stop gate refuses to close while the vault has uncommitted changes; ship-session runs it only when this session touched the vault). Every other repo: run `ship-session --now <session_id>` (preview first with `--dry-run <session_id>`). It ships only repos this session touched: it pushes every branch committed this session after a gitleaks scan, opens PRs, turns on auto-merge, and deletes branches **only after MERGED**. Report the results. (The SessionEnd hook runs the same script again as a safety net; it finds nothing left if this step worked.)
7. **Recap:** check `~/.claude/state/recaps/<date>-<sid8>.md` (copied to NvAEx-Recaps by ship-session).
8. Tell the operator in a few lines: shipped, pending, anything that needs their action.
