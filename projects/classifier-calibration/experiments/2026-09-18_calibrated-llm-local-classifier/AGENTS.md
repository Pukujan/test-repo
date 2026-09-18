# Experiment Continuation Instructions

This experiment is the local calibrated-LLM/classifier benchmark tracked by `Pukujan/test-repo#3`.

## Start here

1. Read `HANDOFF.md`.
2. Read `PLAN.md`.
3. Read the latest checkpoint named by `state.json`.
4. Verify the local dataset manifest/digest and frozen split IDs before running anything.
5. Do not alter the final test set during iteration.

## Scope boundary

Allowed work:

- LLM closed-set classification;
- empirical probability calibration;
- Model2Vec/Potion training and evaluation;
- optional SetFit baseline;
- classification/calibration metrics;
- error analysis and controlled iteration.

Do not add:

- triage or abstention systems;
- multi-judge consensus/jury;
- model routing;
- semantic graph/RAG work;
- deployment/orchestration infrastructure.

Those require a separate experiment.

## Data boundary

The repository is public.

- Never commit private corpora, credentials, proprietary documents, API keys, or model weights.
- Prefer dataset manifests, stable row IDs, hashes, aggregate metrics, and sanitized fixtures.
- If raw predictions contain sensitive text, keep them local and commit only safe derived metrics plus a digest/path description.
- The calibration and test splits must be disjoint.
- The final test split is evaluation-only.

## Handoff

Before stopping:

1. append a numbered checkpoint;
2. update `state.json` and relevant `checks.json` entries;
3. attach durable evidence to every PASS;
4. run `python tools/lab.py sync`;
5. run `python tools/lab.py validate`;
6. commit the synchronized state.
