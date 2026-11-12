#!/usr/bin/env sh
# nvaex-jev-core selftest: runs the real hooks.json commands and scripts in an isolated HOME. Exit 0 only if all behaviour holds.
R="$(cd "$(dirname "$0")/.." && pwd)"; export CLAUDE_PLUGIN_ROOT="$R"
T="$(mktemp -d)"; export HOME="$T"; unset CLAUDE_CONFIG_DIR TYPESAFE_API_KEY CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY TYPESAFE_BASE_URL TYPESAFE_DEFAULT_MODEL JEV_TIMEOUT JEV_TIERS_JSON JEV_TAXONOMY_CSV; fail=0; PRJ="$T/proj"; mkdir -p "$PRJ/.nvaex/rules" "$PRJ/.claude"
ok(){ echo "PASS $1"; }; bad(){ echo "FAIL $1"; fail=1; }
py(){ python3 -c "$@"; }
cmd(){ py "import json;print(json.load(open('$R/hooks/hooks.json'))['hooks']['$1'][0]['hooks'][0]['command'])"; }
run(){ ev="$1"; printf '%s' "$2" | sh -c "$(cmd $ev)"; }
has(){ echo "$1" | grep -q -- "$2"; }
# structure
py "import json;json.load(open('$R/.claude-plugin/plugin.json'))" && ok manifest || bad manifest
[ "$(py "import json;h=json.load(open('$R/hooks/hooks.json'))['hooks'];print(len(h),all(len(v)==1 for v in h.values()))")" = "5 True" ] && ok "5 events, one entry each" || bad "one entry per event"
py "
import json,sys
h=json.load(open('$R/hooks/hooks.json'))['hooks']
sys.exit(0 if all('killswitch.sh' in e['hooks'][0]['command'].split(';')[0] for v in h.values() for e in v) else 1)" && ok "kill switch runs first in every hook" || bad "killswitch first"
py "
import os,re,sys
b='$R/skills'; bad=[]
for n in os.listdir(b):
    t=open(f'{b}/{n}/SKILL.md').read(); m=re.match(r'---\nname: (.+)\ndescription: (.+)\n---\n',t)
    if not m or m.group(1)!=n or len(t)>5000: bad.append(n)
print(bad); sys.exit(1 if bad else 0)" && ok "skills: name=dir, description, <5KB" || bad skills
for f in $R/licenses/*; do [ -s "$f" ] || bad "license empty $f"; done; ok "licenses present"
# route: time, stage0, router, decisions, contradiction, rules, skip, short dictation, code not flagged
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"Agente, can you implement the router and run the tests then also review the diff\"}")
has "$o" 'Now: ' && has "$o" 'STAGE-0' && has "$o" 'JEV route: L' && ok "route: time+stage0+router" || { bad "route"; echo "$o"; }
# tiers: file valid, ids as given, route line carries the tier, task-type floor applies, fail-open when file missing
py "
import json,sys
T=json.load(open('$R/skills/jev-router/tiers.json'))
ids={v['model'] for v in T['tiers'].values()}
sys.exit(0 if ids=={'claude-haiku-5-5','claude-sonnet-5-5','claude-opus-5-5','claude-fable-5-1'} and all(l['tier'] in T['tiers'] for l in T['levels'].values()) and all(m in T['tiers'] for m in T['task_types_min'].values()) and len(T['levels'])==4 and T['order']==list(T['order']) and set(T['order'])==set(T['tiers']) else 1)" && ok "tiers.json: 4 tiers, ids, L0-L3 and types resolve" || bad tiers.json
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"fix the failing test then also review the diff and debug the crash\"}"); has "$o" 'tier claude-opus-5-5' && ok "route tier: L2 debug -> opus" || { bad "route tier opus"; echo "$o"; }
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"plan the architecture\"}"); has "$o" 'tier claude-fable-5-1' && ok "route tier: plan floor -> fable" || { bad "route tier fable"; echo "$o"; }
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"add tests\"}"); has "$o" 'tier claude-sonnet-5-5' && ok "route tier: L1 build -> sonnet" || { bad "route tier sonnet"; echo "$o"; }
mv "$R/skills/jev-router/tiers.json" "$T/tiers.bak"
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"add tests\"}"); mv "$T/tiers.bak" "$R/skills/jev-router/tiers.json"
has "$o" 'JEV route: L1 | groups' && ! has "$o" 'tier ' && ok "tiers.json missing: route still works" || { bad "tiers missing fail-open"; echo "$o"; }
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"look at \`sever\` in /tmp/stagging.txt and the html page please\"}"); has "$o" STAGE-0 && bad "stage0 false positive on code/path/html" || ok "stage0 ignores code, paths, html"
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"fix bug #skip-enforce\"}"); [ -z "$o" ] && ok skip-enforce || bad skip-enforce
printf '%s\n' '{"decision":"use sqlite for state","rejected":["postgres"],"tags":["database"],"status":"active"}' '{"decision":"old","rejected":["redis"],"tags":["cache"],"status":"superseded"}' > "$PRJ/.nvaex/decisions.jsonl"
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"what database should the state use\"}"); has "$o" 'Decided: use sqlite' && ok "decision injected by tag" || { bad "decision tag"; echo "$o"; }
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"let us move the state to Postgres now\"}"); has "$o" 'CONTRADICTION' && ok "contradiction flagged" || { bad contradiction; echo "$o"; }
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"add a redis cache layer to the service\"}"); has "$o" 'CONTRADICTION' && bad "superseded decision used" || ok "superseded decision ignored"
printf 'keywords: deploy, release\nAlways tag the commit before a release.\n' > "$PRJ/.nvaex/rules/rel.md"
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"prepare the release notes for tomorrow\"}"); has "$o" 'Always tag the commit' && ok "rule selected by keyword" || { bad "rule select"; echo "$o"; }
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"write a haiku about spring\"}"); has "$o" 'Always tag' && bad "unrelated rule injected" || ok "unrelated rule not injected"
# skill gate: nudge for listed skill, silent for others, never blocks
echo '{"mode":"confirm","blocked":["brainstorming"]}' > "$PRJ/.claude/skill-gate.json"
o=$(run PreToolUse "{\"cwd\":\"$PRJ\",\"tool_name\":\"Skill\",\"tool_input\":{\"skill\":\"brainstorming\"}}"); has "$o" 'confirm list' && ! has "$o" '"decision"\|"deny"' && ok "gate nudges, does not block" || { bad gate; echo "$o"; }
o=$(run PreToolUse "{\"cwd\":\"$PRJ\",\"tool_name\":\"Skill\",\"tool_input\":{\"skill\":\"other\"}}"); [ -z "$o" ] && ok "gate silent for unlisted" || bad "gate unlisted"
# health: speaks only on a real repeat; the repair loop is said once, on the edit that makes it 3
for i in 1 2 3 4 5; do o=$(run PostToolUse "{\"session_id\":\"s\",\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"echo $i\"}}"); [ -n "$o" ] && break; done
[ -z "$o" ] && ok "gate3 silent on 5 different calls" || { bad "gate3 nags"; echo "$o"; }
for i in 1 2 3; do o=$(run PostToolUse '{"session_id":"r","tool_name":"Bash","tool_input":{"command":"ls"}}'); done
has "$o" 'Is a step repeating' && ok "gate3 flags the same call 3 times" || { bad "gate3 repeat"; echo "$o"; }
for i in 1 2 3; do o=$(run PostToolUse '{"session_id":"e","tool_name":"Edit","tool_input":{"file_path":"/x/a.py","old_string":"'$i'"}}'); done
has "$o" 'repair loop' && ok "repeat-edit loop flagged" || { bad "repeat edit"; echo "$o"; }
o=$(run PostToolUse '{"session_id":"e","tool_name":"Read","tool_input":{"file_path":"/x/b.py"}}'); has "$o" 'repair loop' && bad "repair loop repeats on later calls" || ok "repair loop said once, not on later calls"
o=$(run PostToolUseFailure '{"session_id":"h","tool_name":"Bash","tool_input":{"command":"grep -n nothing file.txt"},"error":"Exit code 1"}'); [ -z "$o" ] && ok "no-match grep is not a failure" || { bad "grep exit 1 nudged"; echo "$o"; }
# failure research nudge: once, then debounced; Bash only
o=$(run PostToolUseFailure '{"session_id":"f","tool_name":"Bash","tool_input":{"command":"npm i foo"},"error":"ERESOLVE"}'); has "$o" 'today is 20' && has "$o" 'npm i foo' && ok "failure nudge with date" || { bad "failure nudge"; echo "$o"; }
o=$(run PostToolUseFailure '{"session_id":"f","tool_name":"Bash","tool_input":{"command":"npm i foo"},"error":"ERESOLVE"}'); [ -z "$o" ] && ok "failure nudge debounced" || bad debounce
o=$(run PostToolUseFailure '{"session_id":"g","tool_name":"Read","tool_input":{}}'); [ -z "$o" ] && ok "failure nudge Bash only" || bad "bash only"
# scorecard: transcripts
printf '%s\n' '{"type":"user","message":{"role":"user","content":"hi"}}' '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"/x/tests/test_a.py"}}]}}' > "$T/tr.jsonl"
sc(){ run Stop "{\"transcript_path\":\"$T/tr.jsonl\",\"last_assistant_message\":$(py "import json,sys;print(json.dumps(sys.argv[1]))" "$1")}"; }
o=$(sc "Great question! All tests pass and it is done. Remaining files similar.")
for k in false_success phantom_completion test_modification_to_pass sycophancy silent_truncation; do has "$o" "$k" || { bad "scorecard $k"; echo "$o"; }; done
chk(){ o=$(sc "$2"); has "$o" "$1" && ok "check $1" || { bad "check $1"; echo "$o"; }; }
chk cliffhanger "I changed the parser. Let me know if you'd like me to continue with the tests."
chk fake_recall "As we discussed earlier, the parser is slow."
chk aggregator_hallucination "Based on the agents' results, the plan is sound."
chk silent_worker_success "All 4 workers completed."
chk cherry_pick_rollup "3 of 5 workers succeeded, ship it."
chk honest_eta "This should take about 2 hours."
chk emoji_spam "Done 🎉🎉🎉🎉 yay"
chk anthropomorphization "I genuinely enjoy debugging parsers."
chk fake_stats "73.4% of users prefer the new flow."
chk fake_cite "This is shown in prior work [3] and Smith et al. 2024."
chk roleplay_drift "As an AI assistant, I cannot do that."
chk prompt_restate "You asked me to fix the parser, so I will fix the parser."
chk sandbagging_disguise "I tried to run the build but couldn't."
chk rollback_claim_unproven "I reverted the migration."
chk wrap_up "$(printf 'Here is a long answer. %.0s' 1 2 3 4 5 6 7 8 9 10) Is there anything else I can help with?"
chk credential_leak "key is sk-abcdefghijklmnopqrstuvwxyz1234"
# no false positives on honest messages
printf '%s\n' '{"type":"user","message":{"role":"user","content":"a"}}' '{"type":"user","message":{"role":"user","content":"b"}}' '{"message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"pytest -q"}}]}}' > "$T/tr.jsonl"
o=$(sc "Fixed the off-by-one in parse(). Ran pytest: 3 passed, output above. Source: https://docs.python.org/3/. Optimistic 1h, likely 2h, confidence medium."); [ -z "$o" ] && ok "honest message scores clean" || { bad "false positive"; echo "$o"; }
o=$(sc "Next step: run the migration. Status: partial. Pick one of: a, b."); [ -z "$o" ] && ok "explicit next step is not a cliffhanger" || { bad "cliffhanger allow"; echo "$o"; }
printf '%s\n' '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"/x/tests/test_a.py"}}]}}' > "$T/tr.jsonl"
o=$(sc "Great question! All tests pass and it is done."); has "$o" '"decision"\|"block"' && bad "scorecard blocks" || ok "scorecard non-blocking"
o=$(run Stop '{"stop_hook_active":true,"last_assistant_message":"done"}'); [ -z "$o" ] && ok "stop_hook_active skipped" || bad "stop_hook_active"
# kill switches
touch "$T/.nvaex-hooks-off"
o=$(sc "done, all tests pass"); [ -z "$o" ] && ok "global killswitch" || bad "global killswitch"
rm "$T/.nvaex-hooks-off"; mkdir -p "$T/.claude/state/off"; touch "$T/.claude/state/off/nvaex-jev-core.route"
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"implement and review a long thing please\"}"); [ -z "$o" ] && ok "per-hook killswitch" || bad "per-hook killswitch"
rm "$T/.claude/state/off/nvaex-jev-core.route"; touch "$T/.claude/state/off/nvaex-jev-core"
o=$(run UserPromptSubmit "{\"cwd\":\"$PRJ\",\"prompt\":\"implement and review a long thing please\"}"); [ -z "$o" ] && ok "per-package killswitch" || bad "package killswitch"
rm "$T/.claude/state/off/nvaex-jev-core"
# backlog roundtrip
B="python3 $R/scripts/backlog.py"; export NVAEX_BACKLOG="$T/bl.jsonl"
a=$($B add "Write the parser" -p H); b=$($B add "Test the parser" --after $a); c=$($B add "Document it" -p L)
[ "$($B next | cut -c1-30)" = "#1 H open    Write the parser" ] && ok "backlog next = unblocked highest" || { bad "backlog next"; $B next; }
$B list | grep -q 'waiting' && ok "blocked task marked waiting" || bad waiting
$B start $a >/dev/null; $B done $a >/dev/null; $B next | grep -q 'Test the parser' && ok "dependency released after done" || bad "dep release"
$B block $c "needs api key" >/dev/null; $B handoff | grep -q 'BLOCKED' && $B handoff | grep -q 'needs api key' && $B handoff | grep -q 'DONE' && ok "handoff groups states" || bad handoff
$B add "$(printf 'x%.0s' $(seq 1 250))" >/dev/null 2>&1 && bad "long task accepted" || ok "task over 200 chars rejected"
# peers: live pid listed, dead pid dropped
mkdir -p "$T/.claude/sessions"
echo "{\"pid\":$$,\"name\":\"alive-one\",\"status\":\"idle\",\"cwd\":\"/x\",\"updatedAt\":$(date +%s)000}" > "$T/.claude/sessions/1.json"
echo '{"pid":999999,"name":"dead-one","status":"idle","cwd":"/y"}' > "$T/.claude/sessions/2.json"
o=$(python3 "$R/scripts/peers.py"); has "$o" alive-one && ! has "$o" dead-one && has "$o" '1 live' && ok "peers lists live only" || { bad peers; echo "$o"; }
# ---- routing: FAKE TypeSafe server (tests/fake_typesafe.py). Real hook command, real client, real sockets; only the far end is fake.
Q(){ py "import json,sys;print(json.dumps({'cwd':'$PRJ','prompt':sys.argv[1]}))" "$1"; }
python3 "$R/tests/fake_typesafe.py" "$T/fake.port" "$T/fake.log" & FP=$!
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do [ -s "$T/fake.port" ] && break; sleep 0.1; done
U="http://127.0.0.1:$(cat "$T/fake.port")"
K=fake-test-key
jev(){ ( export JEV_SKILLS_INDEX="${JEV_SKILLS_INDEX-$T/no-index}" TYPESAFE_API_KEY="$K" TYPESAFE_BASE_URL="$U/$1" JEV_TIMEOUT="${3:-2}"; run UserPromptSubmit "$(Q "$2")" ); }
fb(){ o=$(jev "$1" "write a haiku about spring" "$3"); has "$o" "via local-fallback ($2)" && has "$o" 'JEV route: L' && ok "FAKE $1 -> local-fallback ($2)" || { bad "fallback $1"; echo "$o"; }; }
o=$(run UserPromptSubmit "$(Q 'add tests')"); has "$o" 'via local-fallback (no-key)' && ok "no key -> local-fallback, stated" || { bad "no key"; echo "$o"; }
o=$(run UserPromptSubmit "$(Q 'hello there')"); has "$o" 'no group matched' && has "$o" 'via local-fallback (no-key)' && ok "no group: fallback still stated" || { bad "no group line"; echo "$o"; }
o=$(jev ok "write a haiku about spring")
has "$o" 'JEV route: L2 | tier claude-fable-5-1 | groups review/plan | try verify-before-done, spec-check, writing-plans, decision-gate' && has "$o" 'via typesafe fake-jev-1.0 conf 0.90/0.90' && ok "FAKE ok: level and groups come from Jev, not the keywords" || { bad "jev ok"; echo "$o"; }
has "$o" "$K" && bad "key in hook output" || ok "key not in hook output"
o=$(jev many "write a haiku about spring"); has "$o" 'groups review/plan/debug/memory/wiki |' && has "$o" 'corpus-verify' && ok "FAKE five groups: no cap on groups or skills" || { bad "caps"; echo "$o"; }
py "import json;json.dump({'skills':[{'id':'s%03d'%i,'purpose':'skill %d'%i} for i in range(300)]},open('$T/idx.json','w'))"
: > "$T/fake.log"; o=$(JEV_SKILLS_INDEX="$T/idx.json" jev ok "write a haiku about spring"); has "$o" 'try s000, s240, s001, s241 ' || has "$o" 'try s000, s240, s001, s241|' ; has "$o" 's000' && has "$o" 's240' && ! has "$o" 's002' && py "import json;q=json.loads(json.loads(open('$T/fake.log').readline())['body'])['questions'];assert sorted(k for k in q if k.startswith('skill_'))==['skill_0','skill_1'] and len(q['skill_0']['criteria'])==240" && ok "FAKE 300-skill roster: Jev reads all of it in one request, picks come from the index" || { bad "roster"; echo "$o"; }
o=$(jev risky "write a haiku about spring"); has "$o" 'JEV route: L3' && ok "FAKE mode L2 with 40% on L3 holds L3" || { bad "L3 risk"; echo "$o"; }
o=$(jev http401 "write a haiku about spring"); has "$o" 'CONFIG FAULT' && ok "FAKE 401 flagged as a config fault, not Jev unsure" || { bad "config fault"; echo "$o"; }
o=$(jev http500 "write a haiku about spring"); ! has "$o" 'CONFIG FAULT' && ok "FAKE 500 is not a config fault" || bad "500 flagged"
o=$(jev busy "write a haiku about spring"); has "$o" 'local-fallback (http-429)' && o=$(jev ok "write a haiku about spring"); has "$o" 'local-fallback (backoff)' && sleep 1 && o=$(jev ok "write a haiku about spring"); has "$o" 'via typesafe' && grep -q req-fake-1 "$T/.claude/state/nvaex-jev-core/route.jsonl" && ok "FAKE Retry-After honored, then Jev used again; request id logged" || { bad "backoff"; echo "$o"; }
o=$(jev low "write a haiku about spring"); has "$o" 'conf 0.40/0.30 LOW: check it' && ok "FAKE low confidence flagged" || { bad "low conf"; echo "$o"; }
o=$(jev none "write a haiku about spring"); has "$o" 'JEV route: L0' && has "$o" 'no group matched' && has "$o" 'via typesafe' && ok "FAKE companion Noul says nothing fits -> no group" || { bad "none"; echo "$o"; }
o=$(jev none "force push the rewritten branch"); has "$o" 'JEV route: L3' && has "$o" 'via typesafe' && ok "FAKE Jev says L0, code floor holds L3 on force push" || { bad "floor"; echo "$o"; }
: > "$T/fake.log"
o=$(jev ok 'review my key sk-abcdefghijklmnopqrstuvwxyz1234 with password=hunter2hunter2 token: ghp_abcdefghijklmnop1234 TYPESAFE_API_KEY=plainvalue1 mail jo.doe@example.com at postgres://bob:pw9x@db.example.com/x Bearer abcdefgh12345678') # gitleaks:allow (fake test string)
for s in sk-abcdef hunter2 ghp_abc plainvalue1 jo.doe pw9x abcdefgh12345678; do grep -q -- "$s" "$T/fake.log" && { bad "secret left the phone: $s"; }; done
grep -q 'REDACTED' "$T/fake.log" && grep -q 'review my key' "$T/fake.log" && ok "FAKE redacted before sending, rest of prompt kept" || bad "redaction"
: > "$T/fake.log"; o=$(jev ok "$(py "print('start '+'word '*4000+'finish')")"); [ "$(py "import json;print(len(json.loads(json.loads(open('$T/fake.log').readline())['body'])['state']['task'])<8100)")" = True ] && grep -q 'finish' "$T/fake.log" && ok "FAKE long prompt cut to head and tail" || bad truncate
for c in 401 403 422 429 500 529; do fb http$c http-$c; done
fb garbage bad-response; fb unknown bad-response
: > "$T/fake.log"; fb redirect http-302; [ "$(grep -c '"path"' "$T/fake.log")" = 1 ] && ok "FAKE redirect not followed: key sent once" || bad "redirect followed"
S0=$(date +%s); fb slow timeout 0.5; S1=$(date +%s); [ $((S1-S0)) -le 2 ] && ok "FAKE timeout: hook back in $((S1-S0))s (fake sleeps 4)" || bad "hook waited $((S1-S0))s"
o=$( ( export TYPESAFE_API_KEY=$K TYPESAFE_BASE_URL=http://127.0.0.1:9; run UserPromptSubmit "$(Q 'add tests')" ) ); has "$o" 'local-fallback (network)' && ok "connection refused -> local-fallback (network)" || { bad network; echo "$o"; }
o=$( ( export TYPESAFE_API_KEY=$K TYPESAFE_BASE_URL=http://example.com; run UserPromptSubmit "$(Q 'add tests')" ) ); has "$o" 'local-fallback (bad-base-url)' && ok "plain http off-device refused" || { bad "http refused"; echo "$o"; }
o=$( ( export TYPESAFE_API_KEY="abc def-LEAK"; run UserPromptSubmit "$(Q 'add tests')" ) ); has "$o" 'local-fallback (bad-key-format)' && ! has "$o" LEAK && ok "malformed key: reason only, key not quoted" || { bad "bad key"; echo "$o"; }
o=$( ( export CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY=$K TYPESAFE_BASE_URL="$U/ok"; run UserPromptSubmit "$(Q 'add tests')" ) ); has "$o" 'via typesafe' && ok "FAKE key from plugin config works" || { bad "plugin option key"; echo "$o"; }
o=$( ( export CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY='${user_config.typesafe_api_key}'; run UserPromptSubmit "$(Q 'add tests')" ) ); has "$o" 'local-fallback (no-key)' && ok "unfilled placeholder is no key" || { bad placeholder; echo "$o"; }
mkdir -p "$T/.claude/state/off"; touch "$T/.claude/state/off/nvaex-jev-core.typesafe"; : > "$T/fake.log"
o=$(jev ok "write a haiku about spring"); rm "$T/.claude/state/off/nvaex-jev-core.typesafe"; has "$o" 'local-fallback (typesafe-off)' && [ ! -s "$T/fake.log" ] && ok "off switch: nothing sent, stated" || { bad "off switch"; echo "$o"; }
L="$T/.claude/state/nvaex-jev-core/route.jsonl"; [ -s "$L" ] && ! grep -q 'haiku' "$L" && py "import json;r=[json.loads(x) for x in open('$L')];assert {x['source'] for x in r}=={'typesafe','local-fallback'}" && ok "decision log has source, no prompt text" || bad "route log"
# one router: hook and MCP tool agree, one tiers file, server has no rules of its own
M(){ py "import json,sys;print(json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'jev.route_task','arguments':{'task':sys.argv[1]}}}))" "$1" | python3 -I "$2" | py "import json,sys;r=json.loads(json.loads(sys.stdin.read())['result']['content'][0]['text']);print(r['source'],r['error'],r['level'],'/'.join(r['groups']),r['tier']['model'])"; }
SV="$R/mcp/jev-rea-mcp/server.py"
o=$( ( export TYPESAFE_API_KEY=$K TYPESAFE_BASE_URL="$U/ok"; M "write a haiku about spring" "$SV" ) ); [ "$o" = "typesafe None 2 review/plan claude-fable-5-1" ] && ok "FAKE MCP route_task gives the hook's answer" || { bad "mcp jev"; echo "$o"; }
o=$(M "fix the failing test then also review the diff" "$SV"); h=$(run UserPromptSubmit "$(Q 'fix the failing test then also review the diff')"); has "$h" "$(echo "$o" | awk '{print "JEV route: L"$3" | tier "$5" | groups "$4}')" && has "$o" 'local-fallback no-key' && ok "fallback: MCP and hook agree" || { bad "mcp fallback"; echo "$o"; echo "$h"; }
[ "$(find "$R" -name tiers.json | wc -l | tr -d ' ')" = 1 ] && ok "one tiers.json" || bad "tiers copies"
grep -qE 'L3 = |GROUPS = |def route\(|def tier_for|def taxonomy_match' "$SV" "$R/scripts/route.py" && bad "routing logic outside jev_route.py" || ok "routing logic only in jev_route.py"
kill $FP 2>/dev/null
# package alone: copied out of the tree (no sibling packages), .mcp.json command run as written, hook run, 3 tools listed
A="$T/alone/nvaex-jev-core"; mkdir -p "$T/alone"; cp -r "$R" "$A"
o=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | py "
import json,subprocess,sys
m=json.load(open('$A/.mcp.json'))['mcpServers']['jev-rea-mcp']
sub=lambda s:s.replace('\${CLAUDE_PLUGIN_ROOT}','$A')
r=subprocess.run([m['command']]+[sub(a) for a in m['args']],stdin=sys.stdin,capture_output=True,text=True)
print(len(json.loads(r.stdout)['result']['tools']))"); [ "$o" = 3 ] && ok "package alone: .mcp.json starts jev-rea-mcp, 3 tools" || { bad "mcp alone"; echo "$o"; }
o=$(echo "{\"cwd\":\"$PRJ\",\"prompt\":\"add tests\"}" | CLAUDE_PLUGIN_ROOT="$A" python3 "$A/scripts/route.py"); has "$o" 'JEV route: L1' && ok "package alone: hook routes" || { bad "hook alone"; echo "$o"; }
# groups.json names only skills that exist; the check itself fails on a bad name
F="$(cd "$R/../.." && pwd)"
if [ -d "$F/plugins" ]; then
  o=$(python3 "$R/tests/check_groups.py" "$R/skills/jev-router/groups.json" "$F") && ok "groups.json skills all exist: $o" || { bad "groups.json: $o"; }
  py "import json;g=json.load(open('$R/skills/jev-router/groups.json'));g['groups']['device']['skills'].append('no-such-skill');json.dump(g,open('$T/g.json','w'))"
  python3 "$R/tests/check_groups.py" "$T/g.json" "$F" >/dev/null && bad "check_groups passed a bad name" || ok "check_groups fails on a missing skill"
else echo "SKIP groups.json check (not inside the NovAExopia plugins tree)"; fi
# jev-rea-mcp server selftest
sh "$R/mcp/jev-rea-mcp/tests/selftest.sh" > "$T/mcp.out" 2>&1 && ok "jev-rea-mcp selftest: $(grep -c '^PASS' "$T/mcp.out") checks" || { bad "jev-rea-mcp selftest"; cat "$T/mcp.out"; }
rm -rf "$T"; [ $fail = 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"; exit $fail
