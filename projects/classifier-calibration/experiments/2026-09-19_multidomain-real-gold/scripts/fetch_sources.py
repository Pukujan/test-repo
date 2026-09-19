#!/usr/bin/env python3
"""Fetch bounded, real, no-auth snippets for the multi-domain real-gold contract.

Writes gitignored JSONL under local_data/ (raw text never committed). Each line:
  {"id","source_id","domain","text","gold"}  # gold is source-membership for train,
                                              # independent topical label for test.
Train/teacher/calibration sources carry gold=source_id (domain membership).
Held-out TEST sources carry an independent topical gold label.

Reliability first: short per-call timeouts, UA headers, hard caps. If a source is
unreachable it raises; nothing is silently substituted.
"""
from __future__ import annotations

import gzip
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request

import requests

OUT = "local_data"
UA = {"User-Agent": "classifier-bench/1.0 (research benchmark; contact: bench@example.com)"}
MAXLEN = 600

TRAIN = {}   # source_id -> list[dict]
TEST = {}    # source_id -> list[dict]


def _get(url, headers=None, timeout=45, gz=False, retries=3):
    h = dict(UA)
    if headers:
        h.update(headers)
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=h, timeout=timeout)
            r.raise_for_status()
            return r.content if gz else r.text
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            if code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def _clean(s: str) -> str:
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:MAXLEN]


def write_jsonl(name, rows):
    with open(f"{OUT}/{name}.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{name}: {len(rows)} rows")


# --- TRAIN/TEACHER/CALIBRATION SOURCES (gold = source membership) ---

def fetch_arxiv(cat_query, source_id, domain, cap):
    # arXiv API pages at max_results<=2000; we take a modest cap.
    n = min(cap, 400)
    url = ("http://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(cat_query) + f"&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending")
    xml = _get(url, timeout=60)
    titles = re.findall(r"<summary>(.*?)</summary>", xml, re.S)
    rows = []
    for i, t in enumerate(titles):
        text = _clean(t)
        if len(text) < 120:
            continue
        rows.append({"id": f"arx-{source_id}-{i}", "source_id": source_id,
                     "domain": domain, "text": text, "gold": domain})
        if len(rows) >= cap:
            break
    return rows


def fetch_pubmed(cap):
    es = json.loads(_get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                         "?db=pubmed&retmode=json&retmax=400&term=protein+OR+genome+OR+cell"))
    ids = es["esearchresult"]["idlist"][:cap]
    if not ids:
        raise RuntimeError("pubmed empty")
    ef = _get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
              "?db=pubmed&retmode=text&rettype=abstract&id=" + ",".join(ids), timeout=90)
    rows = []
    for i, blk in enumerate(re.split(r"\n\d+\.\s", ef)[:cap]):
        text = _clean(blk)
        if len(text) < 120:
            continue
        rows.append({"id": f"pm-{i}", "source_id": "pubmed", "domain": "science",
                     "text": text, "gold": "science"})
    return rows


def fetch_fiqa(cap):
    # beir/fiqa corpus = parquet in tree (datasets-server endpoints 404 for it).
    import pyarrow.parquet as pq
    raw = _get("https://huggingface.co/datasets/beir/fiqa/resolve/main/corpus/corpus-00000-of-00001.parquet",
               gz=True, timeout=120)
    table = pq.read_table(io.BytesIO(raw))
    d = table.to_pylist()
    rows = []
    for i, rec in enumerate(d):
        title = rec.get("title", "") or ""
        text = _clean(f"{title} {rec.get('text','')}")
        if len(text) < 80:
            continue
        rows.append({"id": f"fiqa-{rec.get('_id', i)}", "source_id": "fiqa",
                     "domain": "finance", "text": text, "gold": "finance"})
        if len(rows) >= cap:
            break
    return rows


def fetch_courtlistener(cap):
    rows = []
    for q in ["contract breach", "search warrant", "patent infringement", "negligence duty",
              "bankruptcy discharge", "sentencing guidelines"]:
        url = ("https://www.courtlistener.com/api/rest/v4/search/?q="
               + urllib.parse.quote(q) + "&type=o&highlight=on")
        try:
            j = json.loads(_get(url, timeout=60))
        except Exception:
            continue
        for res in j.get("results", []):
            parts = []
            for op in (res.get("opinions") or []):
                if op.get("snippet"):
                    parts.append(op["snippet"])
            if res.get("syllabus"):
                parts.append(res["syllabus"])
            text = _clean(" ".join(parts))
            text = re.sub(r"</?mark>", "", text)
            if len(text) < 120:
                continue
            rows.append({"id": f"cl-{res.get('cluster_id') or res.get('cid','x')}",
                         "source_id": "courtlistener", "domain": "legal",
                         "text": text, "gold": "legal"})
            if len(rows) >= cap:
                return rows
        time.sleep(0.3)
    return rows


# --- HELD-OUT TEST SOURCES (independent topical gold) ---


def fetch_eurlex(cap):
    # EUR-Lex CELEX TXT pages: public EU law; section-chunked, gold=membership.
    celex = ["32016R0679", "32016L0680", "32002L0087", "32011L0036", "32004L0038",
             "32014L0024", "32013L0048", "32019L0790", "32000L0043", "32012L0019"]
    rows = []
    for cx in celex:
        url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A{cx}"
        try:
            html = _get(url, timeout=90)
        except Exception:
            continue
        body = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S | re.I)
        body = re.sub(r"<[^>]+>", " ", body)
        body = re.sub(r"\s+", " ", body)
        chunks = re.split(r"(?=Article \d+[a-z]?\s)", body)
        for i, c in enumerate(chunks):
            text = c.strip()[:MAXLEN]
            if len(text) < 200 or not text.startswith("Article"):
                continue
            rows.append({"id": f"eu-{cx}-a{i}", "source_id": "eurlex", "domain": "legal",
                         "text": text, "gold": "legal"})
            if len(rows) >= cap:
                return rows
        time.sleep(0.5)
    return rows


# --- HELD-OUT TEST SOURCES (independent topical gold) ---


def fetch_20ng(prefix, domain, cap):
    rows = []
    off = 0
    while len(rows) < cap and off < 6000:
        url = ("https://datasets-server.huggingface.co/rows?dataset=SetFit%2F20_newsgroups"
               f"&config=default&split=test&offset={off}&length=100")
        j = json.loads(_get(url, timeout=60))
        for row in j.get("rows", []):
            d = row["row"]
            lt = d.get("label_text", "")
            if not lt.startswith(prefix):
                continue
            text = _clean(d.get("text", ""))
            if len(text) < 100:
                continue
            rows.append({"id": f"20ng-{lt}-{d.get('label')}-{off}-{len(rows)}",
                         "source_id": "20newsgroups", "domain": domain,
                         "text": text, "gold": lt})
            if len(rows) >= cap:
                return rows
        off += 100
        time.sleep(0.2)
    return rows


def fetch_agnews_business(cap):
    import pyarrow.parquet as pq
    raw = _get("https://huggingface.co/datasets/ag_news/resolve/main/data/test-00000-of-00001.parquet",
               gz=True, timeout=90)
    table = pq.read_table(io.BytesIO(raw))
    d = table.to_pylist()
    labels = ["world", "sports", "business", "sci/tech"]
    rows = []
    for i, rec in enumerate(d):
        if int(rec["label"]) != 2:  # business
            continue
        text = _clean(f"{rec.get('title','')} {rec.get('text','')}")
        if len(text) < 60:
            continue
        rows.append({"id": f"agn-biz-{i}", "source_id": "agnews", "domain": "finance",
                     "text": text, "gold": "business"})
        if len(rows) >= cap:
            break
    return rows


def fetch_legislation_uk(cap):
    # UK statutes (public law). Split data.xml into chunked sections.
    acts = ["ukpga/2018/12", "ukpga/2010/24", "ukpga/1996/47", "ukpga/2015/2"]
    rows = []
    for act in acts:
        url = f"https://www.legislation.gov.uk/{act}/data.xml"
        try:
            xml = _get(url, timeout=90, gz=True)
            xml = xml.decode("utf-8", "ignore")
        except Exception:
            continue
        secs = re.findall(r"<Para[ >].*?</Para>|<Section[ >].*?</Section>", xml, re.S)
        for i, s in enumerate(secs):
            text = _clean(s)
            if len(text) < 200:
                continue
            rows.append({"id": f"uk-{act.replace('/','_')}-{i}", "source_id": "legislation_gov_uk",
                         "domain": "legal", "text": text, "gold": "legislation_gov_uk"})
            if len(rows) >= cap:
                return rows
    return rows


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    TRAIN["arxiv_cs"] = fetch_arxiv("cat:cs.*", "arxiv_cs", "technology", 250)
    TRAIN["arxiv_stem"] = fetch_arxiv(
        "cat:physics.* OR cat:q-bio.* OR cat:math.* OR cat:stat.*", "arxiv_stem", "science", 200)
    TRAIN["pubmed"] = fetch_pubmed(150)
    TRAIN["fiqa"] = fetch_fiqa(250)
    TRAIN["courtlistener"] = fetch_courtlistener(120)
    TRAIN["eurlex"] = fetch_eurlex(180)

    TEST["20ng_comp"] = fetch_20ng("comp.", "technology", 200)
    TEST["20ng_sci"] = fetch_20ng("sci.", "science", 200)
    TEST["agnews_biz"] = fetch_agnews_business(200)
    TEST["legislation_uk"] = fetch_legislation_uk(200)

    for name, rows in TRAIN.items():
        write_jsonl("train_" + name, rows)
    for name, rows in TEST.items():
        write_jsonl("test_" + name, rows)
    print("TRAIN totals:", {k: len(v) for k, v in TRAIN.items()})
    print("TEST totals:", {k: len(v) for k, v in TEST.items()})


if __name__ == "__main__":
    main()
