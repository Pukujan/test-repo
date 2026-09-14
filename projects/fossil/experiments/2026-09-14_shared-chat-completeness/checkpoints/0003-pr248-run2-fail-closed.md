# Checkpoint 0003 — PR #248 Run 2 fail-closed validation

**Recorded:** 2026-09-14

## Exact inputs

- Experiment repository: `Pukujan/test-repo`
- Experiment baseline commit: `e325e3471dca8562e75afdefeaf0c2b237e4dfef`
- Share URL: `https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58`
- Candidate FOSSIL implementation: PR #248, exact head `4078cdd`
- Candidate branch: `issue-247-shared-chat-completeness`

## Run 2 capture

The fresh public-share response was retrieved with HTTP 200 and preserved locally outside Git. Its sanitized metadata is in `runs/run-20260914-local-002/source_capture.json`.

- response bytes: `1,513,860`
- response SHA-256: `9f9c4789c123938d7163a74ffe11cec4723e5194081eea0f5acaa97cfb12a141`
- exposed mapping nodes: `517`
- message-bearing nodes: `516`
- active-branch nodes: `517`
- unresolved child references: `0`
- continuation: `/continue` returned HTTP `403` with a provider challenge
- overall completeness: `incomplete`

The full machine-readable parser result, including all discovered node IDs, is `runs/run-20260914-local-002/completeness.json`. The raw response is deliberately not committed.

## Candidate gate result

`runs/run-20260914-local-002/fossil_pr248_ingest_probe.py` imported the exact PR checkout and invoked `scripts.ingest_shared_chat_reconstructions.ingest_manifest` with the Run 2 receipt. The result is recorded in `runs/run-20260914-local-002/fossil_ingest_probe.json`:

- result: `incomplete_capture_refused_before_writes`
- exception: `SharedChatCaptureError`
- durable event files: none
- durable conversation files: none

This proves the candidate gate does not silently promote a fully accounted *response graph* when the provider continuation remains unresolved. It does not prove complete ingestion, semantic query, lineage, or retrieval rebuild; those remain blocked by provider completeness.

## Local PR validation carried forward

At exact PR head `4078cdd`:

- focused completeness/fault/property/accounting tests: `41 passed`
- full suite: `744 passed, 1 skipped, 1 warning`
- Ruff on changed files: pass
- bounded scoped mutation lane: `513` generated mutants, `0` timeouts, `0` no-tests; dangerous predicate/graph/gate mutants were killed, with `57` residual equivalent/diagnostic survivors

Hosted exact-head checks and human review remain pending. No merge, production change, provider-policy change, or acceptance weakening occurred.
