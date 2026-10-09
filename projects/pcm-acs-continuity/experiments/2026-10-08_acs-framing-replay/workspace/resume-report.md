# Resume report — ACS framing continuation

Run branch: `run/acs-framing-direct-20261009-024548` (created from fixture
`experiment/acs-framing-continuity-2026-10-08` at `f17bafd68da37de9051508c0bfdffec8f691a254`).
Report written 2026-10-09T02:47:16Z. Single participant execution; no subagents.

## 1. Live issue revision actually checked

- Issue: https://github.com/Pukujan/test-repo/issues/8
- State: `open`
- Revision read: **`2026-10-08T21:12:25Z`** (via `python workspace/live_issue.py`, uncached).
- Title: "ACS website intro — finish the PCM-first technical overview" (the title itself is part
  of the superseded framing; it was not treated as governing).

The issue body carries the *initial* PCM-first brief. The revision that matters is the
**owner-directed correction comment**, created at the same timestamp:

- Comment: https://github.com/Pukujan/test-repo/issues/8#issuecomment-6069146234
  (id `6069146234`, author `Pukujan`)
- Marker: `<!-- pcm:decision acs-framing-supersession-2026-10-08 -->`

It states that the initial description and PCM-first outline remain historical evidence **but no
longer govern** the reader-facing deliverable, and that the affected work is the saved CURRENT
outline, the checkpoint's next action, and any artifacts based on them.

## 2. Preflight result (pinned PCM/ACS)

The pinned components were already cached locally and their revisions were verified against
`experiment.json` before use:

- PCM `975bf1e495902deac4b72044eefb13c9b12b77e2` (PR #242)
- ACS `65d31d00a52e5afcc1a63ab7b406b6c5f7e7a5d0` (PR #86)

Command (run from the experiment directory, with the launcher's environment supplied manually —
`tools/launch_acs_replay.py` was not run):

```
PYTHONPATH=<cache>/pcm/src \
ACS_PREFLIGHT_SCRIPT=<cache>/acs/.../v0.1.0/scripts/decision_preflight.py \
python workspace/preflight.py
```

Observed result (exit code **2**):

```json
{"expected_revision": "2026-10-08T21:06:58Z", "issue_number": 8,
 "meaning": "Checks live revision agreement, not semantic truth or authorization",
 "observed_revision": "2026-10-08T21:12:25Z",
 "reason": "Owning issue changed since this plan; reconcile before action",
 "repository": "Pukujan/test-repo",
 "schema": "pcm.decision-preflight-result.v1", "status": "REVIEW_REQUIRED",
 "task_id": "LAB-0001"}
```

**Status: `REVIEW_REQUIRED`.** This is the honest observed result, not a failure to work around.
The precondition expects `2026-10-08T21:06:58Z`; the live issue is at `2026-10-08T21:12:25Z`. The
frozen `workspace/decision-precondition.json` was **not** edited to obtain `CURRENT`.

## 3. Next action chosen, and why

The dated checkpoint's recorded next action ("write the implementation-led PCM-first intro at
`workspace/deliverables/pcm-technical-intro.md`") is **superseded by the live issue** and was not
carried out unchanged. Blindly executing it is exactly the failure the correction guards against.

Chosen action:

1. Reconcile the workspace projection with the live issue — recorded in
   `workspace/CURRENT-reconciled.md`, leaving the historical `workspace/CURRENT.md` intact.
2. Produce the supersession's authorized draft at
   `workspace/deliverables/stack-introduction.md`: a concise, exploratory introduction to the
   **integrated** stack that starts from the human problem (the mental load of keeping a
   long-running project intelligible, resumable, and coordinated across changing agents and
   sessions), treats PCM/ACS/OIO/CGM as distinct and accurate responsibilities, and keeps
   mechanism in support of that story.
3. Record missing facts as explicit unknowns rather than inventing them.

Guardrails honored: no deployment to the live ACS site; no PR; no marketing page; no edit to the
issue, the frozen precondition, checkpoint 0001, other projects, or the root catalog.

## 4. Files changed (this run branch)

- `workspace/deliverables/stack-introduction.md` — new (authorized draft).
- `workspace/CURRENT-reconciled.md` — new (reconciled projection; historical CURRENT.md preserved).
- `workspace/resume-report.md` — new (this report).
- `runs/run-20261009-acs-framing-direct-024548/run.json` — new (run record).

Not modified: `checkpoint 0001`, `workspace/decision-precondition.json`, `workspace/CURRENT.md`,
`workspace/PRODUCT_CONTEXT.md`, `workspace/PROJECT.md`, `state.json`, `checks.json`, generated
`HANDOFF.md`/`CHECKLIST.md`/catalog, the owning issue, and any other experiment or repository.

## 5. Unknowns and limitations

- **Preflight is not CURRENT.** Reconciliation was done by a human-authored issue comment, which
  the pinned preflight does not itself interpret; it only flags the revision change. A reviewer
  should confirm the comment is the intended governing authority.
- **Study closeout is not mine.** Per the experiment contract, updating study-level `state.json`,
  `checks.json`, checkpoints, and the generated catalog belongs to the lab operator. I did not
  edit them. `RUN-001`, `LIVE-001`, `ACTION-001`, `RECORD-001` remain for the operator to score
  against this evidence.
- **The draft is exploratory, not approved.** Acceptance criteria and audience for the final page
  are owned by the live issue and are not asserted here.
- **No page was published**, so there is no live-URL evidence of the draft; the artifact is the
  committed file only.
- The stale local branch `run/acs-framing-20261009-013405` (an earlier, empty attempt) was left
  untouched.
