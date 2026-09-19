#!/usr/bin/env python3
"""Real OpenCode-accessible generative LLM classification (qwen3.8-flash / yolo-auto).

Hard rule: real or unavailable, never substitute. No fallback path exists here.
A provider error is recorded as an error for that sample; it never becomes
TF-IDF, logistic regression, a mock, or a heuristic.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parents[1]
FIXTURE = EXP_DIR / "inputs/fixtures/synthetic_topics_v1.jsonl"
SPLIT = EXP_DIR / "inputs/fixtures/split_manifest.json"

PROVIDER = "yolo-auto"
BASE_URL = "https://yolo-auto.com/v1/chat/completions"
EXPERIMENT_ID = "classifier-calibration-2026-09-19-real-opencode-llm-classifier"
DATASET_VERSION = "synthetic-topics-v1"
PROMPT_VERSION = "real-letters-v1"
SEED = 20260919
LANGFUSE_STATUS = "unavailable"

LABELS = ["sports", "technology", "politics", "health"]
LETTER_TO_LABEL = {"A": "sports", "B": "technology", "C": "politics", "D": "health"}
LABEL_TO_LETTER = {v: k for k, v in LETTER_TO_LABEL.items()}
LETTER_IDS = list(LETTER_TO_LABEL.keys())

PROMPT_SYSTEM = (
    "You are a strict single-label topic classifier. Choose exactly one letter: "
    "A=sports, B=technology, C=politics, D=health. "
    "Reply with exactly one capital letter (A, B, C, or D) and nothing else. "
    "No explanation, no punctuation, no spaces, no newline."
)


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def prompt_user(text: str) -> str:
    return f"Topic text:\n{text}\n\nAnswer:"


def http_post(payload: dict, api_key: str, timeout: int = 60, attempts: int = 3):
    body = json.dumps(payload).encode("utf-8")
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(
                BASE_URL, data=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                         "User-Agent": "classifier-bench/1.0"},
            )
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data, int((time.perf_counter() - t0) * 1000), i + 1
        except urllib.error.HTTPError as exc:
            last = exc
            if 400 <= exc.code < 500 and exc.code != 429:
                break
            time.sleep(1.0 * (i + 1))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"{type(last).__name__}: {last}")


def _assert_no_gold(messages, gold_label: str) -> None:
    blob = json.dumps(messages)
    if re.search(r'"label"\s*:', blob) or f'"{gold_label}"' in blob:
        raise AssertionError(f"leak guard tripped for gold={gold_label!r}")


def classify_sample(model: str, sample: dict, split: str, api_key: str, mode: str) -> dict:
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": prompt_user(sample["text"])},
    ]
    _assert_no_gold(messages, sample["label"])
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 1,
        "seed": SEED,
        "logprobs": True,
        "top_logprobs": 20,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    trace_id = uuid.uuid4().hex
    base = {
        "schema": "real-llm-prediction.v1",
        "sample_id": sample["sample_id"],
        "split": split,
        "gold_label": sample["label"],
        "model_id": model,
        "provider_id": PROVIDER,
        "invocation_path": BASE_URL,
        "prompt_version": PROMPT_VERSION,
        "trace_id": trace_id,
        "mode": mode,
    }
    try:
        data, latency, attempts = http_post(payload, api_key)
    except RuntimeError as exc:
        return {**base, "status": "error", "error": str(exc), "predicted_label": None,
                "valid_output": False, "label_logprobs": None, "score_coverage": "none",
                "timestamp": utcnow()}
    choice = data["choices"][0]
    stripped = (choice["message"].get("content") or "").strip()
    predicted = stripped if stripped in LETTER_IDS else None
    label_lp, coverage = None, "none"
    lp = choice.get("logprobs")
    have_lp = bool(lp and lp.get("content"))
    if have_lp:
        tok = lp["content"][0]
        m: dict[str, float] = {}
        if tok["token"].strip() in LETTER_IDS:
            m[tok["token"].strip()] = tok["logprob"]
        for t in tok.get("top_logprobs") or []:
            tk = t["token"].strip()
            if tk in LETTER_IDS and tk not in m:
                m[tk] = t["logprob"]
        if m:
            label_lp = {LETTER_TO_LABEL[l]: round(m[l], 6) for l in LETTER_IDS if l in m}
            coverage = "full" if len(m) == 4 else "partial"
    usage = data.get("usage") or {}
    rec = {**base, "status": "ok", "model_text": stripped[:8],
           "predicted_label": predicted, "valid_output": predicted is not None,
           "logprobs_available": have_lp, "label_logprobs": label_lp,
           "score_coverage": coverage, "provider_echo_model": data.get("model"),
           "latency_ms": latency, "prompt_tokens": usage.get("prompt_tokens"),
           "completion_tokens": usage.get("completion_tokens"),
           "total_tokens": usage.get("total_tokens"), "attempts": attempts,
           "timestamp": utcnow()}
    if mode == "smoke":
        rec["request_params"] = {k: v for k, v in payload.items() if k != "messages"}
        rec["response_content"] = choice["message"].get("content")
    return rec


def run_split(model, split_name, samples, api_key, mode):
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = [pool.submit(classify_sample, model, s, split_name, api_key, mode) for s in samples]
        for f in futs:
            rows.append(f.result())
    rows.sort(key=lambda r: r["sample_id"])
    return rows


def softmax(vec):
    mx = max(vec)
    ex = [math.exp(v - mx) for v in vec]
    s = sum(ex)
    return [v / s for v in ex]


def nll(probs, gold_idx):
    return -sum(math.log(max(p[g], 1e-12)) for p, g in zip(probs, gold_idx)) / max(1, len(probs))


def fit_temperature(vecs, gold_idx):
    def f(t):
        return nll([softmax([v / t for v in vec]) for vec in vecs], gold_idx)
    gr = (math.sqrt(5) - 1) / 2
    a, b = 0.05, 50.0
    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(80):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = f(d)
    return round((a + b) / 2, 4)


def ece(confs, correct_flags, bins=10):
    n_all = len(confs)
    if n_all == 0:
        return None
    buckets = [[] for _ in range(bins)]
    for c, ok in zip(confs, correct_flags):
        buckets[min(int(c * bins), bins - 1)].append((c, ok))
    e = 0.0
    for bucket in buckets:
        if bucket:
            avg_conf = sum(c for c, _ in bucket) / len(bucket)
            avg_acc = sum(1 for _, ok in bucket if ok) / len(bucket)
            e += (len(bucket) / n_all) * abs(avg_conf - avg_acc)
    return round(e, 6)


def classification_metrics(rows):
    done = [r for r in rows if r["status"] == "ok"]
    valid = [r for r in done if r["valid_output"]]
    n = len(done)
    correct = sum(1 for r in valid if LETTER_TO_LABEL[r["predicted_label"]] == r["gold_label"])
    confusion = {g: {p: 0 for p in LABELS} for g in LABELS}
    for r in valid:
        confusion[r["gold_label"]][LETTER_TO_LABEL[r["predicted_label"]]] += 1
    per_class, f1s = {}, []
    for lab in LABELS:
        tp = confusion[lab][lab]
        fp = sum(confusion[g][lab] for g in LABELS if g != lab)
        fn = sum(confusion[lab][p] for p in LABELS if p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per_class[lab] = {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4)}
        f1s.append(f1)
    lat = sorted(r["latency_ms"] for r in done if r.get("latency_ms") is not None)
    errs = len(rows) - n
    return {
        "n_rows": len(rows), "n_completed": n, "n_provider_errors": errs,
        "provider_error_rate": round(errs / len(rows), 4) if rows else None,
        "n_valid_output": len(valid),
        "invalid_output_rate": round((n - len(valid)) / n, 4) if n else None,
        "accuracy_over_completed": round(correct / n, 4) if n else None,
        "accuracy_over_valid": round(correct / len(valid), 4) if valid else None,
        "macro_f1": round(sum(f1s) / len(f1s), 4), "per_class": per_class,
        "confusion": confusion,
        "latency_ms_p50": lat[len(lat) // 2] if lat else None,
        "latency_ms_p95": lat[int(len(lat) * 0.95)] if lat else None,
        "total_tokens": sum(r.get("total_tokens") or 0 for r in done),
    }


def probability_metrics(rows, temperature):
    scored = [r for r in rows if r["status"] == "ok" and r.get("score_coverage") == "full"]
    if not scored:
        return {"scored_n": 0, "temperature": temperature, "log_loss": None,
                "brier": None, "ece": None,
                "partial_or_no_score_n": len([r for r in rows if r["status"] == "ok"])}
    vecs, gidx = [], []
    for r in scored:
        vecs.append([r["label_logprobs"][lab] for lab in LABELS])
        gidx.append(LABELS.index(r["gold_label"]))
    probs = [softmax([v / temperature for v in vec]) for vec in vecs]
    brier = 0.0
    confs, flags = [], []
    for p, gi in zip(probs, gidx):
        brier += sum((p[k] - (1 if k == gi else 0)) ** 2 for k in range(len(LABELS)))
        confs.append(max(p))
        flags.append(int(p.index(max(p)) == gi))
    return {"scored_n": len(scored),
            "partial_or_no_score_n": len([r for r in rows if r["status"] == "ok"]) - len(scored),
            "temperature": temperature, "log_loss": round(nll(probs, gidx), 4),
            "brier": round(brier / len(scored), 4), "ece": ece(confs, flags)}


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def load_fixtures_and_split():
    fixture = {}
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        obj = json.loads(line)
        fixture[obj["sample_id"]] = obj
    return fixture, json.loads(SPLIT.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "full"], required=True)
    ap.add_argument("--model", default="qwen3.8-flash")
    ap.add_argument("--run-id", default="run-20260919-real-001")
    ap.add_argument("--smoke-n", type=int, default=8)
    args = ap.parse_args()

    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("QWEN_API_KEY not set -> models would be marked unavailable, not substituted.")
        sys.exit(2)

    model, run_id = args.model, args.run_id
    rd = EXP_DIR / "runs" / run_id
    fixture, split = load_fixtures_and_split()

    if args.mode == "smoke":
        ids = split["calibration_ids"][: args.smoke_n]
        rows = run_split(model, "smoke", [fixture[i] for i in ids], api_key, "smoke")
        write_json(rd / "smoke" / "smoke_predictions.json", {"rows": rows})
        ok = [r for r in rows if r["status"] == "ok"]
        full = [r for r in ok if r["score_coverage"] == "full"]
        print(f"{model}: smoke {len(ok)}/{len(rows)} ok | echo={rows[0].get('provider_echo_model')} "
              f"| logprobs_all={all(r.get('logprobs_available') for r in ok)} | full-score={len(full)}/{len(ok)}")
        return

    cal = run_split(model, "calibration", [fixture[i] for i in split["calibration_ids"]], api_key, "full")
    test = run_split(model, "test", [fixture[i] for i in split["test_ids"]], api_key, "full")
    write_json(rd / "predictions_calibration.json", {"rows": cal})
    write_json(rd / "predictions_test.json", {"rows": test})

    vecs, gidx = [], []
    for r in cal:
        if r["status"] == "ok" and r.get("score_coverage") == "full":
            vecs.append([r["label_logprobs"][lab] for lab in LABELS])
            gidx.append(LABELS.index(r["gold_label"]))
    if len(vecs) >= 10:
        T = fit_temperature(vecs, gidx)
        src = f"temperature scaling fit on calibration split only (n={len(vecs)})"
    else:
        T = 1.0
        src = f"unavailable: only {len(vecs)} full-score calibration rows"

    metrics = {
        "experiment_id": EXPERIMENT_ID, "run_id": run_id,
        "model_id": model, "provider_id": PROVIDER,
        "provider_echo_models": sorted({r.get("provider_echo_model") for r in cal + test if r["status"] == "ok"}),
        "provenance": "real", "prompt_version": PROMPT_VERSION, "dataset_version": DATASET_VERSION,
        "frozen_split_source": "synthetic-topics-v1 seed 20260918 (identical to completed substitute experiment)",
        "logprobs_status": "available" if any(r.get("logprobs_available") for r in test + cal if r["status"] == "ok") else "unavailable",
        "langfuse_status": LANGFUSE_STATUS, "calibration_source": src,
        "calibration": {"temperature": T, "fit_n": len(vecs), "calibration_metrics": probability_metrics(cal, T)},
        "test": {**classification_metrics(test), **probability_metrics(test, T)},
        "run_timestamp": utcnow(),
    }
    write_json(rd / "metrics.json", metrics)

    events, traces = [], []
    for r in test + cal:
        if r["status"] != "ok":
            continue
        pred = LETTER_TO_LABEL[r["predicted_label"]] if r.get("valid_output") else None
        events.append({
            "schema_version": "classifier-bench.event.v1", "timestamp": r["timestamp"],
            "level": "info", "event": "inference.sample", "experiment_id": EXPERIMENT_ID,
            "run_id": run_id, "sample_id": r["sample_id"], "trace_id": r["trace_id"],
            "system": "real_llm", "model_id": model, "provider_id": PROVIDER,
            "prompt_version": PROMPT_VERSION, "dataset_version": DATASET_VERSION,
            "split": r["split"], "predicted_label": pred, "gold_label": r["gold_label"],
            "correct": (pred == r["gold_label"]) if pred else None, "latency_ms": r.get("latency_ms"),
        })
        traces.append({
            "name": "inference.call", "trace_id": r["trace_id"], "span_id": uuid.uuid4().hex[:16],
            "status": "OK", "attributes": {"sample_id": r["sample_id"], "split": r["split"],
            "model_id": model, "content_mode": "hashes_only"},
            "resource": {"telemetry.sdk.language": "python", "telemetry.sdk.name": "manual-jsonl",
            "service.name": "classifier-calibration-real-llm", "experiment_id": EXPERIMENT_ID,
            "run_id": run_id, "phase": r["split"]},
        })
    append_jsonl(rd / "events.jsonl", events)
    append_jsonl(rd / "otel_traces.jsonl", traces)
    write_json(rd / "observability_reconciliation.json", {
        "expected_test_samples": len(split["test_ids"]),
        "expected_calibration_samples": len(split["calibration_ids"]),
        "completed_predictions": sum(1 for r in cal + test if r["status"] == "ok"),
        "provider_errors": sum(1 for r in cal + test if r["status"] != "ok"),
        "unique_sample_ids": len({r["sample_id"] for r in cal + test}),
        "event_count": len(events), "trace_count": len(traces),
        "langfuse_status": LANGFUSE_STATUS,
        "reconciled": ({r["sample_id"] for r in test} == set(split["test_ids"]))
        and ({r["sample_id"] for r in cal} == set(split["calibration_ids"])),
    })
    write_json(rd / "llm_config.json", {
        "provider": PROVIDER, "model": model, "base_url": BASE_URL,
        "generation": {"temperature": 0.0, "max_tokens": 1, "seed": SEED, "logprobs": True,
                       "top_logprobs": 20, "chat_template_kwargs": {"enable_thinking": False}},
        "prompt_system": PROMPT_SYSTEM,
        "prompt_user_template": "Topic text:\n{text}\n\nAnswer:",
        "prompt_version": PROMPT_VERSION, "credential_env": "QWEN_API_KEY",
        "substitution_policy": "none: real or unavailable only",
    })
    t = metrics["test"]
    print(f"{model}: acc={t['accuracy_over_completed']} macro_f1={t['macro_f1']} "
          f"invalid={t['invalid_output_rate']} T={T} logloss={t['log_loss']} "
          f"provider_errors={t['n_provider_errors']}")


if __name__ == "__main__":
    main()
