#!/usr/bin/env python3
"""wiki_dedup.py WIKI [--min 0.75]: report candidate duplicate pages. Report only; never edits or merges.
Score = max(title token Jaccard, edit ratio, 0.75 if one title contains the other), +0.30 alias cross-match,
+0.05 same folder, +0.10 for >=3 shared tags (+0.05 for 2), capped 1.0. HIGH >= 0.90, MEDIUM >= --min.
Skips index.md/log.md/MAP.md and pages with redirects_to. Output JSON lines, best first."""
import argparse, difflib, json, re, sys
from itertools import combinations
from pathlib import Path

SKIP = {"index.md", "log.md", "map.md", "hot.md"}


def meta(path):
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    fm = {}
    if m:
        for l in m.group(1).splitlines():
            if ":" in l and not l.startswith((" ", "-")):
                k, v = l.split(":", 1); fm[k.strip()] = v.strip()
    lst = lambda v: {x.strip(" \"'").lower() for x in v.strip("[]").split(",") if x.strip(" \"'")}
    h1 = re.search(r"(?m)^#\s+(.+)$", t)
    title = (fm.get("title") or (h1.group(1) if h1 else path.stem)).strip(" \"'")
    return {"title": title, "aliases": lst(fm.get("aliases", "")), "tags": lst(fm.get("tags", "")),
            "redirect": "redirects_to" in fm}


def toks(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def score(a, b, fa, fb):
    ta, tb = a["title"].lower(), b["title"].lower()
    A, B = toks(ta), toks(tb)
    t = max(len(A & B) / len(A | B) if A | B else 0, difflib.SequenceMatcher(None, ta, tb).ratio())
    if (ta in tb or tb in ta) and min(len(ta), len(tb)) >= 3:
        t = max(t, 0.75)
    s = t + (0.30 if ta in b["aliases"] or tb in a["aliases"] else 0) + (0.05 if fa.parent == fb.parent else 0)
    shared = len(a["tags"] & b["tags"])
    return round(min(s + (0.10 if shared >= 3 else 0.05 if shared == 2 else 0), 1.0), 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("wiki", type=Path); ap.add_argument("--min", type=float, default=0.75)
    a = ap.parse_args()
    pages = {}
    for f in sorted(a.wiki.rglob("*.md")):
        if f.name.lower() in SKIP or any(p.startswith(".") for p in f.relative_to(a.wiki).parts):
            continue
        m = meta(f)
        if not m["redirect"]:
            pages[f] = m
    if len(pages) < 10:
        print(f"{len(pages)} pages: too few for meaningful duplicates (pairs still scored)", file=sys.stderr)
    out = []
    for (f1, m1), (f2, m2) in combinations(pages.items(), 2):
        s = score(m1, m2, f1, f2)
        if s >= a.min:
            out.append({"score": s, "label": "HIGH" if s >= 0.90 else "MEDIUM",
                        "a": str(f1.relative_to(a.wiki)), "b": str(f2.relative_to(a.wiki))})
    for o in sorted(out, key=lambda o: -o["score"]):
        print(json.dumps(o))
    print(f"{len(pages)} pages, {len(out)} candidate pairs", file=sys.stderr)


if __name__ == "__main__":
    main()
