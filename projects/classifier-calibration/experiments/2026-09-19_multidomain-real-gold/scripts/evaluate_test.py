#!/usr/bin/env python3
"""EVAL-001/002 + OBS-001: score both systems on the same frozen test ids.

Teacher and Potion are FIXED before this script runs; test gold is scoring-only.
Writes:
  gitignored  runs/<run>/preds/test_preds_{qwen,potion}.jsonl  (per-row gold+text-free preds)
  committed   runs/<run>/eval/eval_summary.json                (aggregates only)
  committed   runs/<run>/observability_reconciliation.json     (counts, no text/gold)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import metrics as M

import argparse

import joblib
from model2vec import StaticModel
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

RUN = "run-20260919-mdrg-001"
LETTERS = ["A", "B", "C", "D"]


def load_teacher(run, split):
    p = common.RUNS / run / "teacher" / f"teacher_labels_{split}.jsonl"
    best = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["sample_id"] not in best or (best[r["sample_id"]]["status"] != "ok" and r["status"] == "ok"):
            best[r["sample_id"]] = r
    return best


def per_class_block(y, pred, probs):
    micro_p, micro_r, micro_f, _ = precision_recall_fscore_support(
        y, pred, average="micro", zero_division=0)
    per = {}
    for i, d in enumerate(common.DOMAINS):
        p_, r_, f_, s_ = precision_recall_fscore_support(
            y, pred, labels=[i], average=None, zero_division=0)
        per[d] = {"precision": round(float(p_[0]), 6), "recall": round(float(r_[0]), 6),
                  "f1": round(float(f_[0]), 6), "support": int(s_[0])}
    macro_p, macro_r, macro_f, _ = precision_recall_fscore_support(
        y, pred, average="macro", zero_division=0)
    cm = confusion_matrix(y, pred, labels=list(range(len(common.DOMAINS)))).tolist()
    return {
        "accuracy": round(float((pred == y).mean()), 6),
        "macro_f1": round(float(macro_f), 6),
        "micro_f1": round(float(micro_f), 6),
        "per_class": per,
        "confusion_matrix_rows_true": cm,
        "confusion_labels": common.DOMAINS,
        "log_loss": round(M.log_loss(y, probs), 6),
        "brier": round(M.brier(y, probs), 6),
        "ece": round(M.expected_calibration_error(y, probs), 6),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=RUN)
    args = ap.parse_args()
    run = args.run_id

    train_rows, cal_rows, test_rows = common.assert_contract()
    gold_idx = {d: i for i, d in enumerate(common.DOMAINS)}
    tt = load_teacher(run, "test")
    provider_errors = len([r for r in test_rows if r["id"] in tt and tt[r["id"]]["status"] != "ok"])

    cal_sum = json.loads((common.RUNS / run / "calibration" / "calibration_summary.json")
                         .read_text(encoding="utf-8"))
    T_qwen = cal_sum["cal001_teacher_temperature"]["temperature"]
    T_potion = cal_sum["pot002_potion_temperature"]["temperature"]

    y = np.array([gold_idx[r["domain"]] for r in test_rows])

    # teacher probs (calibrated with the calibration-fit temperature)
    q_rows, q_probs = [], []
    for r in test_rows:
        rec = tt.get(r["id"])
        if rec and rec["status"] == "ok" and rec["valid_output"]:
            lg = np.array([common.teacher_logit_vector(rec["label_logprobs"])])
            q_probs.append(M.softmax(lg, T_qwen)[0])
            q_rows.append(r["id"])
        else:
            q_probs.append(np.full(4, np.nan))
            q_rows.append(r["id"])
    q_probs = np.vstack(q_probs)
    q_mask = ~np.isnan(q_probs[:, 0])

    md = common.EXP / "models" / run
    model = StaticModel.from_pretrained(str(md / "potion-base"))
    X_te = model.encode([r["text"] for r in test_rows])
    clf = joblib.load(md / "potion_lr.joblib")
    p_logits = clf.decision_function(X_te)
    p_probs = M.softmax(p_logits, T_potion)

    assert q_mask.all(), f"teacher rows missing for {int((~q_mask).sum())} test ids"

    pd_ = common.RUNS / run / "preds"
    pd_.mkdir(exist_ok=True)
    with (pd_ / "test_preds_qwen.jsonl").open("w", encoding="utf-8") as fh:
        for r, pr in zip(test_rows, q_probs):
            fh.write(json.dumps({"sample_id": r["id"], "gold_domain": r["domain"],
                                 "pred_domain": common.DOMAINS[int(pr.argmax())],
                                 "probs": {d: round(float(pr[i]), 6) for i, d in enumerate(common.DOMAINS)}},
                                sort_keys=True) + "\n")
    with (pd_ / "test_preds_potion.jsonl").open("w", encoding="utf-8") as fh:
        for r, pr in zip(test_rows, p_probs):
            fh.write(json.dumps({"sample_id": r["id"], "gold_domain": r["domain"],
                                 "pred_domain": common.DOMAINS[int(pr.argmax())],
                                 "probs": {d: round(float(pr[i]), 6) for i, d in enumerate(common.DOMAINS)}},
                                sort_keys=True) + "\n")

    q_eval = per_class_block(y, q_probs.argmax(axis=1), q_probs)
    p_eval = per_class_block(y, p_probs.argmax(axis=1), p_probs)

    # per-source breakdown (aggregate; source names stay local/gitignored in per-row file)
    src_of = {}
    for s in common.TEST_SOURCES:
        for line in (common.RAW / f"test_{s}.jsonl").read_text(encoding="utf-8").splitlines():
            src_of[json.loads(line)["id"]] = s

    def by_source(probs):
        out = {}
        srcs = [src_of[r["id"]] for r in test_rows]
        for s in sorted(set(srcs)):
            m = np.array([sid == s for sid in srcs])
            dom = common.DOMAIN_BY_TEST[s]
            pred = probs[m].argmax(axis=1)
            yy = y[m]
            out[s] = {"domain": dom, "n": int(m.sum()),
                      "accuracy": round(float((pred == yy).mean()), 6)}
        return out

    q_uncal_logits = np.vstack([common.teacher_logit_vector(tt[r["id"]]["label_logprobs"])
                                for r in test_rows])
    summary = {
        "schema_version": "mdrg.eval.v1",
        "run_id": run, "dataset_version": "seed-20260919",
        "test_ids": sorted(r["id"] for r in test_rows),
        "n_test_rows": len(test_rows),
        "frozen_contract_gate": "assert_contract() passed; both systems fixed before test gold scored",
        "teacher_prompt_version": tt[test_rows[0]["id"]].get("prompt_version"),
        "temperature_used": {"qwen": T_qwen, "potion": T_potion},
        "qwen_teacher_calibrated": q_eval,
        "qwen_teacher_uncalibrated": per_class_block(
            y, M.softmax(q_uncal_logits, 1.0).argmax(axis=1), M.softmax(q_uncal_logits, 1.0)),
        "potion_calibrated": p_eval,
        "qwen_by_test_source": by_source(q_probs),
        "potion_by_test_source": by_source(p_probs),
        "provider_errors_test": provider_errors,
        "substitutions": 0,
    }
    outd = common.RUNS / run / "eval"
    outd.mkdir(exist_ok=True)
    (outd / "eval_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                            encoding="utf-8")

    # ---- OBS-001: reconcile expected vs completed rows/ids/events/traces ----
    events = [json.loads(l) for l in (common.RUNS / run / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    traces = [json.loads(l) for l in (common.RUNS / run / "otel_traces.jsonl").read_text(encoding="utf-8").splitlines()]
    teacher_all = load_teacher(run, "train"), load_teacher(run, "calibration"), load_teacher(run, "test")
    reconc = {"schema_version": "mdrg.obs.v1", "run_id": run, "splits": {}}
    for split, recs in zip(["train", "calibration", "test"], teacher_all):
        rows = {"train": train_rows, "calibration": cal_rows, "test": test_rows}[split]
        exp = {r["id"] for r in rows}
        got = set(recs.keys())
        ok = {k for k, v in recs.items() if v["status"] == "ok"}
        reconc["splits"][split] = {
            "expected_rows": len(exp), "unique_ids_logged": len(got),
            "ok_rows": len(ok), "error_rows": len(got - ok),
            "missing_ids": len(exp - got), "unexpected_ids": len(got - exp),
            "events_logged": sum(1 for e in events if e.get("split") == split),
            "traces_logged": sum(1 for t in traces if t.get("resource", {}).get("phase") == split),
            "ids_unique": len(got) == len(set(got))
        }
    reconc["events_total"] = len(events)
    reconc["traces_total"] = len(traces)
    reconc["consistent"] = all(
        v["expected_rows"] == v["unique_ids_logged"] == v["ok_rows"]
        and v["events_logged"] == v["ok_rows"] and v["traces_logged"] == v["ok_rows"]
        and v["missing_ids"] == 0 and v["unexpected_ids"] == 0
        for v in reconc["splits"].values())
    (common.RUNS / run / "observability_reconciliation.json").write_text(
        json.dumps(reconc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"n_test_rows": len(test_rows),
                      "qwen_acc": q_eval["accuracy"], "qwen_macro_f1": q_eval["macro_f1"],
                      "qwen_ece_post": q_eval["ece"],
                      "potion_acc": p_eval["accuracy"], "potion_macro_f1": p_eval["macro_f1"],
                      "potion_ece_post": p_eval["ece"],
                      "obs_consistent": reconc["consistent"]}, indent=2))


if __name__ == "__main__":
    main()
