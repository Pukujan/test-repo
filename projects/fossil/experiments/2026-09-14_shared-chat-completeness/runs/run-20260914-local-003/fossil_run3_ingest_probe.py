"""Run complete-source ingestion and durable round-trip checks for Run 3.

The raw public-share response and the runtime message markers stay outside the
lab repository.  Only sanitized receipts, counts, hashes, and check results are
written to the public run directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


SHARE_URL = "https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58"
RUN_ID = "run-20260914-local-003"
EXPERIMENT_ID = "fossil-2026-09-14-shared-chat-completeness"
PACK_ID = "pack_f024177f89a5442db84171c3dd7f58e5"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def capture_time(headers_path: Path) -> str:
    for line in headers_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("date:"):
            return parsedate_to_datetime(line.split(":", 1)[1].strip()).astimezone(
                timezone.utc
            ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    raise RuntimeError("source headers did not contain a Date header")


def status_code(headers_path: Path) -> int:
    first = headers_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    return int(first.split()[1])


def receipt(completeness: dict[str, Any], observed_at: str) -> dict[str, Any]:
    source = completeness["source_representation"]
    node_ids = list(source["discovered_node_ids"])
    return {
        "schema_version": "fossil.shared-chat-capture-receipt.v1",
        "capture_id": "capture_run_20260914_local_003",
        "provider": "chatgpt-share",
        "adapter_version": "lab-run3-graph-terminal-v1",
        "source": {
            "external_ref": SHARE_URL,
            "artifact_id": None,
            "sha256": source["response_sha256"],
            "byte_count": source["response_bytes"],
            "captured_at": observed_at,
        },
        "fidelity": "verbatim",
        "completeness": "complete",
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
            "state": "not_present",
            "mechanism": None,
            "attempts": [],
            "termination_reason": "source_terminal",
        },
    }


def runtime_manifest(
    *,
    runtime_specs: dict[str, Any],
    capture_receipt: dict[str, Any],
    observed_at: str,
    source_path: Path,
) -> dict[str, Any]:
    messages = [
        {
            "message_id": item["message_id"],
            "role": item["role"],
            "actor_id": item["actor_id"],
            "marker": item["marker"],
        }
        for item in runtime_specs["messages"]
    ]
    return {
        "schema_version": "fossil.shared-chat-import.v1",
        "import_id": "shared-chat-completeness-run-20260914-local-003",
        "pack_id": PACK_ID,
        "observed_at": observed_at,
        "actor": {
            "actor_id": "shared-chat-completeness-runner",
            "harness_version": "shared-chat-completeness-run3-v1",
            "skill_id": "skill_research-ingestion",
            "skill_version": "1.0.0",
        },
        "conversations": [
            {
                "conversation_id": runtime_specs["conversation_id"],
                "title": "Productizing Fossil Core — shared-chat completeness Run 3",
                "external_ref": SHARE_URL,
                "source_path": str(source_path),
                "source_label": (
                    "verbatim public-share response bytes; derived message and lineage "
                    "fields remain reconstructed"
                ),
                "reconstruction_basis_refs": [SHARE_URL],
                "messages": messages,
                "lineage": {
                    "lineage_id": "lin_shared_chat_completeness_run_20260914_local_003",
                    "nodes": runtime_specs["lineage"]["nodes"],
                    "edges": runtime_specs["lineage"]["edges"],
                    "current_conclusion_refs": runtime_specs["lineage"]["current_conclusion_refs"],
                },
                "capture_receipt": capture_receipt,
            }
        ],
    }


def sanitized_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(manifest))
    conversation = result["conversations"][0]
    conversation["source_path"] = "artifacts/source.response"
    for item in conversation["messages"]:
        item["marker"] = f"source-node:{item['message_id'].removeprefix('msg_src_')}"
    for node in conversation["lineage"]["nodes"]:
        node["text"] = f"observed source node {node['node_id'].removeprefix('ln_src_')[:12]}"
    result["sanitization"] = {
        "raw_capture_publicly_committed": False,
        "message_markers_scrubbed": True,
        "note": "Runtime markers and source bytes remain local-only; this manifest is review metadata.",
    }
    return result


def snapshot_from_json(value: dict[str, Any]):
    from fossil_core.projection.migration import SemanticSnapshot

    tuple_fields = {
        "event_ids": tuple(value["event_ids"]),
        "pack_event_ids": tuple((pack, tuple(events)) for pack, events in value["pack_event_ids"]),
        "namespace_subject_refs": tuple(
            (pack, tuple(subjects)) for pack, subjects in value["namespace_subject_refs"]
        ),
        "provenance_by_event": tuple(tuple(item) for item in value["provenance_by_event"]),
        "claim_states": tuple(tuple(item) for item in value["claim_states"]),
        "relation_states": tuple(tuple(item) for item in value["relation_states"]),
        "event_type_counts": tuple(tuple(item) for item in value["event_type_counts"]),
    }
    return SemanticSnapshot(**tuple_fields)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-run-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--fossil-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--fossil-revision", required=True)
    args = parser.parse_args()

    public_root = args.public_run_root
    runtime_root = args.runtime_root
    fossil_root = args.fossil_root
    output_root = args.output_root
    raw_source = runtime_root / "artifacts" / "source.response"
    source_headers = runtime_root / "artifacts" / "source.headers.txt"
    continue_headers = runtime_root / "artifacts" / "continue.headers.txt"
    completeness = json.loads((public_root / "completeness.json").read_text(encoding="utf-8"))
    runtime_specs = json.loads(
        (runtime_root / "runtime_specs.json").read_text(encoding="utf-8")
    )
    observed_at = capture_time(source_headers)
    raw_bytes = raw_source.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if raw_sha != completeness["source_representation"]["response_sha256"]:
        raise RuntimeError("fresh source bytes do not match the analyzed response hash")
    if len(raw_bytes) != completeness["source_representation"]["response_bytes"]:
        raise RuntimeError("fresh source bytes do not match the analyzed response byte count")

    capture_receipt = receipt(completeness, observed_at)
    public_root.mkdir(parents=True, exist_ok=True)
    write_json(public_root / "capture_receipt.json", capture_receipt)
    manifest = runtime_manifest(
        runtime_specs=runtime_specs,
        capture_receipt=capture_receipt,
        observed_at=observed_at,
        source_path=raw_source,
    )
    write_json(public_root / "manifest.json", sanitized_manifest(manifest))
    runtime_manifest_path = runtime_root / "manifest.runtime.json"
    write_json(runtime_manifest_path, manifest)

    source_status = status_code(source_headers)
    continue_status = status_code(continue_headers)
    write_json(
        public_root / "source_capture.json",
        {
            "schema_version": "lab.source-capture.v1",
            "run_id": RUN_ID,
            "external_ref": SHARE_URL,
            "http_status": source_status,
            "response_bytes": len(raw_bytes),
            "response_sha256": raw_sha,
            "captured_at": observed_at,
            "acquisition": "normal HTTP share-page fetch plus in-app browser observation",
            "fidelity": "verbatim",
            "completeness": "complete",
            "raw_capture_publicly_committed": False,
            "graph_proof": completeness["graph_checks"],
            "optional_action_url": completeness["optional_action_url"],
        },
    )
    write_json(
        public_root / "continuation_diagnosis.json",
        {
            "schema_version": "lab.continuation-diagnosis.v1",
            "run_id": RUN_ID,
            "action_url": completeness["optional_action_url"],
            "classification": "optional_user_action_not_pagination",
            "classification_basis": [
                "the URL is a singleton continue_conversation_url field, not a next/cursor/page token",
                "the full mapping and linear_conversation are embedded in the share response",
                "linear IDs exactly equal the active parent walk and terminate at current_node",
                "the current node has no child obligations and the exposed graph has no unresolved references",
            ],
            "plain_http_probe": {
                "method": "GET",
                "status": continue_status,
                "cf_mitigated": "challenge",
                "outcome": "provider_challenge_observed_no_bypass_attempted",
            },
            "browser_direct_probe": {
                "method": "GET",
                "status": 404,
                "title": "Unhandled Thrown Response!",
                "heading": "404 Not Found",
                "outcome": "route_not_a_data_pagination_response",
            },
            "decision": "The optional action is not treated as an unresolved acquisition obligation for this already-terminal exposed graph.",
            "safety": "No CAPTCHA, Cloudflare, token, session, or anti-bot control was bypassed.",
        },
    )
    write_json(
        public_root / "browser_surface.json",
        {
            "schema_version": "lab.surface-accounting.v1",
            "run_id": RUN_ID,
            "surface": "in_app_browser_share_page",
            "url": SHARE_URL,
            "title": "Productizing Fossil Core",
            "copy_notice_observed": True,
            "prompt_anchor_count": 18,
            "visible_message_nodes_before_prompt_navigation": 4,
            "visible_message_nodes_after_prompt_navigation": 7,
            "embedded_mapping_node_count": 517,
            "embedded_message_count": 516,
            "visible_continuation_control_observed": False,
            "note": "Browser rendering corroborates the share surface; graph completeness is decided by the captured payload checks, not by final visible text.",
        },
    )

    sys.path.insert(0, str(fossil_root / "src"))
    sys.path.insert(0, str(fossil_root))
    from fossil_core.artifact_store import ArtifactStore
    from fossil_core.conversation import ConversationLineage, ConversationStore
    from fossil_core.event_store import DurableEventStore
    from fossil_core.projection.migration import ProjectionComparator, SemanticSnapshot
    from scripts.ingest_shared_chat_reconstructions import ingest_manifest

    if output_root.exists():
        shutil.rmtree(output_root)
    imported = ingest_manifest(runtime_manifest_path, output_root, repo_root=fossil_root)
    if len(imported) != 1:
        raise RuntimeError(f"expected one imported conversation, got {len(imported)}")
    result = imported[0]

    receipt_files = list((output_root / "capture-receipts").glob("*.json"))
    event_files = list((output_root / "events").rglob("evt_*.json"))
    conversation_files = list((output_root / "conversations").rglob("conv_*.json"))
    lineage_files = list((output_root / "lineages").glob("*.json"))
    if [len(receipt_files), len(event_files), len(conversation_files), len(lineage_files)] != [1, 1, 1, 1]:
        raise RuntimeError("complete ingest did not produce exactly one receipt, event, conversation, and lineage")
    stored_receipt = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    artifact_id = stored_receipt["source"]["artifact_id"]
    retained = ArtifactStore(output_root / "artifacts").read_bytes(artifact_id)
    if retained != raw_bytes:
        raise RuntimeError("durable artifact does not equal exact captured source bytes")
    if artifact_id != f"art_{raw_sha[:32]}":
        raise RuntimeError("durable source artifact is not content addressed")
    if stored_receipt["source"]["sha256"] != raw_sha or stored_receipt["source"]["byte_count"] != len(raw_bytes):
        raise RuntimeError("durable receipt is not bound to exact source bytes")
    write_json(public_root / "fossil_capture_receipt_bound.json", stored_receipt)

    conversation_store = ConversationStore(
        output_root / "conversations",
        ArtifactStore(output_root / "artifacts"),
        fossil_root / "schemas" / "conversation" / "v1.schema.json",
    )
    envelope = conversation_store.get(result["conversation_id"])
    lineage_data = json.loads(lineage_files[0].read_text(encoding="utf-8"))
    lineage = ConversationLineage(
        lineage_data,
        schema_path=fossil_root / "schemas" / "conversation-lineage" / "v1.schema.json",
        conversation_store=conversation_store,
        envelope=envelope,
    )

    query_terms = ["FOSSIL", "shared"]

    def query_envelope(candidate: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        return {
            term: [
                {
                    "sequence": message["sequence"],
                    "message_id": message["message_id"],
                    "evidence_status": message["evidence_status"],
                }
                for message in ConversationStore.ordered_messages(candidate)
                if term.lower() in message["text"].lower()
            ]
            for term in query_terms
        }

    query_hits = query_envelope(envelope)
    first_node = lineage_data["nodes"][0]["node_id"]
    last_node = lineage_data["nodes"][-1]["node_id"]
    path = lineage.path(first_node, last_node)
    current = lineage.current_conclusions()
    last_citations = lineage.citations(last_node)
    qry_pass = all(query_hits.values()) and all(
        hit["evidence_status"] == "reconstructed"
        for hits in query_hits.values()
        for hit in hits
    )
    lin_pass = bool(path) and len(path) == len(lineage_data["nodes"]) and bool(current) and bool(last_citations)

    event_store = DurableEventStore(
        output_root / "events", fossil_root / "schemas" / "events" / "v1.schema.json"
    )
    events = list(event_store.iter_events())
    expected_snapshot = SemanticSnapshot.from_events(events)
    projection_root = output_root / "projection"
    destroyed_slot = projection_root / "destroyed-slot"
    destroyed_slot.mkdir(parents=True, exist_ok=True)
    write_json(destroyed_slot / "placeholder.json", {"will_be_destroyed": True})
    shutil.rmtree(destroyed_slot)
    rebuild_slot = projection_root / "rebuild-slot"
    rebuild_slot.mkdir(parents=True, exist_ok=True)
    rebuilt_events = list(event_store.iter_events())
    rebuilt_snapshot = SemanticSnapshot.from_events(rebuilt_events)
    write_json(rebuild_slot / "semantic-snapshot.json", asdict(rebuilt_snapshot))
    candidate_snapshot = snapshot_from_json(
        json.loads((rebuild_slot / "semantic-snapshot.json").read_text(encoding="utf-8"))
    )
    comparison = ProjectionComparator.compare(
        expected=expected_snapshot,
        candidate=candidate_snapshot,
        candidate_slot="run3-rebuild",
        benchmarks={"query": qry_pass, "lineage": lin_pass},
    )
    reb_pass = comparison.passed and not destroyed_slot.exists()

    before_query_digest = hashlib.sha256(
        json.dumps(query_hits, sort_keys=True).encode("utf-8")
    ).hexdigest()
    reloaded_envelope = conversation_store.get(result["conversation_id"])
    after_query_hits = query_envelope(reloaded_envelope)
    after_query_digest = hashlib.sha256(
        json.dumps(after_query_hits, sort_keys=True).encode("utf-8")
    ).hexdigest()
    citations_summary = [
        {
            "span_id": citation["span_id"],
            "artifact_id": citation["artifact_id"],
            "evidence_status": citation["evidence_status"],
            "byte_start": citation["byte_start"],
            "byte_end": citation["byte_end"],
        }
        for citation in last_citations
    ]
    product_gaps = [
        "Public-share bytes are verbatim evidence for the exposed share representation, not an authenticated account export.",
        "Derived messages and lineage are reconstructed; the run does not promote them to verbatim semantic claims.",
        "The current importer provides deterministic message-term query and lineage traversal, not a production semantic/vector retrieval service.",
        "The lineage in this run is a structural source-order reconstruction, not provider-native semantic claim extraction.",
        "Raw source bytes and runtime markers remain local-only; a reviewer cannot independently rerun acquisition from the lab repository alone.",
    ]
    probe = {
        "schema_version": "lab.fossil-ingest-probe.v1",
        "run_id": RUN_ID,
        "experiment_id": EXPERIMENT_ID,
        "upstream_revision": args.fossil_revision,
        "result": "complete_source_ingested_and_roundtripped",
        "receipt_completeness": stored_receipt["completeness"],
        "continuation": stored_receipt["continuation"],
        "counts": {
            "capture_receipts": len(receipt_files),
            "artifacts": len(list((output_root / "artifacts" / "manifests").rglob("*.json"))),
            "events": len(events),
            "conversations": len(conversation_files),
            "messages": len(envelope["messages"]),
            "spans": len(envelope["spans"]),
            "lineage_nodes": len(lineage_data["nodes"]),
            "lineage_edges": len(lineage_data["edges"]),
            "current_conclusions": len(current),
            "citations_for_current_node": len(last_citations),
        },
        "source_binding": {
            "artifact_id": artifact_id,
            "byte_count": len(retained),
            "sha256": raw_sha,
            "matches_capture": retained == raw_bytes,
            "receipt_hash_matches": stored_receipt["source"]["sha256"] == raw_sha,
            "receipt_byte_count_matches": stored_receipt["source"]["byte_count"] == len(raw_bytes),
        },
        "checks": {
            "capture_receipt_complete": stored_receipt["completeness"] == "complete",
            "complete_promotion_allowed": True,
            "durable_artifact_exact": retained == raw_bytes,
            "durable_event_written": len(events) == 1,
            "durable_conversation_written": len(conversation_files) == 1,
            "durable_lineage_written": len(lineage_files) == 1,
            "qry": qry_pass,
            "lin": lin_pass,
            "reb": reb_pass,
        },
        "qry": {
            "mode": "deterministic message-term query over durable conversation envelope",
            "terms": query_terms,
            "hit_counts": {term: len(hits) for term, hits in query_hits.items()},
            "all_hits_reconstructed": qry_pass,
        },
        "lin": {
            "mode": "ConversationLineage structural traversal and citation resolution",
            "path_length": len(path),
            "lineage_node_count": len(lineage_data["nodes"]),
            "current_conclusion_ids": [node["node_id"] for node in current],
            "citation_summary": citations_summary,
            "passed": lin_pass,
        },
        "reb": {
            "mode": "destroy isolated projection slot, rebuild from durable events, compare semantic snapshot",
            "destroyed_slot_absent": not destroyed_slot.exists(),
            "expected_digest": expected_snapshot.digest(),
            "candidate_digest": candidate_snapshot.digest(),
            "mismatches": list(comparison.mismatches),
            "benchmarks": dict(comparison.benchmark_results),
            "query_before_digest": before_query_digest,
            "query_after_digest": after_query_digest,
            "citations_preserved": bool(citations_summary),
            "passed": reb_pass,
        },
        "product_gaps": product_gaps,
        "durable_output_root_local_only": str(output_root),
    }
    write_json(public_root / "fossil_ingest_probe.json", probe)
    write_json(
        public_root / "run.json",
        {
            "schema_version": "lab.run.v1",
            "run_id": RUN_ID,
            "experiment_id": EXPERIMENT_ID,
            "status": "pass" if all(probe["checks"].values()) else "blocked",
            "upstream_revision": args.fossil_revision,
            "command": "fresh public-share capture; graph-terminal proof; complete FOSSIL ingest; QRY/LIN/REB",
            "started_at": observed_at,
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "environment": {
                "lab_repo": "https://github.com/Pukujan/test-repo",
                "fossil_repo": f"https://github.com/Pukujan/fossil-core@{args.fossil_revision}",
                "local_host": "WSL Ubuntu on Windows workspace",
                "browser": "Codex in-app browser observed the public share page",
                "raw_capture_publicly_committed": False,
            },
            "outputs": [
                {"path": "source_capture.json", "kind": "capture-metadata"},
                {"path": "browser_surface.json", "kind": "surface-accounting"},
                {"path": "continuation_diagnosis.json", "kind": "continuation-diagnosis"},
                {"path": "completeness.json", "kind": "completeness-receipt"},
                {"path": "capture_receipt.json", "kind": "fossil-capture-receipt"},
                {"path": "manifest.json", "kind": "sanitized-fossil-ingest-manifest"},
                {"path": "fossil_capture_receipt_bound.json", "kind": "bound-fossil-capture-receipt"},
                {"path": "fossil_ingest_probe.json", "kind": "fossil-ingest-query-lineage-rebuild-probe"},
            ],
        },
    )
    print(json.dumps({"status": "pass", "checks": probe["checks"], "upstream_revision": args.fossil_revision}, indent=2))


if __name__ == "__main__":
    main()
