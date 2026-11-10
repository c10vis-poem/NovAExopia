#!/usr/bin/env python3
"""rule_propose.py: approval-gated rule store. proposed -> active (human) / rejected. Stdlib.
  propose --name N --hint H < SKILL.md   stage a rule (inert)
  list | approve N | reject N | demote N
Root: $NVAEX_RULES_DIR or ~/.claude/nvaex-rules. Logic from compounded skill_propose.py/pin_skill.py (MIT), reduced."""
import argparse, json, os, re, shutil, sys, time
from pathlib import Path

ROOT = Path(os.environ.get("NVAEX_RULES_DIR") or Path.home() / ".claude" / "nvaex-rules")
STATES = (".proposed", "active", ".rejected")
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
THREATS = [re.compile(p, re.I) for p in (
    r"ignore (all )?(previous|prior|above) instructions", r"curl[^\n]*\|\s*(ba)?sh", r"rm\s+-rf\s+[/~]",
    r"\b(api[_-]?key|secret|token)\s*[:=]\s*\S{12,}", r"<\s*/?\s*system\s*>", r"base64\s+-d")]
MAX = 64 * 1024


def d(state):
    return ROOT / state


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    return dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l and not l.startswith(" "))


def find(name):
    for s in STATES:
        if (d(s) / name / "SKILL.md").is_file():
            return s
    return None


def log(event, name, **kw):
    ROOT.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "events.jsonl", "a") as f:
        f.write(json.dumps({"t": int(time.time()), "event": event, "name": name, **kw}) + "\n")


def move(name, dst):
    src = find(name)
    if not src:
        sys.exit(f"no such rule: {name}")
    if src == dst:
        sys.exit(f"{name} already {dst.strip('.')}")
    (d(dst)).mkdir(parents=True, exist_ok=True)
    shutil.move(str(d(src) / name), str(d(dst) / name))
    log(dst.strip("."), name, was=src.strip("."))
    print(f"{name}: {src.strip('.')} -> {dst.strip('.')}")


def propose(a):
    text = sys.stdin.read()
    if len(text.encode()) > MAX:
        sys.exit("refused: over 64 KB")
    if not NAME.match(a.name or ""):
        sys.exit("refused: --name must be kebab-case")
    if len((a.hint or "").strip()) < 20:
        sys.exit("refused: --hint must be 20+ chars")
    fm = frontmatter(text)
    if not fm or fm.get("name", "").strip() != a.name or not fm.get("description", "").strip():
        sys.exit("refused: frontmatter needs name (== --name) and description")
    if fm.get("kind", "").strip() != "rule":
        sys.exit("refused: frontmatter needs kind: rule")
    for t in THREATS:
        if t.search(text):
            sys.exit(f"refused: threat pattern {t.pattern!r}")
    if find(a.name):
        sys.exit(f"refused: {a.name} already exists ({find(a.name).strip('.')})")
    p = d(".proposed") / a.name
    p.mkdir(parents=True)
    (p / "SKILL.md").write_text(text)
    (p / "hint.txt").write_text(a.hint.strip() + "\n")
    log("proposed", a.name)
    print(f"staged {p}/SKILL.md (inert until: /rules approve {a.name})")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    pp = sp.add_parser("propose"); pp.add_argument("--name"); pp.add_argument("--hint")
    sp.add_parser("list")
    for c in ("approve", "reject", "demote"):
        sp.add_parser(c).add_argument("name")
    a = ap.parse_args()
    if a.cmd == "propose":
        propose(a)
    elif a.cmd == "list":
        for s in STATES:
            for p in sorted(d(s).glob("*/SKILL.md")) if d(s).is_dir() else []:
                print(f"{s.strip('.'):9} {p.parent.name}")
    elif a.cmd == "approve":
        if find(a.name) != ".proposed":
            sys.exit("only a proposed rule can be approved")
        move(a.name, "active")
    elif a.cmd == "reject":
        move(a.name, ".rejected")
    else:
        if find(a.name) != "active":
            sys.exit("only an active rule can be demoted")
        move(a.name, ".proposed")


if __name__ == "__main__":
    main()
