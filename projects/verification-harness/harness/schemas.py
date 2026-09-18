"""Shared schema, field-separation rules, and digests.

This module is the single frozen interface. Every other harness module imports
these constants so a field can never accidentally drift between the model-visible
path and the gold path.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

# ---- Arms ------------------------------------------------------------------

ARM_A = "A"      # model answer only
ARM_B = "B"      # deterministic structured validation
ARM_C = "C"      # independent verification
ARM_D1 = "D1"    # neuro-symbolic translation prompt + same B/C authority
ARM_D2 = "D2"    # optional SyMAI adapter (unavailable unless installed)

ARMS = (ARM_A, ARM_B, ARM_C, ARM_D1, ARM_D2)

# ---- Availability states ---------------------------------------------------
# Never collapse these. `unavailable` must never be upgraded to pass.
AVAILABLE = "available"
UNAVAILABLE = "unavailable"

# ---- Gold / model-visible separation --------------------------------------
# Keys that carry the answer, gold program, gold spans, or scoring info.
# The model-visible packet builder MUST drop every one of these, and the leak
# guard test asserts no packet text contains any of them.

GOLD_FIELDS_FINQA = (
    "answer",       # final gold numeric/percentage answer
    "program",      # gold reasoning program
    "program_re",   # gold reasoning program (alternative)
    "steps",        # gold explanation steps
    "explanation",
    "exe_ans",      # gold executed numeric answer
    "exe_args",
    "gold_inds",    # gold supporting facts (table/text spans)
    "gold_table",
    "gold_text",
    "gold_logic",
    "model_input",  # gold model input containing gold_inds
    "ann_table_rows",  # gold annotation row indices
    "ann_text_rows",
    "tfidftopn",
    "answer_type",
)

GOLD_FIELDS_LEGAL = (
    "answer",   # gold label
    "label",
    "gold",
    "gold_label",
    "slice",    # LegalBench gold slice/explanation
    "explanation",
    "doc_label",
    "label_name",
)

# Non-exhaustive backstop substrings; the packet builder rejects any of these
# appearing anywhere in a serialized model-visible packet for a real item.
GOLD_SUBSTRINGS = ("answer", "gold", "exe_ans", "program", "supporting")

# ---- FinQA model-visible keys (only these) --------------------------------

FINQA_VISIBLE_KEYS = ("id", "question", "pre_text", "post_text", "table", "table_ori")

# ---- Legal model-visible keys (only these) --------------------------------

LEGAL_VISIBLE_KEYS = ("index", "text")
LEGAL_TASK_META_VISIBLE_KEYS = ("task", "task_family", "instruction", "choices")

STRUCTURED_FINQA_KEYS = {"answer", "program", "supporting_facts"}
STRUCTURED_LEGAL_KEYS = {"label", "facts", "rules", "cited_spans", "uncertain_fields"}

# ---- Legal label vocabularies --------------------------------------------

LEGAL_LABELS_BINARY = ("Yes", "No")
LEGAL_LABELS_CONTRACTNLI = ("entailment", "contradiction", "not mentioned")

# LegalBench ContractNLI families in nguha/legalbench encode gold as Yes/No
# (Yes == the hypothesis holds == entailment, No == not-entailment). Mapping is
# defined explicitly so scoring never guesses.
CONTRACTNLI_GOLD_TO_CANONICAL = {
    "Yes": "entailment",
    "No": "not mentioned",  # conservative: gold 'No' groups contradiction+NA
}

# ---- LegalBench task family roles for this experiment --------------------
# Chosen for objective, machine-scoreable gold (no subjective judging).
# All five are deterministic Yes/No classification so the legal structured
# validator has one clean label authority (no free-text/exact-match scoring).
# `question_column` records which raw column carries the model-visible stem.
LEGAL_TASKS = {
    "hearsay": {"family": "rule_application", "labels": LEGAL_LABELS_BINARY, "question_column": "text"},
    "definition_classification": {"family": "definition", "labels": LEGAL_LABELS_BINARY, "question_column": "text"},
    "overruling": {"family": "classification", "labels": LEGAL_LABELS_BINARY, "question_column": "text"},
    "contract_nli_confidentiality_of_agreement": {"family": "contract_nli", "labels": LEGAL_LABELS_BINARY, "question_column": "text"},
    "international_citizenship_questions": {"family": "rule_application", "labels": LEGAL_LABELS_BINARY, "question_column": "question"},
}

# ---- Deterministic sampling ----------------------------------------------

SAMPLE_SEED = 20260918

# ---- Digest helpers -------------------------------------------------------

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def item_digest(visible: Any) -> str:
    """Content digest of ONLY the model-visible portion of an item."""
    return sha256_text(canonical_json(visible))
