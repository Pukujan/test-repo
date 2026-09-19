# Real OpenCode LLM classifier vs Potion (compatibility run)

Replaces the documented TF-IDF+LogReg LLM substitute of
`2026-09-18_calibrated-llm-local-classifier` with the **actual OpenCode-configured
generative model** `yolo-auto/qwen3.8-flash`, on the **identical frozen split**
(synthetic-topics-v1, seed 20260918). One changed variable: substitute -> real LLM.

- Primary model: `qwen3.8-flash` via provider `yolo-auto` (owner-directed scope).
  `qwen3.8-27b`, `yolo`, `yolo-small` exist on the same provider (probed reachable)
  but were excluded from this run by owner instruction. `litellm/*` models are
  `unavailable` (LiteLLM proxy on localhost:4000 not running).
- Hard rule: **real or unavailable, never substitute.** No fallback path exists in
  `scripts/real_llm_pipeline.py`.
- Real candidate-label logprobs are available (`score_coverage=full` in smoke);
  temperature scaling is fit on the calibration split only.
- Potion baseline is **not retrained**: compared against the completed experiment's
  recorded results (8M/32M, acc 0.99, error `syn-0176`).
- Langfuse: `unavailable` (no credentials); OTel-shaped local JSONL used instead.
- The synthetic corpus is a compatibility fixture, not the final benchmark. A harder
  real multi-domain corpus is a **separate future experiment**, not a mutation here.

Read `HANDOFF.md`, then `AGENTS.md`, then the last checkpoint.
