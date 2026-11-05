---
name: claude-perfectionist
description: "Activate when the user wants to edit, trim, audit, reorganize, or debug CLAUDE.md or any Claude Code config file. This covers: bloated or messy CLAUDE.md files; Claude running wrong commands or using the wrong package manager due to bad instructions; conflicting rules between CLAUDE.md and .claude/rules; broken subagent references; instruction harness audits across rules, hooks, settings, and MCP config; extracting review checklists or scoped content out of the root claude file; and creating or fixing pre-commit hooks or other Claude Code hooks. Trigger whenever the user's problem traces back to how Claude is configured or instructed — even if they say \"claude file\" instead of \"CLAUDE.md\". Skip general coding, non-config docs, test failures, CI pipelines, and conceptual questions about Claude."
disable-model-invocation: true
---

# Claude Perfectionist

## Overview

Audit the full Claude Code instruction harness. Treat root `CLAUDE.md` as the primary optimization target.

Optimize for **agent reliability per unit of always-on context**, not for the smallest possible file.

Bias toward serious audits of substantial harness systems. Do not optimize for small or bootstrap repos — a real project with a 200-line root file and multiple surfaces is the normal case.

## Non-goals

Do not optimize for any of these alone:
- minimal line count
- maximal extraction into many files
- clever structure for its own sake
- platform-specific behavior not supported by evidence
- abstract "best practices" detached from the repository

## Execution Modes

### Audit
Diagnose only. Return findings, tradeoffs, and open questions. Do not rewrite files.

### Propose
Diagnose and propose the minimum high-leverage changes. Name the target surface for each change. Draft snippets only when they clarify the recommendation.

### Apply
Apply the highest-leverage changes directly with file edits. Keep the edit set small and justified. Summarize what changed afterward.

Apply edits only files inside the repo being audited. User-level and managed files (e.g., `~/.claude/CLAUDE.md`) get proposed snippets, never direct edits.

If the user does not specify a mode, default to `propose`.

## Core Rules

### 1. Optimize the full harness

Evaluate the instruction system around the agent, not just one markdown file.

Primary target: root `CLAUDE.md`

In-scope surfaces when present:
- managed, user, project, ancestor, nested, and imported `CLAUDE.md`
- legacy `CLAUDE.local.md`
- `.claude/rules/`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/`
- `.claude/settings.json` and `.claude/settings.local.json`
- hooks defined in settings
- `.mcp.json` and repo-local MCP configuration
- canonical checked-in docs: `README`, `CONTRIBUTING`, `docs/`, ADRs, schemas, workflow guides
- review-only docs such as `REVIEW.md`

Audit root `CLAUDE.md` first, but do not assume the correct fix belongs there.

### 2. Use evidence before preference

Ground every meaningful finding in evidence. Be honest about what you can and cannot verify.

Evidence order:
1. repo-executable evidence: manifests, lockfiles, task runners, scripts, CI config, settings, hooks, schemas
2. repo-doc evidence: existing instructions, docs, conventions, examples
3. runtime evidence: loaded memories, hook output, logs, status indicators, observed task flow
4. official product docs: only for platform behavior
5. practitioner heuristics: optional tuning guidance, never the sole basis for a hard failure

Hard rules:
- do not invent commands, paths, package managers, or workflows
- do not recommend a verification command unless the repo supports it
- do not emit findings for surfaces you could not inspect
- never treat "not observed" as proof of absence

**Confidence levels.** Every finding has implicit or explicit confidence. Distinguish clearly between:
- **verified defect**: direct repo evidence confirms the problem
- **likely issue**: strong indirect evidence, but not fully proven
- **missing evidence**: cannot confirm or deny — flag it, do not assert
- **open question**: reasonable suspicion that depends on information you do not have

When evidence is incomplete or indirect, do not state a hard defect. Mark it as arguable or not fully verified. When unsure, **lower confidence instead of raising severity**.

### 3. Optimize for always-on context, not just file size

Classify content into four buckets:
- `always_on`: loaded at session start or in the default path
- `conditional`: loaded only when a path, command, or task makes it relevant
- `isolated`: separate-context workers such as subagents
- `zero_context`: deterministic enforcement — settings, hooks, permissions, CI, linters, schemas

Prefer moves that reduce always-on load without weakening reliability. A maintainability-only move is still valid, but label it correctly.

### 4. Prefer the right surface

Use the narrowest surface that still reliably covers the need.

- Root `CLAUDE.md`: durable shared rules, routing, key commands, verification entry points
- Conditional surfaces: path-specific instructions, uncommon workflows, deep reference material, review procedures
- Isolated surfaces: repeatable specialist work benefiting from separate context
- Zero-context enforcement: rules that must hold every time, formatting, lint, policy, permissions

Do not keep review-only guidance in always-on memory when a review-only surface exists.

### 5. Fix before you delete

The default action is not deletion. Use this remediation order:

1. **fix contradictions** — resolve conflicting instructions across surfaces
2. **add or repair verification** — ensure important workflows have concrete proof paths
3. **rewrite unclear instructions** — make existing guidance precise and actionable
4. **extract to a better surface** — when it improves routing or reduces context cost
5. **enforce with hooks/settings/CI** — when deterministic enforcement is more reliable than prose
6. **delete** — only when content is clearly stale, redundant, contradictory, or zero-value

For each instruction, ask: does it prevent a real failure? Does it route Claude correctly? Does it define how to verify success? Is it still true? If the answer to all is no, then delete.

### 6. Require verification

Every important workflow needs a concrete verification path.

Good verification is repo-grounded: a real test command, a build or lint command, a schema check, a deterministic review step, a direct observable artifact.

Bad verification: "make sure it works", "run appropriate tests" without saying how, a fabricated command, a human-only check when an automated one exists.

Missing verification is a high-severity problem when the workflow changes code, data, or external state.

### 7. Negative instructions need a replacement path

A prohibition without an alternative is weak. Prefer:
- not "do not guess commands" → "derive commands from package.json, Makefile, scripts/, CI, or documented workflow; if none exist, say evidence is missing"
- not "do not bloat CLAUDE.md" → "keep high-frequency shared rules in root; move rare or scoped detail to conditional surfaces"

### 8. Planning depends on uncertainty and risk, not LOC

Do not trigger planning from line count alone. Plan when: unclear requirements, multiple competing surfaces, irreversible actions, large blast radius, many coordinated edits, or low observability.

### 9. Keep the perfectionist progressively disclosed

Keep this `SKILL.md` compact. Push detailed schemas, scoring rules, and examples into `references/`. Treat the core file as the control plane.

## Finding Priority

Prioritize findings in this order. Do not let low-signal findings overshadow important ones.

1. **contradictions and broken routing** — direct conflicts between active surfaces
2. **missing verification paths** — important workflows with no proof path
3. **stale or misleading instructions** — commands or references that are wrong
4. **high always-on cost with low value** — bloat that hurts context budget without earning it
5. **weaker hygiene issues** — generic wording, light duplication, minor surface misplacement

A broad audit with many findings is acceptable if findings are strongly prioritized: critical issues first, weaker issues later.

## Findings

Each finding must include:
- `severity`: `critical | major | minor | info`
- `class`: one primary class
- `surface`: where the problem lives
- `evidence`: concrete files, configs, commands, or observed behavior
- `confidence`: `high` (verified) | `medium` (likely) | `low` (arguable)
- `remediation`: one of `keep | rewrite | delete | extract | enforce | investigate`
- `budget_impact`: `saves_always_on | maintainability_only | none | unknown`

Use classes such as: `missing_verification`, `contradiction`, `prose_only_invariant`, `always_on_bloat`, `misplaced_scoped_knowledge`, `review_only_misplacement`, `missing_routing`, `stale_or_unverified_command`, `external_only_source_of_truth`, `generic_low_signal_instruction`, `overlapping_skill_or_command`, `naive_planning_trigger`, `insufficient_evidence`.

Classification supports action. Use it to route decisions, not as an end in itself.

See `references/finding-model.md` for optional fields, tags, and worked examples.

## Severity Rules

Apply severity conservatively. When unsure, lower confidence instead of raising severity.

**Critical**: likely repeated failure or unsafe behavior. Typical: no verification on important workflows, direct contradictions between active instructions, fabricated commands presented as canonical.

**Major**: harness likely works worse than it should. Typical: broad always-on bloat, high-value scoped knowledge in root, missing routing, stale canonical instructions.

**Minor**: lower-risk cleanup. Typical: generic wording, weak examples, light duplication.

**Info**: optional improvements or useful observations.

If evidence is insufficient, do not invent a severity for it: state the severity the finding would have if confirmed, set confidence `low`, and use remediation `investigate` (class `insufficient_evidence`).

Confidence gates:
- low confidence usually caps severity at `minor`
- medium confidence can reach `major`
- `critical` normally requires high confidence

## Grades

Use one overall grade for the harness. Always show both the letter and the human meaning: "Grade: C — major cleanup needed", never just "Grade: C".

- `A` — **production-ready** — no critical findings, verification and routing are present, root context is lean enough
- `B` — **solid, minor issues** — no critical findings, but some major issues remain
- `C` — **major cleanup needed** — one critical finding or several major issues
- `D` — **minimal harness, significant gaps** — multiple critical findings or widespread misplacement and drift
- `F` — **actively misleading** — the harness contradicts itself or cannot be trusted on important workflows

Adjust down one step when any of these hold: important recommendations depend on unread surfaces; canonical commands appear stale or unverified; review-only or path-specific content dominates root memory; the proposal adds complexity without clear gain.

Adjust up one step only when all of these hold: clear verification paths, good routing to narrower surfaces, limited duplication, deterministic enforcement where appropriate.

A new or empty harness gets no grade (`unknown` in the machine report) — grades measure the trustworthiness of a harness that exists.

## Current Platform Notes

Last reviewed: 2026-07. Treat as working assumptions, not eternal truths. If a critical or major finding hinges on one of these behaviors, verify it against current official docs before asserting it.

- Claude Code memory files are automatically loaded; ancestor `CLAUDE.md` files are read recursively upward.
- Imported memory counts as loaded content; imports improve organization but do not remove context cost.
- Settings and hooks are hierarchical configuration, not just advisory prose.
- Subagents have their own context windows and tool access.
- Custom slash commands are conditional task surfaces, not always-on memory.
- Path- or type-scoped rules load only when matching files are in play; unconditional rules count as always-on memory. Skill descriptions are always-on; skill bodies load only on trigger.
- `CLAUDE.local.md` is legacy input. Do not recommend it as the default.

## Workflow

### Phase 1. Inventory surfaces
List every relevant surface you can inspect. Use this checklist:
- project memory: root `CLAUDE.md` and nested `CLAUDE.md` files — glob `**/CLAUDE.md`, excluding dependency directories
- ancestor memory: walk parent directories upward from the repo root
- user memory: `~/.claude/CLAUDE.md`
- legacy memory: `CLAUDE.local.md`
- imports: scan every read memory file for `@path` lines and follow them
- conditional and isolated surfaces: `.claude/rules/`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/*/SKILL.md`
- settings and hooks: `.claude/settings.json` and `.claude/settings.local.json` — read the `hooks` and `permissions` keys, not just the file names
- MCP: `.mcp.json`
- canonical docs: `README`, `CONTRIBUTING`, `docs/`, ADRs, review-only docs such as `REVIEW.md`

Mark unread surfaces and do not speculate about them. If root `CLAUDE.md` is absent, inspect the rest of the harness before treating that as a failure.

### Phase 2. Build the assembled context map
For each surface: always-on, conditional, isolated, or zero-context? Is the knowledge correctly placed? Does it duplicate another source?

The always-on set is: root `CLAUDE.md` + user and ancestor memory + everything reachable via imports + unconditionally loaded rules. Path- or type-scoped rules, commands, skill bodies, and subagents are conditional or isolated.

Estimate always-on cost in tokens: count characters with native tools (`wc -c`, `(Get-Item file).Length`) and divide by 4. Round the result, label it an estimate, and use it for comparison — not as an exact cost.

### Phase 3. Classify each important instruction
For each block worth keeping or changing: `keep`, `rewrite`, `delete`, `extract`, `enforce`, or `investigate`. Name target surfaces and enforcement mechanisms.

### Phase 4. Propose the minimum effective change set
Favor changes with clear leverage. Avoid fifteen micro-extractions when three changes solve most of the problem.

### Phase 5. Validate the proposal
Check every change against repo evidence. Confirm target surfaces are appropriate. Verify no recommendation depends on unread files or imagined tools.

### Phase 6. Add runtime validation
Define a small regression pack. For each task: expected route, expected verification step, expected artifact. Include only in the appendix unless the user asks for it.

## Output Format

Return a human-readable report. Emit the machine-readable report only when the user requests it (e.g., `--json` or "include the machine report").

### Human report: default audit

```
# Verdict
[2–4 sentences. Is the harness trustworthy? Where does it fail? What to fix first.]

Grade: [letter] — [human meaning]

## Top findings
| Severity | Problem | Why it matters | Action |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## Recommended changes
1. [Highest-leverage change]
2. ...

## Open questions
- [Only blocker-level questions]

## Appendix
[Only when needed: harness map, runtime validation plan, longer evidence, rewritten snippets]
```

**Style rules:**
- Write for a technical reader, not the optimizer author.
- Prefer plain words over internal jargon. Say "routing to agents that don't exist" not "phantom subagent routing". Say "per-service rule files" not "scoped surfaces".
- Make every action text specific enough that someone could do it without reading the rest of the report. Bad: "Extract to scoped surfaces". Good: "Move service-specific guidance from root CLAUDE.md into per-service rule files (e.g., `.claude/rules/worker.md`)". Bad: "Add commands". Good: "Document `pnpm test:e2e` and `pnpm typecheck` in the Commands section — both already exist in package.json".
- Keep the default report to one screen when possible.
- Show at most 5 findings unless the user asks for a full dump.
- Show at most 7 recommended changes unless the repo is genuinely broad.
- Use appendix content only when it changes the decision or helps implementation.

### Human report: new or empty harness

```
# Verdict
This repo does not yet have a trustworthy instruction harness. The right first step is a minimal root CLAUDE.md.

## Proposed root CLAUDE.md
[Concrete scaffold]

## Why this is enough for now
- [Reason]

## Open questions
- [Only if the scaffold depends on missing evidence]
```

### Human report: contradiction debug

```
# Verdict
The harness contains direct contradictions. Fix these before any cosmetic cleanup.

Grade: [letter] — [human meaning]

## Contradictions
| Surface | Conflict | Canonical fix |
| --- | --- | --- |
| ... | ... | ... |

## Corrected snippet
[Short corrected snippet]

## Follow-up
- [Optional next step]
```

### Machine report
Only when requested: emit JSON matching `references/report-schema.json`. Keep summary and notes short. Prefer omission over fake precision. Use machine labels in the JSON; keep them out of the human prose unless needed.

## Error Modes

Avoid these failures:
- inventing a complex harness for a simple repo
- recommending extractions for surfaces that do not exist or could not be inspected
- creating a long list of low-value findings instead of the few that matter most
- treating size heuristics as hard blockers
- confusing maintainability wins with real context-budget savings
- moving instructions without improving routing, verification, or enforcement
- asserting defects based on incomplete evidence without marking confidence
- defaulting to deletion when the content needs fixing, not removing

## References

Consult these files only when needed:
- `references/finding-model.md` for optional finding fields, tags, and worked examples
- `references/examples.md` for annotated before/after examples
- `references/report-schema.json` for the machine-readable output schema
