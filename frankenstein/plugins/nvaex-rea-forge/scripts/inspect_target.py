#!/usr/bin/env python3
"""Read-only summary of a repo or folder: extensions, manifests, entrypoints, sensitive-looking files. Stdlib only.
Usage: inspect_target.py <path>. Prints JSON. Called by the rea.inspect_target tool (mcp/rea-mcp)."""
import json, os, re, sys

SKIP = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".gradle"}
MANIFESTS = ["package.json", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod", "build.gradle",
             "build.gradle.kts", "AndroidManifest.xml", "Makefile", "Dockerfile", "plugin.json", "SKILL.md", "server.json"]


def inspect(path, max_files=5000):
    root = os.path.realpath(os.path.expanduser(path))
    if not os.path.isdir(root): return {"error": "not a directory: " + root}
    exts, manifests, entry, flags, n = {}, [], [], [], 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            n += 1
            if n > max_files: break
            rel = os.path.relpath(os.path.join(d, f), root)
            e = os.path.splitext(f)[1].lower() or f
            exts[e] = exts.get(e, 0) + 1
            if f in MANIFESTS and rel.count(os.sep) <= 2: manifests.append(rel)
            if re.match(r"(main|index|server|cli|app)\.\w+$", f) and rel.count(os.sep) <= 2: entry.append(rel)
            if re.search(r"(\.env|id_rsa|\.pem|secret|credential)", f.lower()): flags.append(rel)
        if n > max_files: break
    head = ""
    for r in ("README.md", "readme.md"):
        try:
            head = open(os.path.join(root, r), encoding="utf-8", errors="replace").read(600); break
        except OSError: pass
    git = None
    try: git = open(os.path.join(root, ".git/HEAD")).read().strip()
    except OSError: pass
    return {"path": root, "files_scanned": min(n, max_files), "truncated": n > max_files,
            "top_extensions": dict(sorted(exts.items(), key=lambda kv: -kv[1])[:10]),
            "manifests": manifests[:20], "entrypoints": entry[:20], "sensitive_looking_files": flags[:20],
            "git_head": git, "readme_head": head, "read_only": True}


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit("usage: inspect_target.py <path>")
    print(json.dumps(inspect(sys.argv[1])))
