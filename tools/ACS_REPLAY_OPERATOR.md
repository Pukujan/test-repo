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

No further prompt is needed: the launcher supplies the continuation request and runs Claude Code in non-interactive print mode with the owner's explicitly requested `--dangerously-skip-permissions` setting. A TTY and per-command approval are not required. The fixture task itself remains bounded to this experiment and asks Claude not to push or modify the issue.

## Headless retry after the blocked attempt

The earlier nested Claude process was launched interactively within a background non-TTY shell. Its permission prompts were denied, so that attempt produced no gradeable behavior. This is a harness failure, not a PCM verdict.

The updated launcher uses `claude -p --dangerously-skip-permissions --output-format stream-json --verbose` and writes its raw trace **outside the public repository**, under the user's cache directory. The raw trace is not meant to be committed. Only commit the bounded experiment artifacts after reviewing them.

From the existing checkout, if it is clean:

~~~powershell
git switch experiment/acs-framing-continuity-2026-10-08
git pull --ff-only origin experiment/acs-framing-continuity-2026-10-08
python tools/launch_acs_replay.py
~~~

This can be invoked by another local Claude agent in its ordinary shell; if that outer agent is subject to its own execution restrictions, this script does not override them.

**Trial validity:** no live-issue read, no preflight result and no observable next action or report is INCONCLUSIVE. The launcher returns nonzero if the expected report is missing, even if Claude itself exits zero.

## After Claude exits

The launcher prints three Git commands to record your local experiment files on the run branch. Review the diff first, push your run branch, and send its URL back for assessment. A plain terminal transcript plus the changed files also works if you prefer not to push.

## What this first trial proves and cannot prove

This is a **single known-failure regression**, reconstructed from the October 8 ACS/CGM framing problem, **not a verbatim transcript or an independent holdout**. The checkpoint preserves an old plan; the GitHub issue contains the later authoritative direction. The scorer and desired verdicts are deliberately not in the agent workspace. No sensitive logs, private conversations or production website assets are committed.

This measures whether the resumed Claude task *uses the opt-in PCM/ACS preflight, reconciles live task authority, and chooses its next action accordingly*. It is **not** a validation that every ACS task automatically invokes the guard: no mandatory action hook has shipped. Passing once neither estimates a general success rate nor rules out overfitting.

No production rollout, automatic merges, CGM work, or live ACS website changes are part of this experiment.
