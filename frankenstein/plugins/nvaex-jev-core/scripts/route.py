#!/usr/bin/env python3
"""UserPromptSubmit: time, Stage-0 garble flags, Stage-1 router, project decisions and rules. Non-blocking, stdlib."""
import datetime, glob, json, os, re, sys
sys.dont_write_bytecode = True
import jev_route
d = json.load(sys.stdin)
p = (d.get("prompt") or "").strip()
if not p or "#skip-enforce" in p or p.startswith("/"):
    sys.exit(0)
cwd = d.get("cwd") or os.getcwd()
low = p.lower()
words = set(re.findall(r"[a-z0-9]+", low))
out = ["Now: " + datetime.datetime.now().astimezone().strftime("%a %Y-%m-%d %H:%M %Z (UTC%z)") + ". Anchor relative time to this."]

# Stage 0: STT/layout garble signals; code, paths, URLs and @mentions are kept out of the check.
spoken = re.sub(r"```.*?```|`[^`]*`|\S*[/@]\S*|https?://\S+", " ", p, flags=re.S)
SOUNDALIKE = r"\b(agente|dumas|dumb ass|jane|sea eye|pee are|sever|stagging|ingratiation)\b"
OK = {"html", "tmux", "grpc", "xhtml", "dbms"}
junk = [w for w in re.findall(r"[A-Za-z]{4,}", spoken) if not re.search(r"[aeiouy]", w.lower()) and w.lower() not in OK]
flags = [m.group(0) for m in re.finditer(SOUNDALIKE, spoken, re.I)] + junk[:3]
if flags and len(spoken.split()) >= 4:
    out.append("STAGE-0: possible garbled input (" + ", ".join(flags[:5]) +
               "). Apply the drunken-master skill: your first text, before any tool call, is a 'Read as: ...' line.")

# Stage 1: jev_route.classify: TypeSafe Jev, or the keyword rules when Jev is unavailable. The line always names which.
R = jev_route.classify(p)
lvl, top = R["level"], R["groups"]
tier_s = f" | tier {R['tier']['model']}" if R["tier"] else ""
if R["source"] == "typesafe":
    c = R["confidence"]
    via = f"via typesafe {R['jev_model']} conf {c['level']:.2f}/{c['group']:.2f}" + (" LOW: check it" if R["gated"] == "escalate" else "")
else:
    via = f"via local-fallback ({R['error']})" + (" CONFIG FAULT: fix the Jev key or request, this is not Jev being unsure" if R["config_fault"] else "")
gates = " | L2+: run the task-auditor gates" if lvl >= 2 else ""
if top or R["skills"]:
    out.append(f"JEV route: L{lvl}{tier_s} | groups {'/'.join(top) or 'none'} | try {', '.join(R['skills'])}{gates} | {via}")
else:
    out.append(f"JEV route: L{lvl}{tier_s} | no group matched{gates} | {via}")

# Decision ledger (<project>/.nvaex/decisions.jsonl, ~/.nvaex/decisions.jsonl): inject matches, flag contradictions.
def jl(path):
    try:
        return [json.loads(x) for x in open(path) if x.strip()]
    except Exception:
        return []
lines, budget = [], 400
for D in jl(os.path.join(cwd, ".nvaex/decisions.jsonl")) + jl(os.path.expanduser("~/.nvaex/decisions.jsonl")):
    if not isinstance(D, dict) or D.get("status", "active") != "active" or not D.get("decision"):
        continue
    rej = [r for r in D.get("rejected", []) if re.search(r"\b" + re.escape(str(r).lower()) + r"\b", low)]
    tagged = words & {str(t).lower() for t in D.get("tags", [])}
    if not (rej or tagged):
        continue
    s = (f"CONTRADICTION? prompt mentions rejected option '{rej[0]}'. Decided: {D['decision']}" if rej else
         f"Decided: {D['decision']}" + (f" (not {', '.join(map(str, D['rejected'][:3]))})" if D.get("rejected") else ""))
    if budget - len(s) < 0:
        break
    budget -= len(s)
    lines.append(s)
if lines:
    out.append("DECISIONS: " + " | ".join(lines))

# Rule files (<project>/.nvaex/rules/*.md, first line "keywords: a, b"): inject the ones the prompt matches.
budget = 1600
for f in sorted(glob.glob(os.path.join(cwd, ".nvaex/rules/*.md"))):
    try:
        head, _, body = open(f).read().partition("\n")
    except Exception:
        continue
    kw = {k.strip().lower() for k in head.split(":", 1)[1].split(",")} if head.lower().startswith("keywords:") else set()
    if kw & words and len(body) <= budget:
        budget -= len(body)
        out.append(f"RULE {os.path.basename(f)}: " + body.strip())

print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "\n".join(out)}}))
