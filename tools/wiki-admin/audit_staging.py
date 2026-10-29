#!/usr/bin/env python3
"""Cross-audit of staged wiki pages: the six checks that gate promotion, plus deterministic lint.

What it solves: staged pages (01-inbox/) must not reach the wiki with duplicates, broken links,
bad names, missing indexes or leaked credentials. The six checks and the three verdicts are the
Cross-Auditor template (handoff/2026-10-24/extracts/latest-config-extract.md lines 117 and 333):
duplicates, orphans, naming canon, contradictions vs accepted ADRs, missing MAP.md, credential
leakage -> promotion_recommended / promotion_blocked / needs_human_review. Phase 1 of the
llm-wiki-nocode lint (broken links, orphans, missing/invalid frontmatter) is folded in.
It never modifies staged files: it flags, it does not resolve. Contradictions are not decidable
by a script; pages mentioning an ADR topic are sent to needs_human_review.

Usage: audit_staging.py STAGING_DIR [--wiki WIKI_DIR] [--adr-dir DIR] [--root DIR] [--report DIR]
Writes AUDIT.md and audit.jsonl. Exit 1 if any file is promotion_blocked.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

REQUIRED_FM = ("id", "type", "created", "updated", "sources")
SECRETS = [
    ("openai/anthropic-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
    ("mem0 key", re.compile(r"\bm0sk_[A-Za-z0-9]{8,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("private key block", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
    ("connection string with password", re.compile(r"\b\w+://[^/\s:@]+:[^@\s]{3,}@")),
]
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
LINK = re.compile(r"\[\[([^\]|#]+)")


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fm = {}
    for line in text[4:end].split("\n"):
        if ":" in line and not line.startswith((" ", "-")):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def page_names(folder):
    if not folder or not folder.is_dir():
        return {}
    return {p.stem.lower(): p for p in folder.rglob("*.md") if "_reports" not in p.parts}


def audit(staging, wiki=None, adr_dir=None, root=None):
    root = root or staging.parent
    staged = sorted(p for p in staging.rglob("*.md")
                    if "_reports" not in p.parts and p.name not in ("MAP.md", "index.md"))
    wiki_pages = page_names(wiki)
    known = {**wiki_pages, **page_names(staging)}
    wiki_hash = {}
    for p in wiki_pages.values():
        wiki_hash.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), p)
    adr_topics = sorted({w for p in (adr_dir.rglob("*.md") if adr_dir and adr_dir.is_dir() else [])
                         for w in re.findall(r"[a-z][a-z0-9\-]{5,}", p.stem.lower())})
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in staged}
    seen_hash, inbound = {}, {p.stem.lower(): 0 for p in staged}
    for p, t in texts.items():
        for l in LINK.findall(t):
            k = Path(l.strip()).stem.lower()
            if k in inbound and k != p.stem.lower():
                inbound[k] += 1
    if wiki:
        for p in wiki_pages.values():
            for l in LINK.findall(p.read_text(encoding="utf-8", errors="replace")):
                k = Path(l.strip()).stem.lower()
                if k in inbound:
                    inbound[k] += 1
    rows = []
    for p, t in texts.items():
        block, review = [], []
        h = hashlib.sha256(t.encode()).hexdigest()
        # 1 duplicates
        if h in wiki_hash:
            block.append(f"duplicate of wiki page {wiki_hash[h].name}")
        if h in seen_hash:
            block.append(f"duplicate of staged {seen_hash[h].name}")
        seen_hash.setdefault(h, p)
        # 2 orphans + broken links
        broken = sorted({l.strip() for l in LINK.findall(t) if Path(l.strip()).stem.lower() not in known})
        if broken:
            block.append("broken wikilinks: " + ", ".join(broken[:8]))
        if inbound.get(p.stem.lower(), 0) == 0:
            review.append("orphan: no page links here (add it to index.md or a MAP.md)")
        # 3 naming canon
        if not KEBAB.match(p.name):
            block.append(f"name not kebab-case: {p.name}")
        if p.name.lower().startswith("nova-"):
            block.append("vendor prefix NovA- in name (removed whenever touched)")
        # 4 contradictions vs ADRs (human)
        touched = [w for w in adr_topics if w in t.lower()]
        if touched:
            review.append("touches ADR topics, check for contradiction: " + ", ".join(touched[:5]))
        # 5 missing MAP.md
        if not (p.parent / "MAP.md").exists() and not (p.parent / "index.md").exists():
            review.append(f"folder {p.parent.name}/ has no MAP.md or index.md")
        # 6 credential leakage
        for name, rx in SECRETS:
            if rx.search(t):
                block.append(f"credential pattern: {name}")
        # lint: frontmatter
        fm = frontmatter(t)
        if fm is None:
            block.append("no YAML frontmatter")
        else:
            miss = [k for k in REQUIRED_FM if not fm.get(k)]
            if miss:
                block.append("frontmatter missing: " + ", ".join(miss))
            if fm.get("dry_run", "").lower() == "true":
                block.append("dry-run placeholder draft (no model output yet)")
            srcs = [x.strip().strip("'\"") for x in fm.get("sources", "").strip("[]").split(",") if x.strip()]
            gone = [x for x in srcs if not (Path(x) if Path(x).is_absolute() else root / x).exists()]
            if gone:
                block.append("sources not found: " + ", ".join(gone[:5]))
        verdict = ("promotion_blocked" if block else
                   "needs_human_review" if review else "promotion_recommended")
        rows.append({"file": p.relative_to(staging).as_posix(), "sha256": h,
                     "verdict": verdict, "blocking": block, "review": review})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("staging", type=Path)
    ap.add_argument("--wiki", type=Path)
    ap.add_argument("--adr-dir", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--root", type=Path, help="folder relative `sources` resolve against (default: parent of STAGING)")
    a = ap.parse_args(argv)
    rows = audit(a.staging.resolve(), a.wiki and a.wiki.resolve(), a.adr_dir, a.root and a.root.resolve())
    rep = (a.report or a.staging / "_reports" / "audit").resolve()
    rep.mkdir(parents=True, exist_ok=True)
    with open(rep / "audit.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    L = ["# Cross-audit of staged pages", "", f"- staging: `{a.staging}`", f"- wiki: `{a.wiki}`", ""]
    for r in rows:
        L.append(f"## {r['file']}: {r['verdict']}")
        L += [f"- BLOCK: {x}" for x in r["blocking"]] + [f"- review: {x}" for x in r["review"]] + [""]
        print(f"  [{r['verdict']}] {r['file']}  " + "; ".join(r["blocking"] + r["review"])[:160])
    (rep / "AUDIT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Done: {len(rows)} staged files -> {rep}")
    return 1 if any(r["verdict"] == "promotion_blocked" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
