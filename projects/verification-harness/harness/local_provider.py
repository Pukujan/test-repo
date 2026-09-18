"""Gold-blind local substitute for Luna / NSAI translation.

This environment has no Luna or hosted generative LLM. The provider reads
ONLY the model-visible packet and emits a deterministic structured response.
It never opens gold_index values except via the visible dict passed in.

Used as the primary real-data benchmark substitute. Documented limitation:
extractive heuristics, not an instruct model with token logprobs.
"""
from __future__ import annotations

import re

from . import finqa_program
from . import record as R


MODEL_ABC = "LocalExtractiveScoreProvider"
MODEL_D1 = "LocalNSAITranslator"


def _numbers_from_table(table) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    if not isinstance(table, list):
        return out
    for row in table:
        if not isinstance(row, list):
            continue
        for cell in row:
            val = finqa_program.parse_number(cell)
            if val is not None:
                out.append((str(cell), val))
    return out


def _cite_span(question: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9%$.'-]+", question or "") if len(w) > 2]
    if not words:
        return (question or "item")[:24]
    take = words[: min(6, len(words))]
    span = " ".join(take)
    if span and span in (question or ""):
        return span
    return words[0]


def local_legal(item_id: str, visible: dict, *, nsai: bool) -> dict:
    question = visible.get("question") or visible.get("text") or ""
    task = (visible.get("task") or "").lower()
    q = question.lower()
    label = "No"
    if task == "hearsay":
        if any(w in q for w in ("said", "told", "testified", "statement", "out of court", "heard")):
            label = "Yes"
    elif task == "definition_classification":
        if any(w in q for w in ("means", "defined", "definition", "is a", "refers to")):
            label = "Yes"
    elif task == "overruling":
        if any(w in q for w in ("overrule", "overruled", "overruling", "we reject")):
            label = "Yes"
    elif "contract_nli" in task:
        if any(w in q for w in ("confidential", "non-disclosure", "nda", "shall not disclose")):
            label = "Yes"
    elif "citizenship" in task:
        if any(w in q for w in ("citizen", "nationality", "born in", "naturaliz")):
            label = "Yes" if "not" not in q.split("?")[0][-24:] else "No"
    span = _cite_span(question)
    facts = [f"visible-task:{task or 'legal'}", f"span-used:{span[:80]}"]
    rules = ["label is Yes only if a task-keyword fires on the visible question"]
    struct = {
        "label": label,
        "facts": facts,
        "rules": rules,
        "cited_spans": [span],
        "uncertain_fields": ["gold-blind heuristic; no case law lookup"],
    }
    envelope = {k: struct[k] for k in ("label", "facts", "rules", "cited_spans", "uncertain_fields")}
    return R.new_response(
        item_id,
        prompt_digest="",
        model_identity=MODEL_D1 if nsai else MODEL_ABC,
        raw_answer=label,
        structured=envelope,
        confidence=0.55,
        meta={"provider": "local", "treatment": "D1-NSAI" if nsai else "A/B/C"},
    )


def local_finqa(item_id: str, visible: dict, *, nsai: bool) -> dict:
    question = visible.get("question") or ""
    table = visible.get("table") or []
    nums = _numbers_from_table(table)
    pre = visible.get("pre_text") or []
    fact_src = ""
    if isinstance(pre, list) and pre:
        fact_src = str(pre[0])[:80]
    elif isinstance(table, list) and table:
        fact_src = str(table[0])[:80]
    else:
        fact_src = question[:80] or "table"
    if len(nums) < 2:
        if len(nums) == 1:
            val = nums[0][1]
            prog = f"add({_lit(val)}, const_0)"
        else:
            return R.new_response(
                item_id, prompt_digest="", model_identity=MODEL_D1 if nsai else MODEL_ABC,
                abstained=True, meta={"provider": "local", "reason": "no_numeric_cells"})
    else:
        a, b = nums[-1][1], nums[-2][1]
        q = question.lower()
        if any(w in q for w in ("percent", "percentage", "%", "rate", "ratio", "growth")):
            if b == 0:
                prog = f"subtract({_lit(a)}, {_lit(b)})"
            else:
                prog = f"subtract({_lit(a)}, {_lit(b)}), divide(#0, {_lit(b)})"
        elif any(w in q for w in ("average", "mean")):
            prog = f"add({_lit(a)}, {_lit(b)}), divide(#0, const_2)"
        elif any(w in q for w in ("increase", "decrease", "change", "difference")):
            prog = f"subtract({_lit(a)}, {_lit(b)})"
        else:
            prog = f"subtract({_lit(a)}, {_lit(b)})"
    val, reason = finqa_program.execute_program(prog, table)
    if reason != "ok" or val is None:
        return R.new_response(
            item_id, prompt_digest="", model_identity=MODEL_D1 if nsai else MODEL_ABC,
            abstained=True, meta={"provider": "local", "reason": reason})
    pct = any(w in question.lower() for w in ("percent", "percentage", "%", "rate", "growth"))
    answer = f"{val * 100:.4f}%" if pct and abs(val) < 5 else f"{val:.4f}"
    struct = {
        "answer": answer,
        "program": prog,
        "supporting_facts": [fact_src or "table-derived"],
    }
    return R.new_response(
        item_id,
        prompt_digest="",
        model_identity=MODEL_D1 if nsai else MODEL_ABC,
        raw_answer=answer,
        structured=struct,
        confidence=0.55,
        meta={"provider": "local", "treatment": "D1-NSAI" if nsai else "A/B/C"},
    )


def _lit(val: float) -> str:
    if float(val).is_integer() and abs(val) < 1e12:
        return str(int(val))
    return f"{val:.6g}"


def local_response(item_id: str, visible: dict, *, nsai: bool = False) -> dict:
    packet = R.build_visible_packet(item_id, visible)
    pd = R.prompt_digest(packet)
    if "#" in item_id:
        resp = local_legal(item_id, visible, nsai=nsai)
    else:
        resp = local_finqa(item_id, visible, nsai=nsai)
    resp["prompt_digest"] = pd
    return resp
