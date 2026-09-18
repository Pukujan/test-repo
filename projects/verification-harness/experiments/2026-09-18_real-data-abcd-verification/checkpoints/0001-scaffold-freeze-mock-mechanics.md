# Checkpoint 0001 — scaffold, freeze, mock mechanics

**Checkpoint ID:** `cp-0001`
**Actor:** OpenCode (orchestrator: grok-4.6)
**Date:** 2026-09-18

## State entering checkpoint

Issue #1 requested an A/B/C/D layered-verification benchmark over real legal + financial data. The lab repo had one prior experiment (fossil). Nothing existed for this experiment.

## Work completed

1. Read README, LAB_SPEC, root and fossil project AGENTS/checkpoint conventions; mapped `tools/lab.py` validation contract (generated files, 40-char SHAs, evidence-path resolution, ID patterns).
2. Pinned real datasets with exact 40-char revisions and SHA-256 digests:
   - FinQA: `czyssrs/FinQA@0f16e2867befa6840783e58be38c9efb9229d742`, `dataset/test.json` (1147 items, sha256 831dbfb2...).
   - Legal: `nguha/legalbench@daec8237410aa23e3faf4bc41ad8b3a7e1696826` — the official dump by a LegalBench co-author, which contains BOTH ContractNLI families and objective LegalBench tasks in one source.
   Chose five deterministic Yes/No tasks: hearsay, definition_classification, overruling, contract_nli_confidentiality_of_agreement, international_citizenship_questions (dropped free-text rule_qa to keep one clean label authority).
3. Froze the sample with seed `20260918` using a version-stable digest-rank (sha256(seed:item_id)) — NOT Python's RNG — so the selection cannot drift across interpreters. 50 FinQA + 50 LegalBench; committed `inputs/sample-manifest.json` (IDs + visible digests only) and `inputs/dataset-lock.json` (revisions + digests + acquisition). Raw bytes and gold live only in gitignored `local_data/` and `gold_index/`; nothing redistributable/gold is committed to this public repo.
4. Built `harness/`: schemas (single-source field interface + leak substrings), record (packet builder + LeakError guard), freeze, finqa_program (deterministic FinQA DSL executor, machine-readable failure codes, never crashes), legal_validate (structured legal validator with evidence-grounding check, no gold), capabilities (z3/symai detection), arms (A/B/C/D1/D2 with authority separation; D1 runs through the same B/C authority; D2 refuses to mint PASS), prompt_io (export only visible packets; shape-only ingest), mock (deterministic, digest-derived; sole gold reader, confined), metrics (coverage, false accept/reject, selective accuracy, marginals, unique catches), cli (prepare/export/ingest/run/report).
5. Ran the deterministic mock end to end (50+50 items x A/B/C/D1). Result is an honest tradeoff: B/C raise accepted-accuracy 0.46→0.60 while coverage drops 0.87→0.43 and A→B selective marginal is −0.14. Confirms the benchmark can produce negative/neutral outcomes (no rigged win). Z3 and SyMAI recorded `unavailable` (not installed here; not substituted).
6. Wrote 14 tests (5 leak-safety, 9 mechanics), all passing. Captured durable evidence into `runs/run-20260918-mock-001/` (records.json, metrics.json, mechanics_tests.txt, leak_export_proof.txt, run.json): 101 exported packets scanned, 0 gold-token hits.

## Key decisions

- Authority separation is structural, not procedural: gold is read ONLY in `arms.score_answer_*` (scoring) and `harness/mock.py` (fabrication); B/C decisions read no gold. A correct-but-ungrounded legal answer is rejected even when gold would say the label is right — verified by test.
- The mock provider is explicitly labeled a mechanics harness, NOT a benchmark result.

## Not yet tested (the real benchmark)

No real Luna responses yet (no model API in this environment). `LUNA-001` and `D1-001` remain pending; `SYMAI-001` blocked.

## Known limitation

FinQA `table_*`/named-cell args are not resolved against the visible table (numeric-literal programs execute; gold `exe_ans` is used for scoring). Resolve symbolic cell refs before claiming program-equivalence accuracy.

## Exact next action

Owner, on a machine with Luna:

```bash
python -m harness.cli export-luna-prompts --out runs/run-20260918-luna-001/luna
# run each packet with Luna locally; save strict JSON responses under runs/run-20260918-luna-001/luna/responses/
python -m harness.cli ingest-luna --responses runs/run-20260918-luna-001/luna/responses/
python -m harness.cli run --arms A,B,C --provider luna --responses runs/run-20260918-luna-001/luna/responses/ --run-id run-20260918-luna-001
# separate D1 NSAI-style packet set under luna-d1/responses/, then:
python -m harness.cli run --arms D1 --provider luna --responses runs/run-20260918-luna-001/luna-d1/responses/ --run-id run-20260918-luna-001-d1
python -m harness.cli report --run-id run-20260918-luna-001
```

Append a checkpoint with the real per-arm metrics; do NOT reuse mock numbers as the result.
