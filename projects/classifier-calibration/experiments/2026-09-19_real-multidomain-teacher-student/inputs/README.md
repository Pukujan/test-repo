# Inputs for the real multi-domain benchmark

Do not put arbitrary downloaded corpora here without checking license/public-repo suitability.

Before inference, create:

- `ontology.json` — frozen top-level schema and boundary rules;
- `source-lock.json` — exact public sources/revisions/licenses/acquisition instructions;
- `dataset_manifest.json` — stable sample IDs, source/document provenance, safe digests/counts;
- `split_manifest.json` — train/calibration/test/challenge IDs and source allocation;
- `gold_policy.md` — how independent gold was obtained and which ambiguous items were excluded/moved to challenge.

If source bytes cannot be redistributed, keep them local and record exact stable identifiers plus cryptographic digests.

Gold/test labels must never be copied into Qwen-visible prompts.
