#!/usr/bin/env bash
# Rule 12 (operator, 2026-11-10): read the source first. Working with a fork, an install or any asset, no claim
# rests on gleaned information or training data: the asset's own docs and folder tree are read first, once per
# session per asset. An asset is a repo under $REPOS_DIR/<name> or a vendor folder under the vault's
# Vendor-Registries/<vendor>.
#   Two modes, picked from the operator's prompt (an install is always deep):
#     deep   breakdown, full install, comparison, user guide, evaluation: every clean MD document in the asset's
#            index folder (clean_md/); with no clean MD yet, the full read below.
#     brief  quick rundown, yes/no, fact check: chunk.jsonl looked up (Read, grep, jq), or the current manifest.jsonl
#            plus one file it points to.
#   "Read", the full read (no clean MD yet):
#     full   its folder tree listed (find / tree / ls -R / git ls-files / rg --files) AND every doc file read:
#            README*, INSTALL*, CHANGELOG*, every *.md in its root and in docs/ (two levels).
#     manifest  its current manifest read (vault Assets-Index/<name>/manifest.jsonl, or the vendor folder's
#            manifest.jsonl; current = its "head" matches the repo's HEAD) AND at least one file it points to read.
#   PostToolUse Read|Bash: records reads.   PreToolUse Bash: an install or clone needs its asset read (a clone or
#   a package with no local repo needs official docs fetched this session).   Stop: an answer about an asset's
#   features, flags, install or setup needs that asset read. Blocks once per turn (stop_hook_active allows).
#   Automated runs (AESOP_AUTOMATED=1): a highlight in hooks.log, never a block (Rule 11).
. "$(dirname "$(realpath "$0")")/lib/env.sh"
in=$(cat)
sid=$(jq -r '.session_id // empty' <<<"$in" 2>/dev/null) || exit 0; [ -n "$sid" ] || exit 0
ev=$(jq -r '.hook_event_name // ""' <<<"$in"); tool=$(jq -r '.tool_name // ""' <<<"$in")
cwd=$(jq -r '.cwd // ""' <<<"$in")
REPOS=$(realpath -m "${REPOS_DIR:-$HOME/repos}"); VR="${VAULT:-/nonexistent}/${VENDOR_DIR:-Vendor-Registries}"; AI="${VAULT:-/nonexistent}/${ASSETS_INDEX:-Assets-Index}"
rec="$ST/source-$sid.tsv"
say() {   # block, or highlight on automated runs
  if [ "${AESOP_AUTOMATED:-0}" = 1 ]; then hook_log "HIGHLIGHT (source-gate, Rule 12): $1"; exit 0; fi
  echo "BLOCKED (source-gate): Rule 12, read the source first. $1" >&2; exit 2
}
has() {        # has NAME KIND [PATH]: a record exists this session
  [ -f "$rec" ] && awk -F'\t' -v n="$1" -v k="$2" -v p="${3-}" '$1==n && $2==k && (p=="" || $3==p) {f=1} END {exit !f}' "$rec"
}
asset_of() {   # path -> "name<TAB>root", or nothing
  local p; p=$(realpath -m "$1" 2>/dev/null) || return
  case $p in
    "$REPOS"/*) local n=${p#"$REPOS"/}; n=${n%%/*}; [ -n "$n" ] && printf '%s\t%s\n' "$n" "$REPOS/$n" ;;
    "$VR"/*)    local n=${p#"$VR"/}; n=${n%%/*}; [ -n "$n" ] && printf 'vendor:%s\t%s\n' "$n" "$VR/$n" ;;
    "$AI"/*)    local n=${p#"$AI"/}; n=${n%%/*}; [ -n "$n" ] && printf '%s\t%s\n' "$n" "$REPOS/$n" ;;
  esac
}
docs_of() {    # doc files an asset requires (relative paths)
  ( cd "$1" 2>/dev/null || exit 0
    { ls -1 README* INSTALL* CHANGELOG* *.md 2>/dev/null; find docs doc -maxdepth 2 -name '*.md' 2>/dev/null; } | sort -u )
}
idx_of()      { local n=$1 r=$2; case $n in vendor:*) echo "$r" ;; *) echo "$AI/$n" ;; esac; }   # the asset's index folder
manifest_of() { echo "$(idx_of "$1" "$2")/manifest.jsonl"; }
current() {    # the manifest's HEAD matches the repo (or it records none)
  local m; m=$(manifest_of "$1" "$2"); [ -f "$m" ] || return 1
  local h; h=$(head -1 "$m" | jq -r '.head // empty' 2>/dev/null)
  [ -z "$h" ] || [ "$h" = "$(git -C "$2" rev-parse HEAD 2>/dev/null)" ]
}
clean_of()  { local c; c="$(idx_of "$1" "$2")/clean_md"; [ -d "$c" ] && find "$c" -name '*.md' | sort; }
full_read() {  # tree listed + every doc read
  local n=$1 r=$2 d
  has "$n" tree || return 1
  while IFS= read -r d; do [ -n "$d" ] || continue; has "$n" doc "$r/$d" || return 1; done < <(docs_of "$r")
}
deep_read() {  # every clean MD document read; with no clean MD yet, the full read
  local n=$1 r=$2 c f
  c=$(clean_of "$n" "$r")
  [ -n "$c" ] || { full_read "$n" "$r"; return; }
  while IFS= read -r f; do has "$n" doc "$f" || return 1; done <<<"$c"
}
brief_read() { # chunk.jsonl looked up, or the current manifest plus one file it points to; a deep read also counts
  local n=$1 r=$2
  has "$n" chunk && return 0
  current "$n" "$r" && has "$n" manifest && has "$n" doc && return 0
  deep_read "$n" "$r"
}
is_read() { if [ "${3:-$mode}" = deep ]; then deep_read "$1" "$2"; else brief_read "$1" "$2"; fi; }
missing_docs() { local n=$1 r=$2 d; { clean_of "$n" "$r" | grep . || docs_of "$r" | sed "s|^|$r/|"; } | while IFS= read -r d; do has "$n" doc "$d" || echo "${d##*/}"; done | head -5 | paste -sd ' ' -; }
need() {       # name root what mode -> block with what is missing
  local n=$1 r=$2 what=$3 m=${4:-$mode} t="" md idx; idx=$(idx_of "$n" "$r")
  md=$(missing_docs "$n" "$r")
  if [ "$m" = deep ]; then
    [ -n "$(clean_of "$n" "$r")" ] || has "$n" tree || t="its folder tree (find $r -not -path '*/.git/*'), "
    say "$what $n (deep read): read ${t}every clean MD document in $idx/clean_md/ (none yet: the full tree and every doc file)${md:+; still unread: $md}. Training data and another model's word are not sources. Once per session."
  else
    say "$what $n (brief): look it up in $idx/chunk.jsonl, or read the current $idx/manifest.jsonl plus the file it points to (or do the deep read). Training data and another model's word are not sources."
  fi
}
mode=$(cat "$ST/source-mode-$sid" 2>/dev/null); mode=${mode:-brief}

# ---------- mode, from the operator's prompt ----------
if [ "$ev" = UserPromptSubmit ]; then
  p=$(jq -r '.prompt // ""' <<<"$in" | tr '[:upper:]' '[:lower:]')
  if grep -qE '(breakdown|break down|full install|install|compar(e|ison)|user guide|walkthrough|walk through|deep (read|dive)|evaluat|eval\b|in depth|in-depth|audit|everything about)' <<<"$p"; then m=deep; else m=brief; fi
  mkdir -p "$ST"; echo "$m" > "$ST/source-mode-$sid"; exit 0
fi

# ---------- recording ----------
if [ "$ev" = PostToolUse ]; then
  mkdir -p "$ST"
  case $tool in
    Read)
      f=$(jq -r '.tool_input.file_path // ""' <<<"$in"); f=${f/#\~/$HOME}; a=$(asset_of "$f") || exit 0; [ -n "$a" ] || exit 0
      IFS=$'\t' read -r n r <<<"$a"; f=$(realpath -m "$f")
      case ${f##*/} in manifest.jsonl) k=manifest ;; chunk.jsonl) k=chunk ;; *) k=doc ;; esac
      printf '%s\t%s\t%s\n' "$n" "$k" "$f" >> "$rec" ;;
    Bash)
      c=$(jq -r '.tool_input.command // ""' <<<"$in")
      for w in $c; do
        w=${w//[\"\']/}; w=${w/#\~/$HOME}; case $w in /*) ;; *) continue ;; esac
        a=$(asset_of "$w") || continue; [ -n "$a" ] || continue; IFS=$'\t' read -r n r <<<"$a"
        if grep -qE '(^|[;&|[:space:]])(find|tree|rg --files|git( -C [^ ]+)? ls-files|ls -[a-zA-Z]*R)' <<<"$c"; then printf '%s\ttree\t%s\n' "$n" "$r" >> "$rec"; fi
        if [ -f "$w" ] && grep -qE '(^|[;&|[:space:]])(cat|sed|head|tail|less|bat|grep|rg|jq)[[:space:]]' <<<"$c"; then
          case ${w##*/} in chunk.jsonl) k=chunk ;; manifest.jsonl) k=manifest ;; *) k=doc ;; esac
          printf '%s\t%s\t%s\n' "$n" "$k" "$(realpath -m "$w")" >> "$rec"; fi
      done
      # a listing run from inside an asset with no path names that asset
      a=$(asset_of "$cwd"); if [ -n "$a" ] && grep -qE '^[[:space:]]*(find \.|tree|rg --files|git ls-files|ls -[a-zA-Z]*R)' <<<"$c"; then IFS=$'\t' read -r n r <<<"$a"; printf '%s\ttree\t%s\n' "$n" "$r" >> "$rec"; fi ;;
    WebFetch|WebSearch) printf '*\twebdoc\t%s\n' "$(jq -r '.tool_input.url // .tool_input.query // ""' <<<"$in")" >> "$rec" ;;
    *) case $tool in mcp__*fetch*|mcp__*docs*|mcp__*search*) printf '*\twebdoc\t%s\n' "$tool" >> "$rec" ;; esac ;;
  esac
  exit 0
fi

# ---------- installs and clones ----------
if [ "$ev" = PreToolUse ] && [ "$tool" = Bash ]; then
  c=$(jq -r '.tool_input.command // ""' <<<"$in")
  I='(^|[;&|[:space:]])(pip3? install|pipx install|uv (pip )?install|npm (i|install|ci)|pnpm (add|install)|yarn add|pkg install|apt(-get)? install|cargo install|go install|make install|git clone|gh repo clone|claude plugin install)([[:space:]]|$)'
  command grep -qE "$I" <<<"$c" || exit 0
  a=$(asset_of "$cwd")
  for w in $c; do w=${w//[\"\']/}; w=${w/#\~/$HOME}; case $w in /*) b=$(asset_of "$w"); [ -n "$b" ] && a=$b ;; esac; done
  if [ -n "$a" ]; then IFS=$'\t' read -r n r <<<"$a"; is_read "$n" "$r" deep && exit 0; need "$n" "$r" "Before installing from" deep; fi
  has "*" webdoc && exit 0
  say "Before this install or clone, fetch its official install guide or README (WebFetch, gh repo view, the vendor's docs) and read it. Training data is not a source."
fi

# ---------- answers about an asset ----------
if [ "$ev" = Stop ]; then
  [ "$(jq -r '.stop_hook_active // false' <<<"$in")" = true ] && exit 0
  msg=$(jq -r '.last_assistant_message // ""' <<<"$in")
  command grep -qiE '(^|[^[:alnum:]])(install(s|ed|ing)?|features?|flags?|options?|supports?|setup|set up|config(ure|uration)?|spec|version|commands?)([^[:alnum:]]|$)' <<<"$msg" || exit 0
  for d in "$REPOS"/*/; do
    n=${d%/}; n=${n##*/}; [ ${#n} -ge 4 ] || continue
    command grep -qiE "(^|[^[:alnum:]_-])$(sed 's/[.[\*^$()+?{|]/\\&/g' <<<"$n")([^[:alnum:]_-]|$)" <<<"$msg" || continue
    is_read "$n" "${d%/}" || need "$n" "${d%/}" "This answer is about"
  done
  exit 0
fi
exit 0
