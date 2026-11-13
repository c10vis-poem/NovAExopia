#!/usr/bin/env python3
"""The one JEV router. The UserPromptSubmit hook (route.py) and jev.route_task (mcp/jev-rea-mcp/server.py) both call classify().

TypeSafe Jev decides the level (a Score) and the domain group (a Choice). The keyword rules below are the fallback when
there is no key, no network or an error. Every result names its source and, on fallback, the reason. Stdlib only.
Run it by hand: python3 scripts/jev_route.py "task text"
"""
import csv, glob, json, os, re, sys, threading, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER = os.path.join(ROOT, "skills/jev-router")

# ---- questions, thresholds and limits (what a human reviews and tunes) ----
BASE_URL, API_PATH, MODEL = "https://api.typesafe.ai", "/v1/systemone", "jev-latest"
HOOK_TIMEOUT = 2.0    # seconds, hard deadline; the hook entry allows 5
MAX_TASK = 8000       # characters sent off the phone: head 60%, tail 40%
LEVEL_CONF, GROUP_CONF = 0.65, 0.75  # below either: gated "escalate" (same gates as claude-jev)
SECOND_GROUP = 0.25   # a further option above this also counts as a group (TypeSafe's two-category rule)
FITS_MIN = 0.35       # companion Noul "does any option fit": below this, none does (semantic_find cookbook)
SKILL_GATE = 0.30     # "does any skill apply" below this: no skill (skill_suggestion cookbook)
SKILL_FLOOR = 0.10    # a skill above this share of its Choice counts. A share, never a count: nothing caps how many load
L3_RISK = 0.30        # chance of L3 at or above this holds L3, so a mode of L2 cannot hide real L3 mass
CHOICE_MAX = 240      # one Choice is reliable to about 240 options (API max 255); a longer roster splits, still one request
CONFIG_FAULTS = {"http-401", "http-403", "http-422"}  # our setup is wrong, not "Jev unsure": a tool gate must fail closed on these
LEVEL_Q = {
    "type": "score",
    "instructions": "`task` is a request sent to a coding agent. Which level describes the work that `task` asks for?",
    "criteria": [
        "A quick question or lookup, answered in one reply with nothing changed.",
        "One bounded job with one outcome, such as one edit, one command or one focused answer.",
        "A job of several dependent steps or many files, which needs a plan and checks along the way.",
        "Work that cannot be undone or that spans several repositories, such as deleting data, force pushing, deploying or migrating.",
    ],
}
GROUP_Q_TEXT = "`task` is a request sent to a coding agent. Which kind of work does `task` mainly ask for?"
ANY_GROUP_Q = {"type": "noul", "instructions": "`task` is a request sent to a coding agent. Does `task` ask for software or agent work, not just small talk or a general question unrelated to this work?"}
SKILL_Q_TEXT = "`task` is a request sent to a coding agent. Which skill would help most with `task`?"
ANY_SKILL_Q = {"type": "noul", "instructions": "`task` is a request sent to a coding agent. Would a written procedure or specialist skill help the agent carry out `task`?"}
RULES = ["L0 inline", "L1 one skill", "L2 run audit_gate 1-5 + isolated subagents",
         "L3 L2 plus operator confirmation before destructive steps"]

# ---- local rules ----
L3 = r"\b(delete|rm -rf|force.?push|drop table|migrate|production|deploy|cross.?repo|all repos|irreversible|rewrite history|secrets?)\b"
L2 = r"\b(and then|multi|several|each|every|across|pipeline|refactor|migrate|audit|ingest|harvest)\b"
# Exact destructive shapes: these hold L3 whatever Jev says. Jev may make this stricter, never looser.
HARD_L3 = r"\b(rm -rf|force.?push|drop table|rewrite history|all repos|cross.?repo)\b"
STEPS = r"\b(and then|then|also|after that|finally)\b"

# ---- redaction ----
SECRET = re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"
                    r"|\b(?:sk|pk|rk|ghp|gho|ghu|ghs|ghr|github_pat|glpat|xox[abeprs]|AKIA|ASIA|AIza|hf|npm)[-_A-Za-z0-9]{16,}"
                    r"|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"
                    r"|(?i:\bbearer\s+[A-Za-z0-9._~+/=-]{8,})"
                    r"|(?i:\b[A-Za-z0-9_-]*(?:password|passwd|pwd|passphrase|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)"
                    r"[A-Za-z0-9_-]*[\"']?\s*[:=]\s*[\"']?[^\s\"',;]+)"
                    r"|(?<=://)[^\s/:@]+:[^\s/@]+(?=@))", re.S)
# Off the phone, also drop what is only personal or opaque: email addresses and long mixed tokens.
OUTBOUND = re.compile(r"(\b[\w.+-]+@[\w-]+\.[\w.-]+\b"
                      r"|\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,}\b)")

def redact_outbound(text):
    text, a = SECRET.subn("[REDACTED]", text)
    text, b = OUTBOUND.subn("[REDACTED]", text)
    return text, a + b

def truncate(text, limit=MAX_TASK):
    if len(text) <= limit:
        return text
    head = int(limit * 0.6)
    return text[:head] + "\n...[truncated %d chars]...\n" % (len(text) - limit) + text[head - limit:]

# ---- files ----
def load_groups():
    try:
        with open(os.path.join(ROUTER, "groups.json"), encoding="utf-8") as f:
            return json.load(f)["groups"]
    except (OSError, ValueError, KeyError):
        return {}

def load_index():
    """{skill id: purpose} from every package's generated skills.json: this package, its siblings in the build tree or
    the plugin cache, or the os.pathsep list in JEV_SKILLS_INDEX. Lives outside the model's context; only Jev reads it."""
    env = os.environ.get("JEV_SKILLS_INDEX")
    if env is not None:
        paths = env.split(os.pathsep)
    else:
        paths = [os.path.join(ROOT, "skills.json")]
        for pat in ("../*/skills.json", "../../mcp/*/skills.json", "../../*/*/skills.json"):
            paths += glob.glob(os.path.join(ROOT, pat))
    out, seen = {}, set()
    for p in paths:
        real = os.path.realpath(p)
        if real in seen:
            continue
        seen.add(real)
        try:
            with open(real, encoding="utf-8") as f:
                for row in json.load(f)["skills"]:
                    out.setdefault(row["id"], row.get("purpose") or None)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return out

def tier_for(level, groups):
    """Model tier for a level + task types, from tiers.json (or JEV_TIERS_JSON). None if the file is absent or bad."""
    try:
        path = os.environ.get("JEV_TIERS_JSON") or os.path.join(ROUTER, "tiers.json")
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            T = json.load(f)
        order = T["order"]
        t = T["levels"]["L%d" % level]["tier"]
        if level > 0:
            for g in groups:
                m = T["task_types_min"].get(g)
                if m in order and order.index(m) > order.index(t):
                    t = m
        return {"tier": t, "model": T["tiers"][t]["model"]}
    except (OSError, ValueError, KeyError, TypeError):
        return None

def csv_path():
    return os.environ.get("JEV_TAXONOMY_CSV") or os.path.join(ROUTER, "taxonomy.csv")

_tax = None
def taxonomy_match(t):
    global _tax
    if _tax is None:
        _tax = []
        try:
            with open(csv_path(), newline="", encoding="utf-8") as f:
                rd = csv.DictReader(f)
                cols = rd.fieldnames or []
                lc = next((c for c in cols if "level" in c.lower()), None)
                tc = next((c for c in cols if re.search("task|example|desc|pattern", c.lower())), None)
                for r in rd if lc and tc else []:
                    m = re.search(r"[0-3]", r[lc] or "")
                    w = set(re.findall(r"[a-z]{4,}", (r[tc] or "").lower()))
                    if m and w:
                        _tax.append((int(m.group()), w, (r[tc] or "")[:40]))
        except OSError:
            pass
    best = None
    words = set(re.findall(r"[a-z]{4,}", t))
    for lvl, w, label in _tax:
        s = len(w & words) / len(w)
        if s >= 0.4 and (best is None or s > best[0]):
            best = (s, lvl, label)
    return (best[1], best[2]) if best else None

# ---- fallback: keyword rules ----
def local_route(text, groups):
    """(level, groups, rule, why). Taxonomy CSV if present, else keyword and length rules."""
    low = text.lower()
    words = set(re.findall(r"[a-z0-9]+", low))
    hits = sorted(((len(words & set(g.get("kw", []))), n) for n, g in groups.items()), reverse=True)
    top = [n for c, n in hits if c]
    hit = taxonomy_match(low)
    if hit:
        return hit[0], top, "csv:" + hit[1], []
    if re.search(L3, low):
        return 3, top, "keywords", ["irreversible/cross-repo keyword"]
    n, steps = len(text), len(re.findall(STEPS, low))
    level = 0 if n < 60 and not top else 1 if n < 200 and steps == 0 else 2 if n < 600 else 3
    if level < 2 and re.search(L2, low):
        return 2, top, "keywords", ["multi-step keyword"]
    return level, top, "keywords", [["short/trivial", "single bounded task", "several steps or long task", "very long task"][level]]

# ---- TypeSafe Jev ----
class Fallback(Exception):
    """Why Jev was not used. The reason is a fixed short code, never exception text: that can quote the key."""
    def __init__(self, reason, request_id=None):
        super().__init__(reason)
        self.reason, self.request_id = reason, request_id

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # urllib would resend the Authorization header to the new host
        return None

def api_key():
    for n in ("TYPESAFE_API_KEY", "CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY"):
        v = os.environ.get(n, "").strip()
        if v and "${" not in v:
            return v
    # HOLES-B 2b (a5b45d30, 2026-11-12): only ~/bin/crane exported the key (from nvaex-secret), so any other launch
    # (plain claude, the shims, AGY) routed with local-fallback (no-key). The router asks the secret store itself.
    cmd = os.environ.get("NVAEX_SECRET_CMD") or os.path.expanduser("~/bin/nvaex-secret")
    if not os.access(cmd, os.X_OK):
        return ""
    import subprocess
    try:
        r = subprocess.run([cmd, "get", "TYPESAFE_API_KEY"], capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.SubprocessError):
        return ""
    v = r.stdout.strip() if r.returncode == 0 else ""
    return v if v and "${" not in v else ""

def endpoint():
    base = (os.environ.get("TYPESAFE_BASE_URL") or BASE_URL).rstrip("/")
    u = urllib.parse.urlsplit(base)
    if u.scheme == "https" or (u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost")):
        return base + API_PATH
    raise Fallback("bad-base-url")  # the key never goes out in clear text

def questions(groups, index=None):
    """All in one request: questions are independent and extra ones cost next to nothing. A Choice always picks
    something, so each has a companion Noul that says whether anything fits (vendor: not a "none" option)."""
    q = {"level": LEVEL_Q, "any_group": ANY_GROUP_Q,
         "group": {"type": "choice", "instructions": GROUP_Q_TEXT, "criteria": {n: g.get("desc") for n, g in groups.items()}}}
    ids = sorted(index or {})
    if ids:
        q["any_skill"] = ANY_SKILL_Q
        for i in range(0, len(ids), CHOICE_MAX):
            chunk = ids[i:i + CHOICE_MAX]
            if len(chunk) >= 2:
                q["skill_%d" % (i // CHOICE_MAX)] = {"type": "choice", "instructions": SKILL_Q_TEXT,
                                                       "criteria": {s: index[s] for s in chunk}}
    return q

def backoff_path():
    return os.path.expanduser("~/.claude/state/nvaex-jev-core/backoff")

def note_backoff(headers):
    """429/529 with a Retry-After: skip Jev until it passes, since the next prompt would otherwise call again at once."""
    try:
        ms = headers.get("retry-after-ms")
        wait = float(ms) / 1000 if ms else float(headers.get("Retry-After"))
    except (TypeError, ValueError):
        return
    try:
        os.makedirs(os.path.dirname(backoff_path()), exist_ok=True)
        with open(backoff_path(), "w", encoding="utf-8") as f:
            f.write(str(time.time() + min(max(wait, 0), 60)))
    except OSError:
        pass

def backing_off():
    try:
        with open(backoff_path(), encoding="utf-8") as f:
            return time.time() < float(f.read())
    except (OSError, ValueError):
        return False

def post(body, key, timeout):
    """POST with a hard deadline. The worker thread also covers DNS, which urllib's timeout does not."""
    req = urllib.request.Request(endpoint(), data=body, method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    box = {}
    def call():
        try:
            with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as r:
                box["data"] = r.read(1 << 20)
                box["rid"] = r.headers.get("x-typesafe-request-id")
        except urllib.error.HTTPError as e:
            box["err"] = "http-%d" % e.code
            box["rid"] = e.headers.get("x-typesafe-request-id")
            if e.code in (429, 529):
                note_backoff(e.headers)
        except TimeoutError:
            box["err"] = "timeout"
        except urllib.error.URLError as e:
            box["err"] = "timeout" if isinstance(e.reason, TimeoutError) else "network"
        except Exception as e:
            box["err"] = "error-" + type(e).__name__
    t = threading.Thread(target=call, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise Fallback("timeout")
    if "err" in box:
        raise Fallback(box["err"], box.get("rid"))
    return box["data"], box.get("rid")

def pick_skills(answers, index):
    """Every skill Jev gives a real share to, best first. No count limit."""
    if not index or float(answers["any_skill"]["noul"]) < SKILL_GATE:
        return []
    scored = {}
    for name, a in answers.items():
        if name.startswith("skill_"):
            for s, p in a["probabilities"].items():
                if s in index and float(p) > SKILL_FLOOR:
                    scored[s] = float(p)
    return sorted(scored, key=lambda s: -scored[s])

def parse(data, groups, index=None):
    """Answers are checked in code: only a known level, known groups and known skills get through."""
    try:
        j = json.loads(data)
        A = j["answers"]
        lv, gp = A["level"], A["group"]
        probs = {int(k): float(v) for k, v in lv["probabilities"].items()}
        level = max(probs, key=lambda k: (probs[k], k))
        if probs.get(3, 0) >= L3_RISK:
            level = 3
        gprobs = {k: float(v) for k, v in gp["probabilities"].items()}
        first = gp["choice"]
        if level not in range(4) or first not in groups:
            raise ValueError
        fits = float(A["any_group"]["noul"])
        rest = sorted((k for k, v in gprobs.items() if v > SECOND_GROUP and k != first and k in groups),
                      key=lambda k: -gprobs[k])
        picked = [] if fits < FITS_MIN else [first] + rest
        lc, gc = float(lv["confidence"]), float(gp["confidence"])
        return {"level": level, "groups": picked, "model": str(j.get("model"))[:40],
                "confidence": {"level": lc, "group": gc},
                "gated": "auto" if lc >= LEVEL_CONF and gc >= GROUP_CONF else "escalate",
                "skills": pick_skills(A, index),
                "usage": j.get("usage")}
    except (KeyError, TypeError, ValueError, AttributeError):
        raise Fallback("bad-response")

def ask_jev(text, groups, timeout, index=None):
    if os.path.exists(os.path.expanduser("~/.claude/state/off/nvaex-jev-core.typesafe")):
        raise Fallback("typesafe-off")
    if not groups:
        raise Fallback("no-groups-file")
    if backing_off():
        raise Fallback("backoff")
    key = api_key()
    if not key:
        raise Fallback("no-key")
    if not re.fullmatch(r"[\x21-\x7e]+", key):
        raise Fallback("bad-key-format")
    clean, n = redact_outbound(text)
    body = json.dumps({"model": os.environ.get("TYPESAFE_DEFAULT_MODEL") or MODEL,
                       "state": {"task": truncate(clean)}, "questions": questions(groups, index)}).encode("utf-8")
    data, rid = post(body, key, timeout)
    jev = parse(data, groups, index)
    jev["redacted"], jev["request_id"] = n, rid
    return jev

def log(res):
    """Decision log for the fallback rate. Never the prompt."""
    try:
        d = os.path.expanduser("~/.claude/state/nvaex-jev-core")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "route.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({k: res.get(k) for k in ("level", "groups", "skills", "source", "error", "request_id", "jev_model", "ms")}
                               | {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}) + "\n")
    except OSError:
        pass

def classify(text, timeout=None):
    """Route one task. Never raises; source is 'typesafe' or 'local-fallback', and error holds the fallback reason."""
    t0 = time.time()
    if timeout is None:
        try:
            timeout = float(os.environ.get("JEV_TIMEOUT") or HOOK_TIMEOUT)
        except ValueError:
            timeout = HOOK_TIMEOUT
    G = load_groups()
    level, top, rule, why = local_route(text, G)
    res = {"source": "local-fallback", "error": None, "rule": rule, "config_fault": False}
    picked = []
    try:
        jev = ask_jev(text, G, timeout, load_index())
        level, top, why = jev.pop("level"), jev.pop("groups"), []
        picked = jev.pop("skills")
        res.update(source="typesafe", rule="typesafe", jev_model=jev.pop("model"), **jev)
    except Fallback as e:
        res.update(error=e.reason, request_id=e.request_id, config_fault=e.reason in CONFIG_FAULTS)
    except Exception as e:
        res["error"] = "error-" + type(e).__name__
    if res["source"] == "typesafe" and level < 3 and re.search(HARD_L3, text.lower()):
        level, why = 3, ["code floor: destructive or cross-repo shape; Jev may raise this, never lower it"]
    skills = picked or list(dict.fromkeys(s for t in top for s in G[t].get("skills", [])))  # no index or no pick: every skill of every group; no count cap
    res.update(level=level, groups=top, tier=tier_for(level, top), skills=skills, rules=RULES[level], why=why,
               taxonomy_csv_loaded=os.path.isfile(csv_path()), ms=int((time.time() - t0) * 1000))
    log(res)
    return res

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    print(json.dumps(classify(" ".join(sys.argv[1:]) or sys.stdin.read()), indent=1))
