"""Run PR #248's shared-chat gate against the live Run 2 capture.

The public-share response is retained only as local ignored evidence.  This
probe commits the sanitized receipt and asks the PR implementation to promote
it. An incomplete receipt must be retained as durable evidence while complete
conversation promotion is rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SHARE_URL = "https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58"
RUN_ID = "run-20260914-local-002"
EXPERIMENT_ID = "fossil-2026-09-14-shared-chat-completeness"
PACK_ID = "pack_f024177f89a5442db84171c3dd7f58e5"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _receipt(completeness: dict[str, Any], captured_at: str) -> dict[str, Any]:
    source = completeness["source_representation"]
    continuation_probe = completeness["continuation_probe"]
    node_ids = list(source["discovered_node_ids"])
    return {
        "schema_version": "fossil.shared-chat-capture-receipt.v1",
        "capture_id": "capture_run_20260914_local_002",
        "provider": "chatgpt-share",
        "adapter_version": "lab-run2-v1",
        "source": {
            "external_ref": SHARE_URL,
            "artifact_id": None,
            "sha256": source["response_sha256"],
            "byte_count": source["response_bytes"],
            "captured_at": captured_at,
        },
        "fidelity": "verbatim",
        "completeness": completeness["completeness"],
        "graph": {
            "discovered_node_count": len(node_ids),
            "accounted_node_count": len(node_ids),
            "message_node_count": len(source["message_node_ids"]),
            "discovered_node_ids": node_ids,
            "accounted_node_ids": node_ids,
            "message_node_ids": list(source["message_node_ids"]),
            "root_node_ids": list(source["root_nodes"]),
            "current_node_id": source["current_node"],
            "active_branch_node_ids": list(source["active_branch_node_ids"]),
            "non_active_exposed_node_ids": list(source["non_active_exposed_node_ids"]),
            "unresolved_refs": list(source["unresolved_refs"]),
        },
        "continuation": {
            "state": "unresolved",
            "mechanism": "/continue",
            "attempts": [
                {
                    "ref": continuation_probe["url"],
                    "outcome": "http_error",
                    "status_code": continuation_probe["http_status"],
                }
            ],
            "termination_reason": "http_error",
        },
    }


def _manifest(
    receipt: dict[str, Any], observed_at: str, *, source_path: str
) -> dict[str, Any]:
    return {
        "schema_version": "fossil.shared-chat-import.v1",
        "import_id": "shared-chat-completeness-run-20260914-local-002",
        "pack_id": PACK_ID,
        "observed_at": observed_at,
        "actor": {
            "actor_id": "shared-chat-completeness-runner",
            "harness_version": "shared-chat-completeness-run2-v1",
            "skill_id": "skill_research-ingestion",
            "skill_version": "1.0.0",
        },
        "conversations": [
            {
                "conversation_id": "conv_shared_chat_completeness_run_20260914_local_002",
                "title": "Productizing Fossil Core — shared-chat completeness Run 2",
                "external_ref": SHARE_URL,
                "source_path": source_path,
                "source_label": "live public shared-chat Run 2; promotion intentionally gated",
                "reconstruction_basis_refs": [SHARE_URL],
                "messages": [],
                "lineage": {
                    "lineage_id": "lin_shared_chat_completeness_run_20260914_local_002",
                    "nodes": [],
                    "edges": [],
                    "current_conclusion_refs": [],
                },
                "capture_receipt": receipt,
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fossil-root", type=Path, required=True)
    parser.add_argument("--fossil-revision", default="4078cdd")
    args = parser.parse_args()

    run_root = Path(__file__).resolve().parent
    raw_source_path = run_root / "artifacts" / "source.response"
    if not raw_source_path.exists():
        raise FileNotFoundError(raw_source_path)
    completeness = json.loads((run_root / "completeness.json").read_text(encoding="utf-8"))
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = _receipt(completeness, captured_at)
    manifest = _manifest(receipt, captured_at, source_path="artifacts/source.response")
    _write_json(run_root / "capture_receipt.json", receipt)
    _write_json(run_root / "manifest.json", manifest)

    source = completeness["source_representation"]
    continuation = completeness["continuation_probe"]
    _write_json(
        run_root / "source_capture.json",
        {
            "schema_version": "lab.source-capture.v1",
            "run_id": RUN_ID,
            "external_ref": SHARE_URL,
            "http_status": 200,
            "response_bytes": source["response_bytes"],
            "response_sha256": source["response_sha256"],
            "fidelity": "verbatim",
            "completeness": completeness["completeness"],
            "raw_capture_publicly_committed": False,
            "continuation_probe": {
                "url": continuation["url"],
                "http_status": continuation["http_status"],
                "outcome": continuation["outcome"],
            },
        },
    )
    _write_json(
        run_root / "browser_surface.json",
        {
            "schema_version": "lab.surface-accounting.v1",
            "run_id": RUN_ID,
            "surface": "raw_http_capture",
            "note": "Run 2 used the raw public-share response and graph decoder; no browser accessibility surface was used as a completeness oracle.",
            "mapping_node_count": source["mapping_node_count"],
            "message_bearing_node_count": source["message_bearing_node_count"],
        },
    )

    # Put the checked-out PR package ahead of any globally installed fossil_core
    # so this probe cannot accidentally exercise another checkout.
    sys.path.insert(0, str(args.fossil_root / "src"))
    sys.path.insert(0, str(args.fossil_root))
    from scripts.ingest_shared_chat_reconstructions import ingest_manifest
    from fossil_core.artifact_store import ArtifactStore

    output_root = run_root / "artifacts" / "pr248-ingest-output"
    runtime_manifest_path = run_root / "artifacts" / ".manifest.runtime.json"
    runtime_manifest = _manifest(
        receipt, captured_at, source_path=str(raw_source_path)
    )
    _write_json(runtime_manifest_path, runtime_manifest)
    try:
        ingest_manifest(runtime_manifest_path, output_root, repo_root=args.fossil_root)
    except ValueError as exc:
        outcome = "incomplete_capture_preserved_and_promotion_refused"
        error_type = type(exc).__name__
        error = str(exc)
    else:
        raise RuntimeError("PR #248 unexpectedly accepted an incomplete capture")
    finally:
        runtime_manifest_path.unlink(missing_ok=True)

    event_files = sorted((output_root / "events").rglob("evt_*.json")) if (output_root / "events").exists() else []
    conversation_files = sorted((output_root / "conversations").rglob("conv_*.json")) if (output_root / "conversations").exists() else []
    if event_files or conversation_files:
        raise RuntimeError("incomplete capture gate wrote durable output")
    receipt_files = sorted((output_root / "capture-receipts").glob("*.json"))
    if len(receipt_files) != 1:
        raise RuntimeError(f"expected one durable capture receipt, found {len(receipt_files)}")
    stored_receipt = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    retained_artifact_id = stored_receipt["source"]["artifact_id"]
    retained_bytes = ArtifactStore(output_root / "artifacts").read_bytes(retained_artifact_id)
    raw_bytes = raw_source_path.read_bytes()
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if retained_bytes != raw_bytes:
        raise RuntimeError("durable capture artifact does not match exact Run 2 bytes")
    if stored_receipt["source"]["sha256"] != raw_sha256:
        raise RuntimeError("durable capture receipt sha256 is not bound to Run 2 bytes")
    if stored_receipt["source"]["byte_count"] != len(raw_bytes):
        raise RuntimeError("durable capture receipt byte_count is not bound to Run 2 bytes")
    if retained_artifact_id != f"art_{raw_sha256[:32]}":
        raise RuntimeError("durable capture artifact identity is not content-addressed")

    # Keep a public, sanitized copy of the bound receipt. The raw capture and
    # FOSSIL artifact bytes remain local-only, while the receipt metadata makes
    # the exact source binding independently reviewable from the lab repo.
    public_receipt_path = run_root / "fossil_capture_receipt_bound.json"
    _write_json(public_receipt_path, stored_receipt)

    _write_json(
        run_root / "fossil_ingest_probe.json",
        {
            "schema_version": "lab.fossil-ingest-probe.v1",
            "run_id": RUN_ID,
            "experiment_id": EXPERIMENT_ID,
            "upstream_revision": args.fossil_revision,
            "result": outcome,
            "error_type": error_type,
            "error": error,
            "receipt_completeness": receipt["completeness"],
            "continuation": receipt["continuation"],
            "durable_capture_receipt_files": [str(public_receipt_path.relative_to(run_root))],
            "durable_event_files": [str(path.relative_to(run_root)) for path in event_files],
            "durable_conversation_files": [str(path.relative_to(run_root)) for path in conversation_files],
            "retained_artifact_id": retained_artifact_id,
            "retained_byte_count": len(retained_bytes),
            "retained_sha256": raw_sha256,
            "assertions": {
                "incomplete_capture_rejected": True,
                "incomplete_evidence_preserved": True,
                "retained_bytes_match_capture": True,
                "receipt_source_binding_matches_capture": True,
                "no_events_written": not event_files,
                "no_conversations_written": not conversation_files,
            },
        },
    )
    _write_json(
        run_root / "run.json",
        {
            "schema_version": "lab.run.v1",
            "run_id": RUN_ID,
            "experiment_id": EXPERIMENT_ID,
            "status": "pass",
            "upstream_revision": args.fossil_revision,
            "command": "Run 2 public-share capture; graph decode; PR #248 evidence preservation and promotion gate",
            "started_at": captured_at,
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "environment": {
                "lab_repo": "https://github.com/Pukujan/test-repo",
                "fossil_repo": f"https://github.com/Pukujan/fossil-core@{args.fossil_revision}",
                "local_host": "WSL Ubuntu on Windows workspace",
                "browser": None,
                "raw_capture_publicly_committed": False,
            },
            "outputs": [
                {"path": "source_capture.json", "kind": "capture-metadata"},
                {"path": "browser_surface.json", "kind": "surface-accounting"},
                {"path": "completeness.json", "kind": "completeness-receipt"},
                {"path": "capture_receipt.json", "kind": "fossil-capture-receipt"},
                {"path": "manifest.json", "kind": "fossil-ingest-manifest"},
                {"path": "fossil_capture_receipt_bound.json", "kind": "bound-fossil-capture-receipt"},
                {"path": "fossil_ingest_probe.json", "kind": "fossil-pr248-gate-probe"},
            ],
            "notes": "The exposed mapping graph is fully accounted for, but the provider continuation returned HTTP 403. PR #248 durably retained the exact source artifact and bound receipt, then rejected complete-conversation promotion before writing events or conversations.",
        },
    )
    print(json.dumps({"result": outcome, "error": error, "upstream_revision": args.fossil_revision}, indent=2))


if __name__ == "__main__":
    main()
