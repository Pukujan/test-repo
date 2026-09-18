# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `verification-harness-2026-09-18-real-data-abcd-verification`  
**Status:** `running`

## Question

On real legal and financial benchmark examples, how much does each verification layer (deterministic validation, independent verification, neuro-symbolic translation) improve reliability beyond the model alone, measured against withheld gold, and can the experiment honestly report that a layer adds no value or hurts?

## Current focus

Harness scaffold + frozen real data (FinQA + LegalBench) + A/B/C/D1 mechanics validated end-to-end via deterministic mock with proven gold separation.

## Last durable checkpoint

`checkpoints/0001-scaffold-freeze-mock-mechanics.md` — Scaffolded harness, froze 50 FinQA + 50 LegalBench sample (seed 20260918) with gold separated, validated A/B/C/D1 mechanics + leak guard via deterministic mock; Z3/SyMAI recorded unavailable.

## Exact next action

Run the primary real-data benchmark with the owner's local Luna: (1) python -m harness.cli export-luna-prompts --out runs/run-20260918-luna-001/luna ; (2) run each packet with Luna locally and save strict JSON responses ; (3) ingest-luna then run --arms A,B,C --provider luna ; (4) separately export/ingest a distinct D1 NSAI-style prompt set and run --arms D1 ; (5) score, append a checkpoint with the real per-arm metrics, and update checks LUNA-001/D1-001 with evidence. Do NOT reuse mock results as a benchmark result.

## Blockers

- Real Luna inference requires the owner's local model; this environment has no model API.
- Z3 and SymbolicAI/SyMAI are not installed here; C-with-Z3 and D2 remain unavailable until installed and pinned (never substituted).
- FinQA named-cell/table_* program args are not resolved against the visible table (numeric-literal programs execute; gold exe_ans is used for scoring). Resolving symbolic cell references is an open refinement before program-equivalence accuracy is claimed.

## Important findings

- A single redownloadable public source, nguha/legalbench (official dump by a LegalBench co-author, revision daec8237410aa23e3faf4bc41ad8b3a7e1696826), provides BOTH ContractNLI families and objective-label LegalBench tasks, satisfying the legal-side requirement in one pinned dataset.
- The legal task set is restricted to deterministic Yes/No classification (hearsay, definition_classification, overruling, contract_nli_confidentiality_of_agreement, international_citizenship_questions) so the structured legal validator has one clean label authority; free-text rule_qa was dropped to avoid brittle exact-match scoring.
- FinQA official repo is czyssrs/FinQA at 0f16e2867befa6840783e58be38c9efb9229d742 (test.json = 1147 items, sha256 831dbfb2...). Raw bytes and gold are gitignored, not committed to this public repo.
- Gold/visible separation is enforced three ways: freeze-time strip, build_visible_packet guard, and 101-export token scan (0 hits). B/C never read gold for their decision; only arms.score_answer_* does.
- The mock run is a deliberate honest tradeoff, not a rigged win: B/C lift accepted-accuracy (0.46->0.60) but cut coverage (0.87->0.43) and A->B selective marginal is negative (-0.14) with a 16% false-reject rate. This proves the benchmark can produce negative/neutral layer results.
- The mock provider is the ONLY place gold is read (to fabricate realistic correct/incorrect mixes); arms consume stored responses and never re-read gold.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
