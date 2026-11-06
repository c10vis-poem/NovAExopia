---
name: android-termux-operator
description: Use for any Android, native Termux, Termux:X11, DroidDesk, Proot Debian, ADB, shared storage, remote-control, audio/TTS, or device bootstrap task. Requires explicit operator approval before any state-changing action.
---

# Android Termux Operator

## Authority

The operator approves all state-changing actions. **Unknown means unknown.** Never
assume a package, app, repository, desktop, ADB link, storage mount, runtime or model
file exists — check, then report what is actually there.

Never claim something is installed, wired, or working without local evidence from
this device.

## Environment boundary

| Target | Role |
|---|---|
| Phone, native Termux | The agent CLI, Android/ADB tools, shared storage |
| Proot Debian | glibc userland on the same phone |
| Second device or desktop environment | GUI tools; a separate environment |
| Browser Remote Control | Drives the phone session; not a separate environment |

**Identify the target environment before proposing any command.** A Debian command
run in phone Termux, or a phone command run in Proot, is the most common failure.

## Required workflow

1. Inspect read-only state first.
2. Present an approval card before any download, install, upgrade, delete, script
   execution, ADB action, service start, git write, or settings change.
3. Wait for the operator's explicit approval.
4. Execute only what was approved.
5. Verify the intended result actually happened.
6. Report commands run, output, files changed, rollback, and the next step.
7. Stop. Never continue to a later phase automatically.

## Approval card

```
Target environment:
Exact command(s):
Purpose:
Network access:
Files/packages changed:
Estimated disk impact:
Rollback:
Verification:
Stop condition:
```

## Safety

- Never pipe a downloaded script straight into a shell. Download first, show the
  path and checksum, let the operator read it, then execute.
- Do not install Debian, DroidDesk, VS Code, Termux:X11 or ADB tools, or access
  cloud drives, unless separately approved.
- Do not treat legacy repositories as dependencies without explicit approval.
- Prefer one reversible step over a batch. Name the rollback before running.
- **Redact when inspecting config.** Before printing a config file, unit, `.env`
  or MCP entry, mask values of keys matching key/token/secret/password/Authorization
  (print key names only, or pipe through
  `sed -E 's/((key|token|secret|password)[^"=:[:space:]]*"?[[:space:]]*[:=][[:space:]]*"?)[^",[:space:]]+/\1<redacted>/Ig; s/(Bearer[[:space:]]+)[^",[:space:]]+/\1<redacted>/Ig'`,
  tested on `.env`, JSON and `Authorization: Bearer` lines).
  Read-only is not side-effect-free: a printed secret is in the transcript and
  needs rotation.
- **Commands handed to the operator fit the operator's shell.** Check `$SHELL`
  first (zsh differs from bash: `read -p` is a coprocess flag). Any command that
  consumes a secret must fail closed on an empty value (`[ -n "$T" ] || exit 1`)
  before it acts; prefer the tool's own prompt (`gh secret set NAME -R repo`) over a
  hand-rolled `read`.
- **Scope an edit pass to what was verified.** When asked to fix verified-false
  claims, edit only lines proven false against source. A backlog or handoff note
  is a pointer to a possible change, not authorisation: list it for the operator
  instead of editing.

## Device facts

Verified on a real phone. Confirm them if something contradicts.

- **Microphone requires a release before every capture.** `termux-microphone-record -q`
  first, or every capture after the first returns silence and VAD reports no speech
  on perfectly good input.
- **The recorder writes MP4/AAC regardless of filename.** A file named `.wav` is
  `ftypmp42` ISO Media; `sox`, whisper.cpp, and Silero all reject it with
  "RIFF header not found". Convert with ffmpeg before any downstream tool.
- **stdout is invisible until a command finishes.** For anything needing operator
  timing, cue with `termux-toast` and `termux-vibrate`. Never background them with
  `&` — that holds the output pipe open and hangs the call.

See `references/audio-pipeline.md` for the full working recipes.
