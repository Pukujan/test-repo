# Durable Plan — Real Multi-Domain Teacher-Student Benchmark

## Goal

Move beyond synthetic harness validation and test the actual workflow of interest:

> Can a cheap local Potion/Model2Vec classifier learn useful real-domain classification behavior from a strong real Qwen teacher and generalize to independently labeled, source-held-out real documents?

This is not a competition to pick a winning model. Qwen is the semantic teacher/reference; Potion is the student we want to train, measure, and iterate.

## Phase 0 — freeze the experiment contract

Before any model inference:

1. read `ONTOLOGY.md`;
2. create `inputs/ontology.json`;
3. select and pin real public data sources;
4. create `inputs/source-lock.json`;
5. create the dataset/sample manifest;
6. freeze train/calibration/test IDs and source allocation;
7. run leakage/source-shortcut audits;
8. checkpoint the frozen design.

No Qwen calls and no Potion training before this phase is durably committed.

## Phase 1 — acquire real heterogeneous data

### Required domains

- legal
- finance
- science
- technology

### Source-selection rule

Prefer at least two genuinely different public source families per domain so the classifier cannot solve the task by recognizing one benchmark's writing style.

Reasonable examples include:

- legal: LegalBench task texts, ContractNLI/contracts, public statutes/regulatory text;
- finance: FinQA/financial-report contexts, public SEC/financial-report excerpts, another finance corpus;
- science: PubMed abstracts, arXiv/non-CS scientific abstracts, another scientific corpus;
- technology: StackOverflow/developer questions, public software documentation/issues, CS abstracts.

These are examples, not permission to silently use stale/unlicensed data. The executing agent must verify the exact source, revision, license/redistribution constraints, and stable acquisition path before use.

### Public-repo rule

If raw source bytes cannot be committed safely/licensably, commit only:

- stable source identifier;
- exact upstream revision/version;
- retrieval instructions;
- sample/document ID;
- SHA-256/content digest;
- safe metadata;
- sanitized fixture if allowed.

Keep disallowed/private bytes local.

## Phase 2 — prevent dataset-fingerprint cheating

Before freezing the final text representation, inspect for source shortcuts such as:

- dataset/benchmark names;
- source URL/domain names;
- explicit category names;
- boilerplate unique to one source;
- repeated task instructions;
- headers that directly reveal the domain.

Mask/remove these when they are not semantically part of the content.

Record every transformation deterministically.

Primary test design should be **source-held-out** where feasible:

```text
domain
  train/calibration: source family A
  primary test:      source family B
```

If more than two sources exist, use multiple training sources and hold out at least one source family per domain.

A same-source random test may exist only as a diagnostic secondary slice.

## Phase 3 — build frozen splits

Use stable sample IDs and a fixed seed, recommended `20260919`.

Create disjoint:

- training split;
- calibration split;
- primary source-held-out test split;
- optional same-source diagnostic test;
- optional mixed-domain challenge slice.

The primary test must remain untouched after inference starts.

Record per-domain and per-source counts.

Avoid duplicates and near-duplicates across splits; run deterministic hash/near-duplicate checks where practical.

## Phase 4 — establish independent gold

For the core benchmark, gold must be independent of Qwen.

Preferred gold sources:

1. source-native objective labels/provenance when they genuinely encode the top-level domain;
2. explicit human review for ambiguous mappings;
3. documented adjudication for boundary cases.

Do not use Qwen's own labels as test truth.

Items whose domain is genuinely ambiguous should be excluded from the core single-label score and moved to the mixed-domain challenge slice rather than forced into a label.

## Phase 5 — real Qwen teacher/reference run

Use the real model path already proven in the previous experiment:

```text
provider: yolo-auto
model: qwen3.8-flash
policy: real or unavailable; no substitute
```

Use a frozen prompt version derived from the ontology definitions.

Requirements:

- gold labels absent from model-visible input;
- deterministic/near-deterministic generation;
- exact provider/model echo captured;
- candidate-label logprobs captured when available;
- stable run/sample/trace IDs;
- latency/tokens/errors captured;
- invalid output recorded, not repaired silently.

Run Qwen over:

- training rows to create **teacher labels** for Potion;
- calibration rows for calibration/reference evaluation;
- final test rows for teacher/reference metrics only.

### Teacher quality

Because source gold exists, measure Qwen's teacher-label accuracy on data where gold is available.

Do not silently remove teacher mistakes from the training labels after seeing test results.

If you decide to clean teacher labels, that is a new controlled run with explicit cleaning policy.

## Phase 6 — calibrate Qwen

Fit temperature scaling (or another justified calibrator) using calibration gold only.

Record pre/post:

- log loss;
- Brier score;
- ECE/reliability curve;
- accuracy/macro-F1;
- fitted parameters.

Never fit calibration on final test data.

## Phase 7 — train Potion/Model2Vec student

The baseline student must train on:

```text
training text -> Qwen teacher label
```

not on hidden final-test gold.

Start with one stable Potion configuration; use `minishlab/potion-base-8M` unless the environment or prior evidence gives a concrete reason otherwise.

Record:

- exact model ID/revision;
- Model2Vec/package versions;
- classifier head;
- hyperparameters;
- seed;
- exact train IDs;
- exact teacher-label artifact digest.

Do not tune against final test errors.

## Phase 8 — calibrate Potion

If the student exposes class probabilities/scores, calibrate using **calibration gold only**.

Record the raw and calibrated metrics separately.

This answers whether Potion's confidence is actually useful, not merely whether its argmax is correct.

## Phase 9 — same-test evaluation

Evaluate Qwen and Potion on the same frozen primary test IDs.

The primary operational result is the Potion student.

Report:

- Potion accuracy and macro-F1;
- per-domain precision/recall/F1;
- confusion matrix;
- calibrated log loss/Brier/ECE;
- source-held-out performance;
- latency/throughput;
- model footprint where easy to measure.

Alongside it report Qwen as teacher/reference:

- gold accuracy;
- calibration;
- latency/tokens;
- invalid/provider errors.

Also record:

- Qwen correct / Potion wrong;
- Qwen wrong / Potion correct;
- both wrong;
- both correct but with very different confidence.

Do not turn this into an overall model ranking.

## Phase 10 — mixed-domain challenge

Keep natural cross-domain items separate from the headline single-label benchmark unless they have independently reviewed multi-label gold.

Useful challenge categories:

- legal + finance;
- legal + technology;
- finance + technology;
- science + technology.

For this first experiment, qualitative/error-slice reporting is acceptable if defensible multi-label gold is unavailable.

Do not coerce mixed-domain examples into a single label just to increase benchmark size.

## Error taxonomy

Every baseline conclusion should separate at least:

- teacher-label error;
- student-only semantic error;
- shared teacher/student error;
- source/domain-shift error;
- ontology-boundary ambiguity;
- source-boilerplate/shortcut issue;
- chunking/context insufficiency;
- calibration-only failure (argmax correct, confidence poor);
- invalid/provider/infrastructure error.

This error taxonomy is more important than one aggregate score.

## Iteration

After the baseline, choose one evidence-driven change.

Examples:

- increase teacher-labeled training examples for a weak domain;
- improve teacher prompt definitions;
- clean a documented teacher-noise slice;
- change Potion size/head;
- rebalance classes;
- improve text normalization.

Do not change multiple variables at once unless explicitly documented.

Never change frozen test membership/labels because a model failed them.

A second run should answer a specific hypothesis, not simply "try to get a higher score."

## Observability

Reuse the existing benchmark observability discipline:

- stable `experiment_id`, `run_id`, `sample_id`, `trace_id`;
- structured JSONL events;
- OTel-compatible traces;
- per-call provider/model/prompt/config provenance;
- machine-readable reconciliation;
- deterministic aggregate metrics from row-level predictions.

If Langfuse is genuinely configured, use it and prove trace visibility/reconciliation.

If it is unavailable, record `langfuse_status=unavailable` and preserve local OTel evidence. Never call local JSONL traces "Langfuse."

## Minimum baseline artifacts

Expected once execution begins:

```text
inputs/
  ontology.json
  source-lock.json
  dataset_manifest.json
  split_manifest.json
  gold_policy.md

runs/run-.../
  run.json
  teacher_config.json
  teacher_predictions_train.json
  teacher_predictions_calibration.json
  teacher_predictions_test.json
  teacher_calibration.json
  potion_config.json
  potion_metrics.json
  comparison.json
  error_analysis.md
  events.jsonl
  otel_traces.jsonl
  observability_reconciliation.json
```

Raw corpus bytes may remain local when licensing/privacy requires it; preserve digests and exact acquisition instructions.

## Baseline completion criteria

Do not mark the experiment completed merely because scripts ran.

Completion requires:

1. frozen real public sources and ontology;
2. source-aware split with independent gold;
3. leak/source-shortcut checks;
4. proven real qwen3.8-flash teacher inference;
5. teacher quality measured against gold;
6. Qwen calibrated on calibration gold only;
7. Potion trained on teacher labels;
8. Potion calibrated on calibration gold where applicable;
9. both evaluated on the same untouched source-held-out test;
10. error taxonomy and mixed-domain challenge report;
11. observability reconciliation;
12. at least one explicit conclusion about where the student does/does not reproduce useful teacher behavior;
13. `python tools/lab.py sync` and `python tools/lab.py validate` pass.

Negative results are valid. If Potion fails under source shift, say so.
