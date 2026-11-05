---
name: tts
description: Speak text aloud on this phone (Android voice, or espeak-ng as fallback). Use when the user asks to read something out loud or wants a spoken reply or alert.
---

# tts

Plain text-to-speech from what the phone already has. No daemon, no cloud, no plugin.

Order of preference (checked 2026-11-05: all three present):
1. `termux-tts-speak` (Android's voice, needs the Termux:API app).
2. `espeak-ng` (robotic, always works offline, can write a WAV).
3. If the agent has claw-mcp: `claw.device action=tts` (it calls `termux-tts-speak`).
For realtime voice conversations use the `aesop-voice-pipeline` skill instead (Kokoro voices, mic loop).

## Steps
1. `bash scripts/speak.sh "text to say"` (path relative to this skill). Or pipe text on stdin.
2. `--engine espeak` forces the fallback. `--out file.wav` writes audio with espeak-ng instead of playing it.
3. Exit 3 means no engine is installed: tell the operator, do not install.
4. Keep spoken text short (limit 4000 characters); strip code blocks, URLs and markdown before speaking.
5. Stopping speech: end the `termux-tts-speak` process; there is no queue to manage.
