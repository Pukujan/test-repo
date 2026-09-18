# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `classifier-calibration-2026-09-18-calibrated-llm-local-classifier`  
**Status:** `ready`

## Question

Can a calibrated LLM classifier and a locally trained lightweight classifier be evaluated reproducibly against the same domain-specific corpus split, with calibration quality, classification quality, and iteration history recorded durably?

## Current focus

Prepare Run 1 with observability as part of the evidence contract: freeze the dataset splits, instrument a small smoke subset with stable sample/trace correlation, reconcile telemetry completeness, then execute the calibrated LLM and Potion/Model2Vec baselines on the same untouched test IDs.

## Last durable checkpoint

`checkpoints/0002-observability-contract.md` — Made benchmark observability a Run 1 acceptance requirement using OpenTelemetry correlation, Langfuse trace inspection, structured event logs, optional Promptfoo evaluation, optional Prometheus/Grafana runtime metrics, and machine-readable reconciliation.

## Exact next action

Locally clone Pukujan/test-repo; read HANDOFF.md, PLAN.md, and OBSERVABILITY.md; freeze train/calibration/test IDs; configure a privacy-safe telemetry content mode; run a small observability smoke subset and reconcile sample/prediction/trace/event counts before launching the full LLM calibration and Potion/Model2Vec baseline.

## Blockers

- None.

## Important findings

- Scope remains narrow: calibrated LLM classification, local classifier training/testing, result comparison, controlled iteration, and only the observability required to prove/debug those benchmark runs.
- Triage, consensus/jury, routing, graph construction, RAG, and unrelated orchestration remain explicitly out of scope.
- OpenTelemetry is the instrumentation/correlation contract; Langfuse is the primary human trace/debug UI; Promptfoo is an optional eval runner; Prometheus/Grafana are reserved for local model-server/runtime metrics.
- Structured row/event artifacts and deterministic metric files remain the durable evidence; dashboards are secondary views and must reconcile with those artifacts.
- Run 1 must begin with a small observability smoke subset proving stable IDs, inspectable traces, structured events, privacy/content-mode compliance, and count reconciliation.
- The repository is public; private corpora, credentials, proprietary source text, model weights, raw sensitive predictions, and telemetry secrets must remain local and be represented here only by safe manifests, hashes, aggregate metrics, or sanitized fixtures.
- The LLM calibration set and final test set must be disjoint; the final test set stays frozen during iteration.
- Both the LLM and local classifier must be evaluated on the same test row IDs and label schema.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
