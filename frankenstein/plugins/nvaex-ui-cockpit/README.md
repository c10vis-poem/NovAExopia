# nvaex-ui-cockpit

Nine small, independent UI mods for Claude Code in one hot-swappable package (Frankenstein set, package 6). Python stdlib and a TSX hooks module; no daemons, no network, no hooks that block.

| Mod | What you get | Command |
| --- | --- | --- |
| `plugins-panel` | Band above the prompt `Plugins: 8/47 active`; pane with each plugin's skills, agents, commands, hooks and listed-token footprint | `/plugins-panel` |
| `env-customizer-panel` | Pane with global / marketplace / repo overview and a profile picker (harness-scope profiles). Writes only `<repo>/.claude/harness-scope.json` | `/env`, `/env use NAME`, `/env clear` |
| `obsidian-config-tree` | Searchable tree of every enabled skill, agent, command, hook and script with a one-line plain-English explanation | `/config-tree [query]` |
| `context-window` | Pane listing what entered the conversation (messages, tool calls, tool results) grouped by kind and tool, with chars/4 token estimates. No limits, no usage bars | `/context-window` |
| `file-tree-panel` | Pane with the workspace file tree; click a folder to open or close it (noise dirs like `.git`, `node_modules` hidden) | `/files [/dir]` |
| `agent-configs-panel` | Pane with marketplaces, agent packages (installed plugins and their agents) and workflows (harness-scope profiles). Prev / Next cycle through workflows and packages, Apply selects a profile or enables/disables a package via the `claude` CLI | `/configs`, `/configs next\|prev\|apply` |
| `top-button-row` | Row of buttons (Plugins, Files, Configs, Env, Tree, Context, Jev, Cards) that each open that mod's pane. A mod that is switched off loses its button. The API has no screen-top slot; the row sits in the band above the prompt | none |
| `browser-cards` | When a browser-driving tool's result carries a choice, a card pops up with one button per option. Press an option to answer into the chat, or "Type a reply..." to drop down a prompt bar on the card whose text goes into the chat. Wire format a tool emits: a line `CHOICE: question \| a \| b`, or JSON `{"choice":{"question":"..","options":["a","b"]}}`. Browser tools are matched by name (`browser`, `chrome`, `playwright`, `claw`, `tinyfish`, `webview`, `puppeteer`, `cdp`) | `/cards`, `/cards clear` |
| `jev-panel` | Pane with the routing tier (from the `JEV route:` line `nvaex-jev-core` injects into the conversation), active decisions (`~/.nvaex/decisions.jsonl`, `<project>/.nvaex/decisions.jsonl`) and the last scorecard line (`~/.claude/state/nvaex-jev-core/scorecard.jsonl`). Each missing source is reported as "not found"; no dependency on `nvaex-jev-core` | `/jev` |

## Swap in / out
```
claude plugin enable  nvaex-ui-cockpit@novaexopia
claude plugin disable nvaex-ui-cockpit@novaexopia
```
Nothing else depends on it and it depends on nothing else. After enabling, `/reload-plugins` or restart.

Swap one mod without touching the others:
```
mkdir -p ~/.claude/state/off && touch ~/.claude/state/off/nvaex-ui-cockpit.context-window   # off
rm ~/.claude/state/off/nvaex-ui-cockpit.context-window                                       # back on
```
Mod names: `plugins-panel`, `env-customizer-panel`, `obsidian-config-tree`, `context-window`, `file-tree-panel`, `agent-configs-panel`, `top-button-row`, `browser-cards`, `jev-panel`. Whole package off: `touch ~/.claude/state/off/nvaex-ui-cockpit`. Everything off (all Frankenstein packages): `touch ~/.nvaex-hooks-off`.

## Hooks and kill switches
One hooks module (`hooks/register.tsx`), one `session.start` hook for the package (it runs each mod's init, failing open), plus per-mod `command.run` and `ui.render`. Each mod asks `scripts/killswitch.sh nvaex-ui-cockpit <mod>` (cached 2 s) before acting; when off it passes straight to the engine. Nothing blocks, so no override message is needed.

## Notes
- Layout: terminal bands and panes need the terminal surface; panes seat at 110+ columns (see `$.ui.open`), the commands print text when no pane is placed.
- `env-customizer-panel` never edits `~/.claude/settings*.json`. A profile takes effect when the harness-scope mod is installed and the next session starts.
- The usage gauge (context %, cache TTL, 5h/7d) was removed: the operator is building a custom usage display. `context-window` shows entrants only.

## Not built
No usage gauge (operator is building a custom usage display). `plugin-eval`, `plugin-improver`, `statusline-pro`, `claude-hud` were not found on the device (see SOURCES.md). `nvaex-jev-core` writes no routing-tier file today (its router only injects a context line); `jev-panel` reads that line from the conversation, so the tier shows only when the router ran this session.

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
PASS context rows (node)
PASS agentconfigs marketplace row
PASS agentconfigs package row (agents listed)
PASS agentconfigs workflow row
PASS agentconfigs marks current workflow
PASS settings.json untouched by agentconfigs
PASS added-mod logic (node)
PASS claude plugin validate
PASS claude plugin test (8 pass)
PASS one session.start entry
PASS usage gauge removed
PASS no settings writes in hooks
SELFTEST PASS
```
What the engine tests prove (`claude plugin test`, 8 pass): the mods load under the real hooks loader; each added command runs through its hook; each pane is mounted on the terminal surface and pressed/typed into by key (folder opens and lists its files; Prev/Next/Apply cycles and runs the exact `claude plugin disable` / `profiles.py use` argv; a browser-tool result raises a card, an option and a typed reply reach `prompt.submit` with the card's question; jev pane shows the route and decisions, and "not found" when files are absent; a switched-off mod loses its button; a button press opens that mod's pane). A mutation (dropping the question from the reply) made the cards test fail.

Not verified, needs the live phone: actual drawing and layout on the terminal (the test kit checks the tree, not the paint), the 110-column dock threshold, the real button/hotkey feel, whether `AbovePrompt` is acceptable as the top bar, `$.prompt.submit` from a card landing in a running turn, `tool.call` seeing real MCP browser results (the `text` field format), and `claw-mcp` actually emitting `CHOICE:` lines (it does not yet). Type-check with `tsc` was not run (no tsc on the device).

## Install
```
/plugin install nvaex-ui-cockpit --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein` then `claude plugin install nvaex-ui-cockpit@novaexopia`. Swap out: `claude plugin disable nvaex-ui-cockpit@novaexopia`.
