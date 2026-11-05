#!/usr/bin/env python3
"""UserPromptSubmit: Stage-0 garble flags + Stage-1 router (group shortlist, L0-L3). Non-blocking, stdlib."""
import json, os, re, sys
d = json.load(sys.stdin)
p = (d.get("prompt") or "").strip()
if not p or "#skip-enforce" in p or p.startswith("/"):
    sys.exit(0)
root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = json.load(open(os.path.join(root, "skills/jev-router/groups.json")))["groups"]

# Stage 0: cheap STT/layout garble signals (the drunken-master skill does the real repair).
SOUNDALIKE = r"\b(agente|dumas|dumb ass|jane|sea eye|pee are|sever|stagging|ingratiation)\b"
junk = [w for w in re.findall(r"[A-Za-z]{4,}", p) if not re.search(r"[aeiouy]", w.lower())]
flags = [m.group(0) for m in re.finditer(SOUNDALIKE, p, re.I)] + junk[:3]
out = []
if flags:
    out.append("STAGE-0: possible garbled input (" + ", ".join(flags[:5]) +
               "). Apply the drunken-master skill: your first text, before any tool call, is a 'Read as: ...' line.")

# Stage 1: pick up to 3 groups by keyword hits, then the top skills of those.
words = set(re.findall(r"[a-z]+", p.lower()))
hits = sorted(((len(words & set(g["kw"])), n) for n, g in G.items()), reverse=True)
top = [n for c, n in hits if c][:3]
n = len(p)
tools = len(re.findall(r"\b(and then|then|also|after that|finally)\b", p.lower()))
lvl = 0 if n < 60 and not top else 1 if n < 200 and tools == 0 else 2 if n < 600 else 3
if top:
    sk = [s for t in top[:2] for s in G[t]["skills"][:1]]
    out.append(f"JEV route: L{lvl} | groups {'/'.join(top)} | try {', '.join(sk)}"
               + (" | L2+: run the task-auditor gates" if lvl >= 2 else ""))
elif lvl >= 2:
    out.append(f"JEV route: L{lvl} | no group matched | run the task-auditor gates")
if out:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": "\n".join(out)}}))
