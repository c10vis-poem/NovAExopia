# Finding Model

Additive detail for the core finding defined in `SKILL.md` — required fields, classes,
severity, confidence gates, and grades all live there. This file only adds what `SKILL.md`
does not: optional fields, routing tags, edge-case rules, and worked examples.

## Optional fields

Use only when useful:
- `target_surface`: destination when `extract` is chosen
- `enforcement_mechanism`: hook, setting, permission, CI, linter, schema
- `secondary_tags`: short routing tags such as `review_only`, `path_scoped`, `version_sensitive`, `shared_policy`, `legacy_surface`
- `notes`: brief nuance or caveat

## Low-confidence exceptions

Low-confidence findings should rarely be `critical`. Exceptions:
- direct contradictions in inspected active surfaces
- fabricated command/path presented as canonical
- important workflow with no concrete verification path despite strong repo evidence that verification matters

## Good finding example

```yaml
severity: major
class: misplaced_scoped_knowledge
surface: CLAUDE.md
confidence: high
evidence:
  - CLAUDE.md contains frontend-only review checklist
  - repo has .claude/rules/frontend.md
remediation: extract
target_surface: .claude/rules/frontend.md
budget_impact: saves_always_on
```

## Good enforcement example

```yaml
severity: critical
class: prose_only_invariant
surface: CLAUDE.md
confidence: high
evidence:
  - CLAUDE.md says always run lint before stop
  - repo has CI and local lint command
remediation: enforce
enforcement_mechanism: hook
budget_impact: maintainability_only
```
