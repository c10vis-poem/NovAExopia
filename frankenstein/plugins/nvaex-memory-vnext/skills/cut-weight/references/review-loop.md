# One concise review, one shared understanding

Keep one living `review.md` in the local run directory alongside `inventory.json`
and the recovery `manifest.json`. Do not create a new in-repo report stack.

## Before execution

Record:
- mode, project, scope, run directory, baseline HEAD/status and coverage limits;
- past purpose, existing implementation, agreed direction, unresolved intent;
- sources supporting that interpretation (paths and relevant passages);
- groups with exact members, evidence, proposed disposition and preserved knowledge;
- the few questions that change disposition, answers and any split groups;
- resolved action plan including surviving-document edits and recovery location.

Use the inventory's `review_items` as the coverage checklist. For every ID record
its exact members, disposition, rationale, and inspected evidence. One group can
cover multiple IDs if they are listed explicitly; split mixed tooling folders
by member path. Add items discovered through links or unrecognized tools. Include
all major guidance and backlog documents, regardless of name, age, or Git state.
KEEP requires specific current usefulness; unknown usefulness becomes ASK.
For optional tooling, every KEEP must identify an application runtime/build/test/
deploy dependency or an explicit user retention decision. "Active tool config"
alone fails this check. List undecided optional tools as ASK and include them in
the grouped retention question; do not mark all checklist items resolved merely
because each folder contains configuration or code.
UNREVIEWED means inspection did not happen and must never be presented as KEEP.

Make the plan available before mutations. If the user requested only an audit or
discussion, stop after the review. Do not ask for execution approval just to turn
an audit into cleanup. For a cleanup request, act within already authorized
scope and resolved decisions. If a proposed action is outside that scope, ask
about that concrete action only; do not reopen the entire plan. Never treat
silence, elapsed time, or a suggested default as an answer.

Prefer 2-4 material questions, grouped by initiative or evidence. This is guidance,
not a fixed quota. Do not ask about facts already established in the session,
and do not ask separately about every file or every plugin. A user can split a
group by naming an exception. Hold unresolved groups without blocking independent
approved cleanup. If the user does not answer, retain the affected material.

## After execution

Update the same review with:
- actual moves/deletions/local-only changes and documentation edits;
- useful findings/decisions retained and their surviving homes;
- reference checks and relevant baseline-versus-after results;
- any restored files and newly discovered operating dependencies;
- exact recovery paths/commands and a link to the manifest;
- remaining decisions, errors, scan caps, and skipped checks;
- working-tree reduction, tracked-file reduction, and disk-space impact separately.

Report checklist totals: resolved / ASK / UNREVIEWED, with all unresolved IDs and
reasons. Verify the totals against the discovered checklist and added items.
ASK or UNREVIEWED entries and material scan exclusions mean a partial pass; say
what was accomplished without claiming complete sanitation. This accounting is
not a demand for more questions: batch ambiguous groups and retain unanswered
ones explicitly. Ignored files cannot disappear from the accounting.

Audit recovery against the actual changes: every removed non-disposable file has
a verified archive copy; every edited file has a verified pre-edit copy; every
change is recorded in manifest.json with original tracking state and final status.
Do not substitute a minimal TSV or assume Git makes pre-edit copies optional.
Reference repairs must include content checks of the destination's authority,
not merely successful path resolution. Report separately whether recovery,
coverage, document currentness, and relevant consumer checks passed.

Do not label static inspection as runtime verification. Keep the local archive
without a mandatory teardown question or expiry. The repository should contain
less residue after the operation, not a newly committed collection of cleanup
reports. Existing team documentation conventions may justify a concise decision
entry, but not copying the entire review back into source control.
