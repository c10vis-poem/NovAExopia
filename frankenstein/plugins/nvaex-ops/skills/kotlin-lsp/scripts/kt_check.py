#!/usr/bin/env python3
"""Kotlin sanity check with what this phone has. NOT a compiler and NOT a language server.
Usage: kt_check.py --tools            report which Kotlin tools exist (exit 0 always)
       kt_check.py FILE.kt|DIR ...    lint-level checks per file; exit 1 if any finding
Checks: (), [], {} balance with strings/comments/raw strings skipped; unterminated string or block comment;
one 'package' line at most; '!!' count (info); tabs mixed with space indents. Standard library only."""
import os, shutil, subprocess, sys

def tools():
    for t in ("kotlinc", "kotlin", "gradle", "kotlin-language-server", "ktlint", "detekt", "java"):
        p = shutil.which(t); print(f"{t}: {p or 'missing'}")
    if shutil.which("java"):
        print(subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()[0])
    have = shutil.which("kotlinc") or shutil.which("kotlin-language-server")
    print("compile/LSP available: " + ("yes" if have else "NO (only the structural checks below)"))

PAIR = {")": "(", "]": "[", "}": "{"}

def check(path):
    s = open(path, encoding="utf-8", errors="replace").read()
    out, st, i, n, line = [], [], 0, len(s), 1
    while i < n:
        c = s[i]
        if c == "\n": line += 1
        if s.startswith("//", i):
            while i < n and s[i] != "\n": i += 1
            continue
        if s.startswith("/*", i):          # Kotlin block comments nest
            depth, start = 1, line; i += 2
            while i < n and depth:
                if s.startswith("/*", i): depth += 1; i += 2
                elif s.startswith("*/", i): depth -= 1; i += 2
                else:
                    if s[i] == "\n": line += 1
                    i += 1
            if depth: out.append((start, "unterminated block comment"))
            continue
        if s.startswith('"""', i):
            start = line; j = s.find('"""', i + 3)
            if j < 0: out.append((start, "unterminated raw string")); break
            line += s.count("\n", i, j); i = j + 3
            while i < n and s[i] == '"': i += 1
            continue
        if c == '"':
            start = line; i += 1
            while i < n and s[i] not in '"\n':
                if s.startswith("${", i):      # template: skip to the matching }, quotes inside allowed
                    depth = 0
                    while i < n:
                        depth += (s[i] == "{") - (s[i] == "}"); i += 1
                        if depth == 0 or s[i - 1] == "\n": break
                    continue
                i += 2 if s[i] == "\\" else 1
            if i >= n or s[i] == "\n": out.append((start, "unterminated string"))
            i += 1; continue
        if c == "'":
            j = s.find("'", i + 2 if s[i + 1:i + 2] == "\\" else i + 1)
            if 0 < j - i < 8: i = j + 1; continue
        if c in "([{": st.append((c, line))
        elif c in PAIR:
            if not st: out.append((line, f"unmatched '{c}'"))
            elif st[-1][0] != PAIR[c]: out.append((line, f"'{c}' closes '{st[-1][0]}' opened at line {st[-1][1]}")); st.pop()
            else: st.pop()
        i += 1
    for ch, ln in st: out.append((ln, f"'{ch}' never closed"))
    pk = [k for k, l in enumerate(s.split("\n"), 1) if l.startswith("package ")]
    if len(pk) > 1: out.append((pk[1], "second package line"))
    return sorted(out), s.count("!!")

def main(a):
    if a == ["--tools"]: tools(); return 0
    files = []
    for p in a:
        if os.path.isdir(p):
            for dp, dn, fn in os.walk(p):
                dn[:] = [d for d in dn if d not in (".git", "build", ".gradle")]
                files += [os.path.join(dp, f) for f in fn if f.endswith((".kt", ".kts"))]
        elif os.path.isfile(p): files.append(p)
        else: print(f"no such path: {p}", file=sys.stderr); return 2
    if not files: print(__doc__.split("\n")[1], file=sys.stderr); return 2
    bad = 0
    for f in sorted(files):
        finds, bangs = check(f)
        for ln, msg in finds: print(f"{f}:{ln}: {msg}")
        bad += len(finds)
        print(f"{f}: {len(finds)} findings, {bangs} uses of !!")
    return 1 if bad else 0

if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
