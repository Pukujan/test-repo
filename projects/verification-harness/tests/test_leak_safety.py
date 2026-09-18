"""Leak-safety tests: model-visible packets and prompts must never expose gold."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness import prompt_io, record as R, schemas as S  # noqa: E402

BANNED_VISIBLE_KEYS = set(S.GOLD_FIELDS_FINQA) | set(S.GOLD_FIELDS_LEGAL)


def _items_and_gold():
    gi = R.load_gold_index()
    manifest = json.loads((R.EXPERIMENT_DIR / "inputs" / "sample-manifest.json").read_text(encoding="utf-8"))
    items = [it["item_id"] for it in manifest["items"]]
    return items, gi


def test_build_visible_packet_has_no_gold_keys():
    items, gi = _items_and_gold()
    for iid in items:
        packet = R.build_visible_packet(iid, gi[iid]["visible"])
        leaked = BANNED_VISIBLE_KEYS & set(packet.keys())
        assert not leaked, (iid, leaked)


def test_build_visible_packet_has_no_gold_values():
    items, gi = _items_and_gold()
    for iid in items:
        gold = gi[iid]["gold"]
        text = json.dumps(R.build_visible_packet(iid, gi[iid]["visible"]), ensure_ascii=False)
        for v in (gold.get("answer"), gold.get("exe_ans"), gold.get("program")):
            if v is None:
                continue
            sval = str(v).strip()
            if len(sval) >= 6:  # short numeric gold can coincidentally match table cells
                assert sval not in text, (iid, sval[:30])


def test_guard_packet_rejects_gold_key():
    try:
        R.guard_packet({"item_id": "x", "answer": "42"}, "x")
    except R.LeakError:
        return
    raise AssertionError("guard_packet did not reject a gold key")


def test_exported_prompt_files_have_no_gold(tmp_path):
    items, gi = _items_and_gold()
    out = tmp_path / "luna"
    prompt_io.export_prompts(items, gi, out)
    for iid in items:
        text = (out / f"{prompt_io._safe(iid)}.json").read_text(encoding="utf-8")
        low = text.lower()
        for token in ("\"answer\"", "exe_ans", "gold_inds", "\"program\":"):
            assert token not in low, (iid, token)


def test_manifest_has_no_gold():
    m = (R.EXPERIMENT_DIR / "inputs" / "sample-manifest.json").read_text(encoding="utf-8").lower()
    assert "exe_ans" not in m
    assert "program" not in m
    assert "\"answer\"" not in m
