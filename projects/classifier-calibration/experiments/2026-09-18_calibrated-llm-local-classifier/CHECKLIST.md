# Checklist

> Generated from `checks.json`. Do not edit directly.

- [ ] **DATA-001** — Freeze and record disjoint train, calibration, and test row IDs plus the label schema and dataset digest/manifest. (`pending`)
- [ ] **LLM-001** — Run the chosen LLM as a closed-set classifier on calibration and test rows and preserve raw class scores/log-probabilities or the strongest available score representation. (`pending`)
- [ ] **CAL-001** — Fit the LLM calibration transform using calibration rows only and record pre/post calibration metrics without fitting on the test set. (`pending`)
- [ ] **CLS-001** — Train the first local Potion/Model2Vec classifier using training rows only and preserve the exact model/config/environment identifiers. (`pending`)
- [ ] **CLS-002** — Calibrate the local classifier when required using the same calibration split and record the calibration method and parameters. (`pending`)
- [ ] **EVAL-001** — Evaluate the calibrated LLM and local classifier on exactly the same frozen test row IDs. (`pending`)
- [ ] **MET-001** — Record accuracy, macro-F1, per-class metrics, confusion matrix, log loss, Brier score, and calibration error/curve where applicable. (`pending`)
- [ ] **OBS-001** — Assign stable experiment/run/sample IDs and propagate trace correlation identifiers through the benchmark execution. (`pending`)
- [ ] **OBS-002** — Produce structured per-sample events or a safe durable digest/manifest with model, prediction, score, timing, and correlation metadata. (`pending`)
- [ ] **OBS-003** — Capture inspectable OpenTelemetry/Langfuse traces for the Run 1 smoke subset without violating the configured telemetry content mode. (`pending`)
- [ ] **OBS-004** — Reconcile expected samples, completed predictions, unique sample IDs, traces, structured events, missing IDs, and duplicates in a machine-readable run artifact. (`pending`)
- [ ] **OBS-005** — Verify dashboard/trace aggregates agree with deterministic row-level and run-level metric artifacts for the smoke subset and final run. (`pending`)
- [ ] **OBS-006** — Record observability configuration, tool versions, sampling/content policy, and telemetry privacy boundary without committing secrets. (`pending`)
- [ ] **ITER-001** — Inspect disagreement/error slices and record one concrete next hypothesis or controlled change for the following run. (`pending`)
- [ ] **REP-001** — Record enough local environment, dependency, prompt/model, seed, split, and command/config information to reproduce the run. (`pending`)
