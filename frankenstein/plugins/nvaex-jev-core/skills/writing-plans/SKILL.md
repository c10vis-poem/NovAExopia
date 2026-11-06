---
name: writing-plans
description: Use when a spec spans several steps, before touching code. Writes a task-by-task plan another agent can execute.
---
# Writing plans

Write for an executor who has not seen this code or spec. Exact paths, exact names, checkable steps.

**Header:** goal (one sentence), approach (2-3 sentences), stack, spec path, global constraints copied verbatim from the spec (versions, naming, platform).

**Map files first:** which file is created or changed and its one responsibility. Follow existing patterns; split by responsibility, not layer.

**Tasks:** the smallest unit with its own test cycle. Fold setup and docs into the task that needs them. Each task lists: Files (create/modify with line ranges, test), Consumes (exact signatures from earlier tasks), Produces (exact names and types later tasks rely on), then checkbox steps:
- [ ] write the failing test (show it)
- [ ] run it, expect FAIL (exact command)
- [ ] implement (signature; one line on approach)
- [ ] run it, expect PASS
- [ ] commit

**Review focus:** list the five inputs or failure modes the spec implies but no test exercises; add a pinning test to the task that owns each. The spec's silence is not permission to break.

No placeholders ("handle errors", "etc."). If the spec spans independent subsystems, write one plan per subsystem. Save under `docs/plans/YYYY-MM-DD-<name>.md` unless the project says otherwise.
