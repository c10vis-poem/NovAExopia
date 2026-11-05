#!/usr/bin/env bash
# Expose a local MCP server through a Cloudflare named tunnel. No Docker.
#   tunnel.sh check [PORT]   report cloudflared, cf, token env, and whether PORT answers locally (never prints the token)
#   tunnel.sh run PORT       run cloudflared in the foreground with the token from env TUNNEL_TOKEN; Ctrl-C ends it
# The public hostname -> http://localhost:PORT mapping is set on the tunnel in the Cloudflare dashboard (operator side).
set -u
c=${1:-}; port=${2:-}
have_cfd=0; command -v cloudflared >/dev/null && have_cfd=1
if [ "$c" = check ]; then
  echo "cloudflared: $( [ $have_cfd = 1 ] && command -v cloudflared || echo MISSING)"
  echo "cf (Cloudflare CLI, manages tunnels but cannot carry traffic): $(command -v cf || echo missing)"
  echo "TUNNEL_TOKEN: $( [ -n "${TUNNEL_TOKEN:-}" ] && echo set || echo NOT SET)"
  if [ -n "$port" ]; then
    if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then echo "127.0.0.1:$port: accepting connections"; else echo "127.0.0.1:$port: nothing listening"; fi
  fi
  [ $have_cfd = 1 ] || { echo "STOP: cloudflared is not installed. Installing it is the operator's call; this skill does not install."; exit 3; }
  exit 0
fi
if [ "$c" = run ]; then
  [ $have_cfd = 1 ] || { echo "STOP: cloudflared is not installed. Installing it is the operator's call."; exit 3; }
  [ -n "${TUNNEL_TOKEN:-}" ] || { echo "STOP: set TUNNEL_TOKEN in the environment (never on the command line)."; exit 3; }
  case "$port" in ''|*[!0-9]*) echo "usage: tunnel.sh run PORT" >&2; exit 2;; esac
  (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null || { echo "STOP: nothing is listening on 127.0.0.1:$port; start the MCP server first."; exit 4; }
  exec cloudflared tunnel --no-autoupdate run
fi
echo "usage: tunnel.sh check [PORT] | run PORT" >&2; exit 2
