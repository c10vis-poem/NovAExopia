#!/usr/bin/env bash
# Rule 12: read the source first, once per session per asset. Two modes from the operator's prompt:
# deep (every clean MD, or the full read) and brief (chunk.jsonl, or the current manifest + a pointed file).
S=$(cd "$(dirname "$0")/../../scripts" && pwd); B=$(cd "$S/../bin" && pwd); T=$(mktemp -d)
export HOME=$T STATE_DIR=$T/st REPOS_DIR=$T/repos VAULT=$T/vault
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
mkdir -p "$T/bin"; printf '#!/bin/sh\necho PUBLIC\n' > "$T/bin/gh"; chmod +x "$T/bin/gh"; export PATH="$T/bin:$PATH"
pass=0; fail=0
ok(){ if [ "$1" = "$2" ]; then pass=$((pass+1)); echo "PASS $3"; else fail=$((fail+1)); echo "FAIL $3 (got $1 want $2)"; fi; }
R=$REPOS_DIR/jevtool; mkdir -p "$R/docs" "$VAULT/Vendor-Registries/acme"
echo "# Jev" > "$R/README.md"; echo "# Install" > "$R/INSTALL.md"; echo "# Guide" > "$R/docs/guide.md"; echo x > "$R/main.py"
git -C "$R" init -q && git -C "$R" add . && git -C "$R" commit -q -m init
# session-scoped helpers: E <sid> <event> <tool> <input> [cwd]; ST <sid> <msg> [active]; P <sid> <prompt>
E(){ jq -cn --arg s "$1" --arg e "$2" --arg t "$3" --argjson i "$4" --arg c "${5:-/}" '{session_id:$s,hook_event_name:$e,tool_name:$t,tool_input:$i,cwd:$c}' | bash "$S/source-gate.sh" 2>"$T/err"; echo $?; }
ST(){ jq -cn --arg s "$1" --arg m "$2" --argjson a "${3:-false}" '{session_id:$s,hook_event_name:"Stop",last_assistant_message:$m,stop_hook_active:$a}' | bash "$S/source-gate.sh" 2>"$T/err"; echo $?; }
P(){ jq -cn --arg s "$1" --arg p "$2" '{session_id:$s,hook_event_name:"UserPromptSubmit",prompt:$p}' | bash "$S/source-gate.sh" >/dev/null 2>&1; }
RD(){ E "$1" PostToolUse Read "$(jq -cn --arg f "$2" '{file_path:$f}')" >/dev/null; }
BA(){ E "$1" PostToolUse Bash "$(jq -cn --arg c "$2" '{command:$c}')" "${3:-/}" >/dev/null; }
INST='{"command":"pip install -e ."}'
P S1 "what flags does jevtool have?"

# S1: full read (no clean MD yet)
ok "$(E S1 PreToolUse Bash "$INST" "$R")" 2 "install in an unread repo -> block"
ok "$(command grep -c 'still unread' "$T/err")" 1 "reason lists the unread docs"
ok "$(ST S1 "jevtool supports a --fast flag.")" 2 "answer about an unread asset's flags -> block"
ok "$(ST S1 "jevtool supports a --fast flag." true)" 0 "stop_hook_active -> pass"
ok "$(ST S1 "The weather is nice.")" 0 "answer not about an asset -> pass"
ok "$(ST S1 "Read as: launch with jevtool attached, then set up the flags.")" 0 "the operator's words restated -> not a claim"
ok "$(ST S1 "jevtool is attached. The settings file has flags.")" 0 "name and feature word in different sentences -> pass"
P S6 "how is the weather"
ok "$(ST S6 "jevtool supports a --fast flag.")" 0 "operator did not ask about jevtool -> no read required"
RD S1 "$R/README.md"; RD S1 "$R/INSTALL.md"
ok "$(E S1 PreToolUse Bash "$INST" "$R")" 2 "docs read but no tree, one doc missing -> block"
BA S1 "find $R -not -path '*/.git/*'"; RD S1 "$R/docs/guide.md"
ok "$(E S1 PreToolUse Bash "$INST" "$R")" 0 "tree + every doc read -> install passes"
ok "$(ST S1 "jevtool supports a --fast flag.")" 0 "answer after the full read -> pass"
ok "$(E S1 PreToolUse Bash '{"command":"git clone https://github.com/x/newthing"}')" 2 "clone with no docs fetched -> block"
E S1 PostToolUse WebFetch '{"url":"https://github.com/x/newthing#readme"}' >/dev/null
ok "$(E S1 PreToolUse Bash '{"command":"git clone https://github.com/x/newthing"}')" 0 "clone after its README was fetched -> pass"
ok "$(E S1 PreToolUse Bash '{"command":"ls -la"}')" 0 "not an install -> pass"
P S2 "what does jevtool support?"
ok "$(AESOP_AUTOMATED=1 bash -c "jq -cn '{session_id:\"S2\",hook_event_name:\"Stop\",last_assistant_message:\"jevtool supports x\"}' | bash '$S/source-gate.sh'" 2>/dev/null; echo $?)" 0 "automated run: highlight, not a block"
ok "$(command grep -c 'HIGHLIGHT (source-gate' "$STATE_DIR/hooks.log")" 1 "automated highlight logged"

# manifests
bash "$B/asset-manifest" "$R" >/dev/null; I=$VAULT/Assets-Index/jevtool
ok "$([ -f "$I/manifest.jsonl" ] && echo yes)" yes "manifest written to Assets-Index/<repo>/"
ok "$([ -f "$I/POINTER.md" ] && echo yes)" yes "pointer written next to it"
ok "$(sed -n 1p "$I/manifest.jsonl" | jq -r .head)" "$(git -C "$R" rev-parse HEAD)" "manifest records HEAD"
ok "$(grep -c '"path":"docs/guide.md"' "$I/manifest.jsonl")" 1 "manifest lists each file"

# S3: brief via the manifest
P S3 "quick check: does jevtool have a fast flag?"
ok "$(ST S3 "jevtool supports a --fast flag.")" 2 "brief: nothing looked up -> block"
ok "$(command grep -c '(brief)' "$T/err")" 1 "brief reason names chunk.jsonl or the manifest"
RD S3 "$I/manifest.jsonl"
ok "$(ST S3 "jevtool supports a --fast flag.")" 2 "brief: manifest alone is not enough"
RD S3 "$R/docs/guide.md"
ok "$(ST S3 "jevtool supports a --fast flag.")" 0 "brief: manifest + a pointed file -> pass"
ok "$(E S3 PreToolUse Bash "$INST" "$R")" 2 "an install is always deep: a brief lookup is not enough"
echo y >> "$R/main.py"; git -C "$R" commit -qam change
P S5 "quick: is there a fast flag in jevtool?"; RD S5 "$I/manifest.jsonl"; RD S5 "$R/docs/guide.md"
ok "$(ST S5 "jevtool supports a --fast flag.")" 2 "repo moved past the manifest's HEAD -> manifest not current"

# S4: brief via chunk.jsonl, deep via clean MD
mkdir -p "$I/clean_md"; echo '{"id":1,"text":"fast flag"}' > "$I/chunk.jsonl"; echo "# A" > "$I/clean_md/a.md"; echo "# B" > "$I/clean_md/b.md"
P S4 "fact check: does jevtool have a fast flag?"
BA S4 "grep -i fast $I/chunk.jsonl"
ok "$(ST S4 "jevtool supports a --fast flag.")" 0 "brief: chunk.jsonl grep -> pass"
P S4 "give me a full breakdown of jevtool and compare it to the others"
ok "$(ST S4 "jevtool supports a --fast flag and these options.")" 2 "deep: chunk lookup not enough"
ok "$(command grep -c 'clean_md' "$T/err")" 1 "deep reason points at clean_md/"
RD S4 "$I/clean_md/a.md"
ok "$(ST S4 "jevtool supports a --fast flag and these options.")" 2 "deep: one clean MD of two -> block"
RD S4 "$I/clean_md/b.md"
ok "$(ST S4 "jevtool supports a --fast flag and these options.")" 0 "deep: every clean MD read -> pass"
ok "$(E S4 PreToolUse Bash "$INST" "$R")" 0 "install (deep) after every clean MD -> pass"

# records are the gate's, not the agent's
X(){ jq -cn --arg f "$1" '{tool_name:"Write",tool_input:{file_path:$f}}' | bash "$S/state-guard.sh" 2>/dev/null; echo $?; }
ok "$(X "$T/.claude/state/source-S4.tsv")" 2 "agent cannot write the read records"
ok "$(X "$T/.claude/state/source-mode-S4")" 2 "agent cannot write the mode"

# vendor folder and the public-vault guard
echo "# A" > "$VAULT/Vendor-Registries/acme/guide.md"; bash "$B/asset-manifest" "$VAULT/Vendor-Registries/acme" >/dev/null
ok "$([ -f "$VAULT/Vendor-Registries/acme/manifest.jsonl" ] && echo yes)" yes "vendor manifest sits next to the raw files"
printf '#!/bin/sh\necho PRIVATE\n' > "$T/bin/gh"; git -C "$R" remote add origin https://github.com/c/priv.git
ok "$(bash "$B/asset-manifest" "$R" >/dev/null 2>&1; echo $?)" 1 "private repo refused (the vault is public)"
echo "== $pass passed, $fail failed"; rm -rf "$T"; [ "$fail" -eq 0 ]
