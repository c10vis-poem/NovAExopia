// Built-in ADB client: the adbd wire protocol over a loopback socket, Node built-ins only. No adb binary, Shizuku or Tasker.
// Pairing stays with the operator (`adb pair` writes this key into the phone's trusted list); this client reuses that key.
// Handles both adbd modes: wireless debugging (A_STLS, TLS 1.3 with a client certificate over the adb key) and classic
// tcpip (A_AUTH token signature, then public key).
import net from "node:net";
import tls from "node:tls";
import { constants, createPrivateKey, createPublicKey, privateEncrypt, sign } from "node:crypto";
import { createReadStream, readFileSync, statSync } from "node:fs";
import { homedir, hostname, userInfo } from "node:os";
import { join } from "node:path";
import { ClawError } from "./wire.mjs";
import { run } from "./platform.mjs";

const cmd = (s) => s.charCodeAt(0) | (s.charCodeAt(1) << 8) | (s.charCodeAt(2) << 16) | (s.charCodeAt(3) << 24);
const A = { CNXN: cmd("CNXN"), AUTH: cmd("AUTH"), OPEN: cmd("OPEN"), OKAY: cmd("OKAY"), CLSE: cmd("CLSE"), WRTE: cmd("WRTE"), STLS: cmd("STLS") };
const VERSION = 0x01000001, STLS_VERSION = 0x01000000, HOST_MAXDATA = 1024 * 1024;
const AUTH_TOKEN = 1, AUTH_SIGNATURE = 2, AUTH_RSAPUBLICKEY = 3;
const OUTPUT_CAP = 1024 * 1024;
const HOST_BANNER = "host::features=shell_v2,cmd\0";
const SHA1_DIGEST_INFO = Buffer.from("3021300906052b0e03021a05000414", "hex");

// ---- keys
export const loadKey = (path) => {
  const file = path || process.env.CLAW_ADB_KEY || join(homedir(), ".android", "adbkey");
  let pem;
  try { pem = readFileSync(file, "utf8"); }
  catch { throw new ClawError(`no adb key at ${file}. Pair once with the adb binary, which creates it: adb pair 127.0.0.1:<pairing-port> <code>.`); }
  return createPrivateKey(pem);
};

// adb's own public key format: base64 of the mincrypt RSAPublicKey struct, then a comment.
const toBig = (b64u) => BigInt("0x" + Buffer.from(b64u, "base64url").toString("hex"));
const leBytes = (n, len) => { const b = Buffer.alloc(len); for (let i = 0; i < len; i++) { b[i] = Number(n & 255n); n >>= 8n; } return b; };
export function adbPublicKeyB64(key) {
  const { n: nStr, e: eStr } = createPublicKey(key).export({ format: "jwk" });
  const n = toBig(nStr), e = toBig(eStr), bytes = Buffer.from(nStr, "base64url").length;
  if (bytes !== 256) throw new Error(`adb keys are RSA-2048; this one has ${bytes * 8} bits`);
  const m32 = 1n << 32n;
  let inv = 1n; for (let i = 0; i < 6; i++) inv = (inv * (2n - (n % m32) * inv)) % m32; // Newton: n^-1 mod 2^32
  inv = ((inv % m32) + m32) % m32;
  const n0inv = (m32 - inv) % m32, rr = (1n << BigInt(2 * bytes * 8)) % n;
  const head = Buffer.alloc(8); head.writeUInt32LE(bytes / 4, 0); head.writeUInt32LE(Number(n0inv), 4);
  const tail = Buffer.alloc(4); tail.writeUInt32LE(Number(e), 0);
  return Buffer.concat([head, leBytes(n, bytes), leBytes(rr, bytes), tail]).toString("base64");
}
export const signToken = (key, token) => privateEncrypt({ key, padding: constants.RSA_PKCS1_PADDING }, Buffer.concat([SHA1_DIGEST_INFO, token]));

// Self-signed X.509 for the adb key (adbd checks the certificate's public key against its trusted list, not a chain). DER by hand: Node has no certificate writer.
const derLen = (n) => n < 128 ? Buffer.from([n]) : n < 256 ? Buffer.from([0x81, n]) : Buffer.from([0x82, n >> 8, n & 255]);
const der = (tag, ...parts) => { const b = Buffer.concat(parts); return Buffer.concat([Buffer.from([tag]), derLen(b.length), b]); };
export function adbCertificatePem(key) {
  const algo = der(0x30, Buffer.from("06092a864886f70d01010b", "hex"), Buffer.from([5, 0])); // sha256WithRSAEncryption
  const name = der(0x30, der(0x31, der(0x30, Buffer.from("0603550403", "hex"), der(0x0c, Buffer.from("adb"))))); // CN=adb
  const time = (s) => der(0x17, Buffer.from(s));
  const tbs = der(0x30,
    der(0xa0, der(2, Buffer.from([2]))), der(2, Buffer.from([1])), algo, name,
    der(0x30, time("200101000000Z"), time("490101000000Z")), name,
    createPublicKey(key).export({ type: "spki", format: "der" }));
  const cert = der(0x30, tbs, algo, der(3, Buffer.from([0]), sign("sha256", tbs, key)));
  return `-----BEGIN CERTIFICATE-----\n${cert.toString("base64").match(/.{1,64}/g).join("\n")}\n-----END CERTIFICATE-----\n`;
}

// ---- connection
class Conn {
  constructor(key) { this.key = key; this.buf = Buffer.alloc(0); this.streams = new Map(); this.next = 1; this.maxData = 4096; this.features = new Set(); this.banner = ""; this.dead = false; this.mode = "plain"; }

  attach(sock) {
    this.sock = sock;
    sock.on("data", (d) => this.feed(d));
    sock.on("error", (e) => { this.lastError = e; });
    sock.on("close", () => this.onClose());
  }
  onClose() {
    this.dead = true;
    for (const s of this.streams.values()) s.fail(new Error("adb connection closed"));
    this.streams.clear();
    this.onHandshakeClose?.();
  }
  close() { this.dead = true; this.sock?.destroy(); }

  send(command, a0, a1, data = Buffer.alloc(0)) {
    const h = Buffer.alloc(24);
    let sum = 0; for (const b of data) sum = (sum + b) >>> 0; // ignored by adbd >= VERSION, required below it
    h.writeUInt32LE(command >>> 0, 0); h.writeUInt32LE(a0 >>> 0, 4); h.writeUInt32LE(a1 >>> 0, 8);
    h.writeUInt32LE(data.length, 12); h.writeUInt32LE(sum, 16); h.writeUInt32LE((command ^ 0xffffffff) >>> 0, 20);
    this.sock.write(Buffer.concat([h, data]));
  }

  feed(d) {
    this.buf = this.buf.length ? Buffer.concat([this.buf, d]) : d;
    while (this.buf.length >= 24) {
      const command = this.buf.readUInt32LE(0), magic = this.buf.readUInt32LE(20), len = this.buf.readUInt32LE(12);
      if (((command ^ magic) >>> 0) !== 0xffffffff || len > 64 * 1024 * 1024) { this.lastError = new Error("bad adb packet (not an adbd on this port?)"); return this.sock.destroy(); }
      if (this.buf.length < 24 + len) return;
      const data = this.buf.subarray(24, 24 + len), a0 = this.buf.readUInt32LE(4), a1 = this.buf.readUInt32LE(8);
      this.buf = this.buf.subarray(24 + len);
      this.dispatch(command | 0, a0, a1, Buffer.from(data));
    }
  }

  dispatch(command, a0, a1, data) {
    if (this.onHandshake && (command === A.CNXN || command === A.AUTH || command === A.STLS)) return this.onHandshake(command, a0, a1, data);
    const s = this.streams.get(a1);
    if (command === A.OKAY && s) s.onOkay(a0);
    else if (command === A.WRTE && s) { this.send(A.OKAY, s.local, a0); s.onData(data); }
    else if (command === A.CLSE && s) { if (s.remote && !s.sentClose) this.send(A.CLSE, s.local, s.remote); this.streams.delete(a1); s.onClosed(); }
  }

  handshake(timeoutMs, authWaitMs) {
    return new Promise((res, rej) => {
      let signed = false, promptSent = false, timer;
      const finish = (fn, v) => { clearTimeout(timer); this.onHandshake = null; this.onHandshakeClose = null; fn(v); };
      const arm = (ms, why) => { clearTimeout(timer); timer = setTimeout(() => finish(rej, why()), ms); };
      arm(timeoutMs, () => new Error("adbd did not answer the handshake"));
      this.onHandshakeClose = () => finish(rej, this.lastError || new Error("adbd closed the connection during the handshake"));
      this.onHandshake = (command, a0, a1, data) => {
        if (command === A.STLS) {
          this.send(A.STLS, STLS_VERSION, 0);
          const raw = this.sock;
          raw.removeAllListeners("data"); raw.removeAllListeners("close"); raw.removeAllListeners("error");
          raw.on("error", () => {});
          const t = tls.connect({ socket: raw, key: this.key.export({ type: "pkcs8", format: "pem" }), cert: adbCertificatePem(this.key), rejectUnauthorized: false, minVersion: "TLSv1.3", maxVersion: "TLSv1.3" });
          this.mode = "tls";
          this.attach(t);
        } else if (command === A.AUTH && a0 === AUTH_TOKEN) {
          if (!signed) { signed = true; this.send(A.AUTH, AUTH_SIGNATURE, 0, signToken(this.key, data)); }
          else if (!promptSent) {
            promptSent = true; // phone shows "Allow debugging?"
            const who = `${userInfo().username}@${hostname()}`.replace(/\s/g, "");
            this.send(A.AUTH, AUTH_RSAPUBLICKEY, 0, Buffer.from(`${adbPublicKeyB64(this.key)} ${who}\0`));
            arm(authWaitMs, () => new ClawError("The phone did not accept this adb key in time.", { question: "Allow the debugging prompt on the phone, then what?", options: ["I allowed it, retry", "Skip this device step"] }));
          }
        } else if (command === A.CNXN) {
          this.maxData = Math.max(1024, Math.min(a1, HOST_MAXDATA));
          this.banner = data.toString().replace(/\0+$/, "");
          this.features = new Set((/features=([^;]*)/.exec(this.banner)?.[1] || "").split(",").filter(Boolean));
          finish(res, this);
        }
      };
      this.send(A.CNXN, VERSION, HOST_MAXDATA, Buffer.from(HOST_BANNER));
    });
  }

  // One logical stream. Flow control: each WRTE we send waits for the device's OKAY.
  open(dest) {
    const local = this.next++;
    let opened, refused, ended, failed;
    const ready = new Promise((res, rej) => { opened = res; refused = rej; });
    const end = new Promise((res, rej) => { ended = res; failed = rej; });
    ready.catch(() => {}); end.catch(() => {}); // settled on purpose even when nobody waits yet
    const st = {
      local, remote: 0, acks: [], closed: false, sentClose: false,
      onData: () => {},
      onOkay: (remote) => { if (!st.remote) { st.remote = remote; opened(); } else st.acks.shift()?.res(); },
      onClosed: () => {
        st.closed = true;
        if (!st.remote) return st.fail(new Error(`device refused stream ${dest.split(":")[0]}:`));
        st.acks.splice(0).forEach((a) => a.rej(new Error("stream closed by device")));
        ended();
      },
      fail: (e) => { st.closed = true; st.acks.splice(0).forEach((a) => a.rej(e)); refused(e); failed(e); },
    };
    this.streams.set(local, st);
    this.send(A.OPEN, local, 0, Buffer.from(dest + "\0"));
    return { st, ready, end };
  }
  async write(st, data) {
    for (let o = 0; o < data.length; o += this.maxData) {
      if (st.closed) throw new Error("stream closed by device");
      const chunk = data.subarray(o, o + this.maxData);
      const acked = new Promise((res, rej) => st.acks.push({ res, rej }));
      this.send(A.WRTE, st.local, st.remote, chunk);
      await acked;
    }
  }
  closeStream(st) { if (st.remote && !st.closed && !st.sentClose) { st.sentClose = true; this.send(A.CLSE, st.local, st.remote); } }

  // shell: uses the v2 framing when the device offers it, which is the only way to get the exit code.
  shell(command, timeoutMs = 60000) {
    const v2 = this.features.has("shell_v2");
    const { st, end } = this.open(`${v2 ? "shell,v2,raw" : "shell"}:${command}`);
    return new Promise((res, rej) => {
      const out = [], err = []; let outLen = 0, errLen = 0, exit = null, frag = Buffer.alloc(0), truncated = false;
      const keep = (list, b, n) => { if (n >= OUTPUT_CAP) { truncated = true; return n; } list.push(b.subarray(0, OUTPUT_CAP - n)); return n + b.length; };
      const timer = setTimeout(() => { this.closeStream(st); rej(new Error(`adb shell timed out after ${timeoutMs} ms`)); }, timeoutMs);
      st.onData = (d) => {
        if (!v2) { outLen = keep(out, d, outLen); return; }
        frag = frag.length ? Buffer.concat([frag, d]) : d;
        while (frag.length >= 5 && frag.length >= 5 + frag.readUInt32LE(1)) {
          const id = frag[0], n = frag.readUInt32LE(1), body = frag.subarray(5, 5 + n);
          if (id === 1) outLen = keep(out, body, outLen); else if (id === 2) errLen = keep(err, body, errLen); else if (id === 3) { exit = body[0]; this.closeStream(st); }
          frag = frag.subarray(5 + n);
        }
      };
      end.then(
        () => { clearTimeout(timer); res({ exit, stdout: Buffer.concat(out).toString(), stderr: Buffer.concat(err).toString(), ...(truncated ? { truncated: true } : {}) }); },
        (e) => { clearTimeout(timer); rej(e); });
    });
  }

  // Streamed install: `cmd package install -S` over exec:, available since Android 7. The APK is never pushed to storage.
  async install(path, { replace = true, timeoutMs = 300000 } = {}) {
    let size;
    try { const s = statSync(path); if (!s.isFile()) throw 0; size = s.size; } catch { throw new Error(`no APK file at ${path}`); }
    const { st, ready, end } = this.open(`exec:cmd package install ${replace ? "-r " : ""}-S ${size}`);
    let output = "";
    st.onData = (d) => { if (output.length < 8192) output += d.toString(); };
    const timer = setTimeout(() => this.close(), timeoutMs); // closing fails the stream, which rejects below
    try {
      await ready;
      try { for await (const chunk of createReadStream(path, { highWaterMark: this.maxData })) await this.write(st, chunk); }
      catch (e) { if (this.dead || !st.closed) throw e; } // device closed early: its output says why
      await end;
    } finally { clearTimeout(timer); }
    const text = output.trim();
    if (!/^Success/m.test(text)) throw new Error("install failed: " + (text || "no output from device"));
    return { bytes: size, result: text };
  }
}

export async function connect({ host = "127.0.0.1", port, key, timeoutMs = 10000, authWaitMs = 30000 }) {
  const conn = new Conn(key);
  await new Promise((res, rej) => {
    const sock = net.connect({ host, port });
    const t = setTimeout(() => { sock.destroy(); rej(new Error("connect timed out")); }, timeoutMs);
    sock.once("connect", () => { clearTimeout(t); conn.attach(sock); res(); });
    sock.once("error", (e) => { clearTimeout(t); rej(new Error(e.code || e.message)); });
  });
  try { return await conn.handshake(timeoutMs, authWaitMs); }
  catch (e) { conn.close(); throw e; }
}

// ---- claw.device actions
const LOOPBACK = new Set(["127.0.0.1", "::1", "localhost"]);
let session = null; // { conn, host, port }
const getprop = async (name) => { try { return (await run("getprop", [name], 3000)).trim(); } catch { return ""; } };

async function candidatePorts(a) {
  if (a.port) return [+a.port];
  const ports = [process.env.CLAW_ADB_PORT, await getprop("service.adb.tls.port"), await getprop("service.adb.tcp.port"), "5555"];
  return [...new Set(ports.filter((p) => /^\d+$/.test(p || "") && +p > 0).map(Number))];
}

async function ensure(a = {}) {
  if (session && !session.conn.dead && (!a.port || +a.port === session.port)) return session;
  const host = a.host || "127.0.0.1";
  if (!LOOPBACK.has(host)) throw new Error(`adb is loopback only here, refusing ${host}`);
  const key = loadKey();
  const tried = [];
  for (const port of await candidatePorts(a)) {
    try {
      const conn = await connect({ host, port, key, timeoutMs: a.timeout || 10000, authWaitMs: +process.env.CLAW_ADB_AUTH_WAIT || 30000 });
      session?.conn.close();
      return (session = { conn, host, port });
    } catch (e) {
      if (e instanceof ClawError) throw e;
      tried.push(`${port}: ${e.message}`);
    }
  }
  throw new ClawError(`No adbd reachable on ${host} (tried ${tried.join("; ")}). Wireless debugging must be on and paired.`, {
    question: "ADB is not reachable. Turn on Wireless debugging; what next?",
    options: ["Wireless debugging is on, retry", "Skip this device step"],
  });
}

export async function adbAction(action, a) {
  if (action === "adb-status") return JSON.stringify(session && !session.conn.dead ? { connected: true, host: session.host, port: session.port, mode: session.conn.mode, banner: session.conn.banner } : { connected: false });
  if (action === "adb-disconnect") { session?.conn.close(); session = null; return "disconnected"; }
  const s = await ensure(a);
  if (action === "adb-connect") return JSON.stringify({ connected: true, host: s.host, port: s.port, mode: s.conn.mode, banner: s.conn.banner });
  if (action === "adb-shell") {
    const command = a.command ?? (a.args || []).map(String).join(" ");
    if (!command) throw new Error("adb-shell needs command");
    return JSON.stringify(await s.conn.shell(command, a.timeout || 60000));
  }
  if (action === "adb-tap") {
    const [x, y] = [a.x ?? a.args?.[0], a.y ?? a.args?.[1]].map(Number);
    if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0) throw new Error("adb-tap needs integer x and y");
    const r = await s.conn.shell(`input tap ${x} ${y}`, a.timeout || 15000);
    if (r.exit) throw new Error(`input tap exit ${r.exit}: ${r.stderr || r.stdout}`);
    return `tapped ${x},${y}`;
  }
  if (action === "adb-install") {
    const path = a.path ?? a.args?.[0];
    if (!path) throw new Error("adb-install needs path");
    return JSON.stringify(await s.conn.install(String(path), { replace: a.replace !== false, timeoutMs: a.timeout || 300000 }));
  }
  throw new Error("unknown adb action " + action);
}
