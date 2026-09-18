# Observability Contract

## Purpose

Observability is part of the benchmark's evidence contract, not a dashboard added after the experiment works.

A run is not considered fully reproducible unless a future agent can answer:

- which sample produced a result;
- which model/prompt/classifier/calibrator produced it;
- what raw scores existed before calibration;
- what calibrated probabilities were used;
- how long each stage took;
- whether an error came from data, inference, calibration, evaluation, or infrastructure;
- whether the telemetry itself is complete.

Dashboards are views. Durable run artifacts are evidence.

## OSS responsibilities

Use each tool for one job.

### OpenTelemetry

OpenTelemetry is the canonical instrumentation and correlation layer.

All benchmark components should emit or propagate OTel trace context where practical. Instrumentation must not depend on a single dashboard vendor.

Required correlation attributes:

- `experiment_id`
- `run_id`
- `sample_id`
- `dataset_version`
- `split`
- `label_schema_version`
- `model_id`
- `model_revision` when available
- `prompt_version` for LLM runs
- `classifier_revision` for local classifier runs
- `calibration_method`
- `calibration_version`
- `trace_id`
- `span_id`

### Langfuse

Langfuse is the primary human-facing LLM/application trace UI.

Use it for:

- trace inspection;
- prompt/model metadata;
- latency and token/cost views;
- per-sample scores;
- error filtering;
- run/model/domain comparisons;
- debugging individual failed examples.

Langfuse is not the sole durable record of the experiment.

### Promptfoo

Promptfoo is an evaluation/test runner when useful.

Use it for:

- prompt/model matrices;
- deterministic assertions;
- structured-output validity checks;
- replayable LLM test cases;
- linking evaluation cases to traces when supported.

Do not use Promptfoo as the canonical calibration implementation or as the only result store.

### Prometheus + Grafana

Use Prometheus/Grafana only for local serving/runtime observability, primarily when running vLLM or another long-lived model server.

Expected infrastructure metrics include, where exposed:

- requests in flight / queue depth;
- requests per second;
- tokens per second;
- TTFT p50/p95/p99;
- generation/inter-token latency;
- request duration;
- KV-cache utilization;
- GPU utilization and memory;
- OOM/errors;
- request failures;
- model-server uptime.

Do not duplicate classification-quality dashboards in Grafana unless there is a concrete operational need.

### Structured local event log

Every run must produce a structured event stream or an equivalent safe local artifact.

Preferred local file:

```text
runs/<run-id>/events.jsonl
```

If row-level events contain private information, keep the raw file local and commit only:

- its SHA-256;
- byte/event counts;
- schema/version;
- safe aggregate metrics;
- a sanitized fixture showing the event shape.

## Telemetry content modes

Do not assume prompts/documents may be copied into telemetry.

Support a content-capture mode in run configuration:

```text
none
hash
sanitized
full
```

For private domain corpora, default to `hash` or `sanitized`.

Even when content is suppressed, retain safe metadata such as:

- `sample_id`;
- input digest;
- input length;
- gold label ID;
- predicted label ID;
- raw score vector if safe;
- calibrated probability vector if safe;
- timings;
- trace identifiers.

## Per-sample trace contract

Use one root trace per evaluated sample per system.

Recommended LLM shape:

```text
TRACE classify.sample
  SPAN dataset.resolve
  SPAN llm.classify
  SPAN calibration.apply
  SPAN prediction.evaluate
  SPAN metrics.record
```

Recommended local-classifier shape:

```text
TRACE classify.sample
  SPAN embedding
  SPAN classifier.predict
  SPAN calibration.apply
  SPAN prediction.evaluate
  SPAN metrics.record
```

The `calibration.apply` span may be omitted only when the run explicitly records that no post-hoc calibration was applied.

### Required LLM span fields

At minimum record or make recoverable:

- sample ID;
- model ID/revision;
- prompt version;
- output label;
- candidate/raw class scores or strongest available score representation;
- input/output token counts when available;
- invalid-output/error state;
- latency;
- trace ID.

### Required classifier span fields

At minimum record:

- sample ID;
- embedding/base model ID;
- classifier revision/config hash;
- raw class scores;
- output label;
- latency;
- trace ID.

### Required calibration span fields

Record:

- calibration method;
- calibrator version/config hash;
- fitted parameter identifier;
- raw score/probability vector reference;
- calibrated probability vector reference.

Do not record a model's self-reported confidence as if it were calibrated probability.

## Structured event schema

A minimal event should resemble:

```json
{
  "schema_version": "classifier-bench.event.v1",
  "timestamp": "RFC3339",
  "level": "INFO",
  "event": "classification.completed",
  "experiment_id": "...",
  "run_id": "...",
  "sample_id": "...",
  "trace_id": "...",
  "system": "llm|potion|setfit",
  "model_id": "...",
  "predicted_label": "...",
  "gold_label": "...",
  "correct": true,
  "latency_ms": 12.3
}
```

Additional fields are allowed, but the correlation identifiers must remain stable.

Do not emit unstructured messages such as `prediction complete` as the only log record.

## Run-level durable artifacts

Extend the run layout to include:

```text
runs/
  run-YYYYMMDD-local-001/
    run.json
    dataset_manifest.json
    split_manifest.json

    observability.json
    observability_reconciliation.json
    events.schema.json
    events.jsonl                 # only if safe to commit
    events.jsonl.sha256          # use when raw events stay local

    llm_config.json
    llm_metrics.json
    llm_calibration.json

    classifier_config.json
    classifier_metrics.json

    comparison.json
    error_analysis.md
```

`observability.json` records:

- OTel SDK/exporter configuration;
- Langfuse configuration mode and project/environment identifier without secrets;
- Promptfoo version/config reference when used;
- Prometheus/Grafana endpoints/config identifiers when used;
- telemetry content mode;
- log/event schema version;
- sampling policy;
- expected trace cardinality.

Never commit API keys or collector credentials.

## Observability reconciliation

Observability must be measured, not assumed.

At the end of a run, produce `observability_reconciliation.json` with at least:

- expected sample count;
- completed sample count;
- prediction row count;
- root traces emitted;
- root traces observable in the configured trace backend, if one is used;
- unique sample IDs;
- duplicate sample IDs;
- missing prediction IDs;
- missing trace IDs;
- structured event count;
- invalid/failed inference count;
- whether aggregate metrics can be regenerated from row-level results.

Example:

```text
expected samples       10000
completed samples      10000
prediction rows        10000
root traces emitted    10000
backend traces found   10000
missing trace ids          0
duplicate sample ids       0
```

If trace/event capture is incomplete, the ML metrics may still be recorded, but the observability checks must not be marked PASS.

## Dashboard contract

### Langfuse dashboard

At minimum, make it possible to inspect/filter:

- run;
- system/model;
- dataset version;
- label/domain;
- correct vs incorrect;
- raw vs calibrated confidence;
- latency;
- token usage/cost when applicable;
- invalid outputs;
- individual trace details.

Recommended run-level charts:

- accuracy by run/model;
- macro-F1 by run/model;
- per-class error rate;
- Brier score;
- log loss;
- calibration error;
- p50/p95 latency;
- tokens/sample;
- invalid-output rate.

### Grafana dashboard

When a model server exposes Prometheus metrics, include only operational/runtime views needed to diagnose benchmark performance:

- request rate;
- queue depth;
- TTFT;
- token throughput;
- request duration;
- KV-cache;
- GPU/VRAM;
- failures/OOM.

## Source-of-truth hierarchy

Use this order when numbers disagree:

1. frozen dataset/split manifests;
2. row-level prediction/result artifacts;
3. deterministic aggregate metric artifacts regenerated from those rows;
4. structured event logs/traces;
5. dashboard aggregates.

A dashboard value that disagrees with committed/reproducible metric artifacts is a defect to investigate, not an alternate truth.

## Failure policy

Observability is considered defective when any of the following occurs without an explicit documented exception:

- evaluated samples lack stable sample IDs;
- completed predictions lack trace/correlation IDs;
- duplicate sample IDs are not explained;
- trace/event counts do not reconcile with completed samples;
- model/prompt/classifier/calibrator identity is missing;
- raw and calibrated scores cannot be distinguished;
- dashboard metrics disagree with deterministic aggregate artifacts;
- telemetry leaks content outside the configured content mode.

Do not mark observability checks PASS based on screenshots or prose alone.

## Run 1 requirement

Before executing the full Run 1 benchmark, perform a small smoke subset and prove that:

1. IDs propagate correctly;
2. sample traces are inspectable;
3. structured events are emitted;
4. private content follows the configured capture mode;
5. trace/prediction/event counts reconcile;
6. aggregate metrics can be regenerated.

Only then execute the larger first benchmark.
