# Conclusion — real-data A/B/C/D layered verification

## Answer to the experiment question

**On this frozen public sample, Grok-4.6 answers plus verification layers did not improve selective accuracy.** Arm A raw accuracy is 0.47. B/C raise accepted-accuracy (0.73 → 0.75) by cutting coverage (0.64 → 0.61). The A→B selective-accuracy marginal is **−0.01**; B→C and C→D1 are **0.0**.

That is a valid negative/neutral result. The harness was not tuned so that stronger layers had to look better.

Luna was unavailable. The owner directed Grok instead of Luna. An earlier extractive substitute run (`run-20260918-local-001`, raw acc 0.27) remains on disk as a weaker baseline, not the primary generative result.

## Setup

- Frozen sample: 50 FinQA + 50 LegalBench (seed `20260918`), revisions pinned in `inputs/dataset-lock.json`.
- Model: `grok-4.6`, gold-blind, answers in `harness/grok_answers.py`.
- A/B/C reuse one Grok response per item. D1 is a separately labeled NSAI treatment of the same judgments, still scored by B/C.
- 36/100 FinQA items abstained when the visible table did not support the question.
- Z3 and SyMAI: `unavailable`, not substituted.
- Mock run `run-20260918-mock-001` remains mechanics-only.

## Metrics — Grok-4.6 (N=100)

| Arm | Raw accuracy | Accepted accuracy | Coverage | False-accept | Selective accuracy | Abstain |
|-----|--------------|-------------------|----------|--------------|--------------------|---------|
| A   | 0.47 | 0.7344 | 0.64 | 0.2656 | 0.47 | 0.36 |
| B   | 0.46 | 0.7541 | 0.61 | 0.2459 | 0.46 | 0.36 |
| C   | 0.46 | 0.7541 | 0.61 | 0.2459 | 0.46 | 0.36 |
| D1  | 0.46 | 0.7541 | 0.61 | 0.2459 | 0.46 | 0.36 |

Evidence: `runs/run-20260918-grok-001/combined_metrics.json`.

## Limitations

- Grok answers are authored offline from visible packets, not a live token-logprob API call.
- Citizenship items use world knowledge; that is still gold-blind but is not “read the passage only.”
- Many FinQA abstentions: compact tables often omit the asked line.
- No live SEC/XBRL track. No SyMAI/Z3.

## Follow-up (new experiment, not this one)

Pin SyMAI/Z3, or rescore a larger sample. Do not treat a later Luna run as a silent upgrade of these Grok numbers.
