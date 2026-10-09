# An introduction to the integrated agent project-work stack

*Exploratory draft — 2026-10-09. Written under the owner-directed correction recorded on
[issue #8](https://github.com/Pukujan/test-repo/issues/8)
(marker `acs-framing-supersession-2026-10-08`). Every claim below is bounded by
`workspace/PRODUCT_CONTEXT.md`; see "Open unknowns" for what is deliberately not asserted.*

## The problem: a project that outlives the session

Working on a long-running project with AI agents is easy to start and hard to keep straight.
A project accumulates many sessions, and the agents, tools, and people around it change over
time. What gets lost is rarely the code — it is the thread: what was decided, why, what has
already been tried, what is safe to do next, and who is allowed to decide.

Most of that cost is mental. Someone has to hold the state of the work across sessions, notice
when a plan has been overtaken by a newer decision, keep several agents from stepping on each
other, and turn raw activity into something another person can actually read. The stack
described here is four separate products, each aimed at one part of that load.

## Four responsibilities, deliberately separate

**PCM — Project Continuity Modules** carries project continuity. It is a GitHub-first CLI and
contract for long-horizon tasks: checkpoints, resumed handoffs, evidence links, request-ID retry
safety, PR/CI progression, and reconciliation of authority when a plan is superseded. PCM is not
a Temporal-compatible event engine, and it cannot by itself certify the product meaning of a
drafted page.

**ACS — Agent Custom Setup** coordinates agents. It provides install/hotload, a decision-boss
lease, join-order roles, a GitHub-oriented claim queue, an agent-less watchdog, and a
propose-to-PR workflow. Coordination is not truth: holding a seat or a lease does not establish
a fact or authorize a new position.

**OIO — Observational Issue Ops** handles intake of observations and operations. It offers a
shared filing ontology for observational and operational issue evidence, with filer provenance
and triage. Filing an observation is not authorization to implement it.

**CGM — Content Generation Modules** helps with human-facing communication and media: writing,
context and brand, human readability, asset naming, visual direction, images, and HTML
assistance. It is not a guarantee of product research or buyer insight.

These four are related but have distinct ownership. They are not interchangeable, and no one of
them substitutes for another.

## How they fit together

The continuity layer keeps a project's history and decisions recoverable. The coordination layer
keeps multiple agents working on that project without collision. The intake layer gives
observations and operational evidence a consistent, attributed home. The communication layer
turns that material into something a person can read. Together they aim at a single outcome: a
long-running project stays intelligible and resumable even as the sessions and agents around it
change.

## What this draft does not claim

- No deployment guarantees, buyer quotes, audience research, or named personas.
- No claim that any layer makes the work autonomously correct.
- No invented clock-time scenarios.
- The pinned PCM/ACS components this experiment references are draft-PR code, not certified
  stack releases.

## Open unknowns

- The intended audience and the final acceptance criteria belong to the live issue; this draft
  does not invent them.
- No concrete worked example (if any is wanted) has been specified by the owner.
- Whether the final page should carry repo/protocol evidence links, and at what depth, is not
  yet settled by the current accepted scope.
