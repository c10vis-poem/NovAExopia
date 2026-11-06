---
name: code-map
description: Generate an interactive HTML map of a codebase (node graph, search, cited files). Use to explore or document a codebase.
allowed-tools: Bash(node *), Glob, Grep, Read, Write
argument-hint: "[architecture | flow <topic>]"
---

# code-map

Turn a scan of the current repo into an interactive HTML map. **You produce only the data;
a bundled generator renders it.** Never write the HTML engine by hand and never assign node
coordinates — that is the generator's job, and doing it yourself is the main way this goes
wrong.

## The pipeline

1. Pick the **mode** (below).
2. **Scan** the repo and build a model: layers, clusters, nodes (with real file citations),
   edges, and — optionally — flows, matrices, walkthroughs, notes.
3. **Write `data.json`** conforming to [reference/schema.md](reference/schema.md).
4. **Generate:**
   ```bash
   node ${CLAUDE_SKILL_DIR}/scripts/generate.mjs data.json <name>-map.html
   ```
5. If the generator reports validation errors, **fix `data.json` and re-run.** Never edit the
   generated HTML. Then tell the user the output path.

## Modes (exactly two — do not invent others)

**`architecture`** (default) — the whole system.
- Layers = the kinds of component (e.g. `api`, `worker`, `data`, `external` — pick 3–6 that
  fit *this* codebase).
- Clusters = the major regions (request surface, services, persistence, background worker,
  external systems). Aim for 4–6.
- Nodes = the significant components (entrypoints, routers, key services/modules, the data
  store, schedulers, external integrations). One node per real unit; don't map every file.
- Flows = a few representative end-to-end paths (a request, a background job, a webhook).

**`flow <topic>`** — one pipeline traced end to end (e.g. `flow billing`, `flow auth`).
- Scope nodes to the stages of *that* path only, in order.
- Layers = the stages/phases of the pipeline.
- A walkthrough that steps through the transformation with concrete values is high-value here.
- This is the standout mode — use it to explain "what happens when X."

## Scanning rules

- **Cite real files on every node** (`path` or `path:line`). Use Glob/Grep/Read to confirm
  they exist. A node without a real citation is a bug.
- Prefer significance over completeness: a readable map of the ~15–25 things that matter
  beats an exhaustive dump.
- Group every node into exactly one `cluster` and tag it with one `layer`.
- Give clusters a `row` (0, 1, 2…) to control top-to-bottom banding; the generator places
  them left-to-right within a row and auto-grids the nodes inside.
- Keep node `label` short (≈17 chars/line; it wraps to two lines max).
- Edges are `[fromId, toId, "short label"]` describing what flows between them.

## Output

The generator writes a single self-contained `.html` file (no server, no build). Report its
path; suggest the user open it in a browser. The map has: a pan/zoom node graph, click-a-node
detail (purpose, decisions, files, connections), click-an-edge relationships, flow tabs, a
step-through walkthrough player, matrices, and scan notes.

## Don't

- Don't hand-write or hand-edit the HTML engine.
- Don't put `x`/`y` on nodes (the generator lays them out).
- Don't add modes beyond `architecture` and `flow`.
- Don't invent files — every citation must be real.

See [reference/schema.md](reference/schema.md) for the full `data.json` contract.
