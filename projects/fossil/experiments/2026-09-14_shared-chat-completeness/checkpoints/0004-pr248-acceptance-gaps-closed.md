# Checkpoint 0004 — PR #248 acceptance gaps closed and Run 2 preserved

**Recorded:** 2026-09-14

## Exact inputs

- Experiment repository: `Pukujan/test-repo`
- Share URL: `https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58`
- Candidate FOSSIL implementation: PR #248, local exact head `a73ae7c00c6e7b4c61a7fede8639727f10a08c23`
- Candidate branch: `issue-247-shared-chat-completeness`

## Run 2 capture

The fresh public-share response was retrieved with HTTP 200 and preserved locally outside Git. Its sanitized metadata is in `runs/run-20260914-local-002/source_capture.json`; the raw response remains deliberately uncommitted.

- response bytes: `1,513,860`
- response SHA-256: `9f9c4789c123938d7163a74ffe11cec4723e5194081eea0f5acaa97cfb12a141`
- exposed mapping nodes: `517`
- message-bearing nodes: `516`
- active-branch nodes: `517`
- unresolved child references: `0`
- continuation: `/continue` returned HTTP `403` with a provider challenge
- overall completeness: `incomplete`

## Acceptance result

The exact candidate checkout was run against the exact Run 2 bytes. The result is recorded in `runs/run-20260914-local-002/fossil_ingest_probe.json`:

- result: `incomplete_capture_preserved_and_promotion_refused`
- exception: `SharedChatCaptureError`
- retained artifact: `art_9f9c4789c123938d7163a74ffe11cec4`
- retained byte count: `1,513,860`
- retained SHA-256: `9f9c4789c123938d7163a74ffe11cec4723e5194081eea0f5acaa97cfb12a141`
- bound receipt: `fossil_capture_receipt_bound.json`
- durable event files: none
- durable conversation files: none

This closes the three bounded acceptance gaps: source receipt SHA-256/byte_count/artifact identity are checked against the exact bytes before promotion; incomplete evidence and its receipt are durably retained while complete-conversation promotion is refused; and a dedicated bounded mutation workflow is committed. The raw capture and FOSSIL artifact bytes remain local-only, with their exact digest and receipt metadata preserved in the lab evidence.

## Local PR validation

- focused shared-chat suite: `53 passed`
- full suite: `754 passed, 1 skipped, 2 warnings`
- Ruff on changed files: pass
- bounded mutation lane: `563` total, `480` killed, `83` survived, `0` no-tests, `0` timeouts, score `85.26%`
- mutation gate: minimum score `84%`, maximum survivors `90`, maximum no-tests `0`; pass

The mounted Windows filesystem produced the known hardlink `errno 1` during the first probe attempt. The same code and bytes were rerun on WSL ext4 without an upstream workaround, and all exact-byte assertions passed.

Hosted exact-head checks and independent review are still pending. No merge, production change, provider-policy change, or acceptance weakening occurred.
