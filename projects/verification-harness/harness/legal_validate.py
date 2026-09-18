"""Deterministic validation of a model's own legal structured output (arm B).

Reads only the model-visible item and the model response; never gold. Produces
a structured verdict with explicit rejection reasons. A missing/unsupported
evidence field is `unknown`/rejection, never a fabricated pass.
"""
from __future__ import annotations

from typing import Any

from . import schemas as S


def _normalize_label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    mapping = {
        "yes": "Yes", "no": "No",
        "true": "Yes", "false": "No",
        "entailment": "entailment",
        "contradiction": "contradiction",
        "not mentioned": "not mentioned",
        "na": "not mentioned", "n/a": "not mentioned",
    }
    return mapping.get(v)


def validate_legal_response(visible: dict, structured: dict | None) -> dict:
    """Return {"valid": bool, "label": str|None, "reasons": [...], "checks": {...}}.

    No gold consulted.
    """
    reasons: list[str] = []
    checks: dict[str, Any] = {}

    if not isinstance(structured, dict):
        return {"valid": False, "label": None, "reasons": ["no_structured_output"], "checks": {}}

    # (1) schema
    extra = set(structured.keys()) - S.STRUCTURED_LEGAL_KEYS
    if extra:
        reasons.append(f"unexpected_keys:{sorted(extra)}")

    # (2) label vocabulary
    label = _normalize_label(structured.get("label"))
    checks["label_present"] = label is not None
    if label is None:
        reasons.append("invalid_or_missing_label")

    # (3) evidence: must provide at least one supporting fact and one cited span
    facts = structured.get("facts")
    spans = structured.get("cited_spans")
    checks["has_facts"] = isinstance(facts, list) and len(facts) > 0
    checks["has_spans"] = isinstance(spans, list) and len(spans) > 0
    if not checks["has_facts"]:
        reasons.append("missing_supporting_facts")
    if not checks["has_spans"]:
        reasons.append("missing_cited_spans")

    # (4) cited spans must actually appear in the model-visible text (evidence
    #     grounding). An unsupported span is a rejection, not a pass.
    haystack = (visible.get("question") or "") + " " + (visible.get("text") or "")
    grounded = 0
    ungrounded = []
    if isinstance(spans, list):
        for s in spans:
            if isinstance(s, str) and s.strip() and s.strip() in haystack:
                grounded += 1
            else:
                ungrounded.append(str(s)[:40])
    checks["grounded_spans"] = grounded
    checks["ungrounded_spans"] = ungrounded
    if isinstance(spans, list) and spans and grounded == 0:
        reasons.append("no_grounded_cited_span")

    valid = not reasons
    return {"valid": valid, "label": label, "reasons": reasons, "checks": checks}
