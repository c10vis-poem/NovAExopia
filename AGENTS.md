# NovÆxopia — tools, harness, and engine layer

Canon name: **NovÆxopia**. Repo name: `NovAExopia`. See `NovAExorpus/NAMING-CANON.md`.

## What this is

The action surface of the Æsop-Xi stack — what the agent (NovÆxenti) can
actually do. Contains inference engine configs, model weight management,
runtime definitions, and tool-skill wiring. Supersedes the earlier "Omni Claw"
/ "NovA-Claw" / "NovÆcopia" naming.

## Stack position

```
Æsop-Xi          infrastructure (MCPs, hooks, memory, routing, protocols)
  └─ NovÆxenti   agent logic — executor + query cores
       └─ NovÆxopia   tools, harness, engine (this repo)
            ├─ Æsc         terminal daemon
            └─ Æyre        voice / vision daemon
```

## Conventions

- `daemons/` — shell daemon and media daemon lifecycle configs, IPC contracts.
- `runtimes/` — how a model is loaded and served (llama.cpp, QAIRT, ONNX, etc.).
- `tool-skills/` — tool/skill wiring per inference backend (was `engines/`).
- Weight manifests in `weights/` — model metadata, quantization specs, device
  compatibility. Actual weight files are NOT stored in git.
- `config/` holds cross-cutting settings (temperature defaults, token limits,
  routing rules).
- `manifest.jsonl` is the machine-readable index.
- `.claude-plugin/marketplace.json` is the `novaexopia` Claude Code plugin marketplace. Entries point at each plugin's own repository (`url` or `git-subdir` sources); no plugin code is stored here. Entries are generated with `~/local-plugins/make-entries.sh` on the operator's phone.

## Operator Rule 1 — no action without an explicit prompt

A skipped or unanswered question is NOT consent. No action — reading,
searching, or anything else — without an explicit prompt or permitted
request. State-changing or not, it doesn't matter.

## Operator Rule 2 — read this file and RESUME.md first

Before doing anything else in this repo, read this AGENTS.md and RESUME.md.
Standing convention across the operator's repos for months — step one,
every session, no exceptions.

## Git workflow

PR required. No direct pushes to main. CI runs gitleaks + structure check.
Before every push, scan the diff for secrets/keys and refuse to push if any
are found. On green CI, auto-merge into `main` immediately — do not wait for
a manual merge step. Auto-merge and auto-delete are set together while CI runs; GitHub deletes the
branch on merge (operator, 2026-11-10).

The point of this workflow is that everything reaches `main` — a branch
that never gets a PR opened, or a PR that never gets merged, is a failure
of this rule, not a valid alternative to it. Don't let work sit stranded.

## Memory (operator, 2026-10-23 and 2026-11-12)

OmniRoute, mem0, Terrestrial Brain and Reasoning Bank are dropped (Aesop-Xi AGENTS.md "Runtime memory stack:
DROPPED"): do not set them up, route through them or test them. Memory for every agent in this repo:
- **Project memory:** the `nvaex-memory` plugin (`plugins/nvaex-memory/`, MCP server `dumbass-memory`): frozen
  claims, task state and the session-start snapshot. It is on and used every session and is never turned off.
- **Repo files:** MEMORY.md, RESUME.md, PENDING.md and HANDOFF.md at the repo root.
- **Across projects:** NvAEx-Recaps `memory/` (`general.md`, `active/<project>.md`) and `handoff/<date>/`.
- **Shared state:** the vault `c10vis-poem/NovAExorpus` (`AGENTS.md` "Start here", `RESUME.md`, `PENDING.md`).

`tools/bootstrap.sh` calls `~/repos/aesop-xi/tools/bootstrap.sh`, a path that does not exist on the phone (the
clone is `~/repos/Aesop-Xi`), so it only prints a warning. Kept until the owner decides on it (PENDING.md).

## What loads in this repo, for every agent (operator, 2026-11-10)
This file is the authority. `CLAUDE.md` only points here. Launch from the repo root (or `crane`).
- **Plugins** live at `plugins/<name>/` (two folders deep): jev-core, memory, rea-forge, burn, ui-cockpit, claw-mcp,
  wiki-admin (the old wiki package; greedy-crane in NovAExorpus is the wiki admin). Marketplace `novaexopia` = this repo.
- **Rules and hooks:** the `aesops-enforcements` plugin lives in Aesop-Xi (`plugins/aesops-enforcements/`, marketplace
  `aesop-xi`), with its RULES.md. Every repo's settings and the user settings enable it from there.
- **Claude Code:** `.claude/settings.json` enables every plugin above, `aesops-enforcements@aesop-xi` and
  `greedy-crane@nvaex-vault`, sets the default agent (`"agent": "greedy-crane:wiki-admin"`; `claude --agent <name>`
  picks another), and turns off the root `.mcp.json` copies of the plugins' MCP servers (`disabledMcpjsonServers`), so
  Claude uses the plugins' own copies.
- **Every other agent (AGY, any MCP client):** `.mcp.json` starts the same six servers (claw, chrome-devtools,
  jev-rea-mcp, dumbass-memory, rea-mcp, burn-mcp) by repo-relative path; `.agents/plugins.json` registers `plugins/`.
- **Launchers:** `~/bin/crane` = greedy-crane, this repo as root, the vault, Aesop-Xi and shared storage attached.
  One launcher per agent (copy it, change `--agent`).
- Shared plugin tools: `tools/plugin-shared/`. Plugin design docs: `docs/plugins/`.
