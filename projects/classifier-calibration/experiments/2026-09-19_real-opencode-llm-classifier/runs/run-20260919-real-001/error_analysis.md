# Error analysis - real LLM (qwen3.8-flash) on frozen synthetic split

- Test rows: 100; valid: 100; provider errors: 0; invalid: 0
- Errors: 1; high-confidence (>0.9) wrong: 0

## Per-error detail (post-temperature-scaled probabilities)

### syn-0147
- gold `technology` -> predicted `health` at confidence 0.6902
- text: "Briefing covers encryption, with emphasis on neural and recent cardio."
- substitute (TF-IDF+LogReg) prediction: `technology`
- reading: health-adjacent vocabulary (cardio/neural) outweighed technology in the
  closed-set logprob; at ~0.69 confidence this is a soft/coherent uncertainty, not a
  overconfident miss.

## Key comparisons on the frozen split

- Real LLM error: `syn-0147` (technology misread as health).
- Potion 8M/32M error (completed experiment, same split): `syn-0176`. Real LLM prediction on syn-0176: `technology` (correct).
- Substitute error: `none (accuracy 1.00)`.
- Real LLM and Potion make DIFFERENT single errors; substitute is perfect on its own fixture.

## Ceiling-effect note

The synthetic corpus is keyword-saturated and close to the substitute's feature space, so the
substitute's 1.00 is expected. 0.99 from a real generative LLM neither beats nor loses to it in
any meaningful sense; it shows the fixture is saturated. Generalization needs a separate,
harder, real-domain experiment.
