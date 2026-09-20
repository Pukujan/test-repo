#!/usr/bin/env python3
"""CAL-001 + POT-001 + POT-002, before the test split is touched.

- CAL-001: temperature-scale the Qwen teacher on the calibration split ONLY
  (calibration gold = source membership, per gold_policy.md). Pre/post log-loss,
  Brier, ECE recorded.
- POT-001: Potion (minishlab/potion-base-32M embeddings + LogisticRegression)
  trained on Qwen TEACHER labels of the train split — never real gold.
- POT-002: Potion temperature scaling fit on the calibration split only.

The test split is NOT loaded here. Model artifacts + per-row predictions stay
gitignored; only aggregate numbers are written to the committed summary.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import metrics as M

import argparse

import joblib
from model2vec import StaticModel

POTION_BASE = "minishlab/potion-base-32M"
LR_C = 50.0
LETTERS = ["A", "B", "C", "D"]
RUN = "run-20260919-mdrg-001"


def load_teacher(run, split):
    p = common.RUNS / run / "teacher" / f"teacher_labels_{split}.jsonl"
    best = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        key = r["sample_id"]
        if key not in best or (best[key]["status"] != "ok" and r["status"] == "ok"):
            best[key] = r
    return best


def teacher_logits(rec):
    return np.array(common.teacher_logit_vector(rec["label_logprobs"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=RUN)
    args = ap.parse_args()
    run = args.run_id
    train_rows, cal_rows, test_rows = common.assert_contract()
    assert len(test_rows) > 0
    tt = load_teacher(run, "train")
    tc = load_teacher(run, "calibration")
    tr_ok = [r for r in train_rows if tt[r["id"]]["status"] == "ok" and tt[r["id"]]["valid_output"]]
    cal_ok = [r for r in cal_rows if tc[r["id"]]["status"] == "ok" and tc[r["id"]]["valid_output"]]
    assert len(tr_ok) == len(train_rows), f"train teacher labels incomplete: {len(tr_ok)}/{len(train_rows)}"
    assert len(cal_ok) == len(cal_rows), f"cal teacher labels incomplete: {len(cal_ok)}/{len(cal_rows)}"

    gold_idx = {d: i for i, d in enumerate(common.DOMAINS)}

    # ---- CAL-001: teacher temperature scaling on calibration only ----
    cal_logits = np.vstack([teacher_logits(tc[r["id"]]) for r in cal_ok])
    cal_gold = np.array([gold_idx[r["domain"]] for r in cal_ok])
    pre = M.metric_block(cal_gold, M.softmax(cal_logits, 1.0))
    T_qwen = M.fit_temperature(cal_logits, cal_gold)
    post = M.metric_block(cal_gold, M.softmax(cal_logits, T_qwen))
    teacher_cal_acc_vs_membership = pre["accuracy"]
    teacher_cal_agree_post = post["accuracy"]

    # ---- POT-001: Potion on TEACHER labels only ----
    model = StaticModel.from_pretrained(POTION_BASE)
    X_tr = model.encode([r["text"] for r in tr_ok])
    y_tr_teacher = np.array([gold_idx[tt[r["id"]]["teacher_domain"]] for r in tr_ok])
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(C=LR_C, max_iter=1000, random_state=common.SEED)
    clf.fit(X_tr, y_tr_teacher)

    # ---- POT-002: Potion temperature on calibration split only ----
    X_cal = model.encode([r["text"] for r in cal_ok])
    cal_logits_p = clf.decision_function(X_cal)
    pre_p = M.metric_block(cal_gold, M.softmax(cal_logits_p, 1.0))
    T_potion = M.fit_temperature(cal_logits_p, cal_gold)
    post_p = M.metric_block(cal_gold, M.softmax(cal_logits_p, T_potion))

    import model2vec, sklearn, sklearn.linear_model
    md = common.EXP / "models" / run
    md.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(md / "potion-base"))
    joblib.dump(clf, md / "potion_lr.joblib")

    import subprocess
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                            cwd=common.EXP).stdout.strip()

    summary = {
        "schema_version": "mdrg.calibration-potion.v1",
        "run_id": run,
        "dataset_version": "seed-20260919",
        "frozen_contract_gate": "assert_contract() passed before any artifact was written; test split not loaded",
        "cal001_teacher_temperature": {
            "split": "calibration", "n": len(cal_ok),
            "temperature": round(T_qwen, 6),
            "pre": pre, "post": post,
            "teacher_vs_source_membership_agreement_cal_pre": teacher_cal_acc_vs_membership,
            "note": "logprobs at temp 0 used as logits; T fit by golden-section NLL on calibration gold only"
        },
        "pot001_potion_train": {
            "embedding_model": POTION_BASE,
            "classifier": {"type": "LogisticRegression", "C": LR_C, "max_iter": 1000,
                           "random_state": common.SEED},
            "train_target": "Qwen3.8-flash teacher labels (never real gold)",
            "n_train_rows": len(tr_ok),
            "teacher_label_distribution_on_train": {
                d: int((y_tr_teacher == i).sum()) for i, d in enumerate(common.DOMAINS)},
            "train_agreement_teacher_vs_source_membership": round(
                float((y_tr_teacher == np.array([gold_idx[r["domain"]] for r in tr_ok])).mean()), 6)
        },
        "pot002_potion_temperature": {
            "split": "calibration", "n": len(cal_ok), "temperature": round(T_potion, 6),
            "pre": pre_p, "post": post_p
        },
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": np.__version__, "sklearn": sklearn.__version__,
            "model2vec": model2vec.__version__, "git_commit": commit
        },
        "artifact_paths_gitignored": ["models/", "runs/**/preds/", "runs/**/teacher/"],
    }
    out = common.RUNS / run / "calibration"
    out.mkdir(exist_ok=True)
    (out / "calibration_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                                  encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("cal001_teacher_temperature", "pot002_potion_temperature")},
                     indent=2))
    print("wrote", out / "calibration_summary.json", "and models/")


if __name__ == "__main__":
    main()
