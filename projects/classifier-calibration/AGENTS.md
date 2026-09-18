# Classifier Calibration Project Rules

Read root `AGENTS.md` first.

For experiments in this project:

- Stay inside `Pukujan/test-repo`; do not inspect or mutate any other GitHub repository for this project.
- Keep the project limited to LLM calibration, local classifier training/testing, evaluation, and controlled iteration.
- Do not add triage, consensus/jury, routing, graph, RAG, or orchestration work unless a new experiment is explicitly created for it.
- Use disjoint train, calibration, and test splits. Never fit prompts, thresholds, calibration transforms, classifier parameters, or label mappings on the final test set.
- Evaluate competing models on the same frozen test row IDs and label schema.
- Preserve exact prompts/configs/model identifiers/seeds and environment facts needed to reproduce each run.
- Never equate model self-reported confidence with calibrated probability without empirical calibration evidence.
- This repository is public. Keep private corpora, credentials, proprietary text, model weights, and sensitive raw predictions local.
- Append checkpoints; do not rewrite experimental history.
- Before handoff, update `state.json` and `checks.json`, append a checkpoint, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
