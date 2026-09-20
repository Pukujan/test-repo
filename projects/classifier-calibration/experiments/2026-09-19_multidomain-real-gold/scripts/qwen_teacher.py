#!/usr/bin/env python3
"""Real qwen3.8-flash teacher labeling for the frozen multi-domain contract.

Hard rule (experiment AGENTS.md): real or unavailable, NEVER substitute. A
provider error is recorded as an error row and counted; it never becomes a
heuristic, mock, or another model. Gold/newsgroup/label fields are never sent
(common.assert_no_gold). Model-visible text is the frozen contract text
(assert_contract gate must pass first).

Writes:
  gitignored runs/<run>/teacher/teacher_labels_<split>.jsonl   (per-row gold + logprobs)
  committed     runs/<run>/events.jsonl                        (NO gold, NO raw text: ids + model output + provenance only)
  committed     runs/<run>/otel_traces.jsonl
Resumable: re-running skips ids already present in the teacher file.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

PROVIDER = "yolo-auto"
BASE_URL = "https://yolo-auto.com/v1/chat/completions"
EXPERIMENT_ID = "classifier-calibration-2026-09-19-multidomain-real-gold"
DATASET_VERSION = "seed-20260919"
PROMPT_VERSION = common.PROMPT_VERSION
SEED = common.SEED
LETTER_IDS = list(common.LETTER_TO_DOMAIN.keys())


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_post(payload, api_key, timeout=60, attempts=5):
    body = json.dumps(payload).encode("utf-8")
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(
                BASE_URL, data=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                         "User-Agent": "mdrg-teacher/1.0"})
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8")), int((time.perf_counter() - t0) * 1000), i + 1
        except urllib.error.HTTPError as exc:
            last = exc
            if 400 <= exc.code < 500 and exc.code != 429:
                break
            time.sleep(3.0 * (i + 1))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"{type(last).__name__}: {last}")


def classify(model, sample, split, api_key, prompt_version=None):
    system, user = common.prompt_pair(sample, prompt_version)
    common.assert_no_gold([{"role": "system", "content": system}, {"role": "user", "content": user}],
                          sample["domain"])
    payload = {"model": model, "messages": [{"role": "system", "content": system},
                                            {"role": "user", "content": user}],
               "temperature": 0.0, "max_tokens": 1, "seed": SEED, "logprobs": True,
               "top_logprobs": 20, "chat_template_kwargs": {"enable_thinking": False}}
    trace_id = uuid.uuid4().hex
    base = {"schema": "mdrg-teacher-pred.v1", "sample_id": sample["id"], "split": split,
            "gold_domain": sample["domain"], "model_id": model, "provider_id": PROVIDER,
            "invocation_path": BASE_URL,
            "prompt_version": prompt_version or PROMPT_VERSION, "trace_id": trace_id}
    try:
        data, latency, attempts = http_post(payload, api_key)
    except RuntimeError as exc:
        return {**base, "status": "error", "error": str(exc), "teacher_letter": None,
                "teacher_domain": None, "valid_output": False, "label_logprobs": None,
                "score_coverage": "none", "timestamp": utcnow()}
    choice = data["choices"][0]
    stripped = (choice["message"].get("content") or "").strip()
    letter = stripped if stripped in LETTER_IDS else None
    label_lp, coverage = {}, "none"
    lp = choice.get("logprobs")
    have = bool(lp and lp.get("content"))
    if have:
        tok = lp["content"][0]
        if tok["token"].strip() in LETTER_IDS:
            label_lp[tok["token"].strip()] = tok["logprob"]
        for t in tok.get("top_logprobs") or []:
            tk = t["token"].strip()
            if tk in LETTER_IDS and tk not in label_lp:
                label_lp[tk] = t["logprob"]
        if label_lp:
            coverage = "full" if len(label_lp) == 4 else "partial"
    label_lp = {l: round(v, 6) for l, v in label_lp.items()}
    usage = data.get("usage") or {}
    return {**base, "status": "ok", "model_text": stripped[:8], "teacher_letter": letter,
            "teacher_domain": common.LETTER_TO_DOMAIN.get(letter) if letter else None,
            "valid_output": letter is not None, "logprobs_available": have,
            "label_logprobs": label_lp,
            "score_coverage": coverage, "provider_echo_model": data.get("model"),
            "latency_ms": latency, "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"), "attempts": attempts, "timestamp": utcnow()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "calibration", "test"], required=True)
    ap.add_argument("--model", default="qwen3.8-flash")
    ap.add_argument("--run-id", default="run-20260919-mdrg-001")
    ap.add_argument("--mode", choices=["smoke", "full"], default="full")
    ap.add_argument("--smoke-n", type=int, default=8)
    ap.add_argument("--prompt-version", default=common.PROMPT_VERSION)
    args = ap.parse_args()

    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("QWEN_API_KEY not set -> teacher would be marked unavailable, not substituted.")
        sys.exit(2)

    # FROZEN CONTRACT GATE: byte-identical reconstruction or abort before any call.
    rows = common.load_split(args.split)
    if args.mode == "smoke":
        rows = rows[: args.smoke_n]

    rd = common.RUNS / args.run_id
    (rd / "teacher").mkdir(parents=True, exist_ok=True)
    tpath = rd / "teacher" / f"teacher_labels_{args.split}.jsonl"

    prior = []
    if tpath.exists():
        for line in tpath.read_text(encoding="utf-8").splitlines():
            try:
                prior.append(json.loads(line))
            except Exception:
                pass
    # only ok rows are terminal; error rows (e.g. 429) are retried on re-run
    done = {r["sample_id"] for r in prior if r.get("status") == "ok"}
    todo = [r for r in rows if r["id"] not in done]
    print(f"{args.split}: {len(rows)} rows, {len(done)} ok, {len(todo)} to call")

    lock = threading.Lock()
    produced = 0

    def work(s):
        nonlocal produced
        rec = classify(args.model, s, args.split, api_key, args.prompt_version)
        with lock:
            with tpath.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
            produced += 1
            if produced % 50 == 0:
                print(f"  ...{produced}/{len(todo)}")
        return rec

    if todo:
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(work, todo))

    # committed observability (no gold, no raw text): aggregate ALL teacher files.
    raw_all = [json.loads(l) for tp in sorted((rd / "teacher").glob("teacher_labels_*.jsonl"))
               for l in tp.read_text(encoding="utf-8").splitlines()]
    # dedupe retried rows: prefer ok over error for the same (split, sample_id)
    best = {}
    for r in raw_all:
        key = (r["split"], r["sample_id"])
        prev = best.get(key)
        if prev is None or (prev["status"] != "ok" and r["status"] == "ok"):
            best[key] = r
    allrecs = list(best.values())
    events, traces = [], []
    for r in allrecs:
        if r["status"] != "ok":
            continue
        events.append({"schema_version": "mdrg.event.v1", "timestamp": r["timestamp"],
                       "level": "info", "event": "teacher.sample", "experiment_id": EXPERIMENT_ID,
                       "run_id": args.run_id, "sample_id": r["sample_id"], "trace_id": r["trace_id"],
                       "system": "qwen_teacher", "model_id": args.model, "provider_id": PROVIDER,
                       "prompt_version": PROMPT_VERSION, "dataset_version": DATASET_VERSION,
                       "split": r["split"], "predicted_domain": r["teacher_domain"],
                       "valid_output": r["valid_output"], "latency_ms": r.get("latency_ms"),
                       "score_coverage": r.get("score_coverage")})
        traces.append({"name": "teacher.call", "trace_id": r["trace_id"], "span_id": uuid.uuid4().hex[:16],
                       "status": "OK", "attributes": {"sample_id": r["sample_id"], "split": r["split"],
                       "model_id": args.model, "content_mode": "hashes_only"},
                       "resource": {"service.name": "mdrg-qwen-teacher", "experiment_id": EXPERIMENT_ID,
                       "run_id": args.run_id, "phase": r["split"]}})
    # rewrite committed observability deterministically from full teacher file
    (rd / "events.jsonl").write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in events), encoding="utf-8")
    (rd / "otel_traces.jsonl").write_text("".join(json.dumps(t, sort_keys=True) + "\n" for t in traces), encoding="utf-8")

    ok = [r for r in allrecs if r["status"] == "ok"]
    here = [r for r in allrecs if r["split"] == args.split]
    ok_here = [r for r in here if r["status"] == "ok"]
    full = [r for r in ok_here if r.get("score_coverage") == "full"]
    errs = len(here) - len(ok_here)
    echo = sorted({r.get("provider_echo_model") for r in ok_here})
    match = sum(1 for r in ok_here if r["teacher_domain"] == r["gold_domain"])
    print(f"{args.split}: ok={len(ok_here)} errors={errs} echo={echo} "
          f"full_score={len(full)} logprobs_all={all(r.get('logprobs_available') for r in ok_here) if ok_here else None}")
    print(f"{args.split}: teacher-vs-source-membership agreement on completed = {match}/{len(ok_here)} "
          f"({round(100*match/len(ok_here),2) if ok_here else 0}%)")


if __name__ == "__main__":
    main()
