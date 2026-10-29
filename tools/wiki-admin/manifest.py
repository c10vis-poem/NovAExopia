#!/usr/bin/env python3
"""JSONL manifest (index) for a repo, a tier folder or the vault, and a lookup over it.

What it solves: agents must find files through an index instead of scanning folders
("manifest.jsonl query -> targeted leaf notes; never load a whole tier", file-administrator
AGENT.md). This extends ~/wiki-admin/tools/wiki_admin.py (path, sha256, size, summary; kept
as fields) to the tier manifest record from `_log-schema-and-JSONL-strctr.md` (Drive id
1NsLqXYuO7iFMODwN8dhOYLOnV3YiiTIv) and fixes the weaknesses listed for generate-jsonl-markers.py
in handoff/2026-10-24/extracts/wiki-admin-extract.md B9:
  - full sha256 of the file bytes (not 16 hex chars of decoded text);
  - retrieval_tokens deterministic: ranked by count, then alphabetically (not list(set)[:15]);
  - per-tier manifests (--per-tier) besides one root file;
  - the summary skips YAML frontmatter; tier comes from the path, not a "novae" substring.

Record: id, file, path, tier, category, sha256, size, tokens (estimate: chars/4), title,
semantic_summary, summary, entities_extracted, skills_tools_extracted, retrieval_tokens,
provenance_source, last_synced.

Usage:
  manifest.py build ROOT [--out FILE] [--per-tier]   (default OUT: ROOT/manifest.jsonl)
  manifest.py query WORDS... --manifest FILE [--limit N]
  manifest.py ROOT OUT                                (old wiki_admin.py form)
"""
import argparse, hashlib, json, os, re, sys
from collections import Counter
from datetime import datetime, timezone

EXTS = (".md", ".jsonl", ".json", ".py", ".js", ".ts", ".sh", ".txt", ".yaml", ".yml", ".csv")
SKIP = {".git", ".obsidian", ".trash", "node_modules", "__pycache__", "_reports"}
STOP = set("the and for with that this from into your have will what when where which their "
           "there about then than them they been were also only each more most must should "
           "would could does done using used make made over under page file files".split())
# First path component -> tier of the 5+1 model (scaffold script) and the 8-repo mirror layout.
TIERS = [
    (1, "raw", ("01_raw_sources", "raw", "raw_database", "references", "sources")),
    (2, "wiki", ("02_wiki_md", "wiki_md", "wiki", "clean_md", "openwiki", "01-inbox")),
    (3, "recall_cache", ("03_recall_cache",)),
    (4, "skills_runtime", ("04_skills_runtime", "skills", "tools", "scripts", "tool-skills")),
    (5, "episodic", ("05_episodic_logs", "audit", "pending", "questions_pending", "lint_pending")),
]
WORD = re.compile(r"[a-z0-9][a-z0-9_\-]{3,}")
TAG = re.compile(r"<[^>]+>")


def tier_of(rel):
    first = rel.split("/", 1)[0].lower() if "/" in rel else ""
    for n, name, roots in TIERS:
        if first in roots:
            return n, name
    return 0, "root"


def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm = {}
            for line in text[4:end].split("\n"):
                if ":" in line and not line.startswith((" ", "-")):
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"')
            return fm, text[end + 4:].lstrip("-\n")
    return {}, text


def tokens_for(stem, body):
    count = Counter()
    for line in body.split("\n"):
        if line.startswith("#"):
            count.update(w for w in WORD.findall(TAG.sub("", line).lower()) if w not in STOP)
    for w in WORD.findall(stem.lower().replace("_", "-")):
        if w not in STOP:
            count[w] += 2
    return [w for w, _ in sorted(count.items(), key=lambda kv: (-kv[1], kv[0]))[:15]]


def record(root, full):
    rel = os.path.relpath(full, root).replace(os.sep, "/")
    data = open(full, "rb").read()
    text = data.decode("utf-8", "replace")
    fm, body = split_frontmatter(text)
    stem = os.path.splitext(os.path.basename(full))[0]
    title = fm.get("title") or next((TAG.sub("", l).lstrip("# ").strip() for l in body.split("\n")
                                     if l.startswith("# ")), stem)
    summary = fm.get("description") or fm.get("summary") or next(
        (l.strip()[:200] for l in body.split("\n")
         if l.strip() and not l.lstrip().startswith(("#", "---", "```", "|", "<!--"))), "")
    tier, tname = tier_of(rel)
    base = os.path.basename(full)
    skills_tools = []
    if base == "SKILL.md":
        skills_tools.append({"type": "skill", "name": fm.get("name", stem), "path": rel})
    elif tier == 4 and base.endswith((".py", ".sh", ".js", ".ts")):
        skills_tools.append({"type": "tool", "name": stem, "path": rel})
    links = sorted(set(m.split("|")[0].split("#")[0].strip()
                       for m in re.findall(r"\[\[([^\]]+)\]\]", body)))
    tags = sorted(set(re.findall(r"(?<![\w#])#([A-Za-z][\w/-]+)", body)))
    return {
        "id": hashlib.sha256(rel.encode()).hexdigest()[:16],
        "file": base, "path": rel, "tier": tier,
        "category": "skill" if skills_tools and skills_tools[0]["type"] == "skill"
        else "tool" if skills_tools else tname,
        "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        "tokens": len(text) // 4, "title": title[:200],
        "semantic_summary": summary, "summary": summary or "No header found.",
        "entities_extracted": (links + ["#" + t for t in tags])[:40],
        "skills_tools_extracted": skills_tools,
        "retrieval_tokens": tokens_for(stem, body),
        "provenance_source": fm.get("source") or fm.get("original_path") or rel,
        "last_synced": datetime.fromtimestamp(os.path.getmtime(full), timezone.utc)
        .isoformat(timespec="seconds"),
    }


def build(root, out, per_tier=False):
    rows = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        for f in sorted(files):
            full = os.path.join(d, f)
            if f.endswith(EXTS) and not f.startswith("manifest") and \
                    os.path.abspath(full) != os.path.abspath(out):
                rows.append(record(root, full))
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"manifest: {len(rows)} files -> {out}")
    if per_tier:
        by = {}
        for r in rows:
            by.setdefault(r["tier"], []).append(r)
        for t, rs in sorted(by.items()):
            p = os.path.join(os.path.dirname(out) or ".", f"manifest.tier{t}.jsonl")
            with open(p, "w", encoding="utf-8") as fh:
                fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rs)
            print(f"  tier {t}: {len(rs)} -> {p}")
    return rows


def query(words, manifest, limit=10):
    terms = [w.lower() for w in words]
    hits = []
    for line in open(manifest, encoding="utf-8"):
        r = json.loads(line)
        hay_tok = set(r.get("retrieval_tokens", []))
        hay = " ".join([r["path"], r.get("title", ""), r.get("semantic_summary", "")]).lower()
        score = sum(3 * (t in hay_tok) + (t in hay) for t in terms)
        if score:
            hits.append((-score, r["path"], r))
    for _, _, r in sorted(hits)[:limit]:
        print(f"{r['path']}\t{r['title'][:60]}\t{r['semantic_summary'][:80]}")
    return [h[2] for h in sorted(hits)[:limit]]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] not in ("build", "query", "-h", "--help"):
        root = argv[0]  # legacy: wiki_admin.py [ROOT] [OUT]
        build(root, argv[1] if len(argv) > 1 else "manifest.jsonl")
        return 0
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("root"); b.add_argument("--out")
    b.add_argument("--per-tier", action="store_true")
    q = sub.add_parser("query"); q.add_argument("words", nargs="+")
    q.add_argument("--manifest", required=True); q.add_argument("--limit", type=int, default=10)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(a.root, a.out or os.path.join(a.root, "manifest.jsonl"), a.per_tier)
    else:
        query(a.words, a.manifest, a.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
