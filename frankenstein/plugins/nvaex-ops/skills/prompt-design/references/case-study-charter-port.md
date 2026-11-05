# Case study: porting a prompt-engineering charter across harnesses

The constructed example (`example-support-agent-recast.md`) shows this doctrine's
output. This file shows its process — a real session in which the doctrine, its own
authoring artifacts, and its verification machinery all ran at once, including two
repairs of the author's own work. Events are as recorded in the transcript; where
evidence ran out, this file says so rather than rounding up.

## Setting

The originating deployment ran a prompt-engineering charter as standing instructions:
three-requirement intake, ask-don't-assume with a scoped [ASSUMPTION] escape hatch,
operator precedence with a duty to voice disagreement, convergence-based verification
with independence counting, and helper roles (advisor, verifiers, synthesis, second
opinion) mapped to concrete tools. The session's tasks, in order: refine that charter;
verify environment facts for a target harness (skill format, model tiers); read and
critique a third-party prompt-design skill (`intrinsic-prompt-design`, MIT); port the
charter into a skill for that harness; produce supporting references. The SKILL.md you
are reading descends from that session.

## Episodes

### 1. Inventory before integration

Before critiquing external material, its directory was enumerated via the host git API
(authoritative by construction) rather than the rendered HTML page (only weak
corroboration); file sizes were recorded; the license was checked (MIT) before any
borrowing was considered. A fact-check subagent given the same enumeration task
returned exactly: "I have no web access tools and cannot reach GitHub at all." It was
not briefed for fetching again. Capability matching is the brief-writer's job; the
subagent's honest refusal was the correct outcome of an incorrect brief.

### 2. Verifying target-environment facts

Two first-party documentation properties for the target harness disagreed about whether
`name`/`description` are required fields in directory-form skills. Sources sharing an
author count as one, so independence could not be established; the resolution was
defensive design — provide both fields explicitly — plus an open question for the
operator. (The harness later answered it: one field was dropped as unsupported and its
trigger content merged into the description.) Separately, operator-supplied model facts
(two model tiers, reasoning-effort controls) were checked against platform
documentation and confirmed. Operator say-so does not waive verification duty; nor
does confirmation require ceremony when a claim checks out immediately.

### 3. Tooling failure: read the observed failure, not the assumed one

A long advisory call failed with "No stream data within 30s" while a one-line ping
succeeded. First repair hypothesis: payload too large — split into bounded passes. The
falsifier arrived immediately: even a 180-word substantive probe failed, while trivial
pings kept succeeding. Content size was not the discriminant; latency was (the model's
actual replies later proved to take ~400s against a fixed 30s stream window, a
parameter the caller could not set). The working repair was an operator relay: the
operator retrieved the completed outputs from logs and pasted them in. Three durable
rules fell out: diagnose what you observed, not what you expected; preserve the failing
artifact — the timed-out call — rather than pretending it succeeded; never present
helper input you did not receive as if received.

### 4. Convergent critique, adversarial adjudication

The third-party skill received four independent passes — two from the session's
strongest advisor (87 and 51 findings), one from the nuance specialist (6 findings),
and one from the author-model. Convergence was treated as signal (reasons-everywhere
needs scoping; hard constraints must stay hard; the trust-gap mechanism should not
transfer). Divergences were adjudicated, not averaged:

- The advisor graded the skill's missing security/hierarchy sections high-severity.
  The reviewer demoted that verdict for the skill's sandboxed home harness and promoted
  it only into the general-purpose port. Severity is deployment-relative.
- The advisor recommended replacing the skill's interrupt-shaped routing description.
  The reviewer held position: the author's own experiment record labels the attention
  effect untested (n=0) and frames the new wording as a candidate under a planned live
  test; "replace now" would discard an honestly-labeled in-flight experiment. Held,
  with reasons, without escalation or retreat.
- The advisor's claim that stating a failure mode "primes" the model into producing it
  was logged as an open hypothesis rather than adopted. No-invented-facts applies
  hardest to the most authoritative voice in the room.
- Independence was discounted where due: the experiments' "3 independent judges" were
  three samples of one model — one source type, not three.

### 5. Caught by one's own reference file

The constructed example was sent to a fresh nuance pass before shipping, targeted at
exactly one question: does the example violate the doctrine it claims to demonstrate?
It did, in three places — failure-mode narratives embedded inside hard-constraint
bullets (the violation its own changelog claimed to repair); a reason attached to a
mechanical prohibition ("it logs a supervisor touch"); and the human-escalation path, a
guardrail, written as a dismissible judgment default. All three findings were adopted,
one with modification (escalation restructured as a hard trigger floor with judgment
above it), each change logged with its reason. The cheapest pass in the stack caught
the most expensive mistake. This episode is why this file exists.

### 6. Generative vs. self-undermining, as triage

Reviewing the third-party skill's internal tensions produced two classes, not one. Its
self-reference (a skill about instruction, instructing the reader) was classified
generative — named and left standing. Its unqualified "stated trust constructs
capability" mechanism was classified self-undermining for general use — not
transferred. Finding tensions is the detector; the
keep-fix distinction is the doctrine.

## What this session could not establish

- Whether the ported skill outperforms the original charter, or no charter: untested.
  The deployment described here is argued, not measured.
- Any attention-capture claim about routing descriptions: n=0 in every experiment
  discussed, including the ones this session praised for their hygiene.
- Whether cheap-instance delegation in the target harness (which has no dedicated
  subagent servers) preserves the independence the verification section wants:
  designed for, not proven.
- The advisor timeout was diagnosed and worked around (relay), never fixed.

## Session event → charter element exercised

| Episode | Element exercised |
|---|---|
| 1 | Verification duty; helper capability matching |
| 2 | Independence counting; [ASSUMPTION] discipline; open questions |
| 3 | Repair loop (actual failure, minimal patch); no simulated verification |
| 4 | Challenge handling (bilateral); proportionality; operator precedence (relay) |
| 5 | Repair loop on own output; fresh-frame verification; motivated edits logged |
| 6 | Generative vs. self-undermining classification |

## Moral, kept short

The doctrine proved itself not when it was obeyed but when it was caught disobeying
itself — by a smaller model, on an artifact the author had already reviewed — and the
fix was logging the catch rather than hiding it. Port that reflex, not the prose.
