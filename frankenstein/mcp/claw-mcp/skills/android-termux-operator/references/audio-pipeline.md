# Audio pipeline in native Termux

Load this only when working on recording, transcription, or speech output. These were verified on a real Android phone; confirm them on yours.

## Recording

Two non-obvious failures, both of which look like "the microphone is broken":

1. **The recorder does not release the mic.** Without `-q` first, every capture
   after the first returns near-silence (amplitude ~0.001 instead of ~0.3). VAD
   then correctly reports NO SPEECH, which reads as a broken VAD.
2. **The file is MP4/AAC no matter what you name it.** `-f out.wav` still produces
   `ftypmp42` ISO Media. `sox` and whisper.cpp reject it: "RIFF header not found".

Working sequence:

```bash
termux-microphone-record -q >/dev/null 2>&1        # mandatory release
termux-microphone-record -f rec.m4a -l 8 -r 16000 -c 1 -b 64
ffmpeg -y -i rec.m4a -ar 16000 -ac 1 -acodec pcm_s16le rec.wav
```

`-r 16000` works fine *after* a release. Native 16 kHz beats capturing at the 8 kHz default and upsampling.

Verify a capture actually contains speech before blaming anything downstream:

```bash
sox rec.wav -n stat 2>&1 | grep "Maximum amplitude"
```

Real speech reads roughly 0.2–0.6. Anything under 0.01 is silence.

## Cueing the speaker

stdout does not appear until the command completes, so a printed "TALK NOW" is never seen in time. Use:

```bash
termux-toast -b red -c white -g middle "TALK NOW - 3 SEC"
termux-vibrate -d 800
```

Do **not** background these with `&`. A backgrounded job inherits stdout and holds the pipe open, which hangs the calling tool until it times out.

## Transcription

Silero VAD at 16 kHz requires exactly 512-sample frames; pad the final short chunk or it misbehaves. Models that need glibc run in `proot-distro login debian`; the mic only works from Termux, so each utterance round-trips Termux to proot and back.

## Speech output

A local sherpa-onnx Kokoro voice (model.onnx, voices.bin, tokens.txt, espeak-ng-data, dict, lexicons) worked: synthesize to a wav in `$TMPDIR` and play it with `play`. No Android dependency. Write wavs with the stdlib `wave` module if `soundfile` is missing.

Android TTS engines may be a dead end: on the test phone `com.google.android.tts` and the vendor engine hung (exit 124, no audio), so `termux-tts-speak` was not usable. Audio output itself was fine.

Strip markdown before speaking, or headings and paths are pronounced as "hashtag hashtag" and "slash".

## Voice input

`termux-speech-to-text` works and is one press, but it **truncates every capture after roughly 8–12 words**. Android owns that endpointing and the wrapper exposes no timeout. It has no press-to-stop: it is one blocking call. Do not fix the truncation by calling it again and stitching: it needs 1–2 s to initialise, longer than the pause between sentences.

An offline chain (record, VAD, STT) has no endpointing: slower, but complete. Prefer it for long speech.

`RecognitionListener#onError(7)` in logcat is `ERROR_NO_MATCH`: the recognizer ran and heard nothing. It does not mean anything is broken.

### The keyboard mic button does not work in Termux

Termux reports `inputType = TYPE_NULL`, so Gboard disables voice typing. `enforce-char-based-input = true` switches to a visible-password type, and keyboards suppress voice input there too, so the mic stays dead and suggestions are lost. Do not retry.

### Getting speech into a TUI prompt

The way to inject text into a running TUI prompt is tmux `send-keys -l` (literal, no Enter, so it arrives editable). The TUI must be **started** inside tmux: a running process's terminal cannot be moved in afterwards.

A function key bound to a mic script can reach an editor instead when the session is not in tmux (nvim maps `<F1>` to `:help`), which looks like a hang. Map those keys to `<Nop>` in the editor.

tmux is not a substitute for `termux-wake-lock`. tmux keeps the session alive when the terminal goes away; wake-lock keeps the CPU running with the screen off.

### Shebangs

**Termux has no `/usr/bin/env`.** A `#!/usr/bin/env python3` shebang fails silently when the file is executed directly while working fine under `python3 file`. Use `#!/data/data/com.termux/files/usr/bin/env python3`.
