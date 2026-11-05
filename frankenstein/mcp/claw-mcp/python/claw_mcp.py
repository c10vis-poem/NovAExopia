#!/usr/bin/env python3
"""claw-mcp stdio shim (stdlib only). Same 6 tool schemas as the Kotlin server.
Drivers that need the JVM return isError "not-implemented". No daemons."""
import json, os, re, subprocess, sys, urllib.request, html

HERE = os.path.dirname(os.path.abspath(__file__))
NI = "not-implemented in the Python shim: needs the Kotlin JVM server (see README)"
CDP = "http://127.0.0.1:%s" % os.environ.get("CDP_PORT", "9222")
DEVICE_CMDS = {"battery": ["termux-battery-status"], "wifi": ["termux-wifi-connectioninfo"],
               "notify": ["termux-notification"], "adb-devices": ["adb", "devices"]}

def _get(url, headers=None, data=None, timeout=15):
    req = urllib.request.Request(url, data=data, headers=headers or {"User-Agent": "claw-mcp/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def search(a): raise NotImplementedError(NI + " (claw.search provider driver)")

def scrape(a):
    body = _get(a["url"])
    n = a.get("max_chars", 20000)
    if a.get("format", "text") == "html": return body[:n]
    body = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()[:n]

def browser(a):
    act = a.get("action", "version")
    if act == "version": return _get(CDP + "/json/version", timeout=5)
    if act == "tabs":
        return json.dumps([{k: t.get(k) for k in ("id", "title", "url")} for t in json.loads(_get(CDP + "/json/list", timeout=5))])
    raise NotImplementedError(NI + " (CDP websocket action: " + act + ")")

def device(a):
    cmd = DEVICE_CMDS.get(a.get("action"))
    if not cmd: raise ValueError("action must be one of %s" % sorted(DEVICE_CMDS))
    if a["action"] == "notify": cmd = cmd + [str(x) for x in a.get("args", [])]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    return (r.stdout + r.stderr).strip() or "exit %d" % r.returncode

def infer(a):
    key = os.environ.get("OPENROUTER_API_KEY")
    if a.get("provider", "openrouter") != "openrouter" or not key:
        raise NotImplementedError(NI + " (provider driver; shim supports openrouter with OPENROUTER_API_KEY)")
    d = json.dumps({"model": a["model"], "messages": [{"role": "user", "content": a["prompt"]}]}).encode()
    r = json.loads(_get("https://openrouter.ai/api/v1/chat/completions", {"Authorization": "Bearer " + key, "Content-Type": "application/json"}, d, 120))
    return r["choices"][0]["message"]["content"]

def workflows(a):
    path = os.environ.get("CLAW_WORKFLOWS", os.path.join(HERE, "..", "workflows.json"))
    try: wf = json.load(open(path))
    except OSError: wf = {}
    if a.get("action", "list") == "list": return json.dumps(sorted(wf))
    return json.dumps([TOOLS[s["tool"]][2](s.get("arguments", {})) for s in wf[a["name"]]])

def S(**p): return {"type": "object", "properties": {k: {"type": v} for k, v in p.items()}}
def R(s, *req): return dict(s, required=list(req))
TOOLS = {
 "claw.search": ("Web search via a provider driver.", R(S(query="string"), "query"), search),
 "claw.scrape": ("Fetch a URL; return text (or html).", R(S(url="string", format="string", max_chars="integer"), "url"), scrape),
 "claw.browser": ("Phone Chrome over CDP :9222. action: version|tabs (shim); navigate/eval/click need JVM.", S(action="string"), browser),
 "claw.device": ("Android/Termux device: action battery|wifi|notify|adb-devices.", R(S(action="string", args="array"), "action"), device),
 "claw.infer": ("Multi-provider inference (shim: openrouter).", R(S(provider="string", model="string", prompt="string"), "model", "prompt"), infer),
 "claw.workflows": ("action list|run; run needs name. Named tool sequences from workflows.json.", S(action="string", name="string"), workflows),
}

def handle(m):
    meth = m.get("method")
    if m.get("id") is None: return None
    if meth == "initialize":
        return {"protocolVersion": m["params"].get("protocolVersion", "2024-11-05"), "capabilities": {"tools": {}},
                "serverInfo": {"name": "claw-mcp-shim", "version": "0.1.0"}}
    if meth == "ping": return {}
    if meth == "tools/list":
        return {"tools": [{"name": n, "description": d, "inputSchema": s} for n, (d, s, _) in TOOLS.items()]}
    if meth == "tools/call":
        p = m["params"]; t = TOOLS.get(p.get("name"))
        if not t: return {"__err": (-32602, "unknown tool")}
        try: return {"content": [{"type": "text", "text": str(t[2](p.get("arguments") or {}))}]}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": "%s: %s" % (type(e).__name__, e)}]}
    return {"__err": (-32601, "method not found")}

def main():
    for line in sys.stdin:
        if not line.strip(): continue
        try: m = json.loads(line); r = handle(m)
        except Exception as e: m, r = {"id": None}, {"__err": (-32700, str(e))}
        if r is None: continue
        out = {"jsonrpc": "2.0", "id": m.get("id")}
        if "__err" in r: out["error"] = {"code": r["__err"][0], "message": r["__err"][1]}
        else: out["result"] = r
        sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()

if __name__ == "__main__": main()
