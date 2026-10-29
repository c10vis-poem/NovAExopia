#!/usr/bin/env bash
# Round-trip self-test of the wiki-admin tools on synthetic files (no network, no key).
# Proves: converter reports EMPTY/ERROR/unsupported, verify passes good files and FAILs a cut one,
# manifest rebuild is byte-identical, Gemini dry-run drafts and refuses private files,
# audit blocks bad pages, promote moves only an approved, recommended page.
# Needs: python3 with pymupdf + python-docx, pandoc, and the vault's tools/check.py.
set -u
T=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); trap 'rm -rf "$W"' EXIT; cd "$W"
fail() { echo "SELFTEST FAIL: $*"; exit 1; }
mkdir -p raw wiki 01-inbox
python3 - <<'PY'
import pymupdf, docx
d = pymupdf.open(); p = d.new_page()
p.insert_text((72, 72), "Wiki admin selftest PDF. Version 3.8.1 runs on port 20128 at /opt/dumbass.")
for i in range(20): p.insert_text((72, 100 + 14 * i), f"Line {i}: the converter keeps every named detail like SM8750 and 16 GB.")
d.save("raw/sample.pdf")
b = pymupdf.open(); b.new_page(); b.save("raw/blank.pdf")
x = docx.Document(); x.add_heading("Selftest DOCX", 1); x.add_paragraph("Path ~/repos/NovusAExenti and model gemini-3.8-flash."); x.save("raw/sample.docx")
PY
printf '<html><body><h1>Selftest HTML</h1><p>Node Alpha uses QAIRT 2.31.</p></body></html>' > raw/sample.html
printf 'not a pdf' > raw/broken.pdf; printf 'x' > raw/notes.xyz
python3 "$T/convert_raw_to_md.py" raw clean > conv.log; [ $? -eq 1 ] || fail "converter should exit 1 (empty+error)"
grep -q '"status": "empty"' clean/_reports/convert/report.jsonl || fail "blank.pdf not reported EMPTY"
grep -q '"status": "error"' clean/_reports/convert/report.jsonl || fail "broken.pdf not reported ERROR"
grep -q '"status": "unsupported"' clean/_reports/convert/report.jsonl || fail "notes.xyz not reported"
python3 "$T/verify.py" clean --raw raw > ver.log || { cat ver.log; fail "verify did not pass good files"; }
python3 - <<'PY'
p = "clean/sample.pdf.md"; s = open(p).read(); e = s.find("\n---\n", 4) + 5; open(p, "w").write(s[:e] + s[e:][: (len(s) - e) // 3])
PY
python3 "$T/verify.py" clean --raw raw > ver2.log && fail "verify passed a cut file"
grep -q '\[FAIL\] sample.pdf.md' ver2.log || fail "cut file not FAIL"
python3 "$T/manifest.py" build clean --out m1.jsonl >/dev/null; python3 "$T/manifest.py" build clean --out m2.jsonl >/dev/null
cmp -s m1.jsonl m2.jsonl || fail "manifest not deterministic"
export WIKI_ADMIN_LOG="$W/calls.jsonl"
env -u GEMINI_API_KEY -u GOOGLE_API_KEY python3 "$T/gemini_infer.py" draft clean/sample.docx.md --out 01-inbox/sample.md >/dev/null || fail "dry-run draft"
grep -q 'dry_run: true' 01-inbox/sample.md || fail "draft not marked dry-run"
printf -- '---\ntags: [pii]\n---\nx\n' > priv.md
env -u GEMINI_API_KEY python3 "$T/gemini_infer.py" draft priv.md --out 01-inbox/p.md 2>/dev/null; [ $? -eq 3 ] || fail "private file not refused"
printf '# Inbox\n' > 01-inbox/MAP.md; printf '# Wiki\n- [[good-page]]\n' > wiki/index.md
printf -- '---\nid: good-page\ntype: concept\ncreated: 2026-10-28\nupdated: 2026-10-28\nsources: ["raw/sample.pdf"]\n---\n# Good\n' > 01-inbox/good-page.md
python3 "$T/audit_staging.py" 01-inbox --wiki wiki > aud.log; [ $? -eq 1 ] || fail "audit should block the dry-run draft"
grep -q 'promotion_recommended\] good-page.md' aud.log || { cat aud.log; fail "good page not recommended"; }
python3 "$T/promote.py" 01-inbox/sample.md --wiki wiki --audit 01-inbox/_reports/audit/audit.jsonl --approved-by selftest >/dev/null && fail "blocked page promoted"
python3 "$T/promote.py" 01-inbox/good-page.md --wiki wiki --audit 01-inbox/_reports/audit/audit.jsonl --approved-by selftest >/dev/null || fail "approved page not promoted"
[ -f wiki/good-page.md ] && grep -q good-page wiki/log.md || fail "promotion not logged"
echo "SELFTEST PASS (converter, verify + canary, manifest, gemini dry-run + privacy, audit, promote)"
