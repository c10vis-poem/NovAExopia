#!/usr/bin/env bash
# Speak text on this phone. Usage: speak.sh [--engine auto|termux|espeak|wav FILE] TEXT...   or   echo TEXT | speak.sh
# termux: Android's own voice via termux-tts-speak (needs the Termux:API app). espeak: espeak-ng, to the speaker through play/ffplay if present.
# wav FILE: write a WAV with espeak-ng and do not play (used for tests and for handing audio to another tool).
set -u
eng=auto; out=""
while [ $# -gt 0 ]; do case "$1" in
  --engine) eng=$2; shift 2;;
  --out) out=$2; shift 2;;
  --) shift; break;;
  *) break;; esac; done
if [ $# -gt 0 ]; then text="$*"; else text=$(cat); fi
[ -n "$text" ] || { echo "speak: no text" >&2; exit 2; }
[ ${#text} -le 4000 ] || { echo "speak: text over 4000 characters; split it" >&2; exit 2; }
if [ -n "$out" ]; then
  command -v espeak-ng >/dev/null || { echo "speak: espeak-ng missing" >&2; exit 3; }
  espeak-ng -w "$out" -- "$text"; exit $?; fi
if [ "$eng" = auto ]; then
  if command -v termux-tts-speak >/dev/null; then eng=termux; elif command -v espeak-ng >/dev/null; then eng=espeak; else echo "speak: no engine (termux-tts-speak, espeak-ng)" >&2; exit 3; fi
fi
case "$eng" in
  termux) command -v termux-tts-speak >/dev/null || { echo "speak: termux-tts-speak missing" >&2; exit 3; }
          # Never background this: it holds the caller's stdout pipe open
          exec termux-tts-speak -- "$text";;
  espeak) command -v espeak-ng >/dev/null || { echo "speak: espeak-ng missing" >&2; exit 3; }
          exec espeak-ng -- "$text";;
  *) echo "speak: unknown engine $eng" >&2; exit 2;;
esac
