# Tooling folders: inspect their role

The inventory labels known tool families as `tool-material`, not disposable.
Examples include `.gstack`, `.compound-engineering`, `.impeccable`, `_canon-check`,
and `_critic-layer`. Unknown plugin output must also be identified by content,
references, and producer/consumer evidence; no registry is exhaustive.

Inspect a folder before proposing its disposition:

| Contents | Treatment |
|---|---|
| Application-required hooks, scripts, MCP config, commands | KEEP with evidence of the runtime/build/test/deploy dependency |
| Optional development/review plugin code, skills, hooks, configuration | ASK whether to retain this tool's local setup, unless the user already decided |
| Canonical instructions and reusable project guidance | KEEP or reconcile in place |
| Completed audits, screenshots, transcripts, obsolete plans | Group by pass; preserve unresolved findings, then ARCHIVE |
| Useful local settings or private state | LOCAL_ONLY when shared consumers do not need tracked copies |
| Rebuildable caches or explicitly disposable output | DELETE within the agreed scope |
| Mixed or unknown purpose | Split by role; ask only about unresolved groups |

Before removing a tool host folder, inspect repo instructions, package scripts,
`.claude/settings*.json`, hook registrations, `.mcp.json`, skill/command links,
and other configuration that names it. A plugin installed globally does not prove
its local output is needed; absence from application imports does not prove a
local hook is unused. Do not modify global plugin installations as repo cleanup.

`CLAUDE.md`, `AGENTS.md`, module `INTENT.md`, and other instructions are maintained
in place. Their filename is not permission to archive, untrack, or delete them.
Reconcile stale content while preserving actual operating constraints. If the
repository itself distributes plugins, its plugin folders and skill references
are product assets, not cleanup residue.

No separate mandatory plugin questionnaire. Include meaningful tooling questions
in the same brief intent conversation. Existing answers apply across matching
groups. Identify who the consumer is: an optional review plugin reading its own
configuration is not an application dependency and does not settle retention.

Every detected tooling group must appear in the review, including ignored files
and tracked example configs. Split reports/captures from active settings and
scripts; do not use a single cache-file mention to account for a mixed folder.
State the evidence for keeping each subgroup. "Already gitignored; no action
needed" is invalid for a local-folder sanitation request. If no current use is
established, propose archiving completed output and ask whether unused setup
material should remain. Registry misses discovered during reading must be added
to the checklist; an unrecognized tool name does not exclude it from scope.

## Optional tool retention takes precedence over configuration protection

Distinguish **application operations** from **development-tool operations**.
An optional plugin can have executable code, registered hooks, tracked settings,
and a functioning cache without being necessary to the product. Those facts
describe how removal must be handled; they do not decide whether the tool stays.
Apply this distinction before the generic protected-configuration KEEP rule.

For each optional tooling group, establish one of:
- application-required: cite the actual runtime/build/test/deploy consumer; KEEP;
- user-retained: cite the user's current decision to keep the local setup; KEEP;
- user-retired: remove local setup within the agreed scope, preserving unique
  customizations and repairing its local registrations;
- retention undecided: ASK, even if the plugin is installed, configured, or active.

Do not claim "active" from filenames like active-tab.json, a tracked template,
an ignore exception, the presence of scripts, or a tool reading its own settings.
An ignore rule describes tracking policy, not a dependency. A configuration
example is not an active configuration. File ages help prioritize questions but
do not replace this retention decision. Apply the rule to repo-local agent skill
collections as well as named plugin folders.

Batch undecided tools into one material question with per-tool exceptions:
"These local development tools are not required by the application. Keep their
local setups, or remove them and reinstall when needed? I recommend archiving
unique settings and removing the unused setup; you can keep individual tools."
Explain any hook/command that will stop working and any unique configuration
that reinstalling will NOT reproduce. Honor an existing remove/keep decision
without asking again. Do not uninstall global plugins or remove product source
as part of local-folder cleanup.

When removal is selected, treat the folder and its local registrations as one
group. Inspect repository hooks/imports/config, remove only the retired tool's
references, preserve unrelated entries, and verify remaining tooling/application
consumers. Archive unique local code/config before removal; delete reproducible
stock files or caches only when regeneration or explicit discard is established.
An empty tool host folder should not remain merely because it once held a plugin.
