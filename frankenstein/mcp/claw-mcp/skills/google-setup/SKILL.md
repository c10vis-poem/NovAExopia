---
disable-model-invocation: true
name: google-setup
description: Set up, add or re-authorize a Google account for claw-mcp. Use on no credentials, Insufficient Permission, bad token.
---

# google-setup (setup, add account, reauth: one skill)

claw-mcp reads one token file per account: `$CLAW_GOOGLE_DIR/google-<account>.json` (default `~/.config/claw-mcp`), mode 600, holding `{client_id, client_secret, refresh_token}`. This skill gets that file made. No MCP server, no Node project, no Docker.

## What only the operator can do (once per Google Cloud project)
1. In console.cloud.google.com make or pick a project. Enable the Google Drive API, Gmail API and Google Calendar API.
2. Configure the OAuth consent screen (External). While the app is in Testing, add every Google address you will connect as a test user. Testing-mode refresh tokens expire after 7 days; publish the app (or accept re-running login weekly) to avoid that.
3. Credentials, Create credentials, OAuth client ID, type **Desktop app**. Download the JSON. Keep it outside any repo (for example `~/.config/claw-mcp/client_secret.json`, chmod 600).
4. For each account, approve the consent screen in the phone's browser when the script asks. Google shows an "unverified app" warning for your own app; choose Advanced, continue.

The agent cannot do these clicks and must not ask for the client secret or any token in chat.

## Commands (path relative to this skill)
- See what exists, values never shown: `python3 -I scripts/google_oauth.py check`
- Add an account, or reauth one (same command; it replaces the file):
  `python3 -I scripts/google_oauth.py login <account> --client-file ~/.config/claw-mcp/client_secret.json`
  It prints a consent URL (public client id only), opens it with `termux-open-url` when present (`--no-browser` to skip), waits up to 5 minutes on `127.0.0.1`, exchanges the code, writes the file with mode 600.
- Scopes default to read Drive + create Drive files, read Gmail + create drafts, Calendar. Narrow with `--scopes drive,gmail,calendar`.
- Client from env instead of a file: `CLAW_GOOGLE_CLIENT_ID`, `CLAW_GOOGLE_CLIENT_SECRET`.

## When to reauth
- Error "Insufficient Permission": the token was minted without the scope; rerun login.
- "token refresh failed ... invalid_grant": revoked, expired (Testing mode, 7 days) or password changed; rerun login.
- `check` shows "REFUSED by claw": `chmod 600` the file.
- No refresh_token returned: revoke the app at myaccount.google.com/permissions and log in again.

## Safety
Never print, paste, commit or log token files or the client secret. Both accounts use the same client and different `<account>` names. Test the result with a read call, for example `claw.device action=google service=calendar op=calendars account=<account>` (a read; nothing is written).
