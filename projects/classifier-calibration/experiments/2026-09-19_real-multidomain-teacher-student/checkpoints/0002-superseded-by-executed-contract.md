# Checkpoint 0002 — Superseded by the executed multi-domain contract

## What this records

A parallel plan-only branch of this experiment (`origin/main` @
`ceec93d976b8c97d52561765f79f36e86254a944`) was created at `2026-09-19T05:42:00Z`
and never executed: its `inputs/` directory contains only a `README.md`
placeholder, every check in `checks.json` is still `pending`, and its
`next_action` asks for the Phase 0 freeze that a sibling experiment has already
completed and committed.

## Duplicate-question collision (flagged before spending Qwen calls)

This plan and the sibling experiment
`2026-09-19_multidomain-real-gold` (local commit
`28fe876c9d337399bd7e1bb71a256523cf4f3475`, created `2026-09-19T06:00:00Z`)
own the **same durable question**: a real heterogeneous legal/finance/science/
technology corpus, a `yolo-auto/qwen3.8-flash` teacher, a Potion/Model2Vec
student trained on teacher labels (not gold), calibrated probabilities, and an
independent source-held-out real-gold test. Same seed date (`20260919`), same
four-label ontology, same source-holdout + gold-separation policy.

The sibling went **past** this plan's entire next action:

- it pinned sources (`inputs/source-lock.json` with sha256 + immutable HF
  revisions), froze `inputs/ontology.json`, `gold_policy.md`, the dataset and
  split manifests, and ran the leak/source-fingerprint/duplicate audits
  (`inputs/audit_report.json`, `clean: True`);
- it froze concrete splits (seed 20260919, cal frac 0.3; test T191/S190/F200/
  L193 after 24 documented leak prunes) and its next action is now real Qwen
  teacher labeling on the train split only.

## Source/split collision risk

If this plan were executed independently, it would re-fetch, re-split, and
re-audit the same domains under the same seed and produce a second frozen
contract for one question, violating "one experiment answers one durable
question". Because the sibling already pruned 24 test rows and committed exact
split membership, any non-byte-identical re-execution here would become a
divergent `dataset_version` competing with the frozen sibling test split — a
split-collision and a second-frozen-test hazard. No Qwen calls were spent here,
and none should be.

## Durable decision

This experiment is `superseded` by `2026-09-19_multidomain-real-gold`. Its
plan content (PLAN.md/ONTOLOGY.md) is retained as durable design history; it is
not deleted and no earlier checkpoint is rewritten. The live continuation, the
frozen contract, and all future Qwen/Potion runs belong to the sibling
experiment. No PASS is claimed in this checkpoint.
