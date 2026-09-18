# Durable Local Test Plan

## Objective

Build no platform. Run a small, reproducible benchmark that compares:

1. one LLM used as a closed-set classifier and calibrated empirically;
2. one locally trained Model2Vec/Potion classifier;
3. their results on the exact same frozen test examples.

Then inspect errors and run controlled iterations.

## Scope

This experiment does **not** test triage, consensus, routing, graph construction, RAG, or production orchestration.

Observability for this benchmark is in scope because it is required to prove and debug the experiment. It must remain benchmark-focused rather than becoming a separate platform project.

The unit of work is a benchmark run under `runs/<run-id>/`.

## OSS stack

Core benchmark dependencies:

- Python 3.11+
- `pandas`
- `pyarrow`
- `scikit-learn`
- `model2vec[train]`
- `vllm` when the chosen LLM is local and compatible, or another OpenAI-compatible local endpoint
- optional `netcal` only if the desired calibration method is not convenient in scikit-learn
- optional `setfit` only as a comparison baseline after the Potion baseline exists

Observability/evaluation dependencies:

- OpenTelemetry for trace context and instrumentation;
- Langfuse as the primary LLM/application trace UI;
- Promptfoo when useful for prompt/model test matrices and assertions;
- Prometheus + Grafana only when needed for local model-server/runtime metrics;
- structured JSONL event logs as the durable local forensic record.

Do not introduce another framework unless a concrete missing capability blocks a run.

Read `OBSERVABILITY.md` before executing Run 1.

## Dataset contract

Keep the actual private corpus local if it is not safe for this public repository.

For each experiment dataset version, record a safe manifest containing:

- dataset/version identifier;
- label schema and label definitions;
- row-ID generation rule;
- total row count and per-label counts;
- source digest(s) or safe source pointer;
- split-generation code/config/seed;
- train row IDs or a digest of them;
- calibration row IDs or a digest of them;
- test row IDs or a digest of them.

Required split rule:

```text
train ∩ calibration = ∅
train ∩ test        = ∅
calibration ∩ test  = ∅
```

The final test IDs remain frozen across iterations for this experiment.

If the task is multilabel, record that explicitly and use multilabel metrics; do not silently coerce it into single-label classification.

## LLM classification contract

Use a fixed closed label set.

Preferred scoring method:

1. map labels to stable short output IDs such as `A`, `B`, `C`, ...;
2. use a deterministic or near-deterministic classification prompt;
3. obtain model-derived class logits/log-probabilities for every candidate label when the serving stack supports it;
4. normalize candidate scores consistently;
5. preserve the raw score vector before calibration.

Do not treat a model-generated `"confidence": 0.93` field as calibrated probability. It may be recorded as a diagnostic, but model-derived class scores are preferred.

For multi-token label names, score the complete candidate sequence or use short stable label IDs.

## LLM calibration contract

Fit calibration only on the calibration split.

Baseline method: temperature scaling when usable logits or comparable class scores are available.

For class-score vector `z` and learned temperature `T`:

```text
p_calibrated = softmax(z / T)
```

Record:

- calibration method;
- fitted parameter(s);
- optimization objective;
- calibration-set size and label distribution;
- pre/post log loss;
- pre/post Brier score;
- pre/post calibration error/curve;
- accuracy/macro-F1 to confirm calibration did not accidentally change the classification contract.

If only probabilities are available, use a documented probability calibrator such as sigmoid/Platt or isotonic regression as appropriate. Do not fit on the final test set.

## Local classifier contract

First baseline: Model2Vec/Potion.

Train only on the training split.

Record:

- exact package versions;
- base Potion model identifier;
- classifier/head type;
- seed;
- training hyperparameters;
- label mapping;
- train/calibration/test manifest version;
- local hardware/runtime facts relevant to reproducibility.

If its raw probabilities are poorly calibrated, fit a separate calibrator using the calibration split only.

SetFit is optional later as an independent small-model baseline; it is not required for the first run.

## Evaluation contract

Both the calibrated LLM and the local classifier must be evaluated on exactly the same frozen test row IDs.

Minimum classification metrics:

- accuracy;
- macro-F1;
- per-class precision/recall/F1;
- confusion matrix.

Minimum probability/calibration metrics when probabilities are meaningful:

- log loss;
- Brier score;
- expected calibration error or an explicitly documented calibration-error statistic;
- reliability/calibration curve.

Also record:

- inference latency/throughput where easy to measure;
- model size or serving footprint where relevant;
- failed/invalid-output count for the LLM.

## Observability contract

Observability is a required part of every benchmark run.

Use stable `experiment_id`, `run_id`, `sample_id`, `trace_id`, and relevant model/config identifiers so a single prediction can be followed across:

- row-level result;
- structured event log;
- OpenTelemetry trace;
- Langfuse trace;
- Promptfoo case when used;
- model-server metrics when used;
- run-level aggregate metrics.

Before the full Run 1 benchmark, execute a smoke subset and prove telemetry completeness/reconciliation.

See `OBSERVABILITY.md` for the detailed span schema, event schema, privacy/content modes, dashboard responsibilities, reconciliation rules, and failure policy.

## Run layout

Recommended durable layout once execution begins:

```text
runs/
  run-YYYYMMDD-local-001/
    run.json
    dataset_manifest.json
    split_manifest.json

    observability.json
    observability_reconciliation.json
    events.schema.json
    events.jsonl
    events.jsonl.sha256

    llm_config.json
    llm_metrics.json
    llm_calibration.json

    classifier_config.json
    classifier_metrics.json

    comparison.json
    error_analysis.md
```

Only commit `events.jsonl` when it is safe for this public repository. Otherwise keep it local and commit its digest/count/schema plus safe derived metrics.

Private or large artifacts remain outside Git. `run.json` should record their local path description and digest when useful, without exposing sensitive locations or content.

## First run

The first run should do only this:

1. prepare the labeled dataset locally;
2. freeze train/calibration/test IDs;
3. configure the observability content mode and correlation IDs;
4. run a small telemetry smoke subset and reconcile sample/prediction/trace/event counts;
5. run one LLM prompt/model over calibration and test rows;
6. fit one calibration transform on calibration rows;
7. train one Potion/Model2Vec classifier on training rows;
8. calibrate it only if needed;
9. evaluate both on the same frozen test IDs;
10. write metrics and a confusion/error analysis;
11. reconcile observability and deterministic result artifacts;
12. choose one next change based on observed evidence.

Do not expand the architecture during Run 1.

## Iteration discipline

Each later run should document what changed from the previous run.

Prefer one controlled change at a time, for example:

- LLM prompt wording;
- LLM model;
- Potion model size;
- class weighting;
- training-set size;
- label-definition cleanup;
- calibration method.

Do not modify test labels or test membership in response to model errors. If the gold label is genuinely wrong, record the correction transparently and create a new dataset/test version.

## First-run acceptance target

The first run is complete when the experiment has durable evidence for:

- frozen data/split manifest;
- LLM raw scores and calibration result;
- trained local classifier result;
- same-test comparison;
- classification and calibration metrics;
- reproducibility/config record;
- correlated structured observability with reconciliation evidence;
- error analysis and next hypothesis.

No particular accuracy threshold is required for Run 1. The purpose is to establish a trustworthy baseline.
