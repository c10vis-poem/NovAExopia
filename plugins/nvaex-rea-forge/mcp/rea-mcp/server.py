#!/usr/bin/env python3
"""rea-mcp: stdlib stdio MCP server for nvaex-rea-forge. Thin: tools run scripts in ../../scripts, which hold the logic."""
import json, os, subprocess, sys

NAME, VERSION, PROTO = "rea-mcp", "0.1.0", "2024-11-05"
SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scripts"))


def script(name, *args):
    r = subprocess.run([sys.executable, "-B", "-I", os.path.join(SCRIPTS, name), *args],
                       capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "%s exit %d" % (name, r.returncode))
    return json.loads(r.stdout)


TOOLS = {
    "rea.inspect_target": (lambda a: script("inspect_target.py", a["path"]),
                           "Read-only inspection of a repo/dir: extensions, manifests, entrypoints, sensitive-looking files.",
                           {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
}


def handle(m):
    meth, i = m.get("method"), m.get("id")
    if i is None: return None  # notification
    if meth == "initialize":
        r = {"protocolVersion": PROTO, "capabilities": {"tools": {}}, "serverInfo": {"name": NAME, "version": VERSION}}
    elif meth == "tools/list":
        r = {"tools": [{"name": n, "description": d, "inputSchema": s} for n, (_, d, s) in TOOLS.items()]}
    elif meth == "tools/call":
        p = m.get("params") or {}
        t = TOOLS.get(p.get("name"))
        if not t: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32602, "message": "unknown tool"}}
        try:
            res, err = t[0](p.get("arguments") or {}), False
        except Exception as e:
            res, err = {"error": "%s: %s" % (type(e).__name__, e)}, True
        r = {"content": [{"type": "text", "text": json.dumps(res, indent=1)}], "isError": err}
    elif meth == "ping": r = {}
    else: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": i, "result": r}


def main():
    for line in sys.stdin:
        if not line.strip(): continue
        try: out = handle(json.loads(line))
        except json.JSONDecodeError: out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        if out: sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()


if __name__ == "__main__": main()
