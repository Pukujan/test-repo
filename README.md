# Durable Experiment Lab

This repository is the shared laboratory for reproducible experiments across projects.

The durable unit is an **experiment**. An experiment may have multiple **runs**, but it keeps one question, one checklist, one append-only checkpoint history, and one current handoff.

## Layout

```text
projects/<project>/experiments/<YYYY-MM-DD>_<slug>/
```

Each experiment contains:

- `experiment.json` — what is being tested and exact upstream revisions;
- `state.json` — current resumable state;
- `checks.json` — machine-readable acceptance checklist;
- `checkpoints/` — append-only continuation history;
- `inputs/` — source fixtures/evidence pointers;
- `runs/` — actual executions and results;
- `HANDOFF.md` — generated current resume page;
- `CHECKLIST.md` — generated human checklist;
- `conclusion.md` — final conclusion once completed.

## Resume any experiment

A new local/cloud ChatGPT, Claude, Codex, or other agent should:

1. read root `AGENTS.md`;
2. read the project `AGENTS.md`;
3. read the experiment `HANDOFF.md` and experiment-local `AGENTS.md`;
4. read the last checkpoint;
5. verify live upstream refs;
6. continue from the recorded exact next action.

Do not rely on chat history as the only record of experiment state.

## Commands

```bash
python tools/lab.py sync
python tools/lab.py validate
```

`sync` regenerates human-facing views from machine-readable state. `validate` is the CI contract.

## First experiment

`projects/fossil/experiments/2026-09-14_shared-chat-completeness/` tests FOSSIL shared-chat ingestion using a real long ChatGPT share and tracks `Pukujan/fossil-core#247`.

## Privacy

This repository is currently public. Do not commit secrets, private transcripts, credentials, or non-public source bytes. Public-share captures may be committed only after verifying they are intentionally public and suitable for redistribution. Large or private durable artifacts should be stored elsewhere and referenced by digest/location.