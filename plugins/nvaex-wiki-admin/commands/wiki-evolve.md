---
description: Propose, evaluate, apply or roll back an evidence-linked skill improvement (trimmed llm-wiki evolve).
argument-hint: "<propose|evaluate|apply|rollback|history> ..."
---

Use the `llm-wiki` skill and read its `references/evolution-workflow.md` first.

Request: $ARGUMENTS

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wiki_evolve.py --help` for the verbs. `apply` (graduating repeated Q&A or a reviewed proposal into a permanent page/skill) only on an evaluated, reviewed proposal and the operator's explicit approval of that named change. `history` is read-only. Never bypass failed evaluations.
