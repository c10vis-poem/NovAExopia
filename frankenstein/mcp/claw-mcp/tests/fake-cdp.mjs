// Fake Chrome DevTools endpoint + fake search/infer/web host for selftest. Not Chrome: proves our client speaks CDP/WebSocket correctly.
import http from "node:http";
import { createHash } from "node:crypto";
const calls = []; let url = "about:blank", extraTabs = 0;
const PAGE = '<html><head><title>T</title><script>x()</script></head><body><h1>Hello</h1><p>See <a href="https://e.com/a">link</a> and <b>bold</b>.</p><ul><li>one</li><li>two</li></ul></body></html>';
const frame = (s) => { const b = Buffer.from(s), n = b.length;
  const h = n < 126 ? Buffer.from([0x81, n]) : n < 65536 ? Buffer.from([0x81, 126, n >> 8, n & 255]) : Buffer.concat([Buffer.from([0x81, 127, 0, 0, 0, 0]), Buffer.from([(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255])]);
  return Buffer.concat([h, b]); };
function* frames(buf) { // client frames are masked
  while (buf.length >= 6) { let n = buf[1] & 127, o = 2; if (n === 126) { n = buf.readUInt16BE(2); o = 4; } else if (n === 127) { n = Number(buf.readBigUInt64BE(2)); o = 10; }
    if (buf.length < o + 4 + n) return; const k = buf.subarray(o, o + 4), d = Buffer.from(buf.subarray(o + 4, o + 4 + n)); for (let i = 0; i < n; i++) d[i] ^= k[i & 3];
    yield [buf[0] & 15, d.toString()]; buf = buf.subarray(o + 4 + n); } }
const reply = (id, result) => JSON.stringify({ id, result });
function onCdp(m, sock) {
  calls.push(m); const { id, method, params } = m;
  if (method === "Page.navigate") { url = params.url; sock.write(frame(reply(id, { frameId: "f" }))); return sock.write(frame(JSON.stringify({ method: "Page.loadEventFired", params: {} }))); }
  let r = {};
  if (method === "Runtime.evaluate") { const e = params.expression, v = e.includes("outerHTML") ? PAGE : e.includes("getBoundingClientRect") ? (e.includes("#pw") ? { x: 5, y: 6, type: "password", n: 1, labels: [] } : e.includes("#nope") ? null : e.includes("#many") ? { x: 1, y: 2, type: "", n: 3, labels: ["First", "Sec|ond", "Third"] } : { x: 100, y: 200, type: "text", n: 1, labels: [] }) : e === "1+1" ? 2 : e.includes("querySelector") && e.includes("!!") ? true : null;
    r = { result: { type: "object", value: v } }; }
  if (method === "Accessibility.getFullAXTree") r = { nodes: [{ role: { value: "button" }, name: { value: "Go" } }, { ignored: true }] };
  sock.write(frame(reply(id, r)));
}
http.createServer((q, s) => {
  const j = (o) => (s.setHeader("content-type", "application/json"), s.end(JSON.stringify(o)));
  if (q.url === "/json/version") return j({ Browser: "FakeChrome/1", webSocketDebuggerUrl: "x" });
  if (q.url.startsWith("/_settabs")) { extraTabs = +q.url.split("=")[1]; return j({}); }
  if (q.url === "/json/list") return j([{ id: "AB12", type: "page", title: "T", url, webSocketDebuggerUrl: `ws://127.0.0.1:${port}/devtools/page/AB12` }, ...Array.from({ length: extraTabs }, (_, i) => ({ id: "CD" + i + "EFGHIJK", type: "page", title: "Tab | " + i, url: "https://t.test/" + i, webSocketDebuggerUrl: `ws://127.0.0.1:${port}/devtools/page/CD${i}` }))]);
  if (q.url.startsWith("/json/new")) { url = decodeURIComponent(q.url.split("?")[1]); return j({ id: "AB12", url }); }
  if (q.url === "/_calls") return j(calls);
  if (q.url === "/page") return s.end(PAGE);
  if (q.url === "/search" && q.method === "POST") return s.end('<div><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fx&amp;rut=1">Example <b>Org</b></a><a class="result__snippet" href="#">A snippet</a></div><div><a class="result__a" href="https://b.com">Bee</a></div>');
  if (q.url === "/blocked") { s.statusCode = 202; return s.end("<html>anomaly-modal bot check</html>"); }
  if (q.url === "/infer") return j({ choices: [{ message: { content: "pong" } }] });
  s.statusCode = 404; s.end();
}).on("upgrade", (q, sock) => {
  sock.write("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + createHash("sha1").update(q.headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest("base64") + "\r\n\r\n");
  let buf = Buffer.alloc(0);
  sock.on("data", (d) => { buf = Buffer.concat([buf, d]); for (const [op, t] of frames(buf)) { if (op === 1) onCdp(JSON.parse(t), sock); } buf = Buffer.alloc(0); }).on("error", () => {});
}).listen(0, "127.0.0.1", function () { port = this.address().port; console.log(port); });
let port;
