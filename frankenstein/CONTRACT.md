# Frankenstein build contract (read before building any package)

Source spec: `frankenstein_package_and_mcp_architecture_blueprint (1).md` (business Drive id `1_Xzf9FMB0QZWql0Q1_Y5TuAUL8Q0RL0w`; device copy `~/storage/shared/Download/Frankenstein/`). This contract is how every package is laid out so they are **hot-swappable** and all live in **one place, each in its own folder**.

## Where everything lives
```
NovAExopia/frankenstein/
  CONTRACT.md                 (this file)
  shared/killswitch.sh        (one kill switch every hook sources)
  plugins/<package>/          (one Claude Code plugin per package)
  mcp/<server>/               (one MCP server per folder)
  marketplace.fragment.json   (entries the root .claude-plugin/marketplace.json includes)
```
Packages: `plugins/nvaex-jev-core`, `plugins/nvaex-memory`, `plugins/nvaex-wiki-admin`, `plugins/nvaex-rea-forge`, `plugins/nvaex-burn`, `plugins/nvaex-ui-cockpit`. Servers: `mcp/claw-mcp`, `mcp/dumbass-memory-mcp`. `jev-rea-mcp` lives inside its package at `plugins/nvaex-jev-core/mcp/jev-rea-mcp` and installs with it.

## Hot-swap rules (every package)
1. **Self-contained.** Everything the package needs is inside its folder. Paths use `${CLAUDE_PLUGIN_ROOT}`. No package reads another package's files; shared code is only `frankenstein/shared/`, vendored into the package at build time by `bin/vendor-shared.sh` if needed.
2. **Standard plugin shape:** `.claude-plugin/plugin.json` (name, version, description, author "The Builder", license), `skills/<name>/SKILL.md`, optional `agents/`, `commands/`, `hooks/hooks.json`, `scripts/`, `README.md`, `tests/selftest.sh`.
3. **Swap = enable/disable.** `claude plugin enable|disable <package>@novaexopia` swaps it in or out; no other step. A package must work with any subset of the others disabled.
4. **One hook entry per lifecycle event per package**, every hook command first runs `killswitch.sh <package> <hook-name>` and exits 0 if `~/.nvaex-hooks-off` exists, or `~/.claude/state/off/<package>` or `~/.claude/state/off/<package>.<hook-name>` exists. No hook blocks by default; blocking hooks must name their override and revoke in the block message (Fable RULES.md guarantee 2). Hooks fail **closed only where the spec says so**; otherwise fail open and log.
5. **Custom first.** Source plugins are parts donors: copy only the files the spec names, strip media, demos, lockfiles, telemetry, auto-commits and network calls. Record every copied file and its origin in `SOURCES.md` inside the package (path, original plugin, version, license). Keep upstream LICENSE files for anything copied.
6. **Local-first.** Runs on this phone (Termux, Android arm64, no glibc, no root). No Docker, no daemons left running, no network unless the spec requires it. Python stdlib or Node built-ins first.
7. **Measured.** `tests/selftest.sh` exits 0 only when the package's core behaviour works on the device; record its output in the package README under "Tested on device".
8. **Never** write into the vault (`~/storage/shared/Documents/NovAExorpus`), `~/.claude/settings*.json`, or any repo other than this worktree. No installs, no pushes, no commits (the lead commits).

## Where the parts are on this phone
- Synced plugins: `~/.claude/plugins/synced/*/*/` (find by `.claude-plugin/plugin.json` `name`).
- Local plugins: `~/local-plugins/plugins/<name>/`; plugin cache: `~/.claude/plugins/cache/`.
- Repos: `~/repos/` (e.g. `NovA-code-review-graph`, `NvAEx-cf`, greedy-crane in `~/repos/.review/NovAExorpus-fable/plugins/greedy-crane/`).
- If a named part is not on the phone, do not invent it: list it in `SOURCES.md` under "Missing" and build the rest.
