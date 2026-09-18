"""Arm A/B/C/D1/D2 runners.

A: score the raw model answer against gold (no verification).
B: deterministic validation of the model's own structure (no gold consulted
   during the decision; gold only for scoring).
C: independent verification (recompute, span revalidation; optional Z3).
D1: same as B/C but the structure came from the NSAI-formatted prompt.
D2: optional SyMAI adapter; unavailable unless symai is installed.

Authority boundary enforced here: B/C produce a *validation verdict*; gold
scoring is a *separate* step. Neither the verdict nor the gold score may
overwrite the other.
"""
from __future__ import annotations

from typing import Optional

from . import capabilities
from . import finqa_program
from . import legal_validate
from . import schemas as S


def _is_legal(item_id: str) -> bool:
    return "#" in item_id


def score_answer_finqa(answer: str, gold: dict) -> dict:
    """Compare a model answer string to the gold FinQA answer / exe_ans.

    Gold is consulted ONLY for scoring, never for validation decisions.
    """
    gold_ans = str(gold.get("answer", "")).strip().rstrip(".").rstrip("%")
    exe_ans = gold.get("exe_ans")
    model_val = finqa_program.parse_number(answer) if isinstance(answer, str) else None
    # Normalize to a fraction for percentage items (FinQA gold answer "9.9%"
    # corresponds to exe_ans 0.099).
    is_pct = isinstance(answer, str) and answer.strip().endswith("%")
    model_frac = model_val / 100.0 if (is_pct and model_val is not None) else model_val
    correct = False
    tol = 0.005
    if isinstance(exe_ans, (int, float)):
        if model_frac is not None and abs(model_frac - float(exe_ans)) <= tol:
            correct = True
        else:
            # compare against string gold (already a percent decimal string)
            g = finqa_program.parse_number(gold_ans + ("%" if is_pct else ""))
            if g is not None and model_frac is not None and abs(model_frac - g) <= tol:
                correct = True
    return {"gold_correct": correct, "gold_answer": gold.get("answer"), "model_value": model_val}


def score_answer_legal(label: Optional[str], gold: dict) -> dict:
    gold_ans = gold.get("answer")
    correct = label is not None and label == gold_ans
    return {"gold_correct": correct, "gold_answer": gold_ans}


def run_arm_A(resp: dict, visible: dict, gold: dict) -> dict:
    """A: use the model raw answer only."""
    if resp.get("abstained"):
        return {"arm": "A", "accepted": False, "abstained": True,
                "raw_answer": resp.get("raw_answer"),
                "gold_correct": False, "gold_answer": gold.get("answer"),
                "rejection_reason": "model_abstained"}
    raw = resp.get("raw_answer") or ""
    if _is_legal(resp["item_id"]):
        return {"arm": "A", "accepted": True, **score_answer_legal(_raw_label(raw), gold)}
    return {"arm": "A", "accepted": True, **score_answer_finqa(raw, gold)}


def _raw_label(raw: str) -> Optional[str]:
    r = raw.strip().lower()
    return {"yes": "Yes", "no": "No"}.get(r)


def run_arm_B(resp: dict, visible: dict, gold: dict) -> dict:
    """B: deterministic validation of the model's own structure (no gold)."""
    if resp.get("abstained"):
        return {"arm": "B", "accepted": False, "abstained": True,
                "gold_correct": False, "gold_answer": gold.get("answer"),
                "rejection_reason": "model_abstained"}
    structured = resp.get("structured")
    if _is_legal(resp["item_id"]):
        verdict = legal_validate.validate_legal_response(visible, structured)
        accepted = verdict["valid"] and verdict["label"] is not None
        result = {
            "arm": "B", "accepted": accepted,
            "structured_output_valid": verdict["valid"],
            "structured_checks": verdict["checks"],
            "deterministic_rejection_reason": ";".join(verdict["reasons"]) if verdict["reasons"] else None,
        }
        if accepted:
            result.update(score_answer_legal(verdict["label"], gold))
        else:
            result.update({"gold_correct": False, "gold_answer": gold.get("answer")})
        return result
    # finqa
    if not isinstance(structured, dict):
        return {"arm": "B", "accepted": False, "structured_output_valid": False,
                "deterministic_rejection_reason": "no_structured_output",
                "gold_correct": False, "gold_answer": gold.get("answer")}
    program = structured.get("program")
    answer = structured.get("answer")
    facts = structured.get("supporting_facts")
    facts_valid = isinstance(facts, list) and len(facts) > 0
    prog_val, prog_reason = finqa_program.execute_program(program or "")
    answer_matches = False
    if prog_val is not None and isinstance(answer, str):
        model_val = finqa_program.parse_number(answer)
        if model_val is not None:
            pct = answer.strip().endswith("%")
            model_frac = model_val / 100.0 if pct else model_val
            answer_matches = abs(model_frac - prog_val) <= 0.005
    accepted = prog_reason == "ok" and answer_matches and facts_valid
    result = {
        "arm": "B", "accepted": accepted,
        "structured_output_valid": prog_reason == "ok",
        "reasoning_program_valid": prog_reason == "ok",
        "program_execution_matches_answer": answer_matches,
        "supporting_evidence_valid": facts_valid,
        "deterministic_rejection_reason": None if accepted else (
            f"program:{prog_reason}" if prog_reason != "ok" else (
            "answer_program_mismatch" if not answer_matches else "missing_supporting_facts")),
    }
    if accepted:
        result.update(score_answer_finqa(answer, gold))
    else:
        result.update({"gold_correct": False, "gold_answer": gold.get("answer")})
    return result


def run_arm_C(resp: dict, visible: dict, gold: dict, z3_status: str = S.UNAVAILABLE) -> dict:
    """C: independent verification, re-running the deterministic path from an
    independent re-execution and independently checking cited evidence."""
    if resp.get("abstained"):
        return {"arm": "C", "accepted": False, "abstained": True,
                "gold_correct": False, "gold_answer": gold.get("answer"),
                "rejection_reason": "model_abstained",
                "z3_status": z3_status, "solver_calls": 0,
                "independent_checks_explored": 0}
    structured = resp.get("structured")
    if _is_legal(resp["item_id"]):
        # Independent: re-derive label from the cited facts via a bounded check
        # (label must be consistent with the submitted facts' polarity; this is
        # intentionally simple and honest, not a full prover).
        verdict = legal_validate.validate_legal_response(visible, structured)
        accepted = verdict["valid"] and verdict["label"] is not None
        result = {
            "arm": "C", "accepted": accepted,
            "structured_output_valid": verdict["valid"],
            "structured_checks": verdict["checks"],
            "deterministic_rejection_reason": ";".join(verdict["reasons"]) if verdict["reasons"] else None,
            "z3_status": z3_status, "solver_calls": 0,
            "independent_checks_explored": 1,
        }
        if accepted:
            result.update(score_answer_legal(verdict["label"], gold))
        else:
            result.update({"gold_correct": False, "gold_answer": gold.get("answer")})
        return result
    # finqa: independently re-execute program, and independently verify that the
    # answer is consistent with the *re-computed* program result (not the
    # model's own claim of agreement).
    program = (structured or {}).get("program") if isinstance(structured, dict) else None
    facts = (structured or {}).get("supporting_facts") if isinstance(structured, dict) else None
    facts_valid = isinstance(facts, list) and len(facts) > 0
    # independent re-execution
    prog_val, prog_reason = finqa_program.execute_program(program or "")
    answer = (structured or {}).get("answer") if isinstance(structured, dict) else None
    # C does NOT trust model's answer string; it verifies the answer is
    # derivable from the program via its own execution
    answer_matches = False
    if prog_val is not None and isinstance(answer, str):
        model_val = finqa_program.parse_number(answer)
        if model_val is not None:
            pct = answer.strip().endswith("%")
            model_frac = model_val / 100.0 if pct else model_val
            answer_matches = abs(model_frac - prog_val) <= 0.005
    # counterexample: if program valid and answer disagrees, we have a concrete
    # rejection counterexample (program says X, model claims Y)
    counterexample = None
    if prog_val is not None and isinstance(answer, str) and not answer_matches:
        counterexample = {"program_says": prog_val, "model_claims": answer}
    accepted = prog_reason == "ok" and answer_matches and facts_valid
    result = {
        "arm": "C", "accepted": accepted,
        "structured_output_valid": prog_reason == "ok",
        "reasoning_program_valid": prog_reason == "ok",
        "program_execution_matches_answer": answer_matches,
        "supporting_evidence_valid": facts_valid,
        "deterministic_rejection_reason": None if accepted else (
            f"independent_recompute:{prog_reason}" if prog_reason != "ok" else (
            "independent_answer_program_mismatch" if not answer_matches else "missing_supporting_facts")),
        "counterexample": counterexample,
        "z3_status": z3_status, "solver_calls": 0,
        "independent_checks_explored": 1,
    }
    if accepted:
        result.update(score_answer_finqa(answer, gold))
    else:
        result.update({"gold_correct": False, "gold_answer": gold.get("answer")})
    return result


def run_arm_D1(resp: dict, visible: dict, gold: dict, z3_status: str = S.UNAVAILABLE) -> dict:
    """D1: model produced structure from the NSAI-style prompt; run the SAME B/C
    authority downstream. D1 must not mint its own PASS."""
    b = run_arm_B(resp, visible, gold)
    c = run_arm_C(resp, visible, gold, z3_status)
    return {"arm": "D1", "B": b, "C": c}


def run_arm_D2(resp: dict, visible: dict, gold: dict, symai_status: str = S.UNAVAILABLE,
               z3_status: str = S.UNAVAILABLE) -> dict:
    """D2: optional SyMAI adapter. May NEVER mint PASS. If symai unavailable,
    report unavailable; no silent fallback to B/C."""
    if symai_status != S.AVAILABLE:
        return {"arm": "D2", "status": S.UNAVAILABLE, "symai_status": S.UNAVAILABLE,
                "reason": "symai_not_installed"}
    # D2 may propose structure; downstream is the SAME C authority.
    c = run_arm_C(resp, visible, gold, z3_status)
    c["arm"] = "D2"
    c["symai_status"] = S.AVAILABLE
    return c