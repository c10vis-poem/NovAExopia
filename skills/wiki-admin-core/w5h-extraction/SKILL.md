---
name: w5h-extraction
description: "Extracts and formats complete Who, What, When, Where, Why, and How (W5+H) operational matrices from stream-of-consciousness transcripts and unorganized architectural notes."
---

# W5+H Extraction Protocol

Source: operator doc `_02.wiki-admn-docs/w5h-extraction.md.txt` (Drive id 1Y5O-dw8kT1As1uAwmCke41GuiyV9PnN0). The procedure below is that text, unchanged. Operator rule 2 (RULES.md) applies on top: W5+H is followed *loosely*; fill the dimensions that carry weight and say "not stated" for the rest instead of inventing.

Use this skill when processing raw operator voice notes, meeting transcripts, or brainstorming sessions to derive an authoritative system architecture matrix without losing human intent.

## Step-by-step procedure

### 1. Ingest and isolate raw input
- Read the unstructured input completely before segmenting.
- Identify all explicit names, model types, hardware specifications, and personal constraints.
- Note any verbatim directives, invariants, or prohibitions (e.g., non-destructive file rules, naming requirements).

### 2. Extract the six dimensions
Populate each dimension using concise, factual language:

1. **WHO**
   - Primary human operators and decision-makers.
   - Distinct agent personas and service daemons (e.g., UI shell, terminal daemon, media daemon, router, auditor).
2. **WHAT**
   - Core functional deliverable or software system being constructed.
   - Target schemas, data structures, and database engines.
3. **WHEN**
   - Active project phase and immediate priority milestones.
   - Trigger conditions: real-time execution, daily batch handoff, or scheduled maintenance sweeps.
4. **WHERE**
   - Physical hardware nodes (e.g., phone, server board, workstation, cloud provider).
   - Filesystem paths, port bindings, and communication socket routes.
5. **WHY**
   - Technical root problem being solved (e.g., preventing LMK crashes, avoiding context window bloat, cost optimization).
   - Core architectural invariants and safety guarantees.
6. **HOW**
   - Underlying protocols, CLI commands, scripts, and libraries.
   - Dataflow sequence from ingress to final verification.

### 3. Format output
Present the final analysis as a markdown comparison table followed by an ASCII topology diagram, highlighting any open tickets or unresolved questions for operator review.

## In this stack

- Bulk extraction over long transcripts runs on Gemini through `tools/wiki-admin/gemini_infer.py w5h <file>` (it sends this procedure as the instruction). The output is a draft: it lands in `01-inbox/` and is reviewed like any other page.
- Operator turns are decisions; LLM text quoted in a transcript is proposal. Mark echoes of a decision by an LLM as `[LLM-echo]` (convention from `handoff/2026-10-24/extracts/wiki-admin-extract.md`).
