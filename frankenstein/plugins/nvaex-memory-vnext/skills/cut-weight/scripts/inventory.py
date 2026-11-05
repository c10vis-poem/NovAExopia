#!/usr/bin/env python3
"""Read-only metadata and Markdown discovery for Cut Weight. Python stdlib only.

No semantic verdicts, cleanup, or content execution. Writes only --out (required).
Bulk dependency directories are omitted, not labeled disposable. Caps and errors
are explicit. All Markdown is discovered; bounded headings are only reading aids.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

PROTECTED_DIRS = {".git", "_quarantine", "_graveyard"}
BULK_DIRS = {"node_modules", ".venv", "venv"}
ARTIFACT_DIRS = {
    "dist", "build", "out", ".next", ".nuxt", "coverage", ".nyc_output",
    "htmlcov", "__pycache__", ".pytest_cache", ".cache", ".vite", ".turbo",
    ".parcel-cache", "playwright-report", "test-results", ".mypy_cache", ".ruff_cache",
}
TOOL_DIRS = {".gstack", ".compound-engineering", ".impeccable",
             "_canon-check", "_critic-layer", ".specstory"}
CANONICAL_NAMES = {"claude.md", "agents.md", "agent.md", "gemini.md", "intent.md",
                   ".cursorrules", ".windsurfrules", ".clinerules", ".goosehints",
                   ".aider.conf.yml"}
DOC_TERMS = {"plan", "roadmap", "strategy", "product", "vision", "design", "intent",
             "audit", "review", "improvement", "summary", "brief", "decision"}


def run_git(root, args, input_text=None):
    try:
        return subprocess.run(["git", "-C", root, "-c", "core.quotepath=off"] + args,
                              input=input_text, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_data(root, max_commits):
    ls = run_git(root, ["ls-files", "-z"])
    if ls is None or ls.returncode:
        return None, {}, {"available": False, "history_available": False}
    tracked = set(filter(None, ls.stdout.split("\0")))
    prefix_result = run_git(root, ["rev-parse", "--show-prefix"])
    prefix = prefix_result.stdout.rstrip("\n") if prefix_result and not prefix_result.returncode else ""
    log = run_git(root, ["log", "-z", "--format=%x01%ct", "--name-only",
                         "--max-count=%d" % (max_commits + 1), "--", "."])
    touched, commits, timestamp = {}, 0, None
    if log is not None and log.returncode == 0:
        for token in log.stdout.split("\0"):
            if token.startswith("\x01"):
                commits += 1
                if commits > max_commits:
                    break
                timestamp = int(token[1:].strip())
            elif token and timestamp is not None:
                # Git inserts one separator newline before the first name.
                name = token[1:] if token.startswith("\n") else token
                if prefix and name.startswith(prefix):
                    name = name[len(prefix):]
                if name:
                    touched.setdefault(name, timestamp)
    return tracked, touched, {
        "available": True, "history_available": log is not None and log.returncode == 0,
        "commits_scanned": min(commits, max_commits), "history_truncated": commits > max_commits,
        "note": "Missing last-touch is unknown (untracked, outside scanned history, or unavailable).",
    }


def linklike(path):
    return os.path.islink(path) or getattr(os.path, "isjunction", lambda p: False)(path)


def agent_category(rel, name):
    parts = rel.lower().split("/")
    low = name.lower()
    if low in CANONICAL_NAMES or rel.lower() == ".github/copilot-instructions.md":
        return "canonical"
    if low == ".mcp.json" or "rules" in parts and ".cursor" in parts:
        return "agent-config"
    if low in {".aider.chat.history.md", ".aider.input.history", "settings.local.json"} or low.startswith(".aider.tags.cache"):
        return "tool-material"
    if ".claude" in parts:
        return "agent-config"
    if any(part in TOOL_DIRS for part in parts):
        return "tool-material"
    return None


def name_signals(name):
    low = name.lower()
    return (["backup-suffix"] if low.endswith((".bak", ".old", ".orig", ".tmp", "~")) else []) + (
        ["review-name"] if any(x in low for x in ("scratch", "deprecated", "archive", "-old", "_old", "-copy", "wip")) else [])


def document_metadata(path, rel, limit, errors):
    entry = {"path": rel, "topic_hints": sorted(t for t in DOC_TERMS if t in rel.lower())}
    try:
        with open(path, "rb") as stream:
            raw = stream.read(limit + 1)
        content = raw[:limit].decode("utf-8", errors="replace")
        entry["preview_truncated"] = len(raw) > limit
        headings = re.findall(r"^#{1,6} +(.+)$", content, re.MULTILINE)
        entry["headings"] = [h[:240] for h in headings[:12]]
        entry["headings_truncated"] = len(headings) > 12
        entry["note"] = "Discovery only; read content and linked context before judging relevance."
    except OSError as exc:
        errors.append({"path": rel, "error": type(exc).__name__})
        entry["unreadable"] = True
    return entry


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def review_items(files, documents, threshold):
    """Discovery checklist, not deletion verdicts. Ignore state never exempts."""
    groups = {}
    for entry in files:
        age_reasons = []
        for clock in ("mtime_days", "git_last_touch_days"):
            if entry.get(clock) is not None and entry[clock] >= threshold:
                age_reasons.append(clock + ">=" + str(threshold))
        entry["age_review_reasons"] = age_reasons
        if not entry.get("agent_artifact"):
            continue
        parts = entry["path"].split("/")
        group = next(("/".join(parts[:i + 1]) + "/"
                      for i, part in enumerate(parts[:-1])
                      if part.lower() in TOOL_DIRS | {".claude", ".cursor"}),
                     entry["path"])
        item = groups.setdefault(group, {"id": "tool:" + group, "kind": "tooling",
                                        "members": [], "age_flagged_members": [],
                                        "retention": "UNDECIDED",
                                        "retention_rule": "Establish application dependency or user choice; optional tool self-use, tracking, and executable files do not justify KEEP.",
                                        "status": "UNREVIEWED"})
        item["members"].append(entry["path"])
        if age_reasons:
            item["age_flagged_members"].append(entry["path"])
    by_path = {f["path"]: f for f in files}
    items = list(groups.values())
    # All discovered Markdown needs accounting, not only recognized root names.
    # A tool group can cover its document items explicitly in the final review.
    for doc in documents:
        reasons = ["document-purpose-and-currentness"]
        reasons.extend(by_path[doc["path"]]["age_review_reasons"])
        headings = " ".join(doc.get("headings", [])).lower()
        if re.search(r"\b(done|completed|resolved)\b", headings):
            reasons.append("completion-history-heading; inspect unresolved knowledge")
        items.append({"id": "doc:" + doc["path"], "kind": "document",
                      "members": [doc["path"]], "reasons": reasons,
                      "status": "UNREVIEWED"})
    return sorted(items, key=lambda item: item["id"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--out", required=True, help="explicit output path; use the external run directory")
    ap.add_argument("--max-files", type=positive, default=200000)
    ap.add_argument("--max-commits", type=positive, default=500)
    ap.add_argument("--document-bytes", type=positive, default=16384)
    ap.add_argument("--review-age-days", type=positive, default=60,
                    help="mandatory review trigger on either age clock; never a delete threshold")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        ap.error("root must be a directory")
    out = os.path.abspath(args.out)
    if os.path.lexists(out):
        ap.error("output already exists; choose a fresh run path")
    tracked, touched, git = git_data(root, args.max_commits)
    files, documents, omitted, protected, errors = [], [], [], [], []
    capped, now = False, time.time()
    # A tracked file inside a conventionally bulky directory must remain visible.
    tracked_parents = set()
    for name in tracked or ():
        parts = name.split("/")
        tracked_parents.update("/".join(parts[:i]) for i in range(1, len(parts)))

    def relative(path):
        return os.path.relpath(path, root).replace(os.sep, "/")

    def walk_error(exc):
        errors.append({"path": relative(exc.filename), "error": type(exc).__name__})

    for dp, dns, fns in os.walk(root, onerror=walk_error, followlinks=False):
        dns.sort()
        fns.sort()
        for d in list(dns):
            full = os.path.join(dp, d)
            rel = relative(full)
            if d in PROTECTED_DIRS:
                dns.remove(d)
                protected.append(rel + "/")
            elif linklike(full):
                dns.remove(d)
                fns.append(d)  # record the link itself, never follow it
            elif os.path.lexists(os.path.join(full, ".git")):
                dns.remove(d)
                omitted.append({"path": rel + "/", "reason": "nested-repository", "files": None, "bytes": None})
            elif d in BULK_DIRS and rel not in tracked_parents:
                dns.remove(d)
                omitted.append({"path": rel + "/", "reason": "bulk-dependency-directory; not inspected or proven disposable", "files": None, "bytes": None})
        for fn in sorted(fns):
            full = os.path.join(dp, fn)
            rel = relative(full)
            if fn == ".git":
                protected.append(rel)  # worktree/submodule pointer files too
                continue
            if os.path.abspath(full) == out:
                continue
            if len(files) >= args.max_files:
                capped = True
                break
            try:
                st = os.lstat(full)
            except OSError as exc:
                errors.append({"path": rel, "error": type(exc).__name__})
                continue
            linked = linklike(full)
            entry = {"path": rel, "bytes": st.st_size,
                     "mtime_days": round((now - st.st_mtime) / 86400, 1),
                     "git_last_touch_days": round((now - touched[rel]) / 86400, 1) if rel in touched else None,
                     "tracked": rel in tracked if tracked is not None else None,
                     "signals": name_signals(fn)}
            if linked:
                entry["symlink_or_junction"] = True
            if any(part in ARTIFACT_DIRS for part in rel.split("/")[:-1]):
                entry["signals"].append("artifact-directory-name-only")
            category = agent_category(rel, fn)
            if category:
                entry["agent_artifact"] = category
            files.append(entry)
            if fn.lower().endswith(".md") and not linked:
                documents.append(document_metadata(full, rel, args.document_bytes, errors))
        if capped:
            break
    ignored = run_git(root, ["check-ignore", "--no-index", "-z", "--stdin"],
                      "".join(f["path"] + "\0" for f in files)) if tracked is not None else None
    ignored_paths = set(ignored.stdout.split("\0")) if ignored is not None and ignored.returncode in (0, 1) else None
    for entry in files:
        entry["matches_ignore_rule"] = entry["path"] in ignored_paths if ignored_paths is not None else None
    files.sort(key=lambda f: f["path"])
    checklist = review_items(files, documents, args.review_age_days)
    report = {
        "schema_version": 2, "root": root,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "git": git, "protected_paths": protected, "omitted_dirs": omitted,
        "files_capped": capped, "errors": errors,
        "coverage": {"inventoried_files": len(files), "total_files": None,
                     "max_files": args.max_files, "document_preview_bytes": args.document_bytes,
                     "note": "No total-tree claim; omitted directories and protected paths are not counted. Names are hints, never removal verdicts."},
        "agent_artifacts": {category: [f["path"] for f in files if f.get("agent_artifact") == category]
                            for category in ("canonical", "agent-config", "tool-material")},
        "review_policy": {"age_days": args.review_age_days,
                          "note": "Review triggers only. Ignored/untracked is not a KEEP reason. Missing history is unknown. Recent modification does not prove current relevance."},
        "review_items": checklist,
        "documents": documents, "files": files,
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    print("cut-weight: %d files; %d Markdown documents; %d omitted directories; %d errors%s" %
          (len(files), len(documents), len(omitted), len(errors), "; FILE CAP REACHED" if capped else ""))
    print("Metadata only, no cleanup decisions. Inventory: %s" % out)
    print("Review checklist: %d items; age trigger: %d days" % (len(checklist), args.review_age_days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
