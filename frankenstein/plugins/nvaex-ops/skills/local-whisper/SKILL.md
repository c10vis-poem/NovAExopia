---
name: local-whisper
description: Transcribe an audio or video file to text on this phone, offline, with the on-device Parakeet speech-to-text. Use when the user hands over a recording, voice note or video and wants the words.
---

# local-whisper

Speech-to-text that runs on this phone only. Nothing is uploaded and no MCP server is involved.

What the phone really has (checked 2026-11-05): `~/tools/whisper-parakeet/parakeet-cli` plus the model `~/models/parakeet/ggml-parakeet-tdt-0.6b-v3-q8_0.bin`. The binary is a glibc build, so it only runs inside `proot-distro login debian`; the script handles that. The same folder holds `whisper-cli`, but no Whisper model file is on the phone, so Parakeet is the engine. `ffmpeg` converts any input to 16 kHz mono.

## Steps
1. Check: `bash scripts/transcribe.sh --check` (path relative to this skill). It prints `ready` or says exactly what is missing and exits 3. If it exits 3, stop and tell the operator; do not install anything.
2. Transcribe: `bash scripts/transcribe.sh /path/to/file.m4a` prints the text on stdout.
3. Long files: Parakeet has no 10 second ceiling (the older Moonshine engine does). A minute of audio takes a few seconds.
4. Write the transcript where the user asked; keep the original file untouched.

## Limits
- English quality is proven; other languages are untested here.
- Subtitles with timestamps are not produced; the script returns plain text.
- Live microphone dictation is a different job: see the `aesop-voice-pipeline` skill and `~/bin/vv`.
