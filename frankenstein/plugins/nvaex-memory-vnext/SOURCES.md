# Sources (parts donors; custom first)

| Path here | Origin | Version | License | How |
|---|---|---|---|---|
| scripts/memory_lint.py | anchor-memory (Rishabh Choudhry) scripts/memory_lint.py | 0.1.0 | MIT | copied verbatim (stdlib drift linter) |
| skills/anchor-memory/spec.md | anchor-memory docs/anchor-anchors-spec.md | 0.1.0 | MIT | copied verbatim |
| skills/ccfind/SKILL.md, scripts/ccfind.mjs | ccfind (Evghenii Pogonii) | 0.19.0 | MIT | copied verbatim (no network code found; demos/gifs/CI dropped) |
| skills/cut-weight/** (SKILL.md, references/, scripts/inventory.py) | cut-weight (Matthew Cohen) | 0.4.5 | MIT | copied verbatim (SHA-256 archive protocol is in references/quarantine-protocol.md) |
| scripts/vnext.py snapshot/freeze | continuity (vikash) 1.5.1 design | MIT | reimplemented in ~60 lines; upstream bundles are 150KB-900KB JS and include auto-commit + blocking Stop, so not copied |
| scripts/vnext.py nudge, skills/whydone | whydone (Danil Chevgan) 1.4.1, SCHEMA.md v1 + PromptInjection idea | MIT | reimplemented nudge-only; entry format follows SCHEMA v1; 409KB CLI not copied |
| scripts/vnext.py recap, config.json | memory-agent (Volodymyr Isai) 0.1.0 design (daily KB, autoPromote key) | MIT | reimplemented mechanically; upstream is LLM-driven + polling capture (daemon-like), so not copied |
| scripts/vnext.py map | create-smartfolder (Paul Hess) 6.6.0 concept only | CC-BY-4.0 AND MIT | reimplemented; upstream SKILL.md (36KB) and kit (258KB) not copied, and upstream does not produce MAP.md |
| scripts/killswitch.sh | frankenstein/shared/killswitch.sh | n/a | vendored copy |
| licenses/*.LICENSE | upstream LICENSE files for every plugin above | | kept |

## Missing
- Spec names a 322-line anchor-memory linter: phone copy is exactly 322 lines (matches).
- Spec: `memsearch-aesop` and `OB1` Supabase schemas: not searched for or copied; the spec's Section 2 row 2 task text did not list them for this build. Add later.
- JEV auditor gate / `jevmem` (promotion step): belongs to nvaex-jev-core; this package never promotes.
- Upstream memory-agent LLM extraction/merge pipeline: deliberately not included.
