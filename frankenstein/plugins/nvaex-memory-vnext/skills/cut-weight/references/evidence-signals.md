# Evidence and disposition

Apply this order, explaining exceptions in the review:

1. **Optional development tooling -> retention decision first.** Apply
   [agent-artifacts.md](agent-artifacts.md) before protecting configuration.
   If application-required or explicitly user-retained, KEEP. If retention is
   undecided, ASK; if user-retired, remove its local setup and registrations
   with appropriate recovery. Executable plugin files are not automatically
   application source. Self-use by the tool is not a product dependency.
2. **Application operational consumer or protected role -> KEEP.** Source, tests, lockfiles,
   migrations, runtime assets, CI/deploy, credentials/data, application-required
   skills/hooks and configuration are protected. Zero text references does not make a
   platform-consumed file dead. Dynamic loading preserves the relevant directory.
3. **Current guidance or unique knowledge -> KEEP or CONSOLIDATE.** Read content.
   Unresolved findings, rationale, and working procedures need a surviving home.
4. **Superseded/completed residue -> ARCHIVE.** Establish what replaced it or
   why the pass is finished. Resolve any useful remaining knowledge first.
5. **Proven disposable output -> DELETE.** Confirm an applicable regeneration
   command or explicit discard authorization. `build`, `dist`, `out`, screenshots,
   logs, JSON, and databases are not inherently disposable.
6. **Useful user-retained personal/tool state -> LOCAL_ONLY.** Verify the tool still needs its
   location and that shared consumers do not depend on tracked copies.
7. **Consequential uncertainty -> ASK.** Only the affected group waits.

## Mandatory review triggers

Default to 60 days, configurable through `--review-age-days`. If either mtime or
Git last-touch reaches the threshold, review purpose, recent activity, current
consumer, and supersession evidence. Record both clocks when they disagree; a
fresh checkout or minor edit does not refresh the meaning of old content. Null
Git history is unknown, not recent activity and not a reason to skip local files.
Record dated content/status evidence separately from filesystem/Git clocks.

Also review completed-pass output, superseded narrative, example configuration,
and Done-heavy backlogs even below the threshold. These are review obligations,
not automatic archive/delete rules. Operational files remain protected.

Ignored/untracked state affects sharing and recovery, never relevance. Evaluate
local clutter and tracked clutter equally. Current activity means evidence of
use or unfinished work, not merely a modified timestamp. An old QA report and
its screenshots can be one archive proposal while an active hook in the same
tool family remains untouched. If usefulness cannot be established, ask the
user about the group rather than quietly keeping it.

## Additional evidence

- **References:** trace imports, instruction imports, scripts, links, manifests,
  CI and hook commands. Search both path and basename, excluding archive internals.
  A live dependency protects; a reference in superseded narrative can be repaired.
  Documents that only reference one another can form a historical cluster.
- **Age:** use mtime and Git last-touch as supporting evidence. Null history is
  unknown, never proof of age. New reports can already be redundant; old specs
  can still be authoritative. State scan limits.
- **Names:** `old`, `scratch`, plugin names, and dated filenames are discovery
  hints. Never let names alone authorize a move or deletion.
- **Content:** identify unique knowledge, replacement documents, unfinished work,
  duplicated passages, and the original purpose of an output. Preserve provenance
  when consolidating. Semantic judgments must cite inspected content.
- **Size:** helps prioritize and report impact; it does not determine relevance.

Do not automatically cut generated-but-required inputs: lockfiles, snapshots,
migrations, committed codegen, vendored assets, or deploy output without a proven
rebuild path. Do not prune dependencies or edit dead code during ordinary residue
cleanup. Record those as separately scoped maintenance work.
