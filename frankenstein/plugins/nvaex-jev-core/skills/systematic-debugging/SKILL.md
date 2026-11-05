---
name: systematic-debugging
description: Use for any bug, test failure, build failure or unexpected behaviour, before proposing a fix.
---
# Systematic debugging

No fix without a root cause. A symptom patch is a second bug.

1. **Investigate.** Read the whole error and stack. Reproduce it reliably. Check what changed (diff, deps, config, env). If the system has layers, log what enters and leaves each boundary once, find the layer that breaks, then dig there. Trace bad values back up the call chain to the source.
2. **Compare.** Find similar working code; list every difference, however small.
3. **Hypothesise.** State one cause and the evidence for it. Change one variable at a time. Test the smallest change that would confirm it.
4. **Fix.** Write a failing test first, make one fix at the cause, run it, then the suite.

Stop rule: two failed fixes means your model of the system is wrong. Go back to step 1. Three means stop and use the fail-loud-escalate skill; do not try variation four.

Under time pressure or when "it's obviously X": still do step 1. Guessing is slower.
