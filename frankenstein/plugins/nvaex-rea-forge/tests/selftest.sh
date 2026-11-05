#!/usr/bin/env sh
# nvaex-rea-forge selftest: harvest a fixture, wrap its CLI, run it, sync round trip.
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
ok() { echo "PASS $1"; }; die() { echo "FAIL $1"; exit 1; }
python3 -c "import json;json.load(open('$R/.claude-plugin/plugin.json'))" && ok plugin.json
# fixture fork
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
git init -q . && git add -A && git -c user.email=a@b -c user.name=t commit -qm base
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
OUT=$(sh "$T/out/wrap/fork" 7); [ "$OUT" = "91" ] || die "wrapped CLI ($OUT)"; ok wrap-runs
grep -q '^name:' "$T/out/wrap/SKILL.md" && ok wrap-skill
# sync round trip: local mod -> save -> reset -> apply
echo "# mine" >> cli.py; git -c user.email=a@b -c user.name=t commit -qam mod
(cd "$T" && python3 "$R/scripts/sync.py" save "$F" HEAD~1 >/dev/null)
git reset -q --hard HEAD~1
python3 "$R/scripts/sync.py" check "$F" "$T/patches" >/dev/null || die sync-check
python3 "$R/scripts/sync.py" apply "$F" "$T/patches" >/dev/null || die sync-apply
grep -q '# mine' cli.py && ok sync-roundtrip
# optional code-review-graph backend
if command -v code-review-graph >/dev/null 2>&1; then
  python3 "$R/scripts/harvest.py" "$F" --out "$T/out2" --crg >/dev/null
  python3 -c "import json;print('INFO crg backend:',json.load(open('$T/out2/CAPABILITY_CARD.json'))['ast'].get('backend'))"
fi
node "$R/skills/code-map/scripts/generate.mjs" 2>&1 | head -1 | grep -qi "usage\|data" && ok code-map-loads || echo "INFO code-map generator not exercised"
echo "SELFTEST PASS"
