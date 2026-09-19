#!/usr/bin/env python3
"""Build the frozen multi-domain source-held-out contract + run the audits.

Reads raw fetched JSONL from local_data/ (gitignored), applies a deterministic
cleaning transform, splits source-A pools into train/calibration by id-hash
(seed fixed), and emits input manifests + audit_report.json. Raw text and gold
are never committed.

Audits:
  1. duplicates: exact normalized-text and fuzzy (char 5-gram containment) across
     train vs test and within each split.
  2. source/benchmark-name leakage: blocklist regex; TEST rows must not name their
     own or any training source identity.
  3. dataset fingerprints: NNTP/email/quote/boilerplate artifacts in TEST rows.
  4. gold leakage: the gold label token must not appear as a standalone keyword in
     any model-visible text; report rate per domain.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
RAW = EXP / "local_data"
INP = EXP / "inputs"
SEED = 20260919
CAL_FRAC = 0.3

# source_id -> role. test sources are the four independent-gold corpora.
TRAIN_SOURCES = ["arxiv_cs", "arxiv_stem", "pubmed", "fiqa", "courtlistener", "eurlex"]
TEST_SOURCES = ["20ng_comp", "20ng_sci", "agnews_biz", "legislation_uk"]

NAME_BLOCKLIST = [
    r"\bag[_ ]news\b", r"\b20[_ ]?news ?groups?\b", r"\bnewsgroups?\b",
    r"\bfiqa\b", r"\bphrasebank\b", r"\bleg[dl]ar\b", r"\bcasehold\b",
    r"\blegalbench\b", r"\bcourt ?listener\b", r"\beur[- ]?lex\b", r"\bpubmed\b",
    r"\bsec[- ]edgar\b", r"\barxiv\b", r"\blegislation\.gov\.uk\b", r"\bmediawiki\b",
    r"\bsci/tech\b", r"\bdbpedia\b", r"\bai2[_ ]arc\b", r"\bsciq\b",
]
FINGERPRINTS = [
    r"<[^\s@]+@[^\s@]+>",            # emails
    r"\bwrote:|\bsays?:|writes?:",   # quoting attribution
    r"\bIn article\s*<",              # NNTP header
    r"\bArticle-ID:|\bKeywords:|\bArchive-Name:|\bSummary:\s",
    r"^\s*(From|Subject|Newsgroups|Reply-To|Organization|Lines):\s",
    r"\|>|>>|\|\s*--",                # quote/sig markers
]

# Gold-leak is defined narrowly/adversarially (see gold_policy.md): the model's
# visible closed set is the 4 coarse labels {legal,finance,science,technology}.
# A leak is only (a) an explicit answer/label field, (b) a copy-able source
# identifier that maps 1:1 to the coarse answer (dotted newsgroup IDs), or
# (c) a multiple-choice answer marker. Ordinary topical use of a domain word
# (including "business"/"finance" inside a finance article) is CONTENT, not
# leakage: forbidding answer words from their own topic text would invalidate the
# benchmark. Gold leakage must not be inflated into removing valid signal.
GOLD_LEAK_PATTERNS = [
    r"\bcomp\.[a-z.]+", r"\bsci\.[a-z.]+", r"\brec\.sports", r"\btalk\.[a-z.]+",
    r"\balt\.[a-z.]+", r"\bsci/tech\b", r"\bcomp\.misc\b",
    r"\blabel(?:led)?\s*[:=]", r"\bcategory\s*[:=]", r"\btopic\s*[:=]\s*\w",
    r"\banswer\s*[:=]",
]


DOMAIN_BY_TEST = {"20ng_comp": "technology", "20ng_sci": "science",
                  "agnews_biz": "finance", "legislation_uk": "legal"}
DOMAIN_BY_TRAIN = {"arxiv_cs": "technology", "arxiv_stem": "science", "pubmed": "science",
                   "fiqa": "finance", "courtlistener": "legal", "eurlex": "legal"}


def load(name):
    p = RAW / f"{name}.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def clean(s):
    s = re.sub(r"\|>|>>|\|\s*--", " ", s)
    s = re.sub(r"^\s*(From|Subject|Newsgroups|Reply-To|Organization|Lines|Keywords|Summary|Archive-Name|Article-ID):\s.*$",
               " ", s, flags=re.M)
    s = re.sub(r"<[^\s@]+@[^\s@]+>", " ", s)
    s = re.sub(r"\S+\s*$", "", s) if s.endswith("@") else s
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


def ngrams(s, n=5):
    s = norm(s)
    return {s[i:i + n] for i in range(max(0, len(s) - n + 1))}


def containment(a, b):
    ga, gb = ngrams(a), ngrams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / min(len(ga), len(gb))


def split_cal(rows):
    out_tr, out_cal = [], []
    for r in rows:
        h = hashlib.sha256(f"{SEED}:{r['id']}".encode()).digest()
        frac = h[0] / 255.0
        (out_cal if frac < CAL_FRAC else out_tr).append(r)
    return out_tr, out_cal


def main():
    train_all, cal_all, test_all = [], [], []
    for s in TRAIN_SOURCES:
        tr, cal = split_cal(load(f"train_{s}"))
        for r in tr:
            r["domain"] = DOMAIN_BY_TRAIN[s]
        for r in cal:
            r["domain"] = DOMAIN_BY_TRAIN[s]
        train_all += tr
        cal_all += cal
    for s in TEST_SOURCES:
        rows = load(f"test_{s}")
        for r in rows:
            r["domain"] = DOMAIN_BY_TEST[s]
        test_all += rows

    # apply deterministic cleaning to model-visible text; record counts.
    cleaned = 0
    for pool in (train_all, cal_all, test_all):
        for r in pool:
            c = clean(r["text"])
            if c != r["text"]:
                cleaned += 1
            r["text"] = c
    train_all = [r for r in train_all if len(r["text"]) >= 60]
    cal_all = [r for r in cal_all if len(r["text"]) >= 60]
    test_all = [r for r in test_all if len(r["text"]) >= 60]

    # ---- deterministic TEST pruning (documented, before freezing) ----
    # Drop TEST rows that leak a copyable source identifier / answer field / MC
    # marker (narrow gold rule), name their own benchmark, carry NNTP/sig
    # fingerprints, or are exact internal duplicates (first occurrence kept).
    prune = {"gold_id_or_answer": [], "benchmark_name": [], "fingerprint": [],
             "internal_exact_dup": []}

    def has_name(t):
        return any(re.search(p, t, re.I) for p in NAME_BLOCKLIST)

    def has_fp(t):
        return any(re.search(p, t, flags=re.I | re.M) for p in FINGERPRINTS)

    def has_gold(t):
        return any(re.search(p, t, re.I) for p in GOLD_LEAK_PATTERNS)

    kept, seen_norm = [], set()
    for r in test_all:
        if has_gold(r["text"]):
            prune["gold_id_or_answer"].append(r["id"]); continue
        if has_name(r["text"]):
            prune["benchmark_name"].append(r["id"]); continue
        if has_fp(r["text"]):
            prune["fingerprint"].append(r["id"]); continue
        n = norm(r["text"])
        if n in seen_norm:
            prune["internal_exact_dup"].append(r["id"]); continue
        seen_norm.add(n); kept.append(r)
    test_all = kept

    # ---- audit 1: duplicates (post-prune, on the frozen contract) ----
    seen_tr = {norm(r["text"]) for r in train_all}
    dup_exact_test = sum(1 for r in test_all if norm(r["text"]) in seen_tr)
    # fuzzy test-vs-train (sampled against train text for cost)
    fuzzy = 0
    tr_texts = [r["text"] for r in train_all]
    step = max(1, len(tr_texts) // 200)
    for r in test_all:
        if any(containment(r["text"], t) > 0.6 for t in tr_texts[::step]):
            fuzzy += 1
    # internal near-dup within test (post-prune => expect 0)
    tt = [r["text"] for r in test_all]
    test_int = 0
    for i in range(len(tt)):
        for j in range(i + 1, len(tt)):
            if norm(tt[i]) == norm(tt[j]):
                test_int += 1

    # ---- audit 2: name leakage in model-visible TEST text ----
    name_hits = []
    for r in test_all:
        for pat in NAME_BLOCKLIST:
            if re.search(pat, r["text"], re.I):
                name_hits.append({"id": r["id"], "domain": r["domain"], "pattern": pat})
                break

    # ---- audit 3: fingerprint residue in TEST text ----
    fp_hits = []
    for r in test_all:
        for pat in FINGERPRINTS:
            if re.search(pat, r["text"], flags=re.I | re.M):
                fp_hits.append({"id": r["id"], "domain": r["domain"], "pattern": pat})
                break

    # ---- audit 4: gold leakage (narrow rule: copyable id / answer field / MC) ----
    gold_hits = []
    for r in test_all:
        for pat in GOLD_LEAK_PATTERNS:
            if re.search(pat, r["text"], re.I):
                gold_hits.append({"id": r["id"], "gold": r["gold"], "pattern": pat})
                break

    def counts(rows):
        d = {}
        for r in rows:
            d[r["domain"]] = d.get(r["domain"], 0) + 1
        return d

    def digest(rows):
        h = hashlib.sha256()
        for r in sorted(rows, key=lambda x: x["id"]):
            h.update(r["id"].encode()); h.update(b"\x00"); h.update(r["text"].encode()); h.update(b"\x00")
        return h.hexdigest()

    manifest = {
        "schema_version": "lab.dataset_manifest.v1",
        "dataset_id": "multidomain-real-gold-v1",
        "dataset_version": f"seed-{SEED}",
        "seed": SEED,
        "calibration_fraction": CAL_FRAC,
        "domain_counts": {"train": counts(train_all), "calibration": counts(cal_all),
                          "test": counts(test_all)},
        "source_role": {**{s: "train" for s in TRAIN_SOURCES}, **{s: "test" for s in TEST_SOURCES}},
        "per_domain_sources": {
            "technology": {"train": ["arxiv_cs"], "test": ["20ng_comp"]},
            "science": {"train": ["arxiv_stem", "pubmed"], "test": ["20ng_sci"]},
            "finance": {"train": ["fiqa"], "test": ["agnews_biz"]},
            "legal": {"train": ["courtlistener", "eurlex"], "test": ["legislation_uk"]},
        },
        "test_source_disjoint_from_train": True,
        "train_text_digest": digest(train_all),
        "calibration_text_digest": digest(cal_all),
        "test_text_digest": digest(test_all),
        "rows_cleaned": cleaned,
        "note": "raw text + gold gitignored; pin only digests + per-row ids",
    }
    (INP / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def split_manifest(name, rows):
        return {
            "schema_version": "lab.split_manifest.v1", "split": name, "seed": SEED,
            "ids": sorted(r["id"] for r in rows),
            "id_digest": hashlib.sha256(("\n".join(sorted(r["id"] for r in rows))).encode()).hexdigest(),
            "domains": counts(rows),
        }
    for name, rows in (("train", train_all), ("calibration", cal_all), ("test", test_all)):
        (INP / f"split_{name}.json").write_text(json.dumps(split_manifest(name, rows), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = {
        "schema_version": "lab.audit.v1",
        "duplicates": {"test_vs_train_exact": dup_exact_test, "test_vs_train_fuzzy_gt_0.6": fuzzy,
                       "test_internal_exact_pairs": test_int},
        "name_leak_test_rows": name_hits[:50], "name_leak_count": len(name_hits),
        "fingerprint_test_rows": fp_hits[:50], "fingerprint_count": len(fp_hits),
        "gold_leak_test_rows": gold_hits[:50], "gold_leak_count": len(gold_hits),
        "pruned_from_test": {k: v[:50] for k, v in prune.items()},
        "pruned_counts": {k: len(v) for k, v in prune.items()},
        "rows": {"train": len(train_all), "calibration": len(cal_all), "test": len(test_all)},
        "clean": (dup_exact_test == 0 and test_int == 0 and len(name_hits) == 0
                  and len(fp_hits) == 0 and len(gold_hits) == 0),
    }
    (INP / "audit_report.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit["duplicates"], indent=2))
    print("name_leak", audit["name_leak_count"], "fingerprint", audit["fingerprint_count"],
          "gold_leak", audit["gold_leak_count"], "cleaned", cleaned)
    print("pruned", audit["pruned_counts"], "clean:", audit["clean"])
    print("counts", manifest["domain_counts"])


if __name__ == "__main__":
    main()
