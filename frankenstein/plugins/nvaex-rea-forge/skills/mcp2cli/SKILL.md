---
name: mcp2cli
description: Turn an MCP stdio server into a shell CLI plus a small SKILL.md to save context. Use for rarely used stateless servers.
---
# mcp2cli (trimmed from mcp2cli by mason)

**Generate:** `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp2cli.py gen <name> <outdir> <server cmd...>` introspects the server over stdio (`tools/list`), writes the shim `<outdir>/<name>` and `<outdir>/SKILL.md`. Installing the shim on PATH is the operator's call.
**Try:** `mcp2cli.py tools <cmd...>`, `mcp2cli.py call <cmd...> -- <tool> key=value`.

**Convert only if** the tools are stateless request/response with text or JSON output (local system tools, SaaS API wrappers, DB queries, search, doc/media processing, proxies to a remote API). For infra servers that wrap an existing CLI, point a SKILL.md at that CLI instead.
**Keep as MCP if** it holds session state (browser automation, REPL, auth redirects, memory graphs), streams, aggregates other MCP servers, or structures the model's own reasoning.
**Partial:** extract the stateless reads as CLI, keep the stateful tools in MCP.

Generated SKILL.md must not mention MCP, keep one example per command, and name the env vars used for auth. Source of the server's code is not rewritten: the shim talks to the server as is, so any server dependency stays.
