#!/usr/bin/env sh
# Real stdio round trip against server.py. Exit 0 only if every check passes.
D=$(cd "$(dirname "$0")/.." && pwd)
unset TYPESAFE_API_KEY CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY TYPESAFE_BASE_URL
# jev.remember data dir: tilde form under an isolated HOME proves expansion; cwd is an empty dir to prove nothing lands there
TH="${TMPDIR:-/tmp}/jev-rea-home-$$"; mkdir -p "$TH/cwd"; export HOME="$TH"; export JEV_MEMORY_DIR="~/mem-test"; cd "$TH/cwd"
python3 -B -I -c "import sys;sys.path.insert(0,'$D');import server" || { echo "FAIL import"; exit 1; }
[ -z "$(ls -A "$TH/cwd")" ] && [ ! -e "$TH/mem-test" ] && echo "PASS import creates nothing" || { echo "FAIL import creates files"; exit 1; }
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"recall","query":"x"}}}' | python3 -I "$D/server.py" >/dev/null
[ ! -e "$TH/mem-test" ] && [ -z "$(ls -A "$TH/cwd")" ] && echo "PASS recall on missing dir creates nothing" || { echo "FAIL recall created files"; exit 1; }
env -u JEV_MEMORY_DIR python3 -B -I -c "
import sys,os;sys.path.insert(0,'$D');import server
sys.exit(0 if server.mem_dir()==os.path.join('$TH','.nvaex','jev-memory') else 1)" && echo "PASS default data dir is ~/.nvaex/jev-memory" || { echo "FAIL default data dir"; exit 1; }
[ ! -e "$D/data/tiers.json" ] && [ -f "$D/../../skills/jev-router/tiers.json" ] && echo "PASS one tiers.json, in the plugin" || { echo "FAIL tiers.json copy"; exit 1; }
S=$(date +%s%N 2>/dev/null)
OUT=$(printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"jev.route_task","arguments":{"task":"delete old branches across all repos and force push"}}}' \
 '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"jev.audit_gate","arguments":{"gate":"1","evidence":{"goal":"x"}}}}' \
 '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"recall","query":"sqlite"}}}' \
 '{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"add","text":"State store is sqlite, not postgres. api_key=abc123SECRET","tags":["db","Storage"],"project":"demo"}}}' \
 '{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"add","text":"State store is sqlite, not postgres. api_key=abc123SECRET","tags":["db"],"project":"demo"}}}' \
 '{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"add","text":"Deploys go through the PR pipeline","tags":["ci"]}}}' \
 '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"recall","query":"which database sqlite","project":"demo"}}}' \
 '{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"recall","tags":["ci"]}}}' \
 '{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"recall","query":"kubernetes"}}}' \
 '{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"jev.remember","arguments":{"action":"add","text":"  "}}}' \
 '{"jsonrpc":"2.0","id":15,"method":"tools/call","params":{"name":"jev.route_task","arguments":{"task":"please design the architecture and plan the roadmap for the next phase"}}}' \
 | python3 -I "$D/server.py") || { echo FAIL server; exit 1; }
E_=$(date +%s%N 2>/dev/null)
printf "%s\n" "$OUT" | python3 -I -c '
import sys, json, glob, os
r = {}
for l in sys.stdin: j = json.loads(l); r[j["id"]] = j
def txt(i): return json.loads(r[i]["result"]["content"][0]["text"])
ok = []
def chk(n, c): ok.append(c); print(("PASS " if c else "FAIL ") + n)
chk("initialize", r[1]["result"]["serverInfo"]["name"] == "jev-rea-mcp")
names = sorted(t["name"] for t in r[2]["result"]["tools"])
chk("tools/list: the 3 jev.* tools only", names == ["jev.audit_gate","jev.remember","jev.route_task"])
chk("route_task L3", txt(3)["level"] == 3)
chk("route_task states its source and reason", txt(3)["source"] == "local-fallback" and txt(3)["error"] == "no-key")
g = txt(4)["gates"][0]
chk("audit_gate incomplete, non-blocking", g["status"] == "incomplete" and txt(4)["blocking"] is False)
chk("route_task L3 -> fable tier", txt(3)["tier"]["model"] == "claude-fable-5-1")
chk("route_task plan -> fable", txt(15)["tier"]["model"] == "claude-fable-5-1")
chk("remember: recall on empty store is empty", txt(7)["count"] == 0)
a = txt(8)
chk("remember add: stored, secret redacted", a["stored"] is True and a["redacted"] == 1)
chk("remember add: tilde expanded to HOME", a["path"] == os.path.expanduser("~/mem-test/memory.jsonl") and not a["path"].startswith("~"))
chk("remember add: duplicate not stored twice", txt(9)["duplicate"] is True and txt(9)["id"] == a["id"])
txt(10)
rc = txt(11)
chk("remember recall: query + project match", rc["count"] == 1 and "sqlite" in rc["memories"][0]["text"] and "abc123SECRET" not in rc["memories"][0]["text"] and rc["memories"][0]["tags"] == ["db","storage"])
chk("remember recall: tag filter", txt(12)["count"] == 1 and txt(12)["memories"][0]["text"].startswith("Deploys"))
chk("remember recall: no match is empty", txt(13)["count"] == 0)
chk("remember add: empty text is an error", "error" in txt(14))
chk("remember: file mode 0600, one line per add", oct(os.stat(a["path"]).st_mode & 0o777) == "0o600" and len(open(a["path"]).read().splitlines()) == 2)
chk("remember: nothing written to cwd", os.listdir(os.getcwd()) == [])
sys.exit(0 if all(ok) else 1)
'; RC=$?
rm -rf "$TH"
[ -n "$S" ] && echo "round-trip ms: $(( (E_-S)/1000000 ))"
[ $RC -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"; exit $RC
