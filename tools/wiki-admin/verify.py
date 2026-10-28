#!/usr/bin/env python3
"""Independent check of converted Markdown against its raw source (corpus-verify, Hard rule 5).

What it solves: "the tool that cleaned a file does not get a vote on whether the cleaning was
good." The converter (convert_raw_to_md.py) reads PDFs with PyMuPDF, DOCX with python-docx and
HTML with pandoc. This wrapper runs the vault's tools/check.py, which reads the same sources with
pypdf, stdlib zipfile + xml.etree, BeautifulSoup and a raw byte read, and compares named details
(versions, paths, numbers, identifiers) and text segments. It reuses check.py unchanged; it only
points it at any RAW / CLEAN pair instead of the vault's hardcoded folders.

It also refuses a pair when the converter used the checker's own extractor (then the check would
not be independent): verdict NOT-INDEPENDENT.

Before any verdict counts, a canary runs: one real pair is cut in half and must FAIL. If it does
not, the checker is broken and the run stops (exit 2), as check.py itself does.

Usage: verify.py CLEAN_DIR --raw RAW_DIR [--report DIR] [--check-py PATH]
Writes: <report>/<name>.check.md per file, FINDINGS.jsonl, SUMMARY.md.
Exit: 0 all PASS*, 1 any FAIL / ERROR / NO-SOURCE / NOT-INDEPENDENT, 2 canary broken or bad args.
"""
import argparse, importlib.util, json, os, sys
from pathlib import Path

DEFAULT_CHECK = "/storage/emulated/0/Documents/NovAExorpus/tools/check.py"
# Library names check.py extracts with; a converter naming one of these is not independent.
CHECKER_LIBS = {"pdf": "pypdf", "docx": "zipfile", "html": "beautifulsoup", "text": None}


def load_checker(path):
    spec = importlib.util.spec_from_file_location("corpus_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # check.py resolves the vault at import; it must exist
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("clean", type=Path)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--check-py", default=os.environ.get("WIKI_ADMIN_CHECK_PY", DEFAULT_CHECK))
    a = ap.parse_args(argv)
    clean, raw = a.clean.resolve(), a.raw.resolve()
    report = (a.report or clean / "_reports" / "verify").resolve()
    if not clean.is_dir() or not raw.is_dir():
        print("ERROR: CLEAN and RAW must be folders", file=sys.stderr)
        return 2
    ck = load_checker(a.check_py)
    ck.SRC, ck.CLEAN = str(raw), str(clean)

    files = sorted(p for p in clean.rglob("*.md") if "_reports" not in p.parts)
    pairs, rows = [], []
    for cp in files:
        fm, body = ck.read_clean(str(cp))
        src = fm.get("source", "").strip().strip('"')
        if not src or not (raw / src).is_file():
            rows.append({"clean": cp.relative_to(clean).as_posix(), "source": src,
                         "verdict": "NO-SOURCE", "fails": 0,
                         "detail": "no `source:` line" if not src else "source not in RAW"})
            continue
        if fm.get("type", "").strip() == "condensed":
            rows.append({"clean": cp.relative_to(clean).as_posix(), "source": src,
                         "verdict": "CONDENSED", "fails": 0, "detail": "summary by design"})
            continue
        pairs.append((cp, src, fm, body))

    # Canary: the checker must FAIL a half-cut file, or nothing it says can be trusted.
    canary = "skipped (no pair with 400+ chars)"
    for cp, src, fm, body in pairs:
        if len(body) >= 400:
            v = ck.check_one(src, str(cp), body[: len(body) // 2])[0]
            if v != "FAIL":
                print(f"Canary BROKEN: half of {cp.name} got {v}, expected FAIL")
                return 2
            canary = f"ok (half of {cp.name} -> FAIL)"
            break
    print(f"Checker: {a.check_py}\nCanary:  {canary}")

    report.mkdir(parents=True, exist_ok=True)
    findings = open(report / "FINDINGS.jsonl", "w", encoding="utf-8")
    for cp, src, fm, body in pairs:
        rel = cp.relative_to(clean).as_posix()
        kind = ck.kind_of(str(raw / src))
        lib = CHECKER_LIBS.get(kind)
        if lib and lib in fm.get("converter", "").lower():
            rows.append({"clean": rel, "source": src, "verdict": "NOT-INDEPENDENT", "fails": 0,
                         "detail": f"converter used {lib}, the checker's own extractor"})
            continue
        verdict, fnd, notes, kind, extractor, meta, _ = ck.check_one(src, str(cp), body)
        nfail = sum(1 for f in fnd if f[0] == "FAIL")
        rows.append({"clean": rel, "source": src, "verdict": verdict, "fails": nfail,
                     "detail": "; ".join(f[2] for f in fnd if f[0] == "FAIL")[:300]})
        for sev, klass, name, detail in fnd:
            findings.write(json.dumps({"source": src, "clean": rel, "kind": kind, "severity": sev,
                                       "class": klass, "finding": name, "detail": detail},
                                      ensure_ascii=False) + "\n")
        out = report / (rel.replace("/", "__")[:-3] + ".check.md")
        out.write_text(ck.render(src, str(cp), verdict, fnd, notes, kind, extractor, meta),
                       encoding="utf-8")
    findings.close()

    L = ["# Verify summary", "", f"- clean: `{clean}`", f"- raw: `{raw}`",
         f"- checker: `{a.check_py}` (independent extractors)", f"- canary: {canary}", "",
         "| clean | source | verdict | fails | detail |", "|---|---|---|---|---|"]
    for r in rows:
        L.append("| {clean} | {source} | {verdict} | {fails} | {detail} |".format(
            **{k: str(v).replace("|", "/") for k, v in r.items()}))
        print(f"  [{r['verdict']}] {r['clean']}  {r['detail'][:120]}")
    (report / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    bad = [r for r in rows if not r["verdict"].startswith(("PASS", "CONDENSED"))]
    print(f"Done: {len(rows)} checked, {len(rows) - len(bad)} pass, {len(bad)} not pass -> {report}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
