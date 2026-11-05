# nvaex-ui-cockpit

Four small, independent UI mods for Claude Code in one hot-swappable package (Frankenstein set, package 6). Python stdlib and a TSX hooks module; no daemons, no network, no hooks that block.

| Mod | What you get | Command |
| --- | --- | --- |
| `plugins-panel` | Band above the prompt `Plugins: 8/47 active`; pane with each plugin's skills, agents, commands, hooks and listed-token footprint | `/plugins-panel` |
| `env-customizer-panel` | Pane with global / marketplace / repo overview and a profile picker (harness-scope profiles). Writes only `<repo>/.claude/harness-scope.json` | `/env`, `/env use NAME`, `/env clear` |
| `obsidian-config-tree` | Searchable tree of every enabled skill, agent, command, hook and script with a one-line plain-English explanation | `/config-tree [query]` |
| `token-cache-gauge` | One band: context fill %, prompt-cache TTL countdown `5:00` to `0:00`, 5h/7d fuel (percent left). Separate mod so a custom usage display can replace it | `/gauge [5m\|1h]` |

## Swap in / out
```
claude plugin enable  nvaex-ui-cockpit@novaexopia
claude plugin disable nvaex-ui-cockpit@novaexopia
```
Nothing else depends on it and it depends on nothing else. After enabling, `/reload-plugins` or restart.

Swap one mod without touching the others (e.g. to run your own usage display instead of the gauge):
```
mkdir -p ~/.claude/state/off && touch ~/.claude/state/off/nvaex-ui-cockpit.token-cache-gauge   # off
rm ~/.claude/state/off/nvaex-ui-cockpit.token-cache-gauge                                       # back on
```
Mod names: `plugins-panel`, `env-customizer-panel`, `obsidian-config-tree`, `token-cache-gauge`. Whole package off: `touch ~/.claude/state/off/nvaex-ui-cockpit`. Everything off (all Frankenstein packages): `touch ~/.nvaex-hooks-off`.

## Hooks and kill switches
One hooks module (`hooks/register.tsx`), one `session.start` hook for the package (it runs each mod's init, failing open), plus per-mod `command.run`, `ui.render`, and for the gauge `session.measure` and `turn.step` (observe only, always `next`). Each mod asks `scripts/killswitch.sh nvaex-ui-cockpit <mod>` (cached 2 s) before acting; when off it passes straight to the engine. Nothing blocks, so no override message is needed.

Option (`/config`): `cacheTtl` = `5m` (default) or `1h`.

## Notes
- Layout: terminal bands and panes need the terminal surface; panes seat at 110+ columns (see `$.ui.open`), the commands print text when no pane is placed.
- `env-customizer-panel` never edits `~/.claude/settings*.json`. A profile takes effect when the harness-scope mod is installed and the next session starts.
- Cache TTL is an estimate from the last answered request (no transcript parsing); set it with `/gauge 5m|1h`.

## Not built
JEV telemetry feed (routing tier, sub-agent count, `claude-eta`): needs `nvaex-jev-core`; a cockpit that required it would break hot-swap. Add it there as a status-line contribution. `plugin-eval`, `plugin-improver`, `statusline-pro`, `claude-hud` were not found on the device (see SOURCES.md).

## Tested on device
`sh tests/selftest.sh` (Termux, Android arm64, node 26, python 3.14):
```
PASS inventory summary
PASS inventory counts
PASS inventory json+tokens
PASS profiles list
PASS profile use writes selector
PASS profile marked current
PASS bad name rejected
PASS profile clear
PASS settings.json untouched
PASS config tree one-line explanation
PASS config tree no match
PASS ks default on
PASS ks per-mod off
PASS ks other mod unaffected
PASS ks global off
PASS gauge fmt (node)
PASS claude plugin validate
PASS claude plugin test (3 pass)
SELFTEST PASS
```
Not verified: live drawing in an interactive session (bands/panes). The engine's `claude plugin test` mounts the gauge band on the terminal surface, with the engine stubbed; the three panes were validated, not mounted.

## Install
```
/plugin install nvaex-ui-cockpit --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-ui-cockpit@novaexopia`. Swap out: `claude plugin disable nvaex-ui-cockpit@novaexopia`.
