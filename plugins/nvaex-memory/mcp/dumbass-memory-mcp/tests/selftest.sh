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
export DUMBASS_CRG_DB="$T/crg.db" DUMBASS_GRAPHIFY_JSON="$T/g.json" NVAEX_STATE="$T/state" NVAEX_RECAPS="$T/recaps"
export DUMBASS_SHARED_DIR="$T/shared"
mkdir -p "$T/recaps/memory" "$T/repo/sub/deep" "$T/repo/memory"
git -C "$T/repo" init -q .
cat > "$T/repo/memory/decisions.md" <<'M'
<!-- @meta
id: stale-b
status: active
anchors:
  - kind: file_exists
    file: nothere.txt
    expect: present
-->
M
printf '%s\n' '{"type":"user","message":{"content":"set up the widget ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAA"}}' '{"type":"assistant","message":{"content":[{"type":"text","text":"Done"}]}}' > "$T/tr.jsonl"
echo "hello" > "$T/f.txt"
python3 -I - "$H/server.py" "$T/f.txt" "$T" <<'PY'
import json, subprocess, sys, hashlib, os
srv, f, T = sys.argv[1:4]
REPO = T + "/repo"
p = subprocess.Popen([sys.executable, srv], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
n = [0]
def rpc(method, params=None, note=False):
    m = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not note: n[0] += 1; m["id"] = n[0]
    p.stdin.write(json.dumps(m) + "\n"); p.stdin.flush()
    return None if note else json.loads(p.stdout.readline())
def tool(name, /, **a):
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
ok(names == sorted(["memory.query", "memory.record_claim", "memory.ast_impact", "memory.cas_verify", "memory.scope_status",
                    "memory.snapshot", "memory.freeze", "memory.task", "memory.recap", "memory.export", "memory.map", "memory.lint",
                    "memory.save", "memory.session_summary", "memory.search", "memory.timeline", "memory.get_observations",
                    "memory.session_context"]),
   "tools/list has the 5 stream tools + 7 memory.py tools + 6 observation tools, no nudge")
# observation store (claude-mem port): JSONL in DUMBASS_SHARED_DIR is the source of truth, FTS5 index rebuilt from it
sv = tool("memory.save", project="p", type="decision", title="Use stdlib sqlite for claude-mem", facts=["no bun"],
          text="password=hunter2xyz")
ok(sv["saved"] and len(sv["id"]) == 64, "save writes a sha256-keyed record")
ok(tool("memory.save", project="p", type="decision", title="Use stdlib sqlite for claude-mem", facts=["no bun"],
        text="password=hunter2xyz")["saved"] is False, "save refuses the same content twice")
line = open(os.environ["DUMBASS_SHARED_DIR"] + "/p.jsonl").read()
ok("hunter2xyz" not in line and "[REDACTED]" in line, "save redacts secrets before writing")
hits = tool("memory.search", query="claude-mem sqlite", project="p")["results"]
ok(len(hits) == 1 and hits[0]["type"] == "decision", "search finds it (step 1)")
ok(tool("memory.get_observations", ids=[hits[0]["id"]])["observations"][0]["facts"] == ["no bun"], "get_observations returns the full record (step 3)")
ok(tool("memory.timeline", id=hits[0]["id"])["timeline"][0]["anchor"] is True, "timeline anchors on the id (step 2)")
tool("memory.session_summary", project="p", request="port claude-mem", completed="store and search")
cx = tool("memory.session_context", project="p")
ok(cx["stored"] == 2 and cx["last_summary"]["completed"] == "store and search", "session_context: recent index + last summary")
for ext in ("", "-wal", "-shm"):  # the whole local index, as a fresh device would have it
    if os.path.exists(os.environ["DUMBASS_DATA_DIR"] + "/observations_index.db" + ext):
        os.remove(os.environ["DUMBASS_DATA_DIR"] + "/observations_index.db" + ext)
rb = tool("memory.search", query="claude-mem", project="p")["results"]
ok(sorted(r["type"] for r in rb) == ["decision", "summary"] and hits[0]["id"] in [r["id"] for r in rb],
   "index rebuilds from the JSONL alone (decision and summary both found)")
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
# memory.py tools, real script on a real git repo
def bad(name, /, **a):
    r = rpc("tools/call", {"name": name, "arguments": a})["result"]
    return r["isError"], r["content"][0]["text"]
fz = tool("memory.freeze", text="Deploys must go through the PR pipeline", cwd=REPO)["output"]
ok(fz.startswith("frozen "), "freeze stores a claim")
cid = fz.split()[1]
ok(os.path.isfile(T + "/recaps/memory/continuity/repo.claims.jsonl"), "freeze wrote where memory.py writes it")
ok(cid in tool("memory.freeze", action="list", cwd=REPO)["output"], "freeze list shows it")
tool("memory.task", action="add", name="wire widget", cwd=REPO)
st = tool("memory.task", action="patch", patch={"next": "write test", "old": None}, cwd=REPO)
ok(st["state"] == {"next": "write test"} and st["name"] == "wire widget", "task add + patch")
e, msg = bad("memory.task", action="patch", patch={"big": "a" * 4500}, cwd=REPO)
ok(e and "4000" in msg, "task over cap is a tool error with the reason")
sn = tool("memory.snapshot", cwd=REPO)["snapshot"]
ok("PR pipeline" in sn and "write test" in sn, "snapshot returns frozen claim + active task")
ok(tool("memory.task", action="done", cwd=REPO)["done"] is True, "task done")
tool("memory.freeze", action="unfreeze", id=cid, cwd=REPO)
ok(tool("memory.freeze", action="list", cwd=REPO)["output"] == "", "unfreeze removes it")
os.makedirs(T + "/empty")
ok(tool("memory.snapshot", cwd=T + "/empty")["snapshot"] == "", "snapshot empty when nothing to inject")
rc = tool("memory.recap", transcript_path=T + "/tr.jsonl", session_id="sess-1", cwd=REPO)
txt = open(rc["written"]).read() if rc["written"] else ""
ok("set up the widget" in txt and "ghp_" not in txt and "Done" in txt, "recap writes the daily file, secret redacted")
ok(tool("memory.recap", transcript_path=T + "/tr.jsonl", session_id="sess-1", cwd=REPO)["written"] is None, "recap once per session")
ok(bad("memory.recap", transcript_path=T + "/none.jsonl")[0], "recap with no transcript is a tool error")
ex = tool("memory.export", transcript_path=T + "/tr.jsonl", session_id="sess-abcdefgh")["written"]
ok(ex.startswith(T + "/state/exports/") and oct(os.stat(ex).st_mode & 0o777) == "0o600" and "ghp_" not in open(ex).read(), "export writes redacted 0600 file")
mp = tool("memory.map", path=REPO)["wrote"]
ok(REPO + "/MAP.md" in mp and os.path.isfile(REPO + "/MAP.md"), "map writes MAP.md")
li = tool("memory.lint", root=REPO)
ok(li["clean"] is False and li["findings"][0]["entry_id"] == "stale-b", "lint finds drift (drift is a result, not an error)")
os.makedirs(T + "/clean/memory")
for ledger in ("decisions.md", "FACTS.md"): open(T + "/clean/memory/" + ledger, "w").write("plain\n")
ok(tool("memory.lint", root=T + "/clean")["clean"] is True, "lint clean on ledgers with no drift")
src = open(srv).read()
ok(not any(d in src for d in ("def extract_claims", "def load_claims", "def mapgen", "def turns")), "server copies no memory.py logic")
p.stdin.close(); p.wait(timeout=5)
ok(p.returncode == 0, "clean exit on EOF")
PY
# real CRG db, read-only, if present
R="$HOME_REAL/repos/NovA-code-review-graph/.code-review-graph/graph.db"
if [ -f "$R" ]; then
  OUT=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"memory.query","arguments":{"q":"main","streams":["crg"],"limit":2}}}' | DUMBASS_CRG_DB="$R" python3 -I "$H/server.py")
  case "$OUT" in *qualified_name*) echo "PASS real CRG db read-only query";; *) echo "FAIL real CRG: $OUT"; exit 1;; esac
fi
echo "SELFTEST OK"
