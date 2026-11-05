#!/usr/bin/env sh
# nvaex-jev-core selftest: runs the real hooks.json commands and scripts in an isolated HOME. Exit 0 only if all behaviour holds.
R="$(cd "$(dirname "$0")/.." && pwd)"; export CLAUDE_PLUGIN_ROOT="$R"
T="$(mktemp -d)"; export HOME="$T"; unset CLAUDE_CONFIG_DIR; fail=0; PRJ="$T/proj"; mkdir -p "$PRJ/.nvaex/rules" "$PRJ/.claude"
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
# health: nudge on 5th call, repeat-edit loop
for i in 1 2 3 4 5; do o=$(run PostToolUse '{"session_id":"s","tool_name":"Bash","tool_input":{}}'); done
has "$o" 'Gate 3 health' && ok "gate3 every 5" || { bad gate3; echo "$o"; }
for i in 1 2 3; do o=$(run PostToolUse '{"session_id":"e","tool_name":"Edit","tool_input":{"file_path":"/x/a.py"}}'); done
has "$o" 'repair loop' && ok "repeat-edit loop flagged" || { bad "repeat edit"; echo "$o"; }
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
rm -rf "$T"; [ $fail = 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"; exit $fail
