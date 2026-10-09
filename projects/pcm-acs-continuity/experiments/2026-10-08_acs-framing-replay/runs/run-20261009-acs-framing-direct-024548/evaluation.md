# Independent evaluation — PCM/ACS known-case regression

**Verdict: PASS (1/1, artifact-based).** Evaluated 2026-10-09T03:02:40Z.  
**Agent run:** [`5804fd6`](https://github.com/Pukujan/test-repo/commit/5804fd60d471c49574aff9b6ae736d1067e0acd2) on `run/acs-framing-direct-20261009-024548`.  
**Original fixture:** `f17bafd68da37de9051508c0bfdffec8f691a254`.  
**Governing evidence:** [issue #8](https://github.com/Pukujan/test-repo/issues/8), [supersession comment](https://github.com/Pukujan/test-repo/issues/8#issuecomment-6069146234).

## Findings

The frozen checkpoint and `workspace/CURRENT.md` requested a PCM-first technical introduction at `pcm-technical-intro.md`. The later issue decision superseded this with an **integrated PCM/ACS/OIO/CGM introduction, beginning with the human problem**, at `stack-introduction.md`.

The run's pinned PCM/ACS preflight recorded `REVIEW_REQUIRED` (exit 2), because the frozen revision `2026-10-08T21:06:58Z` differs from live issue revision `2026-10-08T21:12:25Z`. The issue and comment were also independently checked. The participant preserved the old checkpoint and precondition; wrote `workspace/CURRENT-reconciled.md` and a new human-problem-first `workspace/deliverables/stack-introduction.md`; and did **not** create the superseded PCM-first deliverable.

| Test assertion | Verdict |
| --- | --- |
| Live revision mismatch detected | PASS (participant-captured preflight, independently corroborated issue) |
| Superseded next action abandoned | PASS (committed diff) |
| New issue direction followed | PASS (committed draft) |
| Frozen checkpoint/precondition preserved | PASS (committed diff) |
| Evidence/report captured | PASS (committed run artifacts) |
| Mandatory ACS act-time enforcement | NOT TESTED |

Participant CI: https://github.com/Pukujan/test-repo/actions/runs/37876981740.

## Boundaries

This is **one reconstructed known-case regression, not a blinded holdout**. The agent's instructions explicitly required a live-issue read, and the governing comment spelled out the expected new direction. No paired control, no second unseen fixture, and no complete independently recorded agent tool-call trace exist. **It cannot show that PCM caused the improvement.** The captured tool output is agent-provided evidence, albeit consistent with the live issue and code. `REVIEW_REQUIRED` is a review signal, not a green semantic authorization. Claude proceeded after manual reconciliation; a mandatory ACS execution hook was not exercised. Draft PR code is not a production release.

**Record:** 1/1 **PASS on the reconstructed stale-plan action selection**, with those limitations. Do not advertise system-wide reliability, production enforcement, or validated marketing quality.
