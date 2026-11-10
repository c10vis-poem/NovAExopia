#!/usr/bin/env bash
# Stop, rule 7: a turn cannot end on a yes/no or either/or question. Reads the last non-empty line of the
# final answer. It matches phrases, so it catches the common forms, not every one. Blocks once
# (stop_hook_active allows), so it can never hold a turn open. Fails open on bad input.
in=$(cat)
active=$(jq -r '.stop_hook_active // false' <<<"$in" 2>/dev/null) || exit 0
[ "$active" = true ] && exit 0
last=$(jq -r '.last_assistant_message // ""' <<<"$in" | sed -E '/^[[:space:]]*$/d' | tail -1 | sed -E 's/[*_`]+//g; s/[[:space:]]+$//')
[ -n "$last" ] || exit 0
# Rule 2's check-in (okay, amend, override, defer) is the required answer format, not a yes/no or either/or question.
command grep -qiE '\b(ok|okay)\b.*\bamend\b|\bamend\b.*\boverride\b|\bdefer\b.*\boverride\b' <<<"$last" && exit 0
yn="(want me to|should i|shall i|do you want|would you like|can i |could i |may i |is that (ok|okay|fine|right|alright)|does that work|sound good|sounds good|yes or no|y/n)"
hit=
if command grep -qiE '\?$' <<<"$last"; then
  command grep -qiE "$yn" <<<"$last" && hit=yes/no
  command grep -qiE '(^|[[:space:]])(ok|okay|right|yes|no)\?$' <<<"$last" && hit=yes/no
  command grep -qiE '[[:space:]]or[[:space:]]' <<<"$last" && hit=either/or
fi
command grep -qiE ",? or i('|’)?(ll| will) " <<<"$last" && hit=either/or
# Rule 8: the agent never tells the operator to merge; merging is the agent's job (auto-merge on green CI).
all=$(jq -r '.last_assistant_message // ""' <<<"$in" 2>/dev/null)
if command grep -qiE "(you|you'll|you will)[[:space:]]+(need to|have to|must|should|can|will need to|got to)[[:space:]]+(click )?merge|please[[:space:]]+(click )?merge|go ahead and merge|merge (it|the pr|this pr|pr #?[0-9]+) (yourself|manually|by hand)|(^|[.!][[:space:]]+)merge (it|the pr|this pr|pr #?[0-9]+)[.!]" <<<"$all"; then
  echo "BLOCKED (question-gate, rule 8): the answer tells the operator to merge. Merging is the agent's job: enable auto-merge (gh pr merge --auto --squash --delete-branch) or wait for green CI and merge it, then report." >&2
  exit 2
fi
[ -n "$hit" ] || exit 0
echo "BLOCKED (question-gate): the answer ends on a $hit question: ${last:0:160}. Pick the path and do it, or ask one open question naming what you are missing." >&2
exit 2
