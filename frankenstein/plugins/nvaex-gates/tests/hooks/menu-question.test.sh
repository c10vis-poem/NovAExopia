#!/usr/bin/env bash
S=$(cd "$(dirname "$0")/../../scripts" && pwd); T=$(mktemp -d); export HOME=$T
pass=0; fail=0
ok(){ if [ "$1" = "$2" ]; then pass=$((pass+1)); echo "PASS $3"; else fail=$((fail+1)); echo "FAIL $3 (got $1 want $2)"; fi; }
M(){ jq -cn --argjson q "$1" '{tool_name:"AskUserQuestion",tool_input:{questions:$q}}' | bash "$S/menu-gate.sh" 2>/dev/null; echo $?; }
Q(){ jq -cn --arg m "$(printf "$1")" --argjson a "${2:-false}" '{last_assistant_message:$m,stop_hook_active:$a}' | bash "$S/question-gate.sh" 2>/dev/null; echo $?; }
ok "$(M '[{"question":"Which?","options":[{"label":"A"},{"label":"B"}]}]')" 2 "menu with no write-in -> block"
ok "$(M '[{"question":"Which?","options":[{"label":"A"},{"label":"Write my own answer"}]}]')" 0 "menu with write-in -> pass"
ok "$(M '[{"question":"1","options":[{"label":"Other"}]},{"question":"2","options":[{"label":"A"}]}]')" 2 "second question lacks it -> block"
ok "$(echo 'not json{' | bash "$S/menu-gate.sh" 2>/dev/null; echo $?)" 0 "malformed -> pass"
ok "$(Q 'Done.\n\nWant me to ship it?')" 2 "want me to -> block"
ok "$(Q 'A or B?')" 2 "either/or -> block"
ok "$(Q 'Is that ok?')" 2 "is that ok -> block"
ok "$(Q 'Press 2, or I will keep approving.')" 2 "or I will -> block"
ok "$(Q 'Which package did you mean?')" 0 "open question -> pass"
ok "$(Q 'All set.')" 0 "no question -> pass"
ok "$(Q 'Want me to ship it?' true)" 0 "blocks once only"
J=$(jq -cn '{session_id:"S",hook_event_name:"PreToolUse",cwd:"/",tool_name:"Write",tool_input:{file_path:"/x/new.txt"}}')
bash "$S/session-log.sh" <<<"$J"; ok "$?" 0 "session-log never blocks"
ok "$(grep -c NEW "$T/.claude/state/changes-S.log")" 1 "PreToolUse goes to the action log"
STATE_DIR=$T/s RECAPS_DIR=$T/r bash "$S/session-log.sh" <<<"$(jq -c '.hook_event_name="PostToolUse"' <<<"$J")"
ok "$(grep -c new.txt "$T"/r/*-S.md)" 1 "PostToolUse goes to the recap"
echo "== $pass passed, $fail failed"; rm -rf "$T"; [ "$fail" -eq 0 ]
