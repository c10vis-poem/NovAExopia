#!/usr/bin/env python3
"""batch_ledger.py: JSONL checkpoint ledger for rolling batches (default 25 files, 4 workers).
NEW (no donor on the phone). Staging only: it reads a folder and writes one ledger file.

  plan   DIR --ledger L.jsonl [--size 25]   list files (skips .git etc.), write one line per batch
  next   --ledger L.jsonl [--workers 4]     print up to N pending batch ids (rolling window)
  claim  --ledger L.jsonl ID                pending -> running
  done   --ledger L.jsonl ID [--note TXT]   running -> done   (also: fail ID --note TXT)
  status --ledger L.jsonl                   counts per state
A ledger line is the latest state for a batch id; updates append, last line per id wins.
"""
import argparse, json, os, sys, time
SKIP = {".git", "node_modules", "__pycache__", ".venv", ".in_use"}

def load(p):
    st = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line); st[r["id"]] = r
    return st

def put(p, r):
    r["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main(a):
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("arg", nargs="?")
    ap.add_argument("--ledger", required=True); ap.add_argument("--size", type=int, default=25)
    ap.add_argument("--workers", type=int, default=4); ap.add_argument("--note", default="")
    o = ap.parse_args(a); st = load(o.ledger)
    if o.cmd == "plan":
        if st: print("ledger exists; plan refused (resume with next/claim/done)", file=sys.stderr); return 1
        files = []
        for r, ds, fs in os.walk(o.arg):
            ds[:] = sorted(d for d in ds if d not in SKIP)
            files += [os.path.join(r, f) for f in sorted(fs)]
        for i in range(0, len(files), o.size):
            put(o.ledger, {"id": f"b{i // o.size + 1:03d}", "state": "pending", "files": files[i:i + o.size]})
        print(f"{len(files)} files, {-(-len(files) // o.size)} batches of <= {o.size}"); return 0
    if o.cmd == "next":
        running = sum(r["state"] == "running" for r in st.values())
        for r in [r for r in st.values() if r["state"] == "pending"][:max(0, o.workers - running)]: print(r["id"])
        return 0
    if o.cmd == "status":
        c = {}
        for r in st.values(): c[r["state"]] = c.get(r["state"], 0) + 1
        print(json.dumps(c, sort_keys=True)); return 0
    want = {"claim": ("pending", "running"), "done": ("running", "done"), "fail": ("running", "failed")}.get(o.cmd)
    if not want or o.arg not in st: print("bad command or batch id", file=sys.stderr); return 2
    r = st[o.arg]
    if r["state"] != want[0]: print(f"{o.arg} is {r['state']}, expected {want[0]}", file=sys.stderr); return 1
    r = dict(r, state=want[1], note=o.note); put(o.ledger, r); print(f"{o.arg} -> {want[1]}"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
