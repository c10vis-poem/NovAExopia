# Owner steps: getting the rules-plugin fix live (contract A2, 2026-11-11)

Plain terminal commands (no `!`). Paths:
- OVER THERE = `~/repos/Aesop-Xi`: the live rules plugin runs from this folder (marketplace `aesop-xi` is a
  directory source pointing here). Branch `rebuild-2026-11-10`.
- MY COPY = `~/repos/Aesop-Xi-contract-a`: branch `contract-a/enforcements`, the fix. 39 tests pass
  (`tests/test_contract.py` 15, `tests/test_contract_a.py` 24).

## What the branch holds (4 commits on top of origin/main)
| Commit | What | From |
|---|---|---|
| 98e89e6 | "contract enforcement replaces the old gates (not pushed; owner checks first)" | earlier session |
| 5620fa7 | restore two tracked .pyc files | earlier session |
| e8a55ff | the unsaved edits found in OVER THERE today (RULES.md, contract.py, hook.py) | earlier session, committed today unchanged |
| d58792a | the contract A fixes | this session |

98e89e6 says "owner checks first": pushing this branch pushes it too. Your `#push` approves all four.

## Step 1: make the fix live on this phone now (no push needed)
OVER THERE's unsaved edits are already inside e8a55ff, so set them aside, then fast-forward:

    git -C ~/repos/Aesop-Xi stash push -m pre-contract-a
    git -C ~/repos/Aesop-Xi merge --ff-only contract-a/enforcements

The eight `.bak` files are untracked and stay where they are (delete them by hand when you are done with them).

## Step 2: re-fingerprint the running session(s)
The plugin files changed, so a running session pauses until you do this (its id is in the status line):

    python3 -I ~/repos/Aesop-Xi/plugins/aesops-enforcements/lib/hook.py refingerprint aa762319-f987-4c8e-a8ce-c3d964d9148c

The session then continues by itself (new in this fix); no `#ok` or `#redo` needed.

## Step 3: status bar (optional)
`~/.claude/settings.json` already has a `statusLine` (a synced plugin's `statusline.sh`). Pick one:
- Replace it:

      "statusLine": {"type": "command", "command": "python3 -I /data/data/com.termux/files/home/repos/Aesop-Xi/plugins/aesops-enforcements/lib/statusline.py"}

- Or keep both: ask for a small wrapper script that prints the old line and the contract line (contract B).

## Step 4: push and PR (after `#push` in the session)
The agent runs: `git -C ~/repos/Aesop-Xi-contract-a push -u origin contract-a/enforcements`, then
`gh pr create -R c10vis-poem/Aesop-Xi --base main --head contract-a/enforcements`. Aesop-Xi's branch protection
and CI were not checked yet: if `main` has no required checks, auto-merge would merge at once, so the agent waits
for checks and you merge by hand. Open PR #84 (hooks/safety-net-enable-all, 2026-11-03) is unrelated and untouched.

## Undo
    git -C ~/repos/Aesop-Xi reset --hard 5620fa7
    git -C ~/repos/Aesop-Xi stash apply

(The first puts OVER THERE back on the old commit; the second brings back the unsaved edits.) Then re-fingerprint.

## Found while doing this
- `~/.claude/settings.json` holds an API key in plain text (the TinyFish env line). Move it to nvaex-secrets
  and rotate it. The plugin's secret protection blocks reading `.env`-style files but not keys inside
  settings.json; contract B can close that.
