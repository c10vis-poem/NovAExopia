# webview

A Claude Code plugin that lets an agent drive the operator's own Chrome on this Android phone, with the logged-in sessions already in it. It is plain chrome-devtools-mcp from the [c10vis-poem fork](https://github.com/c10vis-poem/NvAEx-chrome-devtools-mcp), pointed at Chrome's DevTools socket through `adb forward`. Any MCP client (Hermes, a Gemini driver, a wiki corpus agent) can use the same server by running `bin/webview-mcp`.

## How it connects

Chrome on Android exposes the Chrome DevTools Protocol (CDP, the wire protocol every browser agent uses) on the abstract socket `chrome_devtools_remote`. Android blocks normal apps, Termux included, from opening that socket: a direct `socat ABSTRACT-CONNECT:chrome_devtools_remote` from Termux gets `Permission denied`. Only the shell user can reach it, which means adb. So:

```
agent -> webview MCP (bin/webview-mcp) -> http://127.0.0.1:9222
      -> adb forward tcp:9222 localabstract:chrome_devtools_remote -> Chrome
```

## One-time setup

1. Build the fork (from the fork, never npm):
   ```sh
   gh repo sync c10vis-poem/NvAEx-chrome-devtools-mcp
   cd ~/repos/NvAEx-chrome-devtools-mcp && git pull
   PUPPETEER_SKIP_DOWNLOAD=1 npm ci
   node node_modules/typescript/bin/tsc6    # see note below
   node scripts/post-build.ts
   ```
   `npm run build` fails on Termux: it calls `tsc` from TypeScript 7, whose native binary has no Android build. The bundled TypeScript 6 compiler (`tsc6`) emits the same output; it reports a few type errors and still writes `build/`.
2. Pair adb with the phone itself (wireless debugging over loopback):
   - Settings > About phone > tap Build number 7 times (if Developer options is hidden).
   - Settings > Developer options > Wireless debugging: ON.
   - Tap "Pair device with pairing code". Keep that dialog open in split screen with Termux and run `adb pair 127.0.0.1:<pairing port> <code>`.
   - Back on the Wireless debugging screen, note "IP address & Port" and run `bash bin/webview-connect --adb 127.0.0.1:<port>`.

The connect port changes each time wireless debugging restarts, and Android turns it off when Wi-Fi drops. Pairing survives; only step 2's last line repeats.

## Use

```sh
bash bin/webview-connect          # forward + print Chrome's /json/version
bash bin/webview-connect --list   # other DevTools sockets (WebView apps)
```

Install the plugin locally: `claude --plugin-dir ~/repos/NovAExopia/mcp_connectors/webview`. A marketplace entry comes later. The `webview` skill tells the agent the work loop.

Settings (environment): `CHROME_DEVTOOLS_MCP_DIR` (fork path, default `~/repos/NvAEx-chrome-devtools-mcp`), `CDP_PORT` (9222), `CDP_SOCKET` (`chrome_devtools_remote`), `ADB_SERIAL`.

## Other MCP clients

Any stdio MCP client can run the same server. Generic config (replace the path):

```json
{
  "mcpServers": {
    "webview": {
      "command": "bash",
      "args": ["/path/to/mcp_connectors/webview/bin/webview-mcp"]
    }
  }
}
```

`bin/webview-mcp` prints the link status to stderr, never stdout.

## Not yet

- Headless or own-Chromium mode for the Hyperion-XI and AEthX-AEsc app WebViews. Their sockets are named `webview_devtools_remote_<pid>`; `bin/webview-connect --list` shows them, but the pid changes per launch and nothing maps it to `CDP_SOCKET` yet.
- A search tool.
- A marketplace entry (pending the marketplace branch).

## Limits

- Chrome must be running on the phone for the socket to exist.
- Some chrome-devtools-mcp tools assume desktop Chrome (extensions, PWA install, performance traces) and may fail against Android Chrome.
