#!/usr/bin/env python3
"""Shared, deterministic data reconstruction + frozen-contract gate.

Every inference stage calls load_split() which REBUILDS the split rows exactly
as scripts/build_and_audit.py froze them (same clean(), same >=60 length filter,
same id-hash train/calibration partition, same test prune rules) and then
asserts the reconstructed text digest equals the frozen
inputs/dataset_manifest.json digest. If the digest does not match, the contract
has drifted and we abort before any model call. Raw text stays in gitignored
local_data/; only ids/digests/labels are ever committed.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
RAW = EXP / "local_data"
INP = EXP / "inputs"
RUNS = EXP / "runs"

SEED = 20260919
CAL_FRAC = 0.3

TRAIN_SOURCES = ["arxiv_cs", "arxiv_stem", "pubmed", "fiqa", "courtlistener", "eurlex"]
TEST_SOURCES = ["20ng_comp", "20ng_sci", "agnews_biz", "legislation_uk"]

DOMAIN_BY_TEST = {"20ng_comp": "technology", "20ng_sci": "science",
                  "agnews_biz": "finance", "legislation_uk": "legal"}
DOMAIN_BY_TRAIN = {"arxiv_cs": "technology", "arxiv_stem": "science", "pubmed": "science",
                   "fiqa": "finance", "courtlistener": "legal", "eurlex": "legal"}

# Letter contract is frozen in inputs/ontology.json (A=legal,B=finance,C=science,D=technology).
LETTER_TO_DOMAIN = {"A": "legal", "B": "finance", "C": "science", "D": "technology"}
DOMAIN_TO_LETTER = {v: k for k, v in LETTER_TO_DOMAIN.items()}
DOMAINS = ["legal", "finance", "science", "technology"]

PROMPT_VERSION = "mdrg-letters-v1"

PROMPT_SYSTEM_V2 = (
    "You are a strict single-label topic classifier. Choose exactly one letter: "
    "A=legal, B=finance, C=science, D=technology. "
    "Science (C) covers natural-science and space-research discussion, including "
    "scientific instruments, missions, physics, astronomy, and biology research; "
    "technology (D) covers computing, software, networking, and consumer products. "
    "If hardware or spacecraft equipment is discussed in a research context, prefer C. "
    "Reply with exactly one capital letter (A, B, C, or D) and nothing else. "
    "No explanation, no punctuation, no spaces, no newline."
)
PROMPT_VERSIONS = {PROMPT_VERSION: None, "mdrg-letters-v2": PROMPT_SYSTEM_V2}

NAME_BLOCKLIST = [
    r"\bag[_ ]news\b", r"\b20[_ ]?news ?groups?\b", r"\bnewsgroups?\b",
    r"\bfiqa\b", r"\bphrasebank\b", r"\bleg[dl]ar\b", r"\bcasehold\b",
    r"\blegalbench\b", r"\bcourt ?listener\b", r"\beur[- ]?lex\b", r"\bpubmed\b",
    r"\bsec[- ]edgar\b", r"\barxiv\b", r"\blegislation\.gov\.uk\b", r"\bmediawiki\b",
    r"\bsci/tech\b", r"\bdbpedia\b", r"\bai2[_ ]arc\b", r"\bsciq\b",
]
FINGERPRINTS = [
    r"<[^\s@]+@[^\s@]+>",
    r"\bwrote:|\bsays?:|writes?:",
    r"\bIn article\s*<",
    r"\bArticle-ID:|\bKeywords:|\bArchive-Name:|\bSummary:\s",
    r"^\s*(From|Subject|Newsgroups|Reply-To|Organization|Lines):\s",
    r"\|>|>>|\|\s*--",
]
GOLD_LEAK_PATTERNS = [
    r"\bcomp\.[a-z.]+", r"\bsci\.[a-z.]+", r"\brec\.sports", r"\btalk\.[a-z.]+",
    r"\balt\.[a-z.]+", r"\bsci/tech\b", r"\bcomp\.misc\b",
    r"\blabel(?:led)?\s*[:=]", r"\bcategory\s*[:=]", r"\btopic\s*[:=]\s*\w",
    r"\banswer\s*[:=]",
]


def clean(s: str) -> str:
    s = re.sub(r"\|>|>>|\|\s*--", " ", s)
    s = re.sub(r"^\s*(From|Subject|Newsgroups|Reply-To|Organization|Lines|Keywords|Summary|Archive-Name|Article-ID):\s.*$",
               " ", s, flags=re.M)
    s = re.sub(r"<[^\s@]+@[^\s@]+>", " ", s)
    s = re.sub(r"\S+\s*$", "", s) if s.endswith("@") else s
    return re.sub(r"\s+", " ", s).strip()


def norm(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


def split_cal(rows):
    out_tr, out_cal = [], []
    for r in rows:
        h = hashlib.sha256(f"{SEED}:{r['id']}".encode()).digest()
        (out_cal if h[0] / 255.0 < CAL_FRAC else out_tr).append(r)
    return out_tr, out_cal


def _has(t, pats):
    return any(re.search(p, t, re.I) for p in pats)


def _load(name):
    p = RAW / f"{name}.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def digest(rows):
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x["id"]):
        h.update(r["id"].encode()); h.update(b"\x00"); h.update(r["text"].encode()); h.update(b"\x00")
    return h.hexdigest()


def rebuild_all():
    train_all, cal_all, test_all = [], [], []
    for s in TRAIN_SOURCES:
        tr, cal = split_cal(_load(f"train_{s}"))
        for r in tr:
            r["domain"] = DOMAIN_BY_TRAIN[s]
        for r in cal:
            r["domain"] = DOMAIN_BY_TRAIN[s]
        train_all += tr
        cal_all += cal
    for s in TEST_SOURCES:
        rows = _load(f"test_{s}")
        for r in rows:
            r["domain"] = DOMAIN_BY_TEST[s]
        test_all += rows

    for pool in (train_all, cal_all, test_all):
        for r in pool:
            r["text"] = clean(r["text"])
    train_all = [r for r in train_all if len(r["text"]) >= 60]
    cal_all = [r for r in cal_all if len(r["text"]) >= 60]
    test_all = [r for r in test_all if len(r["text"]) >= 60]

    kept, seen = [], set()
    for r in test_all:
        if _has(r["text"], GOLD_LEAK_PATTERNS):
            continue
        if _has(r["text"], NAME_BLOCKLIST):
            continue
        if _has(r["text"], FINGERPRINTS):
            continue
        n = norm(r["text"])
        if n in seen:
            continue
        seen.add(n)
        kept.append(r)
    test_all = kept
    return train_all, cal_all, test_all


def _frozen():
    return json.loads((INP / "dataset_manifest.json").read_text(encoding="utf-8"))


def assert_contract():
    """Abort unless reconstructed digests + counts match the frozen manifest."""
    train_all, cal_all, test_all = rebuild_all()
    f = _frozen()
    exp_counts = f["domain_counts"]
    checks = {
        "train_text_digest": (digest(train_all), f["train_text_digest"]),
        "calibration_text_digest": (digest(cal_all), f["calibration_text_digest"]),
        "test_text_digest": (digest(test_all), f["test_text_digest"]),
    }
    problems = [f"{k}: got {got} != frozen {want}" for k, (got, want) in checks.items() if got != want]
    for split, rows in (("train", train_all), ("calibration", cal_all), ("test", test_all)):
        got = {}
        for r in rows:
            got[r["domain"]] = got.get(r["domain"], 0) + 1
        if got != exp_counts[split]:
            problems.append(f"{split} counts {got} != frozen {exp_counts[split]}")
    # also assert split id sets match the committed split manifests
    for split, rows in (("train", train_all), ("calibration", cal_all), ("test", test_all)):
        sm = json.loads((INP / f"split_{split}.json").read_text(encoding="utf-8"))
        if sorted(r["id"] for r in rows) != sm["ids"]:
            problems.append(f"{split} id set drift vs split_{split}.json")
    if problems:
        raise SystemExit("FROZEN CONTRACT DRIFT — refusing to run inference:\n  " + "\n  ".join(problems))
    return train_all, cal_all, test_all


def load_split(split: str):
    train_all, cal_all, test_all = assert_contract()
    return {"train": train_all, "calibration": cal_all, "test": test_all}[split]


def prompt_pair(sample, prompt_version: str | None = None):
    """Model-visible prompt. Gold/newsgroup/label fields are NEVER included."""
    system = (
        "You are a strict single-label topic classifier. Choose exactly one letter: "
        "A=legal, B=finance, C=science, D=technology. "
        "Reply with exactly one capital letter (A, B, C, or D) and nothing else. "
        "No explanation, no punctuation, no spaces, no newline."
    )
    if prompt_version and prompt_version in PROMPT_VERSIONS:
        custom = PROMPT_VERSIONS[prompt_version]
        if custom is not None:
            system = custom
    user = f"Topic text:\n{sample['text']}\n\nAnswer:"
    return system, user


def teacher_logit_vector(label_logprobs, missing_margin=10.0):
    """4-letter logit vector A,B,C,D. Labels absent from top_logprobs (rare, when the
    provider returns fewer tokens than classes) get observed-min minus missing_margin,
    i.e. ~0 probability. Marked as partial coverage upstream; never a fabricated score."""
    ls = ["A", "B", "C", "D"]
    obs = [label_logprobs[l] for l in ls if l in label_logprobs]
    floor = min(obs) - missing_margin if obs else -30.0
    return [label_logprobs.get(l, floor) for l in ls]


def assert_no_gold(messages, gold_domain: str) -> None:
    blob = json.dumps(messages)
    if re.search(r'"(gold|label|newsgroup|category)"\s*:', blob):
        raise AssertionError("leak guard tripped: label field in prompt")
    if f'"{gold_domain}"' in blob:
        raise AssertionError(f"leak guard tripped: gold domain {gold_domain!r} in prompt")
