# Verification Harness Experiment Rules

Read root `AGENTS.md` and `LAB_SPEC.md` first.

For verification-harness experiments:

- The benchmark answers a reliability question; it must be able to produce a negative or null result. Do not tune the harness so stronger verification is guaranteed to look better.
- Real public benchmark records are the primary scoring material. Synthetic/planted defects are a separately reported robustness track only, never the primary score.
- Gold labels, gold programs, reference spans, and scoring fields must never enter a model-visible packet. Enforce this with a deterministic leak guard that CI runs; model prose is not evidence.
- Freeze dataset revisions and selected sample IDs **before** any model inference. The same frozen item and the same saved Luna response feed arms A, B, and C.
- Arm decisions (B, C) must be made without consulting benchmark gold labels. Gold is used only after inference for scoring.
- A layer may not mint its own PASS from its own prose. D (neuro-symbolic) proposes structure; only deterministic B/C downstream may accept it.
- Missing optional backends (Z3, SyMAI) are recorded as `unavailable`. Never silently substitute another arm or upgrade `unavailable` to pass.
- Distinguish clearly: model answer, model-proposed symbolic structure, deterministic validation, independent verification, and gold score. These are different authorities.
- Before handoff: update `state.json`/`checks.json`, append a checkpoint, run `python tools/lab.py sync` then `python tools/lab.py validate`.
