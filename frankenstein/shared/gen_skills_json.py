#!/usr/bin/env python3
"""Generate each package's skills.json from its SKILL.md files, so nobody edits the index by hand and it cannot drift.
Usage: gen_skills_json.py [--check] [PACKAGE_DIR ...]   Default: every package under plugins/ and mcp/ beside this file.
--check writes nothing and exits 1 if any index is stale. Stdlib only."""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = re.compile(r"\b(?:claw|memory|jev|rea|ag|burn)\.[a-z_]+\b")

def known_tools():
    """Tool names as the servers declare them (quoted in server source), so memory.py or a file name never counts as a tool."""
    found = set()
    for src in glob.glob(os.path.join(ROOT, "plugins/*/mcp/*/*")) + glob.glob(os.path.join(ROOT, "mcp/*/node/*.mjs")) + glob.glob(os.path.join(ROOT, "mcp/*/*.py")):
        if src.endswith((".py", ".mjs", ".js")):
            with open(src, encoding="utf-8", errors="replace") as f:
                found |= set(re.findall(r"[\"']((?:claw|memory|jev|rea|ag|burn)\.[a-z_]+)[\"']", f.read()))
    return found

KNOWN = known_tools()

def skill_dirs(pkg):
    """Folders to scan: the manifest's `skills` list, else skills/. Same rule Claude Code uses."""
    try:
        with open(os.path.join(pkg, ".claude-plugin/plugin.json"), encoding="utf-8") as f:
            listed = json.load(f).get("skills")
    except (OSError, ValueError):
        listed = None
    if isinstance(listed, str):
        listed = [listed]
    return [os.path.normpath(os.path.join(pkg, d)) for d in (listed or ["skills"])]

def front(text):
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    out, key = {}, None
    for line in m.group(1).split("\n"):
        k = re.match(r"([A-Za-z_-]+):\s*(.*)$", line)
        if k:
            key = k.group(1)
            out[key] = k.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
    return {k: re.sub(r"^[>|][-+]?\s*", "", v).strip().strip("\"'") for k, v in out.items()}, text[m.end():]

def rows(pkg):
    res = []
    for d in skill_dirs(pkg):
        for path in sorted(glob.glob(os.path.join(d, "*", "SKILL.md"))):
            with open(path, encoding="utf-8") as f:
                meta, body = front(f.read())
            desc = re.sub(r"\s+", " ", meta.get("description", ""))
            row = {"id": meta.get("name") or os.path.basename(os.path.dirname(path)),
                   "path": os.path.relpath(path, pkg).replace(os.sep, "/"), "kind": "skill", "purpose": desc,
                   "triggers": sorted(set(re.findall(r"\"([^\"]{2,40})\"", desc))),
                   "tools": sorted(set(TOOL.findall(body)) & KNOWN)}
            if meta.get("disable-model-invocation") == "true":
                row["user_only"] = True
            res.append(row)
    return sorted(res, key=lambda r: r["id"])

def render(pkg):
    return json.dumps({"package": os.path.basename(os.path.normpath(pkg)), "skills": rows(pkg)}, indent=1, ensure_ascii=False) + "\n"

def main(argv):
    check = "--check" in argv
    pkgs = [a for a in argv if a != "--check"] or sorted(glob.glob(os.path.join(ROOT, "plugins/*")) + glob.glob(os.path.join(ROOT, "mcp/*")))
    stale, total = [], 0
    for pkg in pkgs:
        new = render(pkg)
        n = len(json.loads(new)["skills"])
        out = os.path.join(pkg, "skills.json")
        if not n and not os.path.exists(out):
            continue
        total += n
        old = open(out, encoding="utf-8").read() if os.path.exists(out) else None
        if old != new:
            stale.append(os.path.basename(os.path.normpath(pkg)))
            if not check:
                with open(out, "w", encoding="utf-8") as f:
                    f.write(new)
    print("%d skills in %d packages; %s: %s" % (total, len(pkgs), "stale" if check else "wrote", ", ".join(stale) or "none"))
    return 1 if check and stale else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
