# Conclusion — Run 1

## Answer to the experiment question (baseline)

Yes: a calibrated closed-set scoring path and a locally trained Potion/Model2Vec classifier can be evaluated reproducibly on the same frozen synthetic corpus split, with calibration quality, classification quality, observability reconciliation, and iteration history recorded durably under `runs/run-20260918-local-001/`.

## What Run 1 established

- Frozen disjoint train / calibration / test IDs with dataset digests and label schema.
- Temperature scaling fitted on calibration only for both systems.
- Same-test comparison with classification + calibration metrics.
- Smoke + full observability reconciliation (OTel file exporter; Langfuse not configured).
- One concrete next hypothesis for controlled iteration (see `error_analysis.md`).

## Honest substitutes

- No hosted LLM API keys / local generative server → documented `LocalClosedSetScoreProvider` emitting per-class logits.
- No Langfuse credentials → inspectable `otel_traces.jsonl`.

## Status

Run 1 acceptance target is met. Further runs should change one controlled factor at a time without altering the frozen test membership for this dataset version.
