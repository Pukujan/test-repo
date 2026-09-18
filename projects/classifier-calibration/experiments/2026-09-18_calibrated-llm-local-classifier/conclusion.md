# Conclusion — classifier-calibration (Runs 1–2)

## Answer to the experiment question

**Yes**, with documented substitutes: a calibrated closed-set scoring path and a locally trained Potion/Model2Vec classifier can be evaluated reproducibly on the same frozen synthetic corpus split, with calibration quality, classification quality, observability reconciliation, and iteration history recorded durably.

## Results

### Run 1 — `runs/run-20260918-local-001/`

- LLM path: `LocalClosedSetScoreProvider` (TF-IDF+LogReg logits) — accuracy **1.00**, macro-F1 **1.00**
- Potion: `minishlab/potion-base-8M` — accuracy **0.99**, macro-F1 **0.99**, log-loss **0.0545**, Brier **0.0198**, ECE **0.0098**
- Disagreement: 1 (`syn-0176`, Potion-only wrong)

### Run 2 — `runs/run-20260918-local-002/` (controlled change)

- Same frozen train/calibration/test ID digests as Run 1
- LLM path unchanged (substitute) — accuracy **1.00**
- Potion: `minishlab/potion-base-32M` — accuracy **0.99**, macro-F1 **0.99**, log-loss **0.0522**, Brier **0.0215**, ECE **0.0126**
- Same Potion-only error: `syn-0176`

**Interpretation:** Scaling the static embedding from 8M→32M did not remove the single hard error on this synthetic fixture; classification accuracy was unchanged. Calibration log-loss improved slightly; Brier/ECE did not uniformly improve. The benchmark harness (frozen splits, temperature scaling on calibration only, same-test comparison, OTel reconciliation) held across the iteration.

## Limitations

- **No hosted / local generative LLM** — closed-set scores came from a documented TF-IDF+LogReg substitute, not token logprobs from an instruct model.
- **No Langfuse** — inspectable traces via OTel JSONL file exporter only (`content_mode=hashes_only`).
- **Synthetic corpus** — public-safe fixture; ceiling effects and keyword-overlap noise limit external validity.
- **Public repo** — no private corpora, secrets, or model weights committed.

## Evidence

- Run artifacts under `runs/run-20260918-local-001/` and `runs/run-20260918-local-002/`
- Checkpoints `checkpoints/0003-run-1-local-001.md`, `checkpoints/0004-run-2-local-002.md`
- Pipelines `scripts/run1_pipeline.py`, `scripts/run2_pipeline.py`
- All required checks in `checks.json` are terminal `pass` with evidence paths

## Follow-up (out of this experiment's closed scope)

Optional new experiment / dataset_version: evaluate a real generative LLM with token logprobs and/or a non-synthetic domain corpus on a freshly frozen split. Do not mutate the frozen test membership of `synthetic-topics-v1` in response to model errors.
