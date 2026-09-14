# Agent Continuation Contract

This repository exists so experiments can survive lost sessions, tool changes, and agent handoffs.

## Read order

1. Root `README.md` and `LAB_SPEC.md`.
2. `projects/<project>/AGENTS.md`.
3. Experiment-local `AGENTS.md`.
4. Experiment `HANDOFF.md`.
5. The checkpoint named by `state.json.last_checkpoint`.
6. Live upstream repo/issue/PR state before any mutation.

## Non-negotiable rules

- Never invent PASS evidence.
- Never mark a check `pass` without a durable evidence reference.
- Never rewrite an existing committed checkpoint; append a new corrective checkpoint instead.
- Preserve raw source bytes when captured; derived parsing/summaries are not substitutes for source evidence.
- Distinguish source fidelity (`verbatim`, `reconstructed`, `mixed`) from capture completeness (`complete`, `incomplete`, `unknown`).
- Exact Git upstream revisions in experiments must be 40-character commit SHAs.
- One experiment answers one durable question; retries belong under `runs/` unless the question changes.
- Large/transient generated artifacts do not become durable merely because CI produced them.
- Never commit secrets or private source material to this public repository.
- Before handoff: update `state.json` and `checks.json`, append a checkpoint, run `python tools/lab.py sync`, then `python tools/lab.py validate`.

## Checkpoint rule

`checkpoints/` is append-only experimental history. If checkpoint 0002 is later found wrong, create checkpoint 0003 explaining the correction. Do not silently edit history.

## Generated files

Do not manually edit:

- root `CATALOG.md` / `catalog.json`;
- experiment `HANDOFF.md`;
- experiment `CHECKLIST.md`.

Generate them with:

```bash
python tools/lab.py sync
```

CI runs:

```bash
python tools/lab.py validate
```

## Handoff language

A fresh agent should be able to receive only:

> Read `<experiment>/HANDOFF.md` and continue from the last durable checkpoint.

and safely resume without requiring the previous chat session.