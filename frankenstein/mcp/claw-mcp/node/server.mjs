// claw-mcp: Node stdio MCP server, built-ins only. Newline-delimited JSON-RPC.
import { createInterface } from "node:readline";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { browser } from "./cdp.mjs";
import { search, scrape, device, infer } from "./drivers.mjs";
import { startListener } from "./listener.mjs";
import { redact, render, renderError } from "./wire.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const S = (p, req = []) => ({ type: "object", properties: p, required: req });
const str = { type: "string" };
async function workflows(a) {
  let wf = {}; try { wf = JSON.parse(readFileSync(process.env.CLAW_WORKFLOWS || join(HERE, "..", "workflows.json"), "utf8")); } catch {}
  if ((a.action || "list") === "list") return JSON.stringify(Object.keys(wf).sort());
  if (!wf[a.name]) throw new Error("unknown workflow " + a.name);
  const res = [];
  for (const st of wf[a.name]) {
    const r = await TOOLS[st.tool].run(st.arguments || {});
    if (r && r.choice) return { text: JSON.stringify([...res, r.text ?? ""]), choice: r.choice }; // an operator pick pauses the sequence
    res.push(r);
  }
  return JSON.stringify(res);
}
export const TOOLS = {
  "claw.search": { d: "Web search, keyless provider. Returns JSON [{title,url,snippet}]; errors clearly if blocked.", s: S({ query: str, limit: { type: "integer" } }, ["query"]), run: search },
  "claw.scrape": { d: "action fetch (default): URL to Markdown (format=html for raw). crawl: bounded, polite, same-origin by default, honours robots.txt; returns JSON pages (max_pages 10/200, max_depth 2/5, delay_ms 1000/min 250, deadline_ms, same_origin, include, exclude, respect_robots). map: same crawl, URLs only. video: metadata + transcript from captions (lang, timestamps, metadata_only). A trailing CHOICE: line means the operator must pick.", s: S({ url: str, action: str, format: str, max_chars: { type: "integer" }, max_pages: { type: "integer" }, max_depth: { type: "integer" }, delay_ms: { type: "integer" }, deadline_ms: { type: "integer" }, same_origin: { type: "boolean" }, respect_robots: { type: "boolean" }, include: str, exclude: str, lang: str, timestamps: { type: "boolean" }, metadata_only: { type: "boolean" } }, ["url"]), run: scrape },
  "claw.browser": { d: "Phone Chrome over CDP 127.0.0.1:9222. action: version|tabs|open|close|navigate|read(format markdown|html|snapshot)|eval|wait|click|type|cdp. Args: tab,url,selector,index,text,expression,submit. Never types passwords. A trailing CHOICE: line means the operator must pick (tab, ambiguous selector, sign-in).", s: S({ action: str, tab: str, url: str, selector: str, text: str, expression: str, format: str, submit: { type: "boolean" }, index: { type: "integer" }, max_chars: { type: "integer" }, x: { type: "number" }, y: { type: "number" }, method: str, params: { type: "object" }, timeout: { type: "integer" } }), run: browser },
  "claw.device": { d: "Device I/O. action: battery|wifi|location|clipboard-get|clipboard-set|toast|tts|vibrate|notify|open-url (args; runs on the termux or aesc backend), platform (which backend serves what, listener state). Built-in adb client over loopback, no adb binary: adb-connect (port, host)|adb-shell (command)|adb-tap (x,y)|adb-install (path)|adb-status|adb-disconnect. adb binary: adb-devices|adb (args=argv). rclone (read-only). google: service drive (op list|get|read|create), gmail (list|get|thread|labels|draft), calendar (list|get|calendars|create); account, query, id, limit, page_token; writes need confirm=true and never send, delete or share. A trailing CHOICE: line means the operator must pick.", s: S({ action: str, args: { type: "array" }, host: str, port: { type: "integer" }, command: str, path: str, x: { type: "integer" }, y: { type: "integer" }, timeout: { type: "integer" }, replace: { type: "boolean" }, account: str, service: str, op: str, query: str, id: str, limit: { type: "integer" }, page_token: str, calendar: str, time_min: str, time_max: str, max_chars: { type: "integer" }, confirm: { type: "boolean" }, name: str, content: str, mime_type: str, folder: str, to: str, cc: str, subject: str, body: str, summary: str, start: str, end: str, description: str, location: str }, ["action"]), run: device },
  "claw.infer": { d: "Inference via provider openrouter|gemini (keys from env).", s: S({ provider: str, model: str, prompt: str }, ["model", "prompt"]), run: infer },
  "claw.workflows": { d: "action list|run (name). Named tool sequences from workflows.json.", s: S({ action: str, name: str }), run: workflows },
};

export async function handle(m) {
  if (m.id === undefined) return null;
  const ok = (result) => ({ jsonrpc: "2.0", id: m.id, result }), err = (code, message) => ({ jsonrpc: "2.0", id: m.id, error: { code, message } });
  switch (m.method) {
    case "initialize": return ok({ protocolVersion: m.params?.protocolVersion || "2024-11-05", capabilities: { tools: {} }, serverInfo: { name: "claw-mcp", version: "0.3.0" } });
    case "ping": return ok({});
    case "tools/list": return ok({ tools: Object.entries(TOOLS).map(([name, t]) => ({ name, description: t.d, inputSchema: t.s })) });
    case "tools/call": {
      const t = TOOLS[m.params?.name]; if (!t) return err(-32602, "unknown tool");
      try { return ok({ content: [{ type: "text", text: redact(render(await t.run(m.params.arguments || {}))) }] }); }
      catch (e) { return ok({ isError: true, content: [{ type: "text", text: redact(renderError(e)) }] }); }
    }
    default: return err(-32601, "method not found");
  }
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  for (const sig of ["SIGTERM", "SIGINT", "SIGHUP"]) process.on(sig, () => process.exit(0)); // exit handlers unlink the socket
  startListener(handle).catch((e) => process.stderr.write("claw-mcp listener: " + e.message + "\n"));
  const pending = new Set();
  createInterface({ input: process.stdin }).on("line", (line) => {
    if (!line.trim()) return;
    let m; try { m = JSON.parse(line); } catch { return console.log(JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse error" } })); }
    const p = handle(m).then((r) => r && console.log(JSON.stringify(r))).finally(() => pending.delete(p)); pending.add(p);
  }).on("close", () => Promise.all(pending).then(() => process.exit(0)));
}
