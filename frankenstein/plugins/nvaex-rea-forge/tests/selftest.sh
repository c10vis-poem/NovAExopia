#!/usr/bin/env sh
# nvaex-rea-forge selftest: every check runs real code on fixtures; any failure exits 1.
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
ok() { echo "PASS $1"; }; die() { echo "FAIL $1"; exit 1; }
G="git -c user.email=a@b -c user.name=t"

# manifest + every skill has frontmatter name/description; folded skills keep LICENSE
python3 -c "import json;j=json.load(open('$R/.claude-plugin/plugin.json'));assert j['name']=='nvaex-rea-forge'" || die plugin.json
for s in "$R"/skills/*/SKILL.md; do
  head -4 "$s" | grep -q '^name:' && head -4 "$s" | grep -q '^description:' || die "frontmatter $s"
done
for d in code-map rea-review rea-customize mcp2cli mindmap; do [ -f "$R/skills/$d/LICENSE" ] || die "LICENSE $d"; done
[ ! -e "$R/hooks" ] || die "unexpected hooks dir"
ok manifest

# harvest + wrap a fixture fork
F="$T/fork"; mkdir -p "$F/prompts"; cd "$F"
cat > cli.py <<'P'
import argparse
# sentry telemetry hook here
def big(x):
    """Sum squares the slow way."""
    t = 0
    for i in range(x):
        t += i * i
    a = t
    b = a
    c = b
    d = c
    e = d
    f = e
    g = f
    h = g
    j = h
    k = j
    return k
if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("n", type=int)
    print(big(p.parse_args().n))
P
echo "You are a careful reviewer. Your task is to review code." > prompts/review.md
git init -q . && git add -A && $G commit -qm base
python3 "$R/scripts/harvest.py" "$F" --out "$T/out" >/dev/null
C="$T/out/CAPABILITY_CARD.json"
python3 - "$C" <<'P' || die card
import json,sys
c=json.load(open(sys.argv[1]))
assert c["schema"].startswith("CAPABILITY_CARD") and c["languages"]["python"]==1
assert any(e["kind"]=="argparse" for e in c["entrypoints"])
assert any(a["name"]=="big" for a in c["algorithms"])
assert any(p["file"].endswith("review.md") for p in c["prompts"])
assert "cli.py" in c["telemetry_files"] and c["packaging_gate"]=="cli-wrap"
P
ok harvest-card
python3 "$R/scripts/wrap.py" "$C" >/dev/null
[ "$(sh "$T/out/wrap/fork" 7)" = "91" ] || die wrapped-cli; ok wrap-runs
grep -q '^name:' "$T/out/wrap/SKILL.md" && ok wrap-skill

# rea-review: quote_check classifies exact (v), dropped qualifier (n), wrong number (u)
Q="$R/skills/rea-review/quote_check.py"
printf 'Note: the rate is 5%% if you qualify. The fee is 2%%.\n' > "$T/page.txt"
st() { python3 "$Q" --quote "$1" --page-file "$T/page.txt" | python3 -c "import json,sys;print(json.load(sys.stdin)['status'])"; }
[ "$(st 'The fee is 2%')" = v ] && [ "$(st 'the rate is 5%')" = n ] && [ "$(st 'The fee is 3%')" = u ] || die quote-check
ok quote-check

# upstream.py: init picks latest stable tag, next sees a new release, prune drops removed skills
U="$T/up"; mkdir -p "$U/skills/keep" "$U/skills/gone"; cd "$U"; echo 1 > skills/keep/f; echo 1 > skills/gone/f
git init -q . && git add -A && $G commit -qm 1 && git tag v1.0.0
echo 2 > skills/keep/f && $G commit -qam 2 && git tag v1.1.0-rc1
W="$T/work"; mkdir -p "$W"
[ "$(python3 "$R/scripts/upstream.py" init "$W" "$U" | python3 -c "import json,sys;print(json.load(sys.stdin)['lastSyncedTag'])")" = v1.0.0 ] || die upstream-init
echo 3 > skills/keep/f && $G commit -qam 3 && git tag v1.2.0
[ "$(python3 "$R/scripts/upstream.py" next "$W")" = "new v1.2.0" ] || die upstream-next
printf '## keep\nx\n## gone\ny\n' > "$W/.turbocharge/intent.md"
rm -r "$U/skills/gone"
python3 "$R/scripts/upstream.py" prune "$W" "$U/skills" | grep -q 'pruned: gone' || die prune
grep -q '^## keep' "$W/.turbocharge/intent.md" && ! grep -q '^## gone' "$W/.turbocharge/intent.md" || die prune-file
python3 -c "import json;p='$W/.turbocharge/settings.json';c=json.load(open(p));c['syncStatus']='failed';json.dump(c,open(p,'w'))"
set +e; python3 "$R/scripts/upstream.py" next "$W" >/dev/null; rc=$?; set -e
[ "$rc" = 3 ] || die "next-blocks-after-failed-sync (rc=$rc)"
ok upstream-sync

# mcp2cli against a fake stdio MCP server
cat > "$T/srv.py" <<'P'
import json,sys
for l in sys.stdin:
    m=json.loads(l); i=m.get("id"); me=m.get("method")
    if i is None: continue
    if me=="initialize": r={"protocolVersion":"2024-11-05","capabilities":{},"serverInfo":{"name":"f","version":"1"}}
    elif me=="tools/list": r={"tools":[{"name":"add","description":"Add two numbers.","inputSchema":{"type":"object","properties":{"a":{"type":"number"},"b":{"type":"number"},"note":{"type":"string"}},"required":["a","b"]}},{"name":"boom","description":"Fails.","inputSchema":{"type":"object","properties":{}}}]}
    elif me=="tools/call":
        p=m["params"]; a=p["arguments"]
        r={"content":[{"type":"text","text":str(a["a"]+a["b"])}]} if p["name"]=="add" else {"isError":True,"content":[{"type":"text","text":"nope"}]}
    else: r={}
    print(json.dumps({"jsonrpc":"2.0","id":i,"result":r}),flush=True)
P
M="$R/scripts/mcp2cli.py"
python3 "$M" gen calc "$T/gen" python3 "$T/srv.py" >/dev/null
[ "$(sh "$T/gen/calc" add a=2 b=3)" = 5 ] || die mcp2cli-call
set +e; sh "$T/gen/calc" boom >/dev/null; rc=$?; set -e
[ "$rc" = 1 ] || die "mcp2cli-error-exit (rc=$rc)"
grep -q 'calc add a=<number> b=<number> note=<string>?' "$T/gen/SKILL.md" && ! grep -qi mcp "$T/gen/SKILL.md" || die mcp2cli-skill
ok mcp2cli

# mindmap checker accepts a valid map, rejects two H1s
K="$R/skills/mindmap/scripts/check.py"
printf -- '---\ntitle: T\nmarkmap:\n  colorFreezeLevel: 2\n---\n\n# Root\n\n## A\n- x\n  - y\n' > "$T/good.md"
printf -- '---\ntitle: T\n---\n# One\n# Two\n## A\n' > "$T/bad.md"
python3 "$K" "$T/good.md" >/dev/null && ! python3 "$K" "$T/bad.md" >/dev/null || die mindmap-check
ok mindmap

# code-map: validator rejects a bad edge; a good data.json renders HTML whose script parses
cat > "$T/d.json" <<'P'
{"title":"T","layers":[{"key":"a","label":"A","color":"#2563eb"}],"clusters":[{"key":"c","label":"C","row":0}],
 "nodes":[{"id":"n1","label":"One","layer":"a","cluster":"c","files":["x.py"]},{"id":"n2","label":"Two","layer":"a","cluster":"c"}],
 "edges":[["n1","n2","calls"]]}
P
sed 's/"n2","calls"/"zz","calls"/' "$T/d.json" > "$T/bad.json"
! node "$R/skills/code-map/scripts/generate.mjs" "$T/bad.json" "$T/b.html" >/dev/null 2>&1 || die code-map-validate
node "$R/skills/code-map/scripts/generate.mjs" "$T/d.json" "$T/m.html" >/dev/null
node -e "
const s=require('fs').readFileSync('$T/m.html','utf8');
if(s.includes('/*__DATA__*/{}'))throw 'marker left';
const js=s.match(/<script>([\s\S]*)<\/script>/)[1];new Function(js);
if(!js.includes('\"id\":\"n1\"'))throw 'data missing'" || die code-map-render
ok code-map

# code-review-graph is required: harvest must use it, and must fail without it
command -v code-review-graph >/dev/null 2>&1 || die "crg-missing"
python3 "$R/scripts/harvest.py" "$F" --out "$T/out2" >/dev/null || die crg
[ "$(python3 -c "import json;print(json.load(open('$T/out2/CAPABILITY_CARD.json'))['ast'].get('backend'))")" = "code-review-graph" ] || die crg-backend
if PATH="/usr/bin:/bin" sh -c 'command -v code-review-graph' >/dev/null 2>&1; then :; else
  PATH="/usr/bin:/bin" "$(command -v python3)" "$R/scripts/harvest.py" "$F" --out "$T/out3" >/dev/null 2>&1 && die crg-should-fail
fi
echo "ok code-review-graph required"

# rea-mcp server, real stdio round trip
sh "$R/mcp/rea-mcp/tests/selftest.sh" > "$T/mcp.out" 2>&1 || { cat "$T/mcp.out"; die rea-mcp; }
python3 -c "import json;assert list(json.load(open('$R/.mcp.json'))['mcpServers'])==['rea-mcp']" || die mcp-json
ok "rea-mcp selftest: $(grep -c '^PASS' "$T/mcp.out") checks"
echo "SELFTEST PASS"
