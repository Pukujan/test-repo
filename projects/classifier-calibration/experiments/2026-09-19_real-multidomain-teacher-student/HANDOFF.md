# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `classifier-calibration-2026-09-19-real-multidomain-teacher-student`  
**Status:** `superseded`

## Question

On a frozen real public heterogeneous corpus spanning legal, finance, science, and technology, can a Potion/Model2Vec classifier trained from real qwen3.8-flash teacher labels reproduce useful domain classification behavior on an independent source-held-out gold test set, with calibrated probabilities and durable error analysis?

## Current focus

Superseded. A parallel sibling experiment already froze and committed the equivalent real multi-domain source-held-out contract; this plan-only directory is retained as design history only.

## Last durable checkpoint

`checkpoints/0002-superseded-by-executed-contract.md` — Duplicate-question collision with 2026-09-19_multidomain-real-gold flagged before any Qwen call; this plan is superseded by that executed contract. No PASS claimed.

## Exact next action

Do not execute this plan and do not spend Qwen calls here. Continue in projects/classifier-calibration/experiments/2026-09-19_multidomain-real-gold: produce yolo-auto/qwen3.8-flash teacher labels on its frozen train split only, then calibrate, train Potion on teacher labels, and evaluate on its untouched source-held-out real-gold test.

## Blockers

- None.

## Important findings

- The completed synthetic experiments are harness validation only; do not modify or extend them.
- The real question is whether a cheap Potion/Model2Vec student can learn useful real-domain classification behavior from qwen3.8-flash teacher labels and generalize to an independent gold test set.
- The primary benchmark is not model-vs-model ranking. Qwen is the semantic teacher/reference; Potion is the student being trained and iterated.
- Core benchmark uses coarse single-label top-level domains first: legal, finance, science, technology. Hierarchical/multilabel schemas are intentionally deferred until this real-data baseline is understood.
- Natural mixed-domain documents are kept as a separately reported challenge slice unless they have independently reviewed multi-label gold; they must not be forced into the headline single-label score.
- To reduce dataset-fingerprint shortcuts, the primary test should hold out source families per domain rather than merely random rows from the same source.
- Teacher-generated labels are never evaluation ground truth. Independent source-derived/reviewed gold is required for calibration and final testing.
- Real-or-unavailable policy remains mandatory for qwen3.8-flash and observability backends; no TF-IDF/mock/model substitution may be silently promoted.
- The repository is public; dataset licensing/privacy rules may require committing only source IDs, digests, manifests, and safe fixtures rather than raw document bytes.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
