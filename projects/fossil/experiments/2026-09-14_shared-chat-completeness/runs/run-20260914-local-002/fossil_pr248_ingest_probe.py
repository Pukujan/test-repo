"""Run PR #248's shared-chat gate against the live Run 2 capture.

The public-share response is retained only as local ignored evidence.  This
probe commits the sanitized receipt and asks the PR implementation to promote
it.  An incomplete receipt must be rejected before any durable FOSSIL output
is written.
"""

from __future__ import annotations

import argparse
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


def _manifest(receipt: dict[str, Any], observed_at: str) -> dict[str, Any]:
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
                "source_path": "examples/shared-chat-ingestion/2026-08-14.json",
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
    completeness = json.loads((run_root / "completeness.json").read_text(encoding="utf-8"))
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = _receipt(completeness, captured_at)
    manifest = _manifest(receipt, captured_at)
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

    output_root = run_root / "artifacts" / "pr248-ingest-output"
    try:
        ingest_manifest(run_root / "manifest.json", output_root, repo_root=args.fossil_root)
    except ValueError as exc:
        outcome = "incomplete_capture_refused_before_writes"
        error_type = type(exc).__name__
        error = str(exc)
    else:
        raise RuntimeError("PR #248 unexpectedly accepted an incomplete capture")

    event_files = sorted((output_root / "events").rglob("evt_*.json")) if (output_root / "events").exists() else []
    conversation_files = sorted((output_root / "conversations").rglob("conv_*.json")) if (output_root / "conversations").exists() else []
    if event_files or conversation_files:
        raise RuntimeError("incomplete capture gate wrote durable output")

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
            "durable_event_files": [str(path.relative_to(run_root)) for path in event_files],
            "durable_conversation_files": [str(path.relative_to(run_root)) for path in conversation_files],
            "assertions": {
                "incomplete_capture_rejected": True,
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
            "command": "Run 2 public-share capture; graph decode; PR #248 ingest gate against incomplete receipt",
            "started_at": captured_at,
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "environment": {
                "lab_repo": "https://github.com/Pukujan/test-repo",
                "fossil_repo": f"https://github.com/Pukujan/fossil-core@{args.fossil_revision}",
                "local_host": "Windows PowerShell",
                "browser": None,
                "raw_capture_publicly_committed": False,
            },
            "outputs": [
                {"path": "source_capture.json", "kind": "capture-metadata"},
                {"path": "browser_surface.json", "kind": "surface-accounting"},
                {"path": "completeness.json", "kind": "completeness-receipt"},
                {"path": "capture_receipt.json", "kind": "fossil-capture-receipt"},
                {"path": "manifest.json", "kind": "fossil-ingest-manifest"},
                {"path": "fossil_ingest_probe.json", "kind": "fossil-pr248-gate-probe"},
            ],
            "notes": "The exposed mapping graph is fully accounted for, but the provider continuation returned HTTP 403. PR #248 rejected the incomplete receipt before writing events or conversations.",
        },
    )
    print(json.dumps({"result": outcome, "error": error, "upstream_revision": args.fossil_revision}, indent=2))


if __name__ == "__main__":
    main()
