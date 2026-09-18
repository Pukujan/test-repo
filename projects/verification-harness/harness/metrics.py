"""Aggregate metrics per arm and marginal layer gains.

Reports tradeoffs (coverage, false accepts, false rejects), not a single winner.
Arm A carries the model's raw gold-correctness; later arms carry accepted +
gold_correct. A 'would have been correct' rejection uses arm A as the signal.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def _rate(num: int, den: int) -> float:
    return (num / den) if den else 0.0


def load_decisions(records: list[dict]) -> dict[str, dict[str, dict]]:
    by_item: dict[str, dict[str, dict]] = defaultdict(dict)
    for rec in records:
        by_item[rec["item_id"]][rec["arm"]] = rec["arm_result"]
    return dict(by_item)


def _d1_decision(inner: dict) -> dict:
    b = inner.get("B", {})
    c = inner.get("C", {})
    return {
        "accepted": bool(b.get("accepted")) and bool(c.get("accepted")),
        "gold_correct": bool(c.get("gold_correct")),
        "abstained": bool(c.get("abstained")),
    }


def summarize_arm(by_item: dict, arm: str) -> dict[str, Any]:
    decisions = {iid: (v[arm] if arm != "D1" else _d1_decision(v[arm]))
                 for iid, v in by_item.items() if arm in v}
    n = len(decisions)
    if n == 0:
        return {"n": 0}
    accepted = [d for d in decisions.values() if d.get("accepted")]
    abstained = sum(1 for d in decisions.values() if d.get("abstained"))
    rejected = n - len(accepted) - abstained

    false_accept = sum(1 for d in accepted if not d.get("gold_correct"))
    false_reject = 0
    for iid, d in decisions.items():
        if d.get("accepted") or d.get("abstained"):
            continue
        a = by_item[iid].get("A", {})
        if a.get("gold_correct"):
            false_reject += 1

    accepted_correct = sum(1 for d in accepted if d.get("gold_correct"))
    return {
        "n": n,
        "raw_accuracy": _rate(sum(1 for d in decisions.values() if d.get("gold_correct")), n),
        "accepted_accuracy": _rate(accepted_correct, len(accepted)),
        "coverage": _rate(len(accepted), n),
        "abstained_rate": _rate(abstained, n),
        "rejected_rate": _rate(rejected, n),
        "false_accept_rate": _rate(false_accept, len(accepted)),
        "false_reject_rate": _rate(false_reject, max(n - abstained, 1)),
        "selective_accuracy": _rate(accepted_correct, n),
    }


def aggregate(records: list[dict]) -> dict:
    by_item = load_decisions(records)
    out: dict[str, Any] = {}
    for arm in ("A", "B", "C", "D1", "D2"):
        if any(arm in v for v in by_item.values()):
            out[arm] = summarize_arm(by_item, arm)

    def sel(name):
        return out.get(name, {}).get("selective_accuracy", 0.0)

    out["_marginal"] = {
        "A_to_B": round(sel("B") - sel("A"), 4),
        "B_to_C": round(sel("C") - sel("B"), 4),
        "C_to_D1": round(sel("D1") - sel("C"), 4),
    }
    out["_unique_catches"] = _unique_catches(by_item)
    return out


def _unique_catches(by_item: dict) -> dict:
    """How many wrong answers each layer caught that the previous one missed."""
    catches = {"B_caught": 0, "C_caught_beyond_B": 0, "D1_caught_beyond_C": 0}
    for iid, v in by_item.items():
        a = v.get("A", {})
        if not a.get("gold_correct"):
            continue  # only count catching actually-correct answers wrongly accepted
    # count wrong items that B rejects but A accepted (A had no structure, so
    # A "accepted" all non-abstain). Compare accepted-correctness.
    for iid, v in by_item.items():
        a = v.get("A", {})
        a_correct = bool(a.get("gold_correct"))
        b = v.get("B", {})
        c = v.get("C", {})
        d1 = _d1_decision(v["D1"]) if "D1" in v else {}
        if b.get("accepted") and not a_correct:
            catches["B_caught"] += 1
        if c.get("accepted") and b.get("accepted") and not a_correct:
            catches["C_caught_beyond_B"] += 1
    return catches


def per_task(records: list[dict]) -> dict:
    by: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for rec in records:
        key = rec.get("task") or "finqa"
        by[rec["arm"]][key].append(rec)
    out: dict = {}
    for arm, tasks in by.items():
        out[arm] = {}
        for t, items in tasks.items():
            acc = [r for r in items if r["arm_result"].get("accepted")]
            out[arm][t] = {
                "n": len(items),
                "coverage": _rate(len(acc), len(items)),
                "accepted_accuracy": _rate(
                    sum(1 for r in acc if r["arm_result"].get("gold_correct")), len(acc)),
            }
    return out
