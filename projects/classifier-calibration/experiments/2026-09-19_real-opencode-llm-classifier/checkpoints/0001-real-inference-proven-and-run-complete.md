# Checkpoint 0001 — Real inference proven; run run-20260919-real-001 complete

## Durable decision

This experiment ran the **actual OpenCode-accessible generative model**
`yolo-auto/qwen3.8-flash` as the closed-set topic classifier on the frozen
`synthetic-topics-v1` split (seed 20260918; 200 train / 100 calibration / 100
test), replacing only the documented TF-IDF+LogReg substitute from the frozen
`2026-09-18` experiment. One variable changed: substitute -> real LLM.

Real inference was **proven before benchmarking**:

- single-call probe returned provider echo `model=qwen3.8-flash`;
- candidate-label logprobs present at the answer position with `top_logprobs=20`,
  `enable_thinking:false`, and all four labels covered (`score_coverage=full`);
- smoke run 8/8 rows carrying model_id/provider_id/invocation_path/timestamp/
  latency/tokens/trace_id.

## Transport finding

`https://yolo-auto.com/v1/chat/completions` returns **403 Forbidden without a
User-Agent header**. The pipeline sends `User-Agent: classifier-bench/1.0`.
This is a transport fix, not a substitution.

## Environment reality

- LiteLLM proxy on localhost:4000 was down; all `litellm/*` models marked
  `unavailable` and **not** substituted (real-or-unavailable rule held).
- Other yolo-auto models (`qwen3.8-27b`, `yolo`, `yolo-small`) are reachable but
  excluded from this run by owner instruction (scope: qwen3.8-flash only).

## Run results (run-20260919-real-001)

- Test acc **0.99**, macro-F1 **0.99**, log-loss **0.0254**, Brier **0.0124**,
  ECE **0.0169** after temperature scaling T=**1.1256** fit on calibration only.
- Latency p50 **1068 ms**, p95 **1548 ms**; total **9952** tokens;
  **0** provider errors; **0** invalid outputs; reconciled=true (200 events /
  200 traces / 200 unique sample IDs).
- Single error: **syn-0147** technology -> health at ~**0.69** confidence
  (health-adjacent vocabulary; a soft, coherent miss).
- Potion's recorded error on this split is **syn-0176**, which the real LLM
  classifies **correctly**; the substitute scored 1.00 on its own fixture.

## Interpretation locked

All three systems are tied at the fixture ceiling (real 0.99, Potion 0.99,
substitute 1.00). The synthetic corpus is keyword-saturated, so this comparison
demonstrates harness compatibility and genuine real-model behavior, not model
superiority/inferiority. Generalization requires a harder, non-synthetic corpus
in a separate experiment.

## Checks / evidence

- checks.json: all applicable checks terminal `pass`; CLS-001/CLS-002 marked
  `not_applicable` because Potion is compared from recorded results, not retrained.
- durable artifacts under `runs/run-20260919-real-001/` including
  `error_analysis.md`, `comparison.json`, `leak_proof.txt`, `metrics.json`,
  `observability_reconciliation.json`, `run.json`.

## Exact next action

None — experiment completed and conclusion written. Optional follow-up (new
experiment): a harder multi-domain corpus on a freshly frozen split; do not
mutate `synthetic-topics-v1` membership in response to errors.
