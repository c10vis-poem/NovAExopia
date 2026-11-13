#!/usr/bin/env python3
"""dumbass-memory-mcp: stdlib stdio MCP server, the memory tools of nvaex-memory.
5 tools over 4 memory streams, plus 7 thin tools that run ../../scripts/memory.py (the single source of that logic).
Streams: 1 code_review_graph.db (read-only), 2 graphify topology (graph.json, read-only),
3 branch-scoped episodic SQLite shards (WAL), 4 SHA-256 CAS ledger.
Env: DUMBASS_DATA_DIR (default ~/.nvaex/memory), DUMBASS_CRG_DB, DUMBASS_GRAPHIFY_JSON, DUMBASS_SCOPE.
"""
import hashlib, json, os, re, sqlite3, subprocess, sys, time

HOME = os.path.expanduser("~")
DATA = os.path.expanduser(os.environ.get("DUMBASS_DATA_DIR", "~/.nvaex/memory"))
SCRIPT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scripts/memory.py"))
VERSION = "0.2.0"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def conn(path, ro=False):
    if ro:
        c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5)
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        c = sqlite3.connect(path, timeout=5)
        c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    c.row_factory = sqlite3.Row
    return c


def default_scope():
    s = os.environ.get("DUMBASS_SCOPE")
    if s:
        return s
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel", "--abbrev-ref", "HEAD"],
                             capture_output=True, text=True, timeout=3).stdout.split()
        if len(top) == 2:
            return "scope://%s/%s" % (os.path.basename(top[0]), top[1])
    except Exception:
        pass
    return "scope://default/main"


def norm_scope(s):
    s = (s or default_scope()).strip()
    m = re.match(r"^scope://([^/]+)/(.+)$", s)
    if not m:
        raise ValueError("scope must look like scope://<repo>/<branch>")
    return "scope://%s/%s" % (m.group(1), m.group(2))


def shard_path(scope):
    return os.path.join(DATA, "episodic_scopes", re.sub(r"[^A-Za-z0-9._-]+", "_", scope[8:]) + ".db")


def shard(scope, create=True):
    p = shard_path(scope)
    if not create and not os.path.exists(p):
        return None
    c = conn(p)
    c.execute("CREATE TABLE IF NOT EXISTS claims(id INTEGER PRIMARY KEY, ts REAL, kind TEXT,"
              " text TEXT, source TEXT, sha256 TEXT)")
    return c


def cas():
    c = conn(os.path.join(DATA, "sha256_cas.db"))
    c.execute("CREATE TABLE IF NOT EXISTS cas(sha256 TEXT PRIMARY KEY, label TEXT, size INTEGER, ts REAL)")
    return c


def crg_path():
    for p in (os.environ.get("DUMBASS_CRG_DB"), os.path.join(DATA, "code_review_graph.db"),
              os.path.join(os.getcwd(), ".code-review-graph/graph.db")):
        if p and os.path.exists(os.path.expanduser(p)):
            return os.path.expanduser(p)


def graphify_path():
    for p in (os.environ.get("DUMBASS_GRAPHIFY_JSON"), os.path.join(DATA, "graphify_topology.json"),
              os.path.join(os.getcwd(), "graphify-out/graph.json")):
        if p and os.path.exists(os.path.expanduser(p)):
            return os.path.expanduser(p)


_G = {}


def graphify():
    p = graphify_path()
    if not p:
        return None
    if _G.get("p") != p:
        _G["p"], _G["d"] = p, json.load(open(p))
    return _G["d"]


def like(q):
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# ---- tools -----------------------------------------------------------------
def t_query(a):
    q, lim = a["q"], int(a.get("limit", 10))
    streams = a.get("streams") or ["crg", "graphify", "episodic"]
    out = {}
    if "episodic" in streams:
        c = shard(norm_scope(a.get("scope")), create=False)
        out["episodic"] = [dict(r) for r in c.execute(
            "SELECT id,kind,text,source,sha256 FROM claims WHERE text LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?",
            (like(q), lim))] if c else []
    if "crg" in streams:
        p = crg_path()
        if p:
            c = conn(p, ro=True)
            out["crg"] = [dict(r) for r in c.execute(
                "SELECT kind,qualified_name,file_path,line_start FROM nodes WHERE name LIKE ? ESCAPE '\\' "
                "OR qualified_name LIKE ? ESCAPE '\\' LIMIT ?", (like(q), like(q), lim))]
        else:
            out["crg"] = {"unavailable": "no code_review_graph.db (set DUMBASS_CRG_DB)"}
    if "graphify" in streams:
        g = graphify()
        ql = q.lower()
        out["graphify"] = [{"id": n["id"], "label": n.get("label"), "community": n.get("community"),
                            "file": n.get("source_file")} for n in g["nodes"]
                           if ql in str(n.get("label", "")).lower()][:lim] if g else \
            {"unavailable": "no graphify graph.json (set DUMBASS_GRAPHIFY_JSON)"}
    return out


def t_record(a):
    scope = norm_scope(a.get("scope"))
    text = a["text"]
    h = sha(text.encode())
    c = shard(scope)
    cur = c.execute("INSERT INTO claims(ts,kind,text,source,sha256) VALUES(?,?,?,?,?)",
                    (time.time(), a.get("kind", "episodic"), text, a.get("source", ""), h))
    c.commit()
    k = cas()
    k.execute("INSERT OR IGNORE INTO cas VALUES(?,?,?,?)", (h, "claim:%s#%d" % (scope, cur.lastrowid), len(text), time.time()))
    k.commit()
    return {"id": cur.lastrowid, "scope": scope, "sha256": h}


def t_impact(a):
    p = crg_path()
    if not p:
        return {"unavailable": "no code_review_graph.db (set DUMBASS_CRG_DB)"}
    c = conn(p, ro=True)
    t, depth, lim = a["target"], int(a.get("depth", 2)), int(a.get("limit", 50))
    seeds = [r[0] for r in c.execute("SELECT qualified_name FROM nodes WHERE qualified_name=? OR name=? LIMIT 20", (t, t))]
    seen, frontier, hits = set(seeds), seeds, []
    for d in range(1, depth + 1):
        nxt = []
        for s in frontier:
            for r in c.execute("SELECT DISTINCT source_qualified,kind FROM edges WHERE target_qualified=? LIMIT 200", (s,)):
                if r[0] not in seen:
                    seen.add(r[0]); nxt.append(r[0]); hits.append({"depth": d, "node": r[0], "via": r[1]})
        frontier = nxt
    files = sorted({r[0] for q in [h["node"] for h in hits[:lim]]
                    for r in c.execute("SELECT file_path FROM nodes WHERE qualified_name=?", (q,))})
    return {"seeds": seeds, "dependents": hits[:lim], "total": len(hits), "files": files}


def t_cas(a):
    if "path" in a:
        h = sha(open(os.path.expanduser(a["path"]), "rb").read())
        label, size = a["path"], os.path.getsize(os.path.expanduser(a["path"]))
    elif "text" in a:
        h, label, size = sha(a["text"].encode()), "text", len(a["text"].encode())
    else:
        raise ValueError("give path or text")
    k = cas()
    known = k.execute("SELECT label FROM cas WHERE sha256=?", (h,)).fetchone()
    if a.get("register") and not known:
        k.execute("INSERT INTO cas VALUES(?,?,?,?)", (h, label, size, time.time())); k.commit()
    exp = a.get("expect_sha256")
    return {"sha256": h, "in_ledger": bool(known), "ledger_label": known[0] if known else None,
            "matches_expected": (h == exp.lower()) if exp else None, "registered": bool(a.get("register") and not known)}


def t_status(a):
    scope = norm_scope(a.get("scope"))
    sd = os.path.join(DATA, "episodic_scopes")
    scopes = sorted(os.listdir(sd)) if os.path.isdir(sd) else []
    c = shard(scope, create=False)
    k = os.path.join(DATA, "sha256_cas.db")
    return {"data_dir": DATA, "scope": scope,
            "claims_in_scope": c.execute("SELECT count(*) FROM claims").fetchone()[0] if c else 0,
            "shards": scopes, "crg_db": crg_path(), "graphify_json": graphify_path(),
            "cas_entries": cas().execute("SELECT count(*) FROM cas").fetchone()[0] if os.path.exists(k) else 0,
            "supabase_mirror": "off (not implemented in 0.1.0)", "version": VERSION}


# ---- tools that run scripts/memory.py; nudge and the hook entries are not tools ------------
def script(a, *args, stdin="", ok=(0,)):
    cwd = os.path.expanduser(a["cwd"]) if a.get("cwd") else None
    r = subprocess.run([sys.executable, "-B", "-I", SCRIPT, *args], input=stdin, capture_output=True,
                       text=True, timeout=120, cwd=cwd)
    if r.returncode not in ok:
        raise RuntimeError((r.stderr or r.stdout).strip() or "memory.py exit %d" % r.returncode)
    return r.stdout.strip()


def t_snapshot(a):
    d = {"cwd": a.get("cwd") or os.getcwd(), "source": a.get("source", "startup")}
    out = script(a, "snapshot", "--report", stdin=json.dumps(d))
    return {"snapshot": json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""}


def t_freeze(a):
    act = a.get("action", "add")
    if act == "add":
        return {"output": script(a, "freeze", stdin=a["text"])}  # stdin: claim text can never be read as a flag
    if act == "list":
        return {"output": script(a, "freeze", "--list")}
    if act == "unfreeze":
        return {"output": script(a, "freeze", "--unfreeze", a["id"])}
    raise ValueError("action must be add, list or unfreeze")


def t_task(a):
    act = a.get("action", "state")
    if act == "add":
        return json.loads(script(a, "task", "add", a["name"]))
    if act == "patch":
        return json.loads(script(a, "task", "patch", json.dumps(a["patch"])))
    if act in ("state", "done"):
        return json.loads(script(a, "task", act))
    raise ValueError("action must be add, patch, state or done")


def session_input(a):
    tp = os.path.expanduser(a["transcript_path"])
    if not os.path.isfile(tp):
        raise ValueError("no transcript at " + tp)
    return json.dumps({"transcript_path": tp, "session_id": a.get("session_id"), "cwd": a.get("cwd") or os.getcwd()})


def t_recap(a):
    return json.loads(script(a, "recap", "--report", stdin=session_input(a)))


def t_export(a):
    return json.loads(script(a, "export", "--report", stdin=session_input(a)))


def t_map(a):
    args = ["map", a["path"]] + (["--depth", str(int(a["depth"]))] if a.get("depth") else []) + (["--force"] if a.get("force") else [])
    out = script(a, *args)
    return {"wrote": [] if out == "nothing written" else out.splitlines()}


def t_lint(a):
    args = ["lint", "--root", os.path.expanduser(a["root"]), "--json"] + (["--files", *a["files"]] if a.get("files") else [])
    found = json.loads(script(a, *args, ok=(0, 1)))
    return {"clean": not found, "findings": found}


S = {"type": "string"}
CWD = {"type": "string", "description": "project folder; default the server's working folder"}
TOOLS = {
    "memory.query": (t_query, "Search claims (episodic scope), code graph nodes (CRG) and graphify labels.",
                     {"q": S, "scope": S, "limit": {"type": "integer"}, "streams": {"type": "array", "items": S}}, ["q"]),
    "memory.record_claim": (t_record, "Store a claim in the branch-scoped shard and register its SHA-256.",
                            {"text": S, "scope": S, "kind": S, "source": S}, ["text"]),
    "memory.ast_impact": (t_impact, "Blast radius: dependents (reverse edges) of a code-graph node.",
                          {"target": S, "depth": {"type": "integer"}, "limit": {"type": "integer"}}, ["target"]),
    "memory.cas_verify": (t_cas, "Hash a file or text; check/register in the SHA-256 ledger; compare to expect_sha256.",
                          {"path": S, "text": S, "expect_sha256": S, "register": {"type": "boolean"}}, []),
    "memory.scope_status": (t_status, "Active scope, shards, stream availability, ledger size.", {"scope": S}, []),
    "memory.snapshot": (t_snapshot, "Return the continuity text the SessionStart hook injects: frozen claims, active task, branch handoff, recent decisions, drift. Writes nothing.",
                        {"cwd": CWD, "source": {"type": "string", "enum": ["startup", "resume", "clear", "compact"]}}, []),
    "memory.freeze": (t_freeze, "Lock settled project claims so every later session sees them at start. action=add (text: claim-shaped lines are extracted), list, or unfreeze (id).",
                      {"action": {"type": "string", "enum": ["add", "list", "unfreeze"]}, "text": S, "id": S, "cwd": CWD}, []),
    "memory.task": (t_task, "The project's active task state (max 4000 chars), re-injected at session start. action=add (name), patch (patch object; null deletes a key), state, or done.",
                    {"action": {"type": "string", "enum": ["add", "patch", "state", "done"]}, "name": S, "patch": {"type": "object"}, "cwd": CWD}, []),
    "memory.recap": (t_recap, "Write a session transcript's prompts and last answer to the daily recap file and roll finished weeks up. Returns the file written; written=null means nothing new (one recap per session).",
                     {"transcript_path": S, "session_id": S, "cwd": CWD}, ["transcript_path"]),
    "memory.export": (t_export, "Save a session transcript as readable text under the state folder (secrets redacted, 0600, last 20 kept). Returns the file written.",
                      {"transcript_path": S, "session_id": S, "cwd": CWD}, ["transcript_path"]),
    "memory.map": (t_map, "Write tiered MAP.md routers for a folder tree. Hand-written MAP.md files are left alone unless force=true.",
                   {"path": S, "depth": {"type": "integer"}, "force": {"type": "boolean"}, "cwd": CWD}, ["path"]),
    "memory.lint": (t_lint, "Check a repo's anchored memory ledgers (decisions.md, FACTS.md) for drift, broken anchors and dangling entries. Read-only.",
                    {"root": S, "files": {"type": "array", "items": S}, "cwd": CWD}, ["root"]),
}


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import observations  # noqa: E402  claude-mem's store and three-step search, ported (see its docstring)
TOOLS.update(observations.TOOLS)
import ob1  # noqa: E402  OB1 layer: governed semantic memory in Supabase (see its docstring)
TOOLS.update(ob1.TOOLS)


def call(name, args):  # no off switch: memory is never turned off (owner, 2026-11-12 and 2026-11-13)
    return TOOLS[name][0](args or {})


def handle(m):
    meth, id_ = m.get("method"), m.get("id")
    if id_ is None:
        return None
    ok = lambda r: {"jsonrpc": "2.0", "id": id_, "result": r}
    if meth == "initialize":
        return ok({"protocolVersion": m.get("params", {}).get("protocolVersion", "2024-11-05"),
                   "capabilities": {"tools": {}}, "serverInfo": {"name": "dumbass-memory-mcp", "version": VERSION}})
    if meth == "ping":
        return ok({})
    if meth == "tools/list":
        return ok({"tools": [{"name": n, "description": d, "inputSchema": {"type": "object", "properties": p, "required": r}}
                             for n, (_, d, p, r) in TOOLS.items()]})
    if meth == "tools/call":
        p = m.get("params", {})
        if p.get("name") not in TOOLS:
            return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32602, "message": "unknown tool"}}
        try:
            res, err = call(p["name"], p.get("arguments")), False
        except Exception as e:
            res, err = {"error": "%s: %s" % (type(e).__name__, e)}, True
        return ok({"content": [{"type": "text", "text": json.dumps(res, default=str)}], "isError": err})
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "method not found"}}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            r = handle(json.loads(line))
        except Exception as e:
            r = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
        if r:
            sys.stdout.write(json.dumps(r) + "\n"); sys.stdout.flush()


if __name__ == "__main__":
    main()
