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

## Operator Rule 1 — no action without an explicit prompt

A skipped or unanswered question is NOT consent. No action — reading,
searching, or anything else — without an explicit prompt or permitted
request. State-changing or not, it doesn't matter.

## Operator Rule 2 — read this file and RESUME.md first

Before doing anything else in this repo, read this CLAUDE.md and RESUME.md.
Standing convention across the operator's repos for months — step one,
every session, no exceptions.

## Git workflow

PR required. No direct pushes to main. CI runs gitleaks + structure check.
Before every push, scan the diff for secrets/keys and refuse to push if any
are found. On green CI, auto-merge into `main` immediately — do not wait for
a manual merge step. Leave the branch in place after merge; do not delete it.

The point of this workflow is that everything reaches `main` — a branch
that never gets a PR opened, or a PR that never gets merged, is a failure
of this rule, not a valid alternative to it. Don't let work sit stranded.
