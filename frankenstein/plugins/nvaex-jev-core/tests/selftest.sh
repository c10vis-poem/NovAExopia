#!/usr/bin/env sh
# nvaex-jev-core selftest: runs each hook command from hooks.json for real, isolated HOME.
R="$(cd "$(dirname "$0")/.." && pwd)"; export CLAUDE_PLUGIN_ROOT="$R"
T="$(mktemp -d)"; export HOME="$T"; fail=0
ok(){ echo "PASS $1"; }; bad(){ echo "FAIL $1"; fail=1; }
cmd(){ python3 -c "import json,sys;print(json.load(open('$R/hooks/hooks.json'))['hooks']['$1'][0]['hooks'][0]['command'])"; }
run(){ ev="$1"; shift; printf '%s' "$1" | sh -c "$(cmd $ev)"; }
python3 -c "import json;json.load(open('$R/.claude-plugin/plugin.json'))" && ok manifest || bad manifest
[ "$(python3 -c "import json;print(len(json.load(open('$R/hooks/hooks.json'))['hooks']))")" = 3 ] && ok "one entry per event" || bad events
grep -q '^name: drunken-master' "$R/skills/drunken-master/SKILL.md" && ok drunken-master || bad drunken-master
# Stage 0 + Stage 1
o=$(run UserPromptSubmit '{"prompt":"Agente, can you implement the router and run the tests then also review the diff"}')
echo "$o" | grep -q 'STAGE-0' && echo "$o" | grep -q 'JEV route: L' && ok "route+stage0" || { bad "route+stage0"; echo "$o"; }
o=$(run UserPromptSubmit '{"prompt":"fix bug #skip-enforce"}'); [ -z "$o" ] && ok skip-enforce || bad skip-enforce
# Gate 3: 5th call nudges
for i in 1 2 3 4 5; do o=$(run PostToolUse '{"session_id":"s","tool_name":"Bash","tool_input":{}}'); done
echo "$o" | grep -q 'Gate 3 health' && ok "gate3 every 5" || { bad gate3; echo "$o"; }
# Scorecard: transcript with a test edit and no Bash, claim of success
printf '%s\n' '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"/x/tests/test_a.py"}}]}}' > "$T/tr.jsonl"
o=$(run Stop "{\"transcript_path\":\"$T/tr.jsonl\",\"last_assistant_message\":\"Great question! All tests pass and it is done. Remaining files similar.\"}")
for k in false_success phantom_completion test_modification_to_pass sycophancy silent_truncation; do echo "$o" | grep -q "$k" || { bad "scorecard $k"; echo "$o"; }; done
echo "$o" | grep -q '"decision"' && bad "scorecard must not block" || ok "scorecard non-blocking"
o=$(run Stop '{"last_assistant_message":"Fixed. Ran pytest: 3 passed."}'); ok "clean stop exits 0"
# Kill switches
touch "$T/.nvaex-hooks-off"
o=$(run Stop "{\"transcript_path\":\"$T/tr.jsonl\",\"last_assistant_message\":\"done, all tests pass\"}"); [ -z "$o" ] && ok "global killswitch" || bad "global killswitch"
rm "$T/.nvaex-hooks-off"; mkdir -p "$T/.claude/state/off"; touch "$T/.claude/state/off/nvaex-jev-core.route"
o=$(run UserPromptSubmit '{"prompt":"implement and review a long thing please"}'); [ -z "$o" ] && ok "per-hook killswitch" || bad "per-hook killswitch"
rm -rf "$T"; [ $fail = 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"; exit $fail
