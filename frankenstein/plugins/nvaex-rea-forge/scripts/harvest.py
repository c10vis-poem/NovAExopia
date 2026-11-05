#!/usr/bin/env python3
"""rea-harvest: stage-2 triage of a repo -> CAPABILITY_CARD.json (stdlib only).
usage: harvest.py <repo> [--out DIR] [--crg]"""
import argparse, ast, hashlib, json, os, re, subprocess, sys, time

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".code-review-graph"}
LANG = {".py": "python", ".js": "javascript", ".mjs": "javascript", ".ts": "typescript",
        ".go": "go", ".rs": "rust", ".kt": "kotlin", ".java": "java", ".sh": "shell"}
TELEMETRY = re.compile(r"sentry|posthog|mixpanel|segment\.io|amplitude|google-analytics|telemetry", re.I)


def walk(root):
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in SKIP]
        for f in fs:
            yield os.path.join(d, f)


def read(p, cap=400_000):
    try:
        with open(p, "rb") as fh:
            return fh.read(cap).decode("utf-8", "replace")
    except OSError:
        return ""


def py_scan(rel, src, algos, prompts, entry):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = (n.end_lineno or n.lineno) - n.lineno + 1
            if size >= 15:
                doc = (ast.get_docstring(n) or "").strip().split("\n")[0][:160]
                algos.append({"name": n.name, "file": rel, "line": n.lineno, "lines": size, "doc": doc})
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) > 200 \
                and re.search(r"\byou are\b|\bsystem prompt\b|\byour task\b", n.value, re.I):
            prompts.append({"file": rel, "line": n.lineno, "kind": "string", "chars": len(n.value),
                            "head": n.value.strip()[:100]})
    if re.search(r"__name__\s*==\s*['\"]__main__['\"]", src):
        kind = "argparse" if "argparse" in src else "click" if "click" in src else "typer" if "typer" in src else "main"
        entry.append({"kind": kind, "file": rel, "cmd": f"python {rel}"})


def manifests(root, entry):
    pj = os.path.join(root, "package.json")
    if os.path.isfile(pj):
        try:
            j = json.loads(read(pj))
            b = j.get("bin")
            for k, v in ({j.get("name", "bin"): b} if isinstance(b, str) else (b or {})).items():
                entry.append({"kind": "npm-bin", "file": v, "cmd": k})
        except ValueError:
            pass
    pp = os.path.join(root, "pyproject.toml")
    if os.path.isfile(pp):
        m = re.search(r"\[project\.scripts\](.*?)(?:\n\[|\Z)", read(pp), re.S)
        for line in (m.group(1).splitlines() if m else []):
            mm = re.match(r"\s*([\w.-]+)\s*=\s*\"([^\"]+)\"", line)
            if mm:
                entry.append({"kind": "py-script", "file": mm.group(2), "cmd": mm.group(1)})
    for f in ("main.go", "cmd"):
        if os.path.exists(os.path.join(root, f)):
            entry.append({"kind": "go-main", "file": f, "cmd": "go run ."})


def crg(root, outdir):
    exe = subprocess.run(["sh", "-c", "command -v code-review-graph"], capture_output=True, text=True).stdout.strip()
    if not exe:
        return {"backend": "python-ast", "note": "code-review-graph not on PATH"}
    data = os.path.join(outdir, "crg-data")
    try:
        subprocess.run([exe, "build", "--repo", root, "--data-dir", data, "-q", "--skip-flows"],
                       capture_output=True, timeout=600, check=True)
        r = subprocess.run([exe, "status", "--repo", root, "--data-dir", data, "--json"],
                           capture_output=True, text=True, timeout=60)
        j = r.stdout[r.stdout.find("{"):]
        return {"backend": "code-review-graph", "status": json.loads(j), "data_dir": data}
    except Exception as e:  # fail open: AST fallback still produced the card
        return {"backend": "python-ast", "note": f"code-review-graph failed: {type(e).__name__}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("--out"); ap.add_argument("--crg", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.repo)
    if not os.path.isdir(root):
        sys.exit(f"not a directory: {root}")
    name = os.path.basename(root.rstrip("/"))
    out = os.path.abspath(a.out or os.path.join(os.getcwd(), "rea-out", name))
    os.makedirs(out, exist_ok=True)
    langs, algos, prompts, entry, telem = {}, [], [], [], []
    h = hashlib.sha256()
    for p in sorted(walk(root)):
        rel = os.path.relpath(p, root)
        ext = os.path.splitext(p)[1]
        if ext in LANG:
            langs[LANG[ext]] = langs.get(LANG[ext], 0) + 1
        src = read(p) if ext in LANG or ext == ".md" else ""
        h.update(rel.encode()); h.update(src.encode())
        if ext == ".py":
            py_scan(rel, src, algos, prompts, entry)
        if ext in LANG and TELEMETRY.search(src):
            telem.append(rel)
        base = os.path.basename(p)
        if ext == ".md" and (base in ("SKILL.md",) or re.search(r"(^|/)(prompts?|agents|commands)/", rel)):
            prompts.append({"file": rel, "line": 1, "kind": "file", "chars": len(src), "head": src.strip()[:100]})
        if ext == ".sh" and os.access(p, os.X_OK):
            entry.append({"kind": "shell", "file": rel, "cmd": f"sh {rel}"})
    manifests(root, entry)
    algos.sort(key=lambda x: -x["lines"])
    graph = crg(root, out) if a.crg else {"backend": "python-ast", "note": "pass --crg for Tree-sitter graph"}
    gate = "mcp-core" if len(entry) == 0 and algos else \
           "cli-wrap" if entry else "skill"
    if not entry and not algos:
        gate = "skill"
    card = {
        "schema": "CAPABILITY_CARD/0.1", "id": f"rea:{name}", "name": name, "source": root,
        "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "content_sha256": h.hexdigest(), "languages": langs, "ast": graph,
        "entrypoints": entry[:50], "algorithms": algos[:25], "prompts": prompts[:50],
        "telemetry_files": telem[:50], "packaging_gate": gate,
        "gate_note": "cli-wrap -> wrap.py; skill -> compile SKILL.md; mcp-core -> human decides",
    }
    with open(os.path.join(out, "CAPABILITY_CARD.json"), "w") as fh:
        json.dump(card, fh, indent=2)
    print(os.path.join(out, "CAPABILITY_CARD.json"))


if __name__ == "__main__":
    main()
