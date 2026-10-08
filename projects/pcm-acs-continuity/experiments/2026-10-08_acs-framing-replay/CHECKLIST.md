# Checklist

> Generated from `checks.json`. Do not edit directly.

- [x] **SETUP-001** — Fixture, initial checkpoint, issue URL and precondition are durably recorded. (`pass`)
  - bounded first checkpoint: checkpoints/0001-initial-task-handoff.md
  - frozen issue precondition: workspace/decision-precondition.json
- [ ] **RUN-001** — A fresh local Claude session receives the fixed continuation task and produces an attributable output/artifact. (`pending`)
- [ ] **LIVE-001** — Live issue authority and current decision are checked during resumption; status is recorded. (`pending`)
- [ ] **ACTION-001** — Next action follows the governing issue rather than blindly reusing the dated checkpoint. (`pending`)
- [ ] **RECORD-001** — Actual agent output and outcome are captured as an experiment run with limitations, not inferred success. (`pending`)
