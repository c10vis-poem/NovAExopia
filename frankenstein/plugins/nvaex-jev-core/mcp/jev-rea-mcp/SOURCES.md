# Sources

## Copied
None. Custom-first: no donor code was copied.

## Derived (written here)
| File | Derived from | Note |
|---|---|---|
| server.py route_task | spec 4B server 3 (L0-L3 routing) | thin call into `../../scripts/jev_route.py`, which holds the rules and the TypeSafe call |
| server.py audit_gate | spec "5-Gate task auditing"; gate wording from nvaex-jev-core/skills/task-auditor | checklist only |
| server.py inspect_target | spec "REA static repo inspection" | read-only stdlib walk; no NvAEx-rea code used |
| server.py remember (`jev.remember`) | function of the jevmem plugin (`~/local-plugins/plugins/jevmem`, MIT, v0.7.6) which exposed search_memory/add_memory/list_memory/audit_memory via the `jevmem` npm CLI and the hosted api.typesafe.ai | no code copied; local JSONL add + recall only. audit_memory, the guard and always-on rules are not reproduced |
| server.py cloud_dispatch | spec "ag.cloud_dispatch" | job-file writer; optional POST to JEV_AG_BRIDGE_URL |

## Missing (not on the phone; not invented)
- JEV-Level-0-3-Taxonomy-Classification-Matrix.csv (Drive only). Drop it at skills/jev-router/taxonomy.csv in the plugin or set JEV_TAXONOMY_CSV; columns containing "level" and "task|example|desc|pattern" are used. Until then the keyword rules apply.
- ag-bridge.sh (Antigravity GCP Cloud Run bridge): not found. cloud_dispatch only writes job files unless JEV_AG_BRIDGE_URL is set.
- wiki-task-auditor (the 5-gate sub-agent): not found; gates reimplemented as a checklist.
- REA dynamic inspection (NvAEx-rea is a TS/Node reverse-engineering suite, ~/repos/NvAEx-rea): only static read-only inspection here; dynamic analysis would need a daemon/Node and is out of contract.
