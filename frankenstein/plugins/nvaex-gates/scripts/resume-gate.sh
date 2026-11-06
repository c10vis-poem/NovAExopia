#!/usr/bin/env bash
# PreToolUse (all tools): rule 1, Read RESUME.md before tools run (the one at the current repo's root,
# else the vault's). Fixed for obs 0051:
#   - each agent keeps its own record per RESUME path: state/resume-seen-<sid>/<agent>/<hash of path>
#     holds the content hash of what that agent Read. Subagents and other repos never share a slot.
#   - drift = content hash differs from what THIS agent Read of THIS file. Same bytes never block.
#   - a Read is never blocked, whatever the state, so the way out of a block is always open.
# Blocks a non-Read call when this agent has not Read that file, or the file changed since it did and
# this session did not write it (change log) and is not in wrap-up (obs 0044). Also:
#   - opening ledger: Reads of AGENTS.md, PENDING.md, MEMORY.md, WRAP-UP.md, RESUME.md, CLAUDE.md go to
#     state/opening-<sid>.tsv (the Stop gate reports which opening steps are missing);
#   - the main agent's Read also keeps the session files other gates use: resume-<sid>.ok (hash),
#     .snap.md (START HERE items), .path, resume-date-<sid>. The old snapshot stays as .snap.prev.md;
#   - date check: missing, future, or older than AESOP_RESUME_MAX_AGE_DAYS (14) is reported, once.
. "$(dirname "$(realpath "$0")")/lib/env.sh"
in=$(cat); sid=$(jq -r '.session_id // empty' <<<"$in") || exit 0; [ -n "$sid" ] || exit 0
cwd=$(jq -r '.cwd // ""' <<<"$in"); tool=$(jq -r '.tool_name // ""' <<<"$in")
agent=$(jq -r '.agent_id // "main"' <<<"$in"); agent=${agent//[^A-Za-z0-9_-]/_}
f=$(jq -r '.tool_input.file_path // ""' <<<"$in"); f=${f/#\~/$HOME}
ok="$ST/resume-$sid.ok"; snap="${ok%.ok}.snap.md"; open="$ST/opening-$sid.tsv"; dir="$ST/resume-seen-$sid/$agent"
seen() { echo "$dir/$(sha256sum <<<"$1" | cut -c1-16)"; }
hash() { sha256sum "$1" | cut -d" " -f1; }

top=$(git -C "${cwd:-$HOME}" rev-parse --show-toplevel 2>/dev/null)
r="$top/RESUME.md"; [ -n "$top" ] && [ -f "$r" ] || r="${VAULT:-/nonexistent}/RESUME.md"
if [ -f "$r" ]; then r=$(realpath "$r"); else r=; fi

date_notice() {   # context line about RESUME's own date, once per session
  local d=$1 max=${AESOP_RESUME_MAX_AGE_DAYS:-14} age
  if [ -z "$d" ]; then echo "RESUME.md ($rf) carries no date in its first 40 lines; treat its START HERE list as unverified and say so to the operator."; return; fi
  age=$(( ( $(date +%s) - $(date -d "$d" +%s 2>/dev/null || date +%s) ) / 86400 ))
  [ "$age" -lt 0 ] && { echo "RESUME.md is dated $d, in the future; the file may be a conflict copy. Tell the operator before acting on it."; return; }
  [ "$age" -gt "$max" ] && echo "RESUME.md is dated $d ($age days ago, limit $max). Its START HERE list may be stale: confirm each item with the operator before working on it."
}

if [ "$tool" = Read ]; then
  rf=; [ -n "$f" ] && rf=$(realpath "$f" 2>/dev/null)
  case ${rf##*/} in AGENTS.md|PENDING.md|MEMORY.md|WRAP-UP.md|RESUME.md|CLAUDE.md) printf 'read:%s\t%s\t%s\n' "${rf##*/}" "$rf" "$(date +%T)" >> "$open" ;; esac
  [ "${rf##*/}" = RESUME.md ] && [ -f "$rf" ] || exit 0
  mkdir -p "$dir"; hash "$rf" > "$(seen "$rf")"
  # session files: main agent only, and only for the file the session opened with
  [ "$agent" = main ] && [ -n "$r" ] && [ "$rf" = "$r" ] || exit 0
  [ ! -f "$ST/resume-$sid.path" ] || [ "$(cat "$ST/resume-$sid.path")" = "$rf" ] || exit 0
  first=; [ -f "$ok" ] || first=1
  [ -f "$snap" ] && cp "$snap" "${ok%.ok}.snap.prev.md"
  hash "$rf" > "$ok"; cp "$rf" "$snap"; echo "$rf" > "$ST/resume-$sid.path"; resume_date "$rf" > "$ST/resume-date-$sid"
  [ -n "$first" ] || { echo "$(date +%T) RESUME re-read" >> "$ST/enforce-$sid.log"; exit 0; }
  n=$(date_notice "$(cat "$ST/resume-date-$sid")")
  [ -n "$n" ] && jq -n --arg c "$n" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'
  exit 0
fi

[ -n "$r" ] || { degrade resume "resume-gate: no RESUME.md reachable from ${cwd:-?} (no repo copy, VAULT='${VAULT:-none}')"; exit 0; }
s=$(seen "$r")
if [ ! -f "$s" ]; then
  echo "$(date +%T) BLOCK resume-gate: $tool before RESUME ($agent)" >> "$ST/enforce-$sid.log"
  echo "BLOCKED (resume-gate): Read $r first, then follow it." >&2; exit 2
fi
[ "$(hash "$r")" = "$(cat "$s")" ] && exit 0
[ -f "$ST/wrapup-$sid" ] && exit 0
grep -qF -- "$r" "$ST/changes-$sid.log" 2>/dev/null && exit 0
grep -qF -- "$r" "$ST/resume-written-$sid" 2>/dev/null && exit 0
echo "$(date +%T) BLOCK resume-gate: RESUME changed on disk ($agent)" >> "$ST/enforce-$sid.log"
echo "BLOCKED (resume-gate): $r changed since this agent read it (another session or device rewrote it). Read it again, then follow the new START HERE list; items you already proposed stay recorded." >&2; exit 2
