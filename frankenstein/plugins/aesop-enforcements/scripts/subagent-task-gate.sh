#!/usr/bin/env bash
# Rule 10, PreToolUse for subagents only: write to task as you work. A subagent that can write must have its
# progress file before its 4th tool call, and must update it at least every 6 tool calls or 5 minutes.
# Writing the progress file itself (Write/Edit on it, or a Bash command naming it) always passes. Main session: no effect.
in=$(cat)
. "$(dirname "$(realpath "$0")")/lib/subagent.sh"
[ -n "$sa_aid" ] || exit 0
sa_exempt && exit 0
[ -f "$sa_tp" ] || exit 0
tool=$(jq -r '.tool_name // ""' <<<"$in"); target=$(jq -r '.tool_input.file_path // .tool_input.command // ""' <<<"$in")
case $tool in ToolSearch|TodoWrite) exit 0 ;; esac
[[ $target == *session-work/*agent-*.md* ]] && exit 0
calls=$(jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .name' "$sa_tp" 2>/dev/null | grep -c .)
if [ -z "$sa_pf" ] || [ ! -f "$sa_pf" ]; then
  [ "${calls:-0}" -lt 3 ] && exit 0
  echo "BLOCKED (subagent-task-gate, rule 10): write to task first. $SA_HOW Write it now (the plan before the work), then continue. OVERRIDE: the operator's direct instruction. REVOKE: the operator runs gate off task-gate." >&2
  exit 2
fi
pm=$(stat -c %Y "$sa_pf"); now=$(date +%s)
since=$(jq -r --argjson t "$pm" 'select(.type=="assistant") | select((.timestamp // "" | sub("\\.[0-9]+Z$";"Z") | fromdateiso8601? // 0) > $t) | .message.content[]? | select(.type=="tool_use") | .name' "$sa_tp" 2>/dev/null | grep -c .)
if [ "${since:-0}" -ge 6 ] || { [ $((now - pm)) -gt 300 ] && [ "${since:-0}" -ge 2 ]; }; then
  echo "BLOCKED (subagent-task-gate, rule 10): $sa_pf not updated for $since tool calls / $(( (now - pm) / 60 )) min. Tick the steps done, update ## Last action (timestamp, what you are doing) and ## Findings, then continue. OVERRIDE: the operator's direct instruction. REVOKE: the operator runs gate off task-gate." >&2
  exit 2
fi
exit 0
