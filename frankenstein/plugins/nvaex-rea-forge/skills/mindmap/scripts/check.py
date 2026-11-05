#!/usr/bin/env python3
"""Validate a Markmap .md: frontmatter, exactly one H1, 1+ H2 branches, depth <= 5, labels short."""
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
e = []
m = re.match(r"---\n(.*?)\n---\n", t, re.S)
if not m or "title:" not in m.group(1): e.append("missing frontmatter title")
body = t[m.end():] if m else t
if len(re.findall(r"(?m)^# ", body)) != 1: e.append("need exactly one H1")
if not re.search(r"(?m)^## ", body): e.append("no ## branches")
for l in body.splitlines():
    b = re.match(r"(\s*)- (.*)", l)
    if b and len(b.group(1)) // 2 > 4: e.append("too deep: " + l.strip()[:30])
    if len((b.group(2) if b else l.lstrip("# ")).split()) > 12: e.append("label too long: " + l.strip()[:30])
print("\n".join(e) or "ok"); sys.exit(1 if e else 0)
