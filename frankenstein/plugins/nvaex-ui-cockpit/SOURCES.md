# Sources (custom first: ideas and small pieces taken, no upstream files copied wholesale)

All upstream plugins are MIT. Their LICENSE files are kept in `licenses/` where upstream shipped one. Read from
`~/.claude/plugins/synced/a5d13a90-190b-42eb-ad1b-69c924919b1b_b410cc73-6e72-411c-a9de-4edf62ec27d7/<id>/`
(their hook dirs are renamed `hooks.off-20261028` on this device; the code was read from there).

| Our file | Taken from | Original plugin / version / license | What was taken |
| --- | --- | --- | --- |
| `hooks/lib/ctx-rows.ts`, `hooks/mods/context-window.tsx` | `10c1f421-9df4-451f-8b82-0e26666eae12/hooks.off-20261028/classify.ts`, `register.tsx` | context-window 0.5.4, MIT (Chris Han; no LICENSE file shipped, manifest says MIT, so none kept) | idea only: list entrants from `$.session.messages({as:'api'})`, chars/4 estimate, tool_result named by its tool_use. Re-written, 3414 bytes. Startup breakdown, i18n, timeline view, token-limit fill not taken (usage display) |
| `hooks/mods/plugins-panel.tsx` (toggle) | `7ae1da3c-5c66-4372-9627-5c77932d0221/src/plugin-config.ts` `togglePlugin` | claude-plugin-manager 1.0.0, MIT (DVKolm), `licenses/LICENSE.plugin-manager` | idea only: enable/disable action. Not taken: it edits settings.json directly; ours calls `claude plugin enable|disable` after a name regex check. Web server, UI bundle, auth not taken |
| `scripts/profiles.py` | `37e770d1-74d7-4c34-8082-f5bdbba14d6e/hooks.off-20261028/profile.ts`, README | harness-scope 0.1.3, MIT (Tatsuya Shimomoto) | profile dir `~/.claude/harness-scope/profiles/`, selector `.claude/harness-scope.json`, rule shape `{skills|agents|instructions|tools: {allow|deny: [...]}}`, name regex, bundled `writing` profile. Python rewrite; only the selector is ever written |
| `scripts/inventory.py`, `scripts/configtree.py` | none (written new, reads `installed_plugins.json` and plugin folders) | n/a | n/a |
| `scripts/killswitch.sh` | `frankenstein/shared/killswitch.sh` | this repo | vendored by `bin/vendor-shared.sh` |

Stripped: icons, screenshots, i18n (7 languages), tests, lockfiles, `.in_use` markers, privacy/ToS links. No network calls, no telemetry.

## Missing (named by the spec, not on this phone, not invented)
- `plugin-eval`, `plugin-improver`: no plugin of those names under `~/.claude/plugins/{synced,cache}`, `~/local-plugins`, `~/repos` (probe: `find -iname`, plugin.json `name` scan of synced). Only an unrelated `plugin-evaluation.md` eval doc exists. Not part of the 4 mods; skipped.
- `statusline-pro`, `claude-hud`: same probes, not found. The gauge is built as a band above the prompt (`ui.render` AbovePrompt) instead of a `statusLine` script. `~/.claude/statusline.py` does not exist on this device.
- JEV telemetry feed (routing tier L0-L3, sub-agent count, `claude-eta`): depends on `nvaex-jev-core`, which a cockpit must not require (hot-swap rule 3). Not built; see README "Not built".

## Removed 2026-11-05 (fold pass)
`token-cache-gauge` (+ `gauge-fmt.ts`, its tests, `cacheTtl` option, licences cache-ttl-timer and context-bar): a usage display derived from plugins the brief removes; the operator is building a custom one. Gas-gauge/context-bar/cache-ttl-timer credits above were dropped with it.

## Size before / after (du -sk)
| Item | Before | After |
| --- | --- | --- |
| package | 139 KB | 124 KB |
| context-window source folder | 181 KB | 3414 bytes of code |
| plugin-manager source folder | 2373 KB | ~12 lines in plugins-panel + 1 KB licence |
| harness-scope | already in package, unchanged (822 KB source) | |

## Added mods (written from scratch, no source files copied)
file-tree-panel, agent-configs-panel, top-button-row, browser-cards, jev-panel: original code from the operator spec (mods/SPEC.md items 1-7). No upstream licence applies.
