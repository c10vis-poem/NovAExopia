---
disable-model-invocation: true
name: mcp-tunnel
description: Expose a local MCP server on this phone to the internet through a Cloudflare named tunnel, without Docker. Use when a remote client must reach an MCP server hosted here. Stops with a plain message if cloudflared or the token is missing.
---

# mcp-tunnel

Our own MCP servers run on the phone (for example claw-mcp). To reach one from outside, a Cloudflare tunnel connector (`cloudflared`) carries traffic from a public hostname to `http://localhost:PORT`. No Docker, no Compose.

## Check first, stop if it fails
`bash scripts/tunnel.sh check 8787` (path relative to this skill; use the real port).
- `cloudflared: MISSING` means stop. As of 2026-11-05 it is NOT on this phone. The `cf` command that is installed is Cloudflare's API CLI: it can create and list tunnels but cannot carry traffic. Tell the operator and wait; do not install anything.
- `TUNNEL_TOKEN: NOT SET` means stop. The token comes from the operator's environment only; never ask for it in chat, never put it in a file or argument, never echo it.
- `nothing listening` means start the MCP server on that port first (it must speak HTTP, not stdio-only).

## Operator side (once, in the Cloudflare dashboard)
Zero Trust, Networks, Tunnels, create a tunnel, copy its token into the shell environment as `TUNNEL_TOKEN`. Add a public hostname pointing at `http://localhost:PORT`. Protect it with an Access policy; an open MCP endpoint is an open door to the tools behind it.

## Run
`bash scripts/tunnel.sh run 8787` runs `cloudflared` in the foreground, reading the token from the environment. Ctrl-C ends it. Do not background it and do not leave it running after the job. Report the hostname the operator configured, not the token.

Not covered: Anthropic's managed MCP tunnel (needs Docker and its own console steps).
