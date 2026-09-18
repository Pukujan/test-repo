# Conclusion — real-data A/B/C/D layered verification

## Answer to the experiment question

**On this frozen public sample, with a documented gold-blind local substitute for Luna, verification layers did not improve selective accuracy.** Arm B/C raised accepted-accuracy (0.27 → 0.32) by cutting coverage (1.00 → 0.85). The A→B / B→C / C→D1 selective-accuracy marginals are all **0.0**. The D1 NSAI-style translation, run from a distinct prompt export through the same B/C authority, matched B/C and added no extra reliability.

That is a valid negative/neutral result. The harness was not tuned so that stronger layers had to look better.

## Setup

- Frozen sample: 50 FinQA + 50 LegalBench (seed `20260918`), revisions pinned in `inputs/dataset-lock.json`.
- Gold never entered model-visible packets (leak scan 200/200 clean).
- A/B/C reused one local response per item. D1 used a separately exported NSAI packet set and separately generated responses.
- Z3 and SyMAI: `unavailable`, not substituted.
- Luna / local generative LLM: **unavailable**. Primary scores use `LocalExtractiveScoreProvider` / `LocalNSAITranslator` (visible text/table only). Mock run `run-20260918-mock-001` remains mechanics-only.

## Metrics (N=100)

| Arm | Raw accuracy | Accepted accuracy | Coverage | False-accept | Selective accuracy |
|-----|--------------|-------------------|----------|--------------|--------------------|
| A   | 0.27 | 0.27 | 1.00 | 0.73 | 0.27 |
| B   | 0.27 | 0.3176 | 0.85 | 0.6824 | 0.27 |
| C   | 0.27 | 0.3176 | 0.85 | 0.6824 | 0.27 |
| D1  | 0.27 | 0.3176 | 0.85 | 0.6824 | 0.27 |

Evidence: `runs/run-20260918-local-001/combined_metrics.json`.

## Limitations

- Extractive substitute, not Luna token logprobs. External validity for “GenAI + verifier” is limited.
- FinQA named-cell/`table_*` resolution exists, but the local provider does not emit gold programs; program-equivalence accuracy is not claimed.
- Legal heuristics are keyword triggers plus grounded span citation. They are weak on purpose and gold-blind.
- No live SEC/XBRL track. No synthetic-mutation primary score.

## Follow-up (new experiment, not this one)

Pin a real local Luna (or other instruct model) and/or a pinned SyMAI engine, freeze a new sample or reuse these IDs, and rescore. Do not treat a later Luna run as a silent upgrade of these substitute numbers.
