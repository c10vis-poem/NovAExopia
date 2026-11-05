#!/usr/bin/env bash
# Stop gate for corpus-ingest workers. Logic vendored from ~/.claude/agents/hooks/worker-stop-gate.sh.
# Blocks while the worker's progress file has unchecked plan steps and an empty "## Blocked".
# Never blocks twice in a row (stop_hook_active). Fails open on any parse error.
in=$(cat)
[ "$(printf '%s' "$in" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ] && exit 0
at=$(printf '%s' "$in" | jq -r '.agent_type // empty' 2>/dev/null)
case "$at" in ""|*corpus-ingest*) ;; *) exit 0 ;; esac
tp=$(printf '%s' "$in" | jq -r '.agent_transcript_path // .transcript_path // empty' 2>/dev/null)
[ -f "$tp" ] || exit 0
OV="Override: touch ~/.claude/state/off/nvaex-wiki-admin.stop-gate (or ~/.nvaex-hooks-off for all hooks). Revoke: delete that file. The operator's direct instructions override this gate."
pf=$(grep -oE '/[^" ]*/session-work/[0-9-]+/agent-[A-Za-z0-9._-]+\.md' "$tp" | head -1)
if [ -z "$pf" ] || [ ! -f "$pf" ]; then
  jq -n --arg o "$OV" '{decision:"block",reason:("You have no progress file. Create ~/.claude/session-work/<date>/agent-<topic>.md with ## Plan (checkboxes), ## Last action, ## Findings, ## Blocked, fill it from what you did, then finish. " + $o)}'
  exit 0
fi
open=$(grep -cE '^\s*- \[ \]' "$pf")
blocked=$(awk '/^## Blocked/{f=1;next} /^## /{f=0} f && NF' "$pf" | grep -vciE '^\s*(-\s*)?(none|nothing|n/a)\.?\s*$')
if [ "${open:-0}" -gt 0 ] && [ "${blocked:-0}" -eq 0 ]; then
  steps=$(grep -E '^\s*- \[ \]' "$pf" | head -5 | sed 's/^\s*- \[ \] //' | paste -sd';' -)
  jq -n --arg r "Your plan in $pf still has $open unchecked step(s): $steps. Do them, or write under ## Blocked exactly why each can't be done, then stop. $OV" '{decision:"block",reason:$r}'
fi
exit 0
