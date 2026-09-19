# Experiment Continuation Instructions

Read root `AGENTS.md`, `LAB_SPEC.md`, and `projects/classifier-calibration/AGENTS.md` first.

## Experiment purpose

Test a real teacher -> student classification workflow:

```text
real heterogeneous public corpus
        |
        +--> real qwen3.8-flash teacher labels + calibrated reference
        |
        +--> Potion/Model2Vec trained on teacher labels
                         |
                         v
              independent frozen gold test
```

The primary question is whether the cheap local student learns useful real-domain semantics and where it fails.

Do not turn this into a model-vs-model leaderboard.

## Completed-history boundary

Do not modify:

- `2026-09-18_calibrated-llm-local-classifier`
- `2026-09-19_real-opencode-llm-classifier`

They are historical evidence.

## Scope

In scope:

- real public heterogeneous corpus acquisition;
- stable source/dataset provenance;
- coarse domain ontology;
- real qwen3.8-flash teacher labeling;
- empirical LLM calibration;
- Potion/Model2Vec training from teacher labels;
- student calibration;
- independent gold evaluation;
- source-shift/error analysis;
- benchmark observability;
- controlled iteration.

Out of scope for this experiment:

- graph/RAG construction;
- ordering/dependency prediction;
- triage/routing/consensus;
- model-vs-model tournament;
- hierarchical taxonomy expansion;
- full production deployment.

## Gold and leakage rules

- Teacher output is not gold.
- Final test gold must come from independent source-derived labels and/or explicit human-reviewed labels.
- Gold/test labels never enter model-visible Qwen prompts.
- Potion training receives teacher labels, not hidden test gold.
- Calibration may use the dedicated calibration gold split only.
- Final test membership and labels stay frozen after inference begins.

## Real-or-unavailable rule

For Qwen use the actual reachable `yolo-auto/qwen3.8-flash` path proven by the previous experiment, unless the owner explicitly changes it.

If unavailable, mark unavailable and stop that path.

Never silently replace it with TF-IDF, logistic regression, another LLM, a mock, or a heuristic.

The same applies to Langfuse or other optional observability backends.

## Data/source shortcut rule

Do not let the benchmark collapse into recognizing dataset boilerplate.

Remove or mask obvious source identifiers such as benchmark names, source URLs, explicit category labels, or repeated headers where practical.

Prefer at least two source families per top-level domain and a source-held-out primary test.

## Handoff

Before stopping:

1. append a numbered checkpoint;
2. update `state.json` and `checks.json`;
3. attach durable evidence to every PASS;
4. run `python tools/lab.py sync`;
5. run `python tools/lab.py validate`;
6. commit synchronized state.

Checkpoints are append-only.
