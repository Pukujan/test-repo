# Checklist

> Generated from `checks.json`. Do not edit directly.

- [x] **DATA-001** — Pin real dataset upstreams at exact revisions with per-file SHA-256 digests and acquisition instructions (no redistributed gold bytes committed). (`pass`)
  - pinned revisions, digests, acquisition: inputs/dataset-lock.json
- [x] **SEED-001** — Deterministically freeze the 50 FinQA + 50 LegalBench sample with seed 20260918 before any inference; record selected IDs and visible digests. (`pass`)
  - frozen sample manifest (seed 20260918): inputs/sample-manifest.json
- [x] **LEAK-001** — Model-visible packets and exported prompt files never expose gold keys or gold values; deterministic guard rejects gold keys. (`pass`)
  - leak-safety test suite: ../../tests/test_leak_safety.py
  - 101 exported packets scanned, 0 gold-token hits: runs/run-20260918-mock-001/leak_export_proof.txt
  - test run output: runs/run-20260918-mock-001/mechanics_tests.txt
- [x] **GOLD-SEP-001** — B/C accept/reject decisions are made without consulting gold (a correct-but-unsupported legal answer is rejected on evidence grounding); gold is read only in scoring helpers. (`pass`)
  - authority-separation test: ../../tests/test_mechanics.py
  - test run output: runs/run-20260918-mock-001/mechanics_tests.txt
- [x] **ARMS-001** — A/B/C reuse the SAME saved response per item; D1 passes the proposal through the same B/C authority instead of minting its own PASS. (`pass`)
  - per-item arm records (one response, four arms): runs/run-20260918-mock-001/records.json
- [x] **EXEC-001** — FinQA reasoning-program DSL executes deterministically with machine-readable failure codes and never crashes on malformed programs. (`pass`)
  - executor tests: ../../tests/test_mechanics.py
  - test run output: runs/run-20260918-mock-001/mechanics_tests.txt
- [x] **CAP-001** — Missing optional backends are typed unavailable and never substituted; metrics record z3/symai status. (`pass`)
  - capabilities field shows z3=unavailable, symai=unavailable: runs/run-20260918-mock-001/records.json
  - D2-unavailable test: ../../tests/test_mechanics.py
- [x] **NEG-001** — The benchmark can report negative/neutral layer value: mock run shows B/C raise accepted-accuracy (0.46->0.60) while cutting coverage (0.87->0.43) with negative A->B selective marginal (-0.14); no rigged-win structure. (`pass`)
  - aggregate metrics with marginal gains, false accept/reject rates: runs/run-20260918-mock-001/metrics.json
- [x] **MOCK-001** — Deterministic mock provider validates full A/B/C/D1 mechanics without credentials and is byte-stable across runs. (`pass`)
  - mock determinism + shape tests: ../../tests/test_mechanics.py
  - mock run record: runs/run-20260918-mock-001/run.json
- [ ] **D1-001** — Distinct NSAI-formatted D1 prompt export and separately-ingested D1 responses exist and are labeled a translation/orchestration treatment. (`pending`)
- [ ] **LUNA-001** — Real Luna responses exported, executed by the owner locally, ingested, and scored through A/B/C/D1 (primary real-data benchmark result). (`pending`)
- [-] **SYMAI-001** — Optional SymbolicAI/SyMAI D2 adapter with pinned version and engine identity; unavailable until symai is installed (never a silent fallback). (`blocked`)
- [ ] **LAB-001** — python tools/lab.py sync and validate pass for this experiment. (`pending`)
