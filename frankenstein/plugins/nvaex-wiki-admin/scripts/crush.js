#!/usr/bin/env node
// crush: JSON / JSONL on stdin or file -> ESON (token-compact, lossless). Uses vendor/eson/index.js
// (origin: NoVa-honey-for-devs eso/). Prints original and crushed byte counts to stderr.
const fs = require("fs"), path = require("path");
const { encode } = require(path.join(__dirname, "..", "vendor", "eson", "index.js"));
const raw = fs.readFileSync(process.argv[2] || 0, "utf8");
let data;
try { data = JSON.parse(raw); } catch { data = raw.split("\n").filter(Boolean).map((l) => JSON.parse(l)); }
const out = encode(Array.isArray(data) ? { rows: data } : data); // ESON root must be an object
process.stdout.write(out + "\n");
console.error(`crush: ${Buffer.byteLength(raw)} -> ${Buffer.byteLength(out)} bytes`);
