"""Memory integrity linter: validates @meta blocks in memory/*.md against the live repo.

stdlib only (no pyyaml/pytest). See docs/anchor-anchors-spec.md
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any

META_OPEN = "<!-- @meta"
META_CLOSE = "-->"


@dataclass
class Entry:
    id: str
    status: str = "active"
    supersedes: str | None = None
    anchors: list[dict[str, Any]] = field(default_factory=list)
    raw: str = ""


def _parse_block_body(body: str) -> Entry:
    """Parse the minimal YAML subset we use: scalar keys + an `anchors:` list of dicts."""
    lines = body.splitlines()
    scalars: dict[str, str] = {}
    anchors: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped == "anchors:":
            i += 1
            cur: dict[str, Any] | None = None
            while i < len(lines):
                aline = lines[i]
                astr = aline.strip()
                if astr.startswith("- "):
                    cur = {}
                    anchors.append(cur)
                    astr = astr[2:].strip()
                    if astr:
                        k, _, v = astr.partition(":")
                        cur[k.strip()] = _coerce(v.strip())
                elif astr and cur is not None and ":" in astr and not astr.startswith("#"):
                    k, _, v = astr.partition(":")
                    cur[k.strip()] = _coerce(v.strip())
                elif astr.startswith("#") or not astr:
                    pass
                else:
                    break
                i += 1
            continue
        if ":" in stripped and not stripped.startswith("#"):
            k, _, v = stripped.partition(":")
            scalars[k.strip()] = v.strip()
        i += 1
    return Entry(
        id=scalars.get("id", ""),
        status=scalars.get("status", "active") or "active",
        supersedes=scalars.get("supersedes") or None,
        anchors=anchors,
        raw=body,
    )


def _coerce(v: str) -> Any:
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_meta_blocks(text: str) -> list[Entry]:
    entries: list[Entry] = []
    idx = 0
    while True:
        start = text.find(META_OPEN, idx)
        if start == -1:
            break
        end = text.find(META_CLOSE, start)
        if end == -1:
            break
        body = text[start + len(META_OPEN):end]
        entries.append(_parse_block_body(body))
        idx = end + len(META_CLOSE)
    return entries


# ---------------------------------------------------------------------------
# Anchor evaluators
# ---------------------------------------------------------------------------


@dataclass
class AnchorResult:
    status: str          # MATCH | DRIFT | BROKEN
    detail: str = ""
    anchor: dict[str, Any] = field(default_factory=dict)


def _read(root: str, rel: str) -> str | None:
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _eval_file_grep(a: dict, root: str) -> AnchorResult:
    text = _read(root, a["file"])
    if text is None:
        return AnchorResult("BROKEN", f"file not found: {a['file']}", a)
    if "scope_after" in a:
        marker = a["scope_after"]
        pos = text.find(marker)
        if pos == -1:
            return AnchorResult("BROKEN", f"scope_after marker not found: {marker}", a)
        text = text[pos:]
    expect = a.get("expect", "present")
    found = a["pattern"] in text
    if expect == "present":
        return AnchorResult("MATCH" if found else "DRIFT",
                            "" if found else f"pattern absent: {a['pattern']}", a)
    if expect == "absent":
        return AnchorResult("MATCH" if not found else "DRIFT",
                            "" if not found else "pattern present but expected absent", a)
    if expect.startswith("count:"):
        want = int(expect.split(":", 1)[1])
        got = text.count(a["pattern"])
        return AnchorResult("MATCH" if got == want else "DRIFT",
                            "" if got == want else f"count {got} != {want}", a)
    return AnchorResult("BROKEN", f"unknown expect: {expect}", a)


def _eval_file_exists(a: dict, root: str) -> AnchorResult:
    exists = os.path.exists(os.path.join(root, a["file"]))
    expect = a.get("expect", "present")
    ok = exists if expect == "present" else (not exists)
    return AnchorResult("MATCH" if ok else "DRIFT",
                        "" if ok else f"file {a['file']} expect={expect} actual_exists={exists}", a)


_EVALUATORS = {
    "file_grep": _eval_file_grep,
    "file_exists": _eval_file_exists,
}


def evaluate_anchor(a: dict, root: str = ".") -> AnchorResult:
    kind = a.get("kind")
    fn = _EVALUATORS.get(kind)
    if fn is None:
        return AnchorResult("BROKEN", f"unknown anchor kind: {kind}", a)
    try:
        return fn(a, root)
    except Exception as e:  # malformed anchor → BROKEN, never crash the linter
        return AnchorResult("BROKEN", f"{type(e).__name__}: {e}", a)


def _compare(actual: Any, expect: str) -> bool:
    expect = expect.strip()
    for op in (">=", "<=", "==", ">", "<"):
        if expect.startswith(op):
            rhs = expect[len(op):].strip()
            try:
                a_num, b_num = float(actual), float(rhs)
                return {">=": a_num >= b_num, "<=": a_num <= b_num, "==": a_num == b_num,
                        ">": a_num > b_num, "<": a_num < b_num}[op]
            except (TypeError, ValueError):
                return op == "==" and str(actual) == rhs
    return str(actual) == expect


def _eval_json_field(a: dict, root: str) -> AnchorResult:
    text = _read(root, a["file"])
    if text is None:
        return AnchorResult("BROKEN", f"file not found: {a['file']}", a)
    data = json.loads(text)
    field_name = a["field"]
    if field_name not in data:
        return AnchorResult("BROKEN", f"json field missing: {field_name}", a)
    ok = _compare(data[field_name], a["expect"])
    return AnchorResult("MATCH" if ok else "DRIFT",
                        "" if ok else f"{field_name}={data[field_name]} fails {a['expect']}", a)


def _eval_golden_metric(a: dict, root: str) -> AnchorResult:
    text = _read(root, a["file"])
    if text is None:
        return AnchorResult("BROKEN", f"file not found: {a['file']}", a)
    rows = list(csv.DictReader(text.splitlines()))
    col = a["column"]
    if not rows or col not in rows[0]:
        return AnchorResult("BROKEN", f"column missing: {col}", a)
    match_value = str(a.get("match_value", "True")).lower()
    count = sum(1 for r in rows if (r.get(col) or "").strip().lower() == match_value)
    expect = a["expect"].strip()
    if expect.startswith("count"):
        ok = _compare(count, expect[len("count"):].strip())
        return AnchorResult("MATCH" if ok else "DRIFT",
                            "" if ok else f"count={count} fails {expect}", a)
    return AnchorResult("BROKEN", f"unknown golden expect: {expect}", a)


_EVALUATORS["json_field"] = _eval_json_field
_EVALUATORS["golden_metric"] = _eval_golden_metric


# ---------------------------------------------------------------------------
# Report aggregation
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    kind: str            # DRIFT | BROKEN | DANGLING | DUPLICATE
    entry_id: str
    detail: str


def lint_text(text: str, root: str = ".") -> list[Finding]:
    entries = parse_meta_blocks(text)
    findings: list[Finding] = []
    seen: set[str] = set()
    ids = {e.id for e in entries if e.id}
    for e in entries:
        if e.id and e.id in seen:
            findings.append(Finding("DUPLICATE", e.id, f"id '{e.id}' appears more than once"))
        seen.add(e.id)
        if e.supersedes and e.supersedes not in ids:
            findings.append(Finding("DANGLING", e.id,
                                    f"supersedes unknown id '{e.supersedes}'"))
        if e.status in ("superseded", "retracted"):
            continue  # dead entries: skip anchor evaluation
        for a in e.anchors:
            r = evaluate_anchor(a, root=root)
            if r.status in ("DRIFT", "BROKEN"):
                findings.append(Finding(r.status, e.id, r.detail))
    return findings


def lint_files(paths: list[str], root: str = ".") -> list[Finding]:
    findings: list[Finding] = []
    for p in paths:
        text = _read(root, p)
        if text is None:
            findings.append(Finding("BROKEN", p, f"memory file not found: {p}"))
            continue
        findings.extend(lint_text(text, root=root))
    return findings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

DEFAULT_FILES = ["memory/decisions.md", "memory/FACTS.md"]


def _files_from_config(root: str) -> list[str] | None:
    """Read ledger file list from anchor.config.json if present."""
    cfg_path = os.path.join(root, "anchor.config.json")
    if not os.path.isfile(cfg_path):
        return None
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        files = cfg.get("memory", {}).get("ledger_files")
        return files or None
    except (json.JSONDecodeError, OSError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Memory integrity linter")
    parser.add_argument("--check", action="store_true",
                        help="run the full check (default mode; accepted for explicitness)")
    parser.add_argument("--quiet", action="store_true", help="only print problems")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    parser.add_argument("--root", default=".", help="repo root")
    parser.add_argument("--files", nargs="*", default=None,
                        help="memory files to check (default: decisions.md + FACTS.md)")
    args = parser.parse_args(argv)

    if args.files is not None:
        files = args.files
    else:
        files = _files_from_config(args.root) or DEFAULT_FILES
    rel_files = [f for f in files if not os.path.isabs(f)]
    findings = lint_files(rel_files, root=args.root)
    for f in files:
        if os.path.isabs(f) and os.path.isfile(f):
            with open(f, encoding="utf-8", errors="replace") as fh:
                findings.extend(lint_text(fh.read(), root=args.root))

    if args.json:
        print(json.dumps([{"kind": x.kind, "entry_id": x.entry_id,
                           "detail": x.detail} for x in findings]))
        return 1 if findings else 0

    if findings:
        if not args.quiet:
            print(f"Memory integrity: {len(findings)} issue(s)\n")
        for x in findings:
            print(f"[{x.kind}] {x.entry_id}: {x.detail}")
        return 1
    if not args.quiet:
        print("Memory integrity: all anchors MATCH, no dangling supersession. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
