#!/usr/bin/env python3
"""jev-rea-mcp: stdlib stdio MCP server, 4 meta-tools. Newline-delimited JSON-RPC."""
import csv, json, os, re, sys, time, urllib.request, uuid

NAME, VERSION, PROTO = "jev-rea-mcp", "0.1.0", "2024-11-05"
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
JOBS = os.environ.get("JEV_JOBS_DIR") or os.path.join(HOME, ".claude/state/jev-rea-mcp/jobs")
CSV_PATH = os.environ.get("JEV_TAXONOMY_CSV") or os.path.join(HERE, "data/taxonomy.csv")
BRIDGE = os.environ.get("JEV_AG_BRIDGE_URL", "")

GROUPS = {  # keyword -> domain group (built-in rules)
    "build": r"\b(implement|build|code|refactor|fix|bug|test|compile|apk|gradle|script)\b",
    "research": r"\b(research|compare|find out|investigate|survey|look up)\b",
    "memory": r"\b(memory|remember|recap|resume|handoff|claim)\b",
    "wiki": r"\b(wiki|vault|corpus|ingest|note|obsidian|markdown)\b",
    "device": r"\b(termux|android|adb|npu|device|phone|install)\b",
    "review": r"\b(review|audit|verify|lint|diff|pr)\b",
    "plan": r"\b(plan|design|architecture|spec|roadmap)\b",
}
L3 = r"\b(delete|rm -rf|force.?push|drop table|migrate|production|deploy|cross.?repo|all repos|irreversible|rewrite history|secrets?)\b"
L2 = r"\b(and then|multi|several|each|every|across|pipeline|refactor|migrate|audit|ingest|harvest)\b"

def route(task):
    t = task.lower()
    src, level, why = "built-in", None, []
    hit = taxonomy_match(t)
    if hit:
        level, src = hit[0], "csv:" + hit[1]
    if level is None:
        n = len(t.split())
        if re.search(L3, t): level, why = 3, ["irreversible/cross-repo keyword"]
        elif re.search(L2, t) or n > 40: level, why = 2, ["multi-step keyword or long task"]
        elif n > 8: level, why = 1, ["single bounded task"]
        else: level, why = 0, ["short/trivial"]
    groups = [g for g, rx in GROUPS.items() if re.search(rx, t)][:3]
    return {"level": level, "source": src, "groups": groups,
            "rules": ["L0 inline", "L1 one skill", "L2 run audit_gate 1-5 + isolated subagents",
                      "L3 L2 plus operator confirmation before destructive steps"][level],
            "why": why, "taxonomy_csv_loaded": os.path.isfile(CSV_PATH)}

_tax = None
def taxonomy_match(t):
    global _tax
    if _tax is None:
        _tax = []
        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                rd = csv.DictReader(f)
                cols = rd.fieldnames or []
                lc = next((c for c in cols if "level" in c.lower()), None)
                tc = next((c for c in cols if re.search("task|example|desc|pattern", c.lower())), None)
                for r in rd if lc and tc else []:
                    m = re.search(r"[0-3]", r[lc] or "")
                    w = set(re.findall(r"[a-z]{4,}", (r[tc] or "").lower()))
                    if m and w: _tax.append((int(m.group()), w, (r[tc] or "")[:40]))
        except OSError:
            pass
    best = None
    words = set(re.findall(r"[a-z]{4,}", t))
    for lvl, w, label in _tax:
        s = len(w & words) / len(w)
        if s >= 0.4 and (best is None or s > best[0]): best = (s, lvl, label)
    return (best[1], best[2]) if best else None

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
    ("jev.route_task", "Classify a task into JEV level L0-L3 and domain groups (taxonomy CSV if present, else built-in rules).",
     {**S(task={"type": "string"}), "required": ["task"]}, lambda a: route(a["task"])),
    ("jev.audit_gate", "5-gate task audit checklist (non-blocking). Pass evidence to see which fields are still missing.",
     S(gate={"type": ["string", "integer"], "description": "1-5 or all"}, evidence={"type": "object"}),
     lambda a: audit(a.get("gate"), a.get("evidence") or {})),
    ("rea.inspect_target", "Read-only inspection of a repo/dir: extensions, manifests, entrypoints, sensitive-looking files.",
     {**S(path={"type": "string"}), "required": ["path"]}, lambda a: inspect(a["path"])),
    ("ag.cloud_dispatch", "Write a job file for cloud work. Only POSTs if JEV_AG_BRIDGE_URL is set AND send=true.",
     {**S(job={"type": "string"}, payload={"type": "object"}, target={"type": "string"}, send={"type": "boolean"}), "required": ["job"]},
     lambda a: dispatch(a["job"], a.get("payload"), a.get("target"), bool(a.get("send")))),
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
