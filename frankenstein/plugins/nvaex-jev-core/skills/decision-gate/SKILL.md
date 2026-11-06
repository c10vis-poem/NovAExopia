---
name: decision-gate
description: "Stop at human decision gates in an agentic build: starting a feature, approving a plan, judging a test, shipping."
---
# Decision gate

The agent runs the stretches between gates; this skill runs the gates. Never decide for the human.

**Gate ∞, always first:** ask in one line what breaks if this is wrong and whether it can be undone. Then pick the set:
- money, customer data, auth, irreversible: full set 0-9 below, in order
- cosmetic and reversible: two gates (3 right small fix, 9 ship it)
- unsure: treat as higher stakes
Also size width: can two pieces run without each other's output? If not, one loop. State the chosen set to the human; that statement is the gate.

**Full set:** 0 should this exist; 1 who is it for and what is a win; 2 which direction; 3 right plan and scope; 4 is the architecture sane; 5 off the rails; 6 does the test prove it; 7 is the cost right; 8 risk acceptable to ship; 9 ship now, to whom.

**At each gate:** name it, present the decision the human owns (not a recommendation), show the evidence the pipeline produced (plan, test, diff, cost), then stop and wait. If the gate is outside the human's expertise, steelman the opposite, list what the change does not do, name what would turn red, propose a cheaper tier, and still let them decide.

A gate with no tool behind it is still a gate. Match rigor to blast radius, not habit.
