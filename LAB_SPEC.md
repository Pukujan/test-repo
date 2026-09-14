# Lab Specification v1

## Purpose

This repository is a cross-project experiment ledger. It optimizes for reproducibility, durable continuation, exact evidence, and safe handoff between local/cloud agents.

## Identity hierarchy

```text
Repository
  -> Project
      -> Experiment
          -> Run
```

- A **project** groups related experiments.
- An **experiment** owns one durable question and acceptance checklist.
- A **run** is one concrete execution attempt/configuration.
- A **checkpoint** records continuation state between sessions; checkpoints are append-only.

## Required experiment files

Each experiment directory must contain:

- `README.md`
- `AGENTS.md`
- `experiment.json`
- `state.json`
- `checks.json`
- `HANDOFF.md` (generated)
- `CHECKLIST.md` (generated)
- `checkpoints/`
- `inputs/`

`runs/` appears once executions begin. `conclusion.md` is required when the experiment is `completed`.

## State lifecycle

Allowed experiment states:

`planned -> ready -> running -> blocked -> running -> completed -> superseded`

Not every experiment uses every state.

Allowed check states:

`pending`, `running`, `pass`, `fail`, `blocked`, `not_applicable`.

## Evidence rules

A PASS requires durable evidence. Evidence should point to one or more of:

- committed result/run file;
- exact upstream commit/PR/issue/run reference;
- immutable source artifact digest/location;
- deterministic command output preserved in the experiment.

Model prose alone is not test evidence.

## Source rules

Record these separately:

- **fidelity** — whether captured material is `verbatim`, `reconstructed`, or `mixed`;
- **completeness** — whether acquisition is `complete`, `incomplete`, or `unknown`.

A verbatim capture may still be incomplete.

Raw captured bytes are immutable inputs. Parsing, semantic extraction, summaries, indexes, embeddings, and reports are derived.

## Runs

A run should record exact upstream revision, command/configuration, environment facts relevant to the result, start/end timestamps when available, output/metric references, and terminal result. A retry with the same experiment question is another run, not another experiment.

## Checkpoints and handoffs

Checkpoint files are immutable after commit. `state.json` is the mutable current pointer. `HANDOFF.md` is generated from current state and is optimized for a fresh agent/session.

## Generated views

`python tools/lab.py sync` generates:

- experiment `HANDOFF.md`;
- experiment `CHECKLIST.md`;
- root `CATALOG.md`;
- root `catalog.json`.

CI must reject stale generated views.

## Public-repository boundary

This repository is public unless that setting is changed externally. Do not store credentials, private conversations, private exports, or proprietary large artifacts here. Store safe evidence pointers plus digests when bytes cannot live in Git.

## Completion

An experiment may be marked `completed` only when:

- required checks have terminal states;
- at least one run exists if execution was required;
- `conclusion.md` states the result, limitations, evidence, and follow-up;
- generated views are synchronized;
- validation passes.