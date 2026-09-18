# Experiment Continuation Instructions

This experiment is the local calibrated-LLM/classifier benchmark tracked by `Pukujan/test-repo#3`.

## Start here

1. Read `HANDOFF.md`.
2. Read `PLAN.md`.
3. Read `OBSERVABILITY.md`.
4. Read the latest checkpoint named by `state.json`.
5. Verify the local dataset manifest/digest and frozen split IDs before running anything.
6. Do not alter the final test set during iteration.

## Scope boundary

Allowed work:

- LLM closed-set classification;
- empirical probability calibration;
- Model2Vec/Potion training and evaluation;
- optional SetFit baseline;
- classification/calibration metrics;
- error analysis and controlled iteration;
- benchmark observability required to reproduce and debug these runs.

Do not add:

- triage or abstention systems;
- multi-judge consensus/jury;
- model routing;
- semantic graph/RAG work;
- unrelated deployment/orchestration infrastructure.

Observability must remain scoped to the benchmark. Do not turn it into an independent platform project.

## Observability rules

- Use stable `experiment_id`, `run_id`, and `sample_id` everywhere.
- Propagate `trace_id` across the benchmark where practical.
- OpenTelemetry is the canonical instrumentation/correlation layer.
- Langfuse is the primary trace/debug UI, not the sole evidence store.
- Promptfoo is an eval runner when useful, not the calibration source of truth.
- Prometheus/Grafana are for local serving/runtime metrics when needed.
- Produce structured local events or a safe digest/manifest of them for every run.
- Reconcile expected samples, completed predictions, unique sample IDs, traces, and events.
- Never mark observability PASS from screenshots or prose alone.
- Dashboard aggregates must agree with deterministic metric artifacts; disagreements are defects to investigate.
- Respect the telemetry content mode in `OBSERVABILITY.md`; private source text must not leak into traces/logs.

## Data boundary

The repository is public.

- Never commit private corpora, credentials, proprietary documents, API keys, model weights, or telemetry credentials.
- Prefer dataset manifests, stable row IDs, hashes, aggregate metrics, and sanitized fixtures.
- If raw predictions/events contain sensitive text, keep them local and commit only safe derived metrics plus a digest/path description.
- The calibration and test splits must be disjoint.
- The final test split is evaluation-only.

## Handoff

Before stopping:

1. append a numbered checkpoint;
2. update `state.json` and relevant `checks.json` entries;
3. attach durable evidence to every PASS;
4. reconcile observability for any executed run;
5. run `python tools/lab.py sync`;
6. run `python tools/lab.py validate`;
7. commit the synchronized state.
