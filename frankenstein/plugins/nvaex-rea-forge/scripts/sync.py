#!/usr/bin/env python3
"""customize-and-sync for a fork: keep local mods as patches, rebase on upstream, reapply.
usage: sync.py save  <fork> <upstream-ref>   # patches/ <- git diff <ref> over tracked files
       sync.py apply <fork> <patch-dir>       # git apply each patch in order (3-way)
       sync.py check <fork> <patch-dir>       # dry-run apply
Never fetches, commits or pushes; you pull upstream yourself, then run apply."""
import glob, os, subprocess, sys

def git(repo, *args, inp=None):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, input=inp)

def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    cmd, repo, arg = sys.argv[1:]
    if cmd == "save":
        r = git(repo, "diff", "--binary", arg)
        if r.returncode:
            sys.exit(r.stderr)
        os.makedirs("patches", exist_ok=True)
        out = os.path.join("patches", "0001-local-mods.patch")
        open(out, "w").write(r.stdout)
        print(out, len(r.stdout), "bytes")
    elif cmd in ("apply", "check"):
        rc = 0
        for p in sorted(glob.glob(os.path.join(arg, "*.patch"))):
            flags = ["--check"] if cmd == "check" else ["--3way"]
            r = git(repo, "apply", *flags, os.path.abspath(p))
            print(("ok  " if not r.returncode else "FAIL"), p, r.stderr.strip()[:200])
            rc |= r.returncode
        sys.exit(rc)
    else:
        sys.exit(__doc__)

main()
