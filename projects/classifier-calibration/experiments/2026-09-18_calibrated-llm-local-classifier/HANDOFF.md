# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `classifier-calibration-2026-09-18-calibrated-llm-local-classifier`  
**Status:** `completed`

## Question

Can a calibrated LLM classifier and a locally trained lightweight classifier be evaluated reproducibly against the same domain-specific corpus split, with calibration quality, classification quality, and iteration history recorded durably?

## Current focus

Run 1 complete: durable smoke+full artifacts under runs/run-20260918-local-001 with calibrated LocalClosedSetScoreProvider vs Potion/Model2Vec on frozen test IDs. Ready for controlled iteration from the recorded next hypothesis.

## Last durable checkpoint

`checkpoints/0003-run-1-local-001.md` — Completed Run 1: synthetic fixture, frozen splits, smoke+full observability reconciliation, temperature-scaled local closed-set score provider, Potion/Model2Vec baseline, same-test comparison, and next hypothesis.

## Exact next action

Potion/Model2Vec errs more than the score provider. Next controlled change: try potion-base-32M (larger static embedding) with the same train/calibration/test IDs and re-fit temperature scaling on calibration only.

## Blockers

- None.

## Important findings

- Scope remains narrow: calibrated LLM classification, local classifier training/testing, result comparison, controlled iteration, and only the observability required to prove/debug those benchmark runs.
- Triage, consensus/jury, routing, graph construction, RAG, and unrelated orchestration remain explicitly out of scope.
- OpenTelemetry is the instrumentation/correlation contract; Langfuse is the primary human trace/debug UI; Promptfoo is an optional eval runner; Prometheus/Grafana are reserved for local model-server/runtime metrics.
- Structured row/event artifacts and deterministic metric files remain the durable evidence; dashboards are secondary views and must reconcile with those artifacts.
- Run 1 used a documented LocalClosedSetScoreProvider (TF-IDF+LogReg logits) because no hosted LLM API keys or local generative LLM server were available; temperature scaling and the full comparison pipeline still ran.
- Potion/Model2Vec (minishlab/potion-base-8M) trained successfully via model2vec[train]; classifier also temperature-scaled on calibration only.
- Langfuse was not configured (no credentials); inspectable OTel traces were written to otel_traces.jsonl with content_mode=hashes_only.
- The repository is public; private corpora, credentials, proprietary source text, model weights, raw sensitive predictions, and telemetry secrets must remain local and be represented here only by safe manifests, hashes, aggregate metrics, or sanitized fixtures.
- The LLM calibration set and final test set must be disjoint; the final test set stays frozen during iteration.
- Both the LLM and local classifier must be evaluated on the same test row IDs and label schema.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
