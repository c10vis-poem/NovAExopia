---
name: verify-before-done
description: Use before claiming work is done, fixed, passing or merged, or relaying a subagent's success. Run a command first.
---
# Verify before done

No completion claim without a command run this turn. "Should work" is not a result.

1. Name the command that proves the claim.
2. Run it fully and fresh. Read the output and exit code.
3. State the result with the evidence, or the real failing state.

| Claim | Proof |
|---|---|
| Tests pass | full run, 0 failures (lint or build is not it) |
| Build ok | build exits 0 |
| Bug fixed | original symptom re-run and gone |
| Regression test | red then green: revert fix, it fails; restore, it passes |
| Subagent finished | read its diff; never trust its report |
| Requirements met | re-read the spec line by line |
| New code works | find its call-site in non-test code, then drive the real path (request, job, CLI), not a test that inserts straight into storage |

Check the criterion, not just the run. A check proves only what it measured: for any transform (transcribe, scrape, migrate, convert) assert coverage (rows, pages, duration in vs out), not "ran without error".

Red flags: "should", "probably", "Done!" before running, commit without a fresh run, partial run offered as full, trusting an agent's success line.
