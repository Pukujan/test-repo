# Real-data A/B/C/D layered-verification benchmark

Does each verification layer (deterministic validation, independent verification, neuro-symbolic translation) actually improve reliability of GenAI answers on **real legal and financial benchmark data**, measured against withheld gold — and can the experiment honestly show that a layer adds nothing or hurts?

This experiment implements `Pukujan/test-repo#1`.

## Arms

- **A** — model answer only (baseline).
- **B** — deterministic structured validation of the model's own answer/program/evidence (no gold consulted).
- **C** — independent verification (recompute arithmetic, validate spans, bounded rule checks; optional Z3).
- **D1** — neuro-symbolic translation prompt, then the **same** B/C authority.
- **D2** — optional SymbolicAI/SyMAI adapter (unavailable unless installed and pinned; may never mint PASS).

## Primary data

- Financial: **FinQA** public test split (`czyssrs/FinQA`), deterministic seed `20260918` sample (~50, scaling to 100+).
- Legal: **LegalBench** objective-label tasks + **ContractNLI** families via the paper author's official `nguha/legalbench` dump, deterministic sample (~50).

Dataset revisions and selected record IDs are frozen before inference in `inputs/dataset-lock.json` and `inputs/sample-manifest.json`.

## Layout

- `harness/` (project-level, sibling of this experiment): reproducible Python package (sampling, packet builder with gold-separation + leak guard, FinQA program executor, legal evidence validator, independent verifier, Luna prompt exporter/importer, mock provider, arms runner, metrics).
- `inputs/`: frozen dataset lock + sample manifest + acquisition instructions (no redistributed gold bytes committed here).
- `runs/`: concrete executions (mock mechanics run first).

See the project and root `AGENTS.md` for the non-negotiable rules.
