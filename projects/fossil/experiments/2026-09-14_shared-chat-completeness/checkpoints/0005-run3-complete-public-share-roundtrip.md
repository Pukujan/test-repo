# Checkpoint 0005 — Run 3 complete public-share round trip

Recorded: 2026-09-14

## Exact inputs

- Experiment repository: `Pukujan/test-repo`
- Share URL: `https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58`
- FOSSIL main: `2b20dc8a7704d4bf93f2e00fa26e229ac529cba4`
- FOSSIL tree: `7c09f724e2a7698dcc34e5013a3abd143306a908`
- PR #248 was merged into that main commit; no PR reopening or FOSSIL code change was made for Run 3.

## Fresh Run 3 source proof

Run 2 remains immutable incomplete regression evidence: its `/continue` probe returned HTTP 403 with a provider challenge, and merged FOSSIL retained its exact bytes and refused complete promotion.

Run 3 fetched the supplied share URL again through a normal HTTP request and observed the share page in the in-app browser. The raw response remains local-only. Sanitized evidence is in `runs/run-20260914-local-003/`:

- HTTP status: `200`
- captured-at: `2026-09-14T20:13:51Z`
- byte count: `1,517,420`
- SHA-256: `9e77214c5be6f3958be8d9eceea2ecd568b877a86b4c7a33db578546b199eb4b`
- mapping nodes: `517`
- message-bearing nodes: `516`
- roles: `40 system`, `18 user`, `236 assistant`, `222 tool`
- `linear_conversation` count: `517`
- active parent-walk count: `517`
- linear IDs equal active parent-walk IDs in order: `true`
- current node is the final linear node and has no children: `true`
- unresolved child references: `0`
- non-active exposed nodes: `0`

The response also exposes `continue_conversation_url`. A normal plain GET returned HTTP 403 with a provider challenge; a direct in-app-browser GET returned a 404 route response. No CAPTCHA, Cloudflare, token, session, or anti-bot bypass was attempted. The URL is recorded separately as an optional user-action URL. The terminal classification is based on the embedded graph proof above, not on the final visible message and not on the failed probe.

## Merged FOSSIL round trip

The complete receipt was accepted by merged FOSSIL and bound to the exact source bytes:

- content-addressed artifact: `art_9e77214c5be6f3958be8d9eceea2ecd5`
- one capture receipt, one event, one conversation, and one lineage written
- `516` reconstructed messages and `516` reconstructed lineage nodes with `515` structural edges
- source artifact bytes, SHA-256, byte count, and receipt identity all matched
- complete conversation promotion was permitted

The downstream checks passed in the same run:

- QRY: deterministic message-term query returned grounded reconstructed hits for `FOSSIL` and `shared`.
- LIN: full structural lineage path and current-node citation resolved.
- REB: an isolated projection slot was destroyed, rebuilt from durable events, and compared by semantic snapshot; expected and candidate digests matched, query digests matched before/after, and citations remained present.

## Validation

- focused shared-chat tests: `49 passed`
- full merged-main suite: `754 passed, 1 skipped, 2 warnings`
- hosted PR #248 acceptance had already passed before merge, including bounded mutation assurance: `563` mutants, `480` killed, `83` reviewed survivors, `0` no-tests, `0` timeouts, score `85.26%`

## Remaining product gaps

This completes the experiment for the exact public-share representation, not an authenticated account export. Derived messages and lineage remain explicitly reconstructed. The current FOSSIL importer provides deterministic term query and structural lineage traversal, not a production semantic/vector retrieval service; the Run 3 lineage is source-order reconstruction rather than provider-native semantic claim extraction. Raw capture bytes and runtime markers remain local-only.
