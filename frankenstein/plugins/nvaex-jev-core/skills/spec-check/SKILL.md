---
name: spec-check
description: Use at the start of a coding task to capture requirements, and whenever you are about to say done, to compare what was built against them.
---
# Spec check (requirements versus built)

Static reading only. Do not run the project to do this.

**Start:** write `SPEC_CHECKLIST.md` with `Task: <kebab-slug>`, one checkbox per requirement (testable wording), and an Open questions list. Same slug: update in place. New task: rename the old file to `SPEC_CHECKLIST.<old-slug>.md` first; never overwrite.

**Before saying done:** for each item, Grep its identifiers, Read only the matched ranges, and classify:
- done (cite file:line)
- missing (nothing implements it)
- partial (one case handled, others skipped, e.g. one role of three)
- silent-fail (error swallowed, guard inside a try/catch that drops it, missing await)
- stub (guard or auth function ignoring its parameters and returning a constant)
- hardcoded (TODO plus a literal where logic belongs)
- missing state (loading, error, empty)
- mismatch (API succeeds but the UI never shows it, or a UI-hidden action is still callable)

Report `MISSING n / PARTIAL n / DONE n` with evidence, fix the gaps, re-check. Tests passing is not the spec met. Scope to a diff with `git diff --name-only <base>...HEAD` when the change is large; validate the ref as one plain token first.
