# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `fossil-2026-09-14-shared-chat-completeness`  
**Status:** `completed`

## Question

Can current FOSSIL capture the entire long shared ChatGPT conversation, prove completeness, ingest it durably, query its semantic history, and rebuild retrieval without losing meaning?

## Current focus

Run 3 completed the public-share representation round trip against merged FOSSIL main; residual product gaps are recorded as scope, not hidden as completeness.

## Last durable checkpoint

`checkpoints/0005-run3-complete-public-share-roundtrip.md` — Run 3 proved the exposed public-share graph terminal, ingested the exact bytes through merged FOSSIL, and passed deterministic QRY/LIN/REB with product gaps recorded.

## Exact next action

Independent review of the scoped Run 3 conclusion. Start a new additive run only if an authenticated account export, provider continuation contract, or production semantic retrieval surface is required.

## Blockers

- The public-share representation is not an authenticated account export; the result is scoped to all data exposed by this exact share response.
- Derived message and lineage records are explicitly reconstructed, and the current run's lineage is structural source order rather than provider-native semantic claim extraction.
- Raw source bytes and runtime markers remain local-only, so independent acquisition replay requires a new legitimate source capture.

## Important findings

- Owner observed that long shared chats can be only partially ingested until a local agent is explicitly told to inspect the whole conversation.
- fossil-core issue #247 now tracks the requirement that complete ingestion must be proven mechanically rather than inferred from a successful first fetch.
- The captured response body is verbatim evidence for the public-share representation: 1,430,356 bytes, SHA-256 a07c069b6a23678bdf989f22225c031c50deecd11c2ae1f7cf938100bede39e5.
- The response graph contains 517 exposed nodes and 516 unique message-bearing nodes: 40 system, 18 user, 236 assistant, and 222 tool messages; one root/current traversal covers all exposed mapping nodes with zero unresolved child references.
- The local browser's initial accessible surface exposed 18 prompt controls, demonstrating why a surface-only importer cannot account for the provider graph.
- The current FOSSIL baseline accepted a bounded verbatim subset without knowing capture completeness; the focused conversation tests passed 7/7 under WSL Ubuntu 22.04, while the broader 40-test baseline had 39 passes and one unrelated date-format failure.
- The exact current FOSSIL artifact publisher fails on this Windows filesystem with WinError 1 from os.link; the baseline probe completed under WSL without changing upstream code.
- Run 2 retrieved 1,513,860 bytes with SHA-256 9f9c4789c123938d7163a74ffe11cec4723e5194081eea0f5acaa97cfb12a141; the exposed graph again contained 517 mapping nodes and 516 message-bearing nodes, while /continue returned HTTP 403.
- Against PR #248 exact head 4078cdd, the sanitized incomplete receipt was rejected as SharedChatCaptureError before any durable event or conversation file was written; this is the expected fail-closed result.
- Against PR #248 exact head a73ae7c00c6e7b4c61a7fede8639727f10a08c23, the exact Run 2 bytes were retained as art_9f9c4789c123938d7163a74ffe11cec4 with a bound SHA-256/byte_count receipt, then complete-conversation promotion was refused because /continue remained unresolved.
- The dedicated shared-chat mutation lane generated 563 mutants: 480 killed, 83 reviewed survivors, zero no-tests, zero timeouts, score 85.26%, and passed its explicit 84%/90-survivor/zero-no-tests gate.
- All hosted exact-head checks passed on a73ae7c00c6e7b4c61a7fede8639727f10a08c23, including dedicated mutation run 34876757413; PR #248 then merged into FOSSIL main at 2b20dc8a7704d4bf93f2e00fa26e229ac529cba4.
- Run 3 fresh response: 1,517,420 bytes, SHA-256 9e77214c5be6f3958be8d9eceea2ecd568b877a86b4c7a33db578546b199eb4b; 517 mapping nodes, 516 messages, exact linear/active ID equality, current node terminal, zero unresolved child references, and zero non-active exposed nodes.
- Run 3 complete promotion wrote one content-addressed artifact art_9e77214c5be6f3958be8d9eceea2ecd5, one event, one conversation, one lineage, 516 reconstructed messages, and 516 reconstructed lineage nodes; exact-byte binding, QRY, LIN, and REB all passed.
- The /continue field was recorded separately: plain GET returned 403 with a provider challenge and browser direct GET returned 404; no bypass was attempted. The full embedded graph was classified terminal because its linear IDs exactly match the active parent walk and end at current_node with no child obligations.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
