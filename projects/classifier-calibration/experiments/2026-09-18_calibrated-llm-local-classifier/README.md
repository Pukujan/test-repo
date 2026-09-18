# Calibrated LLM versus local lightweight classifier

This experiment establishes a minimal local benchmark for the classification workflow discussed in `Pukujan/test-repo#3`.

It answers one question: can an LLM classifier be empirically calibrated and compared fairly with a locally trained lightweight classifier on the same domain-tagging corpus split?

The first local classifier is Model2Vec/Potion. SetFit may be added later only as a baseline if useful.

The experiment deliberately excludes triage, consensus, routing, graph construction, and production orchestration.

Start with `HANDOFF.md`, then read `PLAN.md` and the checkpoint named by `state.json`.
