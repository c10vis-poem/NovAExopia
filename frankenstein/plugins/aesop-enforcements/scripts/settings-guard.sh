#!/usr/bin/env bash
# PreToolUse (Bash|Edit|Write): the agent may not change the operator's Claude Code configuration:
# ~/.claude/settings.json, ~/.claude/settings.local.json, ~/.claude.json. Blocks Edit/Write on them and
# Bash that writes them (redirect, tee, sed -i, mv, cp onto, truncate, rm, ln). Reads stay allowed.
# Also, in any repo: no writing disableAllHooks true to a settings file, and no starting a session with it.
# No agent override; the operator's own `!` commands are not agent tool calls and never reach here.
in=$(cat); tool=$(jq -r '.tool_name // ""' <<<"$in" 2>/dev/null) || exit 0
say(){ echo "BLOCKED (settings-guard): Claude Code settings are operator-owned (advisor, model, plugins, hooks). Give the operator the command as a ! line instead." >&2; exit 2; }
KILL='disableAllHooks\\?"?[[:space:]]*(:|=)[[:space:]]*\\?"?true'
kill_say(){ echo "BLOCKED (settings-guard): disableAllHooks true turns every hook off, in any repo or settings file. Only the operator sets that, with a ! line." >&2; exit 2; }
if [ "$tool" != Bash ]; then
  f=$(jq -r '.tool_input.file_path // ""' <<<"$in"); f=${f/#\~/$HOME}
  case $f in "$HOME/.claude/settings.json"|"$HOME/.claude/settings.local.json"|"$HOME/.claude.json") say ;; esac
  case $f in */.claude/settings*.json|*/settings*.json)
    jq -r '(.tool_input.new_string // "") + (.tool_input.content // "")' <<<"$in" | command grep -qE "$KILL" && kill_say ;;
  esac
  exit 0
fi
c=$(jq -r '.tool_input.command // ""' <<<"$in")
# Anywhere, any file: a command that writes disableAllHooks true, or starts a session with it.
if command grep -qE "$KILL" <<<"$c"; then
  w=$(sed -E 's/[0-9]*>+[[:space:]]*(\/dev\/null|&[0-9])//g' <<<"$c")
  command grep -qE '>|(^|[;&|[:space:](])(tee|mv|cp|python3?|node|perl|ruby)[[:space:]]|sed[[:space:]]+-[a-zA-Z]*i|--settings' <<<"$w" && kill_say
fi
H="(~|\\\$HOME|\\\$\\{HOME\\}|${HOME//./\\.})"
F="$H/\\.claude(/settings(\\.local)?\\.json|\\.json)"
# After `cd ~/.claude`, bare settings(.local).json names count too
command grep -qE "(^|[;&|[:space:]])cd[[:space:]]+[\"']?$H/\\.claude/?[\"']?([;&|[:space:]]|$)" <<<"$c" && F="($F|(^|[[:space:]\"'])settings(\\.local)?\\.json)"
command grep -qE "$F" <<<"$c" || exit 0
while IFS= read -r s; do
  command grep -qE "$F" <<<"$s" || continue
  command grep -qE ">[[:space:]]*[\"']?$F|(^|[[:space:](])(tee|mv|truncate|rm|ln|unlink|dd)[[:space:]]|(sed|perl)[[:space:]]+-[a-zA-Z]*i" <<<"$s" && say
  command grep -qE "(^|[[:space:](])cp[[:space:]].*[[:space:]][\"']?$F[\"']?[[:space:]]*$" <<<"$s" && say
done < <(sed -E 's/[0-9]*>+[[:space:]]*(\/dev\/null|&[0-9])//g' <<<"$c" | tr ';&|' '\n\n\n')
exit 0
