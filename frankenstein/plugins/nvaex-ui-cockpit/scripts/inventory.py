#!/usr/bin/env python3
"""Plugin inventory for plugins-panel. Read-only. Usage: inventory.py summary|list|json"""
import json, re, sys
sys.dont_write_bytecode = True
from pathlib import Path

HOME = Path.home()
CL = HOME / ".claude"


def load(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return {}


def fm(path):
    """name/description from frontmatter, '' if none."""
    try:
        t = Path(path).read_text(errors="ignore")
    except Exception:
        return "", ""
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    if not m:
        return "", ""
    out = {}
    for k in ("name", "description"):
        mm = re.search(rf"^{k}:\s*(.*?)(?=\n\S|\Z)", m.group(1), re.S | re.M)
        out[k] = re.sub(r"\s+", " ", mm.group(1)).strip(" >|\"'") if mm else ""
    return out["name"], out["description"]


def footprint(root):
    """Always-listed text (name + description of skills, agents, commands) in ~tokens (chars/4)."""
    chars, sk, ag, cm = 0, 0, 0, 0
    for f in root.glob("skills/*/SKILL.md"):
        n, d = fm(f); chars += len(n) + len(d) + 4; sk += 1
    for f in root.glob("agents/*.md"):
        n, d = fm(f); chars += len(n or f.stem) + len(d) + 4; ag += 1
    for f in root.glob("commands/*.md"):
        n, d = fm(f); chars += len(n or f.stem) + len(d) + 4; cm += 1
    return chars // 4, sk, ag, cm


def hook_count(root):
    h = load(root / "hooks" / "hooks.json")
    n = len(h.get("modules", []))
    for ev in (h.get("hooks") or {}).values():
        for g in ev:
            n += len(g.get("hooks", []))
    return n


def inventory():
    enabled = load(CL / "settings.json").get("enabledPlugins", {})
    installed = load(CL / "plugins" / "installed_plugins.json").get("plugins", {})
    rows = []
    for key, entries in installed.items():
        e = entries[0] if entries else {}
        root = Path(e.get("installPath", ""))
        tok, sk, ag, cm = footprint(root) if root.is_dir() else (0, 0, 0, 0)
        rows.append({"plugin": key, "active": bool(enabled.get(key)), "skills": sk, "agents": ag,
                     "commands": cm, "hooks": hook_count(root) if root.is_dir() else 0, "tokens": tok})
    rows.sort(key=lambda r: (not r["active"], -r["tokens"]))
    return rows


def main(argv):
    cmd = argv[0] if argv else "summary"
    rows = inventory()
    act = [r for r in rows if r["active"]]
    if cmd == "json":
        print(json.dumps({"active": len(act), "total": len(rows), "plugins": rows}))
    elif cmd == "list":
        print(f"Plugins: {len(act)}/{len(rows)} active")
        for r in rows:
            print(f"{'on ' if r['active'] else 'off'} {r['plugin']}  skills {r['skills']} agents {r['agents']} "
                  f"cmds {r['commands']} hooks {r['hooks']}  ~{r['tokens']} tok")
        print(f"active footprint ~{sum(r['tokens'] for r in act)} tok")
    else:
        print(f"Plugins: {len(act)}/{len(rows)} active")


if __name__ == "__main__":
    main(sys.argv[1:])
