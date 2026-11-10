#!/usr/bin/env python3
"""Cross-session task list. Usage: backlog.py add|list|next|start|done|block|handoff ..."""
import argparse, json, os, sys, time
F = os.environ.get("NVAEX_BACKLOG") or os.path.expanduser("~/.claude/state/nvaex-jev-core/backlog.jsonl")
def load():
    try:
        return [json.loads(x) for x in open(F) if x.strip()]
    except FileNotFoundError:
        return []
def save(T):
    os.makedirs(os.path.dirname(F), exist_ok=True)
    open(F + ".tmp", "w").write("".join(json.dumps(t) + "\n" for t in T)); os.replace(F + ".tmp", F)
RANK = {"H": 0, "M": 1, "L": 2}
def ready(t, T):
    done = {x["id"] for x in T if x["state"] == "done"}
    return t["state"] in ("open", "active") and all(a in done for a in t["after"])
def show(t, T):
    flag = "" if ready(t, T) or t["state"] != "open" else " [waiting]"
    return f"#{t['id']} {t['p']} {t['state']:7} {t['text']}" + flag + (f"  ({t['why']})" if t.get("why") else "")
a = argparse.ArgumentParser(); s = a.add_subparsers(dest="c", required=True)
x = s.add_parser("add"); x.add_argument("text"); x.add_argument("-p", default="M", choices="HML"); x.add_argument("--project", default=""); x.add_argument("--after", type=int, action="append", default=[])
s.add_parser("list").add_argument("--all", action="store_true"); s.add_parser("next"); s.add_parser("handoff")
for n in ("start", "done", "block"):
    y = s.add_parser(n); y.add_argument("id", type=int)
    if n == "block": y.add_argument("why")
r = a.parse_args(); T = load()
def get(i):
    for t in T:
        if t["id"] == i: return t
    sys.exit(f"no task #{i}")
if r.c == "add":
    if len(r.text) > 200: sys.exit("task text over 200 chars: split it")
    for i in r.after: get(i)
    t = {"id": max([q["id"] for q in T] + [0]) + 1, "text": r.text, "p": r.p, "project": r.project, "after": r.after, "state": "open", "t": int(time.time())}
    T.append(t); save(T); print(t["id"])
elif r.c in ("start", "done", "block"):
    t = get(r.id); t["state"] = {"start": "active", "done": "done", "block": "blocked"}[r.c]
    if r.c == "block": t["why"] = r.why
    save(T); print(show(t, T))
elif r.c == "list":
    for t in sorted(T, key=lambda t: (RANK[t["p"]], t["id"])):
        if r.all or t["state"] != "done": print(show(t, T))
elif r.c == "next":
    c = sorted((t for t in T if ready(t, T)), key=lambda t: (t["state"] != "active", RANK[t["p"]], t["id"]))
    print(show(c[0], T) if c else "nothing ready")
else:
    for title, f in (("DONE", lambda t: t["state"] == "done"), ("IN PROGRESS", lambda t: t["state"] == "active"),
                     ("BLOCKED", lambda t: t["state"] == "blocked"), ("WAITING", lambda t: t["state"] == "open" and not ready(t, T)),
                     ("NEXT", lambda t: t["state"] == "open" and ready(t, T))):
        rows = [show(t, T) for t in T if f(t)]
        if rows: print(title + "\n  " + "\n  ".join(rows))
