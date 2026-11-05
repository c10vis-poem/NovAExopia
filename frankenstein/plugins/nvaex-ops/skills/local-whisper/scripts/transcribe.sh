#!/usr/bin/env bash
# Transcribe an audio/video file on this phone. Offline. Usage: transcribe.sh FILE [--check]
# Engine: Parakeet TDT 0.6B v3 (ggml q8) via parakeet-cli, a glibc build, so it runs inside proot-distro debian.
# Override paths with WHISPER_DIR, PARAKEET_MODEL, WHISPER_PROOT (distro name), WHISPER_THREADS.
set -u
DIR=${WHISPER_DIR:-$HOME/tools/whisper-parakeet}
MODEL=${PARAKEET_MODEL:-$HOME/models/parakeet/ggml-parakeet-tdt-0.6b-v3-q8_0.bin}
DISTRO=${WHISPER_PROOT:-debian}
THREADS=${WHISPER_THREADS:-4}
need() { echo "local-whisper: $1" >&2; exit 3; }
command -v ffmpeg >/dev/null || need "ffmpeg missing (pkg install ffmpeg is the operator's call)"
command -v proot-distro >/dev/null || need "proot-distro missing"
[ -x "$DIR/parakeet-cli" ] || need "$DIR/parakeet-cli missing (see the aesop-voice-pipeline setup_whisper_parakeet.sh)"
[ -s "$MODEL" ] || need "model $MODEL missing"
if [ "${1:-}" = "--check" ]; then echo "ready: engine=$DIR/parakeet-cli model=$MODEL distro=$DISTRO"; exit 0; fi
[ $# -eq 1 ] && [ -f "$1" ] || { echo "usage: transcribe.sh FILE | --check" >&2; exit 2; }
W=$(mktemp -d "${TMPDIR:-/tmp}/lw.XXXXXX") || exit 1; trap 'rm -rf "$W"' EXIT
ffmpeg -y -loglevel error -i "$1" -vn -ar 16000 -ac 1 -c:a pcm_s16le "$W/a.wav" || { echo "local-whisper: ffmpeg could not decode $1" >&2; exit 4; }
# -np: print only the transcript on stdout; progress and backend logs go to stderr
proot-distro login "$DISTRO" -- env LD_LIBRARY_PATH="$DIR" "$DIR/parakeet-cli" -np -t "$THREADS" -m "$MODEL" -f "$W/a.wav" 2>"$W/err"
rc=$?; [ $rc -eq 0 ] || { tail -5 "$W/err" >&2; exit $rc; }
