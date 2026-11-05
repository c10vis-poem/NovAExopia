# Handoff from design review and execution

Cut Weight works independently or as the cleanup stage in a larger workflow.
Its inventory and recovery protocol are identical in both forms. Bundling does
not broaden authorization or turn cleanup into an automatic final step.

## Intake

Read the relevant current canon report, explicit decisions, review issue IDs,
implementation/verification status, and run ledger if available. These are
evidence of intent, not commands to delete. Carry forward decisions within their
scope; ask only about genuinely unresolved retention choices.

Separate these roles before classifying a workflow's artifacts:

- Current standards and decision records remain authority until superseded.
- Unresolved issues and incomplete verification remain live work.
- Active plans/ledgers and their referenced evidence remain required consumers.
- Completed, superseded captures and reports are archive candidates only after
  unique decisions and unresolved findings have a surviving home.
- Reproducible scratch output needs an exact regeneration path or an explicit
  discard decision before DELETE.

Do not move evidence that a current run still references merely because that
step is complete: a hash-based ledger would correctly mark it missing. Retain it
while the run remains current. If the user retires an entire historical run,
archive its coherent evidence set and record that retirement and recovery path.
Never change a failed/unverified issue to verified as part of cleanup.

## Recovery location and result

Follow `quarantine-protocol.md`. Choose the graveyard outside every containing
Git worktree. Inventory, living review, verified original copies and manifest
belong there even when the calling workflow normally stores outputs in-project.
Return the absolute review and manifest paths, actual dispositions, unresolved
item IDs, coverage limits and recovery instructions. A calling run may record
those pointers; do not put archive payloads in its ordinary evidence directory.

After authorized cleanup, verify affected references/consumers, preserve the
pre-edit backups and disclose any partial pass. If a canon baseline tracked a
changed document, refresh its affected findings before saving a new baseline.
The inventory discovers metadata; semantic classification, authorization,
mutation and restoration are agent/user work, not automatic script guarantees.
