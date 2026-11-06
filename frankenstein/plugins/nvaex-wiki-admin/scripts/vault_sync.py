#!/usr/bin/env python3
"""vault_sync.py SRC DEST [--ext .md,.pdf] [--apply]: copy project docs into DEST/<project>/.
Reduced from obsidian-sync (MIT): copy only (no symlink/move), DEST is mandatory (no vault auto-detect),
dry-run unless --apply. Nothing in SRC is changed. Flattens a/b/c/f.md -> a-b-c/f.md; skips CLAUDE.md,
.git, .claude, node_modules, venvs, build dirs. Writes DEST/<project>/.sync-manifest.json (sha256 per file)."""
import argparse, hashlib, json, shutil, sys
from pathlib import Path

SKIP_DIRS = {".claude", ".claude-plugin", ".git", ".github", "node_modules", "venv", ".venv", "env", "build", "dist", "__pycache__", ".pytest_cache"}
SKIP_FILES = {"CLAUDE.md", "__context__.md"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path); ap.add_argument("dest", type=Path)
    ap.add_argument("--ext", default=".md,.pdf"); ap.add_argument("--project")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    src, exts = a.src.resolve(), tuple(e.strip().lower() for e in a.ext.split(","))
    if not src.is_dir():
        sys.exit(f"not a directory: {src}")
    out = a.dest.resolve() / (a.project or src.name)
    if src == out or src in out.parents:
        sys.exit("DEST must be outside SRC")
    plan, manifest = [], {}
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src)
        if not f.is_file() or f.suffix.lower() not in exts or f.name in SKIP_FILES or SKIP_DIRS & set(rel.parts):
            continue
        t = out / ("-".join(rel.parts[:-1]) or ".") / rel.name
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        state = "same" if t.is_file() and hashlib.sha256(t.read_bytes()).hexdigest() == h else "update" if t.exists() else "new"
        plan.append((f, t, state)); manifest[str(t.relative_to(out))] = h
    for f, t, s in plan:
        print(f"{s:6} {f.relative_to(src)} -> {t.relative_to(out.parent)}")
        if a.apply and s != "same":
            t.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, t)
    if a.apply:
        out.mkdir(parents=True, exist_ok=True)
        (out / ".sync-manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(plan)} files; {'applied' if a.apply else 'dry-run (add --apply)'}", file=sys.stderr)


if __name__ == "__main__":
    main()
