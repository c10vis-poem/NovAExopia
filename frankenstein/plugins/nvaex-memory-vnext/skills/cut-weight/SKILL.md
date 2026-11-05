---
name: cut-weight
description: 'Sanitize repositories and project folders by removing development residue: superseded plans, completed audits, duplicate docs, plugin output, scratch files, and disposable artifacts. Read project intent, resolve consequential ambiguities through a brief grouped conversation, archive locally, and repair surviving guidance. Use for repository bloat, folder cleanup, or audit-only reviews. Operational code is protected; feature retirement is separate work.'
---

# Cut Weight

When called from a review, canon-alignment or execution workflow, read
[workflow-handoff.md](references/workflow-handoff.md). Use the same cleanup and
recovery contract whether installed independently or bundled inside another plugin.

Cut the residue of building and reviewing a product while preserving the
machinery that operates it. Product intent is the filter for documentation
and development artifacts, not permission to remove sidelined features.

## Scope and modes

- **audit**: inventory, interpretation, proposed groups and unresolved questions.
  No project edits, moves, untracking, commits, or execution checks with side
  effects. Write audit output outside the project. Respect requests for no Q&A.
- **cleanup** (default for action requests): establish the shared understanding,
  execute the authorized cleanup groups, reconcile docs, and verify.
- **aggressive**: the same scope with more decisive removal of proven residue.
  It does not broaden authorization to source, data, or permanent archive purge.
  Treat previous "standard" invocations as cleanup.

Protect source, tests, dependencies, lockfiles, migrations, runtime assets,
secrets/data, CI, deployment, and application-required tool configuration by default. Core
operating files move only as an explicitly scoped exception with dependency
analysis, recovery, and baseline checks. Otherwise record separate follow-up
work. "Deferred", "secondary", and "not promoted" do not mean obsolete code;
never require a promise of future use to protect working implementation.

This protection covers the product, not every development plugin used to build
or review it. Optional tool code, skills, hooks, caches, and configuration require
a retention decision under [agent-artifacts.md](references/agent-artifacts.md).
If there is no application dependency or existing user decision, ASK whether to
keep or remove the local setup. Being installed, tracked, or executable does not
settle that question. Removal can include local registrations and recoverable
customizations; global plugin uninstall remains outside ordinary folder cleanup.

## 1. Discover before questioning

Read repository instructions and inspect Git status without changing it.
Preserve existing edits and staging; never auto-stash, auto-commit a dirty tree,
initialize Git, or add untracked files just to create a checkpoint.

Choose a unique run directory outside the repository, normally a sibling:
`<project>-graveyard/<UTC-timestamp>-<unique-id>/`. Keep the inventory, one
living `review.md`, and recovery manifest there. Do not introduce three new
reports into the project on every run. An explicitly chosen in-repo archive
must be ignored before use and verified untracked; see
[quarantine-protocol.md](references/quarantine-protocol.md).

Run the read-only inventory using the installed skill's absolute script path:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/cut-weight/scripts/inventory.py" "<project-root>" --out "<absolute-run-directory>/inventory.json"
```

If the plugin variable is unavailable, locate this skill's `scripts/inventory.py`.
Use Python 3. The script inventories metadata and discovers Markdown; it does
not decide semantic relevance, prove reachability, or execute cleanup. Report
caps, omitted directories, unknown history, and errors as coverage limits.

Read [intent-review.md](references/intent-review.md). Inspect current guidance,
recent plans, strategy/product/roadmap/design files, and related older clusters.
Follow links and shared initiatives across folders; do not stop at root-level
Markdown or a filename keyword match. Existing module `INTENT.md` files are
useful evidence, not a required standard or reason to create another document.

Use [entry-points.md](references/entry-points.md) to identify runtime and tool
consumers near candidates. The operational keep-set is a protective boundary,
not the main cleanup target. Follow repository-specific discovery tools first.

The inventory includes `review_items`, an explicit checklist for every discovered
Markdown document and recognized tooling group. Use `--review-age-days N` to
override the default **60-day review trigger**. Either age clock crossing the
threshold requires review; missing Git history does not exempt an untracked file.
Age flags never authorize removal of operational files. Read completion history
and supersession evidence even for recently modified documents.

## 2. Establish the shared filter

Present a short, cited interpretation of what the project was, what exists,
its agreed current direction, and what remains undecided. Distinguish observed
implementation, user decisions, and proposals. Do not invent a future roadmap.

Ask only questions whose answers change disposition or preserve unique knowledge.
Usually 2-4 grouped questions are sufficient; zero is fine if the session already
settled them. Offer a recommendation, evidence, affected groups, and a free-text
way to split a group. Do not ask per file, reopen settled decisions, or use a
questionnaire as ceremony. Await answers on genuinely unresolved groups while
continuing independent analysis. Silence is not agreement.

Examples: "These completed audits appear superseded by the current baseline;
retain the unresolved findings in the backlog and archive the old runs?" or
"These two plans disagree about whether the experiment is still active. Which
should guide this cleanup?" Do not ask whether to retire working features as a
routine part of sanitation.

Read [review-loop.md](references/review-loop.md) for the concise record and
execution boundary. Existing explicit authorization persists: make the plan
concrete and reviewable, but do not request a second approval for the same scope.

## 3. Classify by purpose and evidence

Read [evidence-signals.md](references/evidence-signals.md) and, for tooling
folders, [agent-artifacts.md](references/agent-artifacts.md).

Group by initiative, improvement pass, tool, or shared purpose, with exact paths.
Separate current guidance, reusable decisions, superseded narrative, finished
review output, active configuration, and disposable output even within one folder.

Account for every `review_items` ID in the review, including ignored/untracked
material. Group IDs together when appropriate, but enumerate all covered IDs
and paths. Add tool families or major documents discovered outside the script's
registry. Assign a disposition with evidence, or explicitly mark UNREVIEWED.
Report resolved, ASK, and UNREVIEWED counts; gaps mean a partial pass, not complete
sanitation. KEEP requires a current consumer, retained knowledge, or explicit user
decision. "Already ignored", "canonical filename", and "another old doc links
here" are not sufficient reasons. Uncertain usefulness is ASK, not an invented KEEP.

| Disposition | Meaning |
|---|---|
| KEEP | Current useful material or protected operating files |
| CONSOLIDATE | Preserve unique useful content in an existing authoritative doc, then archive redundant originals |
| ARCHIVE | Move obsolete material to the local graveyard with a verified recovery copy |
| LOCAL_ONLY | Keep at its working path, ignore, and untrack if currently tracked |
| DELETE | Proven disposable/regenerable output within the authorized scope |
| ASK | A meaningful unresolved decision; leave the affected material untouched |

Age, references, or a plugin name alone never decide. Recent material may be
superseded; old material may be authoritative. A live dependency blocks removal,
while a stale link from an old plan can be repaired rather than preserving both
forever. Default uncertain non-regenerable residue to archive, not permanent loss.

## 4. Execute and reconcile

Follow [quarantine-protocol.md](references/quarantine-protocol.md). Record the
baseline Git state and relevant checks, create recovery copies for changed and
removed files, then execute only the resolved groups. Do not publish or rewrite
Git history. Commits are not required for recovery and are not automatic.

Cleanup includes bounded edits to surviving guidance:

- `AGENTS.md`: correct maps, commands, and references to current documents.
- `CLAUDE.md`: remove stale/duplicate directions; preserve operational invariants.
- `DESIGN.md`: repair references and distinguish current rules from experiments.
  Aesthetic redesign or changing the design canon is separate work.
- Product/strategy/intent docs: retain one authoritative home for each fact;
  link instead of copying narratives across every instruction file.

Read the destinations of guidance links before calling them repaired. Check
PRODUCT, STRATEGY, TODOS/backlogs, and current baseline documents against the agreed
direction. A valid link to a superseded product narrative is still stale guidance.
Separate genuinely open backlog items from lengthy Done/history sections; retain
useful unresolved knowledge and propose archiving completed history as a group.

Preserve accurate documentation of existing features even when they are not
current priorities. Never rewrite a historical audit to pretend a later result
was known then; update the current index or add a dated supersession note.
Broader product, architecture, or aesthetic decisions become follow-ups.

## 5. Verify and finish

Check surviving links and instruction imports, tool/hook references, Git status,
and the staged diff. Confirm no archive contents or private artifacts are staged.
Reconcile the review checklist and recovery manifest before claiming completion.
Verify archived hashes and pre-edit backups, including tracked guidance files.
Use `manifest.json` with the fields in the recovery protocol; a path/hash TSV is
not a replacement. Missing records/backups must be disclosed and repaired where
possible, never described as unnecessary because Git exists.
Re-run relevant baseline checks for any affected consumers; documentation-only
cleanup normally needs reference/content checks, not the entire application suite.
If a regression appears, restore implicated files and record the reason.

Update the same `review.md` with actual dispositions, knowledge retained,
verification, coverage limits, and exact recovery paths/commands. Distinguish
working-tree files removed, files no longer tracked, and actual disk space freed:
archiving on the same disk does not free that disk space. Keep the graveyard by
default. Permanent purge is a separate explicit request, never a routine closing
question or automatic 30-day expiry.
