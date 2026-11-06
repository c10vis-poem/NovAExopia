#!/usr/bin/env python3
"""gdrive_fetch.py REMOTE:path DEST [--dry-run]: copy a Drive path to DEST via rclone (read-only on Drive).
Google Docs -> docx, Sheets -> csv, Slides -> pptx. Skips files that already exist locally."""
import shutil, subprocess, sys

args = [a for a in sys.argv[1:] if a != "--dry-run"]
if len(args) != 2 or ":" not in args[0]:
    sys.exit(__doc__)
if not shutil.which("rclone"):
    sys.exit("rclone not on PATH")
cmd = ["rclone", "copy", args[0], args[1], "--drive-export-formats", "docx,csv,pptx",
       "--ignore-existing", "--immutable", "-v"] + (["--dry-run"] if "--dry-run" in sys.argv else [])
print(" ".join(cmd), file=sys.stderr)
sys.exit(subprocess.call(cmd))
