"""Record + model-response packet schema and the gold-separating packet builder.

This is the coupling layer. Everything downstream imports it so the shape of a
frozen item, a model-visible packet, and an ingested model response cannot drift.

Authority separation (kept explicit, never collapsed):
  visible packet  -> what the model may see (NO gold).
  gold            -> read only AFTER inference, for scoring.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from . import schemas as S

EXPERIMENT_DIR = Path(__file__).resolve().parents[1] / "experiments" / (
    "2026-09-18_real-data-abcd-verification"
)

GOLD_INDEX_PATH = EXPERIMENT_DIR / "gold_index" / "gold.json"

# Keys a model-visible packet may contain, by dataset.
FINQA_PACKET_KEYS = {"id", "question", "pre_text", "post_text", "table", "task", "task_family", "dataset"}
LEGAL_PACKET_KEYS = {"index", "question", "task", "task_family", "dataset"}

# Keys a response packet may contain.
RESPONSE_KEYS = {
    "item_id",
    "prompt_digest",
    "model_identity",
    "raw_answer",
    "structured",
    "abstained",
    "confidence",
    "meta",
}

STRUCTURED_FINQA_KEYS = S.STRUCTURED_FINQA_KEYS
STRUCTURED_LEGAL_KEYS = S.STRUCTURED_LEGAL_KEYS


class LeakError(Exception):
    """Raised when a model-visible packet would expose gold material."""


def load_gold_index(path: Path = GOLD_INDEX_PATH) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_record(item_id: str, gold_index: Optional[dict] = None) -> dict:
    """Return {item_id, dataset, task, visible, gold} for a frozen item."""
    gi = gold_index if gold_index is not None else load_gold_index()
    rec = gi[item_id]
    dataset = "finqa" if item_id not in {k for k in gi if "#" in k} and "#" not in item_id else "legalbench"
    return {
        "item_id": item_id,
        "dataset": rec.get("dataset", dataset),
        "task": rec.get("task"),
        "visible": rec["visible"],
        "gold": rec["gold"],
    }


def build_visible_packet(item_id: str, visible: dict) -> dict:
    """Return ONLY the model-visible portion, never gold.

    The visible dict from the gold index is already stripped of gold fields at
    freeze time, but we defensively rebuild from the known-visible keys and then
    run the leak guard, so a bug in freeze cannot silently expose gold.
    """
    packet = {
        "item_id": item_id,
        "dataset": visible.get("dataset") or ("finqa" if "#" not in item_id else "legalbench"),
    }
    for key in ("id", "index", "question", "pre_text", "post_text", "table", "task", "task_family"):
        if key in visible:
            packet[key] = visible[key]

    guard_packet(packet, item_id)
    return packet


def guard_packet(packet: dict, item_id: str = "?") -> None:
    """Deterministically reject a packet that carries any gold key or gold value."""
    if not isinstance(packet, dict):
        raise LeakError(f"packet is not a dict for {item_id}")
    gold_keys = set(S.GOLD_FIELDS_FINQA) | set(S.GOLD_FIELDS_LEGAL)
    present = gold_keys & set(packet.keys())
    if present:
        raise LeakError(f"packet for {item_id} carries gold keys: {sorted(present)}")


def prompt_digest(packet: dict) -> str:
    return S.item_digest(packet)


def new_response(
    item_id: str,
    *,
    prompt_digest: str,
    model_identity: str,
    raw_answer: Optional[str] = None,
    structured: Optional[dict] = None,
    abstained: bool = False,
    confidence: Optional[float] = None,
    meta: Optional[dict] = None,
) -> dict:
    return {
        "item_id": item_id,
        "prompt_digest": prompt_digest,
        "model_identity": model_identity,
        "raw_answer": raw_answer,
        "structured": structured,
        "abstained": abstained,
        "confidence": confidence,
        "meta": meta or {},
    }


def validate_response_shape(resp: dict) -> list[str]:
    """Return a list of structural problems (empty == structurally well-formed).

    Checks the envelope only; arm-specific validity (program executes, label in
    vocab, spans present) lives in the per-arm validators. No gold consulted.
    """
    problems: list[str] = []
    missing = RESPONSE_KEYS - set(resp.keys())
    if missing:
        problems.append(f"missing response keys: {sorted(missing)}")
    struct = resp.get("structured")
    if isinstance(struct, dict):
        dataset = "legalbench" if "#" in str(resp.get("item_id", "")) else "finqa"
        allowed = STRUCTURED_LEGAL_KEYS if dataset == "legalbench" else STRUCTURED_FINQA_KEYS
        extra = set(struct.keys()) - allowed
        if extra:
            problems.append(f"unexpected structured keys: {sorted(extra)}")
    return problems
