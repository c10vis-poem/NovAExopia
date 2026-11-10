#!/usr/bin/env node
/**
 * code-map generator.
 *
 * Usage:  node generate.mjs <data.json> [out.html]
 *
 * Takes a `data.json` (see ../reference/schema.md), VALIDATES it, AUTO-LAYS-OUT
 * the nodes within their clusters (the agent never supplies x/y), injects the
 * result into the fixed engine template, and writes a self-contained HTML map.
 *
 * Zero dependencies. The agent's whole job is to produce a valid data.json —
 * it never writes the engine and never places coordinates.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const TEMPLATE = join(HERE, '..', 'template', 'engine.html');

// Layout constants — must stay in sync with the engine's NODE_W / NODE_H.
const NODE_W = 150, NODE_H = 58;
const PAD_X = 20, PAD_Y = 16;     // padding inside a cluster box
const LABEL_H = 28;               // space for the cluster label at the top
const GAP_X = 28, GAP_Y = 26;     // gaps between nodes inside a cluster
const CL_GAP_X = 30, CL_GAP_Y = 36; // gaps between clusters
const MARGIN = 24;                // outer margin around everything

function die(msg) { console.error('✖ ' + msg); process.exit(1); }

/** Lighten a #rrggbb hex toward white (~86%) for the soft node background tint. */
function tintOf(hex) {
  const m = /^#?([0-9a-fA-F]{6})$/.exec(String(hex || '').trim());
  if (!m) return '#eef2f6';
  const n = parseInt(m[1], 16);
  const mix = 0.86;
  const ch = (c) => Math.round(c + (255 - c) * mix).toString(16).padStart(2, '0');
  return '#' + ch((n >> 16) & 255) + ch((n >> 8) & 255) + ch(n & 255);
}

// ---- load -----------------------------------------------------------------
const dataPath = process.argv[2];
if (!dataPath) die('usage: node generate.mjs <data.json> [out.html]');
let raw;
try { raw = JSON.parse(readFileSync(resolve(dataPath), 'utf8')); }
catch (e) { die(`cannot read/parse ${dataPath}: ${e.message}`); }

const layers = raw.layers || [];
const clusters = raw.clusters || [];
const nodes = raw.nodes || [];
const edges = raw.edges || [];

// ---- validate (hard gates) ------------------------------------------------
const errs = [];
if (!layers.length) errs.push('layers[] is empty (need 3–6)');
if (!clusters.length) errs.push('clusters[] is empty');
if (!nodes.length) errs.push('nodes[] is empty');

const layerKeys = new Set(layers.map((l) => l.key));
const clusterKeys = new Set(clusters.map((c) => c.key));
const nodeIds = new Set();
for (const n of nodes) {
  if (!n.id) { errs.push(`node missing id: ${JSON.stringify(n).slice(0, 70)}`); continue; }
  if (nodeIds.has(n.id)) errs.push(`duplicate node id: "${n.id}"`);
  nodeIds.add(n.id);
  if (!layerKeys.has(n.layer)) errs.push(`node "${n.id}": unknown layer "${n.layer}"`);
  if (!clusterKeys.has(n.cluster)) errs.push(`node "${n.id}": unknown cluster "${n.cluster}"`);
}
for (const e of edges) {
  const [a, b] = e;
  if (!nodeIds.has(a)) errs.push(`edge references unknown node (from): "${a}"`);
  if (!nodeIds.has(b)) errs.push(`edge references unknown node (to): "${b}"`);
}
for (const f of (raw.flows || [])) {
  for (const id of (f.nodes || [])) {
    if (!nodeIds.has(id)) errs.push(`flow "${f.id}": unknown node "${id}"`);
  }
}
for (const c of clusters) {
  if (!nodes.some((n) => n.cluster === c.key)) errs.push(`cluster "${c.key}" has no nodes`);
}
for (const m of (raw.matrices || [])) {
  const w = (m.headers || []).length;
  if (!w) errs.push(`matrix "${m.title}" has no headers`);
  (m.rows || []).forEach((r, i) => {
    if (r.length !== w) errs.push(`matrix "${m.title}" row ${i}: ${r.length} cells, expected ${w}`);
  });
}
for (const w of (raw.walkthroughs || [])) {
  for (const s of (w.stages || [])) {
    if (s.layer && !layerKeys.has(s.layer)) errs.push(`walkthrough "${w.id}": stage layer "${s.layer}" unknown`);
  }
}
if (errs.length) {
  console.error('✖ data.json failed validation:');
  for (const e of errs) console.error('   - ' + e);
  process.exit(1);
}

// ---- auto-layout ----------------------------------------------------------
const nodesByCluster = new Map(clusters.map((c) => [c.key, nodes.filter((n) => n.cluster === c.key)]));
const colsFor = (n) => (n <= 2 ? 1 : n <= 6 ? 2 : 3);

for (const c of clusters) {
  const ns = nodesByCluster.get(c.key);
  const cols = c.cols || colsFor(ns.length);
  const rows = Math.ceil(ns.length / cols);
  c._cols = cols;
  c.w = PAD_X * 2 + cols * NODE_W + (cols - 1) * GAP_X;
  c.h = LABEL_H + PAD_Y * 2 + rows * NODE_H + (rows - 1) * GAP_Y;
}

// place clusters: group by `row`, left->right within a row, rows stacked
const byRow = new Map();
for (const c of clusters) {
  const r = Number.isInteger(c.row) ? c.row : 0;
  if (!byRow.has(r)) byRow.set(r, []);
  byRow.get(r).push(c);
}
let curY = MARGIN, maxRight = 0;
for (const r of [...byRow.keys()].sort((a, b) => a - b)) {
  let curX = MARGIN, rowH = 0;
  for (const c of byRow.get(r)) {
    c.x = curX; c.y = curY;
    curX += c.w + CL_GAP_X;
    rowH = Math.max(rowH, c.h);
    maxRight = Math.max(maxRight, c.x + c.w);
  }
  curY += rowH + CL_GAP_Y;
}
const vbW = maxRight + MARGIN;
const vbH = curY - CL_GAP_Y + MARGIN;

// place nodes inside their cluster's internal grid
for (const c of clusters) {
  nodesByCluster.get(c.key).forEach((n, i) => {
    const col = i % c._cols, row = Math.floor(i / c._cols);
    n.x = c.x + PAD_X + col * (NODE_W + GAP_X);
    n.y = c.y + LABEL_H + PAD_Y + row * (NODE_H + GAP_Y);
  });
}

// ---- assemble the laid-out DATA the engine consumes -----------------------
const DATA = {
  title: raw.title || 'Code Map',
  subtitle: raw.subtitle || '',
  summary: raw.summary || '',
  mode: raw.mode || 'architecture',
  meta: raw.meta || [],
  layers: layers.map((l) => ({ key: l.key, label: l.label, color: l.color, tint: l.tint || tintOf(l.color) })),
  clusters: clusters.map((c) => ({ key: c.key, label: c.label, x: c.x, y: c.y, w: c.w, h: c.h })),
  nodes: nodes.map((n) => ({
    id: n.id, label: n.label, hint: n.hint || '', layer: n.layer, x: n.x, y: n.y,
    description: n.description || '', decisions: n.decisions || [], files: n.files || [], data: n.data || [],
  })),
  edges,
  flows: raw.flows || [],
  matrices: raw.matrices || [],
  walkthroughs: raw.walkthroughs || [],
  notes: raw.notes || [],
  sections: raw.sections || {},
  viewBox: `0 0 ${vbW} ${vbH}`,
};

// ---- inject + write -------------------------------------------------------
let tpl;
try { tpl = readFileSync(TEMPLATE, 'utf8'); }
catch (e) { die(`cannot read engine template at ${TEMPLATE}: ${e.message}`); }
if (!tpl.includes('/*__DATA__*/{}')) die('engine template is missing the /*__DATA__*/{} injection marker');
const out = process.argv[3] || `${DATA.mode}-map.html`;
writeFileSync(out, tpl.replace('/*__DATA__*/{}', JSON.stringify(DATA)));

console.log(`✓ wrote ${out}`);
console.log(`  ${nodes.length} nodes · ${edges.length} edges · ${(raw.flows || []).length} flows · ${(raw.matrices || []).length} matrices · viewBox ${vbW}×${vbH}`);
