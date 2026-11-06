#!/usr/bin/env sh
# nvaex-ui-cockpit selftest. Runs on the device; touches only a temp HOME. Exit 0 = pass.
here=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export HOME="$T/home"; mkdir -p "$HOME/.claude/plugins" "$T/repo"
fail=0; ok() { echo "PASS $1"; }; bad() { echo "FAIL $1"; fail=1; }
chk() { n=$1; shift; if "$@" >"$T/out" 2>&1; then ok "$n"; else bad "$n"; sed 's/^/  /' "$T/out"; fi; }
has() { grep -q -- "$1" "$T/out"; }

# fixture: one enabled plugin with a skill, one disabled, one profile
P="$HOME/.claude/plugins/cache/m/demo/1.0"; mkdir -p "$P/skills/hello" "$P/.claude-plugin" "$HOME/.claude/harness-scope/profiles"
printf -- '---\nname: hello\ndescription: Says hello to the user. Second sentence.\n---\nbody\n' > "$P/skills/hello/SKILL.md"
printf '{"modules":["./register.tsx"]}' > "$P/hooks.json"; mkdir -p "$P/hooks"; mv "$P/hooks.json" "$P/hooks/hooks.json"
cat > "$HOME/.claude/plugins/installed_plugins.json" <<J
{"version":2,"plugins":{"demo@m":[{"installPath":"$P"}],"idle@m":[{"installPath":"$T/none"}]}}
J
echo '{"enabledPlugins":{"demo@m":true,"idle@m":false}}' > "$HOME/.claude/settings.json"
echo '{"skills":{"allow":["hello"]}}' > "$HOME/.claude/harness-scope/profiles/docs.json"
S="$here/scripts"

# plugins-panel backend
python3 "$S/inventory.py" summary > "$T/out" 2>&1; has 'Plugins: 1/2 active' && ok "inventory summary" || { bad "inventory summary"; cat "$T/out"; }
python3 "$S/inventory.py" list > "$T/out" 2>&1; has 'skills 1 agents 0 cmds 0 hooks 1' && ok "inventory counts" || { bad "inventory counts"; cat "$T/out"; }
python3 "$S/inventory.py" json | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d["active"]==1 and d["plugins"][0]["tokens"]>0' && ok "inventory json+tokens" || bad "inventory json"

# env-customizer backend
python3 "$S/profiles.py" list --repo "$T/repo" > "$T/out" 2>&1; has 'docs' && has 'writing' && ok "profiles list" || bad "profiles list"
python3 "$S/profiles.py" use docs --repo "$T/repo" >/dev/null 2>&1; grep -q '"profile": "docs"' "$T/repo/.claude/harness-scope.json" && ok "profile use writes selector" || bad "profile use"
python3 "$S/profiles.py" list --repo "$T/repo" > "$T/out"; grep -q '^\* docs' "$T/out" && ok "profile marked current" || bad "profile current"
python3 "$S/profiles.py" use ../evil --repo "$T/repo" >/dev/null 2>&1 && bad "bad name rejected" || ok "bad name rejected"
python3 "$S/profiles.py" clear --repo "$T/repo" >/dev/null; [ ! -e "$T/repo/.claude/harness-scope.json" ] && ok "profile clear" || bad "profile clear"
[ "$(cat "$HOME/.claude/settings.json")" = '{"enabledPlugins":{"demo@m":true,"idle@m":false}}' ] && ok "settings.json untouched" || bad "settings.json touched"

# config tree backend
python3 "$S/configtree.py" hello > "$T/out" 2>&1; has 'Says hello to the user.' && ! has 'Second sentence' && ok "config tree one-line explanation" || { bad "config tree"; cat "$T/out"; }
python3 "$S/configtree.py" zzzz > "$T/out" 2>&1; has 'no match' && ok "config tree no match" || bad "config tree no match"

# kill switch (the mods call exactly this)
K="$here/scripts/killswitch.sh"
sh "$K" nvaex-ui-cockpit context-window && bad "ks default on" || ok "ks default on"
mkdir -p "$HOME/.claude/state/off"; touch "$HOME/.claude/state/off/nvaex-ui-cockpit.context-window"
sh "$K" nvaex-ui-cockpit context-window && ok "ks per-mod off" || bad "ks per-mod off"
sh "$K" nvaex-ui-cockpit plugins-panel && bad "ks other mod unaffected" || ok "ks other mod unaffected"
rm "$HOME/.claude/state/off/nvaex-ui-cockpit.context-window"; touch "$HOME/.nvaex-hooks-off"
sh "$K" nvaex-ui-cockpit env-customizer-panel && ok "ks global off" || bad "ks global off"
rm "$HOME/.nvaex-hooks-off"

# context-window rows
chk "context rows (node)" node "$here/tests/ctx.test.mjs"

# agent-configs backend: marketplace + package + workflow rows from the fixture
mkdir -p "$HOME/.claude/plugins/marketplaces/m/.claude-plugin" "$P/agents"
echo '{"plugins":[{"name":"a"},{"name":"b"}]}' > "$HOME/.claude/plugins/marketplaces/m/.claude-plugin/marketplace.json"
printf -- '---\nname: builder\ndescription: builds\n---\n' > "$P/agents/builder.md"
echo "{\"m\":{\"source\":{\"source\":\"github\",\"repo\":\"o/m\"},\"installLocation\":\"$HOME/.claude/plugins/marketplaces/m\"}}" > "$HOME/.claude/plugins/known_marketplaces.json"
python3 "$S/agentconfigs.py" items --repo "$T/repo" > "$T/out" 2>&1
grep -q "^market	m	2 plugins	o/m$" "$T/out" && ok "agentconfigs marketplace row" || { bad "agentconfigs marketplace row"; cat "$T/out"; }
grep -q "^pkg	demo@m	on	builder$" "$T/out" && ok "agentconfigs package row (agents listed)" || { bad "agentconfigs package row"; cat "$T/out"; }
grep -q "^wf	docs	off	" "$T/out" && ok "agentconfigs workflow row" || bad "agentconfigs workflow row"
python3 "$S/profiles.py" use docs --repo "$T/repo" >/dev/null; python3 "$S/agentconfigs.py" items --repo "$T/repo" | grep -q "^wf	docs	on	" && ok "agentconfigs marks current workflow" || bad "agentconfigs marks current workflow"
[ "$(cat "$HOME/.claude/settings.json")" = '{"enabledPlugins":{"demo@m":true,"idle@m":false}}' ] && ok "settings.json untouched by agentconfigs" || bad "settings.json touched by agentconfigs"

# pure logic of the added mods: tree rows, config cycling and apply argv (injection rejected), choice cards, jev view, button row
chk "added-mod logic (node)" node "$here/tests/libs.test.mjs"

# engine: manifest + hooks module + mod tests (needs the claude binary; HOME restored for it)
REALHOME=$(getent passwd "$(id -u)" 2>/dev/null | cut -d: -f6); [ -n "$REALHOME" ] || REALHOME=${REAL_HOME:-/data/data/com.termux/files/home}
CL=$(command -v claude); [ -n "$CL" ] || CL="$REALHOME/.local/bin/claude"
if [ -x "$CL" ]; then
  HOME=$REALHOME "$CL" plugin validate "$here" </dev/null > "$T/out" 2>&1; has 'Found 1 error\|Found [0-9]* errors' && bad "claude plugin validate" || ok "claude plugin validate"
  HOME=$REALHOME "$CL" plugin test "$here" </dev/null > "$T/out" 2>&1; has ' 0 fail' && [ "$(sed -n 's/.*\([0-9][0-9]*\) pass.*/\1/p' "$T/out" | head -1)" = 8 ] \
    && ok "claude plugin test ($(grep -o '[0-9]* pass' "$T/out"))" || { bad "claude plugin test"; tail -15 "$T/out"; }
else echo "SKIP claude binary not found"; fi

# structure: one hooks module, one session.start, no gauge left, no settings writes in code
[ "$(grep -c "on('session.start'" "$here/hooks/register.tsx")" = 1 ] && ok "one session.start entry" || bad "one session.start entry"
[ ! -e "$here/hooks/mods/token-cache-gauge.tsx" ] && ok "usage gauge removed" || bad "usage gauge removed"
grep -rq 'settings.*json' "$here/hooks" && bad "no settings writes in hooks" || ok "no settings writes in hooks"
for m in plugins-panel env-customizer-panel obsidian-config-tree context-window file-tree-panel agent-configs-panel top-button-row browser-cards jev-panel; do
  [ -f "$here/hooks/mods/$m.tsx" ] && grep -q "^const MOD = '$m'" "$here/hooks/mods/$m.tsx" && grep -q "mod.$m\|isOff(\$, MOD)" "$here/hooks/mods/$m.tsx" || bad "mod $m present and gated"
done
for l in cache-ttl-timer context-bar; do [ ! -e "$here/licenses/LICENSE.$l" ] || bad "stale license $l"; done

[ $fail = 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"
exit $fail
