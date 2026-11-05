#!/usr/bin/env bash
# resume-gate.sh: blocks non-Read tools until RESUME is Read; records opening reads; re-checks the hash per agent
# and per path (obs 0044, 0051); never blocks a Read; dates RESUME.
S=$(cd "$(dirname "$0")/../../scripts" && pwd); T=$(mktemp -d); trap 'rm -rf "$T"' EXIT; export HOME=$T
st=$T/.claude/state; mkdir -p "$st"; repo=$T/repo; git init -q "$repo"
pass=0; fail=0
ok(){ if [ "$1" = "$2" ]; then pass=$((pass+1)); echo "PASS $3"; else fail=$((fail+1)); echo "FAIL $3 (got $1 want $2)"; fi; }
G(){ jq -n --arg t "$1" --arg f "$2" --arg c "$repo" '{session_id:"S",cwd:$c,tool_name:$t,tool_input:{file_path:$f}}' | bash "$S/resume-gate.sh" >"$T/out" 2>"$T/err"; echo $?; }
# A <agent> <cwd> <tool> [file]: one tool call from a subagent
A(){ jq -n --arg a "$1" --arg c "$2" --arg t "$3" --arg f "${4:-}" '{session_id:"M",agent_id:$a,cwd:$c,tool_name:$t,tool_input:{file_path:$f}}' | bash "$S/resume-gate.sh" >/dev/null 2>&1; echo $?; }
B(){ jq -n --arg c "$1" --arg t "$2" --arg f "${3:-}" '{session_id:"M",cwd:$c,tool_name:$t,tool_input:{file_path:$f}}' | bash "$S/resume-gate.sh" >/dev/null 2>&1; echo $?; }
printf '# RESUME\n\n**Last updated: 2026-01-01**\n\n## START HERE\n1. a\n' > "$repo/RESUME.md"; printf '# rules\n' > "$repo/AGENTS.md"
ok "$(G Bash "")" 2 "blocked before RESUME is read"
ok "$(G Read "$repo/AGENTS.md")" 0 "Read is never blocked, even before RESUME"
ok "$(G Bash "")" 2 "still blocked for other tools after that"
ok "$(G Read "$repo/RESUME.md")" 0 "Read RESUME -> allowed"
ok "$([ -f "$st/resume-S.ok" ] && [ -f "$st/resume-S.snap.md" ] && echo y)" y "hash + snapshot written"
ok "$(cat "$st/resume-date-S")" 2026-01-01 "RESUME date recorded"
ok "$(grep -c 'days ago' "$T/out")" 1 "stale RESUME reported as context"
ok "$(G Read "$repo/AGENTS.md")" 0 "after RESUME: tools run"
ok "$(grep -c '^read:AGENTS.md' "$st/opening-S.tsv")" 2 "opening ledger records both AGENTS.md reads"
# external change -> block once until re-read; re-read refreshes
echo "- 2. b" >> "$repo/RESUME.md"
ok "$(G Bash "")" 2 "RESUME changed on disk -> blocked"
ok "$(grep -c 'changed since this agent read it' "$T/err")" 1 "reason explains the drift"
ok "$(G Read "$repo/RESUME.md")" 0 "re-read allowed"
ok "$([ -f "$st/resume-S.snap.prev.md" ] && echo y)" y "old snapshot kept"
ok "$(G Bash "")" 0 "after re-read: allowed"
# this session wrote it (change log) -> no drift block
printf '%s\tEDIT\trepo:repo\t%s\n' "$(date '+%F %T')" "$repo/RESUME.md" >> "$st/changes-S.log"; echo "- 3. c" >> "$repo/RESUME.md"
ok "$(G Bash "")" 0 "own write recorded in change log -> no block"
# wrap-up mode -> no drift block
rm "$st/changes-S.log"; echo "- 4. d" >> "$repo/RESUME.md"; touch "$st/wrapup-S"
ok "$(G Bash "")" 0 "wrap-up mode -> no drift block"
# undated RESUME is reported
rm -f "$st"/resume-S* "$st"/advised-* "$st/wrapup-S"; printf '# RESUME\n## START HERE\n1. a\n' > "$repo/RESUME.md"
G Read "$repo/RESUME.md" >/dev/null; ok "$(grep -c 'carries no date' "$T/out")" 1 "undated RESUME reported"
# obs 0051: the loop. Main session on the vault RESUME, subagents in two other repos with their own RESUMEs.
export VAULT=$T/vault; mkdir -p "$VAULT"; printf '# vault RESUME 2026-11-05\n## START HERE\n1. v\n' > "$VAULT/RESUME.md"
ra=$T/ra; rb=$T/rb; git init -q "$ra"; git init -q "$rb"; echo '# A' > "$ra/RESUME.md"; echo '# B' > "$rb/RESUME.md"
ok "$(B "$T" Read "$VAULT/RESUME.md")" 0 "0051: main reads the vault RESUME"
ok "$(B "$T" Bash)" 0 "0051: main runs"
vh=$(cat "$st/resume-M.ok")
ok "$(A a1 "$ra" Bash)" 2 "0051: subagent a1 must read ITS repo's RESUME once"
ok "$(A a1 "$ra" Read "$ra/RESUME.md")" 0 "0051: a1 reads repo A RESUME"
ok "$(A a2 "$rb" Read "$rb/RESUME.md")" 0 "0051: a2 reads repo B RESUME"
ok "$(cat "$st/resume-M.ok")" "$vh" "0051: subagent reads leave the main agent's hash alone"
loops=0; for i in 1 2 3 4 5 6 7 8; do
  for r in "$(B "$T" Bash)" "$(A a1 "$ra" Bash)" "$(A a2 "$rb" Agent)" "$(B "$T" Agent)" "$(A a1 "$ra" SendMessage)"; do [ "$r" = 0 ] || loops=$((loops+1)); done
done
ok "$loops" 0 "0051: 40 interleaved calls across agents and repos, file unchanged: no block"
a=$(B "$ra" Bash); ok "$a" 2 "main moves into repo A: one block for that RESUME"
ok "$(B "$ra" Read "$ra/RESUME.md")" 0 "main reads repo A RESUME"
ok "$(cat "$st/resume-M.ok")" "$vh" "the session's own RESUME record stays the vault's"
ok "$(B "$ra" Bash)" 0 "main in repo A runs"; ok "$(B "$T" Bash)" 0 "main back on the vault: no block, same bytes"
touch "$VAULT/RESUME.md"; ok "$(B "$T" Bash)" 0 "mtime change alone is not drift"
echo "- 2. w" >> "$ra/RESUME.md"
ok "$(A a1 "$ra" Bash)" 2 "real change in repo A: a1 blocked"
ok "$(A a2 "$rb" Bash)" 0 "real change in repo A: a2 in repo B unaffected"
ok "$(B "$T" Bash)" 0 "real change in repo A: main on the vault unaffected"
ok "$(A a1 "$ra" Read "$S/resume-gate.sh")" 0 "drift: Read of anything still allowed (hook's own source)"
ok "$(A a1 "$ra" Read "$ra/RESUME.md")" 0 "drift: re-read"
ok "$(A a1 "$ra" Bash)" 0 "drift cleared after one re-read"
unset VAULT
echo "== $pass passed, $fail failed"; [ "$fail" -eq 0 ]
