#!/usr/bin/env bash
# Rule 9, the one session log. Before a call: the action (change-log). After: repos, files and git actions
# (session-ledger), and unfinished items carried from earlier sessions when RESUME is Read (carryover).
# PreCompact and SessionEnd: the scratchpad is saved and this session's unfinished items recorded.
# ship-session folds the log into the recap that goes to NvAEx-Recaps. Never blocks.
. "$(dirname "$(realpath "$0")")/lib/parts.sh"
case $event:$tool in
  PreToolUse:*) run_parts change-log ;;
  PostToolUse:Read) run_parts carryover ;;
  PostToolUse:*) run_parts session-ledger ;;
  PreCompact:*) run_parts archive-scratchpad ;;
  SessionEnd:*) run_parts archive-scratchpad carryover ;;
esac
