#!/usr/bin/env sh
# One real request to api.typesafe.ai through the real client. Needs TYPESAFE_API_KEY. Not part of selftest. Costs a fraction of a cent.
# Exit 0 only if the answer came from TypeSafe. Prints the routing result, never the key.
R="$(cd "$(dirname "$0")/.." && pwd)"
[ -n "$TYPESAFE_API_KEY$CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY" ] || { echo "LIVE SKIPPED: no TYPESAFE_API_KEY"; exit 2; }
unset TYPESAFE_BASE_URL
JEV_TIMEOUT="${JEV_TIMEOUT:-6}" python3 -I "$R/scripts/jev_route.py" "${1:-fix the failing login test and then review the diff}" | python3 -I -c '
import json, sys
r = json.load(sys.stdin)
print(json.dumps({k: r.get(k) for k in ("source", "error", "level", "groups", "tier", "skills", "jev_model", "confidence", "gated", "usage", "ms")}, indent=1))
print("LIVE PASS" if r["source"] == "typesafe" else "LIVE FAIL")
sys.exit(0 if r["source"] == "typesafe" else 1)'
