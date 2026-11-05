#!/usr/bin/env python3
"""List skills under one or more plugin (or skills) directories; flag problems.
Usage: inventory.py [--json] DIR [DIR ...]
A skill is any DIR/**/SKILL.md. Checks: frontmatter present, name and description set,
name equals folder name, duplicate names across all given DIRs. Reads files only.
Exit 0 clean, 1 problems found, 2 bad usage. Standard library only; no network."""
import json, os, sys

def frontmatter(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return None, str(e)
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, "no frontmatter"
    fm, key = {}, None
    for ln in lines[1:]:
        if ln.strip() == "---":
            return fm, None
        if ln[:1] in " \t" and key:       # continuation of a folded value
            fm[key] += " " + ln.strip()
        elif ":" in ln:
            key, _, v = ln.partition(":")
            key = key.strip()
            fm[key] = v.strip().strip("\"'")
    return None, "frontmatter not closed"

def main(argv):
    as_json = "--json" in argv
    dirs = [a for a in argv if a != "--json"]
    if not dirs or any(not os.path.isdir(d) for d in dirs):
        print(__doc__.split("\n")[1], file=sys.stderr); return 2
    rows, problems = [], []
    for root in dirs:
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in (".git", "node_modules")]
            if "SKILL.md" in fn:
                p = os.path.join(dp, "SKILL.md"); folder = os.path.basename(dp)
                fm, err = frontmatter(p)
                row = {"path": os.path.relpath(p, root), "root": root, "folder": folder}
                if err: problems.append((p, err)); row["name"] = None
                else:
                    row["name"] = fm.get("name"); row["description"] = (fm.get("description") or "")[:120]
                    row["user_only"] = fm.get("disable-model-invocation") == "true"
                    if not fm.get("name"): problems.append((p, "no name"))
                    elif fm["name"] != folder: problems.append((p, f"name '{fm['name']}' != folder '{folder}'"))
                    if not fm.get("description"): problems.append((p, "no description"))
                rows.append(row)
    seen = {}
    for r in rows:
        if r.get("name"): seen.setdefault(r["name"], []).append(os.path.join(r["root"], r["path"]))
    for n, ps in seen.items():
        if len(ps) > 1: problems.append((n, "duplicate name in: " + ", ".join(ps)))
    rows.sort(key=lambda r: (r["root"], r["path"]))
    if as_json:
        print(json.dumps({"skills": rows, "problems": [{"where": w, "issue": i} for w, i in problems]}, indent=1))
    else:
        for r in rows: print(f"{r.get('name') or '(none)':32} {'user ' if r.get('user_only') else 'model'}  {r['path']}")
        print(f"\n{len(rows)} skills, {len(problems)} problems")
        for w, i in problems: print(f"PROBLEM {w}: {i}")
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
