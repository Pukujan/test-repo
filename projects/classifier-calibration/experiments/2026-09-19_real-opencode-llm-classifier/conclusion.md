# Conclusion — classifier-calibration (2026-09-19 real OpenCode LLM compatibility run)

## Answer to the experiment question

**Yes.** Replacing the prior experiment's documented TF-IDF+LogReg LLM
substitute with the real OpenCode-accessible generative model
`yolo-auto/qwen3.8-flash` on the **identical frozen split** produced a complete,
real-inference result: accuracy **0.99**, macro-F1 **0.99**, and well-calibrated
real logprob scores (temperature-scaled log-loss **0.0254**, Brier **0.0124**,
ECE **0.0169**, T=**1.1256** fit on the calibration split only). Zero provider
errors, zero invalid outputs, zero gold-label leakage.

## Results

### Run `runs/run-20260919-real-001/`

| System | Accuracy | Macro-F1 | Log-loss | Brier | ECE | Error |
|---|---|---|---|---|---|---|
| **Real LLM qwen3.8-flash** (this run) | 0.99 | 0.99 | 0.0254 | 0.0124 | 0.0169 | `syn-0147` |
| Potion base-8M (prior, recorded) | 0.99 | 0.99 | 0.0545 | 0.0198 | 0.0098 | `syn-0176` |
| Potion base-32M (prior, recorded) | 0.99 | 0.99 | 0.0522 | 0.0215 | 0.0126 | `syn-0176` |
| TF-IDF+LogReg substitute (prior) | 1.00 | 1.00 | ~0 | ~0 | ~0 | none |

- Single real-LLM error: **syn-0147** ("Briefing covers encryption, with
  emphasis on neural and recent cardio." — technology misread as health at ~0.69
  confidence). A soft, coherent miss driven by health-adjacent vocabulary, not an
  overconfident failure. The real LLM classifies Potion's error (`syn-0176`)
  **correctly**; the substitute was perfect on its own fixture.
- Real-model latency: p50 **1068 ms**, p95 **1548 ms**; **9952** total tokens.
- Observability reconciled: 200 events / 200 OTel traces / 200 unique sample IDs;
  `reconciled=true`. Langfuse unavailable -> inspectable OTel JSONL used.

## Interpretation

- **Real-vs-substitute is not a quality comparison.** The synthetic corpus is
  keyword-saturated and near the substitute's feature space; the substitute's
  1.00 is expected and proves nothing about model quality. The 0.99 from the
  real model neither beats nor loses to it.
- **Real-vs-Potion is meaningful at the margin**: both reach 0.99 but make
  **different single errors** (syn-0147 vs syn-0176), and the real model's
  calibrated logprob scores are better than Potion's on this split
  (log-loss 0.0254 vs 0.0545; ECE 0.0169 vs 0.0098 is slightly worse).
- The benchmark harness (frozen digests, calibration-only temperature scaling,
  same-test-ID evaluation, OTel reconciliation, leak guards) held end-to-end
  under a real hosted LLM with real token logprobs.

## Limitations

- **One model, one provider** (`qwen3.8-flash` via yolo-auto) by owner scope;
  other yolo-auto models reachable but excluded; LiteLLM models unavailable.
- **Synthetic fixture** -> ceiling effect; external validity for real-domain
  classification is not established here.
- **No Langfuse** UI; durable OTel JSONL only.
- **Public repo**: no secrets/weights committed; env-var reference only.

## Evidence

- `runs/run-20260919-real-001/metrics.json`, `predictions_test.json`,
  `predictions_calibration.json`, `error_analysis.md`, `comparison.json`,
  `leak_proof.txt`, `observability_reconciliation.json`, `run.json`, `llm_config.json`
- `checkpoints/0001-real-inference-proven-and-run-complete.md`
- `scripts/real_llm_pipeline.py`, `scripts/analyze_errors.py`
- All applicable `checks.json` entries terminal `pass`; CLS-001/CLS-002
  `not_applicable` (Potion compared from recorded results, not retrained).

## Follow-up (out of closed scope)

Optional new experiment / new dataset_version: evaluate a real LLM (and Potion)
on a harder, non-synthetic multi-domain corpus with a freshly frozen split, where
the substitute fixture's ceiling effect no longer dominates. Do not mutate
`synthetic-topics-v1` membership in response to model errors.
