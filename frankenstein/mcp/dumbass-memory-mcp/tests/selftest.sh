#!/usr/bin/env bash
# Real stdio round trip against server.py with fixture data in a temp dir.
set -eu
H="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME_REAL="$HOME" DUMBASS_DATA_DIR="$T/data" DUMBASS_SCOPE="scope://demo/main"
sqlite3 "$T/crg.db" "CREATE TABLE nodes(id INTEGER PRIMARY KEY,kind TEXT,name TEXT,qualified_name TEXT UNIQUE,file_path TEXT,line_start INT);
CREATE TABLE edges(id INTEGER PRIMARY KEY,kind TEXT,source_qualified TEXT,target_qualified TEXT,file_path TEXT);
INSERT INTO nodes(kind,name,qualified_name,file_path,line_start) VALUES('Function','core','a.py::core','a.py',1),('Function','mid','b.py::mid','b.py',2),('Function','top','c.py::top','c.py',3);
INSERT INTO edges(kind,source_qualified,target_qualified,file_path) VALUES('CALLS','b.py::mid','a.py::core','b.py'),('CALLS','c.py::top','b.py::mid','c.py');"
echo '{"nodes":[{"id":"x","label":"CoreThing","community":1,"source_file":"a.py"}],"links":[]}' > "$T/g.json"
export DUMBASS_CRG_DB="$T/crg.db" DUMBASS_GRAPHIFY_JSON="$T/g.json"
echo "hello" > "$T/f.txt"
python3 -I - "$H/server.py" "$T/f.txt" <<'PY'
import json, subprocess, sys, hashlib, os
srv, f = sys.argv[1:3]
p = subprocess.Popen([sys.executable, srv], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
n = [0]
def rpc(method, params=None, note=False):
    m = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not note: n[0] += 1; m["id"] = n[0]
    p.stdin.write(json.dumps(m) + "\n"); p.stdin.flush()
    return None if note else json.loads(p.stdout.readline())
def tool(name, **a):
    r = rpc("tools/call", {"name": name, "arguments": a})["result"]
    assert not r["isError"], r
    return json.loads(r["content"][0]["text"])
def ok(c, msg):
    print(("PASS " if c else "FAIL ") + msg)
    if not c: p.kill(); sys.exit(1)
r = rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}})
ok(r["result"]["serverInfo"]["name"] == "dumbass-memory-mcp", "initialize")
rpc("notifications/initialized", note=True)
names = sorted(t["name"] for t in rpc("tools/list")["result"]["tools"])
ok(names == sorted(["memory.query", "memory.record_claim", "memory.ast_impact", "memory.cas_verify", "memory.scope_status"]), "tools/list has 5 tools")
c = tool("memory.record_claim", text="auth uses core()", kind="semantic")
ok(c["sha256"] == hashlib.sha256(b"auth uses core()").hexdigest(), "record_claim returns sha256")
q = tool("memory.query", q="core")
ok(len(q["episodic"]) == 1 and len(q["crg"]) == 1 and len(q["graphify"]) == 1, "query hits all 3 streams")
i = tool("memory.ast_impact", target="core")
ok([d["node"] for d in i["dependents"]] == ["b.py::mid", "c.py::top"], "ast_impact walks callers to depth 2")
v = tool("memory.cas_verify", path=f, expect_sha256=hashlib.sha256(b"hello\n").hexdigest(), register=True)
ok(v["matches_expected"] and v["registered"], "cas_verify match + register")
ok(tool("memory.cas_verify", path=f)["in_ledger"], "cas ledger remembers")
ok(tool("memory.cas_verify", text="auth uses core()")["in_ledger"], "claim registered in ledger")
s = tool("memory.scope_status")
ok(s["claims_in_scope"] == 1 and s["cas_entries"] == 2, "scope_status counts")
ok(os.popen("sqlite3 %s/data/episodic_scopes/demo_main.db 'pragma journal_mode'" % os.environ["DUMBASS_DATA_DIR"].rsplit("/data", 1)[0]).read().strip() == "wal", "shard is WAL")
p.stdin.close(); p.wait(timeout=5)
ok(p.returncode == 0, "clean exit on EOF")
PY
# kill switch via fake HOME
mkdir -p "$T/h/.claude/state/off"; touch "$T/h/.claude/state/off/dumbass-memory-mcp"
OUT=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"memory.scope_status","arguments":{}}}' | HOME="$T/h" python3 -I "$H/server.py")
case "$OUT" in *"kill switch active"*) echo "PASS kill switch disables tools";; *) echo "FAIL kill switch"; exit 1;; esac
# real CRG db, read-only, if present
R="$HOME_REAL/repos/NovA-code-review-graph/.code-review-graph/graph.db"
if [ -f "$R" ]; then
  OUT=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"memory.query","arguments":{"q":"main","streams":["crg"],"limit":2}}}' | DUMBASS_CRG_DB="$R" python3 -I "$H/server.py")
  case "$OUT" in *qualified_name*) echo "PASS real CRG db read-only query";; *) echo "FAIL real CRG: $OUT"; exit 1;; esac
fi
echo "SELFTEST OK"
