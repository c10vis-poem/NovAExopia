# Sources

## Copied
| File here | Origin | Version | License |
|---|---|---|---|
| skills/drunken-master/SKILL.md (verbatim) | drunken-master (beatlejute), synced plugin fda4eab2... | 1.1.3 | MIT (LICENSE-drunken-master) |

## Derived (written here, not copied)
| File | Derived from | License note |
|---|---|---|
| scripts/scorecard.py (13 regex checks) | llm-dark-patterns SPEC.md + packs/locale/en.txt vocabulary (waitdeadai) | Apache-2.0 (LICENSE-llm-dark-patterns kept) |
| skills/jev-router/, scripts/route.py | claude-jev / building-with-typesafe-jev two-stage idea; rewritten as local keyword router | n/a, no code copied |
| skills/task-auditor/, scripts/health.py | spec's 5 gates; claude-eta "every 5 calls" cadence + repeat-edit loop idea | n/a, no code copied |
| scripts/killswitch.sh | frankenstein/shared/killswitch.sh via bin/vendor-shared.sh | own |

## Not copied (deliberate)
- claude-jev / jevmem runtime: calls hosted api.typesafe.ai (network + API key); contract is local-first. Router is a local keyword table instead.
- claude-eta (1.3.x): TypeScript dist, telemetry/admin server, lockfile. Only the cadence idea used.
- spec-drift, skill-gate: hooks live in hooks.off-* dirs (disabled on this phone); skill-gate blocks. Not needed by the row-1 spec capabilities.
- aesop-task-observer: already installed globally (~/repos/aesop-task-observer, 691-line skill); a second copy would double-trigger. Operator decision below.

## Missing (not on the phone)
- llm-dark-patterns `hooks/*.sh` (the 30 check scripts; only hooks.off-20261028/hooks.json, packs/, lib/ and test fixtures exist). Scorecard is a reimplementation of 13 checks.
- context-protector, safe-bash (no plugin of these names found under ~/.claude/plugins, ~/local-plugins, ~/repos).
- claude-code-audit-stack: present (agents only: claim-auditor etc.), not copied; its hooks are disabled and the spec names it only as the "audit-Dynamic" concept.
- JEV-Level-0-3-Taxonomy-Classification-Matrix.csv (Drive only; levels in route.py are a length/keyword heuristic).
