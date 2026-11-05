#!/usr/bin/env python3
"""Build real docx/xlsx/pptx/pdf files on the fly and run office.py against them."""
import os, subprocess, sys, tempfile, zipfile
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "office-files", "scripts", "office.py")
d = tempfile.mkdtemp()
def run(*a):
    r = subprocess.run([sys.executable, "-I", O, *a], capture_output=True, text=True); return r.returncode, r.stdout
def mk(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for n, c in files.items(): z.writestr(n, c)
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
# docx: python-docx if present (a real writer), else a hand-built one
dx = os.path.join(d, "a.docx")
try:
    import docx; D = docx.Document(); D.add_paragraph("Hello ACME world"); D.add_paragraph("second line"); D.save(dx)
except ImportError:
    mk(dx, {"word/document.xml": f'<w:document {W}><w:body><w:p><w:r><w:t>Hello ACME world</w:t></w:r></w:p><w:p><w:r><w:t>second line</w:t></w:r></w:p></w:body></w:document>'})
rc, out = run("text", dx); assert rc == 0 and "Hello ACME world" in out and "second line" in out, out
rc, out = run("replace", dx, "ACME", "NovA", os.path.join(d, "b.docx")); assert rc == 0 and "replaced 1" in out, out
assert "Hello NovA world" in run("text", os.path.join(d, "b.docx"))[1]
assert "ACME" in run("text", dx)[1], "original was modified"
assert run("replace", dx, "ABSENT", "x", os.path.join(d, "c.docx"))[0] == 1 and not os.path.exists(os.path.join(d, "c.docx"))
assert run("replace", dx, "ACME", "x", dx)[0] != 0, "in-place edit allowed"
S = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
xs = os.path.join(d, "a.xlsx")
mk(xs, {"xl/sharedStrings.xml": f'<sst {S}><si><t>name</t></si><si><t>alice</t></si></sst>',
        "xl/worksheets/sheet1.xml": f'<worksheet {S}><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>7</v></c></row><row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>42</v></c></row></sheetData></worksheet>'})
t = run("text", xs)[1]; assert "name\t7" in t and "alice\t42" in t, t
rc, out = run("replace", xs, "alice", "bob", os.path.join(d, "b.xlsx")); assert rc == 0 and "bob\t42" in run("text", os.path.join(d, "b.xlsx"))[1]
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
px = os.path.join(d, "a.pptx")
mk(px, {"ppt/slides/slide1.xml": f'<p:sld xmlns:p="x" {A}><a:p><a:r><a:t>Title ACME</a:t></a:r></a:p></p:sld>',
        "ppt/slides/slide2.xml": f'<p:sld xmlns:p="x" {A}><a:p><a:r><a:t>Second</a:t></a:r></a:p></p:sld>'})
t = run("text", px)[1]; assert "--- slide 1 ---" in t and "Title ACME" in t and "Second" in t, t
assert run("replace", px, "ACME", "NovA", os.path.join(d, "b.pptx"))[0] == 0 and "Title NovA" in run("text", os.path.join(d, "b.pptx"))[1]
# pdf: made by PyMuPDF if present (two pages), read with pdftotext, split with pypdf/mutool
try:
    import fitz
    pd = fitz.open()
    for s in ("page one text", "page two text"): pd.new_page().insert_text((72, 72), s)
    pf = os.path.join(d, "a.pdf"); pd.save(pf)
    t = run("text", pf)[1]; assert "page one text" in t and "page two text" in t, t
    rc, out = run("pages", pf, "2", os.path.join(d, "p2.pdf")); assert rc == 0, out
    t = run("text", os.path.join(d, "p2.pdf"))[1]; assert "page two text" in t and "page one" not in t, t
    pdf = "pdf read+split ok"
except ImportError:
    pdf = "pdf skipped (no PyMuPDF to make one)"
print("office.py ok:", pdf)
