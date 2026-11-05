#!/usr/bin/env bash
# nvaex-ops selftest: structure, dangling-path checks, real script behaviour. No network.
set -u; export PYTHONDONTWRITEBYTECODE=1
P=$(cd "$(dirname "$0")/.." && pwd); W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
fail() { echo "SELFTEST FAIL: $*"; exit 1; }; n=0; chk() { n=$((n+1)); echo "ok  $*"; }
jq -e '.name=="nvaex-ops" and .license and .author.name' "$P/.claude-plugin/plugin.json" >/dev/null || fail plugin.json
[ ! -e "$P/hooks" ] && [ ! -e "$P/.mcp.json" ] || fail "package must have no hooks or MCP server"
chk "plugin.json valid; no hooks, no MCP server (nothing to kill-switch)"
vis=0
for f in "$P"/skills/*/SKILL.md; do
  d=$(basename "$(dirname "$f")"); fm=$(awk 'NR==1&&$0!="---"{exit 1} NR>1&&$0=="---"{exit} NR>1{print}' "$f") || fail "no frontmatter: $d"
  printf '%s\n' "$fm" | grep -qx "name: $d" || fail "name != dir: $d"
  printf '%s\n' "$fm" | grep -q '^description:' || fail "no description: $d"
  printf '%s\n' "$fm" | grep -q '^disable-model-invocation: true' || vis=$((vis+1))
  # relative links inside the skill resolve
  case "$d" in skill-development|plugin-package-repair) continue;; esac  # these teach skill layout with made-up example paths
  # (^|space/paren/backtick) prefix skips URL fragments such as .../durable-objects/examples/index.md
  for r in $(grep -oE '(^|[ (`[])(references|jobs|specs|examples)/[A-Za-z0-9_./-]+\.(md|json|sh|py|sql)' "$f" | sed -E 's/^[ (`[]//' | sort -u); do
    [ -e "$(dirname "$f")/$r" ] || [ -e "$P/$r" ] || echo "  warn: $d -> $r (not shipped)" >> "$W/warn"
  done
done
[ "$vis" -le 20 ] || fail "$vis model-visible skills (routing limit 20)"
chk "all skills: name==dir, description set; $vis model-visible (<=20), rest user-invoked"
miss=0
for p in $(grep -rhoE 'CLAUDE_PLUGIN_ROOT\}?/(scripts|cli)/[A-Za-z0-9_./-]+' --exclude-dir=hook-development --exclude-dir=plugin-structure --exclude-dir=skill-development "$P/skills" "$P/commands" "$P/agents" | sed -E 's#CLAUDE_PLUGIN_ROOT\}?/##' | sort -u); do
  case "$p" in scripts/validate.sh|scripts/load-context.sh|scripts/helper.py|scripts/run.sh|scripts/tool.sh) continue;; esac  # examples in plugin-authoring docs
  [ -e "$P/$p" ] || { echo "dangling: $p"; miss=1; }
done
[ $miss = 0 ] || fail "skills reference scripts that are not in the package"
chk "every script a skill points at exists in the package"
for p in $(grep -rhoE 'CLAUDE_SKILL_DIR\}?/(scripts|jobs|specs)/[A-Za-z0-9_.-]+' "$P/skills" | sed -E 's#.*\}?/(scripts|jobs|specs)/#\1/#' | sort -u); do
  ls "$P"/skills/*/"$p" >/dev/null 2>&1 || fail "dangling skill-dir ref $p"; done
[ -f "$P/skills/env-setup-wizard/scripts/env_audit.py" ] || fail "env_audit.py"
chk "skill-dir refs resolve (env_audit, context7)"
for f in $(find "$P" -name '*.py'); do python3 -I -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$f" || fail "syntax $f"; done
for f in $(find "$P" -name '*.sh'); do bash -n "$f" || fail "syntax $f"; done
chk "all .py parse, all .sh pass bash -n"
for l in "$P"/licenses/*; do [ -s "$l" ] || fail "empty license $l"; done
[ "$(ls "$P/licenses" | wc -l)" -ge 25 ] || fail "licenses missing"
grep -q '^| ' "$P/SOURCES.md" || fail SOURCES
chk "upstream licenses kept ($(ls "$P/licenses" | wc -l) files), SOURCES.md present"
export NVAEX_TASKS="$W/t.tsv"; T="$P/scripts/mytasks.sh"
[ -z "$(bash "$T" list)" ] || fail "list not empty at start"
bash "$T" add "Add KEY to .env" "tests need it" | grep -q '^#1 ' || fail add1
bash "$T" add $'two\tlines\nhere' >/dev/null
[ "$(wc -l < "$NVAEX_TASKS")" -eq 2 ] || fail "tab/newline injection split a record"
bash "$T" list | grep -q '^#2 two lines here$' || fail "sanitised title"
bash "$T" done 1 >/dev/null; bash "$T" list | grep -q '#1' && fail "done task still listed"
bash "$T" reject 2 "no" >/dev/null; [ -z "$(bash "$T" list)" ] || fail "rejected task still listed"
bash "$T" add "three" >/dev/null; bash "$T" list | grep -q '^#3 three' || fail "id not incrementing"
bash "$T" answer 3 "use npm" >/dev/null; awk -F'\t' '$1==3&&$3=="answered"&&$5=="use npm"{f=1}END{exit !f}' "$NVAEX_TASKS" || fail answer
bash "$T" done 99 2>/dev/null && fail "unknown id accepted"
chk "mytasks.sh: add/list/done/reject/answer, ids increment, injection sanitised, bad id fails"
timeout 10 bash "$P/skills/context7/scripts/context7.sh" >"$W/c7.out" 2>&1; [ $? -ne 0 ] || fail "context7 ran with no args"
chk "context7.sh rejects an empty invocation"
python3 "$P/cli/cc.py" --help 2>&1 | grep -q "claudestrophobic" || fail "cc.py --help"
chk "cc.py (sessions/projects lister) starts"
# --- no reference to another plugin: every <plugin>:<name> must be nvaex-ops:<name> and resolve to a file here
# Reference forms scanned: Agent(...)/Workflow(...) specs, name:/agentType:/subagent_type: "x:y", `x:y`, /x:y.
# Excluded: README/SOURCES (they describe donors), licenses, this file, and non-plugin tokens (file:line, node:*, three CSS declarations in bake-claude-md-files).
{ grep -rhoE '(Agent|Workflow)\([^)]*\)' "$P" --exclude-dir=licenses --exclude=README.md --exclude=SOURCES.md --exclude=selftest.sh -I
  grep -rhoE '(subagent_type|agentType|name)[:=] ?"[a-z][a-z0-9-]*:[a-z][a-z0-9-]*"' "$P" --exclude-dir=licenses --exclude=README.md --exclude=SOURCES.md --exclude=selftest.sh -I
  grep -rhoE '`/?[a-z][a-z0-9-]*:[a-z][a-z0-9-]*`' "$P" --exclude-dir=licenses --exclude=README.md --exclude=SOURCES.md --exclude=selftest.sh -I
  grep -rhoE '(^|[ (])/[a-z][a-z0-9-]*:[a-z][a-z0-9-]*' "$P" --exclude-dir=licenses --exclude=README.md --exclude=SOURCES.md --exclude=selftest.sh -I
} | grep -oE '[a-z][a-z0-9-]*:[a-z][a-z0-9-]*' | sort -u | grep -vE '^(file:line|node:[a-z]+|display:block|overflow-wrap:anywhere|white-space:pre-wrap)$' > "$W/xrefs"
foreign=$(grep -v '^nvaex-ops:' "$W/xrefs" || true)
[ -z "$foreign" ] || fail "references to other plugins: $(echo $foreign | tr '\n' ' ')"
for x in $(sed -n 's/^nvaex-ops://p' "$W/xrefs"); do
  [ -e "$P/agents/$x.md" ] || [ -e "$P/skills/$x/SKILL.md" ] || [ -e "$P/commands/$x.md" ] || [ -e "$P/workflows/$x.js" ] || fail "nvaex-ops:$x resolves to no agent, skill, command or workflow in the package"
done
chk "every <plugin>:<name> reference is nvaex-ops:<name> and resolves ($(wc -l < "$W/xrefs") distinct)"
# --- the restricted claude-security fold must stay gone (Anthropic-proprietary, public repo)
if grep -rIl -i 'claude-security\|scan-inventory\|scan-researcher\|nvaex-ops:scan' "$P" --exclude=selftest.sh --exclude=README.md --exclude=SOURCES.md >/dev/null; then fail "claude-security material found in the package"; fi
[ ! -e "$P/workflows" ] && [ ! -e "$P/skills/claude-security" ] && [ ! -e "$P/licenses/LICENSE.claude-security" ] || fail "claude-security path still present"
chk "no claude-security skill, agents, workflow, scripts or license in the package"
# --- rebuilt items: run each script for real
S="$P/skills"
bash "$S/tts/scripts/speak.sh" --out "$W/t.wav" "self test" || fail "tts speak.sh --out"; [ -s "$W/t.wav" ] || fail "tts wav empty"
bash "$S/tts/scripts/speak.sh" --engine nope x 2>/dev/null; [ $? -eq 2 ] || fail "tts bad engine must exit 2"
chk "tts: espeak-ng wrote a WAV; bad engine rejected"
if bash "$S/local-whisper/scripts/transcribe.sh" --check >/dev/null 2>&1; then
  tr=$(bash "$S/local-whisper/scripts/transcribe.sh" "$W/t.wav" 2>/dev/null); echo "$tr" | grep -qiE "self.?test" || fail "local-whisper did not read back 'self test' (got: $tr)"
  chk "local-whisper: espeak WAV -> Parakeet in proot read back '$tr'"
else echo "skip local-whisper: engine not present on this machine ($(bash "$S/local-whisper/scripts/transcribe.sh" --check 2>&1 | head -1))"; fi
python3 -I "$S/skill-inventory/scripts/inventory.py" "$P/skills" >/dev/null || fail "skill-inventory on this package reported problems"
mkdir -p "$W/sk/a" "$W/sk/b" "$W/sk/c"; for d in a b; do printf -- '---\nname: dup\ndescription: x\n---\n' > "$W/sk/$d/SKILL.md"; done; printf 'no fm\n' > "$W/sk/c/SKILL.md"
python3 -I "$S/skill-inventory/scripts/inventory.py" "$W/sk" > "$W/inv.out"; [ $? -eq 1 ] || fail "inventory missed planted problems"
grep -q "duplicate name" "$W/inv.out" && grep -q "no frontmatter" "$W/inv.out" || fail "inventory output lacks duplicate/frontmatter findings"
chk "skill-inventory: this package clean; planted duplicate and missing frontmatter flagged"
python3 -I "$S/kotlin-lsp/scripts/kt_check.py" --tools | grep -q "compile/LSP available" || fail "kt_check --tools"
printf 'fun f(m: Map<String,String>) {\n  println("a ${m["x"]} b")\n}\n' > "$W/ok.kt"; printf 'fun f() {\n  g(]\n' > "$W/bad.kt"
python3 -I "$S/kotlin-lsp/scripts/kt_check.py" "$W/ok.kt" >/dev/null || fail "kt_check false positive on string template"
python3 -I "$S/kotlin-lsp/scripts/kt_check.py" "$W/bad.kt" >/dev/null; [ $? -eq 1 ] || fail "kt_check missed broken Kotlin"
chk "kotlin-lsp: structural check passes a template string, fails unbalanced code (no compiler/LSP on this phone)"
T="$S/mcp-tunnel/scripts/tunnel.sh"; bash "$T" run 1 >/dev/null 2>&1; [ $? -ne 0 ] || fail "tunnel run with no token must stop"
mkdir -p "$W/bin"; printf '#!/bin/sh\n[ -n "$TUNNEL_TOKEN" ] && echo "stub cloudflared got token: yes" || echo "stub: no token"\n' > "$W/bin/cloudflared"; chmod +x "$W/bin/cloudflared"
python3 -c "import socket,time;s=socket.socket();s.bind(('127.0.0.1',0));s.listen(1);print(s.getsockname()[1],flush=True);time.sleep(8)" > "$W/port" & lp=$!; sleep 1
out=$(PATH="$W/bin:$PATH" TUNNEL_TOKEN=SECRETVALUE bash "$T" run "$(cat "$W/port")" 2>&1); kill $lp 2>/dev/null; wait $lp 2>/dev/null
echo "$out" | grep -q "got token: yes" || fail "tunnel run did not reach cloudflared (got: $out)"; echo "$out" | grep -q SECRETVALUE && fail "tunnel printed the token"
if command -v cloudflared >/dev/null; then :; else bash "$T" check 2>&1 | grep -q "STOP: cloudflared is not installed" || fail "tunnel check must stop when cloudflared is missing"; fi
chk "mcp-tunnel: stops without token; with a stub cloudflared the token reaches it from env and is never printed"
python3 -I "$P/tests/google_oauth_fake.py" >/dev/null || fail "google_oauth fake flow"
chk "google-setup: loopback OAuth against a fake token endpoint (PKCE, state check, 0600 file, no secret printed, reauth replaces)"
python3 -I "$S/harness-setup/scripts/stack_scan.py" "$P" | grep -q "languages:" || fail "stack_scan"
mkdir -p "$W/h/.claude"; printf '{"permissions":{"allow":["Bash(*)"]}}' > "$W/h/.claude/settings.json"; printf '{bad' > "$W/h/.mcp.json"
python3 -I "$S/harness-audit/scripts/config_audit.py" "$W/h" > "$W/au.out"; [ $? -eq 1 ] || fail "config_audit should exit 1 on planted HIGH findings"
grep -q "over-broad" "$W/au.out" && grep -q "invalid JSON" "$W/au.out" || fail "config_audit findings missing"
python3 -I "$S/harness-audit/scripts/config_audit.py" "$P" >/dev/null || fail "config_audit reports HIGH on this package"
chk "harness-setup scan runs; harness-audit flags planted wildcard permission and bad JSON, clean on this package"
python3 -I "$P/tests/office_test.py" 2>&1 | grep -q "office.py ok" || fail "office.py round trip"
chk "office-files: docx/xlsx/pptx/pdf read, replace (original untouched), pdf page split"
# --- claude-backup secret scan must fail CLOSED and still catch a planted key
D=$(mktemp -d); export CLAUDE_PLUGIN_DATA="$D/data"
printf 'hello\n' > "$D/clean.txt"; printf 'k = %s%s\n' 'ghp_' "$(printf 'a%.0s' $(seq 36))" > "$D/dirty.txt"
( source "$P/scripts/common.sh"; scan_for_secrets "$D/clean.txt" ) >/dev/null 2>&1 || fail "secret scan rejected a clean file"
( source "$P/scripts/common.sh"; scan_for_secrets "$D/dirty.txt" ) >/dev/null 2>&1 && fail "secret scan passed a planted token"
mkdir -p "$D/p/scripts"; cp "$P/scripts/common.sh" "$D/p/scripts/"
( source "$D/p/scripts/common.sh"; scan_for_secrets "$D/clean.txt" ) >/dev/null 2>&1 && fail "secret scan passed with NO manifest (must fail closed)"
unset CLAUDE_PLUGIN_DATA
chk "claude-backup scan_for_secrets: clean passes, planted token fails, missing manifest fails closed"
[ -s "$W/warn" ] && { echo "note: relative refs not shipped:"; sort -u "$W/warn" | head -50; }
echo "SELFTEST PASS ($n checks)"
