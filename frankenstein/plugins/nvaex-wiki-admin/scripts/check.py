#!/usr/bin/env python3
"""
Phase 2 RLVR Validation - Corpus Verify (Hard Rule 5)
Independent verification that content survived the cleaning pass.
Uses DISJOINT extractors from tools/clean.py:
  - PDF: clean.py uses mutool (mupdf/C); check.py uses pypdf (pure Python)
  - DOCX: clean.py uses python-docx; check.py uses stdlib zipfile + xml.etree
  - HTML: clean.py uses stdlib html.parser; check.py uses BeautifulSoup4
  - Text: clean.py uses open().read(); check.py uses byte read + encoding probe
The tool that cleaned a file does not get a vote on whether the cleaning was good.
"""
import datetime, difflib, os, re, sys, unicodedata

def find_dirs():
    docs = "/storage/emulated/0/Documents"
    for e in os.listdir(docs):
        if "xorpus" in e.lower():
            novae = os.path.join(docs, e)
            break
    else:
        raise FileNotFoundError("NovAExorpus dir not found")
    # The old Repos/ level is gone: raw_database/, clean_md/, audit/ sit at the vault root.
    raw_db = os.path.join(novae, "raw_database")
    return (novae, os.path.join(raw_db, "raw"), os.path.join(raw_db, "02_MY_ORIGINALS"),
            os.path.join(raw_db, "Dump", "zip"), os.path.join(novae, "clean_md"),
            os.path.join(novae, "audit"))

VAULT, RAW_DIR, ORIGINALS_DIR, DUMP_DIR, CLEAN_DIR, AUDIT_DIR = find_dirs()
# check_one()/render() name sources relative to SRC and cleaned files under CLEAN.
SRC, CLEAN = VAULT, CLEAN_DIR
TODAY = datetime.date.today().isoformat()


# ---------------------------------------------------------------- normalising

# Zero-width marks and the BOM.  They carry no content, so they must not create
# a false difference — but a BOM left sitting inside a markdown body is worth
# saying out loud, so it is reported separately.
_INVISIBLE = dict.fromkeys(map(ord, "​‌‍⁠﻿­᠎"), None)

_LIGATURES = {"Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe", "ß": "ss",
              "Ø": "O", "ø": "o", "Đ": "D", "đ": "d", "Ł": "L", "ł": "l",
              "Ð": "D", "þ": "th", "Þ": "Th"}


def fold(s):
    """Unicode -> comparable ASCII-ish.  Applied to both sides, always."""
    s = unicodedata.normalize("NFKC", s).translate(_INVISIBLE)
    s = "".join(_LIGATURES.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


_NOTALNUM = re.compile(r"[^a-z0-9]+")


def squash(s):
    """Every separator gone.  'CHIP SM8750' and 'CHIPSM8750' both become
    'chipsm8750', so a value welded to its neighbour is still found.  This is
    what makes the fused-token blind spot visible."""
    return _NOTALNUM.sub("", fold(s).lower())


def wordstream(s):
    """Every separator collapsed to one space, wrapped in spaces.  Word
    boundaries survive here, so comparing this against squash() says whether a
    boundary was destroyed."""
    return " " + _NOTALNUM.sub(" ", fold(s).lower()).strip() + " "


def extract_pdf_pypdf(pdf_path):
    """PDF extraction using pypdf (DISJOINT from clean.py's mutool)."""
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)

def extract_docx_stdlib(docx_path):
    """DOCX extraction using stdlib zipfile + xml.etree (DISJOINT from clean.py's python-docx)."""
    import zipfile
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(docx_path) as z:
        # Read word/document.xml
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
        root = tree.getroot()
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        parts = []
        for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            texts = []
            for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                if t.text:
                    texts.append(t.text)
            if texts:
                parts.append("".join(texts))
        return "\n".join(parts)

def extract_html_bs4(html_path):
    """HTML extraction using BeautifulSoup4 (DISJOINT from clean.py's stdlib html.parser)."""
    from bs4 import BeautifulSoup
    with open(html_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")
    return soup.get_text(separator="\n")

def extract_text_bytes(filepath):
    """Text extraction via byte read + encoding probe (DISJOINT from clean.py's utf-8 open)."""
    with open(filepath, "rb") as f:
        raw = f.read()
    # Try utf-8, then latin-1, then ascii
    for enc in ["utf-8", "latin-1", "ascii"]:
        try:
            return raw.decode(enc)
        except:
            continue
    return raw.decode("utf-8", errors="replace")

def sniff_file(filepath):
    with open(filepath, "rb") as f:
        magic = f.read(16)
    if magic.startswith(b"%PDF"):
        return "pdf"
    if magic.startswith(b"PK"):
        return "docx"
    if magic.startswith(b"<") or magic.startswith(b"\xef\xbb\xbf<"):
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                preview = f.read(500).lower()
            if "<html" in preview or "<div" in preview or "<!doctype" in preview:
                return "html"
        except:
            pass
        return "xml"
    return "text"

def get_source_file(clean_file_path):
    """Extract the source filename from the YAML frontmatter."""
    with open(clean_file_path, "r", encoding="utf-8") as f:
        content = f.read(8192)
    fm = re.match(r"---\n(.*?)\n---", content, re.S)
    m = re.search(r"^source:\s*(.+)", fm.group(1) if fm else content[:500], re.M)
    if m:
        return m.group(1).strip().strip("\"'")
    return None

def find_source(source_name, *dirs):
    """Find the source in raw/, 02_MY_ORIGINALS/ or Dump/zip/ by the bare filename
    clean.py writes, or as a path (absolute or vault-relative)."""
    p = os.path.join(VAULT, source_name)
    if os.path.isfile(p):
        return p
    for search_dir in dirs:
        p = os.path.join(search_dir, source_name)
        if os.path.isfile(p):
            return p
    # Originals moved out of the vault: PDFs to the keep's vault-pdfs/ (same
    # vault-relative path), NovA-Corpus originals to _salvage/.../originals/.
    keep = os.path.join(os.path.dirname(VAULT), "Merovingian's_keep")
    mirror = os.path.join(keep, "vault-pdfs")
    for search_dir in (VAULT,) + dirs:
        p = os.path.join(mirror, os.path.relpath(search_dir, VAULT), source_name)
        if os.path.isfile(os.path.normpath(p)):
            return os.path.normpath(p)
    salvage = os.path.join(keep, "_salvage", "NovA-Corpus", "originals")
    base = os.path.basename(source_name)
    for root, _, files in os.walk(salvage):
        if base in files:
            return os.path.join(root, base)
    return None


def kind_of(path):
    k = sniff_file(path)
    return "text" if k == "xml" else k


def _read_bytes_text(path):
    with open(path, "rb") as f:
        bom = f.read(3) == b"\xef\xbb\xbf"
    return extract_text_bytes(path).lstrip("\ufeff"), "byte read + encoding probe", {"bom": bom}


# Each extractor -> (text, how it was read, meta).  None of them is clean.py's.
EXTRACTORS = {
    "pdf": lambda p: (extract_pdf_pypdf(p), "pypdf PdfReader.extract_text()", {}),
    "docx": lambda p: (extract_docx_stdlib(p), "stdlib zipfile + xml.etree", {}),
    "html": lambda p: (extract_html_bs4(p), "BeautifulSoup4 get_text()", {}),
    "text": _read_bytes_text,
}

# Extraction is byte-faithful only for plain text.  An exact line-level audit
# is valid there and nowhere else.
EXACT = {"text"}


# ------------------------------------------------------- the documented spec
#
# Transcribed by hand from README.md -> "The one job".  This is the *policy*,
# not clean.py's implementation of it.  A line counts as furniture only if it
# is made of nothing but these fragments; anything else that went missing is a
# finding, whatever the cleaner called it.

CHROME = [
    ("browser/app chrome", re.compile(
        r"Use code with caution\.?|Ask anything|AI Mode"
        r"|All\s+Images\s+Videos\s+News\s+Maps\s+Shopping\s+Books\s+Flights\s+Finance"
        r"|Try without personalization|Search Labs|Sign in"
        r"|Show more|Show less|\bMore\b|\bTools\b"
        r"|\d+\s+sites?\b", re.I)),
]
PAGE_NUMBER = ("page number", re.compile(r"^\s*(?:page\s+)?[-–—]?\s*\d{1,4}\s*(?:/\s*\d{1,4}\s*)?[-–—]?\s*$", re.I))


def furniture_class(line, kind):
    """Name the furniture rule a line falls under, or None if it is content."""
    if not line.strip():
        return "blank line"
    if kind == "pdf" and PAGE_NUMBER[1].match(line):
        return PAGE_NUMBER[0]
    residue = line
    hit = None
    for name, rx in CHROME:
        new = rx.sub(" ", residue)
        if new != residue:
            hit = name
        residue = new
    if hit and not re.sub(r"[^\w]", "", residue):
        return hit
    return None


# ---------------------------------------------------------------- the atoms
#
# Named, typed details.  Each is looked for by containment; none is counted.

ATOM_RULES = [
    ("url", re.compile(r"(?:https?://|www\.|drive://|file://|git@)[^\s<>\"'()\[\]{}]+")),
    ("email", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("hash/key", re.compile(r"\b(?:[0-9a-f]{16,}|gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("measurement", re.compile(
        r"\b\d[\d,]*(?:\.\d+)?\s*(?:[-–—]\s*\d[\d,]*(?:\.\d+)?\s*)?"
        r"(?:GB|MB|KB|TB|GiB|MiB|KiB|TOPS|GHz|MHz|kHz|Hz|ms|fps|dpi|px|%|bytes?|"
        r"tokens?|pages?|files?|cores?|threads?|USD|W)\b")),
    ("version", re.compile(r"\bv?\d+\.\d+(?:\.\d+)*(?:[A-Za-z]\w*)?\b")),
    ("path", re.compile(r"(?:[A-Za-z0-9_.~\-]+/){1,}[A-Za-z0-9_.\-]+")),
    ("identifier", re.compile(
        r"\b(?:[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+"       # snake_case / SCREAMING
        r"|[A-Za-z]{2,}\d[A-Za-z0-9]*"                   # SM8750, v79
        r"|\d+[A-Za-z]{2,}[A-Za-z0-9]*)\b")),            # 3APK
    ("acronym", re.compile(r"\b[A-Z][A-Z0-9]{2,9}\b")),
    ("date", re.compile(r"\b(?:20\d\d[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d\d)\b")),
    ("number", re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")),
]

MIN_MISSING = 3    # squashed length below which absence cannot be asserted
MIN_FUSED = 4      # squashed length below which a substring hit means nothing
MIN_SEGMENT = 24   # squashed length of a segment worth checking as a whole


_RUNCHAR = re.compile(r"[A-Za-z0-9._\-\u2013/]")


def find_atoms(lines):
    """-> ([(klass, verbatim, line_no)], n_unjudgeable), deduped on (klass, text).

    An atom is only usable if THIS checker's own extractor produced it as a
    complete run.  pypdf welds tightly-set figure cells (0.40 and 0.95 arrive
    as 0.400.95); demanding that a fragment of that appear as a standalone
    token in the cleaned file would invent a failure that is the checker's own
    fault.  Fragments are counted and set aside, never asserted.
    """
    seen, atoms, skipped = set(), [], 0
    for n, line in lines:
        for klass, rx in ATOM_RULES:
            for m in rx.finditer(line):
                before = line[m.start() - 1] if m.start() > 0 else ""
                after = line[m.end()] if m.end() < len(line) else ""
                if (before and _RUNCHAR.match(before)) or (after and _RUNCHAR.match(after)):
                    skipped += 1
                    continue
                v = m.group(0).strip(".,;:)]}'\"")
                key = (klass, v)
                if not v or key in seen:
                    continue
                seen.add(key)
                atoms.append((klass, v, n))
    return atoms, skipped


def judge_atom(verbatim, hay_sq, hay_ws):
    """INTACT | RESPACED | FUSED | MISSING | None (too short to judge)"""
    a_sq, a_ws = squash(verbatim), wordstream(verbatim).strip()
    if len(a_sq) < MIN_MISSING:
        return None
    if a_ws and (" " + a_ws + " ") in hay_ws:
        return "INTACT"
    if a_sq not in hay_sq:
        return "MISSING"
    if len(a_sq) < MIN_FUSED:
        return None
    return "FUSED" if a_ws and a_ws in hay_ws else "RESPACED"


# -------------------------------------------------------------- the segments

_SENT = re.compile(r"(?<=[.!?;])\s+")


def segments(lines):
    """Order-sensitive units.  A word-frequency diff is blind to these: every
    word can be present and the sentence still gone."""
    out = []
    for n, line in lines:
        line = line.strip()
        if not line:
            continue
        parts = _SENT.split(line) if len(line) > 300 else [line]
        for p in parts:
            if len(squash(p)) >= MIN_SEGMENT:
                out.append((p.strip(), n))
    return out


def chunk_split(seg, hay_sq):
    """Greedily cover a segment with the fewest contiguous runs that each
    survive in the cleaned file.  -> [(text, survived)].

    One chunk  = the phrase survived intact.
    Two chunks = a line break moved; the words are all there, in order.
    More, or a chunk marked False = something to report by name.
    """
    words = [w for w in seg.split() if w]
    chunks, i, n = [], 0, len(words)
    while i < n:
        j = n
        while j > i and squash(" ".join(words[i:j])) not in hay_sq:
            j -= 1
        if j == i:
            chunks.append((words[i], False))
            i += 1
        else:
            chunks.append((" ".join(words[i:j]), True))
            i = j
    return chunks


# ------------------------------------------------------------- the two ends

TAIL_STEPS = (400, 250, 150, 80, 40)
_ENDS_CLOSED = re.compile(r"[.!?…\"'”’)\]}|:*_`—–-]\s*$")
_BARE_TAG = re.compile(r"^\s*</?[A-Za-z][\w:-]*\s*/?>\s*$")


EDGE_CHARS = 60


def edge_block(content, head):
    """The first (or last) content lines of the source, enough of them to make
    EDGE_CHARS squashed characters."""
    seq = content if head else list(reversed(content))
    acc, got = 0, []
    for _n, line in seq:
        if not line.strip():
            continue
        got.append(line)
        acc += len(squash(line))
        if acc >= EDGE_CHARS:
            break
    return "\n".join(got if head else reversed(got))


def edge_check(content, hay_sq, head):
    """-> (block, [pieces of it that are nowhere in the cleaned file]).

    Chunk-based rather than one contiguous run: pypdf and pymupdf disagree
    about icon glyphs and line breaks at the very end of a page, and that
    disagreement is not a truncation.  A piece that is nowhere at all is."""
    block = edge_block(content, head)
    if not squash(block):
        return block, []
    return block, [c for c, ok in chunk_split(block, hay_sq) if not ok]


def last_real_line(text):
    """The last line that is actually prose, ignoring a trailing wrapper tag
    such as the </content> that Drive text exports end with."""
    for line in reversed(text.rstrip().split("\n")):
        if line.strip() and not _BARE_TAG.match(line):
            return line.strip()
    return ""


def looks_truncated(text):
    """Does the SOURCE itself stop mid-thought?  Upstream defect if so —
    reported, never repaired."""
    last = last_real_line(text)
    if not last or _ENDS_CLOSED.search(last):
        return None
    if re.match(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|\||```|---|===|\{|\})", last):
        return None
    if len(last.split()) < 3:
        return None
    return last[-100:]


# ------------------------------------------------------------------- pairing

def read_clean(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    fm, body = {}, raw
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 3)
        if end != -1:
            for line in raw[4:end].split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
            body = raw[end + 5:]
    return fm, body


def build_pairs():
    """Pair by the `source:` line the cleaned file already declares.  Reading a
    declaration is not the same as trusting a verdict."""
    sources = sorted(
        os.path.relpath(os.path.join(r, f), SRC).replace("\\", "/")
        for r, _, fs in os.walk(SRC) for f in fs if not f.startswith("MANIFEST"))
    by_source, orphans = {}, []
    for r, _, fs in os.walk(CLEAN):
        for f in sorted(fs):
            cp = os.path.join(r, f).replace("\\", "/")
            fm, body = read_clean(cp)
            key = fm.get("source", "")
            if not key:
                orphans.append((cp, "no `source:` line in frontmatter"))
                continue
            # Some producers declare source relative to the repo root (e.g.
            # "raw/README.md"); this checker computes sources relative to SRC
            # itself (e.g. "README.md"). Fall back to stripping one leading
            # path segment before giving up on a match.
            resolved = key if key in sources else None
            if resolved is None and "/" in key:
                stripped = key.split("/", 1)[1]
                if stripped in sources:
                    resolved = stripped
            if resolved in by_source:
                orphans.append((cp, "second file claiming source %r" % key))
            elif resolved is None:
                orphans.append((cp, "claims source %r, which is not in %s/" % (key, SRC)))
            else:
                by_source[resolved] = (cp, fm, body)
    return sources, by_source, orphans


# ------------------------------------------------------------------ checking

MAX_LIST = 40


def q(s, n=170):
    s = s.replace("\n", "\\n")
    return "`" + (s[:n] + "…" if len(s) > n else s).replace("`", "'") + "`"


def check_one(rel, clean_path, body):
    src_path = os.path.join(SRC, rel)
    kind = kind_of(src_path)
    findings, notes = [], []

    try:
        src, extractor, meta = EXTRACTORS[kind](src_path)
    except Exception as ex:
        findings.append(("FAIL", "extraction failed",
                         "the checker could not read %s independently" % rel,
                         "%s: %s" % (type(ex).__name__, ex)))
        return "ERROR", findings, notes, kind, "n/a", {}, None

    if clean_path is None:
        findings.append((
            "FAIL", "no counterpart",
            "%s has no file in %s/" % (rel, CLEAN),
            "%d characters of text were extracted from this source by an "
            "independent reader (%s) and none of them are anywhere in the "
            "corpus." % (len(src.strip()), extractor)))
        return "NO-COUNTERPART", findings, notes, kind, extractor, meta, None

    hay_sq, hay_ws = squash(body), wordstream(body)

    # --- split the source into content and documented furniture -------------
    all_lines = list(enumerate(src.split("\n"), 1))
    content, furniture = [], []
    for n, line in all_lines:
        why = furniture_class(line, kind)
        if why and why != "blank line":
            furniture.append((n, line, why))
        elif why != "blank line":
            content.append((n, line))
    content_text = "\n".join(l for _, l in content)

    for n, line, why in furniture:
        survived = squash(line) and squash(line) in hay_sq
        notes.append("%s — %s, source line %d: %s"
                     % ("still present in the cleaned file" if survived
                        else "removed, and it is furniture", why, n, q(line)))

    # --- atoms --------------------------------------------------------------
    buckets = {"MISSING": [], "FUSED": [], "RESPACED": []}
    judged = 0
    atoms, unjudgeable = find_atoms(content)
    for klass, verbatim, line_no in atoms:
        v = judge_atom(verbatim, hay_sq, hay_ws)
        if v is None:
            continue
        judged += 1
        if v != "INTACT":
            buckets[v].append((klass, verbatim, line_no))

    for klass, verbatim, line_no in buckets["MISSING"]:
        findings.append((
            "FAIL", "missing value",
            "the %s %s appears in the source and not in the cleaned file"
            % (klass, q(verbatim)), "source line %d" % line_no))
    for klass, verbatim, line_no in buckets["FUSED"]:
        findings.append((
            "FAIL", "fused token",
            "the %s %s survives only welded to its neighbour" % (klass, q(verbatim)),
            "source line %d — the characters are in the cleaned file, the "
            "separate token is not, so a word diff cannot see it" % line_no))
    for klass, verbatim, line_no in buckets["RESPACED"]:
        findings.append((
            "WARN", "respaced value",
            "the %s %s survives with its internal spacing changed"
            % (klass, q(verbatim)), "source line %d" % line_no))

    # --- segments -----------------------------------------------------------
    segs = segments(content)
    for seg, line_no in segs:
        if squash(seg) in hay_sq:
            continue
        chunks = chunk_split(seg, hay_sq)
        lost = [c for c, ok in chunks if not ok]
        if lost:
            findings.append((
                "FAIL", "missing text",
                "text at source line %d is not in the cleaned file: %s"
                % (line_no, q(seg, 240)),
                "found nowhere in the cleaned file: "
                + ", ".join(q(x, 70) for x in lost[:8])))
        elif len(chunks) > 2:
            findings.append((
                "WARN", "broken run",
                "source line %d survives only in %d separate pieces: %s"
                % (line_no, len(chunks), q(seg, 240)),
                "the pieces: " + " || ".join(q(c, 60) for c, _ in chunks[:6])))
        # exactly two chunks is a line break moving; not a loss

    # --- exact line audit, where extraction is byte-faithful ----------------
    if kind in EXACT:
        a = [fold(l).rstrip() for _, l in all_lines]
        b = [fold(l).rstrip() for l in body.split("\n")]
        raw_a = [l for _, l in all_lines]
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        already = {f[2] for f in findings}
        for op, i1, i2, _j1, _j2 in sm.get_opcodes():
            if op not in ("delete", "replace"):
                continue
            for k in range(i1, i2):
                line = raw_a[k]
                if not line.strip():
                    continue
                if furniture_class(line, kind):
                    continue
                if squash(line) and squash(line) in hay_sq:
                    continue   # moved, not lost — the containment checks own it
                msg = ("source line %d was removed and is not furniture under "
                       "the README strip policy: %s" % (k + 1, q(line, 240)))
                if msg in already:
                    continue
                findings.append((
                    "FAIL", "line removed", msg,
                    "exact line-level audit — extraction is byte-faithful for "
                    "plain text, so this is definitive"))

    if meta.get("bom") and body.startswith("﻿"):
        findings.append((
            "WARN", "stray byte-order mark",
            "the source's UTF-8 BOM was carried into the middle of the cleaned "
            "file, after the frontmatter",
            "U+FEFF now sits at the first character of the markdown body"))

    # --- the two ends -------------------------------------------------------
    tail_block, tail_lost = edge_check(content, hay_sq, head=False)
    head_block, head_lost = edge_check(content, hay_sq, head=True)
    if tail_lost:
        findings.append((
            "FAIL", "truncated by cleaning",
            "the end of the source is not in the cleaned file",
            "the source ends %s — nowhere in the cleaned file: %s"
            % (q(tail_block, 170), ", ".join(q(x, 70) for x in tail_lost[:8]))))
    if head_lost:
        findings.append((
            "FAIL", "head missing",
            "the beginning of the source is not in the cleaned file",
            "the source begins %s — nowhere in the cleaned file: %s"
            % (q(head_block, 170), ", ".join(q(x, 70) for x in head_lost[:8]))))

    upstream = looks_truncated(content_text)
    if upstream:
        reproduced = not tail_lost
        findings.append((
            "UPSTREAM", "source truncated",
            "the SOURCE itself stops mid-sentence — an upstream defect, not a "
            "cleaning defect",
            "its own last words: %s — the cleaned file %s. Nothing in this "
            "repo can repair this; it needs re-retrieving at the origin."
            % (q(upstream), "reproduces that ending faithfully" if reproduced
               else "does not even reach that ending")))

    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    ups = [f for f in findings if f[0] == "UPSTREAM"]
    if fails:
        verdict = "FAIL"
    elif warns:
        verdict = "PASS WITH WARNINGS"
    else:
        verdict = "PASS"
    if ups:
        verdict += " + UPSTREAM DEFECT"

    meta = dict(meta)
    meta.update({"atoms judged": judged,
                 "atoms set aside (fused by the checker's own extractor)": unjudgeable,
                 "segments checked": len(segs),
                 "furniture lines found by the checker": len(furniture),
                 "end of source survives": "no" if tail_lost else "yes",
                 "start of source survives": "no" if head_lost else "yes"})
    return verdict, findings, notes, kind, extractor, meta, None


# -------------------------------------------------------------------- report

def render(rel, clean_path, verdict, findings, notes, kind, extractor, meta):
    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    ups = [f for f in findings if f[0] == "UPSTREAM"]
    L = ["---",
         "checker: tools/check.py",
         "checked: %s" % TODAY,
         "source: %s" % (SRC + "/" + rel),
         "cleaned: %s" % (clean_path or "NONE"),
         "source_kind: %s" % kind,
         "extractor: %s" % extractor,
         "independent_of: tools/clean.py — different extractor, different "
         "comparison method, no shared code",
         "verdict: %s" % verdict,
         "fails: %d" % len(fails),
         "warnings: %d" % len(warns),
         "upstream_defects: %d" % len(ups),
         "---", "",
         "# Check — %s" % rel, "",
         "## Verdict: %s" % verdict, ""]
    if not findings:
        L += ["Every named detail an independent extractor found in the source "
              "was found again in the cleaned file. No detail is missing.", ""]
    L += ["| | |", "|---|---|"]
    for k, v in meta.items():
        L.append("| %s | %s |" % (k, v))
    L.append("")

    def block(title, rows, blurb):
        if not rows:
            return
        L.append("## %s — %d" % (title, len(rows)))
        L.extend(["", blurb, ""])
        for _sev, klass, name, detail in rows[:MAX_LIST]:
            L.append("### %s — %s" % (klass.upper(), name))
            if detail:
                L.extend(["", detail])
            L.append("")
        if len(rows) > MAX_LIST:
            L.extend(["_… and %d more of the same kind. All of them are in "
                      "`03-check/FINDINGS.jsonl`._" % (len(rows) - MAX_LIST), ""])

    block("Fails", fails,
          "Each names a detail that is in the source and is not in the cleaned "
          "file, or is there in a form a reader cannot get back out.")
    block("Warnings", warns,
          "The detail survived; something about its shape did not.")
    block("Upstream defects", ups,
          "Already wrong in the source before this repo touched it. Reported, "
          "not repaired — hard rule 1.")

    if notes:
        L.append("## Furniture, audited independently — %d line(s)" % len(notes))
        L += ["",
              "Every line the *checker* judges furniture under the strip policy "
              "in `README.md` → \"The one job\", and what actually became of it. "
              "This is not the cleaner's own report of what it removed.", ""]
        for n in notes[:MAX_LIST]:
            L.append("- %s" % n)
        if len(notes) > MAX_LIST:
            L.append("- _… and %d more._" % (len(notes) - MAX_LIST))
        L.append("")
    return "\n".join(L) + "\n"


def canary_check(clean_files):
    """Truncate the first checkable clean file to half its body and require a FAIL."""
    for clean_path in clean_files:
        source_name = get_source_file(clean_path)
        source_path = source_name and find_source(source_name, RAW_DIR, ORIGINALS_DIR, DUMP_DIR)
        if not source_path:
            continue
        _fm, body = read_clean(clean_path)
        if len(body) < 400:
            continue
        rel = os.path.relpath(source_path, SRC)
        verdict, *_ = check_one(rel, clean_path, body[: len(body) // 2])
        if verdict == "FAIL":
            return f"ok (half of {os.path.basename(clean_path)} -> FAIL)"
        return f"BROKEN: half of {os.path.basename(clean_path)} got {verdict}, expected FAIL"
    return "skipped (no checkable pair in this run)"


def main():
    """python3 tools/check.py [--dry-run] [CLEAN_MD ...]  (default: every file in clean_md/)"""
    dry_run = "--dry-run" in sys.argv
    picked = [a for a in sys.argv[1:] if not a.startswith("--")]
    clean_files = picked or [os.path.join(CLEAN_DIR, f) for f in sorted(os.listdir(CLEAN_DIR))
                             if f.endswith(".md") and f != "POINTER.md"]

    print("Phase 2 RLVR Validation - Corpus Verify")
    print(f"Raw:    {RAW_DIR}")
    print(f"Clean:  {CLEAN_DIR}")
    print(f"Audit:  {AUDIT_DIR}" + (" (dry run, nothing written)" if dry_run else ""))
    print(f"Clean files to verify: {len(clean_files)}")
    print()

    # Canary: the checker's own output is checked too. A real pair is cut in half; if the
    # checker does not FAIL it, this run's verdicts cannot be trusted and nothing is reported.
    canary = canary_check(clean_files)
    print(f"Canary: {canary}")
    if canary.startswith("BROKEN"):
        sys.exit(2)
    print()

    rows = []
    for clean_path in clean_files:
        clean_file = os.path.basename(clean_path)
        with open(clean_path, "r", encoding="utf-8") as f:
            head = f.read(2048)
        if re.match(r"---\n(?:.*\n)*?type:\s*condensed\s*\n", head):
            # A deliberate summary: shorter than its source by design, so containment does not apply.
            rows.append((clean_file, "CONDENSED", "summary, not checked for containment"))
            print(f"  [CONDENSED] {clean_file[:60]:<60} summary, not checked for containment")
            continue
        source_name = get_source_file(clean_path)
        source_path = source_name and find_source(source_name, RAW_DIR, ORIGINALS_DIR, DUMP_DIR)
        if not source_path:
            why = "no source in frontmatter" if not source_name else "source not found: " + source_name
            rows.append((clean_file, "NO-SOURCE", why))
            print(f"  [NO-SOURCE] {clean_file[:60]:<60} {why}")
            continue
        _fm, body = read_clean(clean_path)
        rel = os.path.relpath(source_path, SRC)
        verdict, findings, notes, kind, extractor, meta, _ = check_one(rel, clean_path, body)
        fails = [f for f in findings if f[0] == "FAIL"]
        rows.append((clean_file, verdict, "%d fails" % len(fails)))
        print(f"  [{verdict}] {clean_file[:60]:<60} {len(fails)} fails")
        for _sev, klass, name, _detail in fails[:5]:
            print(f"      {klass}: {name[:160]}")
        if not dry_run:
            os.makedirs(AUDIT_DIR, exist_ok=True)
            dest = os.path.join(AUDIT_DIR, os.path.splitext(clean_file)[0] + ".check.md")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(render(rel, clean_path, verdict, findings, notes, kind, extractor, meta))

    count = lambda p: sum(1 for r in rows if p(r[1]))
    print()
    print("--- Summary ---")
    print(f"Total:   {len(rows)}")
    print(f"PASS:    {count(lambda v: v.startswith('PASS'))}")
    print(f"FAIL:    {count(lambda v: v.startswith('FAIL'))}")
    print(f"Other:   {count(lambda v: not v.startswith(('PASS', 'FAIL')))}")

    if not dry_run:
        report_path = os.path.join(AUDIT_DIR, "rlvr_verification_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("---\nsource: tools/check.py (pypdf/zipfile+xml.etree/BeautifulSoup4)\ntype: rlvr-audit\n---\n\n")
            f.write("# Phase 2 RLVR Verification Report\n\n")
            f.write("| File | Verdict | Detail |\n|------|---------|--------|\n")
            for row in rows:
                f.write("| %s | %s | %s |\n" % row)
        print(f"\nReport written to: {report_path}")
    return 1 if any(r[1].startswith("FAIL") for r in rows) else 0

if __name__ == "__main__":
    sys.exit(main())
