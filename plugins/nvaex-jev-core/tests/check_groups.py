#!/usr/bin/env python3
"""Fail if groups.json names a skill that no package in the build holds. Usage: check_groups.py GROUPS.json FRANKENSTEIN_ROOT
Exit 0 all found, 1 something missing, 2 the root has no packages (package copied out of the tree)."""
import json, os, re, sys

groups, root = sys.argv[1], sys.argv[2]
have = set()
for top in ("plugins",):
    for d, _, files in os.walk(os.path.join(root, top)):
        if "SKILL.md" in files and any(x == "skills" or x.startswith("skills-") for x in d.split(os.sep)):
            have.add(os.path.basename(d))
            m = re.search(r"^name:\s*(\S+)\s*$", open(os.path.join(d, "SKILL.md"), encoding="utf-8").read(), re.M)
            if m:
                have.add(m.group(1))
if not have:
    print("no packages under " + root)
    sys.exit(2)
missing = sorted({"%s: %s" % (g, s) for g, v in json.load(open(groups))["groups"].items() for s in v["skills"] if s not in have})
print("missing: " + ", ".join(missing) if missing else "all skills found (%d skills in the build)" % len(have))
sys.exit(1 if missing else 0)
