#!/usr/bin/env sh
# Real stdio round trip against bin/claw-mcp: initialize, tools/list, tools/call, kill switch.
D="$(cd "$(dirname "$0")/.." && pwd)"; fail=0
ck() { if [ "$2" = ok ]; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }
out="$(printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"claw.workflows","arguments":{"action":"list"}}}' \
 '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"claw.search","arguments":{"query":"x"}}}' \
 | sh "$D/bin/claw-mcp")"
echo "$out" | python3 -c '
import sys, json
r = {j["id"]: j for j in map(json.loads, sys.stdin)}
names = sorted(t["name"] for t in r[2]["result"]["tools"])
want = ["claw.browser","claw.device","claw.infer","claw.scrape","claw.search","claw.workflows"]
chk = [("initialize", r[1]["result"]["serverInfo"]["name"].startswith("claw-mcp")),
       ("tools/list has the 6 tools", names == want),
       ("tools/call claw.workflows list", "phone-status" in r[3]["result"]["content"][0]["text"]),
       ("search reports not-implemented", r[4]["result"].get("isError") and "not-implemented" in r[4]["result"]["content"][0]["text"])]
for n, ok in chk: print("PASS" if ok else "FAIL", n)
sys.exit(0 if all(ok for _, ok in chk) else 1)' || fail=1
# kill switch: no output, exit 0
t="$(mktemp -d)"; mkdir -p "$t/.claude/state/off"; : > "$t/.claude/state/off/claw-mcp"
o="$(echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | HOME="$t" sh "$D/bin/claw-mcp")"; rc=$?
[ -z "$o" ] && [ $rc -eq 0 ] && ck "kill switch silences server" ok || ck "kill switch silences server" no
rm -rf "$t"
[ $fail -eq 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"; exit $fail
