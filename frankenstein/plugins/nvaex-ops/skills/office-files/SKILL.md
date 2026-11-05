---
name: office-files
description: Read and edit Word (.docx), Excel (.xlsx), PowerPoint (.pptx) and PDF files on this phone with shell and Python only. Use when the user hands over an office document to read, search, patch text in, or split.
---

# office-files

Uses `scripts/office.py` (standard library) plus `pdftotext`, `pypdf` or `mutool` already on the phone. No Desktop Commander, no MCP, no LibreOffice (absent). Run `python3 -I scripts/office.py tools` to see what exists (checked 2026-11-05: pdftotext, mutool, pandoc, tesseract present; python-docx, pypdf, PyMuPDF present; openpyxl and python-pptx absent, so xlsx and pptx are handled as raw XML).

## Read
`python3 -I scripts/office.py text FILE` prints text: docx paragraphs, xlsx rows as tab-separated lines per sheet (shared strings resolved, formulas show their last cached value), pptx slide text, pdf layout text.
- Scanned PDFs have no text layer: `pdftoppm -r 200 -png in.pdf pg` then `tesseract pg-1.png out` (both present).
- Richer docx conversion: `pandoc in.docx -t markdown`.
- Big sheets: pipe through `head`/`grep`; do not paste whole sheets into the chat.

## Edit
- Text swap: `python3 -I scripts/office.py replace IN OLD NEW OUT` writes a NEW file; it refuses in-place edits. It prints `replaced N`; `0` means nothing matched (Word often splits one phrase across runs; try a shorter phrase) and no file is written.
- PDF pages: `python3 -I scripts/office.py pages in.pdf 1-3,5 out.pdf`.
- Anything structural (new tables, styles, formulas, charts) is out of reach here. Say so, or generate the file from the source in code (`python-docx` is available for docx).
- Always keep the original; show the user the `text` output of the result before calling the edit done.

## Do not
Open files from untrusted sources with macro-capable tools; this path never executes macros. Do not upload documents anywhere.
