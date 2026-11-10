# Skill evolution (wiki_evolve.py)

Stdlib. Candidates are tested in copies; the installed skill changes only on `apply`. The loop driver and agent adapters of upstream llm-wiki are not shipped: the runner is a trusted local executable you supply (it is not a sandbox).

## Cycle
1. `capture --raw <raw> --record experience.json`: save a verified experience as immutable JSON.
2. `propose --id ID --skill <skill-dir> --target <file> --candidate <new-file> --evidence <wiki-page> --reason "..."`: snapshot the skill and stage one evidence-linked edit.
3. `evaluate ID --suite suite.json --runner runner.json --model M --tools T [--repeats 3]`: run baseline and candidate through the runner on the suite; only a measured improvement is eligible.
4. Review with `show ID`, then `apply ID` (needs the operator's named approval of that ID). `rollback ID` restores the original and refuses if the file changed since.
5. `history` lists runs and decisions; `export` / `verify-bundle` archive and check evidence.

Rules: never apply a failed or unevaluated proposal; a run that selects no change is a valid result; a runtime failure never produces an apply-ready proposal. `python3 scripts/wiki_evolve.py <verb> --help` has the flags.

For small behavioural rules from user corrections, use the lighter `rule-learning` skill instead.
