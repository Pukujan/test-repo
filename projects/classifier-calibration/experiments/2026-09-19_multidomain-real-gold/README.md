# Multi-domain real-gold classifier (Qwen teacher + Potion)

Successor to `2026-09-19_real-opencode-llm-classifier`. The previous experiment
showed the synthetic fixture is saturated (real LLM 0.99, Potion 0.99, substitute
1.00 — a ceiling, not a quality signal). This experiment builds a **harder,
multi-domain, real-gold** benchmark where the primary test set is **source-held-out**:
every test domain comes from a corpus absent from training, so source/benchmark
memorization cannot inflate the score.

Domain ontology (pinned in `inputs/ontology.json`): legal, finance, science, technology.

## Pipeline (one frozen contract, then one changed variable at a time)

1. **Freeze** the data contract first: `source-lock.json`, `ontology.json`,
   `dataset_manifest.json`, `split_manifest.json`, `gold_policy.md`; audited for
   duplicates, source/benchmark-name leakage, dataset fingerprints, and gold
   leakage. Commit only digests/manifests, **never** raw text or gold (public repo).
2. **Qwen teacher labels** (`yolo-auto/qwen3.8-flash`, real logprobs, no substitute).
3. **Calibrate Qwen** on the calibration split only.
4. **Train Potion** on Qwen teacher labels (not on real gold).
5. **Calibrate Potion** on the same calibration split.
6. Evaluate **both** on the same **untouched real-gold** source-held-out test set.
7. Error analysis + **one** controlled iteration.

## Hard boundaries

- **Source-holdout is the point.** A test domain's corpus may not contribute any
  training/teacher/calibration row. Enforced by disjoint source IDs in the split
  manifest.
- **Gold separation.** Real gold for the held-out test is used only for final
  scoring, never in a model-visible packet and never as a training target. Potion
  trains on Qwen teacher labels, not real gold. Enforced by a deterministic leak
  guard mirroring `../..verification-harness`.
- **Real or unavailable, never substitute** for any inference step.
- Calibration fits on the calibration split only; never on test.
- Do not edit the frozen contract after inference. If it must change, a new
  dataset_version + new experiment, not a silent edit.
- Digest-pin only: raw corpus bytes, gold, and teacher predictions that embed
  licensed text stay local/gitignored; only manifests/hashes/aggregates are committed.

Read `HANDOFF.md`, then the checkpoint named by `state.json.last_checkpoint`.
