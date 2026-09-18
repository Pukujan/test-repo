"""CLI: freeze/prepare, export-luna-prompts, ingest-luna, run, report.

No model API required: `run --provider mock` uses the deterministic mock so CI
can validate the full A/B/C/D1 mechanics end to end.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import arms as A
from . import capabilities
from . import freeze as freeze_mod
from . import metrics
from . import mock as mock_mod
from . import prompt_io
from . import record as R
from . import schemas as S

EXP = freeze_mod.EXPERIMENT_DIR


def _load_manifest() -> dict:
    return json.loads((EXP / "inputs" / "sample-manifest.json").read_text(encoding="utf-8"))


def _items(manifest: dict) -> list[str]:
    return [it["item_id"] for it in manifest["items"]]


def cmd_prepare(args):
    res = freeze_mod.freeze()
    print(json.dumps({"frozen_items": res["manifest"]["counts"], "seed": res["manifest"]["sample_seed"]}, indent=2))


def cmd_export(args):
    manifest = _load_manifest()
    gi = R.load_gold_index()
    out = Path(args.out)
    prompt_io.export_prompts(_items(manifest), gi, out)
    print(f"exported {len(_items(manifest))} packets to {out}")


def cmd_ingest(args):
    manifest = _load_manifest()
    gi = R.load_gold_index()
    res = prompt_io.ingest_responses(Path(args.responses), gi, _items(manifest))
    print(json.dumps({"ingested": len(res["responses"]), "problems": res["problems"]}, indent=2))


def _run_arm(arm, resp, visible, gold, z3_status, symai_status):
    if arm == "A":
        return A.run_arm_A(resp, visible, gold)
    if arm == "B":
        return A.run_arm_B(resp, visible, gold)
    if arm == "C":
        return A.run_arm_C(resp, visible, gold, z3_status)
    if arm == "D1":
        return A.run_arm_D1(resp, visible, gold, z3_status)
    if arm == "D2":
        return A.run_arm_D2(resp, visible, gold, symai_status, z3_status)
    raise ValueError(arm)


def cmd_run(args):
    manifest = _load_manifest()
    gi = R.load_gold_index()
    arms = [a.strip() for a in args.arms.split(",")]
    run_dir = EXP / "runs" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    caps = capabilities.detect_all()
    z3_status = caps["z3"]
    symai_status = caps["symai"]

    ingested = None
    if args.provider == "luna":
        ingested = prompt_io.ingest_responses(Path(args.responses), gi, _items(manifest))["responses"]

    records = []
    for iid in _items(manifest):
        rec = gi[iid]
        packet = R.build_visible_packet(iid, rec["visible"])
        if args.provider == "mock":
            resp = mock_mod.mock_response(iid, "B", gi)
        elif args.provider == "luna":
            resp = ingested.get(iid)
            if resp is None:
                continue
        else:
            raise ValueError(f"unknown provider {args.provider}")

        for arm in arms:
            ar = _run_arm(arm, resp, rec["visible"], rec["gold"], z3_status, symai_status)
            records.append({
                "item_id": iid,
                "dataset": "legalbench" if "#" in iid else "finqa",
                "task": rec.get("task"),
                "arm": arm,
                "prompt_digest": packet and R.prompt_digest(packet),
                "arm_result": ar,
            })

    # write run artifacts (records are visible-only; gold_correct is scoring-only)
    run_records = []
    for r in records:
        rr = dict(r)
        rr["arm_result"] = {k: v for k, v in r["arm_result"].items() if k != "gold_answer"}
        run_records.append(rr)
    (run_dir / "records.json").write_text(
        json.dumps({"schema_version": "vh.run-records.v1", "provider": args.provider,
                    "sample_seed": manifest["sample_seed"], "arms": arms,
                    "capabilities": caps, "records": run_records},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")

    agg = metrics.aggregate(records)
    (run_dir / "metrics.json").write_text(
        json.dumps({"schema_version": "vh.metrics.v1", "run_id": args.run_id,
                    "aggregate": agg, "per_task": metrics.per_task(records)},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(agg, indent=2))


def cmd_report(args):
    p = EXP / "runs" / args.run_id / "metrics.json"
    print(p.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Layered-verification benchmark harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("prepare").set_defaults(func=cmd_prepare)

    p = sub.add_parser("export-luna-prompts")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("ingest-luna")
    p.add_argument("--responses", required=True)
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("run")
    p.add_argument("--arms", default="A,B,C")
    p.add_argument("--provider", choices=("mock", "luna"), default="mock")
    p.add_argument("--responses", default=None)
    p.add_argument("--run-id", default="run-mock")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("report")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_report)

    args = ap.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
