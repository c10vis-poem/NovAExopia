# Contract A recon (session aa762319, 2026-11-11)

## Where the work happens
- Live plugin: `~/repos/Aesop-Xi/plugins/aesops-enforcements/`, on branch `rebuild-2026-11-10` with **uncommitted**
  edits to RULES.md, lib/contract.py, lib/hook.py, plus eight `.bak` files (git status, 11:56). The live hooks run
  this uncommitted code.
- Worktree: `~/repos/Aesop-Xi-contract-a`, branch `contract-a/enforcements` from HEAD 5620fa7, with the live
  uncommitted plugin files brought in from a `git stash create` snapshot (48a678d; `git diff --stat` against it:
  empty). The `.bak` files are not tracked and were not copied.
- Plugin files (git ls-files): `.claude-plugin/plugin.json`, `RULES.md`, `git-hooks/{pre-commit,pre-push,scan}`,
  `hooks/hooks.json`, `lib/contract.py`, `lib/hook.py`, `salary/{ACTIVE,github.md,opening.md}`,
  `tests/test_contract.py`.

## The last contract session
- Session `7c7b204b-5aa2-42fd-83ce-3b2a3dfc5c18`, launched from NovAExopia-main, 01:49 to 09:08 PST
  (transcript 23 MB). Contracts signed: A, B, B2, B3, B4, C, C2. No handoff or RESUME update was written for it:
  RESUME.md still points at the 2026-11-10 handoff, which is why this session could not find it. Its owner copies
  are in Recaps `contracts/2026-11-11/7c7b204b-*.md`.
- Gate events in its transcript (hook and tool output only, scanned with `recon_items.py`):
  - 314 stop blocks carrying **14,156 listed items** (158 distinct). Each block listed every unmet line of every
    task: at task 2 it already listed task 5, 6 and 7 reads. This is the "mid-task interjection".
  - 119 "Last turn ended with requirements unmet" notices.
  - 56 quiz asks, 12 quote misses.
  - Most repeated items: `task 2: REQUIRE Quiz: 0 of 10 passed` (747 times); one task-7 read (730);
    `REQUIRE Server: claude_ai_Supabase` (234, never met).
  - Denies: protected-files-changed freeze (5: the plugin was edited mid-session), `~/.claude/state` touched (3),
    "belongs to task 2" (3, on the unmeetable Server line), Reads denied under a contract (4: its own notes.md and
    RULES.md).
- False alarms found:
  1. `said RULES.md was read, but no read of it is in the ledger`: the agent read Aesop-Xi's RULES.md; the check
     resolved the bare name against the contract root (NovAExopia) and found a different file.
  2. `REQUIRE Server: <name>` can never be met, and `SCOPE Server:` never matches: the hook takes the server name
     from the hook input's `mcp_server.name`, while contracts are written with the tool-name segment
     (`claude_ai_Supabase`, `plugin_nvaex-memory_dumbass-memory`). This session's breach 1 is the same bug.
  3. Under a contract, Read of the session's own notes.md is denied unless a SCOPE covers it.
  4. Code-level (contract.py): an edit to a file voids every read of it (whole-file sha); lines over 2000 chars
     come back truncated and never match; "read `X`" in a question counts as a claim; non-text reads record
     nothing.

## Other gate defects found while working
- Bash SCOPE refuses any command containing `| ; & < > ` or `$(` anywhere, even inside a quoted regex (this
  session's breach 2: a grep pattern with `|`).
- `git -C <dir> push` does not start with `git push`, so the GitHub salary's `after: #push` hold never applies to
  it; a contract with `SCOPE Bash: git` would let it through. Same for `gh -R ... pr merge`.
- Protection compares literal path strings: `$HOME/.claude/state`, `~/.claude/../.claude/state` or a path built
  in a script are not caught.
- `<root>/.contract/opening.md` replaces the opening and is writable by the agent.
- A protected-file change freezes the session even when the owner made it (5 denies last session).

## Injections that are not the contract plugin
- "Gate 3 health" and "Gate 3 repair loop": `plugins/nvaex-jev-core/scripts/health.py`. The repair-loop line
  fires on every later call once any file reaches 3 edits (line 21 keeps matching `c % 3 == 0`), so one file
  edited three times repeats the line for the rest of the session.
- "research-on-failure" PostToolUseFailure note: fires on any non-zero exit, including a grep with no match.
- "JEV route" UserPromptSubmit line: nvaex-jev-core router; local fallback, no TypeSafe key in the hook's
  environment; lists up to 19 skills.
