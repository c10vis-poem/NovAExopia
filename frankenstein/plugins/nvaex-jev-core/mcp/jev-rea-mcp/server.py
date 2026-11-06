#!/usr/bin/env python3
"""jev-rea-mcp: stdlib stdio MCP server, 5 tools. Newline-delimited JSON-RPC."""
import json, os, re, sys, time, urllib.request, uuid

NAME, VERSION, PROTO = "jev-rea-mcp", "0.2.0", "2024-11-05"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../../scripts")))
import jev_route  # the one router, shared with the hook
HOME = os.path.expanduser("~")
JOBS = os.environ.get("JEV_JOBS_DIR") or os.path.join(HOME, ".claude/state/jev-rea-mcp/jobs")
BRIDGE = os.environ.get("JEV_AG_BRIDGE_URL", "")
ROUTE_TIMEOUT = 6.0  # a tool call can wait longer than a per-prompt hook

# ---- jev.remember: local project memory (replaces the jevmem CLI; no network, no key) ----
MEM_FILE = "memory.jsonl"
MAX_TEXT, MAX_TAGS = 2000, 12

def mem_dir():
    """Resolved at call time, never at import: $JEV_MEMORY_DIR (~ expanded), else ~/.nvaex/jev-memory."""
    d = os.environ.get("JEV_MEMORY_DIR") or "~/.nvaex/jev-memory"
    return os.path.abspath(os.path.expanduser(os.path.expandvars(d)))

def mem_read(path):
    recs, bad = [], 0
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    r = json.loads(line)
                    if isinstance(r, dict) and r.get("text"): recs.append(r)
                    else: bad += 1
                except ValueError: bad += 1
    except FileNotFoundError:
        pass
    return recs, bad

def _words(s): return set(re.findall(r"[a-z0-9]{2,}", s.lower()))

def remember(a):
    action = (a.get("action") or "").lower()
    d = mem_dir(); path = os.path.join(d, MEM_FILE)
    project = (a.get("project") or "").strip() or None
    if action == "add":
        text = (a.get("text") or "").strip()
        if not text: return {"error": "add needs non-empty text"}
        text, nred = jev_route.SECRET.subn("[REDACTED]", text)
        text = text[:MAX_TEXT]
        tags = sorted({str(t).strip().lower() for t in (a.get("tags") or []) if str(t).strip()})[:MAX_TAGS]
        recs, _ = mem_read(path)
        for r in recs:
            if r["text"] == text and r.get("project") == project:
                return {"stored": False, "duplicate": True, "id": r.get("id"), "path": path}
        rec = {"id": uuid.uuid4().hex[:8], "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "project": project, "tags": tags, "text": text}
        os.makedirs(d, mode=0o700, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try: os.write(fd, (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
        finally: os.close(fd)
        return {"stored": True, "id": rec["id"], "redacted": nred, "path": path}
    if action == "recall":
        q = _words(a.get("query") or "")
        want = {str(t).strip().lower() for t in (a.get("tags") or []) if str(t).strip()}
        try: limit = max(1, min(50, int(a.get("limit") or 5)))
        except (TypeError, ValueError): limit = 5
        recs, bad = mem_read(path)
        scored = []
        for i, r in enumerate(recs):
            if project and r.get("project") != project: continue
            tg = set(r.get("tags") or [])
            if want and not (want & tg): continue
            s = len(q & _words(r["text"])) + 2 * len(q & tg)
            if q and s == 0: continue
            scored.append((s, i, r))
        scored.sort(key=lambda x: (-x[0], -x[1]))  # score, then newest first
        return {"count": len(scored), "returned": min(limit, len(scored)), "skipped_bad_lines": bad, "path": path,
                "memories": [{"id": r["id"], "created": r.get("created"), "project": r.get("project"),
                              "tags": r.get("tags", []), "text": r["text"]} for _, _, r in scored[:limit]]}
    return {"error": "action must be 'add' or 'recall'"}

GATES = {
    1: ("Pre-execution spec", ["goal", "files_in_scope", "done_test"]),
    2: ("Dry run", ["commands", "effects"]),
    3: ("Execution health", ["tool_calls", "repeats"]),
    4: ("Post-execution verification", ["command", "output"]),
    5: ("Handoff audit", ["claims", "sources", "not_checked"]),
}
def audit(gate, evidence):
    out = []
    for g in (range(1, 6) if gate in (None, "all") else [int(gate)]):
        title, need = GATES[g]
        missing = [k for k in need if not evidence.get(str(g), evidence).get(k)] if evidence else need
        out.append({"gate": g, "title": title, "need": need, "missing": missing,
                    "status": "pass" if not missing else "incomplete"})
    return {"gates": out, "blocking": False,
            "note": "Checklist only; never blocks. Missing fields are what the agent still owes."}

SKIP = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".gradle"}
MANIFESTS = ["package.json", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod", "build.gradle",
             "build.gradle.kts", "AndroidManifest.xml", "Makefile", "Dockerfile", "plugin.json", "SKILL.md", "server.json"]
def inspect(path, max_files=5000):
    root = os.path.realpath(os.path.expanduser(path))
    if not os.path.isdir(root): return {"error": "not a directory: " + root}
    exts, manifests, entry, flags, n = {}, [], [], [], 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            n += 1
            if n > max_files: break
            rel = os.path.relpath(os.path.join(d, f), root)
            e = os.path.splitext(f)[1].lower() or f
            exts[e] = exts.get(e, 0) + 1
            if f in MANIFESTS and rel.count(os.sep) <= 2: manifests.append(rel)
            if re.match(r"(main|index|server|cli|app)\.\w+$", f) and rel.count(os.sep) <= 2: entry.append(rel)
            if re.search(r"(\.env|id_rsa|\.pem|secret|credential)", f.lower()): flags.append(rel)
        if n > max_files: break
    head = ""
    for r in ("README.md", "readme.md"):
        try:
            head = open(os.path.join(root, r), encoding="utf-8", errors="replace").read(600); break
        except OSError: pass
    git = None
    try: git = open(os.path.join(root, ".git/HEAD")).read().strip()
    except OSError: pass
    return {"path": root, "files_scanned": min(n, max_files), "truncated": n > max_files,
            "top_extensions": dict(sorted(exts.items(), key=lambda kv: -kv[1])[:10]),
            "manifests": manifests[:20], "entrypoints": entry[:20], "sensitive_looking_files": flags[:20],
            "git_head": git, "readme_head": head, "read_only": True}

def dispatch(job, payload, target, send):
    os.makedirs(JOBS, exist_ok=True)
    jid = time.strftime("%Y%m%dT%H%M%S-") + uuid.uuid4().hex[:6]
    rec = {"id": jid, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "job": job,
           "target": target or "antigravity", "payload": payload, "sent": False}
    p = os.path.join(JOBS, jid + ".json")
    with open(p, "w") as f: json.dump(rec, f, indent=1)
    res = {"job_file": p, "sent": False, "bridge_configured": bool(BRIDGE)}
    if send and BRIDGE:
        try:
            rq = urllib.request.Request(BRIDGE, json.dumps(rec).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(rq, timeout=15) as r: res.update(sent=True, http=r.status)
        except Exception as e:
            res["send_error"] = str(e)
    elif send:
        res["note"] = "send requested but JEV_AG_BRIDGE_URL not set; job file only"
    return res

S = lambda **p: {"type": "object", "properties": p}
TOOLS = [
    ("jev.route_task", "Classify a task into JEV level L0-L3, domain groups and model tier with TypeSafe Jev; keyword rules if Jev is unavailable. source says which (typesafe or local-fallback), error says why.",
     {**S(task={"type": "string"}), "required": ["task"]}, lambda a: jev_route.classify(a["task"], ROUTE_TIMEOUT)),
    ("jev.audit_gate", "5-gate task audit checklist (non-blocking). Pass evidence to see which fields are still missing.",
     S(gate={"type": ["string", "integer"], "description": "1-5 or all"}, evidence={"type": "object"}),
     lambda a: audit(a.get("gate"), a.get("evidence") or {})),
    ("rea.inspect_target", "Read-only inspection of a repo/dir: extensions, manifests, entrypoints, sensitive-looking files.",
     {**S(path={"type": "string"}), "required": ["path"]}, lambda a: inspect(a["path"])),
    ("ag.cloud_dispatch", "Write a job file for cloud work. Only POSTs if JEV_AG_BRIDGE_URL is set AND send=true.",
     {**S(job={"type": "string"}, payload={"type": "object"}, target={"type": "string"}, send={"type": "boolean"}), "required": ["job"]},
     lambda a: dispatch(a["job"], a.get("payload"), a.get("target"), bool(a.get("send")))),
    ("jev.remember", "Local project memory (no network). action=add stores text with optional tags/project; action=recall returns the best matches for query/tags/project. Data dir: $JEV_MEMORY_DIR, default ~/.nvaex/jev-memory.",
     {**S(action={"type": "string", "enum": ["add", "recall"]}, text={"type": "string", "description": "add: the memory (max 2000 chars; secret shapes are redacted)"},
          tags={"type": "array", "items": {"type": "string"}}, project={"type": "string", "description": "optional scope; recall filters to it when given"},
          query={"type": "string", "description": "recall: words to match"}, limit={"type": "integer", "description": "recall: 1-50, default 5"}),
      "required": ["action"]}, remember),
]
BY = {t[0]: t for t in TOOLS}

def handle(m):
    meth, i = m.get("method"), m.get("id")
    if i is None: return None  # notification
    if meth == "initialize":
        r = {"protocolVersion": PROTO, "capabilities": {"tools": {}}, "serverInfo": {"name": NAME, "version": VERSION}}
    elif meth == "tools/list":
        r = {"tools": [{"name": n, "description": d, "inputSchema": s} for n, d, s, _ in TOOLS]}
    elif meth == "tools/call":
        p = m.get("params") or {}
        t = BY.get(p.get("name"))
        if not t: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32602, "message": "unknown tool"}}
        try:
            res, err = t[3](p.get("arguments") or {}), False
        except Exception as e:
            res, err = {"error": "%s: %s" % (type(e).__name__, e)}, True
        r = {"content": [{"type": "text", "text": json.dumps(res, indent=1)}], "isError": err}
    elif meth == "ping": r = {}
    else: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": i, "result": r}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: out = handle(json.loads(line))
        except json.JSONDecodeError: out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        if out: sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()

if __name__ == "__main__": main()
