# Rule 8 refuses read-only listing of protected folders (contract A, task 2b)

Found 2026-11-12 16:19 and 16:31 (session b3e21f66). The owner applies this: the plugin is protected.

## What happens
- `find ~/repos/NvAEx-Recaps/contracts -name "*.md"` was refused ("Protected: the command touches ...").
- `grep -n ... ~/repos/Aesop-Xi/plugins/aesops-enforcements/lib/contract.py` was refused the same way.
- RULES.md section 1 allows `ls`, `find` (without -delete or -exec) and `wc` in negotiation, and the Read tool may
  read these same files. So a read-only listing is refused while reading the files is allowed.

## Root cause
`lib/contract.py` `protection()`, lines 711-720: for every Bash command, any protected path in the command text
(line 715-717) or any path-like token under a protected path (line 718-720) is refused. The check does not look
at whether the command only reads.

## Patch (for the owner)
```python
READONLY_BASH = re.compile(r"^(ls|find|wc|grep|stat|diff|cmp|du|file)\s")

def protection(sid, tool, ti):
    ...
    if tool == "Bash" or tool.startswith("mcp__"):
        cmd = ti.get("command", "") if tool == "Bash" else json.dumps(ti)
        if SECRET_BASH.search(cmd):
            return "Protected: this command prints secrets or skips or reroutes git hooks."
        readonly = (tool == "Bash" and READONLY_BASH.match(cmd.strip()) and not SHELL_OPS.search(cmd)
                    and not RECON_UNSAFE.search(cmd))
        if not readonly:
            for d in protected_paths(sid):            # unchanged from here
                ...
```
Read-only means: one of those programs, no `| ; & < > $(` (SHELL_OPS), and no `find -delete/-exec/...`
(RECON_UNSAFE). SECRET_BASH still runs first, so secret files stay unprintable. Nothing becomes writable.

## Tests to add (tests for protection)
1. `find <PLUGIN_ROOT> -name "*.md"`: allowed.
2. `grep -n parse <PLUGIN_ROOT>/lib/contract.py`: allowed.
3. `find <PLUGIN_ROOT> -delete`: refused.
4. `ls <PLUGIN_ROOT> > /tmp/x`: refused (redirect).
5. `rm <PLUGIN_ROOT>/RULES.md`, `sed -i ... <PLUGIN_ROOT>/RULES.md`: refused.
6. `grep KEY ~/.env`-style secret reads: still refused by SECRET_BASH.
Live check: in a new session, the two commands above run.

## Also found while reading contract.py (contract format, not code bugs; for the RULES.md review)
- `REQUIRE Check: <value>` runs the value as a shell command (lines 924-935, shell=True, cwd = root, 15 s
  timeout). RULES.md section 3 lists `Check` without saying so. A sentence there can never pass.
- `SCOPE Bash: <value>` matches the command itself or the value followed by a space (line 839). A folder path
  in a Bash scope never matches a file inside it. RULES.md section 3 says "path folder, command prefix"; the
  path-folder form works only for Read, Write, Edit, Glob, Grep and NotebookEdit.
