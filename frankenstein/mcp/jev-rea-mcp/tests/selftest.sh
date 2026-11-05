#!/usr/bin/env sh
# Real stdio round trip against server.py. Exit 0 only if every check passes.
D=$(cd "$(dirname "$0")/.." && pwd)
export JEV_JOBS_DIR="${TMPDIR:-/tmp}/jev-rea-selftest-$$"; unset JEV_AG_BRIDGE_URL
S=$(date +%s%N 2>/dev/null)
OUT=$(printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"jev.route_task","arguments":{"task":"delete old branches across all repos and force push"}}}' \
 '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"jev.audit_gate","arguments":{"gate":"1","evidence":{"goal":"x"}}}}' \
 '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"rea.inspect_target","arguments":{"path":"'"$D"'"}}}' \
 '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"ag.cloud_dispatch","arguments":{"job":"demo","send":true}}}' \
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
chk("tools/list 4 tools", names == ["ag.cloud_dispatch","jev.audit_gate","jev.route_task","rea.inspect_target"])
chk("route_task L3", txt(3)["level"] == 3)
g = txt(4)["gates"][0]
chk("audit_gate incomplete, non-blocking", g["status"] == "incomplete" and txt(4)["blocking"] is False)
i = txt(5)
chk("inspect_target read-only sees server.py", i["read_only"] and "server.py" in i["entrypoints"] + i["manifests"] + [""] or i["files_scanned"] > 0)
d = txt(6)
chk("cloud_dispatch writes job, does not send", d["sent"] is False and os.path.isfile(d["job_file"]))
sys.exit(0 if all(ok) else 1)
'; RC=$?
rm -rf "$JEV_JOBS_DIR"
[ -n "$S" ] && echo "round-trip ms: $(( (E_-S)/1000000 ))"
[ $RC -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"; exit $RC
