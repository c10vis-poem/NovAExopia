#!/usr/bin/env bash
# Rule 1, the operator's words: no actions, no reading, no tool use without explicit permission or direction.
# Replaces resume-gate. UserPromptSubmit decides, PreToolUse enforces.
#   A prompt starting with # (or the word "hashtag", for dictation) is a direction: opens the job.
#   An affirmation (okay, yes, go, override...) opens the job. Any other prompt closes it.
#   One opening covers the whole job, every tool and step, until the next non-opening prompt.
# Closed: only the opening reads (AGENTS, MEMORY, RESUME, HANDOFF, PENDING, MAP, CLAUDE, and paths those
# documents name), the task-observer session start, and asking the operator.
. "$(dirname "$(realpath "$0")")/lib/env.sh"
in=$(cat); sid=$(jq -r '.session_id // empty' <<<"$in") || exit 0; [ -n "$sid" ] || exit 0
ev=$(jq -r '.hook_event_name // ""' <<<"$in"); job="$ST/job-$sid"; open="$ST/opening-$sid.tsv"

if [ "$ev" = UserPromptSubmit ]; then
  p=$(jq -r '.prompt // ""' <<<"$in" | sed -E '/^[[:space:]]*$/d' | head -1 | sed -E 's/^[[:space:]]+//' | tr '[:upper:]' '[:lower:]')
  # the session-started marker other gates key off (was written by resume-gate)
  cwd=$(jq -r '.cwd // ""' <<<"$in"); top=$(git -C "${cwd:-$HOME}" rev-parse --show-toplevel 2>/dev/null)
  r="$top/RESUME.md"; [ -n "$top" ] && [ -f "$r" ] || r="${VAULT:-/nonexistent}/RESUME.md"
  [ -f "$ST/resume-$sid.ok" ] || { if [ -f "$r" ]; then sha256sum "$r" | cut -d" " -f1 > "$ST/resume-$sid.ok"; else : > "$ST/resume-$sid.ok"; fi; }
  case $p in
    \#*|hashtag*) echo direction > "$job" ;;
    *) if grep -qE "^(ok|okay|yes|yep|yup|yeah|go|go ahead|do it|override|approved)([[:space:][:punct:]]|$)" <<<"$p"; then echo affirmation > "$job"; else rm -f "$job"; fi ;;
  esac
  exit 0
fi

tool=$(jq -r '.tool_name // ""' <<<"$in")
f=$(jq -r '.tool_input.file_path // ""' <<<"$in"); f=${f/#\~/$HOME}
rf=; [ -n "$f" ] && rf=$(realpath "$f" 2>/dev/null)
isdoc() { case ${1##*/} in AGENTS.md|MEMORY.md|RESUME.md|HANDOFF.md|handoff.md|PENDING.md|MAP.md|CLAUDE.md) return 0 ;; esac; return 1; }
# the opening ledger the stop gate reports from: recorded whether or not the job is open
[ "$tool" = Read ] && [ -n "$rf" ] && isdoc "$rf" && printf 'read:%s\t%s\t%s\n' "${rf##*/}" "$rf" "$(date +%T)" >> "$open"
[ -f "$job" ] && exit 0

named() {   # is this path named in a document already read this session?
  local short=${1/#$HOME/\~} doc
  while IFS=$'\t' read -r _ doc _; do
    [ -f "$doc" ] || continue
    grep -qF -- "$1" "$doc" && return 0; grep -qF -- "$short" "$doc" && return 0
    case $1 in "${doc%/*}"/*) grep -qF -- "${1#"${doc%/*}"/}" "$doc" && return 0 ;; esac
  done < "$open"
  return 1
}
case $tool in
  AskUserQuestion|ToolSearch) exit 0 ;;
  Read) [ -n "$rf" ] && { isdoc "$rf" && exit 0; [ -f "$open" ] && named "$rf" && exit 0; } ;;
  Skill) [ "$(jq -r '.tool_input.skill // ""' <<<"$in")" = task-observer ] && exit 0 ;;
  Bash) grep -qE '^bash [^;&|]*session-start-scan\.sh [^;&|]*$' <<<"$(jq -r '.tool_input.command // ""' <<<"$in")" && exit 0 ;;
esac
echo "$(date +%T) HOLD direction-gate: $tool" >> "$ST/enforce-$sid.log"   # not a BLOCK line: a Rule 1 hold is not friction
echo "BLOCKED (direction-gate): Rule 1, no action without the operator's direction ($tool). Say what you would do and ask. The operator opens the job with okay or yes, or a message starting with #." >&2
exit 2
