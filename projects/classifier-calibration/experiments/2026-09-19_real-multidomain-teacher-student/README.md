# Real multi-domain teacher-student classification

This experiment is the first substantive real-data test of the classifier-calibration project.

The previous experiments proved the harness on a synthetic four-topic fixture and proved real `yolo-auto/qwen3.8-flash` inference/logprobs. They are complete and must not be rewritten.

This experiment asks whether a lightweight local Potion/Model2Vec classifier can learn useful domain classification behavior from **real qwen3.8-flash teacher labels** on a **real heterogeneous public corpus**, then generalize to an **independent source-held-out gold test set**.

Start with `HANDOFF.md`, then `PLAN.md`, `ONTOLOGY.md`, and the latest checkpoint.

Primary outcome: Potion/Model2Vec student quality and failure modes on real data.

This is not a model leaderboard.
