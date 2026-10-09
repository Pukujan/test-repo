# One-run operator instructions — Claude local test

The **test repo is not empty**: it is an existing durable experiment lab. The new case lives only on branch [experiment/acs-framing-continuity-2026-10-08](https://github.com/Pukujan/test-repo/tree/experiment/acs-framing-continuity-2026-10-08). Existing experiments are untouched.

## Start

From a terminal with Git, Python 3.11+ and the Claude Code CLI already signed in:

~~~sh
git clone --branch experiment/acs-framing-continuity-2026-10-08 https://github.com/Pukujan/test-repo.git
cd test-repo
python tools/launch_acs_replay.py
~~~

If this repo already exists locally, update the **new branch** without changing the existing experiment branches: fetch it and switch to it first, ensuring your checkout has no uncommitted changes.

The launcher uses a cache **outside the working repository** for two exact pinned drafts:
- PCM revision 975bf1e495902deac4b72044eefb13c9b12b77e2 (PR #242);
- ACS revision 65d31d00a52e5afcc1a63ab7b406b6c5f7e7a5d0 (PR #86).

It rejects a moved source branch instead of silently installing newer code. It creates a separate local run branch, starts a fresh Claude session inside the experiment, and supplies the pinned PCM and ACS module paths through the environment. **It does not run the private grader or edit the owning GitHub issue.**

No further prompt is needed: the launcher supplies the continuation request. Allow normal read-only commands; review any requested writes and keep them inside the named experiment. Do **not** enable permission skipping or permit the agent to push/change the owning issue.

## Permission-gate prerequisite / retry after a blocked run

**Launch from an actual interactive PowerShell or Windows Terminal window with a human present.** Do **not** ask another Claude instance to run the launcher through its background/non-TTY shell or redirect its output to a log. Nested Claude Code asks for ordinary tool permissions; if there is no operator to approve them, a completed process and exit code 0 can still mean **zero measured task actions**. The launcher now refuses noninteractive stdin/stdout *before creating a run branch*. Preparation-only is safe in automation:

~~~powershell
python tools/launch_acs_replay.py --prepare-only
~~~

After an inconclusive headless attempt that left a **clean** local run branch, retain it; do not delete or alter it as "evidence". In the same repository clone, open a fresh interactive terminal and run:

~~~powershell
git status --short
git switch experiment/acs-framing-continuity-2026-10-08
git pull --ff-only origin experiment/acs-framing-continuity-2026-10-08
python tools/launch_acs_replay.py
~~~

Do not continue if the previous branch has uncommitted work—inspect it first. Do not use Claude permission-bypass flags or broad auto-accept settings. The human may approve read-only issue/preflight commands and review writes **only inside this experiment**. Decline any git push, issue edit, or changes elsewhere from the participant. The launcher itself does not request authorization to mutate GitHub.

**Trial validity:** missing live-issue reads, missing preflight result, or no observable next action/report due to permissions = **INCONCLUSIVE**, not a model/PCM failure or success. Preserve the raw CLI transcript if available, but do not synthesize missing evidence.

## After Claude exits

The launcher prints three Git commands to record your local experiment files on the run branch. Review the diff first, push your run branch, and send its URL back for assessment. A plain terminal transcript plus the changed files also works if you prefer not to push.

## What this first trial proves and cannot prove

This is a **single known-failure regression**, reconstructed from the October 8 ACS/CGM framing problem, **not a verbatim transcript or an independent holdout**. The checkpoint preserves an old plan; the GitHub issue contains the later authoritative direction. The scorer and desired verdicts are deliberately not in the agent workspace. No sensitive logs, private conversations or production website assets are committed.

This measures whether the resumed Claude task *uses the opt-in PCM/ACS preflight, reconciles live task authority, and chooses its next action accordingly*. It is **not** a validation that every ACS task automatically invokes the guard: no mandatory action hook has shipped. Passing once neither estimates a general success rate nor rules out overfitting.

No production rollout, automatic merges, CGM work, or live ACS website changes are part of this experiment.
