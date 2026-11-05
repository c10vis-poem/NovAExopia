#!/usr/bin/env python3
"""Config audit of an agent harness in a project folder. Read-only. Usage: config_audit.py DIR [--json]
Checks (each finding is  LEVEL where: message ; levels HIGH MEDIUM LOW INFO):
  instruction files: AGENTS.md / CLAUDE.md present, over 200 lines, both present with different text
  .claude/settings*.json and .mcp.json: valid JSON; wildcard Bash/tool permissions; hook commands and MCP commands that point at files or programs that do not exist
  skills, agents, commands under .claude/ and plugin folders: SKILL.md frontmatter (name == folder, description set)
  secrets: lines in config/instruction files that look like keys (location only, the value is never printed)
Exit 0 when no HIGH finding, 1 when any HIGH, 2 usage. Standard library only."""
import json, os, re, shlex, shutil, sys
SECRET = re.compile(r"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:(api[_-]?key|secret|token|password)\"?\s*[:=]\s*\"?[A-Za-z0-9_\-/+=]{20,}))")
F = []
def add(level, where, msg): F.append((level, where, msg))
def rd(p):
    try: return open(p, encoding="utf-8", errors="replace").read()
    except OSError: return None
def jload(p):
    t = rd(p)
    try: return json.loads(t)
    except Exception as e: add("HIGH", p, f"invalid JSON ({e.__class__.__name__})"); return None
def expand(w, root):
    home = os.path.expanduser("~")
    for k, v in (("${CLAUDE_PROJECT_DIR}", root), ("$CLAUDE_PROJECT_DIR", root), ("${HOME}", home), ("$HOME", home)):
        w = w.replace(k, v)
    return home + w[1:] if w.startswith("~/") else w
def cmd_exists(cmd, root):
    """Return the first path or program in a hook command that does not exist, else None."""
    try: parts = shlex.split(cmd)
    except ValueError: return None
    for i, w in enumerate(parts[:3]):
        w = expand(w, root)
        if "$" in w or w.startswith("-") or w in ("&&", "||", ";", "|"): continue
        if "/" in w:
            if not os.path.exists(w if os.path.isabs(w) else os.path.join(root, w)): return w
        elif i == 0 and not shutil.which(w): return w
    return None
def audit(root):
    ins = {n: rd(os.path.join(root, n)) for n in ("AGENTS.md", "CLAUDE.md")}
    for n, t in ins.items():
        if t is None: continue
        ln = t.count("\n") + 1
        if ln > 200: add("MEDIUM", n, f"{ln} lines; long instruction files get skimmed, split or trim")
        if not t.strip(): add("MEDIUM", n, "empty")
    if ins["AGENTS.md"] and ins["CLAUDE.md"] and ins["AGENTS.md"].strip() != ins["CLAUDE.md"].strip():
        add("LOW", "AGENTS.md/CLAUDE.md", "both exist with different text; Claude Code reads CLAUDE.md first, other agents AGENTS.md: keep one source of truth")
    if not any(ins.values()): add("INFO", root, "no AGENTS.md or CLAUDE.md")
    for sf in ("settings.json", "settings.local.json"):
        p = os.path.join(root, ".claude", sf)
        if not os.path.exists(p): continue
        j = jload(p)
        if not isinstance(j, dict): continue
        for rule in (j.get("permissions") or {}).get("allow", []) or []:
            if rule in ("*", "Bash", "Bash(*)", "Bash(*:*)") or re.fullmatch(r"Bash\((sudo|rm|chmod|curl|sh|bash)[: ]\*\)", str(rule)):
                add("HIGH", p, f"over-broad allow rule: {rule}")
        for ev, groups in (j.get("hooks") or {}).items():
            for g in groups if isinstance(groups, list) else []:
                for h in g.get("hooks", []) if isinstance(g, dict) else []:
                    c = h.get("command") if isinstance(h, dict) else None
                    if c and (bad := cmd_exists(c, root)): add("HIGH", p, f"hook {ev}: '{bad}' does not exist")
    mp = os.path.join(root, ".mcp.json")
    if os.path.exists(mp):
        j = jload(mp)
        for name, s in ((j or {}).get("mcpServers") or {}).items():
            c = s.get("command")
            if c and not (shutil.which(c) or os.path.exists(c if os.path.isabs(c) else os.path.join(root, c))):
                add("HIGH", mp, f"server '{name}': command '{c}' not found")
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "build")]
        if "SKILL.md" in fn:
            t = rd(os.path.join(dp, "SKILL.md")) or ""; p = os.path.relpath(os.path.join(dp, "SKILL.md"), root)
            m = re.match(r"---\n(.*?)\n---", t, re.S)
            if not m: add("MEDIUM", p, "no frontmatter"); continue
            nm = re.search(r"^name:\s*(.+)$", m.group(1), re.M)
            if not nm: add("MEDIUM", p, "no name")
            elif nm.group(1).strip().strip("\"'") != os.path.basename(dp): add("MEDIUM", p, "name != folder")
            if not re.search(r"^description:", m.group(1), re.M): add("MEDIUM", p, "no description")
    cand = [os.path.join(root, n) for n in ("AGENTS.md", "CLAUDE.md", ".mcp.json")] + [os.path.join(root, ".claude", s) for s in ("settings.json", "settings.local.json")]
    for p in cand:
        t = rd(p)
        for i, line in enumerate((t or "").split("\n"), 1):
            if SECRET.search(line): add("HIGH", f"{os.path.relpath(p, root)}:{i}", "looks like a secret (value not shown)")
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--json"]
    if len(a) != 1 or not os.path.isdir(a[0]): print(__doc__, file=sys.stderr); sys.exit(2)
    audit(os.path.abspath(a[0]))
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}; F.sort(key=lambda f: order[f[0]])
    if "--json" in sys.argv: print(json.dumps([{"level": l, "where": w, "message": m} for l, w, m in F], indent=1))
    else:
        for l, w, m in F: print(f"{l} {w}: {m}")
        print(f"{len(F)} findings, {sum(1 for f in F if f[0] == 'HIGH')} HIGH")
    sys.exit(1 if any(f[0] == "HIGH" for f in F) else 0)
