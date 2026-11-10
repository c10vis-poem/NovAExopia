// Minimal CDP driver over Node's built-in fetch + WebSocket. Endpoint: 127.0.0.1:$CDP_PORT (adb forward to Chrome).
import { toMarkdown } from "./md.mjs";
import { ClawError } from "./wire.mjs";
const base = () => `http://127.0.0.1:${process.env.CDP_PORT || 9222}`;
const http = async (path, init) => {
  let r;
  try { r = await fetch(base() + path, { ...init, signal: AbortSignal.timeout(5000) }); }
  catch (e) { throw new ClawError(`Chrome DevTools not reachable at ${base()} (${e.cause?.code || e.message}). Run bin/webview-connect (adb forward tcp:9222 localabstract:chrome_devtools_remote) with Chrome open.`, { question: "Chrome is not reachable over DevTools. What next?", options: ["Chrome is open and forwarded, retry", "Skip this browser step"] }); }
  const t = await r.text(); try { return JSON.parse(t); } catch { return t; }
};

export class Session {
  constructor(ws) { this.ws = ws; this.id = 0; this.p = new Map(); this.ev = []; this.waiters = [];
    ws.onmessage = (e) => { const m = JSON.parse(e.data);
      if (m.id) { const p = this.p.get(m.id); this.p.delete(m.id); m.error ? p.rej(new Error(`${m.error.message} (${m.error.code})`)) : p.res(m.result); }
      else { this.ev.push(m); this.waiters = this.waiters.filter((w) => !w(m)); } };
  }
  static open(url) { return new Promise((res, rej) => { const ws = new WebSocket(url); ws.onopen = () => res(new Session(ws)); ws.onerror = () => rej(new Error("websocket connect failed: " + url)); }); }
  send(method, params = {}) { return new Promise((res, rej) => { const id = ++this.id; this.p.set(id, { res, rej }); this.ws.send(JSON.stringify({ id, method, params }));
    setTimeout(() => this.p.delete(id) && rej(new Error("timeout: " + method)), 15000); }); }
  once(method, ms = 15000) { const seen = this.ev.find((m) => m.method === method); if (seen) return Promise.resolve(seen);
    return new Promise((res) => { const t = setTimeout(() => res(null), ms); this.waiters.push((m) => m.method === method && (clearTimeout(t), res(m), true)); }); }
  close() { this.ws.close(); }
}

// A phone's Chrome usually holds many tabs: never guess which one to act on. The tab used last stays current.
let current = null;
const tabLabel = (t) => `${t.id.slice(0, 8)}: ${(t.title || t.url || "").slice(0, 40)}`;
async function target(a) {
  const tabs = (await http("/json/list")).filter((t) => t.type === "page");
  if (a.tab) {
    const want = String(a.tab).split(":")[0].trim(), t = tabs.find((x) => x.id === want || x.id.startsWith(want));
    if (!t) throw new Error(`no tab ${a.tab}`);
    current = t.id;
    return t;
  }
  const cur = tabs.find((x) => x.id === current);
  if (cur) return cur;
  if (!tabs.length) throw new Error("no open tab; use action=open");
  if (tabs.length === 1) { current = tabs[0].id; return tabs[0]; }
  throw new ClawError(`${tabs.length} tabs open and none selected. Repeat the call with tab=<id>.`, { question: "Which Chrome tab should claw use?", options: tabs.slice(0, 8).map(tabLabel) });
}
async function withTab(a, fn) { const t = await target(a); const s = await Session.open(t.webSocketDebuggerUrl); try { return await fn(s, t); } finally { s.close(); } }
const evalJs = async (s, expression) => { const r = await s.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error("page exception: " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text)); return r.result.value; };
const q = JSON.stringify;
// Finds element `index` of the selector, returning its centre, input type, how many matched, and short labels to pick from.
const point = (sel, index) => `(()=>{const all=[...document.querySelectorAll(${q(sel)})],e=all[${Number.isInteger(index) ? index : 0}];if(!e)return null;e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2,type:e.type||"",n:all.length,labels:all.slice(0,7).map(x=>(x.innerText||x.value||x.getAttribute("aria-label")||x.tagName).trim().slice(0,40))}})()`;
const needOne = (a, p, verb) => {
  if (!p) throw new Error("element not found: " + a.selector);
  if (p.n > 1 && !Number.isInteger(a.index)) throw new ClawError(`${p.n} elements match ${a.selector}. Repeat the ${verb} with index=<n>.`, { question: `Which match of ${a.selector} should claw ${verb}?`, options: p.labels.map((l, i) => `index ${i}: ${l}`) });
};

export async function browser(a) {
  const act = a.action || "version";
  switch (act) {
    case "version": return q(await http("/json/version"));
    case "tabs": return q((await http("/json/list")).filter((t) => t.type === "page").map(({ id, title, url }) => ({ id, title, url })));
    case "open": { const t = await http("/json/new?" + encodeURIComponent(a.url || "about:blank"), { method: "PUT" }); current = t.id; return q({ id: t.id, url: t.url }); }
    case "close": return await http("/json/close/" + (await target(a)).id);
    case "navigate": return withTab(a, async (s) => { if (!a.url) throw new Error("url required"); await s.send("Page.enable");
      const r = await s.send("Page.navigate", { url: a.url }); if (r.errorText) throw new Error("navigate failed: " + r.errorText);
      const ok = await s.once("Page.loadEventFired", 20000); return q({ url: a.url, loaded: !!ok }); });
    case "read": return withTab(a, async (s) => {
      if (a.format === "snapshot") { const { nodes } = await s.send("Accessibility.getFullAXTree");
        return nodes.filter((n) => !n.ignored && n.name?.value).map((n) => `${n.role?.value} ${q(n.name.value)}`).join("\n").slice(0, a.max_chars || 20000); }
      const html = await evalJs(s, "document.documentElement.outerHTML");
      return (a.format === "html" ? html : toMarkdown(html)).slice(0, a.max_chars || 20000); });
    case "eval": return withTab(a, async (s) => q(await evalJs(s, a.expression)));
    case "wait": return withTab(a, async (s) => { const end = Date.now() + (a.timeout || 10000);
      while (Date.now() < end) { if (await evalJs(s, `!!document.querySelector(${q(a.selector)})`)) return "found"; await new Promise((r) => setTimeout(r, 200)); }
      throw new Error("timeout waiting for " + a.selector); });
    case "click": return withTab(a, async (s) => { let p = a.selector ? await evalJs(s, point(a.selector, a.index)) : { x: a.x, y: a.y };
      if (a.selector) needOne(a, p, "click");
      if (p.x == null) throw new Error("click needs selector or x,y");
      for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) await s.send("Input.dispatchMouseEvent", { type, x: p.x, y: p.y, button: "left", clickCount: 1 });
      return `clicked ${p.x},${p.y}`; });
    case "type": return withTab(a, async (s) => {
      const p = await evalJs(s, point(a.selector, a.index)); needOne(a, p, "type into");
      if (p.type === "password") throw new ClawError("refused: password field. claw never handles passwords; log in yourself in the phone's Chrome, then drive the signed-in tab.", { question: "This step needs a password. Sign in by hand in the phone's Chrome; what next?", options: ["I signed in, continue", "Skip this step"] });
      await evalJs(s, `document.querySelectorAll(${q(a.selector)})[${Number.isInteger(a.index) ? a.index : 0}].focus()`);
      await s.send("Input.insertText", { text: a.text ?? "" });
      if (a.submit) for (const type of ["keyDown", "keyUp"]) await s.send("Input.dispatchKeyEvent", { type, key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: type === "keyDown" ? "\r" : undefined });
      return "typed"; });
    case "cdp": return withTab(a, async (s) => q(await s.send(a.method, a.params || {})));
    default: throw new Error("action must be version|tabs|open|close|navigate|read|eval|wait|click|type|cdp");
  }
}
