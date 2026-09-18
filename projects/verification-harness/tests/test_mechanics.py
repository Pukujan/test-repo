"""Mechanics tests for the FinQA executor, mock determinism, and arm authority."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness import arms, finqa_program, mock, record as R, schemas as S  # noqa: E402


def test_parse_number_variants():
    assert finqa_program.parse_number("86,842,000") == 86842000.0
    assert finqa_program.parse_number("9%") == 0.09
    assert finqa_program.parse_number("$1,234.5") == 1234.5
    assert finqa_program.parse_number("total assets") is None


def test_execute_chained_program():
    val, reason = finqa_program.execute_program("subtract(5829, 5735), divide(#0, 5735)")
    assert reason == "ok"
    assert abs(val - 94 / 5735) < 1e-9


def test_execute_const_and_percent():
    val, reason = finqa_program.execute_program("subtract(224.65, const_100), divide(#0, const_100)")
    assert reason == "ok"
    assert abs(val - 1.2465) < 1e-9


def test_execute_failures_are_codes_not_crashes():
    assert finqa_program.execute_program("divide(1, 0)")[1] == "div_by_zero"
    assert finqa_program.execute_program("frobnicate(1, 2)")[1].startswith("unknown_op")
    assert finqa_program.execute_program("add(total assets, 1)")[1].startswith("unresolved_arg")
    assert finqa_program.execute_program("")[1] == "parse_error"
    assert finqa_program.execute_program("add(1, #5)")[1].startswith("bad_reference")


def test_mock_is_deterministic():
    gi = R.load_gold_index()
    items = list(gi.keys())[:5]
    for iid in items:
        a = mock.mock_response(iid, "B", gi)
        b = mock.mock_response(iid, "B", gi)
        assert a == b, iid


def test_mock_responses_are_well_shaped():
    gi = R.load_gold_index()
    for iid in list(gi.keys())[:20]:
        resp = mock.mock_response(iid, "B", gi)
        assert R.validate_response_shape(resp) == []


def test_arm_B_does_not_consult_gold_for_validity():
    """A correct-but-unsupported legal answer is rejected on evidence grounding,
    NOT accepted just because gold would say so."""
    gi = R.load_gold_index()
    legal_iid = next(k for k in gi if "#" in k)
    visible = {"task": "x", "question": "the quick brown fox clause applies here"}
    structured = {"label": "Yes", "facts": ["f"], "rules": ["r"],
                  "cited_spans": ["ZZZ not present at all"], "uncertain_fields": []}
    gold = {"answer": "Yes"}  # gold would say the label is right
    verdict = arms.run_arm_B(
        {"item_id": legal_iid, "raw_answer": "Yes", "structured": structured,
         "abstained": False, "meta": {}},
        visible, gold)
    assert verdict["accepted"] is False  # grounding failure despite correct label
    assert "no_grounded_cited_span" in (verdict.get("deterministic_rejection_reason") or "")


def test_arm_C_provides_counterexample_on_answer_program_mismatch():
    gi = R.load_gold_index()
    finqa_iid = next(k for k in gi if "#" not in k)
    visible = {"question": "q", "table": []}
    structured = {"answer": "999", "program": "subtract(10, 4)", "supporting_facts": ["x"]}
    res = arms.run_arm_C(
        {"item_id": finqa_iid, "raw_answer": "999", "structured": structured,
         "abstained": False, "meta": {}},
        visible, {"answer": "6", "exe_ans": 6.0}, S.UNAVAILABLE)
    assert res["accepted"] is False
    assert res["counterexample"] is not None


def test_arm_D2_unavailable_when_symai_missing():
    res = arms.run_arm_D2({"item_id": "x"}, {}, {}, symai_status=S.UNAVAILABLE)
    assert res["status"] == S.UNAVAILABLE
