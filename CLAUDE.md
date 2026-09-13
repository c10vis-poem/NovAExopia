# NovÆxopia — tools, harness, and engine layer

Canon name: **NovÆxopia**. Repo name: `novaexopia`. See `novae-xorpus/NAMING-CANON.md`.

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

## Operator Rule 0 — no action without explicit order

A skipped or unanswered question is NOT consent. State the concrete plan and
get an explicit go-ahead before any state-changing action, even a local and
easily reversible one.

## Operator Rule 1 — read this file and RESUME.md first

Before doing anything else in this repo, read this CLAUDE.md and RESUME.md.
Standing convention across the operator's repos for months — step one,
every session, no exceptions.

## Git workflow

PR required. No direct pushes to main. CI runs gitleaks + structure check.
Before every push, scan the diff for secrets/keys and refuse to push if any
are found. On green CI, auto-merge into `main` immediately — do not wait for
a manual merge step. Leave the branch in place after merge; do not delete it.
