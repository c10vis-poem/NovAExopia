#!/usr/bin/env bash
# Real stdio round trip against burn-mcp, real scripts, temp state, local webhook and bridge receivers. Exit 0 only if every check passes.
set -u
D="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME="$T/home" BURN_STATE="$T/state" BURN_USAGE_FILE="$T/usage.json" BURN_NOW=1800000000 BURN_PING_CMD="touch $T/pinged"
mkdir -p "$HOME/.claude/state/off"; unset BURN_USAGE_CMD BURN_WEBHOOK_URL AG_BRIDGE_URL AG_JOBS_DIR
python3 -I - "$D/server.py" "$T" <<'PY' || exit 1
import http.server, json, os, subprocess, sys, threading
srv, T = sys.argv[1:3]
got = []
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(s):
        got.append(json.loads(s.rfile.read(int(s.headers["Content-Length"])))); s.send_response(200); s.end_headers()
    def log_message(*a): pass
hs = http.server.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=hs.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/" % hs.server_port
n = [0]
def start(**env):
    return subprocess.Popen([sys.executable, "-I", srv], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env={**os.environ, **env})
def rpc(p, method, params=None):
    n[0] += 1
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n[0], "method": method, "params": params or {}}) + "\n"); p.stdin.flush()
    return json.loads(p.stdout.readline())
def tool(p, name, **a):
    return json.loads(rpc(p, "tools/call", {"name": name, "arguments": a})["result"]["content"][0]["text"])
good = []
def chk(m, c): good.append(c); print(("PASS " if c else "FAIL ") + m)
p = start()
chk("initialize", rpc(p, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}})["result"]["serverInfo"]["name"] == "burn-mcp")
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); p.stdin.flush()
chk("tools/list: 4 tools, no hook, no tick", sorted(t["name"] for t in rpc(p, "tools/list")["result"]["tools"]) == ["ag.cloud_dispatch", "burn.keepalive", "burn.notify", "burn.status"])
chk("status: no usage source -> unknown", tool(p, "burn.status")["mode"] == "unknown")
now = 1800000000
json.dump({"capturedAt": now * 1000, "five_hour": {"used_percentage": 95, "resets_at": now + 3600}, "seven_day": {"used_percentage": 10, "resets_at": now + 360000}}, open(T + "/usage.json", "w"))
chk("status: real reading -> brake", tool(p, "burn.status")["mode"] == "brake")
chk("keepalive: idle session, no ping", "idle" in tool(p, "burn.keepalive")["result"] and not os.path.exists(T + "/pinged"))
os.makedirs(T + "/state", exist_ok=True); open(T + "/state/active", "w").write(str(now))
chk("keepalive: active session, one ping, returns", tool(p, "burn.keepalive")["result"] == "ping" and os.path.exists(T + "/pinged"))
chk("notify: off without webhook", "disabled" in tool(p, "burn.notify", message="hi")["result"])
d = tool(p, "ag.cloud_dispatch", job="demo", payload={"a": 1}, send=True)
chk("dispatch: writes the job under burn state, no bridge, says so", d["sent"] is False and d["job_file"].startswith(T + "/state/jobs/") and "not set" in d["note"] and json.load(open(d["job_file"]))["payload"] == {"a": 1})
chk("dispatch: no POST without a bridge", got == [])
r = rpc(p, "tools/call", {"name": "ag.cloud_dispatch", "arguments": {}})["result"]
chk("dispatch: missing job is a tool error", r["isError"] is True)
p.stdin.close(); p.wait(timeout=5)
p = start(AG_BRIDGE_URL=URL, BURN_WEBHOOK_URL=URL)
d = tool(p, "ag.cloud_dispatch", job="demo2")
chk("dispatch: bridge set but send=false, no POST", d["sent"] is False and got == [])
d = tool(p, "ag.cloud_dispatch", job="demo3", send=True)
chk("dispatch: bridge set and send=true, POSTs", d["sent"] is True and d["http"] == 200 and got[-1]["job"] == "demo3")
chk("notify: POSTs the webhook", tool(p, "burn.notify", message="hello")["result"] == "sent" and got[-1] == {"text": "hello"})
open(os.environ["HOME"] + "/.claude/state/off/nvaex-burn", "w").close()
chk("kill switch: tools return disabled, nothing runs", "disabled" in tool(p, "ag.cloud_dispatch", job="x", send=True) and got[-1] == {"text": "hello"})
p.stdin.close(); p.wait(timeout=5)
chk("clean exit on EOF", p.returncode == 0)
src = open(srv).read()
chk("server copies no script logic", not any(x in src for x in ("urlopen", "def assess", "def dispatch", "os.makedirs")))
sys.exit(0 if all(good) else 1)
PY
echo "SELFTEST OK"
