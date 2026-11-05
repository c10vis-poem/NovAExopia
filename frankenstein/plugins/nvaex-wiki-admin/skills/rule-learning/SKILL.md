---
name: rule-learning
description: Capture a behavioural rule from a user correction, with the user's approval, as a staged skill. Use when the user corrected your approach and the correction generalizes to a class of future requests ("no, search the web first when I ask for the latest version"). Also on "remember this rule" / "save this as a skill". Never saves without an explicit yes.
---

# Rule learning (approval-gated)

Default is NOT proposing. Propose only when all hold:
1. **Generalizable**: the correction covers a class of requests, not this one (a port number is a note, not a rule).
2. **Clear trigger**: you can state the firing condition in one sentence; that sentence is the `description`.
3. **Not already covered**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rule_propose.py list` and the user's CLAUDE.md/AGENTS.md.

## Steps
1. Draft `SKILL.md`: frontmatter `name` (kebab-case), `description` (the trigger), `kind: rule`; sections `When this fires` (2-3 phrases as the user talks), `Rule` (imperative, 1-3 sentences), `Why (origin)` (dated: asked / went wrong / corrected), `Example` (before/after).
2. **Ask the user** (AskUserQuestion) to approve the exact text. No yes, no save.
3. Stage: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rule_propose.py propose --name N --hint "how to tell it worked next time (20+ chars)" < SKILL.md`. It scans for injection/exfil text and refuses unsafe or malformed drafts. Staged rules are inert.
4. Only `/rules approve N` (the user) moves it to active. `reject` and `demote` are one command each; nothing is deleted, files move to `.rejected/`.

State lives in `${NVAEX_RULES_DIR:-~/.claude/nvaex-rules}`, never in the vault.
