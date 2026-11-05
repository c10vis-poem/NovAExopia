#!/usr/bin/env python3
"""env-customizer-panel backend. Profiles use harness-scope's format and selector, so they stay swappable
with the harness-scope mod. Usage:
  profiles.py scopes [--repo DIR]      global / marketplace / repo overview
  profiles.py list | show NAME
  profiles.py use NAME [--repo DIR]    writes DIR/.claude/harness-scope.json {"profile": NAME}
  profiles.py clear [--repo DIR]
Never touches ~/.claude/settings*.json."""
import json, os, re, sys
from pathlib import Path

CL = Path.home() / ".claude"
PDIR = CL / "harness-scope" / "profiles"
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
CATS = {"skills", "agents", "instructions", "tools"}
BUNDLED = {"writing": {"tools": {"deny": ["LSP", "NotebookEdit", "EnterWorktree", "ExitWorktree"]}}}


def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return {}


def valid(p):
    if not isinstance(p, dict) or not set(p) <= CATS:
        return False
    return all(isinstance(r, dict) and len(r) == 1 and next(iter(r)) in ("allow", "deny")
               and isinstance(next(iter(r.values())), list) for r in p.values())


def profiles():
    out = dict(BUNDLED)
    for f in sorted(PDIR.glob("*.json")) if PDIR.is_dir() else []:
        p = jl(f)
        if NAME.match(f.stem) and valid(p):
            out[f.stem] = p
    return out


def sel_path(repo):
    return Path(repo) / ".claude" / "harness-scope.json"


def current(repo):
    return jl(sel_path(repo)).get("profile")


def main(a):
    repo = os.getcwd()
    if "--repo" in a:
        i = a.index("--repo"); repo = a[i + 1]; a = a[:i] + a[i + 2:]
    cmd = a[0] if a else "scopes"
    ps = profiles()
    if cmd == "scopes":
        en = jl(CL / "settings.json").get("enabledPlugins", {})
        mk = jl(CL / "plugins" / "known_marketplaces.json")
        ins = jl(CL / "plugins" / "installed_plugins.json").get("plugins", {})
        print(f"global: {sum(1 for k in ins if en.get(k))}/{len(ins)} installed plugins enabled (edit with /plugin)")
        print(f"marketplaces: {', '.join(sorted(mk)) or 'none'}")
        print(f"repo {repo}: profile {current(repo) or 'none'}")
        print(f"profiles: {', '.join(ps) or 'none'}")
    elif cmd == "list":
        cur = current(repo)
        for n in ps:
            print(("* " if n == cur else "  ") + n)
    elif cmd == "show" and len(a) > 1:
        if a[1] not in ps: sys.exit(f"no profile {a[1]!r}")
        print(json.dumps(ps[a[1]], indent=2))
    elif cmd == "use" and len(a) > 1:
        if not NAME.match(a[1]) or a[1] not in ps: sys.exit(f"no profile {a[1]!r}; have: {', '.join(ps)}")
        p = sel_path(repo); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"profile": a[1]}) + "\n")
        print(f"{p}: profile {a[1]} (takes effect next session; remove with: clear)")
    elif cmd == "clear":
        p = sel_path(repo)
        if p.exists(): p.unlink()
        print("selector removed")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
