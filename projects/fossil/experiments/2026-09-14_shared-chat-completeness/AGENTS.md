# Experiment Continuation Instructions

This experiment tests `Pukujan/fossil-core#247` using the owner-provided long ChatGPT share.

## Start here

1. Read `HANDOFF.md`.
2. Read `checkpoints/0001-initial.md` (or the newer checkpoint named by `state.json`).
3. Verify `Pukujan/fossil-core` still has the exact pinned baseline or explicitly record a new run against a different exact SHA.
4. Do not patch FOSSIL before reproducing current behavior.

## Source acquisition rules

- Share URL: `https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58`.
- Preserve exact retrieved representation before parsing.
- Record SHA-256, byte count, retrieval timestamp, transport/source URL, and acquisition method.
- Do not call capture `complete` because the final visible message exists.
- Exhaust provider graph/pagination/lazy continuation where exposed.
- Record discovered IDs/counts/root/current node/branch/unreachable nodes/continuation termination.
- Keep `fidelity` and `completeness` separate.
- If full acquisition cannot be proven, mark it `incomplete` or `unknown` and continue the experiment honestly.

## Handoff

Before stopping:

1. append a new numbered checkpoint;
2. update `state.json` and relevant `checks.json` entries;
3. attach evidence references to every PASS;
4. run `python tools/lab.py sync`;
5. run `python tools/lab.py validate`;
6. commit the state so another local/cloud session can resume from `HANDOFF.md` alone.
