---
name: google-access
description: Read Drive, Gmail and Calendar for either Google account via claw.device (action=google) or rclone. Use when a task needs the operator's Google data.
---
Design from google-multi-account 0.7.0 (one `account` parameter per call), reduced to REST. Writes: only Drive create, Gmail draft, Calendar create, each with `confirm=true`; nothing sends, deletes or shares.

`claw.device action=google service=drive|gmail|calendar [op=..] account=<name> [query=..] [id=..]`. Ops: drive list|get|read|create; gmail list|get|thread|labels|draft; calendar list|get|calendars|create. Credentials: `$CLAW_GOOGLE_DIR/google-<account>.json` (default `~/.config/claw-mcp`), mode 600, `{client_id, client_secret, refresh_token}`, created by hand, never in a repo. Output is redacted of token values. Proven only against a fake server: no credentials are on this phone, so real Google is untested.

rclone (read-only: lsjson, cat, lsf, about, listremotes): remotes on the phone as of 2026-11-05: `biz:` only.

Why the stock plugin's MCP fails here: its `.mcp.json` runs `/bin/bash ${HOME}/.google-multi-mcp/start.sh`. Termux has no `/bin/bash`, and `~/.google-multi-mcp/` was never installed (checked both). The "ENOENT stdio" text in the error is the harness's wording; the config on disk names `/bin/bash`.

Getting the token files: claw has no OAuth flow of its own. The `nvaex-ops` skill `google-setup` ships `scripts/google_oauth.py` (loopback OAuth for a Desktop-app client; `check` lists token files without values; rerunning `login <account>` is the reauth). Operator steps: create the Google Cloud project and Desktop OAuth client once, approve the consent screen per account.
