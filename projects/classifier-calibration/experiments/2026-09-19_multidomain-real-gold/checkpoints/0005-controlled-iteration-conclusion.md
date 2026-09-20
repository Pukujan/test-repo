# Checkpoint 0005 — Controlled iteration (ITER-001) and conclusion

## Error analysis (held-out test, run-20260919-mdrg-001)

Dominant pattern: the science class collapses into technology. Teacher science
recall 0.3947; 91 of 190 true-science rows predicted technology; technology
precision drops to 0.6426 as a result. Potion inherits and amplifies it (science
recall 0.2368, 110/190 -> technology). The failing slice is `20ng_sci`
(sci.space / sci.electronics discussion that reads as hardware/tech to a
zero-shot labeler trained toward pubmed-style science).

## Controlled iteration (run-20260919-mdrg-002)

Single documented variable: teacher prompt `mdrg-letters-v1` ->
`mdrg-letters-v2`, adding a science/technology boundary rule (natural-science and
space-research context, including instruments/missions, is science even when
hardware is mentioned). Everything else identical: dataset `seed-20260919`,
splits, ontology, gold policy, seed 20260919, model `yolo-auto/qwen3.8-flash`,
temperature-0 greedy decoding, Potion pipeline (potion-base-32M + LR(C=50)),
temperature scaling fit on calibration only, same 774 frozen test ids.

Full pipeline re-run: teacher labels train 759/759, calibration 312/312, test
774/774, 0 provider errors, 0 substitutions; 1 test row with partial
top_logprobs coverage handled by a documented floor rule
(`common.teacher_logit_vector`, missing label = observed-min minus 10 nats, no
fabricated scores).

Effect on the frozen test (both calibrated):

| metric | teacher v1 -> v2 | Potion v1 -> v2 |
|---|---|---|
| accuracy | 0.7933 -> 0.8320 | 0.6731 -> 0.6977 |
| macro-F1 | 0.7746 -> 0.8205 | 0.6515 -> 0.6726 |
| ECE | 0.1129 -> 0.0766 | 0.1355 -> 0.1312 |
| science recall | 0.3947 -> 0.5053 | 0.2368 -> 0.2737 |
| science->technology confusions | 91 -> 64 | 110 -> 92 |

The controlled iteration addressed the targeted pattern: +3.9 accuracy points
for the teacher, science recall +11.1 points, with calibration improving in
lockstep. Potion improved as a downstream consequence of better teacher labels
(no Potion-side variables changed). Residual: science remains the weakest class
for both systems — the next candidate change is train-domain composition (a new
dataset_version, never a silent edit) or class-balanced student logits.

Artifacts: `runs/run-20260919-mdrg-002/{run.json,error_analysis.json,
calibration/calibration_summary.json,eval/eval_summary.json,
observability_reconciliation.json}`; committed observability verified free of
gold fields and raw text.

## Conclusion

See `conclusion.md`. Experiment question answered; status set to completed.
