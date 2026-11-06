#!/usr/bin/env sh
# Each check says what proved it: [real] = the real thing on this phone, [fake] = a fake written for the test; bare PASS lines in check.mjs are the older
# browser/search suite, which runs against tests/fake-cdp.mjs. CLAW_LIVE=1 adds tests/live.mjs (real network, read-only).
# Leaves nothing running: all fakes die with this script; the adb binary is stubbed so no adb server can start; state goes in a temp dir.
# NOT covered, listed again at the end: a real adbd, real phone Chrome, a real Aesc daemon, real Google.
D="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"
node "$D/tests/fake-cdp.mjs" > "$T/port" & FP=$!
trap 'kill $FP 2>/dev/null; rm -rf "$T"' EXIT
i=0; while [ ! -s "$T/port" ] && [ $i -lt 50 ]; do sleep 0.1; i=$((i+1)); done
export FAKE="http://127.0.0.1:$(cat "$T/port")" CDP_PORT="$(cat "$T/port")"
export CLAW_SEARCH_URL="$FAKE/search" CLAW_OPENROUTER_URL="$FAKE/infer" OPENROUTER_API_KEY=k
export CLAW_LISTEN=off CLAW_STATE_DIR="$T/state"
REAL_TERMUX_API=""; command -v termux-battery-status >/dev/null 2>&1 && REAL_TERMUX_API=1; export REAL_TERMUX_API
export REALPATH="$PATH"
mkdir -p "$T/bin"
printf '#!/bin/sh\necho "STUB:$0 $*"\n' > "$T/bin/termux-toast"
cat > "$T/bin/adb" <<'STUB'
#!/bin/sh
if [ "$1" = devices ]; then echo "List of devices attached"; [ -n "$ADB_STUB_DEVICES" ] && printf '%b\n' "$ADB_STUB_DEVICES"; exit 0; fi
echo "STUBADB $*"
STUB
chmod +x "$T/bin/termux-toast" "$T/bin/adb"
export STUBPATH="$T/bin"
rc=0
node "$D/tests/check.mjs" "$D" "$T" </dev/null || rc=1
node "$D/tests/check2.mjs" "$D" "$T" </dev/null || rc=1
python3 -I "$D/tests/google_oauth_fake.py" >/dev/null && echo "PASS google-setup: fake OAuth flow" || { echo "FAIL google-setup fake OAuth flow"; rc=1; }
# skills imported from a private folder: frontmatter intact, nothing private in a public repo
for n in android-termux-operator termux-helper; do
  f="$D/skills/$n"
  if head -3 "$f/SKILL.md" | grep -q "^name: $n$" && ! grep -rqiE 'razr|motorola|NovAEx|u0_a[0-9]|obs 00[0-9]|~/(repos|bin|tools|models|\.claude)|Documents/' "$f"; then echo "PASS [real] skill $n: frontmatter, no private paths"; else echo "FAIL skill $n"; rc=1; fi
done
# kill switch
mkdir -p "$T/h/.claude/state/off"; : > "$T/h/.claude/state/off/claw-mcp"
o="$(echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | HOME="$T/h" sh "$D/bin/claw-mcp")"; krc=$?
if [ -z "$o" ] && [ $krc -eq 0 ]; then echo "PASS [real] kill switch silences server"; else echo "FAIL kill switch silences server"; rc=1; fi
if [ -n "$CLAW_LIVE" ]; then
  env -u CLAW_SEARCH_URL -u CLAW_OPENROUTER_URL -u OPENROUTER_API_KEY node "$D/tests/live.mjs" "$D" </dev/null || rc=1
else echo "SKIPPED live network checks (set CLAW_LIVE=1)"; fi
echo "UNTESTED real adbd (phone not paired; the client has only met tests/fake-adbd.mjs)"
echo "UNTESTED real phone Chrome over CDP (only tests/fake-cdp.mjs)"
echo "UNTESTED real Aesc daemon (only a fake peer on the real socket)"
echo "UNTESTED real Google APIs (no credentials; only tests/fake-services.mjs)"
[ $rc -eq 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"; exit $rc
