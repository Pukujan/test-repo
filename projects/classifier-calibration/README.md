# Classifier Calibration Bench

This project isolates reproducible local experiments for comparing calibrated LLM classification with trained lightweight classifiers.

The scope is intentionally narrow:

- calibrate and evaluate an LLM classifier;
- train and evaluate a local classifier such as Model2Vec/Potion;
- compare both on the same frozen test split;
- inspect errors and iterate.

Out of scope: triage, consensus/jury systems, routing, document graphs, retrieval orchestration, and production deployment.

Current experiment: `2026-09-18_calibrated-llm-local-classifier`.

Coordination issue: `Pukujan/test-repo#3`.
