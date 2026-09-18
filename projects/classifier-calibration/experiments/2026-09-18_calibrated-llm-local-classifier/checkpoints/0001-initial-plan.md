# Checkpoint 0001 — Initial local benchmark plan

## Durable decision

Created a new isolated project, `classifier-calibration`, for the classification benchmark tracked by `Pukujan/test-repo#3`.

The experiment scope is fixed to:

1. empirically calibrate and evaluate one LLM classifier;
2. train/test one local lightweight classifier, initially Model2Vec/Potion;
3. compare both on the identical frozen test set;
4. inspect errors and iterate.

Triage, consensus/jury, routing, graph construction, RAG, and orchestration are out of scope.

## Repository boundary

Only `Pukujan/test-repo` is authorized for GitHub work related to this experiment.

The repository is public. Private corpora, credentials, proprietary source text, model weights, and sensitive raw outputs stay local. Durable Git evidence should use manifests, hashes, metrics, sanitized fixtures, and safe summaries.

## Evaluation contract

- Use disjoint train, calibration, and test splits.
- Fit LLM calibration only on the calibration split.
- Train the local classifier only on the training split.
- Fit any local-classifier calibration only on the calibration split.
- Evaluate both systems on the exact same frozen test row IDs.
- Record classification metrics and probability-calibration metrics.
- Do not use model self-reported confidence as calibrated probability without empirical validation.

## Intended OSS

- pandas / pyarrow
- scikit-learn
- Model2Vec/Potion
- vLLM or another local OpenAI-compatible serving endpoint when applicable
- netcal only if needed
- SetFit only as an optional later baseline

## Exact next action

On the local machine:

1. clone `Pukujan/test-repo`;
2. read `HANDOFF.md` and `PLAN.md`;
3. prepare a safe dataset manifest and freeze train/calibration/test IDs;
4. create the first `runs/run-YYYYMMDD-local-001/`;
5. run the LLM calibration baseline and Potion/Model2Vec training baseline;
6. compare both on the same test IDs;
7. update checks/state and append checkpoint 0002.

No benchmark has been executed yet and no PASS is claimed.
