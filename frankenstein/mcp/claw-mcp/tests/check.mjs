import { spawn } from "node:child_process";
const [D] = process.argv.slice(2); let bad = 0;
const ck = (n, ok, extra = "") => { console.log((ok ? "PASS " : "FAIL ") + n + (ok ? "" : "  " + extra)); if (!ok) bad = 1; };
const p = spawn("sh", [D + "/bin/claw-mcp"], { env: { ...process.env, PATH: process.env.STUBPATH + ":" + process.env.PATH } });
let buf = "", waiters = new Map(); p.stdout.on("data", (d) => { buf += d; let i; while ((i = buf.indexOf("\n")) >= 0) { const m = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1); waiters.get(m.id)?.(m); } });
let n = 0; const rpc = (method, params) => new Promise((res) => { const id = ++n; waiters.set(id, res); p.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n"); });
const call = async (name, args) => { const r = (await rpc("tools/call", { name, arguments: args })).result; return { err: !!r.isError, t: r.content[0].text }; };
const B = (a) => call("claw.browser", a);

ck("initialize", (await rpc("initialize", { protocolVersion: "2024-11-05" })).result.serverInfo.name === "claw-mcp");
const names = (await rpc("tools/list")).result.tools.map((t) => t.name).sort().join();
ck("tools/list has the 6 tools", names === "claw.browser,claw.device,claw.infer,claw.scrape,claw.search,claw.workflows", names);

let r = await call("claw.scrape", { url: process.env.FAKE + "/page" });
ck("scrape -> markdown", r.t.includes("# Hello") && r.t.includes("[link](https://e.com/a)") && r.t.includes("**bold**") && r.t.includes("- one") && !r.t.includes("x()"), r.t);
r = await call("claw.search", { query: "x" });
let j = r.err ? [] : JSON.parse(r.t);
ck("search parses results and unwraps redirect", j.length === 2 && j[0].url === "https://example.org/x" && j[0].title === "Example **Org**" && j[0].snippet === "A snippet", r.t);
process.env.CLAW_SEARCH_URL = "";
{ const q = spawn("sh", [D + "/bin/claw-mcp"], { env: { ...process.env, CLAW_SEARCH_URL: process.env.FAKE + "/blocked" } });
  q.stdin.end(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "claw.search", arguments: { query: "x" } } }) + "\n");
  let o = ""; q.stdout.on("data", (d) => (o += d)); await new Promise((r) => q.on("close", r));
  const m = JSON.parse(o); ck("search block gives clear error", m.result.isError && /blocked by provider/.test(m.result.content[0].text), o); }

ck("browser version", JSON.parse((await B({ action: "version" })).t).Browser === "FakeChrome/1");
ck("browser tabs", JSON.parse((await B({ action: "tabs" })).t)[0].id === "AB12");
ck("browser open", JSON.parse((await B({ action: "open", url: "https://a.test/" })).t).url === "https://a.test/");
r = await B({ action: "navigate", url: "https://b.test/" }); ck("browser navigate waits for load", JSON.parse(r.t).loaded === true, r.t);
ck("browser tabs shows navigated url", JSON.parse((await B({ action: "tabs" })).t)[0].url === "https://b.test/");
r = await B({ action: "read" }); ck("browser read -> markdown", r.t.includes("# Hello") && r.t.includes("- two"), r.t);
ck("browser read snapshot", (await B({ action: "read", format: "snapshot" })).t === 'button "Go"');
ck("browser eval", (await B({ action: "eval", expression: "1+1" })).t === "2");
ck("browser wait", (await B({ action: "wait", selector: "#a" })).t === "found");
r = await B({ action: "click", selector: "#a" }); ck("browser click", r.t === "clicked 100,200", r.t);
r = await B({ action: "type", selector: "#q", text: "hello", submit: true }); ck("browser type", r.t === "typed", r.t);
r = await B({ action: "type", selector: "#pw", text: "secret" }); ck("browser refuses password field", r.err && /never handles passwords/.test(r.t), r.t);
r = await B({ action: "click", selector: "#nope" }); ck("browser click missing element errors", r.err, r.t);
const calls = await (await fetch(process.env.FAKE + "/_calls")).json();
const seq = calls.map((c) => c.method + (c.method === "Input.insertText" ? ":" + c.params.text : c.method === "Input.dispatchMouseEvent" ? ":" + c.params.type + "@" + c.params.x + "," + c.params.y : c.method === "Page.navigate" ? ":" + c.params.url : ""));
ck("CDP frames on the wire (navigate, mouse x3, insertText, Enter)", ["Page.navigate:https://b.test/", "Input.dispatchMouseEvent:mouseMoved@100,200", "Input.dispatchMouseEvent:mousePressed@100,200", "Input.dispatchMouseEvent:mouseReleased@100,200", "Input.insertText:hello"].every((x) => seq.includes(x)) && calls.filter((c) => c.method === "Input.dispatchKeyEvent").length === 2, seq.join(" "));
ck("password never typed", !seq.includes("Input.insertText:secret"));

r = await call("claw.device", { action: "toast", args: ["hi"] }); ck("device toast builds termux-toast call", r.t.startsWith("STUB:") && r.t.endsWith("hi"), r.t);
r = await call("claw.device", { action: "rclone", args: ["purge", "x:"] }); ck("device rclone refuses writes", r.err, r.t);
r = await call("claw.device", { action: "google", service: "drive", account: "none" }); ck("device google: clear error without creds", r.err && /no Google credentials/.test(r.t), r.t);
r = await call("claw.device", { action: "adb-devices" }); ck("device adb-devices runs adb (stub binary, so no adb server starts)", r.t.startsWith("List of devices"), r.t);
r = await call("claw.infer", { model: "m", prompt: "ping" }); ck("infer openrouter path", r.t === "pong", r.t);
r = await call("claw.workflows", { action: "run", name: "phone-status" }); ck("workflows run executes real steps", !r.err && Array.isArray(JSON.parse(r.t)), r.t);
p.stdin.end(); process.exit(bad);
