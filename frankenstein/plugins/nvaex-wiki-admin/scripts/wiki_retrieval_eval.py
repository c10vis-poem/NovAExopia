#!/usr/bin/env python3
"""wiki_retrieval_eval.py CASES.jsonl --wiki DIR [--k 5]: score wiki_search against known answers.
CASES: one JSON per line {"q": "question", "expect": ["slug", ...]}  (slug = page file stem as wiki_search reports it).
Prints per case: hit@k, reciprocal rank, recall@k, the ranked slugs; then hit@k rate and MRR (named, with N).
For a miss it says which stage broke: page absent from the wiki / page present but not retrieved / retrieved below k.
Exit 1 if any case misses. Stdlib; runs wiki_search.py --json (BM25)."""
import argparse, json, subprocess, sys
from pathlib import Path

S = Path(__file__).with_name("wiki_search.py")


def ranked(q, wiki, top):
    r = subprocess.run([sys.executable, str(S), q, "--wiki", wiki, "--json", "--top", str(top), "--per-page", "1"],
                       capture_output=True, text=True, timeout=120)
    try:
        return [x["slug"] for x in json.loads(r.stdout)["results"]]
    except Exception:
        sys.exit(f"wiki_search failed for {q!r}: {r.stderr.strip()[:200]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cases", type=Path); ap.add_argument("--wiki", required=True); ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()
    slugs = {p.stem for p in Path(a.wiki).rglob("*.md")}
    cases = [json.loads(l) for l in a.cases.read_text().splitlines() if l.strip()]
    hits, rrs, bad = 0, 0.0, 0
    for c in cases:
        exp, got = set(c["expect"]), ranked(c["q"], a.wiki, 50)
        first = next((i for i, s in enumerate(got, 1) if s in exp), 0)
        hit = 1 if 0 < first <= a.k else 0
        rec = len(exp & set(got[:a.k])) / len(exp)
        rr = 1 / first if first else 0.0
        hits += hit; rrs += rr
        why = "" if hit else (" MISS: expected page absent from wiki" if not exp & slugs else
                              f" MISS: retrieved at rank {first}, below k={a.k}" if first else " MISS: page exists but was not retrieved")
        bad += not hit
        print(f"hit@{a.k}={hit} rr={rr:.2f} recall@{a.k}={rec:.2f} q={c['q']!r} got={got[:a.k]}{why}")
    n = len(cases)
    print(f"hit@{a.k} rate {hits}/{n}; MRR {rrs / n:.3f} (N={n} questions, page-level slugs)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
