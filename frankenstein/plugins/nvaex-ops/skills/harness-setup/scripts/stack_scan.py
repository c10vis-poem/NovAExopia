#!/usr/bin/env python3
"""Read-only stack scan of a project folder. Usage: stack_scan.py DIR [--json]. Standard library only."""
import json, os, re, sys
from collections import Counter
SKIP = {".git", "node_modules", "build", "dist", ".gradle", "__pycache__", ".venv", "venv", "target", ".next"}
LANG = {".py": "python", ".js": "javascript", ".mjs": "javascript", ".ts": "typescript", ".tsx": "typescript", ".kt": "kotlin", ".kts": "kotlin",
        ".java": "java", ".go": "go", ".rs": "rust", ".sh": "shell", ".c": "c", ".cpp": "c++", ".swift": "swift", ".rb": "ruby", ".md": "markdown", ".json": "json", ".yml": "yaml", ".yaml": "yaml"}
INSTR = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", ".claude/settings.json", ".claude/settings.local.json", ".mcp.json", ".claude-plugin/plugin.json", "RESUME.md"]
def scan(root):
    langs, folders, files, ci = Counter(), set(), set(), []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP)
        rel = os.path.relpath(dp, root)
        if rel == ".": folders = {d for d in dn if not d.startswith(".")}
        if rel.startswith(os.path.join(".github", "workflows")): ci += [os.path.join(rel, f) for f in fn]
        for f in fn:
            langs[LANG.get(os.path.splitext(f)[1].lower(), "other")] += 1
            if rel == ".": files.add(f)
    cmds = []
    def has(n): return n in files
    if has("package.json"):
        try: cmds += [f"npm run {k}  # {v[:60]}" for k, v in json.load(open(os.path.join(root, "package.json"))).get("scripts", {}).items()]
        except Exception: cmds.append("package.json present but unreadable")
    if has("Makefile"):
        cmds += [f"make {m}" for m in re.findall(r"^([A-Za-z][\w-]*):", open(os.path.join(root, "Makefile"), errors="replace").read(), re.M)[:12]]
    for f, c in (("pyproject.toml", "python project (see pyproject.toml for test/lint config)"), ("Cargo.toml", "cargo build / cargo test"), ("go.mod", "go build ./... / go test ./..."),
                 ("gradlew", "./gradlew build (needs Gradle + Android SDK)"), ("requirements.txt", "pip deps in requirements.txt")):
        if has(f): cmds.append(c)
    for dirpath in ("tests", "test"):
        if os.path.isdir(os.path.join(root, dirpath)):
            for s in sorted(os.listdir(os.path.join(root, dirpath))):
                if s.endswith(".sh") and "selftest" in s: cmds.append(f"bash {dirpath}/{s}")
    instr = [i for i in INSTR if os.path.exists(os.path.join(root, i))]
    return {"root": os.path.abspath(root), "languages": dict(langs.most_common(8)), "commands": cmds, "ci": ci, "instruction_files": instr, "top_folders": sorted(folders)}
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--json"]
    if len(a) != 1 or not os.path.isdir(a[0]): print(__doc__, file=sys.stderr); sys.exit(2)
    r = scan(a[0])
    if "--json" in sys.argv: print(json.dumps(r, indent=1)); sys.exit(0)
    print("root:", r["root"]); print("languages:", ", ".join(f"{k} {v}" for k, v in r["languages"].items()) or "none")
    print("instruction files:", ", ".join(r["instruction_files"]) or "none"); print("ci:", ", ".join(r["ci"]) or "none")
    print("top folders:", ", ".join(r["top_folders"]) or "none"); print("commands seen:"); [print("  " + c) for c in r["commands"]] or print("  none")
