# Experiment Continuation Instructions

Read root `AGENTS.md`, `LAB_SPEC.md`, and `../AGENTS.md` first.

This experiment replaces the documented LLM substitute in the completed
`2026-09-18_calibrated-llm-local-classifier` with real OpenCode-accessible
generative models. The previous experiment is frozen history; do not rewrite it.

## Start here

1. Read `HANDOFF.md`.
2. Read the checkpoint named by `state.json.last_checkpoint`.
3. Confirm `inputs/fixtures/*.json` digests match the completed experiment
   (frozen split; the only changed variable is the model).
4. Confirm `QWEN_API_KEY` is present and the provider is reachable
   (`GET https://yolo-auto.com/v1/models`) before any inference.

## Hard boundaries

- **Real or unavailable; never substitute.** No TF-IDF, logistic regression,
  mock, or heuristic may produce a prediction. A failed call is recorded as a
  provider error and counted, never replaced.
- Do not expose gold labels in model-visible messages (pipeline asserts this per
  sample; keep that guard).
- Calibration may be fit on the calibration split only. Never on test.
- Do not edit frozen split membership or the prompt after seeing test errors.
- Model self-reported confidence is not calibrated probability; here we use real
  logprobs, not self-report. If logprobs ever disappear, mark `unavailable`; do
  not fabricate scores.
- Do not retrain or retune Potion to beat the LLM; compare against recorded
  results (`2026-09-18` runs).
- Every prediction row must carry: model_id, provider_id, invocation_path,
  timestamp, latency, tokens, trace_id, and score/logprob status.

## Commands

```bash
python scripts/real_llm_pipeline.py --mode smoke --model qwen3.8-flash \
  --run-id run-20260919-real-001 --smoke-n 8
python scripts/real_llm_pipeline.py --mode full --model qwen3.8-flash \
  --run-id run-20260919-real-001
```

## Handoff

Before stopping: update `state.json`/`checks.json`, append a checkpoint, run
`python tools/lab.py sync`, then `python tools/lab.py validate`, and commit.
