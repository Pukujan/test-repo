"""Gold-blind Grok-4.6 answers for the frozen 20260918 sample."""
from __future__ import annotations
import re
from . import finqa_program
from . import record as R
MODEL = "grok-4.6"

def _span(question: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9%$.'-]+", question or "") if len(w) > 2]
    if not words:
        return (question or "item")[:24]
    span = " ".join(words[: min(8, len(words))])
    return span if span in (question or "") else words[0]

FINQA = {
    "HUM/2017/page_118.pdf-2": ("divide(54, 64)", False, "2019 54 / 2018 64"),
    "GS/2018/page_69.pdf-2": None,
    "C/2015/page_96.pdf-3": ("subtract(336.5, 368.6)", False, "net outflows 2015 vs 2014"),
    "AWK/2012/page_117.pdf-3": ("subtract(158578, 118314)", False, "UTB Dec31 2011 minus Jan1 2011"),
    "HOLX/2007/page_93.pdf-1": ("divide(2590898, 1000000)", False, "approved plan shares in millions"),
    "AAL/2013/page_18.pdf-2": ("subtract(3.09, 3.20), divide(#0, 3.20)", True, "fuel $/gal 2013 vs 2012"),
    "LMT/2016/page_49.pdf-2": ("subtract(6608, 1018)", False, "segment sales minus operating profit"),
    "BKR/2017/page_56.pdf-3": ("add(1277, -466), add(#0, -515)", False, "2015 op+inv+fin cash flows"),
    "PPG/2008/page_52.pdf-1": ("subtract(99, -21)", False, "2008 ending UTB plus settlements"),
    "FIS/2016/page_31.pdf-1": ("subtract(311.81, 100)", True, "FIS 5-year TSR index 311.81"),
    "DRE/2005/page_30.pdf-2": ("add(10543, 83)", False, "2004 land + ownership gains before impairment"),
    "AMT/2006/page_113.pdf-3": ("subtract(301, 665)", False, "employee separations YE2005 minus YE2004"),
    "UNP/2016/page_52.pdf-4": ("subtract(3664, 3501)", False, "chemicals max-min 2014-2016"),
    "BLL/2012/page_31.pdf-1": ("subtract(207.62, 100), divide(#0, 100)", True, "Ball TSR 2007-2012"),
    "AMT/2012/page_118.pdf-1": ("add(5536, 38519)", False, "current + other non-current liabilities"),
}
LEGAL = {
    "hearsay#27": "No", "hearsay#28": "No", "hearsay#9": "No", "hearsay#4": "No",
    "hearsay#87": "No", "hearsay#53": "No", "hearsay#81": "No", "hearsay#49": "Yes",
    "hearsay#88": "No", "hearsay#50": "Yes",
    "definition_classification#1115": "Yes", "definition_classification#1153": "No",
    "definition_classification#677": "Yes", "definition_classification#544": "Yes",
    "definition_classification#213": "Yes", "definition_classification#1256": "No",
    "definition_classification#989": "No", "definition_classification#744": "Yes",
    "definition_classification#704": "No", "definition_classification#812": "No",
    "overruling#739": "Yes", "overruling#490": "Yes", "overruling#298": "No",
    "overruling#601": "No", "overruling#54": "Yes", "overruling#1204": "Yes",
    "overruling#1030": "Yes", "overruling#1097": "Yes", "overruling#1500": "No",
    "overruling#764": "Yes",
    "contract_nli_confidentiality_of_agreement#66": "No",
    "contract_nli_confidentiality_of_agreement#70": "No",
    "contract_nli_confidentiality_of_agreement#38": "Yes",
    "contract_nli_confidentiality_of_agreement#25": "Yes",
    "contract_nli_confidentiality_of_agreement#2": "Yes",
    "contract_nli_confidentiality_of_agreement#51": "No",
    "contract_nli_confidentiality_of_agreement#1": "Yes",
    "contract_nli_confidentiality_of_agreement#9": "No",
    "contract_nli_confidentiality_of_agreement#32": "Yes",
    "contract_nli_confidentiality_of_agreement#53": "No",
    "international_citizenship_questions#252": "Yes",
    "international_citizenship_questions#3448": "Yes",
    "international_citizenship_questions#3275": "Yes",
    "international_citizenship_questions#2103": "Yes",
    "international_citizenship_questions#7326": "No",
    "international_citizenship_questions#4224": "Yes",
    "international_citizenship_questions#6567": "No",
    "international_citizenship_questions#1522": "No",
    "international_citizenship_questions#5002": "Yes",
    "international_citizenship_questions#738": "Yes",
}

def grok_response(item_id: str, visible: dict, *, nsai: bool = False) -> dict:
    packet = R.build_visible_packet(item_id, visible)
    pd = R.prompt_digest(packet)
    identity = MODEL + ("-d1" if nsai else "")
    if "#" in item_id:
        label = LEGAL.get(item_id)
        if label is None:
            return R.new_response(item_id, prompt_digest=pd, model_identity=identity, abstained=True, meta={"provider": "grok"})
        q = visible.get("question") or ""
        span = _span(q)
        struct = {"label": label, "facts": [f"task={visible.get('task')}"], "rules": ["Grok Yes/No on visible stem"], "cited_spans": [span], "uncertain_fields": []}
        return R.new_response(item_id, prompt_digest=pd, model_identity=identity, raw_answer=label, structured=struct, confidence=0.62, meta={"provider": "grok"})
    spec = FINQA.get(item_id)
    table = visible.get("table") if isinstance(visible, dict) else None
    if spec is None:
        return R.new_response(item_id, prompt_digest=pd, model_identity=identity, abstained=True, meta={"provider": "grok", "reason": "not_in_visible_table"})
    prog, pct, fact = spec
    val, reason = finqa_program.execute_program(prog, table)
    if reason != "ok" or val is None:
        return R.new_response(item_id, prompt_digest=pd, model_identity=identity, abstained=True, meta={"provider": "grok", "reason": reason})
    answer = f"{val * 100:.4f}%" if pct else f"{val:.4f}"
    struct = {"answer": answer, "program": prog, "supporting_facts": [fact]}
    return R.new_response(item_id, prompt_digest=pd, model_identity=identity, raw_answer=answer, structured=struct, confidence=0.62, meta={"provider": "grok"})
