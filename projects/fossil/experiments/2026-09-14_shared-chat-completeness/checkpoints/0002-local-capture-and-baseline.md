# Checkpoint 0002 — local capture and baseline characterization

**Checkpoint ID:** `cp-0002`
**Actor:** Codex local
**Date:** 2026-09-14

## State entering checkpoint

Checkpoint `cp-0001` required a local acquisition of the supplied public ChatGPT share, exact upstream verification, and a current FOSSIL ingestion attempt before any implementation change.

## Exact refs

- Lab repository: `Pukujan/test-repo` main at `ba9fa48113d4e888a8df4e66eb1cc0441491ae30`.
- FOSSIL baseline: `Pukujan/fossil-core` main at `c080572905238d9d326401f85e66d04a84832014`.
- Focused defect: `Pukujan/fossil-core#247`.

## Work completed

- Verified the requested experiment exists in `Pukujan/test-repo` and cloned it locally.
- Fetched the supplied public share locally with HTTP 200 and preserved the exact response body locally at `runs/run-20260914-local-001/artifacts/source.response`.
- Recorded the response as `verbatim` fidelity but `incomplete` capture completeness. The body is 1,430,356 bytes with SHA-256 `a07c069b6a23678bdf989f22225c031c50deecd11c2ae1f7cf938100bede39e5`.
- Decoded the React Router streamed representation and mechanically accounted for the exposed graph: 517 mapping nodes, 516 unique message-bearing nodes, 517 linear-conversation entries, one root, current node `45bb61e6-dbbd-4563-a71e-8ca27014845b`, 516 active-branch messages, zero non-active exposed nodes, and zero unresolved child references.
- Recorded the exposed role counts: 40 system, 18 user, 236 assistant, and 222 tool messages.
- Observed the local browser surface separately: 18 prompt controls. This is not treated as completeness evidence; it is the reproducer for the surface-only undercount hazard.
- Probed the exposed `/continue` URL. It returned HTTP 403 with a Cloudflare challenge, so the provider continuation is unresolved and the capture cannot be called complete.
- Ran the current FOSSIL path without changing `fossil-core`. Under WSL Ubuntu 22.04 it accepted a manually bounded verbatim subset and emitted one artifact, one source snapshot, one citation, one conversation envelope, and one `conversation.ingested` event, but no completeness field/gate, lineage, claims, or relations.
- Focused baseline tests passed 7/7: `tests/test_shared_chat_ingestion.py` and `tests/test_conversation_lineage.py`. A broader 40-test baseline had 39 passes and one existing date-format validation failure in `test_source_citation_properties.py`.
- On the Windows host, the exact FOSSIL artifact publisher failed before ingestion with `WinError 1` from `os.link`; WSL was used only to execute the unchanged baseline.

## Findings

The experiment reproduces the defect class: a first-pass surface can expose only 18 prompt controls while the same public-share response contains 516 message-bearing provider nodes. The current FOSSIL path can durably accept a bounded verbatim subset without knowing that the acquisition is incomplete. Exact bytes and provenance therefore do not by themselves prove complete capture.

The exposed mapping graph is fully accounted for, but the provider continuation challenge prevents a stronger claim than `incomplete`. This is the honest result required by the experiment rules.

## Checks updated

- Pass: CAP-001, CAP-002, CAP-003, CAP-004, FID-001, PORT-001.
- Fail: ING-001, because the current baseline has no completeness-aware shared-chat importer and does not produce full semantic ingestion.
- Blocked: QRY-001, LIN-001, REB-001, because the baseline produced no full durable semantic corpus or rebuildable retrieval projection.

Evidence is recorded under `runs/run-20260914-local-001/`. The raw body is intentionally local-only and ignored by Git; public files retain only its digest, safe accounting, and evidence references.

## Not yet tested

- Full durable ingestion of the 516 exposed messages into a completeness-aware FOSSIL conversation envelope.
- Grounded semantic query and historical lineage over the live capture.
- Destruction/rebuild of a retrieval projection from the live capture.
- A consumer-facing portable export beyond the current raw-response digest, source snapshot, citation, envelope, and event probe.

## Exact next action

Do not patch `fossil-core` in this checkpoint. Resume only after either the exposed provider continuation can be traversed or a separately approved completeness-aware importer implementation exists; then rerun the same source accounting and continue the blocked semantic/query/rebuild checks as a new run.

## Do not redo

Do not recapture or overwrite the local raw response unless a new retrieval is intentionally recorded as another additive run. Do not treat the current mapping accounting as proof of an authenticated account export or as proof that the blocked `/continue` path contains no additional exposed material.
