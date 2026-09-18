# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `classifier-calibration-2026-09-18-calibrated-llm-local-classifier`  
**Status:** `ready`

## Question

Can a calibrated LLM classifier and a locally trained lightweight classifier be evaluated reproducibly against the same domain-specific corpus split, with calibration quality, classification quality, and iteration history recorded durably?

## Current focus

Prepare the first local baseline run: freeze a labeled train/calibration/test split, evaluate a closed-set LLM with calibratable class scores, train a Potion/Model2Vec classifier, and compare both on the identical untouched test IDs.

## Last durable checkpoint

`checkpoints/0001-initial-plan.md` — Created the isolated classifier-calibration experiment, fixed scope to LLM calibration plus local classifier training/evaluation, and recorded the first-run contract.

## Exact next action

Locally clone Pukujan/test-repo, read this experiment HANDOFF.md and PLAN.md, place only a safe dataset manifest or local-only dataset path/hash into the run inputs, freeze train/calibration/test IDs, then execute the first LLM and Potion/Model2Vec baseline without changing the test split.

## Blockers

- None.

## Important findings

- Scope is intentionally narrow: calibrated LLM classification, local classifier training/testing, result comparison, and iteration only.
- Triage, consensus/jury, routing, graph construction, and orchestration are explicitly out of scope for this experiment.
- The repository is public; private corpora, credentials, proprietary source text, model weights, and sensitive raw predictions must remain local and be represented here only by safe manifests, hashes, aggregate metrics, or sanitized fixtures.
- The LLM calibration set and the final test set must be disjoint; the test set stays frozen during iteration.
- Both the LLM and local classifier must be evaluated on the same test row IDs and label schema.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
