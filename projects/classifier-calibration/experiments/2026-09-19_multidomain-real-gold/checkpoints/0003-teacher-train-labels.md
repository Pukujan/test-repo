# Checkpoint 0003 — Qwen teacher labels on the frozen train split (TEACH-001)

## What was done

Run `run-20260919-mdrg-001` started. Before any model call, the frozen-contract
gate re-ran: `scripts/common.py::assert_contract()` reconstructed the train,
calibration, and test rows from gitignored `local_data/` via the exact frozen
cleaning/split/prune logic and verified text digests, per-domain counts, and
split id-sets are **byte-identical** to `inputs/dataset_manifest.json` and
`inputs/split_*.json`. Only then inference ran.

Teacher labeling of the **train split only** (759 rows):

- model `qwen3.8-flash`, provider `yolo-auto` (echo verified per row:
  `provider_echo_models = ["qwen3.8-flash"]`), real or unavailable — 0 provider
  errors, 0 substitutions, 759/759 valid single-letter outputs;
- real logprobs captured on every row (`top_logprobs=20`, full 4-label score
  coverage on 759/759);
- gold/newsgroup/label fields never model-visible (per-sample leak guard);
- teacher-vs-source-membership agreement = **0.8682** on train. This teacher
  noise is KEPT as-is in the training target per the frozen gold policy — no
  silent cleaning. A cleaned-labels variant would be a new controlled run.

## Artifacts

- committed: `runs/run-20260919-mdrg-001/run.json` (provenance + aggregates),
  `events.jsonl`, `otel_traces.jsonl` (ids/model-output/latency only; verified
  free of gold fields, newsgroup labels, and licensed raw text);
- gitignored: `runs/.../teacher/teacher_labels_train.jsonl` (embeds gold).

## Environment

Python 3.12.10, Windows host; transport `https://yolo-auto.com/v1/chat/completions`;
prompt version `mdrg-letters-v1` (A=legal,B=finance,C=science,D=technology, single
letter, temp 0, seed 20260919).

## Exact next action

1. Teacher predictions on calibration split (for CAL-001 temperature scaling fit
   and teacher-quality measurement).
2. Train Potion/Model2Vec on Qwen teacher labels (never real gold).
3. Test split untouched until both systems are fixed.
