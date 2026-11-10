#!/usr/bin/env python3
"""obsidian-config-tree backend: every installed skill, agent, command, hook and script with a one-line
plain-English explanation. Read-only. Usage: configtree.py [QUERY] [--md]   (--md = Obsidian-style outline)"""
import json, re, sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from inventory import CL, fm, load  # noqa: E402


def one(s, n=110):
    s = re.sub(r"\s+", " ", s or "").strip()
    s = re.split(r"(?<=[.!?])\s", s, maxsplit=1)[0]
    return s if len(s) <= n else s[: n - 1] + "…"


def roots():
    yield "user", CL
    inst = load(CL / "plugins" / "installed_plugins.json").get("plugins", {})
    en = load(CL / "settings.json").get("enabledPlugins", {})
    for key, es in inst.items():
        if es and en.get(key):
            yield key, Path(es[0].get("installPath", ""))


def hooks_of(r):
    h = load(r / "hooks" / "hooks.json")
    for m in h.get("modules", []):
        yield "module " + m
    for ev, gs in (h.get("hooks") or {}).items():
        for g in gs:
            for x in g.get("hooks", []):
                yield f"{ev}: {x.get('command', x.get('type', ''))}"[:90]


def tree():
    out = []  # (owner, kind, name, explanation)
    for owner, r in roots():
        if not r.is_dir():
            continue
        for f in sorted(r.glob("skills/*/SKILL.md")):
            n, d = fm(f); out.append((owner, "skill", n or f.parent.name, one(d)))
        for k, g in (("agent", "agents/*.md"), ("command", "commands/*.md")):
            for f in sorted(r.glob(g)):
                n, d = fm(f); out.append((owner, k, n or f.stem, one(d)))
        for h in hooks_of(r):
            out.append((owner, "hook", h.split(":")[0].split()[0], h))
        for f in sorted(r.glob("scripts/*")):
            if f.is_file():
                try: first = next((l.strip("#/ \"'\n") for l in f.read_text(errors="ignore").splitlines()[1:6] if l.strip("#/ \"'\n")), "")
                except Exception: first = ""
                out.append((owner, "script", f.name, one(first)))
    return out


def main(a):
    md = "--md" in a
    q = " ".join(x for x in a if x != "--md").lower()
    rows = [r for r in tree() if not q or q in " ".join(r).lower()]
    cur = None
    for owner, kind, name, ex in rows:
        if owner != cur:
            print(f"- {owner}" if md else f"{owner}"); cur = owner
        print(f"  - {kind} `{name}`: {ex}" if md else f"  {kind:7} {name}: {ex}")
    if not rows:
        print("no match")


if __name__ == "__main__":
    main(sys.argv[1:])
