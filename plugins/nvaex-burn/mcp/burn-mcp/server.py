#!/usr/bin/env python3
"""burn-mcp: stdlib stdio MCP server for nvaex-burn. Thin: tools run scripts in ../../scripts, which hold the logic.
hook and tick are not tools: hook fires on an event, tick runs jobs and stays an explicit command."""
import json, os, subprocess, sys

NAME, VERSION, PROTO = "burn-mcp", "0.1.0", "2024-11-05"
SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scripts"))


def disabled():
    return subprocess.run(["sh", os.path.join(SCRIPTS, "killswitch.sh"), "nvaex-burn", "mcp"]).returncode == 0


def script(name, *args, stdin=""):
    r = subprocess.run([sys.executable, "-B", "-I", os.path.join(SCRIPTS, name), *args], input=stdin,
                       capture_output=True, text=True, timeout=90)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip() or "%s exit %d" % (name, r.returncode))
    return r.stdout.strip()


def keepalive(a):
    return {"result": script("burn.py", "keepalive", "--once")}  # one ping; the looping form would hang the server


def notify(a):
    return {"result": script("burn.py", "notify", a["message"])}


S = {"type": "string"}
TOOLS = {
    "burn.status": (lambda a: json.loads(script("burn.py", "status")),
                    "Usage pacer mode (unknown, brake, burn or idle) and why. Read-only.", {}, []),
    "burn.keepalive": (keepalive, "One prompt-cache keep-alive ping, sent only if a prompt was seen in the last 30 minutes.", {}, []),
    "burn.notify": (notify, "Send a message to the operator's webhook (BURN_WEBHOOK_URL). Off unless that is set.", {"message": S}, ["message"]),
    "ag.cloud_dispatch": (lambda a: json.loads(script("cloud_dispatch.py", stdin=json.dumps(a))),
                          "Write a job file for cloud work. Only POSTs if AG_BRIDGE_URL is set AND send=true.",
                          {"job": S, "payload": {"type": "object"}, "target": S, "send": {"type": "boolean"}}, ["job"]),
}


def handle(m):
    meth, i = m.get("method"), m.get("id")
    if i is None: return None  # notification
    if meth == "initialize":
        r = {"protocolVersion": PROTO, "capabilities": {"tools": {}}, "serverInfo": {"name": NAME, "version": VERSION}}
    elif meth == "tools/list":
        r = {"tools": [{"name": n, "description": d, "inputSchema": {"type": "object", "properties": p, "required": q}}
                       for n, (_, d, p, q) in TOOLS.items()]}
    elif meth == "tools/call":
        p = m.get("params") or {}
        t = TOOLS.get(p.get("name"))
        if not t: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32602, "message": "unknown tool"}}
        try:
            if disabled():
                res, err = {"disabled": "kill switch active (~/.nvaex-hooks-off, ~/.claude/state/off/nvaex-burn or nvaex-burn.mcp); remove to revoke"}, False
            else:
                res, err = t[0](p.get("arguments") or {}), False
        except Exception as e:
            res, err = {"error": "%s: %s" % (type(e).__name__, e)}, True
        r = {"content": [{"type": "text", "text": json.dumps(res)}], "isError": err}
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
