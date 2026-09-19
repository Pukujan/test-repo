# Experiment Continuation Instructions

Read root `AGENTS.md`, `LAB_SPEC.md`, and `../AGENTS.md` first.

This experiment builds a harder multi-domain real-gold benchmark to replace the
saturated synthetic fixture used by the two completed 2026-09-18/19 runs. The
frozen data contract is committed **before** any model inference; afterwards it is
append-only.

## Start here

1. Read `HANDOFF.md`.
2. Read the checkpoint named by `state.json.last_checkpoint`.
3. Confirm `inputs/source-lock.json` digests match freshly re-downloaded sources
   (raw bytes are gitignored; verify by digest, do not re-commit text).
4. Confirm the primary test domains are source-disjoint from train/teacher/calibration.

## Hard boundaries

- **Freeze before inference.** Once a run uses the contract, no edit to
  `source-lock.json`, `ontology.json`, `dataset_manifest.json`, or
  `split_manifest.json`. A needed change is a new `dataset_version` + a
  corrective checkpoint, never a silent edit.
- **Source-holdout.** The primary test set may not share a source with training,
  teacher-labeling, or calibration data for that domain. Enforced by disjoint
  `source_id` sets recorded in the split manifest.
- **Gold separation.** Held-out real gold is scoring-only. It never enters a
  model-visible prompt, and Potion is trained on Qwen teacher labels, not real
  gold. Keep the deterministic leak guard green.
- **Real or unavailable, never substitute**, for Qwen teacher inference and any
  later evaluation call.
- **Teacher = `yolo-auto/qwen3.8-flash` only** (owner scope). If it becomes
  unavailable, record `unavailable`; do not substitute another model.
- Calibration transforms fit on the calibration split only, never on test.
- Public repo: commit only manifests, hashes, ontology, policies, and aggregate
  metrics. Raw licensed text, gold, and any prediction file embedding licensed
  full text stay local/gitignored.

## Handoff

Before stopping: update `state.json`/`checks.json`, append a checkpoint, run
`python tools/lab.py sync`, then `python tools/lab.py validate`, and commit.
