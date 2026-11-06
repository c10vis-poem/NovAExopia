#!/usr/bin/env python3
"""The one JEV router. The UserPromptSubmit hook (route.py) and jev.route_task (mcp/jev-rea-mcp/server.py) both call classify().

TypeSafe Jev decides the level (a Score) and the domain group (a Choice). The keyword rules below are the fallback when
there is no key, no network or an error. Every result names its source and, on fallback, the reason. Stdlib only.
Run it by hand: python3 scripts/jev_route.py "task text"
"""
import csv, json, os, re, sys, threading, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER = os.path.join(ROOT, "skills/jev-router")

# ---- questions, thresholds and limits (what a human reviews and tunes) ----
BASE_URL, API_PATH, MODEL = "https://api.typesafe.ai", "/v1/systemone", "jev-latest"
HOOK_TIMEOUT = 2.0    # seconds, hard deadline; the hook entry allows 5
MAX_TASK = 8000       # characters sent off the phone: head 60%, tail 40%
LEVEL_CONF, GROUP_CONF = 0.65, 0.75  # below either: gated "escalate" (same gates as claude-jev)
SECOND_GROUP = 0.25   # a further option above this also counts as a group (TypeSafe's two-category rule)
NONE = "none_of_the_above"
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
NONE_DESC = "None of the other options fit, such as small talk or a general question unrelated to this work."
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
    top = [n for c, n in hits if c][:3]
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
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # urllib would resend the Authorization header to the new host
        return None

def api_key():
    for n in ("TYPESAFE_API_KEY", "CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY"):
        v = os.environ.get(n, "").strip()
        if v and "${" not in v:
            return v
    return ""

def endpoint():
    base = (os.environ.get("TYPESAFE_BASE_URL") or BASE_URL).rstrip("/")
    u = urllib.parse.urlsplit(base)
    if u.scheme == "https" or (u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost")):
        return base + API_PATH
    raise Fallback("bad-base-url")  # the key never goes out in clear text

def questions(groups):
    opts = {n: g.get("desc") for n, g in groups.items()}
    opts[NONE] = NONE_DESC
    return {"level": LEVEL_Q, "group": {"type": "choice", "instructions": GROUP_Q_TEXT, "criteria": opts}}

def post(body, key, timeout):
    """POST with a hard deadline. The worker thread also covers DNS, which urllib's timeout does not."""
    req = urllib.request.Request(endpoint(), data=body, method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    box = {}
    def call():
        try:
            with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as r:
                box["data"] = r.read(1 << 20)
        except urllib.error.HTTPError as e:
            box["err"] = "http-%d" % e.code
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
        raise Fallback(box["err"])
    return box["data"]

def parse(data, groups):
    """Answers are checked in code: only a known level and known groups get through."""
    try:
        j = json.loads(data)
        lv, gp = j["answers"]["level"], j["answers"]["group"]
        probs = {int(k): float(v) for k, v in lv["probabilities"].items()}
        level = max(probs, key=lambda k: (probs[k], k))
        gprobs = {k: float(v) for k, v in gp["probabilities"].items()}
        first = gp["choice"]
        if level not in range(4) or (first != NONE and first not in groups):
            raise ValueError
        rest = sorted((k for k, v in gprobs.items() if v > SECOND_GROUP and k != first and k in groups),
                      key=lambda k: -gprobs[k])
        picked = ([] if first == NONE else [first]) + rest
        lc, gc = float(lv["confidence"]), float(gp["confidence"])
        return {"level": level, "groups": picked[:3], "model": str(j.get("model"))[:40],
                "confidence": {"level": lc, "group": gc},
                "gated": "auto" if lc >= LEVEL_CONF and gc >= GROUP_CONF else "escalate",
                "usage": j.get("usage")}
    except (KeyError, TypeError, ValueError, AttributeError):
        raise Fallback("bad-response")

def ask_jev(text, groups, timeout):
    if os.path.exists(os.path.expanduser("~/.claude/state/off/nvaex-jev-core.typesafe")):
        raise Fallback("typesafe-off")
    if not groups:
        raise Fallback("no-groups-file")
    key = api_key()
    if not key:
        raise Fallback("no-key")
    if not re.fullmatch(r"[\x21-\x7e]+", key):
        raise Fallback("bad-key-format")
    clean, n = redact_outbound(text)
    body = json.dumps({"model": os.environ.get("TYPESAFE_DEFAULT_MODEL") or MODEL,
                       "state": {"task": truncate(clean)}, "questions": questions(groups)}).encode("utf-8")
    jev = parse(post(body, key, timeout), groups)
    jev["redacted"] = n
    return jev

def log(res):
    """Decision log for the fallback rate. Never the prompt."""
    try:
        d = os.path.expanduser("~/.claude/state/nvaex-jev-core")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "route.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({k: res.get(k) for k in ("level", "groups", "source", "error", "jev_model", "ms")}
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
    res = {"source": "local-fallback", "error": None, "rule": rule}
    try:
        jev = ask_jev(text, G, timeout)
        level, top, why = jev.pop("level"), jev.pop("groups"), []
        res.update(source="typesafe", rule="typesafe", jev_model=jev.pop("model"), **jev)
    except Fallback as e:
        res["error"] = e.reason
    except Exception as e:
        res["error"] = "error-" + type(e).__name__
    if res["source"] == "typesafe" and level < 3 and re.search(HARD_L3, text.lower()):
        level, why = 3, ["code floor: destructive or cross-repo shape; Jev may raise this, never lower it"]
    skills = [s for t in top[:2] for s in G[t].get("skills", [])[:1]]
    res.update(level=level, groups=top, tier=tier_for(level, top), skills=skills, rules=RULES[level], why=why,
               taxonomy_csv_loaded=os.path.isfile(csv_path()), ms=int((time.time() - t0) * 1000))
    log(res)
    return res

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    print(json.dumps(classify(" ".join(sys.argv[1:]) or sys.stdin.read()), indent=1))
