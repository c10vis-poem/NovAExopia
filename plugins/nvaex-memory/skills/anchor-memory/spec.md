# Anchor `@meta` anchor spec

A memory entry may carry a machine-checkable `@meta` block. The linter
(`scripts/memory_lint.py`) evaluates each anchor against the live repo and
flags entries that have drifted.

## Block syntax

```
<!-- @meta
id: unique-kebab-id
status: active            # active | superseded | retracted
supersedes: older-id      # optional
anchors:
  - kind: file_exists
    file: path/to/file
    expect: present        # present | absent
  - kind: file_grep
    file: path/to/file
    pattern: "some string"
    expect: present        # present | absent | count:N
    scope_after: "## Heading"   # optional: only search after this marker
  - kind: json_field
    file: path/to/file.json
    field: some_key
    expect: ">= 0.9"       # supports >= <= == > < or exact string
  - kind: golden_metric
    file: path/to/table.csv
    column: passed
    match_value: "True"
    expect: "count >= 10"
-->
```

## Finding kinds
- `DRIFT` — anchor evaluated but reality disagrees (entry is stale).
- `BROKEN` — anchor can't be evaluated (missing file/field/marker).
- `DANGLING` — `supersedes` points at an unknown id.
- `DUPLICATE` — same `id` used by more than one entry.

Entries with `status: superseded|retracted` are skipped during anchor eval.
