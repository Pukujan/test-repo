"""Deterministic mock provider for CI mechanics (no API/credentials).

Gold is read ONLY here, to fabricate a realistic mix of correct and subtly-wrong
model outputs. The arms (A/B/C/D1) consume these stored responses and never
re-read gold; that boundary is kept confined to this module.

Byte-identical across runs: all choices derive from schemas.item_digest, never
Python's global RNG or time.
"""
from __future__ import annotations

from typing import Optional

from . import finqa_program
from . import record as R
from . import schemas as S


def _bucket(item_id: str, salt: str, n: int) -> int:
    h = S.sha256_text(f"{item_id}:{salt}")
    return int(h[:12], 16) % n


def _pick_correct_program(gold: dict) -> Optional[str]:
    prog = gold.get("program")
    return prog if isinstance(prog, str) and prog.strip() else None


def _wrong_program(prog: str) -> str:
    # swap operands of the first subtract/divide to make a subtly wrong program
    v, _ = finqa_program.execute_program(prog)
    if v is None:
        return "divide(1, 0)"
    return "add(0.5, 0.5)"  # valid, executes, but not the gold result


def mock_finqa(item_id: str, gold: dict, visible: dict) -> dict:
    b = _bucket(item_id, "finqa", 100)
    if b < 10:
        return R.new_response(item_id, prompt_digest="", model_identity="mock-deterministic",
                              abstained=True)
    correct = _pick_correct_program(gold)
    exe = gold.get("exe_ans")
    if b < 50:  # correct program + matching answer
        prog = correct or "add(1, 1)"
        val = finqa_program.execute_program(prog)[0]
        if val is None:
            val = float(exe) if isinstance(exe, (int, float)) else 1.0
        ans = _fmt(val, gold)
        struct = {"answer": ans, "program": prog, "supporting_facts": ["revenue"]}
    elif b < 75:  # wrong-but-executable program + matching (wrong) answer -> false accept
        prog = _wrong_program(correct or "add(1, 1)")
        val = finqa_program.execute_program(prog)[0]
        ans = _fmt(val, gold)
        struct = {"answer": ans, "program": prog, "supporting_facts": ["revenue"]}
    elif b < 90:  # valid program but answer disagrees with program -> rejection
        prog = correct or "add(1, 1)"
        struct = {"answer": "999", "program": prog, "supporting_facts": ["revenue"]}
    else:  # missing supporting facts -> rejection
        prog = correct or "add(1, 1)"
        val = finqa_program.execute_program(prog)[0] or 1.0
        struct = {"answer": _fmt(val, gold), "program": prog, "supporting_facts": []}
    return R.new_response(item_id, prompt_digest="", model_identity="mock-deterministic",
                          raw_answer=struct["answer"], structured=struct,
                          confidence=0.5 + (_bucket(item_id, "conf", 50) / 100.0))


def _fmt(val: float, gold: dict) -> str:
    gold_ans = str(gold.get("answer", ""))
    if "%" in gold_ans:
        return f"{val * 100:.2f}%"
    return f"{val:.4f}"


def mock_legal(item_id: str, gold: dict, visible: dict) -> dict:
    b = _bucket(item_id, "legal", 100)
    if b < 8:
        return R.new_response(item_id, prompt_digest="", model_identity="mock-deterministic",
                              abstained=True)
    question = visible.get("question") or visible.get("text") or ""
    correct_lbl = gold.get("answer")
    wrong_lbl = "No" if correct_lbl == "Yes" else "Yes"
    label = correct_lbl if b < 60 else wrong_lbl
    # grounding: pick a real span 75% of the time, else a bogus span
    if question and _bucket(item_id, "span", 100) < 75:
        words = [w for w in question.split() if len(w) > 3]
        span = words[len(words) // 2] if words else question[:20]
    else:
        span = "ZZZ unsupported token not present"
    struct = {
        "label": label,
        "facts": ["relevant contractual fact"],
        "rules": ["applicable legal rule"],
        "cited_spans": [span],
        "uncertain_fields": [],
    }
    if b >= 90:  # schema break: label missing
        struct["label"] = None
    return R.new_response(item_id, prompt_digest="", model_identity="mock-deterministic",
                          raw_answer=label or "", structured=struct,
                          confidence=0.5 + (_bucket(item_id, "conf", 50) / 100.0))


def mock_response(item_id: str, arm: str, gold_index: dict) -> dict:
    rec = gold_index[item_id]
    visible = rec["visible"]
    gold = rec["gold"]
    packet = R.build_visible_packet(item_id, visible)
    pd = R.prompt_digest(packet)
    resp = mock_legal(item_id, gold, visible) if "#" in item_id else mock_finqa(item_id, gold, visible)
    # bind prompt digest after building
    resp["prompt_digest"] = pd
    resp["meta"] = {"arm": arm, "provider": "mock"}
    return resp
