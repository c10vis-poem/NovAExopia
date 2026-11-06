#!/usr/bin/env sh
# Real stdio round trip against rea-mcp, on a fixture repo. Exit 0 only if every check passes.
D=$(cd "$(dirname "$0")/.." && pwd); T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
F="$T/fork"; mkdir -p "$F/.git" "$F/src"; echo 'ref: refs/heads/main' > "$F/.git/HEAD"
echo '# Fixture repo' > "$F/README.md"; echo '{}' > "$F/package.json"; echo 'x=1' > "$F/src/cli.py"; echo 'y=2' > "$F/src/util.py"; echo 'K=v' > "$F/.env"
B=$(cd "$F" && find . -type f | sort | xargs cat | cksum)
python3 -I - "$D/server.py" "$F" "$T/missing" <<'PY' || exit 1
import json, subprocess, sys
srv, fork, missing = sys.argv[1:4]
msgs = [{"id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
        {"method": "notifications/initialized"},
        {"id": 2, "method": "tools/list"},
        {"id": 3, "method": "tools/call", "params": {"name": "rea.inspect_target", "arguments": {"path": fork}}},
        {"id": 4, "method": "tools/call", "params": {"name": "rea.inspect_target", "arguments": {"path": missing}}},
        {"id": 5, "method": "tools/call", "params": {"name": "jev.route_task", "arguments": {"task": "x"}}}]
out = subprocess.run([sys.executable, "-I", srv], input="".join(json.dumps({"jsonrpc": "2.0", **m}) + "\n" for m in msgs), capture_output=True, text=True, timeout=30)
r = {j["id"]: j for j in map(json.loads, out.stdout.splitlines())}
txt = lambda i: json.loads(r[i]["result"]["content"][0]["text"])
good = []
def chk(n, c): good.append(c); print(("PASS " if c else "FAIL ") + n)
chk("initialize", r[1]["result"]["serverInfo"]["name"] == "rea-mcp")
chk("tools/list: rea.inspect_target only", [t["name"] for t in r[2]["result"]["tools"]] == ["rea.inspect_target"])
i = txt(3)
chk("inspect: counts files, finds manifest and entrypoint", i["files_scanned"] == 5 and i["manifests"] == ["package.json"] and i["entrypoints"] == ["src/cli.py"])
chk("inspect: flags .env, reads git HEAD and README, skips .git", i["sensitive_looking_files"] == [".env"] and i["git_head"] == "ref: refs/heads/main" and "Fixture" in i["readme_head"] and i["read_only"] is True)
chk("inspect: a missing folder reports the error", "not a directory" in txt(4)["error"])
chk("unknown tool refused", r[5]["error"]["code"] == -32602)
sys.exit(0 if all(good) else 1)
PY
[ "$B" = "$(cd "$F" && find . -type f | sort | xargs cat | cksum)" ] && echo "PASS target unchanged" || { echo "FAIL target changed"; exit 1; }
grep -q 'os.walk' "$D/server.py" && { echo "FAIL logic copied into server"; exit 1; } || echo "PASS logic only in scripts/inspect_target.py"
echo "SELFTEST OK"
