# Checkpoint 0002 — primary local run + D1 NSAI export

**Checkpoint ID:** `cp-0002`
**Actor:** Grok (orchestrator)
**Date:** 2026-09-18

## State entering checkpoint

Checkpoint 0001 had frozen FinQA + LegalBench, a mock mechanics run, and pending D1 export / Luna scoring / lab sync. PR #2 was still open against an old `main`. Classifier-calibration on `main` had already completed.

## Work completed

1. Rebased the verification-harness tree onto current `main` (`6a3185df`).
2. Re-downloaded pinned FinQA and LegalBench bytes; SHA-256 matched `inputs/dataset-lock.json`. Regenerated gitignored `gold_index/` only.
3. FinQA executor now resolves named cells (`row|col`) and `table_*` column reduces against the visible table. B/C pass that table into independent re-execution.
4. Added distinct D1 NSAI prompt export (`export-luna-prompts --style d1`) and `LocalNSAITranslator`.
5. Added gold-blind `LocalExtractiveScoreProvider` because Luna / hosted generative LLM / SyMAI were unavailable. This is **not** the mock (mock reads gold).
6. Ran primary A/B/C (`run-20260918-local-001`) and separate D1 (`run-20260918-local-001-d1`) on the frozen 100 items. 200 exported packets scanned, 0 gold-token hits. 16 tests passed.
7. Wrote `conclusion.md`. Experiment status → completed.

## Results (frozen 50 FinQA + 50 LegalBench)

| Arm | Raw acc | Accepted acc | Coverage | Selective acc |
|-----|---------|--------------|----------|---------------|
| A   | 0.27    | 0.27         | 1.00     | 0.27          |
| B   | 0.27    | 0.3176       | 0.85     | 0.27          |
| C   | 0.27    | 0.3176       | 0.85     | 0.27          |
| D1  | 0.27    | 0.3176       | 0.85     | 0.27          |

Marginals A→B, B→C, C→D1 are all 0.0 on selective accuracy. B/C raise accepted-accuracy by rejecting 15 internally invalid items; they do not raise the share of gold-correct answers kept.

## Key decisions

- Do not treat mock metrics as the primary score.
- Do not invent a Luna result. Document the substitute the same way classifier-calibration documented LocalClosedSetScoreProvider.
- D2/Z3 remain `unavailable` (no silent fallback).
- Named-cell resolution is now implemented; program-equivalence vs gold programs is still not claimed.

## Next

None. Optional follow-up is a new experiment with real Luna/logprobs or SyMAI pinned, not a mutation of this frozen sample.
