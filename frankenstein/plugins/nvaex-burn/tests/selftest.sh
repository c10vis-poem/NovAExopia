#!/usr/bin/env bash
# nvaex-burn selftest: runs on device, stdlib only, local webhook receiver, never touches vault or settings.
set -u
R="$(cd "$(dirname "$0")/.." && pwd)"; B="$R/scripts/burn.py"
T="$(mktemp -d)"; trap 'kill $WH 2>/dev/null; rm -rf "$T"' EXIT
export BURN_STATE="$T/state" BURN_QUEUE="$T/queue.md" BURN_USAGE_FILE="$T/usage.json" HOME="$T/home"
mkdir -p "$HOME"; unset BURN_WEBHOOK_URL BURN_USAGE_CMD BURN_PING_CMD
NOW=1800000000; export BURN_NOW=$NOW; fail=0
ok() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1: got '$2' want '$3'"; fail=1; fi; }
mode() { python3 "$B" status | python3 -c 'import sys,json;print(json.load(sys.stdin)["mode"])'; }
usage() { printf '{"capturedAt":%s000,"five_hour":{"used_percentage":%s,"resets_at":%s},"seven_day":{"used_percentage":%s,"resets_at":%s}}' $NOW $1 $((NOW+3600)) $2 $((NOW+$3*3600)) > "$T/usage.json"; }

ok "no usage source -> unknown" "$(mode)" unknown
python3 "$B" tick | grep -q '"ran": \[\]'; ok "unknown burns nothing" $? 0
usage 95 10 100; ok "5h>=90 -> brake" "$(mode)" brake
usage 10 96 100; ok "7d>=95 -> brake" "$(mode)" brake
usage 10 50 100; ok ">72h -> idle" "$(mode)" idle
usage 10 50 60;  ok "60h, 50% left -> burn" "$(mode)" burn
usage 10 80 60;  ok "<25% unused -> idle" "$(mode)" idle

# queue: smoulder job runs at 60h, blaze job does not
printf '%s\n' "- [x] smoulder | j1 | touch $T/ran1" "- [x] blaze | j2 | touch $T/ran2" "- [ ] smoulder | j3 | touch $T/ran3" > "$BURN_QUEUE"
usage 10 50 60
python3 "$B" tick --dry-run >/dev/null; [ ! -e "$T/ran1" ]; ok "dry-run runs nothing" $? 0
python3 "$B" tick >/dev/null; [ -e "$T/ran1" ]; ok "approved smoulder job ran" $? 0
python3 "$B" tick >/dev/null; [ ! -e "$T/ran2" ] && [ ! -e "$T/ran3" ]; ok "blaze not yet / unapproved never" $? 0
usage 10 50 10; python3 "$B" tick >/dev/null; [ -e "$T/ran2" ]; ok "blaze runs at 10h" $? 0
[ ! -e "$T/ran3" ]; ok "[ ] job never runs" $? 0

# brake: halts dispatch, flag set, hook injects context and never blocks
printf '%s\n' "- [x] smoulder | j4 | touch $T/ran4" > "$BURN_QUEUE"
usage 95 50 60; python3 "$B" tick >/dev/null
[ -e "$BURN_STATE/brake" ] && [ ! -e "$T/ran4" ]; ok "brake sets flag, spawns nothing" $? 0
out="$(echo '{}' | python3 "$B" hook)"; echo "$out" | grep -q 'sweep'; ok "hook injects sweep under brake" $? 0
usage 10 50 60; echo '{}' | python3 "$B" hook | wc -c | tr -d ' ' | { read n; ok "hook silent when no brake" "$n" 0; }
[ ! -e "$BURN_STATE/brake" ]; ok "brake clears" $? 0

# keep-alive: pings only when active
export BURN_PING_CMD="touch $T/pinged"
rm -f "$BURN_STATE/active"; python3 "$B" keepalive --once | grep -q idle; ok "idle session: no ping" $? 0
echo '{}' | python3 "$B" hook >/dev/null; python3 "$B" keepalive --once | grep -q ping; [ -e "$T/pinged" ]; ok "active session: ping" $? 0

# notify: off without URL, POSTs when configured
python3 "$B" notify hi | grep -q disabled; ok "notify off by default" $? 0
python3 - "$T" <<'PY' &
import http.server,sys
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(s):
        open(sys.argv[1]+"/hook.json","wb").write(s.rfile.read(int(s.headers["Content-Length"]))); s.send_response(200); s.end_headers()
    def log_message(*a): pass
s=http.server.HTTPServer(("127.0.0.1",18765),H); s.handle_request()
PY
WH=$!; sleep 1
BURN_WEBHOOK_URL=http://127.0.0.1:18765/ python3 "$B" notify hello | grep -q sent; grep -q hello "$T/hook.json"; ok "notify POSTs webhook" $? 0

# kill switch
mkdir -p "$HOME/.claude/state/off"; touch "$HOME/.claude/state/off/nvaex-burn"
sh "$R/scripts/killswitch.sh" nvaex-burn userpromptsubmit; ok "killswitch honoured" $? 0
rm "$HOME/.claude/state/off/nvaex-burn"; sh "$R/scripts/killswitch.sh" nvaex-burn userpromptsubmit; ok "killswitch off by default" $? 1
python3 -c "import json;json.load(open('$R/hooks/hooks.json'));json.load(open('$R/.claude-plugin/plugin.json'))"; ok "manifests parse" $? 0
[ "$fail" = 0 ] && echo "SELFTEST PASS" || { echo "SELFTEST FAIL"; exit 1; }
