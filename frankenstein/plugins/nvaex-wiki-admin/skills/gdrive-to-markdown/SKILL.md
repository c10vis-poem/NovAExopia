---
name: gdrive-to-markdown
description: Pull Google Docs/Sheets/Slides (or any Drive file) into raw/ as local files through rclone, then convert to Markdown. Use when the operator names a Drive folder/file to ingest. Local path, no claude.ai connector, no OAuth in this package (rclone remotes already hold the tokens).
---

# Drive to Markdown (step 3 of wiki-admin-ingest)

Rules: the document is saved whole and verbatim (no summaries; clean format only); if the target file already exists, ask before overwriting; never put tokens in the repo.

1. Pick the remote: `rclone listremotes`. Two accounts = two remotes; use the one the operator names.
2. Fetch, read-only on Drive: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gdrive_fetch.py REMOTE:path/in/drive <raw-dir> [--dry-run]`
   Exports Docs as DOCX, Sheets as CSV, Slides as PPTX (rclone `--drive-export-formats`; the converter reports PPTX as unsupported by name), and never deletes or writes to Drive (`copy` only). Existing local files are skipped, not overwritten.
3. Convert: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/convert_raw_to_md.py <raw-dir> <work>/clean_md`, then verify as in `wiki-admin-ingest` step 5.
4. Images and diagrams in a Doc do not survive text export: when a section reads "see figure" with nothing there, leave `> NOTE: figure not transferred` in the file and tell the operator which sections lack one.

If rclone fails with an auth error, stop and report it; do not start an OAuth flow.
