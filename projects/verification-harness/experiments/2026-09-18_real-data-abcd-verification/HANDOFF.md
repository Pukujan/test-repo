# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `verification-harness-2026-09-18-real-data-abcd-verification`  
**Status:** `completed`

## Question

On real legal and financial benchmark examples, how much does each verification layer (deterministic validation, independent verification, neuro-symbolic translation) improve reliability beyond the model alone, measured against withheld gold, and can the experiment honestly report that a layer adds no value or hurts?

## Current focus

Experiment concluded after mock mechanics plus primary gold-blind local A/B/C and distinct D1 NSAI runs on the frozen FinQA+LegalBench sample.

## Last durable checkpoint

`checkpoints/0002-local-primary-and-d1.md` — Primary local substitute run + distinct D1 NSAI export; selective-accuracy marginals are zero; conclusion written.

## Exact next action

None — experiment completed. Optional follow-up is a new experiment with real Luna/logprobs or pinned SyMAI, not a mutation of this frozen sample.

## Blockers

- None.

## Important findings

- Luna and SyMAI were unavailable. Primary scores use gold-blind LocalExtractiveScoreProvider / LocalNSAITranslator. Mock run is mechanics-only.
- On the frozen 100-item public sample, A raw accuracy is 0.27. B/C raise accepted-accuracy to 0.32 by cutting coverage to 0.85. Selective-accuracy marginals A→B, B→C, C→D1 are all 0.0.
- D1 used a distinct NSAI-formatted export and separate responses; it still routes through the same B/C authority and did not improve reliability.
- Z3 and SyMAI remain unavailable and were not substituted.
- FinQA named-cell and table_* resolution now runs against the visible table. Program-equivalence vs gold programs is not claimed.
- Gold/visible separation still holds: 200 exported packets scanned, 0 gold-token hits.
- The repository is public; raw dataset bytes and gold stay gitignored.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
