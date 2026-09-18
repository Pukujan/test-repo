# Error analysis — run-20260918-local-002

## Summary

- Test N: 100
- LLM-substitute accuracy: 1.0000 (macro-F1 1.0000)
- Potion accuracy: 0.9900 (macro-F1 0.9900)
- Disagreements: 1
- Both wrong: 0; LLM-only wrong: 0; Potion-only wrong: 1

## Calibration notes

- LLM temperature T=0.0500; pre/post cal log-loss 0.0820 → 0.0000
- Potion temperature T=0.1500; pre/post cal log-loss 0.5395 → 0.0354

## Disagreement / error slices

Sample IDs (truncated) are listed in `comparison.json`. Raw text is omitted under `hashes_only` content mode; join locally via `sample_id` to the fixture if needed.

## One next hypothesis

Potion potion-base-32M still errs more than the score provider on the frozen test set. Optional follow-up: try a different Model2Vec training recipe (more epochs / lower early-stopping patience) or a denser embedding, keeping the same frozen IDs.
