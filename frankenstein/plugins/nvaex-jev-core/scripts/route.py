#!/usr/bin/env python3
"""UserPromptSubmit: time, Stage-0 garble flags, Stage-1 router, project decisions and rules. Non-blocking, stdlib."""
import datetime, glob, json, os, re, sys
d = json.load(sys.stdin)
p = (d.get("prompt") or "").strip()
if not p or "#skip-enforce" in p or p.startswith("/"):
    sys.exit(0)
root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = json.load(open(os.path.join(root, "skills/jev-router/groups.json")))["groups"]
cwd = d.get("cwd") or os.getcwd()
low = p.lower()
words = set(re.findall(r"[a-z0-9]+", low))
out = ["Now: " + datetime.datetime.now().astimezone().strftime("%a %Y-%m-%d %H:%M %Z (UTC%z)") + ". Anchor relative time to this."]

# Stage 0: STT/layout garble signals; code, paths, URLs and @mentions are kept out of the check.
spoken = re.sub(r"```.*?```|`[^`]*`|\S*[/@]\S*|https?://\S+", " ", p, flags=re.S)
SOUNDALIKE = r"\b(agente|dumas|dumb ass|jane|sea eye|pee are|sever|stagging|ingratiation)\b"
OK = {"html", "tmux", "grpc", "xhtml", "dbms"}
junk = [w for w in re.findall(r"[A-Za-z]{4,}", spoken) if not re.search(r"[aeiouy]", w.lower()) and w.lower() not in OK]
flags = [m.group(0) for m in re.finditer(SOUNDALIKE, spoken, re.I)] + junk[:3]
if flags and len(spoken.split()) >= 4:
    out.append("STAGE-0: possible garbled input (" + ", ".join(flags[:5]) +
               "). Apply the drunken-master skill: your first text, before any tool call, is a 'Read as: ...' line.")

# Stage 1: up to 3 groups by keyword hits, then the top skill of the best two.
hits = sorted(((len(words & set(g["kw"])), n) for n, g in G.items()), reverse=True)
top = [n for c, n in hits if c][:3]
n = len(p)
steps = len(re.findall(r"\b(and then|then|also|after that|finally)\b", low))
lvl = 0 if n < 60 and not top else 1 if n < 200 and steps == 0 else 2 if n < 600 else 3
def tier_for(level, groups):
    """Model tier from skills/jev-router/tiers.json; fail open (empty string) if the file is missing or bad."""
    try:
        T = json.load(open(os.path.join(root, "skills/jev-router/tiers.json")))
        order = T["order"]
        t = T["levels"]["L%d" % level]["tier"]
        if level > 0:
            for g in groups:
                m = T["task_types_min"].get(g)
                if m in order and order.index(m) > order.index(t):
                    t = m
        return T["tiers"][t]["model"]
    except Exception:
        return ""
tier = tier_for(lvl, top)
tier_s = f" | tier {tier}" if tier else ""
if top:
    sk = [s for t in top[:2] for s in G[t]["skills"][:1]]
    out.append(f"JEV route: L{lvl}{tier_s} | groups {'/'.join(top)} | try {', '.join(sk)}"
               + (" | L2+: run the task-auditor gates" if lvl >= 2 else ""))
elif lvl >= 2:
    out.append(f"JEV route: L{lvl}{tier_s} | no group matched | run the task-auditor gates")

# Decision ledger (<project>/.nvaex/decisions.jsonl, ~/.nvaex/decisions.jsonl): inject matches, flag contradictions.
def jl(path):
    try:
        return [json.loads(x) for x in open(path) if x.strip()]
    except Exception:
        return []
lines, budget = [], 400
for D in jl(os.path.join(cwd, ".nvaex/decisions.jsonl")) + jl(os.path.expanduser("~/.nvaex/decisions.jsonl")):
    if not isinstance(D, dict) or D.get("status", "active") != "active" or not D.get("decision"):
        continue
    rej = [r for r in D.get("rejected", []) if re.search(r"\b" + re.escape(str(r).lower()) + r"\b", low)]
    tagged = words & {str(t).lower() for t in D.get("tags", [])}
    if not (rej or tagged):
        continue
    s = (f"CONTRADICTION? prompt mentions rejected option '{rej[0]}'. Decided: {D['decision']}" if rej else
         f"Decided: {D['decision']}" + (f" (not {', '.join(map(str, D['rejected'][:3]))})" if D.get("rejected") else ""))
    if budget - len(s) < 0:
        break
    budget -= len(s)
    lines.append(s)
if lines:
    out.append("DECISIONS: " + " | ".join(lines))

# Rule files (<project>/.nvaex/rules/*.md, first line "keywords: a, b"): inject the ones the prompt matches.
budget = 1600
for f in sorted(glob.glob(os.path.join(cwd, ".nvaex/rules/*.md"))):
    try:
        head, _, body = open(f).read().partition("\n")
    except Exception:
        continue
    kw = {k.strip().lower() for k in head.split(":", 1)[1].split(",")} if head.lower().startswith("keywords:") else set()
    if kw & words and len(body) <= budget:
        budget -= len(body)
        out.append(f"RULE {os.path.basename(f)}: " + body.strip())

print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "\n".join(out)}}))
