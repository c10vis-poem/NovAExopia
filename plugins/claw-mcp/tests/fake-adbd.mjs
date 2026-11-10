// Fake adbd for selftest: speaks the device side of the ADB wire protocol and is deliberately strict about what it accepts
// (magic, checksum, RSA signature verified against a key rebuilt from adb's public format, client TLS certificate key).
// Not a phone. It proves the client follows the protocol as written here, not that a real adbd accepts it.
import net from "node:net";
import tls from "node:tls";
import { constants, createHash, createPublicKey, publicDecrypt, randomBytes } from "node:crypto";

const cmd = (s) => s.charCodeAt(0) | (s.charCodeAt(1) << 8) | (s.charCodeAt(2) << 16) | (s.charCodeAt(3) << 24);
const A = { CNXN: cmd("CNXN"), AUTH: cmd("AUTH"), OPEN: cmd("OPEN"), OKAY: cmd("OKAY"), CLSE: cmd("CLSE"), WRTE: cmd("WRTE"), STLS: cmd("STLS") };
const PREFIX = Buffer.from("3021300906052b0e03021a05000414", "hex");
const b64u = (b) => b.toString("base64url");

// Rebuild the RSA key from the mincrypt struct: rejects a blob with the wrong layout.
export function keyFromAdbBlob(b64) {
  const b = Buffer.from(b64, "base64");
  if (b.length !== 524 || b.readUInt32LE(0) !== 64) throw new Error("bad adb public key layout");
  const n = Buffer.from(b.subarray(8, 264)).reverse();
  return createPublicKey({ key: { kty: "RSA", n: b64u(n), e: b64u(Buffer.from([0, 1, 0, 1]).subarray(b.readUInt32LE(520) === 65537 ? 1 : 0)) }, format: "jwk" });
}
const spki = (k) => k.export({ type: "spki", format: "der" }).toString("hex");

export function fakeAdbd({ mode = "plain", trusted = [], allowPrompt = false, features = "shell_v2,cmd", maxData = 4096, serverKey, serverCert, installFails = false } = {}) {
  const log = { errors: [], taps: [], shells: [], installs: [], prompted: 0, opens: [], tlsClientKeyOk: null };
  const keys = trusted.map(keyFromAdbBlob);
  const server = net.createServer((raw) => {
    let sock = raw, buf = Buffer.alloc(0), token = randomBytes(20), nextRemote = 100;
    const streams = new Map();
    const send = (c, a0, a1, data = Buffer.alloc(0)) => {
      const h = Buffer.alloc(24); let sum = 0; for (const x of data) sum = (sum + x) >>> 0;
      h.writeUInt32LE(c >>> 0, 0); h.writeUInt32LE(a0 >>> 0, 4); h.writeUInt32LE(a1 >>> 0, 8); h.writeUInt32LE(data.length, 12); h.writeUInt32LE(sum, 16); h.writeUInt32LE((c ^ 0xffffffff) >>> 0, 20);
      sock.write(Buffer.concat([h, data]));
    };
    const banner = () => send(A.CNXN, 0x01000001, maxData, Buffer.from(`device::ro.product.name=fake;features=${features}\0`));
    const challenge = () => { token = randomBytes(20); send(A.AUTH, 1, 0, token); };
    const writeAll = async (st, parts) => { for (const p of parts) { const acked = new Promise((r) => st.acks.push(r)); send(A.WRTE, st.mine, st.theirs, p); await acked; } };
    const frame = (id, s) => { const d = Buffer.from(s), h = Buffer.alloc(5); h[0] = id; h.writeUInt32LE(d.length, 1); return Buffer.concat([h, d]); };

    async function runShell(st, command, v2) {
      log.shells.push(command);
      let out = "", err = "", code = 0;
      const tap = /^input tap (\d+) (\d+)$/.exec(command);
      if (command === "echo hi") out = "hi\n";
      else if (command === "fail") { err = "bad\n"; code = 3; }
      else if (tap) log.taps.push([+tap[1], +tap[2]]);
      else if (command === "big") out = "x".repeat(300000);
      else out = "ran: " + command + "\n";
      if (!v2) await writeAll(st, out ? [Buffer.from(out)] : []);
      else {
        // Deliberately split across WRTE packets, mid-frame.
        const all = Buffer.concat([...(out ? [frame(1, out)] : []), ...(err ? [frame(2, err)] : []), frame(3, Buffer.from([code]))]), parts = [];
        for (let o = 0; o < all.length; o += 1000) parts.push(all.subarray(o, o + 1000));
        await writeAll(st, parts);
      }
      send(A.CLSE, st.mine, st.theirs);
    }

    function onPacket(c, a0, a1, data) {
      if (c === A.CNXN) {
        if (a0 < 0x01000000) log.errors.push("old version");
        if (!data.toString().startsWith("host::")) log.errors.push("bad host banner");
        if (mode === "tls") return send(A.STLS, 0x01000000, 0);
        return challenge();
      }
      if (c === A.STLS) {
        raw.removeAllListeners("data");
        const t = new tls.TLSSocket(raw, { isServer: true, key: serverKey, cert: serverCert, requestCert: true, rejectUnauthorized: false, minVersion: "TLSv1.3", maxVersion: "TLSv1.3" });
        t.on("error", (e) => log.errors.push("tls " + e.message));
        t.on("secure", () => {
          const peer = t.getPeerX509Certificate();
          const ok = !!peer && keys.some((k) => spki(k) === spki(peer.publicKey)) && peer.verify(peer.publicKey);
          log.tlsClientKeyOk = ok;
          if (!ok) return t.destroy();
          log.tlsVersion = t.getProtocol();
          sock = t; banner();
        });
        t.on("data", feed);
        return;
      }
      if (c === A.AUTH) {
        if (a0 === 2) {
          let good = false;
          for (const k of keys) { try { good ||= publicDecrypt({ key: k, padding: constants.RSA_PKCS1_PADDING }, data).equals(Buffer.concat([PREFIX, token])); } catch {} }
          return good ? banner() : challenge();
        }
        if (a0 === 3) {
          log.prompted++;
          const b = data.toString().replace(/\0+$/, "").split(" ")[0];
          keyFromAdbBlob(b);
          if (!data.toString().endsWith("\0")) log.errors.push("public key not NUL terminated");
          if (allowPrompt) { log.promptKey = b; banner(); }
          return;
        }
        return log.errors.push("bad AUTH type " + a0);
      }
      if (c === A.OPEN) {
        const dest = data.toString().replace(/\0$/, "");
        log.opens.push(dest);
        if (!data.toString().endsWith("\0")) log.errors.push("OPEN not NUL terminated");
        const mine = nextRemote++, st = { mine, theirs: a0, acks: [], got: [], size: 0 };
        const sh = /^shell(,v2,raw)?:(.*)$/s.exec(dest), inst = /^exec:cmd package install (-r )?-S (\d+)$/.exec(dest);
        if (!sh && !inst) return send(A.CLSE, 0, a0);
        streams.set(a0, st); send(A.OKAY, mine, a0);
        if (sh) runShell(st, sh[2], !!sh[1]);
        else { st.size = +inst[2]; st.replace = !!inst[1]; }
        return;
      }
      const st = streams.get(a0);
      if (!st) return;
      if (c === A.OKAY) return st.acks.shift()?.();
      if (c === A.WRTE) {
        if (data.length > maxData) log.errors.push(`client exceeded max data: ${data.length}`);
        send(A.OKAY, st.mine, st.theirs);
        st.got.push(data);
        const have = st.got.reduce((n, x) => n + x.length, 0);
        if (have >= st.size) {
          const all = Buffer.concat(st.got);
          log.installs.push({ bytes: all.length, sha: createHash("sha256").update(all).digest("hex"), replace: st.replace, packets: st.got.length });
          writeAll(st, [Buffer.from(installFails ? "Failure [INSTALL_FAILED_TEST]\n" : "Success\n")]).then(() => send(A.CLSE, st.mine, st.theirs));
        }
        return;
      }
      if (c === A.CLSE) streams.delete(a0);
    }
    function feed(d) {
      buf = buf.length ? Buffer.concat([buf, d]) : d;
      while (buf.length >= 24) {
        const c = buf.readUInt32LE(0), len = buf.readUInt32LE(12), sum = buf.readUInt32LE(16);
        if (((c ^ buf.readUInt32LE(20)) >>> 0) !== 0xffffffff) { log.errors.push("bad magic"); return sock.destroy(); }
        if (buf.length < 24 + len) return;
        const data = Buffer.from(buf.subarray(24, 24 + len)), a0 = buf.readUInt32LE(4), a1 = buf.readUInt32LE(8);
        let s = 0; for (const x of data) s = (s + x) >>> 0;
        if (s !== sum) log.errors.push("bad checksum");
        buf = buf.subarray(24 + len);
        onPacket(c | 0, a0, a1, data);
      }
    }
    raw.on("data", feed);
    raw.on("error", () => {});
  });
  return new Promise((res) => server.listen(0, "127.0.0.1", () => res({ port: server.address().port, log, close: () => server.close() })));
}
