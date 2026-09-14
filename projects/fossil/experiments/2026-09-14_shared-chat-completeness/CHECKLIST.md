# Checklist

> Generated from `checks.json`. Do not edit directly.

- [x] **CAP-001** — Reproduce the owner-observed partial long-chat acquisition behavior before changing FOSSIL. (`pass`)
  - surface-only undercount versus provider graph: runs/run-20260914-local-001/browser_surface.json
  - current path accepted bounded subset without completeness: runs/run-20260914-local-001/fossil_ingest_probe.json
- [x] **CAP-002** — Preserve exact retrieved shared-page/source bytes with digest and retrieval metadata. (`pass`)
  - local response digest and retrieval metadata: runs/run-20260914-local-001/source_capture.json
  - decoded response digest: runs/run-20260914-local-001/completeness.json
- [x] **CAP-003** — Produce machine-readable completeness evidence instead of inferring completeness from HTTP/render success. (`pass`)
  - machine-readable graph and continuation receipt: runs/run-20260914-local-001/completeness.json
- [x] **CAP-004** — Account for every exposed conversation message/node and identify active branch versus other exposed nodes. (`pass`)
  - 517-node mapping accounting: runs/run-20260914-local-001/completeness.json
- [x] **FID-001** — Record source fidelity separately from capture completeness. (`pass`)
  - fidelity/completeness separation: runs/run-20260914-local-001/source_capture.json
- [!] **ING-001** — Ingest the captured conversation into a fresh FOSSIL pack and inspect durable artifacts, snapshots, events, citations, claims and relations. (`fail`)
  - current baseline probe result: runs/run-20260914-local-001/fossil_ingest_probe.json
  - focused baseline tests: runs/run-20260914-local-001/focused_tests.txt
  - incomplete Run 2 refused before writes by PR #248 candidate: runs/run-20260914-local-002/fossil_ingest_probe.json
- [x] **GATE-001** — Reject an incomplete shared-chat capture before writing durable FOSSIL events or conversations. (`pass`)
  - PR #248 exact-head fail-closed probe: runs/run-20260914-local-002/fossil_ingest_probe.json
  - sanitized Run 2 receipt: runs/run-20260914-local-002/capture_receipt.json
  - candidate probe source: runs/run-20260914-local-002/fossil_pr248_ingest_probe.py
- [-] **QRY-001** — Query what FOSSIL currently understands about the product discussion and obtain grounded source references. (`blocked`)
  - no complete importer output to query: runs/run-20260914-local-001/fossil_ingest_probe.json
- [-] **LIN-001** — Query historical lineage showing how the interpretation moved from handoff framing to durable semantic memory/retrieval framing. (`blocked`)
  - no semantic lineage emitted by current path: runs/run-20260914-local-001/fossil_ingest_probe.json
- [-] **REB-001** — Destroy rebuildable retrieval/projection state, rebuild from durable FOSSIL state, and repeat the query suite without semantic loss. (`blocked`)
  - no rebuildable retrieval projection produced: runs/run-20260914-local-001/fossil_ingest_probe.json
- [x] **PORT-001** — Inventory the actual portable output produced today and identify missing consumer export/product surfaces from evidence rather than assumption. (`pass`)
  - portable output inventory: runs/run-20260914-local-001/fossil_ingest_probe.json
  - safe public evidence boundary: runs/run-20260914-local-001/source_capture.json
