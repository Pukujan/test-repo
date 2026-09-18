# Checkpoint 0002 — Observability contract

## Decision

Observability is now a required part of the classification benchmark's evidence contract.

This does not create a separate observability project. It exists only to make the calibrated-LLM versus local-classifier experiment reproducible, diagnosable, and safe to hand off across sessions/agents.

## Tool responsibilities

- OpenTelemetry: canonical instrumentation and trace-correlation contract.
- Langfuse: primary human-facing LLM/application trace and quality-debug UI.
- Promptfoo: optional evaluation/test runner for prompt/model matrices and assertions.
- Prometheus + Grafana: optional local model-server/runtime metrics, especially for vLLM.
- Structured JSONL events: detailed local forensic log and durable run artifact when safe.
- GitHub lab state/checkpoints: durable experiment continuation and acceptance evidence.

No dashboard is accepted as the sole source of truth.

## Correlation contract

Every evaluated sample must have stable:

- experiment ID;
- run ID;
- sample ID;
- dataset/split/schema identifiers;
- model/prompt/classifier/calibrator identifiers;
- trace ID when tracing is enabled.

The same sample ID must connect row-level predictions, events, traces, evaluation results, and run-level aggregates.

## Privacy contract

Telemetry must use an explicit content mode:

- none;
- hash;
- sanitized;
- full.

Private domain corpora should default to hash or sanitized. Raw private text, credentials, model weights, and telemetry secrets do not belong in this public repository.

## Reconciliation contract

A run must record expected sample count, completed predictions, unique IDs, trace/event counts, missing IDs, duplicates, and whether aggregates can be regenerated from row-level results.

If telemetry is incomplete, classification/calibration results may still be recorded, but observability checks cannot be marked PASS.

## Run 1 gate

Before running the full benchmark, execute a small smoke subset and prove:

1. IDs propagate correctly;
2. traces are inspectable;
3. structured events are emitted;
4. configured privacy/content rules are obeyed;
5. sample/prediction/trace/event counts reconcile;
6. aggregate metrics can be regenerated.

Then run the full calibrated-LLM and Potion/Model2Vec baselines on the same frozen test IDs.

## Durable files

The detailed contract is in `OBSERVABILITY.md`.

`PLAN.md`, `AGENTS.md`, `checks.json`, and `state.json` were updated so future agents cannot treat observability as optional cleanup.

No benchmark has been executed yet and no new PASS is claimed.
