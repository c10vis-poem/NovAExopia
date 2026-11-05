#!/usr/bin/env python3
"""provenance.py: write/verify skill-provenance.json (SHA-256 of every package file).
  provenance.py write [PKG_DIR]   -> PKG_DIR/skill-provenance.json
  provenance.py verify [PKG_DIR]  -> exit 1 on any changed/missing/extra file
"""
import hashlib, json, os, sys
SKIP = {".git", "__pycache__", "node_modules"}

def hashes(root):
    out = {}
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in SKIP]
        for f in fs:
            p = os.path.join(r, f); rel = os.path.relpath(p, root)
            if rel not in ("skill-provenance.json", "README.md") and not f.endswith(".pyc"):
                out[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return dict(sorted(out.items()))

cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
root = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), ".."))
pf = os.path.join(root, "skill-provenance.json")
if cmd == "write":
    json.dump({"algo": "sha256", "files": hashes(root)}, open(pf, "w"), indent=1); print(f"wrote {pf}")
else:
    old = json.load(open(pf))["files"]; new = hashes(root)
    bad = [k for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
    print("provenance OK" if not bad else "provenance DIFF: " + ", ".join(bad)); sys.exit(1 if bad else 0)
