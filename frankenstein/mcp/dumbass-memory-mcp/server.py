#!/usr/bin/env python3
"""dumbass-memory-mcp: stdlib stdio MCP server, 5 tools over 4 memory streams.
Streams: 1 code_review_graph.db (read-only), 2 graphify topology (graph.json, read-only),
3 branch-scoped episodic SQLite shards (WAL), 4 SHA-256 CAS ledger.
Env: DUMBASS_DATA_DIR (default ~/.nvaex/memory), DUMBASS_CRG_DB, DUMBASS_GRAPHIFY_JSON, DUMBASS_SCOPE.
"""
import hashlib, json, os, re, sqlite3, subprocess, sys, time

HOME = os.path.expanduser("~")
DATA = os.path.expanduser(os.environ.get("DUMBASS_DATA_DIR", "~/.nvaex/memory"))
OFF = os.path.join(HOME, ".claude/state/off/dumbass-memory-mcp")
VERSION = "0.1.0"


def disabled():
    return os.path.exists(os.path.join(HOME, ".nvaex-hooks-off")) or os.path.exists(OFF)


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


S = {"type": "string"}
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
}


def call(name, args):
    if disabled():
        return {"disabled": "kill switch active (~/.nvaex-hooks-off or ~/.claude/state/off/dumbass-memory-mcp); remove to revoke"}
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
