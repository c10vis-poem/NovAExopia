# Local graveyard and recovery

## Location and Git boundary

Default to a sibling `<project>-graveyard/<UTC-timestamp>-<unique-id>/` outside
**every containing Git worktree**, not merely outside the selected subfolder.
Resolve the repository root before choosing it. Record the absolute project and
archive paths; never reuse a run directory or overwrite an existing backup.
Use `files/<original-relative-path>` for archived originals and
`before/<original-relative-path>` for files edited in place. Reports sit beside
those folders so source filenames cannot collide with `manifest.json`.

If the user chooses an in-repo graveyard, add its anchored path to `.gitignore`
(or `.git/info/exclude` for a machine-local rule), verify the rule and that no
archive contents are tracked/staged before copying. An already tracked archive
requires an explicit local-only migration; ignoring alone does not untrack it.
Protect old `_quarantine` and `_graveyard` directories from candidate selection.
Never commit archived payloads, cleanup reports, or previously untracked private
files by default. Do not automatically rewrite history: ignoring/untracking and
new removal commits do not erase copies already in older commits.

## Recovery before mutation

1. Capture HEAD if available, index/worktree status, and existing changes.
   Leave unrelated staging and edits alone. No automatic checkpoint commit, Git
   initialization, stash, hard reset, or broad `git add`.
2. For every ARCHIVE/CONSOLIDATE removal and edited guidance/config file, record
   exact source/destination, original tracked status, action, reason, byte size,
   SHA-256, and relevant metadata in `manifest.json`. Include newly created files
   so undo can distinguish creation from modification. Preserve permissions and
   timestamps when copying; report metadata limitations.
3. Copy to the resolved archive and verify the copy's size and SHA-256 before
   removing or editing the source. Write the manifest incrementally with states
   `planned`, `copied`, `applied`, or `failed`; retain partial recovery on failure.
   Re-check the source hash immediately before mutation. If it changed, stop that
   item and re-evaluate instead of overwriting concurrent work.
4. Use native filesystem operations with literal paths. Resolve source and target
   containment before any move/delete. Reject traversal, collisions, symlinks,
   junctions, and nested repositories for automatic mutation; inspect separately.
   Never follow a link out of the project or recurse through archive contents.
5. ARCHIVE: remove originals only after verified copies. Tracked removals appear
   in Git as deletions; archived payloads never enter Git. CONSOLIDATE: verify
   useful knowledge has a surviving home before removing its original.
6. LOCAL_ONLY: keep contents at their existing path, add a narrow ignore rule,
   and use `git rm --cached -- <exact-path>` only if tracked and authorized.
   If staged content differs from disk/HEAD, leave it unresolved rather than
   using force. Record the index change; never untrack unrelated files.
7. DELETE: record the exact regeneration command or explicit discard decision.
   Irreplaceable output with uncertain value goes to ARCHIVE. In a non-Git
   project the same verified local recovery protocol applies.
8. Verify links/consumers and compare relevant checks with baseline. Inspect the
   staged diff and ignored state to ensure recovery material cannot be published.
   Commit only when requested, using exact scoped paths and preserving other work.

## Required manifest and completion check

Use JSON, not a reduced TSV. The manifest records `project_root`, `run_directory`,
`baseline_head` (null without Git), and a `changes` list. Each change contains
`source` (project-relative), `action`, `tracked`, `reason`, `bytes`, `sha256`
(the pre-change content), `backup` (run-relative files/ or before/ path, or null
for a newly created file/proven disposable delete), `metadata`, and `status`.
Record `regeneration` or the explicit discard decision for deletes without a
backup. Record post-edit hashes for new/edited files to detect later changes
during restore. Manifest status must reflect actual applied/failed operations,
not leave removed sources labeled only `copied`.

Before an edit, including a tracked AGENTS.md/CLAUDE.md/ignore-file edit, require
its verified before/ copy. A Git blob may differ from the pre-edit working tree;
"tracked in Git" is never a backup waiver. Before final reporting, compare every
actual changed path with the manifest, re-hash recovery copies, and confirm exact
restore paths/commands are recorded. Disclose any gap as incomplete recovery.
Never fabricate a pre-edit backup after the fact. A recovered baseline copy must
be labeled as such and checked against evidence of the pre-edit state.

Do not auto-stash to create an A/B test baseline. For document-only cleanup,
reference/currentness checks normally suffice. If runtime comparison is needed,
use an isolated baseline checkout without disturbing the user's staging/worktree.

## Restoration

Recovery comes from verified local copies, not an assumed commit. Provide actual
shell-appropriate commands using the real recorded paths, never placeholders.
Before restoring, verify the archived hash and check for destination collisions.
Do not overwrite newer work; restore to a separate path or resolve the conflict.
Restore original relative locations and recorded metadata where supported.

For edited files, use the `before/` copy. For removed files, use `files/`.
For LOCAL_ONLY, remove only the ignore rule added by this run and restore tracking
with `git add -- <path>` when appropriate. Preserve pre-existing ignore rules and
index state; do not offer a broad `git revert` or `reset --hard` as blanket undo.
For newly created files, remove only if unchanged since this run. Re-run the
relevant verification after restore. Local recovery is not a remote backup;
archive loss loses recovery for material that was never committed.

Keep the graveyard until explicitly asked to purge a specified run. There is no
automatic expiry or "delete everything" closing step. Moving to a local archive
reduces working-tree clutter and future sharing, not bytes on the same disk or
old Git history.
