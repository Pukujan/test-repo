# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `classifier-calibration-2026-09-19-real-multidomain-teacher-student`  
**Status:** `ready`

## Question

On a frozen real public heterogeneous corpus spanning legal, finance, science, and technology, can a Potion/Model2Vec classifier trained from real qwen3.8-flash teacher labels reproduce useful domain classification behavior on an independent source-held-out gold test set, with calibrated probabilities and durable error analysis?

## Current focus

Build and freeze the first real heterogeneous public corpus and ontology before any benchmark inference. The primary experiment is qwen3.8-flash teacher labels -> Potion/Model2Vec student -> independent source-held-out gold evaluation, not another model-vs-model contest.

## Last durable checkpoint

`checkpoints/0001-experiment-plan.md` — Created the real multi-domain teacher-student experiment, fixed the ontology/split/data-leakage rules, and defined the exact first execution sequence.

## Exact next action

Select and pin at least two stable public sources per top-level domain (legal, finance, science, technology) where feasible; write inputs/source-lock.json, inputs/ontology.json, and a dataset manifest; construct source-aware train/calibration/test IDs with a source-held-out primary test; run leak/source-fingerprint audits; do not invoke Qwen or train Potion until the frozen manifests are committed and validated.

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
2. Read `PLAN.md`, `ONTOLOGY.md`, and the last checkpoint above.
3. Verify source licenses/revisions and live model/provider state before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
