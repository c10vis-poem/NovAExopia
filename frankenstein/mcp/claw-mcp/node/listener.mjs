// Local socket for the Aesc daemon. Lives and dies with this stdio server; nothing is left running.
//   CLAW_LISTEN=off | unix:/path (default unix:<state>/claw.sock, mode 0600) | tcp:127.0.0.1:PORT (loopback only, token required)
// Newline-delimited JSON-RPC 2.0, both directions on one connection:
//   client -> claw: initialize, ping, tools/list, tools/call (same as stdio); aesc/register {name, ops:[...]}; auth {token} (tcp only, must be first)
//   claw -> client: device/call {op, args} once registered; reply {result} or {error:{message}}
// A second claw on the same path leaves the live socket alone and runs without a listener.
import net from "node:net";
import { chmodSync, existsSync, mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { randomBytes, timingSafeEqual } from "node:crypto";
import { clearPeer, setPeer } from "./platform.mjs";

const MAX_LINE = 1024 * 1024, MAX_CLIENTS = 8, PEER_TIMEOUT = 30000;
const stateDir = () => process.env.CLAW_STATE_DIR || join(homedir(), ".claude", "state", "claw-mcp");
const LOOPBACK = new Set(["127.0.0.1", "::1"]);
let status = { state: "not started" };
export const listenerStatus = () => status;

function token(dir) {
  if (process.env.CLAW_LISTEN_TOKEN) return process.env.CLAW_LISTEN_TOKEN;
  const f = join(dir, "claw.token");
  if (existsSync(f)) return readFileSync(f, "utf8").trim();
  const t = randomBytes(32).toString("hex");
  writeFileSync(f, t, { mode: 0o600 });
  return t;
}
const same = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && timingSafeEqual(x, y); };
const isLive = (path) => new Promise((res) => { const c = net.connect(path); c.once("connect", () => { c.destroy(); res(true); }); c.once("error", () => res(false)); });

function serveClient(sock, handle, secret, clients) {
  clients.add(sock);
  let buf = "", authed = !secret, me = null, nextId = 1;
  const pending = new Map();
  const send = (o) => { if (!sock.destroyed) sock.write(JSON.stringify(o) + "\n"); };
  const request = (method, params) => new Promise((res, rej) => {
    const id = "claw-" + nextId++;
    const t = setTimeout(() => { pending.delete(id); rej(new Error(`aesc did not answer ${method} within ${PEER_TIMEOUT} ms`)); }, PEER_TIMEOUT);
    pending.set(id, { res, rej, t });
    send({ jsonrpc: "2.0", id, method, params });
  });
  const onMessage = async (m) => {
    if (m.method === undefined && pending.has(m.id)) { // reply to our device/call
      const p = pending.get(m.id); pending.delete(m.id); clearTimeout(p.t);
      return m.error ? p.rej(new Error(m.error.message || "aesc error")) : p.res(m.result);
    }
    if (!authed) {
      if (m.method === "auth" && same(m.params?.token, secret)) { authed = true; return send({ jsonrpc: "2.0", id: m.id, result: { ok: true } }); }
      send({ jsonrpc: "2.0", id: m.id ?? null, error: { code: -32001, message: "auth required" } });
      return sock.destroy();
    }
    if (m.method === "aesc/register") {
      if (me) clearPeer(me);
      me = { name: String(m.params?.name || "aesc"), ops: (Array.isArray(m.params?.ops) ? m.params.ops : []).map(String), request };
      setPeer(me);
      return send({ jsonrpc: "2.0", id: m.id, result: { registered: me.ops } });
    }
    const r = await handle(m);
    if (r) send(r);
  };
  sock.setEncoding("utf8");
  sock.on("data", (d) => {
    buf += d;
    if (buf.length > MAX_LINE) return sock.destroy();
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i); buf = buf.slice(i + 1);
      if (!line.trim()) continue;
      let m; try { m = JSON.parse(line); } catch { send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse error" } }); continue; }
      onMessage(m).catch((e) => send({ jsonrpc: "2.0", id: m.id ?? null, error: { code: -32603, message: e.message } }));
    }
  });
  sock.on("error", () => {});
  sock.on("close", () => {
    clients.delete(sock);
    if (me) clearPeer(me);
    for (const p of pending.values()) { clearTimeout(p.t); p.rej(new Error("aesc disconnected")); }
    pending.clear();
  });
}

export async function startListener(handle) {
  const dir = stateDir();
  const spec = process.env.CLAW_LISTEN ?? `unix:${join(dir, "claw.sock")}`;
  if (spec === "off") return (status = { state: "off" });
  const clients = new Set();
  const fail = (why) => { process.stderr.write(`claw-mcp listener: ${why}\n`); return (status = { state: "disabled", spec, why }); };
  const server = net.createServer((sock) => {
    if (clients.size >= MAX_CLIENTS) return sock.destroy();
    serveClient(sock, handle, secret, clients);
  });
  let secret = null, target;
  try {
    mkdirSync(dir, { recursive: true, mode: 0o700 });
    if (spec.startsWith("unix:")) {
      target = { path: spec.slice(5) };
      if (Buffer.byteLength(target.path) > 107) return fail("socket path longer than 107 bytes");
      if (existsSync(target.path)) {
        if (await isLive(target.path)) return fail("another claw already serves " + target.path);
        unlinkSync(target.path);
      }
    } else if (spec.startsWith("tcp:")) {
      const m = /^tcp:(\[.+\]|[^:]+):(\d+)$/.exec(spec), host = m?.[1].replace(/[[\]]/g, "");
      if (!m || !LOOPBACK.has(host)) return fail("tcp is loopback only: tcp:127.0.0.1:PORT");
      target = { host, port: +m[2] };
      secret = token(dir);
    } else return fail("CLAW_LISTEN must be off, unix:/path or tcp:127.0.0.1:PORT");
  } catch (e) { return fail(e.message); }

  return new Promise((res) => {
    const old = process.umask(0o177); // no window where the socket is group/world accessible
    server.once("error", (e) => { process.umask(old); res(fail(e.code || e.message)); });
    server.listen(target, () => {
      process.umask(old);
      server.on("error", () => {});
      if (target.path) {
        chmodSync(target.path, 0o600);
        process.on("exit", () => { try { unlinkSync(target.path); } catch {} });
        res(status = { state: "listening", path: target.path });
      } else {
        const { address, port } = server.address();
        res(status = { state: "listening", host: address, port, token_file: process.env.CLAW_LISTEN_TOKEN ? null : join(dir, "claw.token") });
      }
    });
  });
}
