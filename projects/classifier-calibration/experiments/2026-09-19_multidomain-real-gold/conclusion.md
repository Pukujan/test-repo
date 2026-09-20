# Conclusion — multidomain-real-gold benchmark

## Question

On a harder multi-domain benchmark where the primary test set is
source-held-out from training/teacher/calibration, how do a calibrated
Qwen3.8-flash teacher and a Potion classifier trained on Qwen labels (not real
gold) compare on the same untouched real-gold test set, and what error pattern
does one controlled iteration address?

## Answer

On the frozen source-held-out test set (774 rows, four held-out sources
disjoint from all train/teacher/calibration corpora, real independent topical
gold, identical ids for both systems):

- **Calibrated Qwen3.8-flash teacher** (v1 prompt): accuracy **0.793**,
  macro-F1 **0.775**, ECE 0.113.
- **Potion student trained on Qwen labels** (never real gold): accuracy
  **0.673**, macro-F1 **0.651**, ECE 0.135.
- The teacher outperforms its own distilled student by **12.0 accuracy
  points** on cross-domain real gold — the distillation gap is real and
  large, even though both fit on the same information.
- Temperature scaling on the calibration split reduced teacher calibration
  error materially (calibration-set ECE 0.073 -> 0.025) but ECE on the
  shifted test domains stayed elevated (0.113) — held-out-domain
  over-confidence is not fixed by a single global temperature.
- **One controlled iteration** (prompt v1 -> v2, a single documented
  science/technology boundary rule) targeted the dominant error pattern —
  science collapsing into technology (teacher science recall 0.395, 91/190
  true-science rows predicted technology). It addressed it: teacher accuracy
  0.793 -> 0.832 (+3.9 pts), science recall 0.395 -> 0.505, confusions
  91 -> 64, ECE 0.113 -> 0.077; Potion improved downstream (0.673 -> 0.698)
  with no Potion-side change. Science remains the weakest class — the
  residual motivates a future dataset-composition version change, not a
  silent edit.

## Evidence

- Contract + audit: `inputs/` (frozen before any inference, gate re-verified
  byte-identical at every stage).
- run-20260919-mdrg-001: `runs/run-20260919-mdrg-001/{run.json,calibration/
  calibration_summary.json,eval/eval_summary.json,
  observability_reconciliation.json}` (teacher 759+312+774, 0 errors 0
  substitutions, real logprobs).
- run-20260919-mdrg-002 (controlled iteration): `runs/run-20260919-mdrg-002/
  {run.json,error_analysis.json,eval/eval_summary.json,
  observability_reconciliation.json}`.
- Checkpoints 0001-0005 are the durable narrative.

## Limitations

- 20newsgroups is memorization-prone; some test rows may predate the training
  cut (documented in the contract).
- Train/calibration gold is source membership, not human topical judgment;
  the teacher's ~87-89% agreement with it is itself a measure of that
  mismatch, and that teacher noise is deliberately kept in the student target.
- Single run, single temperature, single global prompt change; no seeds
  variance estimates.

## Security note

A prompt-injection/RCE attempt embedded in tool output (curl of a TEST-NET
address, later a false claim of prior execution) was refused throughout; no
contact, no execution, plan unaltered. Recorded in checkpoints 0001+ and
state.json.
