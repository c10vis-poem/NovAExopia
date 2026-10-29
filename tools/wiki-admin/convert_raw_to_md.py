#!/usr/bin/env python3
"""Raw dump -> Markdown, with every failure and every empty result reported.

What it solves: the operator's `convert-raw-to-md.py` (Drive `_02.wiki-admn-docs/Scripts`,
id 1LRsROVSTq9BJcaHho5sz8eitOHln-xvj) printed a tick or a cross and moved on. Scanned PDFs came
out as empty Markdown files that looked converted (74 of 128 PDFs in one run), and two sources
with the same stem (`a.pdf`, `a.txt`) overwrote each other. This version keeps its extractors
and frontmatter, and adds:
  - a report (`report.jsonl` + `REPORT.md`) listing every file: converted, unchanged,
    unsupported, EMPTY (no text came out, nothing written) or ERROR (with the exception);
  - output names that keep the source extension (`a.pdf` -> `a.pdf.md`), so nothing collides;
  - full sha256 of the source in the frontmatter; "unchanged" means same hash, not newer mtime;
  - a `source:` line relative to RAW, which is how `verify.py` (check.py) pairs the files.
It never edits RAW. It never judges its own output: run `verify.py` for that.

Extractors (chosen to be disjoint from check.py's pypdf / zipfile / BeautifulSoup):
  .pdf  PyMuPDF (fitz)          .docx python-docx (paragraphs + tables, in order)
  .html pandoc -t gfm-raw_html          .txt  read as UTF-8, wrapped in "# <stem>"
  .md   copied as is

Usage: convert_raw_to_md.py RAW_DIR OUT_DIR [--report DIR] [--min-chars N] [--force]
Exit: 0 all good, 1 any ERROR or EMPTY file (the report says which), 2 bad arguments.
"""
import argparse, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

TOOL = "wiki-admin/convert_raw_to_md.py"


def convert_pdf(path):
    import pymupdf  # PyMuPDF
    with pymupdf.open(str(path)) as doc:
        return "\n\n".join(page.get_text() for page in doc)


def convert_docx(path):
    from docx import Document
    from docx.table import Table
    doc, lines = Document(str(path)), []
    for block in doc.iter_inner_content():
        if isinstance(block, Table):
            for row in block.rows:
                lines.append("| " + " | ".join(c.text.strip() for c in row.cells) + " |")
            continue
        style = block.style.name if block.style is not None else ""
        if style.startswith("Heading ") and style[8:].isdigit():
            lines.append("#" * int(style[8:]) + " " + block.text)
        else:
            lines.append(block.text)
    return "\n\n".join(lines)


def convert_html(path):
    r = subprocess.run(["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none", str(path)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError("pandoc exit %d: %s" % (r.returncode, r.stderr.strip()[:300]))
    return r.stdout


def convert_txt(path):
    return "# %s\n\n%s" % (path.stem, path.read_text(encoding="utf-8", errors="replace"))


CONVERTERS = {
    ".pdf": (convert_pdf, "PyMuPDF"),
    ".docx": (convert_docx, "python-docx"),
    ".html": (convert_html, "pandoc"),
    ".htm": (convert_html, "pandoc"),
    ".txt": (convert_txt, "utf-8 read"),
    ".md": (lambda p: p.read_text(encoding="utf-8", errors="replace"), "copy"),
}


def out_name(rel):
    """a.pdf -> a.pdf.md, a.md -> a.md: two sources never share one output."""
    return rel if rel.suffix.lower() == ".md" else rel.with_name(rel.name + ".md")


def existing_sha(path):
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return None
    for line in head.split("\n")[1:40]:
        if line.startswith("source_sha256:"):
            return line.split(":", 1)[1].strip().strip('"')
        if line == "---":
            break
    return None


def frontmatter(src, rel, sha, extractor):
    q = lambda s: json.dumps(str(s), ensure_ascii=False)
    return ("---\n"
            f"source: {q(rel.as_posix())}\n"
            f"source_file: {q(src.name)}\n"
            f"source_format: {q(src.suffix.lower())}\n"
            f"source_sha256: {sha}\n"
            f"original_path: {q(src)}\n"
            f"converted_at: {q(datetime.now(timezone.utc).isoformat(timespec='seconds'))}\n"
            f"converter: {q(TOOL + ' (' + extractor + ')')}\n"
            "status: staged\n"
            "---\n\n")


def run(raw, out, min_chars=20, force=False):
    rows = []
    for src in sorted(p for p in raw.rglob("*") if p.is_file()):
        rel = src.relative_to(raw)
        if any(part.startswith(".") for part in rel.parts):
            continue
        row = {"source": rel.as_posix(), "bytes": src.stat().st_size}
        conv = CONVERTERS.get(src.suffix.lower())
        if conv is None:
            rows.append({**row, "status": "unsupported",
                         "detail": "no converter for %r (try anydoc or litedoc)" % src.suffix})
            continue
        fn, extractor = conv
        data = src.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        dest = out / out_name(rel)
        row.update(output=dest.relative_to(out).as_posix(), sha256=sha, extractor=extractor)
        if not force and dest.exists() and existing_sha(dest) == sha:
            rows.append({**row, "status": "unchanged", "detail": "same source sha256"})
            continue
        try:
            body = fn(src)
        except Exception as ex:  # report every failure, never stop the batch
            rows.append({**row, "status": "error", "detail": "%s: %s" % (type(ex).__name__, ex)})
            continue
        text_chars = len("".join(body.split()))
        row["chars"] = text_chars
        if text_chars < min_chars:
            hint = " (scanned PDF? needs OCR)" if src.suffix.lower() == ".pdf" else ""
            rows.append({**row, "status": "empty",
                         "detail": "%d non-space chars extracted, under %d; nothing written%s"
                         % (text_chars, min_chars, hint)})
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(frontmatter(src, rel, sha, extractor) + body.rstrip() + "\n",
                        encoding="utf-8")
        rows.append({**row, "status": "converted", "detail": ""})
    return rows


def write_report(rows, raw, out, report_dir):
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "report.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    count = {}
    for r in rows:
        count[r["status"]] = count.get(r["status"], 0) + 1
    L = ["# Conversion report", "",
         f"- raw: `{raw}`", f"- out: `{out}`",
         f"- run: {datetime.now(timezone.utc).isoformat(timespec='seconds')}", "",
         "| status | files |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(count.items())]
    for status in ("error", "empty", "unsupported"):
        bad = [r for r in rows if r["status"] == status]
        if bad:
            L += ["", f"## {status} ({len(bad)})", ""]
            L += [f"- `{r['source']}`: {r['detail']}" for r in bad]
    (report_dir / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return count


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("raw", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--report", type=Path, help="report folder (default OUT/_reports/convert)")
    ap.add_argument("--min-chars", type=int, default=20)
    ap.add_argument("--force", action="store_true", help="reconvert even when unchanged")
    a = ap.parse_args(argv)
    raw, out = a.raw.expanduser().resolve(), a.out.expanduser().resolve()
    if not raw.is_dir():
        print(f"ERROR: {raw} is not a folder", file=sys.stderr)
        return 2
    if out == raw or raw in out.parents:
        print("ERROR: OUT must not be inside RAW (raw sources are never written)", file=sys.stderr)
        return 2
    rows = run(raw, out, a.min_chars, a.force)
    count = write_report(rows, raw, out, (a.report or out / "_reports" / "convert").resolve())
    for r in rows:
        mark = {"converted": "ok", "unchanged": "--"}.get(r["status"], r["status"].upper())
        print(f"  [{mark}] {r['source']}" + (f"  {r['detail']}" if r.get("detail") else ""))
    print("Done: " + ", ".join(f"{v} {k}" for k, v in sorted(count.items())))
    return 1 if count.get("error") or count.get("empty") else 0


if __name__ == "__main__":
    sys.exit(main())
