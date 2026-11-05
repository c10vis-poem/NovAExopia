#!/usr/bin/env python3
"""Move an approved staged page from 01-inbox/ into the wiki (the last gate).

What it solves: "Only a promotion/merge worker writes canonical compiled wiki records"
(capture -> stage -> verify -> promote, extract B11). A page is promoted only when ALL hold:
  1. the operator approved it by name (--approved-by is required; an agent cannot default it);
  2. the latest audit (audit_staging.py audit.jsonl) says promotion_recommended, or
     needs_human_review and --reviewed is given;
  3. the file still has the sha256 the audit saw (nobody changed it after the audit);
  4. the target does not exist, or --replace is given and the old page is kept as <name>.prev.md.
Each promotion is appended to the wiki's log.md.

Usage: promote.py STAGED.md --wiki WIKI_DIR [--subdir concepts] --audit AUDIT.jsonl
                  --approved-by NAME [--reviewed] [--replace]
"""
import argparse, hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("staged", type=Path)
    ap.add_argument("--wiki", type=Path, required=True)
    ap.add_argument("--subdir", default="")
    ap.add_argument("--audit", type=Path, required=True)
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--reviewed", action="store_true")
    ap.add_argument("--replace", action="store_true")
    a = ap.parse_args(argv)
    staged = a.staged.resolve()
    rows = [json.loads(l) for l in open(a.audit, encoding="utf-8")]
    row = next((r for r in rows if staged.as_posix().endswith(r["file"])), None)
    if row is None:
        print(f"REFUSED: {staged.name} is not in {a.audit}; run audit_staging.py first")
        return 1
    if row["verdict"] == "promotion_blocked":
        print("REFUSED: audit says promotion_blocked: " + "; ".join(row["blocking"]))
        return 1
    if row["verdict"] == "needs_human_review" and not a.reviewed:
        print("REFUSED: needs_human_review (" + "; ".join(row["review"]) + "); pass --reviewed")
        return 1
    if hashlib.sha256(staged.read_bytes()).hexdigest() != row["sha256"]:
        print("REFUSED: file changed after the audit; audit it again")
        return 1
    dest = a.wiki.resolve() / a.subdir / staged.name
    if dest.exists():
        if not a.replace:
            print(f"REFUSED: {dest} exists; pass --replace to keep it as .prev.md and replace")
            return 1
        shutil.copy2(dest, dest.with_suffix(".prev.md"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(staged), dest)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with open(a.wiki / "log.md", "a", encoding="utf-8") as f:
        f.write(f"- {stamp} promote `{dest.relative_to(a.wiki.resolve())}` "
                f"(audit {row['verdict']}, approved by {a.approved_by})\n")
    print(f"promoted -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
