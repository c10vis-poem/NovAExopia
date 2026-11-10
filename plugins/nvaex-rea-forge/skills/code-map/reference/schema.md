# `data.json` contract

The single interface between the agent and the rendering engine. Produce one valid instance;
`generate.mjs` validates it, lays out the nodes, and renders. All fields shown; only
`title`, `layers`, `clusters`, `nodes`, and `edges` are required.

```jsonc
{
  // ---- header / framing ----
  "title": "Acme API — Architecture",        // required
  "subtitle": "Built from a scan of src/, worker/, prisma/",
  "summary": "One short paragraph for the overview block.",
  "mode": "architecture",                     // "architecture" | "flow"
  "meta": ["Bun + Hono", "Postgres", "Stripe"], // optional header pills

  // ---- layers: 3–6. Drive node color, the legend, and the filter buttons ----
  "layers": [
    { "key": "api", "label": "API", "color": "#2563eb" }   // tint auto-derived if omitted
  ],

  // ---- clusters: grouping boxes. `row` bands them top→bottom ----
  "clusters": [
    { "key": "svc", "label": "API service", "row": 0 }     // optional "cols" to force grid width
  ],

  // ---- nodes: the boxes. NO x/y — the generator places them ----
  "nodes": [
    {
      "id": "api-server",                     // required, unique, referenced by edges/flows
      "label": "API server",                  // required, short (~17 chars/line, wraps to 2)
      "hint": "Bun + Hono",                   // small subtitle line
      "layer": "api",                         // required, must match a layers[].key
      "cluster": "svc",                       // required, must match a clusters[].key
      "description": "What it does, in a sentence or two.",
      "decisions": ["A design decision worth knowing."],
      "files": ["src/index.ts", "src/openapi/app.ts:42"],   // REAL files; cite line where useful
      "data": ["Entities / tables / types it touches"]
    }
  ],

  // ---- edges: [fromId, toId, "short label"] ----
  "edges": [
    ["api-server", "routes", "dispatch"]
  ],

  // ---- flows: walkthrough tabs that highlight a path through the graph ----
  "flows": [
    {
      "id": "request", "label": "Request", "title": "A read request, end to end",
      "nodes": ["dashboard", "api-server", "routes", "repos", "postgres"],
      "steps": ["Step 1…", "Step 2…"],
      "decisions": ["Why it's built this way."]
    }
  ],

  // ---- matrices: optional generic tables (endpoints, tiers, factors…) ----
  "matrices": [
    {
      "title": "Endpoint matrix",
      "headers": ["Area", "Route", "Auth"],   // column count is enforced against every row
      "rows": [["Auth", "/api/v1/auth/me", "JWT"]]
    }
  ],

  // ---- walkthroughs: optional step-through player (great for flow mode) ----
  "walkthroughs": [
    {
      "id": "ex1", "label": "Example",
      "header": { "kind": "GET", "path": "/api/v1/usage", "pairs": [["Authorization", "Bearer …"]] },
      "stages": [
        { "layer": "api", "title": "Stage title", "desc": "What happens.",
          "file": "src/index.ts", "badge": { "type": "pass", "text": "200 OK" } }
      ]
    }
  ],

  // ---- notes: optional "Scan Notes" panel ----
  "notes": [
    { "kind": "ok", "text": "Something solid." },     // kind: "ok" | "info" | "warn"
    { "kind": "warn", "text": "A caveat or gotcha." }
  ],

  // ---- section labels: optional overrides ----
  "sections": { "walkthroughTitle": "Worked example", "matricesTitle": "Reference tables" }
}
```

## Validation gates (the generator hard-fails on these)

- a node `id` that is missing or duplicated;
- a node whose `layer` or `cluster` key isn't declared;
- an `edge` / `flow.nodes` / referencing a node id that doesn't exist;
- a `cluster` with no nodes;
- a `matrix` row whose cell count ≠ its `headers` length;
- a `walkthrough` stage `layer` that isn't declared.

## Layout

You only choose **which cluster** a node belongs to and **which `row`** a cluster sits in.
The generator computes every coordinate: clusters flow left→right within a row and stack by
row; nodes auto-grid inside their cluster (1 col for ≤2 nodes, 2 cols for ≤6, else 3 — or set
`cluster.cols` to force it). The `viewBox` is sized to fit.

## Badge types (walkthrough stages)

`pass` (green), `gate` (red — a check/guard), `return` (blue — a value/response). Omit for none.
