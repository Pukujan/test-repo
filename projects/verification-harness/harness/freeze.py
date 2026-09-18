"""Freeze real benchmark data: acquisition digest, deterministic sample, and
gold/visible separation.

Run from the experiment directory. Raw bytes are read from gitignored
`local_data/`; committed artifacts (`inputs/dataset-lock.json`,
`inputs/sample-manifest.json`) contain pinned revisions, selected IDs, and
model-visible digests but NO gold. Gold is written only to gitignored
`gold_index/gold.json` for post-inference scoring.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from . import schemas as S

EXPERIMENT_DIR = Path(__file__).resolve().parents[1] / "experiments" / (
    "2026-09-18_real-data-abcd-verification"
)

FINQA_N = 50
LEGAL_PER_TASK = 10  # 5 tasks * 10 = 50 legal items


def _digest_order(seed: int, key: str) -> str:
    """Stable pseudo-random ordering, independent of Python RNG version."""
    return hashlib.sha256(f"{seed}:{key}".encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _visible_for_finqa(row: dict) -> dict:
    return {
        "id": row["id"],
        "question": row["qa"]["question"],
        "pre_text": row.get("pre_text", []),
        "post_text": row.get("post_text", []),
        "table": row.get("table", []),
    }


def _visible_for_legal(task: str, meta: dict, row: dict) -> dict:
    qcol = meta.get("question_column", "text")
    return {
        "task": task,
        "task_family": meta["family"],
        "index": row.get("index"),
        "question": row.get(qcol, ""),
    }


def load_finqa(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    items = []
    for row in rows:
        qa = row["qa"]
        if not str(qa.get("program", "")).strip():
            continue  # FinQA test items always carry a gold program; skip none expected
        items.append({
            "dataset": "finqa",
            "item_id": str(row["id"]),
            "visible": _visible_for_finqa(row),
            "gold": {
                "answer": qa.get("answer"),
                "program": qa.get("program"),
                "exe_ans": qa.get("exe_ans"),
                "gold_inds": qa.get("gold_inds", {}),
                "ann_table_rows": qa.get("ann_table_rows", []),
                "ann_text_rows": qa.get("ann_text_rows", []),
            },
        })
    return items


def load_legal(path: Path, task: str) -> list[dict]:
    meta = S.LEGAL_TASKS[task]
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        items = []
        for row in reader:
            vis = _visible_for_legal(task, meta, row)
            items.append({
                "dataset": "legalbench",
                "task": task,
                "item_id": f"{task}#{row.get('index')}",
                "visible": vis,
                "gold": {"answer": row.get("answer")},
            })
    return items


def _sample(items: list[dict], n: int) -> list[dict]:
    ranked = sorted(items, key=lambda it: _digest_order(S.SAMPLE_SEED, it["item_id"]))
    return ranked[:n]


def freeze(exp_dir: Path = EXPERIMENT_DIR) -> dict:
    local = exp_dir / "local_data"
    lock_dir = exp_dir / "inputs"
    lock_dir.mkdir(exist_ok=True)

    finqa_path = local / "finqa_test.json"
    legal_paths = {task: local / "legal" / f"{task}_test.tsv" for task in S.LEGAL_TASKS}

    finqa_items = load_finqa(finqa_path)
    legal_items = []
    for task, path in legal_paths.items():
        legal_items.extend(load_legal(path, task))

    finqa_sample = _sample(finqa_items, FINQA_N)
    legal_sample = []
    for task in S.LEGAL_TASKS:
        task_items = [it for it in legal_items if it["task"] == task]
        legal_sample.extend(_sample(task_items, LEGAL_PER_TASK))

    manifest = {
        "schema_version": "vh.sample-manifest.v1",
        "sample_seed": S.SAMPLE_SEED,
        "counts": {
            "finqa": len(finqa_sample),
            "legal": len(legal_sample),
            "legal_by_task": {t: sum(1 for it in legal_sample if it["task"] == t) for t in S.LEGAL_TASKS},
        },
        "selection_method": "rank items by sha256(f'{seed}:{item_id}') and take top N (version-stable)",
        "items": [],
    }
    gold_index: dict[str, dict] = {}
    for it in finqa_sample + legal_sample:
        vis_digest = S.item_digest(it["visible"])
        manifest["items"].append({
            "dataset": it["dataset"],
            "task": it.get("task"),
            "item_id": it["item_id"],
            "visible_digest": vis_digest,
        })
        gold_index[it["item_id"]] = {"visible": it["visible"], "gold": it["gold"]}

    lock = {
        "schema_version": "vh.dataset-lock.v1",
        "created_at": "2026-09-18T12:00:00Z",
        "note": "Raw bytes are pinned by digest here but are NOT committed (public repo, license, and gold-separation). Re-download from pinned revisions, verify digests, then regenerate the sample.",
        "datasets": {
            "finqa": {
                "upstream_repository": "https://github.com/czyssrs/FinQA",
                "upstream_revision": "0f16e2867befa6840783e58be38c9efb9229d742",
                "file": "dataset/test.json",
                "acquisition": "git archive at the pinned revision; raw bytes to local_data/finqa_test.json",
                "sha256": _file_digest(finqa_path),
                "split": "public test",
                "fidelity": "verbatim",
                "completeness": "complete",
            },
            "legalbench": {
                "upstream_repository": "https://huggingface.co/datasets/nguha/legalbench",
                "upstream_revision": "daec8237410aa23e3faf4bc41ad8b3a7e1696826",
                "acquisition": "hf resolve at the pinned revision per task test.tsv; raw bytes to local_data/legal/",
                "tasks": {
                    task: {
                        "file": f"data/{task}/test.tsv",
                        "sha256": _file_digest(legal_paths[task]),
                        "split": "test",
                        "labels": "Yes/No (binary) or MC (rule_qa)",
                        "fidelity": "verbatim",
                        "completeness": "complete",
                    }
                    for task in S.LEGAL_TASKS
                },
            },
        },
    }

    (lock_dir / "dataset-lock.json").write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (lock_dir / "sample-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gold_dir = exp_dir / "gold_index"
    gold_dir.mkdir(exist_ok=True)
    (gold_dir / "gold.json").write_text(
        json.dumps(gold_index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {"lock": lock, "manifest": manifest, "gold_count": len(gold_index)}


if __name__ == "__main__":
    result = freeze()
    print(json.dumps({"counts": result["manifest"]["counts"], "gold_items": result["gold_count"]}, indent=2))
