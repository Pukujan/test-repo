# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `verification-harness-2026-09-18-real-data-abcd-verification`  
**Status:** `completed`

## Question

On real legal and financial benchmark examples, how much does each verification layer (deterministic validation, independent verification, neuro-symbolic translation) improve reliability beyond the model alone, measured against withheld gold, and can the experiment honestly report that a layer adds no value or hurts?

## Current focus

Experiment concluded. Primary generative run is Grok-4.6 on the frozen FinQA+LegalBench sample; Luna remains unavailable.

## Last durable checkpoint

`checkpoints/0003-grok-primary.md` — Grok-4.6 primary A/B/C/D1 run; selective-accuracy A→B marginal −0.01; layers add no reliability.

## Exact next action

None — experiment completed. Grok replaced Luna for this sample.

## Blockers

- None.

## Important findings

- Owner directed Grok instead of Luna. Primary scores are grok-4.6, gold-blind, encoded in harness/grok_answers.py.
- Grok A raw accuracy is 0.47 with 36% FinQA abstention when the visible table could not support the question.
- B/C raise accepted-accuracy 0.73→0.75 and cut coverage 0.64→0.61. A→B selective marginal is −0.01. D1 matches C.
- The earlier extractive substitute (raw 0.27) is a weaker baseline, not the primary generative result.
- Z3 and SyMAI remain unavailable and were not substituted.
- Mock run is mechanics-only.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
