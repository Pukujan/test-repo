# Checklist

> Generated from `checks.json`. Do not edit directly.

- [ ] **ONT-001** — Freeze the top-level ontology and label definitions before inference; initial core labels are legal, finance, science, technology, with explicit boundary examples. (`pending`)
- [ ] **SRC-001** — Pin real public corpus sources at stable revisions/URLs with license/provenance notes and content/file digests where obtainable; prefer at least two distinct source families per domain. (`pending`)
- [ ] **DATA-001** — Build a real-document dataset manifest with stable sample IDs, source IDs, document/chunk provenance, domain gold, and text/content digests without committing disallowed/private bytes. (`pending`)
- [ ] **SPLIT-001** — Freeze disjoint train/calibration/test IDs before inference, with the primary test source-held-out by domain where feasible; record seed and source allocation. (`pending`)
- [ ] **LEAK-001** — Prove gold labels/source-only answer fields are absent from all model-visible prompts and from any feature explicitly passed to Potion except teacher-produced training labels. (`pending`)
- [ ] **SHORTCUT-001** — Audit obvious dataset/source fingerprint shortcuts (source name, benchmark name, URL/domain token, boilerplate) and remove or separately report them so the classifier must use content semantics. (`pending`)
- [ ] **LLM-001** — Run real yolo-auto/qwen3.8-flash teacher classification with provider-proven real inference, exact prompt/config provenance, candidate-label logprobs when available, and no substitution. (`pending`)
- [ ] **TEACH-001** — Measure teacher-label quality against independent gold on calibration/test and record disagreement/error slices; teacher labels must not be treated as truth. (`pending`)
- [ ] **CAL-001** — Fit and evaluate qwen3.8-flash probability calibration on calibration gold only; preserve pre/post log-loss, Brier, ECE/reliability evidence. (`pending`)
- [ ] **STUD-001** — Train Potion/Model2Vec on training texts using qwen3.8-flash teacher labels only; record model ID, head/config, seed, package versions, and exact training IDs. (`pending`)
- [ ] **STUD-002** — Calibrate the trained student using calibration gold only when probabilities require calibration; never fit calibration on final test. (`pending`)
- [ ] **EVAL-001** — Evaluate Qwen and Potion on exactly the same frozen independent gold test IDs and report Potion performance as the primary student outcome, with teacher/reference metrics alongside it. (`pending`)
- [ ] **SHIFT-001** — Report performance separately on source-held-out test data and any same-source diagnostic slice so source/domain generalization is visible. (`pending`)
- [ ] **MIXED-001** — Keep natural mixed-domain/cross-domain examples in a separate challenge slice unless independently reviewed multi-label gold exists; do not contaminate headline single-label metrics. (`pending`)
- [ ] **MET-001** — Record accuracy, macro-F1, per-domain precision/recall/F1, confusion matrix, log-loss/Brier/ECE where applicable, invalid-output/provider-error counts, latency/tokens, and teacher-student disagreement. (`pending`)
- [ ] **OBS-001** — Produce stable experiment/run/sample/trace correlation, structured events, inspectable traces, and machine-readable reconciliation; use Langfuse if genuinely configured, otherwise record unavailable and preserve OTel evidence. (`pending`)
- [ ] **ERR-001** — Create an error taxonomy covering teacher errors, student-only errors, shared errors, source-shift errors, label-boundary ambiguity, and likely chunk/source artifacts. (`pending`)
- [ ] **ITER-001** — After the baseline, define at most one evidence-driven controlled change for the next run without changing frozen test membership or labels in response to model errors. (`pending`)
- [ ] **REP-001** — Record enough dataset, environment, prompt, model, classifier, seed, command, and observability information to reproduce the baseline. (`pending`)
- [ ] **LAB-001** — Run python tools/lab.py sync and python tools/lab.py validate before handoff; attach durable validation evidence when execution begins. (`pending`)
