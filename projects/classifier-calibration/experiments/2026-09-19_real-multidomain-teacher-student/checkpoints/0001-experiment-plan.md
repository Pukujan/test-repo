# Checkpoint 0001 — Real multi-domain teacher-student experiment planned

## Durable decision

The next classifier experiment is not another synthetic or model-vs-model benchmark.

It will test the original operational question on real data:

> Can a cheap Potion/Model2Vec classifier trained from real qwen3.8-flash teacher labels learn useful domain classification behavior and generalize to an independent source-held-out gold test set?

## Frozen scope

Core top-level ontology:

- legal
- finance
- science
- technology

The first baseline remains single-label to isolate the teacher -> student classification question.

Natural mixed-domain documents are a separately reported challenge slice unless independently reviewed multi-label gold is available.

## Key experimental protections

- completed synthetic experiments remain immutable historical evidence;
- use real public heterogeneous documents, not synthetic topic sentences;
- prefer at least two source families per domain;
- primary test is source-held-out where feasible;
- remove obvious dataset/source fingerprint shortcuts;
- Qwen teacher output is never gold;
- Potion trains on Qwen teacher labels;
- calibration uses calibration gold only;
- final test gold/membership are frozen before inference and never used for fitting;
- qwen3.8-flash is real-or-unavailable only; no silent substitute;
- observability must reconcile row-level predictions, traces, and events.

## Exact next action

Before any model inference:

1. select/pin public source families for each domain;
2. write `inputs/source-lock.json`;
3. freeze `inputs/ontology.json`;
4. build `inputs/dataset_manifest.json`;
5. freeze source-aware `inputs/split_manifest.json`;
6. document independent gold in `inputs/gold_policy.md`;
7. run duplicate/source-shortcut/leak audits;
8. append checkpoint 0002 with the frozen data contract;
9. run `python tools/lab.py sync` and `python tools/lab.py validate`.

Do not invoke Qwen or train Potion until the data contract is frozen and durably committed.

No PASS is claimed in this checkpoint.
