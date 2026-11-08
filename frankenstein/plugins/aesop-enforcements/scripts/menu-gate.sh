#!/usr/bin/env bash
# PreToolUse (AskUserQuestion), rule 5: a menu is allowed only if every question offers a way for the
# operator to write their own answer. Fails open on bad input.
in=$(cat)
miss=$(jq -r '[.tool_input.questions[]? | select(([.options[]?.label // ""] | map(test("write|type|own answer|something else|other|custom"; "i")) | any) | not) | .question] | .[]' <<<"$in" 2>/dev/null) || exit 0
[ -n "$miss" ] || exit 0
echo "BLOCKED (menu-gate): every question needs a write-in option. Add one labeled \"Write my own answer\" to: $(head -c 200 <<<"$miss")" >&2
exit 2
