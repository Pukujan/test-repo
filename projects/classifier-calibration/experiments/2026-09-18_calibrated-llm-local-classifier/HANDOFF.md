# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `classifier-calibration-2026-09-18-calibrated-llm-local-classifier`  
**Status:** `completed`

## Question

Can a calibrated LLM classifier and a locally trained lightweight classifier be evaluated reproducibly against the same domain-specific corpus split, with calibration quality, classification quality, and iteration history recorded durably?

## Current focus

Experiment concluded after Run 1 (potion-base-8M) and Run 2 (potion-base-32M) on identical frozen splits with documented LLM/Langfuse substitutes.

## Last durable checkpoint

`checkpoints/0004-run-2-local-002.md` — Completed Run 2 controlled iteration: potion-base-32M on frozen Run 1 IDs; same single Potion error; conclusion updated.

## Exact next action

None — experiment completed. Optional follow-up (new experiment/dataset_version): real generative LLM logprobs and/or non-synthetic domain corpus.

## Blockers

- None.

## Important findings

- Scope remains narrow: calibrated LLM classification, local classifier training/testing, result comparison, controlled iteration, and only the observability required to prove/debug those benchmark runs.
- Triage, consensus/jury, routing, graph construction, RAG, and unrelated orchestration remain explicitly out of scope.
- OpenTelemetry is the instrumentation/correlation contract; Langfuse is the primary human trace/debug UI; Promptfoo is an optional eval runner; Prometheus/Grafana are reserved for local model-server/runtime metrics.
- Structured row/event artifacts and deterministic metric files remain the durable evidence; dashboards are secondary views and must reconcile with those artifacts.
- Run 1 and Run 2 used documented LocalClosedSetScoreProvider (TF-IDF+LogReg logits) because no hosted LLM API keys or local generative LLM server were available.
- Controlled change Run 2: potion-base-8M → potion-base-32M with identical frozen train/calibration/test digests; accuracy unchanged (0.99); same error sample syn-0176; slight log-loss improvement.
- Langfuse was not configured (no credentials); inspectable OTel traces written to otel_traces.jsonl with content_mode=hashes_only for both runs.
- The repository is public; private corpora, credentials, proprietary source text, model weights, raw sensitive predictions, and telemetry secrets must remain local and be represented here only by safe manifests, hashes, aggregate metrics, or sanitized fixtures.
- The LLM calibration set and final test set must be disjoint; the final test set stays frozen during iteration.
- Both the LLM and local classifier must be evaluated on the same test row IDs and label schema.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
