# Checkpoint 0004 — Calibration, Potion student, and frozen-test evaluation

## What was done

Completed the pipeline for `run-20260919-mdrg-001` (prompt `mdrg-letters-v1`)
**before** the test split was scored. The frozen-contract gate
(`scripts/common.py::assert_contract()`) re-ran at every stage; the test split
text/gold was untouched until both systems were fixed.

- **TEACH-002 (v1):** teacher `yolo-auto/qwen3.8-flash` re-ran on the calibration
  split. The prior session had 70 rows stuck as HTTP 429 errors (56 legal, 14
  finance). `scripts/qwen_teacher.py` was changed so only `status==ok` rows are
  terminal; error rows are retried on re-run and observability is deduped
  (ok preferred over error per `(split, sample_id)`). Result: calibration
  312/312 ok, 0 errors, full logprobs, echo `qwen3.8-flash`, agreement vs source
  membership 267/312 (85.58%). Teacher on test: 774/774 ok, 0 provider errors, 0
  substitutions, full logprobs on 774/774.
- **CAL-001:** temperature scaling of the teacher, fit on the **calibration split
  only** (golden-section NLL minimization on source-membership gold).
  T = 1.4685. Calibration log-loss 0.4011 -> 0.3542, Brier 0.1943 -> 0.1830,
  ECE 0.0727 -> 0.0247.
- **POT-001:** Potion student = `minishlab/potion-base-32M` embeddings +
  `LogisticRegression(C=50, max_iter=1000, random_state=20260919)` trained on
  **Qwen teacher labels only** (759 train rows; source-membership gold never a
  training target).
- **POT-002:** Potion temperature scaling fit on the calibration split only.
  T = 1.7115. Calibration log-loss 0.5050 -> 0.4206, ECE 0.0748 -> 0.0304.
- **EVAL-001 / EVAL-002:** both systems scored on the **same** untouched frozen
  test IDs (n=774), using the calibration-fit temperatures:
  - Teacher (calibrated): accuracy 0.7933, macro-F1 0.7746, log-loss 0.6599,
    Brier 0.3297, ECE 0.1129.
  - Potion (calibrated): accuracy 0.6731, macro-F1 0.6515, log-loss 1.1115,
    Brier 0.5331, ECE 0.1355.
  - Per-class metrics + confusion matrices recorded in
    `runs/run-20260919-mdrg-001/eval/eval_summary.json`.
  - **Prediction-rule note:** the provider's decoded token differs from the
    argmax of its own returned top_logprobs on 39/774 test rows (decoded
    accuracy 0.7558 vs logit-argmax 0.7933; same discrepancy on run-002:
    24/774, 0.8062 vs 0.8320). Evaluation uses the logit-argmax rule for both
    the raw and temperature-calibrated scores (temperature scaling preserves
    argmax, so calibrated accuracy equals uncalibrated argmax accuracy; only
    probability metrics move). The decoded-letter agreement figures are also
    recorded for completeness. Provider metadata inconsistency recorded, not
    patched.
- **OBS-001:** `runs/run-20260919-mdrg-001/observability_reconciliation.json`
  reconciles expected/completed/unique ids and events/traces per split. All three
  splits consistent (train 759, calibration 312, test 774; 1845 events, 1845
  traces, no missing/unexpected ids). Langfuse unavailable -> OTel JSONL used.

## Artifacts

- committed: `runs/run-20260919-mdrg-001/calibration/calibration_summary.json`,
  `runs/run-20260919-mdrg-001/eval/eval_summary.json`,
  `runs/run-20260919-mdrg-001/observability_reconciliation.json`,
  regenerated `events.jsonl` / `otel_traces.jsonl` (no gold, no raw text —
  verified).
- gitignored: `runs/.../teacher/`, `runs/.../preds/`, `models/`.

## Environment

Python 3.12.10; numpy 1.26.4, scikit-learn 1.9.0, model2vec 0.8.2, joblib 1.5.3.
Potion base 32M embeddings (256-d).

## Headline

Teacher beats the teacher-trained student by 12.0 accuracy points on the harder
source-held-out benchmark. Science is the weak class for both (see 0005).

## Exact next action

ITER-001: controlled single-variable iteration addressing the science/technology
confusion.
