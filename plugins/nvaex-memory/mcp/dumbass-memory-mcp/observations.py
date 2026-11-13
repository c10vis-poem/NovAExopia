"""Observation memory for dumbass-memory: claude-mem's store and search, ported to stdlib Python (no Bun, no worker).

What it solves: an agent's findings must survive the session and reach any device or account. claude-mem keeps them in
one SQLite file per machine; here the source of truth is plain JSONL in a git repo (default: the vault's
05_episodic_logs/observations/), one file per project, one line per observation keyed by its SHA-256. Pushing the repo
carries memory to every device; each device rebuilds a local SQLite FTS5 index from the JSONL when the files change.

Ported from claude-mem (c10vis-poem/NvAEx-claude-mem, src/services/sqlite/SessionStore.ts 1311-1342 and
SessionSearch.ts 286-321): the observations and session_summaries columns, FTS5 search, and the three-step search
(search -> timeline -> get_observations). Not ported: the observer model, sync, telemetry, accounts, the viewer.
"""
import hashlib, json, os, re, sqlite3, time

HOME = os.path.expanduser("~")
SHARED = os.path.expanduser(os.environ.get(
    "DUMBASS_SHARED_DIR", "/storage/emulated/0/Documents/NovAExorpus/05_episodic_logs/observations"))
INDEX = os.path.join(os.path.expanduser(os.environ.get("DUMBASS_DATA_DIR", "~/.nvaex/memory")), "observations_index.db")
TYPES = ("decision", "fact", "finding", "bugfix", "discovery", "change", "plan", "question", "summary")
OBS_FIELDS = ("title", "subtitle", "narrative", "text", "facts", "concepts")
SUM_FIELDS = ("request", "investigated", "learned", "completed", "next_steps", "notes")
SECRET = re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"
                    r"|\b(?:sk|pk|rk|ghp|gho|ghs|github_pat|glpat|xox[abeprs]|AKIA|AIza|hf)[-_A-Za-z0-9]{16,}"
                    r"|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"
                    r"|(?i:\b(?:password|passwd|secret|token|api[_-]?key|private[_-]?key)\s*[:=]\s*\S+)"
                    r"|<private>.*?</private>)", re.S)


def redact(s):
    return SECRET.sub("[REDACTED]", s) if isinstance(s, str) else s


def project_file(project):
    return os.path.join(SHARED, re.sub(r"[^A-Za-z0-9._-]+", "_", project) + ".jsonl")


def now():
    t = time.time()
    return t, time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t))


def as_list(v):
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


# ---- local index, rebuilt from the shared JSONL whenever a file changed ----------------------
def index():
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    c = sqlite3.connect(INDEX, timeout=5)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS obs(id TEXT PRIMARY KEY, kind TEXT, project TEXT, session TEXT, type TEXT,
        created_at TEXT, epoch REAL, title TEXT, subtitle TEXT, narrative TEXT, text TEXT, facts TEXT,
        concepts TEXT, files TEXT, source TEXT, raw TEXT);
    CREATE INDEX IF NOT EXISTS obs_proj ON obs(project, epoch);
    CREATE VIRTUAL TABLE IF NOT EXISTS obs_fts USING fts5(id UNINDEXED, title, subtitle, narrative, text, facts,
        concepts, tokenize='porter unicode61');
    CREATE TABLE IF NOT EXISTS files_seen(path TEXT PRIMARY KEY, mtime REAL, size INTEGER);
    """)
    sync(c)
    return c


def sync(c):
    if not os.path.isdir(SHARED):
        return
    for name in sorted(os.listdir(SHARED)):
        if not name.endswith(".jsonl"):
            continue
        p = os.path.join(SHARED, name)
        st = os.stat(p)
        row = c.execute("SELECT mtime,size FROM files_seen WHERE path=?", (p,)).fetchone()
        if row and row["mtime"] == st.st_mtime and row["size"] == st.st_size:
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        put(c, json.loads(line))
                    except ValueError:
                        continue  # a torn line from a concurrent write: the next sync reads it whole
        c.execute("INSERT OR REPLACE INTO files_seen VALUES(?,?,?)", (p, st.st_mtime, st.st_size))
    c.commit()


def put(c, r):
    if c.execute("SELECT 1 FROM obs WHERE id=?", (r["id"],)).fetchone():
        return False
    v = {k: r.get(k) for k in OBS_FIELDS}
    v["facts"] = "\n".join(as_list(r.get("facts")))
    v["concepts"] = ", ".join(as_list(r.get("concepts")))
    if r.get("kind") == "summary":  # a session summary is searched through the same index
        v["title"] = "Session summary: " + (r.get("request") or "")[:120]
        v["narrative"] = "\n".join("%s: %s" % (k, r.get(k)) for k in SUM_FIELDS if r.get(k))
    c.execute("INSERT INTO obs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (r["id"], r.get("kind", "observation"), r.get("project"), r.get("session"), r.get("type"),
               r.get("created_at"), r.get("epoch"), v["title"], v.get("subtitle"), v.get("narrative"),
               v.get("text"), v["facts"], v["concepts"], ", ".join(as_list(r.get("files"))), r.get("source"),
               json.dumps(r)))
    c.execute("INSERT INTO obs_fts VALUES(?,?,?,?,?,?,?)",
              (r["id"], v["title"], v.get("subtitle"), v.get("narrative"), v.get("text"), v["facts"], v["concepts"]))
    return True


def append(record):
    """Write one record to its project's JSONL (the source of truth), then to the local index."""
    body = {k: v for k, v in record.items() if k not in ("id", "created_at", "epoch")}
    record["id"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    c = index()
    if c.execute("SELECT 1 FROM obs WHERE id=?", (record["id"],)).fetchone():
        return {"id": record["id"], "saved": False, "reason": "same content already stored"}
    os.makedirs(SHARED, exist_ok=True)
    p = project_file(record["project"])
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    put(c, record)
    st = os.stat(p)
    c.execute("INSERT OR REPLACE INTO files_seen VALUES(?,?,?)", (p, st.st_mtime, st.st_size))
    c.commit()
    return {"id": record["id"], "saved": True, "file": p}


# ---- tools (claude-mem's names and three-step search) -----------------------------------------
def t_save(a):
    """save_memory / observation_add."""
    if not (a.get("title") or a.get("text") or a.get("narrative")):
        raise ValueError("give title, text or narrative")
    typ = a.get("type", "finding")
    if typ not in TYPES:
        raise ValueError("type must be one of " + ", ".join(TYPES))
    epoch, iso = now()
    rec = {"kind": "observation", "project": a.get("project") or "default", "session": a.get("session"),
           "type": typ, "created_at": iso, "epoch": epoch, "source": a.get("source", "")}
    for k in ("title", "subtitle", "narrative", "text"):
        if a.get(k):
            rec[k] = redact(a[k])
    for k in ("facts", "concepts", "files"):
        if a.get(k):
            rec[k] = [redact(x) for x in as_list(a[k])]
    return append(rec)


def t_summary(a):
    """session_summaries: what the session asked, looked at, learned, finished and left next."""
    epoch, iso = now()
    rec = {"kind": "summary", "project": a.get("project") or "default", "session": a.get("session"),
           "type": "summary", "created_at": iso, "epoch": epoch}
    for k in SUM_FIELDS:
        if a.get(k):
            rec[k] = redact(a[k])
    for k in ("files_read", "files_edited"):
        if a.get(k):
            rec[k] = as_list(a[k])
    return append(rec)


def fts_query(q):
    words = re.findall(r"[\w.-]+", q)
    return " OR ".join('"%s"' % w.replace('"', "") for w in words) if words else '""'


def row_index(r):
    return {"id": r["id"][:12], "type": r["type"], "project": r["project"], "created_at": r["created_at"],
            "title": r["title"] or (r["text"] or r["narrative"] or "")[:100]}


def t_search(a):
    """Step 1: a compact index (id, type, date, title) for a full-text query."""
    c, lim = index(), int(a.get("limit", 20))
    where, args = [], []
    if a.get("project"):
        where.append("o.project=?"); args.append(a["project"])
    if a.get("type"):
        where.append("o.type=?"); args.append(a["type"])
    if a.get("since"):
        where.append("o.created_at>=?"); args.append(a["since"])
    sql = ("SELECT o.* FROM obs_fts f JOIN obs o ON o.id=f.id WHERE obs_fts MATCH ?"
           + "".join(" AND " + w for w in where) + " ORDER BY bm25(obs_fts) LIMIT ?")
    rows = c.execute(sql, [fts_query(a["query"])] + args + [lim]).fetchall()
    return {"results": [row_index(r) for r in rows], "count": len(rows),
            "next": "timeline(id) for context, get_observations(ids) for full records"}


def resolve(c, short):
    r = c.execute("SELECT * FROM obs WHERE id LIKE ? LIMIT 2", (short + "%",)).fetchall()
    if len(r) != 1:
        raise ValueError("id %r matches %d records" % (short, len(r)))
    return r[0]


def t_timeline(a):
    """Step 2: what happened around one observation, in time order, same project."""
    c, n = index(), int(a.get("around", 5))
    if a.get("id"):
        mid = resolve(c, a["id"])
    else:
        hits = t_search({"query": a["query"], "project": a.get("project"), "limit": 1})["results"]
        if not hits:
            return {"timeline": []}
        mid = resolve(c, hits[0]["id"])
    before = c.execute("SELECT * FROM obs WHERE project=? AND epoch<? ORDER BY epoch DESC LIMIT ?",
                       (mid["project"], mid["epoch"], n)).fetchall()
    after = c.execute("SELECT * FROM obs WHERE project=? AND epoch>? ORDER BY epoch LIMIT ?",
                      (mid["project"], mid["epoch"], n)).fetchall()
    return {"timeline": [row_index(r) for r in reversed(before)] + [dict(row_index(mid), anchor=True)]
            + [row_index(r) for r in after]}


def t_get(a):
    """Step 3: full records for the ids picked from search or timeline."""
    c = index()
    return {"observations": [json.loads(resolve(c, i)["raw"]) for i in as_list(a["ids"])]}


def t_context(a):
    """The compact index a session starts with: the project's newest observations and its last summary."""
    c, lim = index(), int(a.get("limit", 25))
    proj = a.get("project") or "default"
    rows = c.execute("SELECT * FROM obs WHERE project=? AND kind='observation' ORDER BY epoch DESC LIMIT ?",
                     (proj, lim)).fetchall()
    last = c.execute("SELECT raw FROM obs WHERE project=? AND kind='summary' ORDER BY epoch DESC LIMIT 1",
                     (proj,)).fetchone()
    total = c.execute("SELECT count(*) FROM obs WHERE project=?", (proj,)).fetchone()[0]
    return {"project": proj, "stored": total, "recent": [row_index(r) for r in rows],
            "last_summary": json.loads(last["raw"]) if last else None, "source_of_truth": project_file(proj)}


S = {"type": "string"}
L = {"type": "array", "items": S}
TOOLS = {
    "memory.save": (t_save, "Save an observation (claude-mem save_memory): a decision, fact, finding, bugfix, "
                    "discovery, change, plan or question, with facts, concepts and files. Written to the project's "
                    "JSONL in the vault (git: every device sees it) and indexed for search. Secrets are redacted.",
                    {"title": S, "subtitle": S, "narrative": S, "text": S, "type": {"type": "string", "enum": list(TYPES)},
                     "facts": L, "concepts": L, "files": L, "project": S, "session": S, "source": S}, []),
    "memory.session_summary": (t_summary, "Save a session summary (claude-mem session_summaries): request, "
                               "investigated, learned, completed, next_steps, notes, files_read, files_edited.",
                               {"request": S, "investigated": S, "learned": S, "completed": S, "next_steps": S,
                                "notes": S, "files_read": L, "files_edited": L, "project": S, "session": S}, []),
    "memory.search": (t_search, "Step 1 of 3: full-text search over saved observations and summaries; returns a "
                      "compact index (id, type, date, title). Filters: project, type, since (ISO date).",
                      {"query": S, "project": S, "type": S, "since": S, "limit": {"type": "integer"}}, ["query"]),
    "memory.timeline": (t_timeline, "Step 2 of 3: observations before and after one id (or the best match for "
                        "query) in the same project, in time order.",
                        {"id": S, "query": S, "project": S, "around": {"type": "integer"}}, []),
    "memory.get_observations": (t_get, "Step 3 of 3: full records for ids from search or timeline (batch them).",
                                {"ids": L}, ["ids"]),
    "memory.session_context": (t_context, "What a new session should start with for a project: newest "
                               "observations (index only) and the last session summary.",
                               {"project": S, "limit": {"type": "integer"}}, []),
}
