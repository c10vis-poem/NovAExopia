#!/usr/bin/env sh
# Contract A3 task 2 (2026-11-12): Gate 3 and the scorecard, through the real hooks.json commands in an isolated
# HOME. Exit 0 only if every case holds. Run: sh tests/test_a3.sh
R="$(cd "$(dirname "$0")/.." && pwd)"; export CLAUDE_PLUGIN_ROOT="$R"
T="$(mktemp -d)"; export HOME="$T"; fail=0
ok(){ echo "PASS $1"; }; bad(){ echo "FAIL $1"; fail=1; }
cmd(){ python3 -c "import json;print(json.load(open('$R/hooks/hooks.json'))['hooks']['$1'][0]['hooks'][0]['command'])"; }
run(){ printf '%s' "$2" | sh -c "$(cmd $1)"; }
has(){ echo "$1" | grep -q -- "$2"; }

# Gate 3 edit count: a Write and two different Edits with no failure is ordinary work (the 16:12 false alarm)
a=$(run PostToolUse '{"session_id":"w","tool_name":"Write","tool_input":{"file_path":"/x/n.md","content":"a"}}')
for i in 1 2; do a="$a$(run PostToolUse '{"session_id":"w","tool_name":"Edit","tool_input":{"file_path":"/x/n.md","old_string":"'$i'"}}')"; done
has "$a" 'repair loop' && { bad "edits with no failure flagged as a repair loop"; echo "$a"; } || ok "edits with no failure: silent"

# a real repair loop: fail, edit, three times
for i in 1 2 3; do run PostToolUseFailure '{"session_id":"e","tool_name":"Bash","tool_input":{"command":"pytest -q"},"error":"Exit code 1"}' >/dev/null
  o=$(run PostToolUse '{"session_id":"e","tool_name":"Edit","tool_input":{"file_path":"/x/a.py","old_string":"'$i'"}}'); done
has "$o" 'repair loop' && ok "fail-edit x3 flagged" || { bad "fail-edit x3 not flagged"; echo "$o"; }

# failed Edits count as failures too (PostToolUseFailure no longer Bash-only)
for i in 1 2 3; do run PostToolUseFailure '{"session_id":"m","tool_name":"Edit","tool_input":{"file_path":"/x/c.py"},"error":"String to replace not found"}' >/dev/null
  o=$(run PostToolUse '{"session_id":"m","tool_name":"Edit","tool_input":{"file_path":"/x/c.py","old_string":"'$i'"}}'); done
has "$o" 'repair loop' && ok "failed-Edit loop flagged" || { bad "failed-Edit loop not flagged"; echo "$o"; }

# Gate 3 repeat check: the same text written to four files is four calls, not one repeated (the 17:16 false alarm)
B="$(python3 -c "print('x'*400)")"; a=""
for f in claude agy dsh hermes; do a="$a$(run PostToolUse "{\"session_id\":\"s4\",\"tool_name\":\"Write\",\"tool_input\":{\"content\":\"$B\",\"file_path\":\"/x/shims/$f\"}}")"; done
has "$a" 'Is a step repeating' && { bad "four files read as one repeated call"; echo "$a"; } || ok "same text, four files: silent"
for i in 1 2 3; do o=$(run PostToolUse '{"session_id":"r","tool_name":"Bash","tool_input":{"command":"ls"}}'); done
has "$o" 'Is a step repeating' && ok "same call 3 times flagged" || { bad "same call 3 times not flagged"; echo "$o"; }

# scorecard: a test edited and then run is not "modified to pass"; edited and never run is, and the file is named
sc(){ run Stop "{\"transcript_path\":\"$T/tr.jsonl\",\"last_assistant_message\":\"$1\"}"; }
printf '%s\n' '{"type":"user","message":{"role":"user","content":"a"}}' \
  '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"/x/tests/test_x.py"}}]}}' \
  '{"message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"python3 -I /x/tests/test_x.py"}}]}}' > "$T/tr.jsonl"
o=$(sc "Ran it: 9 tests pass, output above.")
has "$o" 'test_modification_to_pass' && { bad "flagged although the test ran after the edit"; echo "$o"; } || ok "edit then run: not flagged"
printf '%s\n' '{"type":"user","message":{"role":"user","content":"a"}}' \
  '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"/x/tests/test_x.py"}}]}}' > "$T/tr.jsonl"
o=$(sc "It passes now.")
has "$o" 'test_modification_to_pass (test_x.py edited' && ok "edit without a run: flagged, file named" || { bad "not flagged or file not named"; echo "$o"; }

rm -rf "$T"; [ $fail = 0 ] && echo "TEST_A3 PASS" || echo "TEST_A3 FAIL"; exit $fail
