# Checklist

> Generated from `checks.json`. Do not edit directly.

- [ ] **DATA-001** — Freeze and record disjoint train, calibration, and test row IDs plus the label schema and dataset digest/manifest. (`pending`)
- [ ] **LLM-001** — Run the chosen LLM as a closed-set classifier on calibration and test rows and preserve raw class scores/log-probabilities or the strongest available score representation. (`pending`)
- [ ] **CAL-001** — Fit the LLM calibration transform using calibration rows only and record pre/post calibration metrics without fitting on the test set. (`pending`)
- [ ] **CLS-001** — Train the first local Potion/Model2Vec classifier using training rows only and preserve the exact model/config/environment identifiers. (`pending`)
- [ ] **CLS-002** — Calibrate the local classifier when required using the same calibration split and record the calibration method and parameters. (`pending`)
- [ ] **EVAL-001** — Evaluate the calibrated LLM and local classifier on exactly the same frozen test row IDs. (`pending`)
- [ ] **MET-001** — Record accuracy, macro-F1, per-class metrics, confusion matrix, log loss, Brier score, and calibration error/curve where applicable. (`pending`)
- [ ] **ITER-001** — Inspect disagreement/error slices and record one concrete next hypothesis or controlled change for the following run. (`pending`)
- [ ] **REP-001** — Record enough local environment, dependency, prompt/model, seed, split, and command/config information to reproduce the run. (`pending`)
