# Experiment Continuation Instructions

Read root `AGENTS.md`, `LAB_SPEC.md`, and `../AGENTS.md` first.

This experiment implements `Pukujan/test-repo#1`.

## Start here

1. Read `HANDOFF.md`.
2. Read the checkpoint named by `state.json.last_checkpoint`.
3. Verify the frozen `inputs/dataset-lock.json` revisions still match upstream (FinQA `0f16e286…`, legalbench `daec8237…`) before producing real model outputs.
4. Do not regenerate the sample: `inputs/sample-manifest.json` and `inputs/dataset-lock.json` are frozen with seed `20260918`.

## Hard boundaries

- Raw dataset bytes and gold are gitignored (`local_data/`, `gold_index/`). Never commit them.
- Exported model-visible packets must never contain gold. Tests in `../../tests/test_leak_safety.py` enforce this; run them before any claim.
- Arms A/B/C must reuse the SAME saved model response. B/C must not read gold for their decision. Gold is read only in `arms.score_answer_*` for scoring.
- Z3/SyMAI absence must be reported `unavailable` (see `harness/capabilities.py`); never substitute another arm.

## Real Luna workflow (when model runs begin)

```bash
python -m harness.cli prepare
python -m harness.cli export-luna-prompts --out runs/<run-id>/luna/
# run each exported packet with Luna locally, save strict JSON responses
python -m harness.cli ingest-luna --responses runs/<run-id>/luna/responses/
python -m harness.cli run --arms A,B,C --provider luna --responses runs/<run-id>/luna/responses/ --run-id <run-id>
python -m harness.cli run --arms D1 --provider luna --responses runs/<run-id>/luna/responses-d1/ --run-id <run-id>
python -m harness.cli report --run-id <run-id>
```

The deterministic mock path (`--provider mock`) validates mechanics without credentials; it is NOT a benchmark result.

## Handoff

Before stopping: update `state.json`/`checks.json`, append a new checkpoint, run `python tools/lab.py sync`, then `python tools/lab.py validate`, and commit.
