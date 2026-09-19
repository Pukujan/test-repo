# Gold policy — multidomain-real-gold-v1

This file is the authoritative policy for what counts as "gold", what may be
model-visible, and how leakage is judged. It is frozen with the data contract and
may only change via a corrective checkpoint + new dataset_version, never silently.

## 1. Two kinds of gold (deliberately different)

- **Train/teacher/calibration gold = source membership.** A row from `arxiv_cs`
  is `technology` by construction; `fiqa` is `finance`; `eurlex`/`courtlistener`
  is `legal`; `arxiv_stem`/`pubmed` is `science`. This is a property of where the
  text came from, not a human judgment about the text. It is adequate because the
  model is never shown it at training — the *teacher* assigns the real target.
- **Test gold = independent topical labels.** The four held-out test sources carry
  labels that come from the source's own independent labeling, not from the
  train-source partition: `20newsgroups` newsgroup names (mapped to a domain),
  `ag_news` class (business), UK statutes (public-law domain). Test sources share
  no corpus with any train source, so test gold is not derived from the same signal
  the teacher was trained on.

## 2. Teacher is the training target; test gold is scoring-only

- Potion trains on **Qwen teacher labels**, never on real gold, so the local
  classifier never sees held-out answers.
- Held-out test gold is used **only after** both systems have produced predictions,
  purely for scoring. It never enters any model-visible packet.

## 3. The model-visible closed set is the 4 coarse domains

The model sees exactly one letter option per domain (`A`=legal, `B`=finance,
`C`=science, `D`=technology) plus the sample text. It is never asked to output a
newsgroup name, a CELEX id, or a news category.

## 4. Narrow, adversarial definition of gold leakage

A row is **leaked** (and pruned from test) only if the model-visible text contains
an item the model could copy to get the answer:

1. a copyable source identifier that maps 1:1 to the domain (e.g. `comp.graphics`,
   `sci.med`, `sci/tech`),
2. an explicit answer/label field (`label:`, `category:`, `answer:`), or
3. a multiple-choice answer marker.

Ordinary topical vocabulary is **not** leakage. The word "business" in a business
headline, or "finance" in a finance article, is content: forbidding a domain word
from its own topic text would delete valid signal and make the benchmark incoherent.
This distinction is recorded here so a future agent does not inflate the gold-leak
metric by removing correctly-labeled rows.

## 5. Deterministic, reproducible, auditable

- Pruning runs in `scripts/build_and_audit.py` before freezing, driven only by the
  regex rules above plus exact-duplicate and NNTP/fingerprint patterns.
- The audit emits `inputs/audit_report.json` with per-category counts and the pruned
  ids (truncated). A clean freeze requires duplicates=0, name-leak=0, fingerprint=0,
  gold-leak=0 on the surviving test set.
- Raw text, gold, teacher predictions embedding licensed text, and per-row gold maps
  stay gitignored; only digests, counts, and aggregate metrics are committed.

## 6. No post-hoc gold edits

After the first teacher/eval call touches the test split, test membership and labels
are frozen. Observed errors are analyzed and answered by a controlled change to
*models/calibration/prompts*, or motivate a *new* dataset_version. They never justify
editing which rows are in the frozen test.
