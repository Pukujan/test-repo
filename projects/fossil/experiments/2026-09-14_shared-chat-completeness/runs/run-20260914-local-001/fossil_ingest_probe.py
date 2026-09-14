from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fossil_core.artifact_store import ArtifactStore
from fossil_core.conversation import ConversationStore
from fossil_core.event_store import DurableEventStore
from fossil_core.source import SourceSnapshotStore


SHARE_URL = "https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58"
PACK_ID = "pack_f024177f89a5442db84171c3dd7f58e5"


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: python fossil_ingest_probe.py SOURCE_RESPONSE OUTPUT_ROOT SUMMARY_JSON FOSSIL_ROOT"
        )
    source_path, output_root, summary_path, fossil_root = map(Path, sys.argv[1:])
    raw = source_path.read_bytes()
    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )

    artifacts = ArtifactStore(output_root / "artifacts")
    snapshots = SourceSnapshotStore(
        output_root / "sources",
        artifacts,
        fossil_root / "schemas" / "source-snapshot" / "v1.schema.json",
        fossil_root / "schemas" / "citation" / "v1.schema.json",
    )
    snapshot = snapshots.put_snapshot(
        raw,
        locator={"url": SHARE_URL, "identifier": None, "repository_ref": None},
        retrieved_at=timestamp,
        source_role="primary",
        quality={
            "authority": 0.5,
            "directness": 1.0,
            "independence": 0.0,
            "reproducibility": 0.8,
            "timeliness": 1.0,
            "notes": "Primary evidence for the public-share representation only; not an authenticated account export.",
        },
        media_type="text/html",
    )
    marker = "shared-page representation"
    start = raw.index(marker.encode("utf-8"))
    end = start + len(marker.encode("utf-8"))
    citation = snapshots.create_citation(snapshot["snapshot_id"], byte_start=start, byte_end=end)

    conversations = ConversationStore(
        output_root / "conversations",
        artifacts,
        fossil_root / "schemas" / "conversation" / "v1.schema.json",
    )
    source = conversations.add_source(
        raw,
        evidence_status="verbatim",
        media_type="text/html",
        label="public shared-chat response body",
        external_ref=SHARE_URL,
    )
    span = conversations.span_for_text(source, marker)
    envelope = conversations.commit(
        {
            "schema_version": "fossil.conversation.v1",
            "conversation_id": "conv_live_share_probe_20260914",
            "source_status": "verbatim",
            "title": "Productizing Fossil Core — bounded live-share probe",
            "sources": [source],
            "spans": [span],
            "messages": [
                {
                    "message_id": "msg_live_share_probe_001",
                    "sequence": 0,
                    "parent_message_id": None,
                    "occurred_at": None,
                    "actor": {
                        "actor_id": "shared-chat-rendered-source",
                        "role": "other",
                        "provider": "ChatGPT share page",
                        "model_id": None,
                        "run_id": None,
                        "tool_id": None,
                    },
                    "evidence_status": "verbatim",
                    "text": marker,
                    "source_span_refs": [span["span_id"]],
                }
            ],
        }
    )

    events = DurableEventStore(
        output_root / "events", fossil_root / "schemas" / "events" / "v1.schema.json"
    )
    event = conversations.build_ingested_event(
        envelope,
        pack_id=PACK_ID,
        actor_id="live-shared-chat-probe",
        occurred_at=timestamp,
        recorded_at=timestamp,
    )
    event["source_snapshot_refs"] = [snapshot["snapshot_id"]]
    event["actor"] = {
        "actor_type": "importer",
        "actor_id": "live-shared-chat-probe",
        "harness_version": "experiment-run-20260914-local-001",
        "skill_id": "none",
        "skill_version": "none",
    }
    event["provenance"] = {
        "method": "bounded_live_shared_chat_probe",
        "prompt_or_policy_ref": "projects/fossil/experiments/2026-09-14_shared-chat-completeness",
        "benchmark_ref": "run-20260914-local-001",
    }
    committed_event = events.commit(event)

    summary = {
        "schema_version": "lab.fossil-ingest-probe.v1",
        "result": "accepted_without_completeness_gate",
        "source": {
            "path": str(source_path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "status_presented_to_current_path": "verbatim",
            "capture_completeness_known_to_current_path": False,
        },
        "durable_outputs": {
            "artifact_count": len(list((output_root / "artifacts" / "manifests").rglob("*.json"))),
            "source_snapshot_count": len(list((output_root / "sources" / "snapshots").rglob("*.json"))),
            "citation_count": 1,
            "conversation_envelope_count": len(list((output_root / "conversations").rglob("conv_*.json"))),
            "event_count": len(list((output_root / "events").rglob("evt_*.json"))),
            "lineage_count": len(list((output_root / "lineages").rglob("lin_*.json"))),
            "claim_count": 0,
            "relation_count": 0,
        },
        "refs": {
            "snapshot_id": snapshot["snapshot_id"],
            "citation_id": citation["citation_id"],
            "conversation_id": envelope["conversation_id"],
            "event_id": committed_event["event_id"],
            "artifact_id": source["artifact_id"],
        },
        "finding": "The current ConversationStore/EventStore path accepts a manually bounded verbatim subset and emits durable artifacts, snapshot, citation, envelope, and event, but has no shared-chat completeness field/gate and emits no semantic lineage, claims, or relations.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
