#!/usr/bin/env python3
"""Read and lightly edit docx, xlsx, pptx and pdf with the standard library plus tools on the phone.
  office.py text FILE                  plain text (docx paragraphs, xlsx rows as TSV per sheet, pptx slide text, pdf via pdftotext)
  office.py replace FILE OLD NEW OUT   docx/pptx/xlsx: replace OLD with NEW inside text nodes, write a NEW file OUT (never in place)
  office.py pages FILE.pdf RANGE OUT   pdf: keep pages (1-based, e.g. 1-3,5) using pypdf, else mutool
  office.py tools                      which helpers exist
Limits: replace only matches text that sits inside ONE run/text node (Word splits words across runs when formatting changes);
it reports how many it replaced, and 0 means nothing was changed. No macros, no images, no formulas recalculation.
Exit: 0 ok, 1 nothing replaced or tool failure, 2 usage, 3 required tool missing."""
import os, re, shutil, subprocess, sys, zipfile
import xml.etree.ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
for k, v in NS.items(): ET.register_namespace(k, v)
KIND = {".docx": "docx", ".xlsx": "xlsx", ".pptx": "pptx", ".pdf": "pdf"}

def kind(p):
    k = KIND.get(os.path.splitext(p)[1].lower())
    if not k: sys.exit("unsupported type (docx, xlsx, pptx, pdf)")
    return k

def natural(names, prefix):
    return sorted([n for n in names if re.fullmatch(prefix + r"\d+\.xml", n)], key=lambda n: int(re.findall(r"\d+", n)[-1]))

def text(path):
    k = kind(path)
    if k == "pdf":
        if not shutil.which("pdftotext"): sys.exit("pdftotext missing")
        return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout
    z = zipfile.ZipFile(path); out = []
    if k == "docx":
        root = ET.fromstring(z.read("word/document.xml"))
        for p in root.iter("{%(w)s}p" % NS):
            out.append("".join(t.text or "" for t in p.iter("{%(w)s}t" % NS)))
    elif k == "pptx":
        for i, n in enumerate(natural(z.namelist(), r"ppt/slides/slide"), 1):
            root = ET.fromstring(z.read(n)); out.append(f"--- slide {i} ---")
            for p in root.iter("{%(a)s}p" % NS):
                out.append("".join(t.text or "" for t in p.iter("{%(a)s}t" % NS)))
    else:
        sst = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter("{%(s)s}si" % NS):
                sst.append("".join(t.text or "" for t in si.iter("{%(s)s}t" % NS)))
        for i, n in enumerate(natural(z.namelist(), r"xl/worksheets/sheet"), 1):
            out.append(f"--- sheet {i} ---")
            for row in ET.fromstring(z.read(n)).iter("{%(s)s}row" % NS):
                cells = []
                for c in row.iter("{%(s)s}c" % NS):
                    v = c.find("s:v", NS); t = c.get("t")
                    if t == "inlineStr": val = "".join(x.text or "" for x in c.iter("{%(s)s}t" % NS))
                    elif v is None: val = ""
                    elif t == "s": val = sst[int(v.text)]
                    else: val = v.text or ""
                    cells.append(val)
                out.append("\t".join(cells))
    return "\n".join(out) + "\n"

def replace(path, old, new, outp):
    k = kind(path)
    if k == "pdf": sys.exit("pdf text is not editable here; regenerate the source document")
    if os.path.abspath(outp) == os.path.abspath(path): sys.exit("OUT must differ from FILE")
    tag = {"docx": ("word/document.xml", "w"), "pptx": (None, "a"), "xlsx": ("xl/sharedStrings.xml", "s")}[k]
    zin = zipfile.ZipFile(path); count = 0
    with zipfile.ZipFile(outp, "w", zipfile.ZIP_DEFLATED) as zo:
        for item in zin.infolist():
            data = zin.read(item.filename)
            hit = (item.filename == tag[0]) if tag[0] else re.fullmatch(r"ppt/slides/slide\d+\.xml", item.filename)
            if hit:
                root = ET.fromstring(data)
                for t in root.iter("{%s}t" % NS[tag[1]]):
                    if t.text and old in t.text:
                        count += t.text.count(old); t.text = t.text.replace(old, new)
                data = ET.tostring(root, xml_declaration=True, encoding="UTF-8")
            zo.writestr(item, data)
    if not count: os.remove(outp)
    print(f"replaced {count}" + ("" if count else " (nothing written; text may be split across runs)"))
    return 0 if count else 1

def pages(path, rng, outp):
    if kind(path) != "pdf": sys.exit("pages needs a pdf")
    idx = []
    for part in rng.split(","):
        a, _, b = part.partition("-"); idx += list(range(int(a), int(b or a) + 1))
    try:
        from pypdf import PdfReader, PdfWriter
        r = PdfReader(path); w = PdfWriter()
        for i in idx: w.add_page(r.pages[i - 1])
        with open(outp, "wb") as f: w.write(f)
    except ImportError:
        if not shutil.which("mutool"): sys.exit("neither pypdf nor mutool available")
        subprocess.run(["mutool", "clean", path, outp, rng], check=True)
    print(f"wrote {outp}")
    return 0

def main(a):
    if a[:1] == ["tools"]:
        for t in ("pdftotext", "pdftoppm", "mutool", "pandoc", "tesseract", "unzip", "zip"): print(f"{t}: {shutil.which(t) or 'missing'}")
        for m in ("docx", "pypdf", "pdfminer", "openpyxl", "pptx"):
            try: __import__(m); print(f"python {m}: yes")
            except ImportError: print(f"python {m}: no")
        return 0
    if a[:1] == ["text"] and len(a) == 2: sys.stdout.write(text(a[1])); return 0
    if a[:1] == ["replace"] and len(a) == 5: return replace(*a[1:])
    if a[:1] == ["pages"] and len(a) == 4: return pages(*a[1:])
    print(__doc__, file=sys.stderr); return 2

if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
