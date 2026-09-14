# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `fossil-2026-09-14-shared-chat-completeness`  
**Status:** `blocked`

## Question

Can current FOSSIL capture the entire long shared ChatGPT conversation, prove completeness, ingest it durably, query its semantic history, and rebuild retrieval without losing meaning?

## Current focus

Validate PR #248's completeness gate against a fresh live Run 2 capture and preserve the fail-closed result.

## Last durable checkpoint

`checkpoints/0003-pr248-run2-fail-closed.md` — Fresh Run 2 exposed-node accounting completed; PR #248 refused promotion before durable writes because /continue remained blocked.

## Exact next action

Await exact-head hosted checks and review for PR #248; resume semantic query/lineage/rebuild only after a complete capture can be obtained or a provider continuation can be traversed.

## Blockers

- The public-share response exposes a /continue URL, but local HTTP probing returned HTTP 403 with a Cloudflare challenge; overall capture completeness is therefore incomplete.
- The pinned baseline lacked a shared-chat completeness field/gate; PR #248 now provides a candidate fail-closed gate, but it is not yet the pinned mainline.
- Downstream semantic query, lineage, and retrieval-rebuild checks are blocked because the baseline path emitted no full conversation lineage, claims, relations, or rebuildable retrieval projection.

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

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
