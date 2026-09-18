"""Export model-visible Luna prompt packets and ingest Luna JSON responses.

The exporter emits ONLY visible packets (gold never written). The importer reads
user-saved Luna responses and validates their shape WITHOUT consulting gold.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import record as R
from . import schemas as S


INSTRUCTIONS_FinqA = (
    "You are a financial analyst. Given the SEC filing excerpt and question, "
    "return STRICT JSON with keys: answer (string), program (FinQA-style DSL "
    "program using add/subtract/multiply/divide and #N step references), "
    "supporting_facts (list of short strings from the provided text/table). "
    "Do not include anything outside the JSON."
)
INSTRUCTIONS_LEGAL = (
    "You are a legal reasoner. Given the question, return STRICT JSON with keys: "
    "label (exactly Yes or No), facts (list of short factual statements you "
    "relied on), rules (list of legal rules you applied), cited_spans (list of "
    "exact substrings copied verbatim from the question you relied on), "
    "uncertain_fields (list). Do not include anything outside the JSON."
)


def export_prompts(items: list[str], gold_index: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": "vh.luna-export.v1", "model_identity": "LUNA-TBD", "packets": []}
    for item_id in items:
        rec = gold_index[item_id]
        packet = R.build_visible_packet(item_id, rec["visible"])
        instructions = INSTRUCTIONS_LEGAL if "#" in item_id else INSTRUCTIONS_FinqA
        prompt = {
            "item_id": item_id,
            "visible": packet,
            "instructions": instructions,
        }
        (out_dir / f"{_safe(item_id)}.json").write_text(
            json.dumps(prompt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest["packets"].append({"item_id": item_id, "prompt_digest": R.prompt_digest(packet)})
    (out_dir / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def ingest_responses(responses_dir: Path, gold_index: dict, items: list[str]) -> dict:
    """Read Luna-saved responses into the ingested store. Shape-only validation."""
    ingested = {}
    problems = []
    for item_id in items:
        path = responses_dir / f"{_safe(item_id)}.json"
        if not path.exists():
            problems.append({"item_id": item_id, "reason": "missing_response"})
            continue
        resp = json.loads(path.read_text(encoding="utf-8"))
        shape_problems = R.validate_response_shape(resp)
        if shape_problems:
            problems.append({"item_id": item_id, "reason": "shape", "detail": shape_problems})
        ingested[item_id] = resp
    return {"responses": ingested, "problems": problems}


def _safe(item_id: str) -> str:
    return item_id.replace("/", "_").replace("#", "__")
