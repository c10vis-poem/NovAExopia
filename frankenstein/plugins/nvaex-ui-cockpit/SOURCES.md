# Sources (custom first: ideas and small pieces taken, no upstream files copied wholesale)

All upstream plugins are MIT. Their LICENSE files are kept in `licenses/`. Read from
`~/.claude/plugins/synced/a5d13a90-190b-42eb-ad1b-69c924919b1b_b410cc73-6e72-411c-a9de-4edf62ec27d7/<id>/`
(their hook dirs are renamed `hooks.off-20261028` on this device; the code was read from there).

| Our file | Taken from | Original plugin / version / license | What was taken |
| --- | --- | --- | --- |
| `hooks/mods/token-cache-gauge.tsx`, `hooks/lib/gauge-fmt.ts` | `3cc26927-8537-4e13-af57-560ff2c4684c/hooks.off-20261028/register.js` | cache-ttl-timer 1.0.0, MIT (Seongje Hong) | restart-the-TTL-on-answered-main-loop-request pattern (`turn.step`, skip subagents); 1h/5m TTL idea |
| same | `c12c552c-872f-444e-bf53-779975265e18` and `21b1994e-f093-4312-8375-7dc858669981` `hooks.off-20261028/register.tsx` | context-bar 0.2.1 / 0.2.3, MIT (Akash Bhatnagar / skylu) | `session.measure` feed of context % and rate limits |
| same | `fb42133c-a868-49c9-8daa-65387a20fb16/hooks.off-20261028/register.tsx` | gas-gauge 0.2.2, MIT (Rostech) (no LICENSE file shipped; README/manifest say MIT) | E..F fuel look, percent-left colouring (green/yellow/red) |
| `scripts/profiles.py` | `37e770d1-74d7-4c34-8082-f5bdbba14d6e/hooks.off-20261028/profile.ts`, README | harness-scope 0.1.3, MIT (Tatsuya Shimomoto) | profile dir `~/.claude/harness-scope/profiles/`, selector `.claude/harness-scope.json`, rule shape `{skills|agents|instructions|tools: {allow|deny: [...]}}`, name regex, bundled `writing` profile. Python rewrite; only the selector is ever written |
| `scripts/inventory.py`, `scripts/configtree.py` | none (written new, reads `installed_plugins.json` and plugin folders) | n/a | n/a |
| `scripts/killswitch.sh` | `frankenstein/shared/killswitch.sh` | this repo | vendored by `bin/vendor-shared.sh` |

Stripped: icons, screenshots, i18n (7 languages), tests, lockfiles, `.in_use` markers, privacy/ToS links. No network calls, no telemetry.

## Missing (named by the spec, not on this phone, not invented)
- `plugin-eval`, `plugin-improver`: no plugin of those names under `~/.claude/plugins/{synced,cache}`, `~/local-plugins`, `~/repos` (probe: `find -iname`, plugin.json `name` scan of synced). Only an unrelated `plugin-evaluation.md` eval doc exists. Not part of the 4 mods; skipped.
- `statusline-pro`, `claude-hud`: same probes, not found. The gauge is built as a band above the prompt (`ui.render` AbovePrompt) instead of a `statusLine` script. `~/.claude/statusline.py` does not exist on this device.
- JEV telemetry feed (routing tier L0-L3, sub-agent count, `claude-eta`): depends on `nvaex-jev-core`, which a cockpit must not require (hot-swap rule 3). Not built; see README "Not built".
