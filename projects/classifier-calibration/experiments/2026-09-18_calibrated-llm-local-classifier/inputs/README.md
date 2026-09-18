# Inputs

This directory stores only safe experiment input manifests or sanitized fixtures.

Do **not** commit the private/domain corpus itself unless it is explicitly safe for this public repository.

For local-only datasets, record a manifest containing stable dataset/version identifiers, row/split digests, label schema, counts, and enough provenance to reproduce the run without exposing private source text.

## Run 1 fixture

- `fixtures/synthetic_topics_v1.jsonl` — public-safe synthetic 4-class topic texts (400 rows).
- `fixtures/dataset_manifest.json` / `fixtures/split_manifest.json` — digests, label schema, frozen split IDs.
