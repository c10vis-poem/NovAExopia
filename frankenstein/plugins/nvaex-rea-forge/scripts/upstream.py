#!/usr/bin/env python3
"""Deterministic half of customize-and-sync (from turbocharge). Never commits, pushes or merges.
  upstream.py init  <fork> <upstream-url|path>   write <fork>/.turbocharge/settings.json at upstream's latest stable tag
  upstream.py next  <fork>                       print "new <tag>" or "current <tag>"; exit 3 if a prior sync failed
  upstream.py prune <fork> <upstream-skills-dir> drop intent.md sections whose skill upstream no longer has"""
import json, os, re, subprocess, sys

PRE = re.compile(r"-(alpha|beta|rc|pre)", re.I)

def latest_tag(up):
    r = subprocess.run(["git", "ls-remote", "--tags", "--refs", "--sort=-v:refname", up],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("ls-remote failed: " + r.stderr.strip())
    tags = [l.split("refs/tags/", 1)[1] for l in r.stdout.splitlines() if "refs/tags/" in l]
    stable = [t for t in tags if not PRE.search(t)]
    if stable:
        return stable[0]
    r = subprocess.run(["git", "ls-remote", up, "HEAD"], capture_output=True, text=True)
    return r.stdout.split()[0] if r.stdout.strip() else sys.exit("upstream has no tags and no HEAD")

def cfg_path(fork):
    return os.path.join(fork, ".turbocharge", "settings.json")

def load(fork):
    try:
        return json.load(open(cfg_path(fork)))
    except FileNotFoundError:
        sys.exit("no .turbocharge/settings.json; run init first")

def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    cmd, fork = a[0], a[1]
    if cmd == "init" and len(a) == 3:
        os.makedirs(os.path.dirname(cfg_path(fork)), exist_ok=True)
        c = {"upstreamRepo": a[2], "lastSyncedTag": latest_tag(a[2])}
        json.dump(c, open(cfg_path(fork), "w"), indent=2)
        print(json.dumps(c))
    elif cmd == "next" and len(a) == 2:
        c = load(fork)
        if c.get("syncStatus") == "failed":
            print("blocked: prior sync failed at", c.get("failedTag")); sys.exit(3)
        t = latest_tag(c["upstreamRepo"])
        print(("current " if t == c["lastSyncedTag"] else "new ") + t)
    elif cmd == "prune" and len(a) == 3:
        p = os.path.join(fork, ".turbocharge", "intent.md")
        if not os.path.exists(p) or not open(p).read().strip():
            print("no intent.md"); return
        parts = re.split(r"(?m)^(?=## )", open(p).read())
        keep, gone = [], []
        for s in parts:
            m = re.match(r"## (\S+)", s)
            if m and not os.path.isdir(os.path.join(a[2], m.group(1))):
                gone.append(m.group(1))
            else:
                keep.append(s)
        open(p, "w").write("".join(keep).rstrip("\n") + "".join(f"\n<!-- {g} removed or renamed upstream -->" for g in gone) + "\n")
        print("pruned:", ",".join(gone) or "none")
    else:
        sys.exit(__doc__)

main(sys.argv[1:])
