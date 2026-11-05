#!/usr/bin/env bash
# Operator-only task list. add "title" ["why"] | list | done N | reject N ["reason"] | answer N "text"
set -eu
F="${NVAEX_TASKS:-$HOME/.claude/state/my-tasks.tsv}"; mkdir -p "$(dirname "$F")"; touch "$F"
clean() { printf '%s' "$1" | tr '\t\n' '  '; }
setst() { # id state note
  grep -q "^$1	" "$F" || { echo "no task $1" >&2; exit 1; }
  awk -F'\t' -v OFS='\t' -v id="$1" -v st="$2" -v n="$3" '$1==id{$3=st;$5=n}1' "$F" > "$F.tmp" && mv "$F.tmp" "$F"; }
case "${1:-list}" in
  add) id=$(awk -F'\t' 'BEGIN{m=0}$1>m{m=$1}END{print m+1}' "$F")
       printf '%s\t%s\topen\t%s\t\n' "$id" "$(clean "$2")" "$(clean "${3:-}")" >> "$F"; echo "#$id added" ;;
  list) awk -F'\t' '$3=="open"{printf "#%s %s%s\n",$1,$2,($4!=""?" - "$4:"")}' "$F" ;;
  done) setst "$2" done ""; echo "#$2 done" ;;
  reject) setst "$2" rejected "$(clean "${3:-}")"; echo "#$2 rejected" ;;
  answer) setst "$2" answered "$(clean "$3")"; echo "#$2 answered" ;;
  *) echo "usage: mytasks.sh add|list|done|reject|answer" >&2; exit 2 ;;
esac
